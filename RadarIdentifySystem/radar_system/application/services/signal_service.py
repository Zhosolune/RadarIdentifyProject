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
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
from radar_system.infrastructure.common.config import ConfigManager
from radar_system.infrastructure.async_core.thread_pool.pool import ThreadPool
from radar_system.infrastructure.async_core.event_bus.event import Event

class SignalService:
    """信号处理服务
    
    协调信号数据的加载、验证和处理流程。
    """
    
    def __init__(self, 
                 validator: SignalValidator,
                 processor: SignalProcessor,
                 repository: SignalRepository,
                 excel_reader: ExcelReader,
                 event_bus: EventBus,
                 thread_pool: ThreadPool):
        """初始化信号处理服务
        
        Args:
            validator: 信号验证器
            processor: 信号处理器
            repository: 信号数据仓库
            excel_reader: Excel读取器
            event_bus: 事件总线
            thread_pool: 线程池
        """
        self.validator = validator
        self.processor = processor
        self.repository = repository
        self.excel_reader = excel_reader
        self.event_bus = event_bus
        self.thread_pool = thread_pool
        self.config_manager = ConfigManager.get_instance()
        self.current_signal = None
        self.current_slices = None
        
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
            # 发布开始加载事件
            self.event_bus.publish(Event(
                type="signal_loading_started",
                data={"file_path": file_path}
            ))
            
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
                self.event_bus.publish(Event(
                    type="signal_validation_failed",
                    data={
                        "file_path": file_path,
                        "error": message
                    }
                ))
                return False, message, None
            
            # 保存当前信号数据
            self.current_signal = signal
            self.repository.save(signal)
            
            # 发布加载完成事件
            self.event_bus.publish(Event(
                type="signal_loading_completed",
                data={
                    "signal_id": signal.id,
                    "data_count": signal.data_count,
                    "band_type": signal.band_type,
                    "expected_slices": signal.expected_slices
                }
            ))
            
            return True, "数据加载成功", signal
            
        except Exception as e:
            error_msg = f"加载信号数据出错: {str(e)}"
            system_logger.error(error_msg)
            self.event_bus.publish(Event(
                type="signal_loading_failed",
                data={
                    "file_path": file_path,
                    "error": error_msg
                }
            ))
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
            # 发布开始切片事件
            self.event_bus.publish(Event(
                type="slice_processing_started",
                data={"signal_id": signal.id}
            ))
            
            # 执行切片
            slices = self.processor.slice_signal(signal)
            if not slices:
                return False, "切片处理未生成有效数据", None
                
            # 保存切片结果
            self.current_slices = slices
            
            # 发布切片完成事件
            self.event_bus.publish(Event(
                type="slice_processing_completed",
                data={
                    "signal_id": signal.id,
                    "slice_count": len(slices)
                }
            ))
            
            return True, "切片处理完成", slices
            
        except Exception as e:
            error_msg = f"切片处理出错: {str(e)}"
            system_logger.error(error_msg)
            self.event_bus.publish(Event(
                type="slice_processing_failed",
                data={
                    "signal_id": signal.id,
                    "error": error_msg
                }
            ))
            return False, error_msg, None
            
    def get_current_signal(self) -> Optional[SignalData]:
        """获取当前信号数据"""
        return self.current_signal
        
    def get_current_slices(self) -> Optional[List[SignalSlice]]:
        """获取当前切片列表"""
        return self.current_slices
            
