"""DBSCAN聚类服务单元测试

本模块包含DBSCAN聚类服务的完整单元测试。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from pathlib import Path

from radar_system.domain.signal.entities.signal import SignalSlice, TimeRange
from radar_system.domain.recognition.services.clustering_service import DBSCANClusteringService, ClusteringParams
from radar_system.domain.recognition.services.ui_params_parser import UIParamsParser
from radar_system.infrastructure.common.exceptions import ValidationError


class TestClusteringParams(unittest.TestCase):
    """聚类参数测试类"""
    
    def test_valid_clustering_params(self):
        """测试有效的聚类参数"""
        params = ClusteringParams(eps=2.0, min_samples=3, dimension='CF')
        self.assertEqual(params.eps, 2.0)
        self.assertEqual(params.min_samples, 3)
        self.assertEqual(params.dimension, 'CF')
    
    def test_invalid_dimension(self):
        """测试无效的维度参数"""
        with self.assertRaises(ValueError):
            ClusteringParams(eps=2.0, min_samples=3, dimension='INVALID')
    
    def test_invalid_eps(self):
        """测试无效的eps参数"""
        with self.assertRaises(ValueError):
            ClusteringParams(eps=-1.0, min_samples=3, dimension='CF')
    
    def test_invalid_min_samples(self):
        """测试无效的min_samples参数"""
        with self.assertRaises(ValueError):
            ClusteringParams(eps=2.0, min_samples=0, dimension='CF')


class TestDBSCANClusteringService(unittest.TestCase):
    """DBSCAN聚类服务测试类"""
    
    def setUp(self):
        """测试前置设置"""
        # 模拟配置管理器
        self.mock_config_manager = Mock()
        self.mock_config_manager.clustering.epsilon_cf = 2.0
        self.mock_config_manager.clustering.epsilon_pw = 0.2
        self.mock_config_manager.clustering.min_pts = 1
        
        # 创建测试数据
        self.test_data = np.array([
            [2000.0, 10.0, 45.0, 70.0, 100.0],
            [2001.0, 10.5, 46.0, 71.0, 110.0],
            [2002.0, 11.0, 47.0, 72.0, 120.0],
            [3000.0, 50.0, 80.0, 90.0, 200.0],
        ])
        
        # 创建测试切片
        time_range = TimeRange(start_time=0.0, end_time=250.0)
        self.test_slice = SignalSlice(
            id='test_slice',
            parent_signal_id='test_signal',
            slice_index=0,
            time_range=time_range,
            data=self.test_data
        )
    
    @patch('radar_system.domain.recognition.services.clustering_service.ConfigManager.get_instance')
    def test_service_initialization(self, mock_get_instance):
        """测试服务初始化"""
        mock_get_instance.return_value = self.mock_config_manager
        
        service = DBSCANClusteringService()
        self.assertIsNotNone(service.config_manager)
    
    @patch('radar_system.domain.recognition.services.clustering_service.ConfigManager.get_instance')
    def test_extract_clustering_features_cf(self, mock_get_instance):
        """测试CF维度特征提取"""
        mock_get_instance.return_value = self.mock_config_manager
        service = DBSCANClusteringService()
        
        features = service._extract_clustering_features(self.test_data, 'CF')
        
        # 验证特征形状和内容
        self.assertEqual(features.shape, (4, 1))
        np.testing.assert_array_equal(features.flatten(), [2000.0, 2001.0, 2002.0, 3000.0])
    
    @patch('radar_system.domain.recognition.services.clustering_service.ConfigManager.get_instance')
    def test_extract_clustering_features_pw(self, mock_get_instance):
        """测试PW维度特征提取"""
        mock_get_instance.return_value = self.mock_config_manager
        service = DBSCANClusteringService()
        
        features = service._extract_clustering_features(self.test_data, 'PW')
        
        # 验证特征形状和内容
        self.assertEqual(features.shape, (4, 1))
        np.testing.assert_array_equal(features.flatten(), [10.0, 10.5, 11.0, 50.0])
    
    @patch('radar_system.domain.recognition.services.clustering_service.ConfigManager.get_instance')
    def test_cluster_signal_slice_cf(self, mock_get_instance):
        """测试CF维度聚类"""
        mock_get_instance.return_value = self.mock_config_manager
        service = DBSCANClusteringService()
        
        params = ClusteringParams(eps=5.0, min_samples=2, dimension='CF')
        results, unclustered = service.cluster_signal_slice(self.test_slice, params)
        
        # 验证聚类结果
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) >= 0)
        
        # 验证聚类结果的属性
        for result in results:
            self.assertEqual(result.dim_name, 'CF')
            self.assertEqual(result.slice_index, 0)
            self.assertIsNotNone(result.cluster_data)
    
    @patch('radar_system.domain.recognition.services.clustering_service.ConfigManager.get_instance')
    def test_cluster_empty_slice(self, mock_get_instance):
        """测试空切片聚类"""
        mock_get_instance.return_value = self.mock_config_manager
        service = DBSCANClusteringService()
        
        # 创建空切片
        empty_data = np.array([]).reshape(0, 5)
        time_range = TimeRange(start_time=0.0, end_time=250.0)
        empty_slice = SignalSlice(
            id='empty_slice',
            parent_signal_id='test_signal',
            slice_index=0,
            time_range=time_range,
            data=empty_data
        )
        
        params = ClusteringParams(eps=2.0, min_samples=2, dimension='CF')
        results, unclustered = service.cluster_signal_slice(empty_slice, params)
        
        # 验证空切片结果
        self.assertEqual(len(results), 0)
        self.assertIsNone(unclustered)
    
    @patch('radar_system.domain.recognition.services.clustering_service.ConfigManager.get_instance')
    def test_get_clustering_params_from_ui(self, mock_get_instance):
        """测试从UI获取聚类参数"""
        mock_get_instance.return_value = self.mock_config_manager
        service = DBSCANClusteringService()
        
        # 模拟UI参数
        ui_params = {
            'epsilon_cf': '3.0',
            'min_pts': '2'
        }
        
        params = service.get_clustering_params_from_ui(ui_params, 'CF')
        
        self.assertEqual(params.eps, 3.0)
        self.assertEqual(params.min_samples, 2)
        self.assertEqual(params.dimension, 'CF')
    
    @patch('radar_system.domain.recognition.services.clustering_service.ConfigManager.get_instance')
    def test_invalid_ui_params_fallback(self, mock_get_instance):
        """测试无效UI参数的回退机制"""
        mock_get_instance.return_value = self.mock_config_manager
        service = DBSCANClusteringService()
        
        # 无效的UI参数
        ui_params = {
            'epsilon_cf': 'invalid',
            'min_pts': ''
        }
        
        params = service.get_clustering_params_from_ui(ui_params, 'CF')
        
        # 应该使用默认值
        self.assertEqual(params.eps, 2.0)  # 默认值
        self.assertEqual(params.min_samples, 1)  # 默认值
        self.assertEqual(params.dimension, 'CF')


class TestUIParamsParser(unittest.TestCase):
    """UI参数解析器测试类"""
    
    def test_validate_valid_params(self):
        """测试有效参数验证"""
        self.assertEqual(UIParamsParser.validate_clustering_param_value('2.0', 'epsilon_cf'), 2.0)
        self.assertEqual(UIParamsParser.validate_clustering_param_value('0.2', 'epsilon_pw'), 0.2)
        self.assertEqual(UIParamsParser.validate_clustering_param_value('1', 'min_pts'), 1.0)
    
    def test_validate_invalid_params(self):
        """测试无效参数验证"""
        self.assertIsNone(UIParamsParser.validate_clustering_param_value('', 'epsilon_cf'))
        self.assertIsNone(UIParamsParser.validate_clustering_param_value('invalid', 'epsilon_pw'))
        self.assertIsNone(UIParamsParser.validate_clustering_param_value('-1.0', 'min_pts'))
        self.assertIsNone(UIParamsParser.validate_clustering_param_value('1.5', 'min_pts'))  # 非整数
    
    def test_extract_params_from_mock_window(self):
        """测试从模拟窗口提取参数"""
        # 创建模拟窗口
        mock_window = Mock()
        mock_window.cluster_params = {
            'epsilon_cf': Mock(text=Mock(return_value='2.0')),
            'epsilon_pw': Mock(text=Mock(return_value='0.2')),
            'min_pts': Mock(text=Mock(return_value='1'))
        }
        
        # 模拟QLineEdit的text()方法
        for param_name, widget in mock_window.cluster_params.items():
            widget.text.return_value.strip.return_value = widget.text.return_value
        
        params = UIParamsParser.extract_clustering_params_from_window(mock_window)
        
        self.assertIn('epsilon_cf', params)
        self.assertIn('epsilon_pw', params)
        self.assertIn('min_pts', params)


if __name__ == '__main__':
    unittest.main()
