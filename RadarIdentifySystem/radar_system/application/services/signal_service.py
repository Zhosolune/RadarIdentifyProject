"""信号处理服务模块

本模块实现了信号处理的应用服务，协调信号数据的加载、验证和处理流程。
"""
from typing import Tuple, Optional, Dict, List
import uuid
from datetime import datetime
import pandas as pd
import numpy as np

from radar_system.domain.signal.entities.signal import SignalData, SignalSlice
from radar_system.domain.signal.services.validator import SignalValidator
from radar_system.domain.signal.services.processor import SignalProcessor
from radar_system.domain.signal.repositories.signal_repository import SignalRepository
from radar_system.infrastructure.persistence.excel.reader import ExcelReader
from radar_system.infrastructure.common.logging import system_logger

from radar_system.infrastructure.common.config import ConfigManager
from radar_system.domain.signal.services.plotter import SignalPlotter
from radar_system.infrastructure.persistence.file.file_storage import FileStorage
from pathlib import Path

class SignalService:
    """信号处理服务
    
    协调信号数据的加载、验证和处理流程。
    """
    
    def __init__(self, processor: SignalProcessor, excel_reader: ExcelReader,
                 plotter: SignalPlotter = None, file_storage: FileStorage = None):
        """初始化信号处理服务

        简化的构造函数注入，注入核心依赖和Infrastructure组件

        Args:
            processor: 信号处理器
            excel_reader: Excel读取器
            plotter: 信号绘图服务（可选，用于切片显示）
            file_storage: 文件存储服务（可选，用于切片显示）
        """
        self.processor = processor
        self.excel_reader = excel_reader
        # 直接创建其他依赖，避免过度抽象
        self.validator = SignalValidator()
        self.repository = SignalRepository()
        self.config_manager = ConfigManager.get_instance()
        # Infrastructure组件（用于切片显示业务流程）
        self.plotter = plotter or SignalPlotter()
        self.file_storage = file_storage or FileStorage()
        self.current_signal = None
        self.current_slices = None
        self.current_slice_index = -1  # 添加切片索引管理
        
    def _process_raw_data(self, raw_data: np.ndarray) -> Tuple[np.ndarray, int]:
        """处理原始数据
        
        Args:
            raw_data: 原始数据数组
            
        Returns:
            Tuple[np.ndarray, int]:
                - np.ndarray: 处理后的数据
                - int: 预计切片数量
        """
        # 剔除错误数据
        original_length = len(raw_data)
        processed_data = raw_data[raw_data[:,3] != 255]  # 剔除PA无效值
        filtered_length = len(processed_data)
        
        # 计算预计切片数量
        toa_data = processed_data[:, 4]  # TOA数据
        time_range = np.max(toa_data) - np.min(toa_data)  # 时间范围，单位ms
        slice_duration = self.config_manager.data_processing.slice_length  # 从配置获取切片时长
        expected_slices = int(np.ceil(time_range / slice_duration))
        
        system_logger.info(
            f"数据处理完成：原始数据量 {original_length}，"
            f"有效数据量 {filtered_length}，"
            f"剔除无效数据量 {original_length - filtered_length}，"
            f"预计切片数量 {expected_slices}"
        )
        
        return processed_data, expected_slices
        
    def load_signal_file(self, file_path: str) -> Tuple[bool, str, SignalData]:
        """加载信号数据文件
        
        从Excel文件加载雷达信号数据。使用线程池处理IO密集型的文件读取操作。
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            tuple: (是否成功, 消息, 信号数据)
        """
        try:
            # 记录开始加载日志
            system_logger.info(f"开始加载信号文件: {file_path}")

            # 读取Excel文件
            success, raw_data, message = self.excel_reader.read_radar_data(file_path)
            if not success:
                return False, message, None

            # 处理原始数据
            processed_data, expected_slices = self._process_raw_data(raw_data)

            # 创建信号数据实体
            signal = SignalData(
                id=str(uuid.uuid4()),
                raw_data=processed_data,
                expected_slices=expected_slices,
                is_valid=False
            )

            # 验证数据
            valid, message = self.validator.validate_signal(signal)
            if not valid:
                system_logger.error(f"信号数据验证失败: {message}")
                return False, message, None

            # 保存当前信号数据
            self.current_signal = signal
            self.repository.save(signal)

            # 记录加载完成日志
            system_logger.info(f"信号文件加载完成: {signal.id}, 数据量: {signal.data_count}, 频段: {signal.band_type}")

            return True, "数据加载成功", signal

        except Exception as e:
            error_msg = f"加载信号数据出错: {str(e)}"
            system_logger.error(error_msg)
            return False, error_msg, None
            
    def start_slice_processing(self, signal: SignalData) -> Tuple[bool, str, Optional[List[SignalSlice]]]:
        """开始切片处理
        
        对信号数据进行切片处理，并保存切片结果。
        
        Args:
            signal: 待处理的信号数据
            
        Returns:
            tuple: (是否成功, 消息, 切片列表)
        """
        try:
            # 记录开始切片日志
            system_logger.info(f"开始信号切片处理: {signal.id}")

            # 执行切片
            slices = self.processor.slice_signal(signal)
            if not slices:
                return False, "切片处理未生成有效数据", None

            # 保存切片结果和重置索引
            self.current_slices = slices
            self.current_slice_index = -1  # 重置切片索引

            # 记录切片完成日志
            system_logger.info(f"信号切片处理完成: {signal.id}, 切片数量: {len(slices)}")

            return True, "切片处理完成", slices

        except Exception as e:
            error_msg = f"切片处理出错: {str(e)}"
            system_logger.error(error_msg)
            return False, error_msg, None
            
    def get_current_signal(self) -> Optional[SignalData]:
        """获取当前信号数据"""
        return self.current_signal

    def get_current_slices(self) -> Optional[List[SignalSlice]]:
        """获取当前切片列表"""
        return self.current_slices

    def get_next_slice(self) -> Optional[SignalSlice]:
        """获取下一个切片

        Returns:
            Optional[SignalSlice]: 下一个切片，如果没有则返回None
        """
        if not self.current_slices:
            return None

        # 检查是否还有下一个切片
        if self.current_slice_index + 1 >= len(self.current_slices):
            return None

        # 移动到下一个切片
        self.current_slice_index += 1
        return self.current_slices[self.current_slice_index]

    def get_current_slice(self) -> Optional[SignalSlice]:
        """获取当前切片"""
        if not self.current_slices or self.current_slice_index < 0 or self.current_slice_index >= len(self.current_slices):
            return None
        return self.current_slices[self.current_slice_index]

    def get_slice_info(self) -> Tuple[int, int]:
        """获取切片信息

        Returns:
            Tuple[int, int]: (当前切片索引+1, 总切片数)
        """
        if not self.current_slices:
            return 0, 0
        return self.current_slice_index + 1, len(self.current_slices)

    def is_last_slice(self) -> bool:
        """检查当前是否为最后一个切片

        用于预防性UI状态管理，避免用户点击无效的"下一片"按钮。

        Returns:
            bool: 如果当前是最后一个切片返回True，否则返回False
        """
        if not self.current_slices:
            return True  # 没有切片时视为最后一个
        return self.current_slice_index >= len(self.current_slices) - 1

    def prepare_slice_display_data(self, slice_data: SignalSlice) -> Dict[str, any]:
        """准备切片显示所需的数据

        协调Infrastructure层服务，生成UI层需要的显示数据。
        这个方法承担业务流程协调职责，符合Application层的设计原则。

        Args:
            slice_data: 切片数据

        Returns:
            Dict[str, any]: 包含UI显示所需数据的字典
                - title: 标题文本
                - image_paths: 图像路径字典
                - current_index: 当前切片索引
                - total_count: 总切片数
                - success: 是否成功生成数据
                - error_message: 错误信息（如果有）
        """
        try:
            # 获取切片信息
            current_index, total_count = self.get_slice_info()

            # 生成标题
            title = f"第{current_index}个切片数据 原始图像"

            # 获取当前信号数据
            signal = self.get_current_signal()
            if not signal or not slice_data:
                return {
                    'title': title,
                    'image_paths': {},
                    'current_index': current_index,
                    'total_count': total_count,
                    'success': False,
                    'error_message': '缺少信号数据或切片数据'
                }

            # 更新绘图服务的波段配置
            self.plotter.update_band_config(signal.band_type)

            # 生成图像数据
            image_data = self.plotter.plot_slice(slice_data.data)

            # 保存图像文件
            image_paths = self.file_storage.save_slice_images(
                image_data=image_data,
                slice_idx=current_index,
                is_temp=False
            )

            # 验证图像文件存在性
            validated_paths = {}
            for plot_type, image_path in image_paths.items():
                if image_path and Path(image_path).exists():
                    validated_paths[plot_type] = image_path

            system_logger.debug(f"切片显示数据准备完成: {current_index}/{total_count}")

            return {
                'title': title,
                'image_paths': validated_paths,
                'current_index': current_index,
                'total_count': total_count,
                'success': True,
                'error_message': None
            }

        except Exception as e:
            error_msg = f"准备切片显示数据失败: {str(e)}"
            system_logger.error(error_msg)
            current_index, total_count = self.get_slice_info()
            return {
                'title': f"第{current_index}个切片数据 原始图像",
                'image_paths': {},
                'current_index': current_index,
                'total_count': total_count,
                'success': False,
                'error_message': error_msg
            }
