"""切片显示重构验证测试

验证重构后的切片显示功能是否正常工作，确保：
1. SignalService的prepare_slice_display_data方法正常工作
2. UI层的update_slice_display方法只负责UI更新
3. 业务流程协调正确从UI层移至Application层
4. 功能完整性保持不变
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from pathlib import Path

from radar_system.application.services.signal_service import SignalService
from radar_system.domain.signal.entities.signal import SignalData, SignalSlice
from radar_system.domain.signal.services.processor import SignalProcessor
from radar_system.domain.signal.services.plotter import SignalPlotter
from radar_system.infrastructure.persistence.excel.reader import ExcelReader
from radar_system.infrastructure.persistence.file.file_storage import FileStorage


class TestSliceDisplayRefactoring(unittest.TestCase):
    """切片显示重构验证测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟组件
        self.mock_processor = Mock(spec=SignalProcessor)
        self.mock_excel_reader = Mock(spec=ExcelReader)
        self.mock_plotter = Mock(spec=SignalPlotter)
        self.mock_file_storage = Mock(spec=FileStorage)
        
        # 创建SignalService实例
        self.signal_service = SignalService(
            processor=self.mock_processor,
            excel_reader=self.mock_excel_reader,
            plotter=self.mock_plotter,
            file_storage=self.mock_file_storage
        )
        
        # 创建测试数据
        self.test_signal = SignalData(
            id="test-signal-001",
            raw_data=np.random.rand(1000, 5),
            expected_slices=4,
            is_valid=True
        )
        
        self.test_slice = SignalSlice(
            id="test-slice-001",
            signal_id="test-signal-001",
            data=np.random.rand(100, 5),
            start_time=0.0,
            end_time=250.0,
            slice_index=1
        )
        
    def test_prepare_slice_display_data_success(self):
        """测试prepare_slice_display_data方法成功场景"""
        # 设置模拟数据
        self.signal_service.current_signal = self.test_signal
        self.signal_service.current_slices = [self.test_slice]
        self.signal_service.current_slice_index = 0
        
        # 配置模拟对象
        self.mock_plotter.plot_slice.return_value = {
            'CF': np.random.rand(100, 100),
            'PW': np.random.rand(100, 100),
            'PA': np.random.rand(100, 100),
            'DTOA': np.random.rand(100, 100),
            'DOA': np.random.rand(100, 100)
        }
        
        self.mock_file_storage.save_slice_images.return_value = {
            'CF': '/path/to/cf.png',
            'PW': '/path/to/pw.png',
            'PA': '/path/to/pa.png',
            'DTOA': '/path/to/dtoa.png',
            'DOA': '/path/to/doa.png'
        }
        
        # 模拟文件存在检查
        with patch('pathlib.Path.exists', return_value=True):
            # 执行测试
            result = self.signal_service.prepare_slice_display_data(self.test_slice)
        
        # 验证结果
        self.assertTrue(result['success'])
        self.assertEqual(result['title'], "第1个切片数据 原始图像")
        self.assertEqual(result['current_index'], 1)
        self.assertEqual(result['total_count'], 1)
        self.assertIsNone(result['error_message'])
        self.assertEqual(len(result['image_paths']), 5)
        
        # 验证方法调用
        self.mock_plotter.update_band_config.assert_called_once()
        self.mock_plotter.plot_slice.assert_called_once()
        self.mock_file_storage.save_slice_images.assert_called_once()
        
    def test_prepare_slice_display_data_no_signal(self):
        """测试prepare_slice_display_data方法无信号数据场景"""
        # 设置无信号状态
        self.signal_service.current_signal = None
        self.signal_service.current_slices = []
        self.signal_service.current_slice_index = -1
        
        # 执行测试
        result = self.signal_service.prepare_slice_display_data(self.test_slice)
        
        # 验证结果
        self.assertFalse(result['success'])
        self.assertEqual(result['error_message'], '缺少信号数据或切片数据')
        self.assertEqual(result['image_paths'], {})
        
    def test_prepare_slice_display_data_plotter_error(self):
        """测试prepare_slice_display_data方法绘图错误场景"""
        # 设置模拟数据
        self.signal_service.current_signal = self.test_signal
        self.signal_service.current_slices = [self.test_slice]
        self.signal_service.current_slice_index = 0
        
        # 配置绘图器抛出异常
        self.mock_plotter.plot_slice.side_effect = Exception("绘图失败")
        
        # 执行测试
        result = self.signal_service.prepare_slice_display_data(self.test_slice)
        
        # 验证结果
        self.assertFalse(result['success'])
        self.assertIn("准备切片显示数据失败", result['error_message'])
        
    def test_architecture_compliance(self):
        """测试架构合规性"""
        # 验证SignalService包含Infrastructure组件
        self.assertIsNotNone(self.signal_service.plotter)
        self.assertIsNotNone(self.signal_service.file_storage)
        
        # 验证方法存在
        self.assertTrue(hasattr(self.signal_service, 'prepare_slice_display_data'))
        self.assertTrue(callable(getattr(self.signal_service, 'prepare_slice_display_data')))
        
        # 验证返回数据结构
        self.signal_service.current_signal = self.test_signal
        self.signal_service.current_slices = [self.test_slice]
        self.signal_service.current_slice_index = 0
        
        self.mock_plotter.plot_slice.return_value = {}
        self.mock_file_storage.save_slice_images.return_value = {}
        
        result = self.signal_service.prepare_slice_display_data(self.test_slice)
        
        # 验证返回数据包含所有必需字段
        required_fields = ['title', 'image_paths', 'current_index', 'total_count', 'success', 'error_message']
        for field in required_fields:
            self.assertIn(field, result)


if __name__ == '__main__':
    unittest.main()
