"""信号处理服务模块

本模块实现了信号数据的处理服务，包括切片、验证等功能。
"""
from typing import List, Tuple, Optional
import uuid
import numpy as np

from radar_system.domain.signal.entities.signal import SignalData, SignalSlice, TimeRange
from radar_system.infrastructure.common.logging import system_logger

class SignalProcessor:
    """信号处理服务
    
    负责信号数据的处理，包括切片、验证等功能。
    
    Attributes:
        slice_length (int): 切片长度，单位为ms，默认250ms
        slice_dim (int): 切片维度，默认为4（TOA维度）
    """
    
    def __init__(self, slice_length: int = 250, slice_dim: int = 4):
        """初始化信号处理服务
        
        Args:
            slice_length: 切片长度，单位ms，默认250ms
            slice_dim: 切片维度，默认为4（TOA维度）
        """
        self.slice_length = slice_length
        self.slice_dim = slice_dim
        
    def slice_signal(self, signal: SignalData) -> List[SignalSlice]:
        """对信号数据进行切片
        
        根据预设的slice_length对数据进行时间维度的切片。
        
        Args:
            signal: 待切片的信号数据
            
        Returns:
            List[SignalSlice]: 切片列表，每个元素为一个SignalSlice实例
        """
        if signal.raw_data is None or len(signal.raw_data) == 0:
            system_logger.warning("没有可用的数据进行切片")
            return []
            
        # 获取时间维度的数据
        time_data = signal.raw_data[:, self.slice_dim]
        
        # 计算时间范围
        time_min = np.min(time_data)
        time_max = np.max(time_data)
        
        # 计算切片边界
        slice_boundaries = np.arange(
            time_min, 
            time_max + self.slice_length, 
            self.slice_length
        )
        
        # 存储切片结果
        slices = []
        
        # 进行切片
        for i in range(len(slice_boundaries) - 1):
            start_time = slice_boundaries[i]
            end_time = slice_boundaries[i + 1]
            
            # 提取当前时间窗口内的数据
            mask = (time_data >= start_time) & (time_data < end_time)
            current_slice_data = signal.raw_data[mask]
            
            # 跳过空切片
            if len(current_slice_data) == 0:
                continue
                
            # 创建时间范围(使用切片边界)
            time_range = TimeRange(
                start_time=start_time,
                end_time=end_time
            )
            
            # 创建切片实例
            slice_instance = SignalSlice(
                id=str(uuid.uuid4()),
                parent_signal_id=signal.id,
                slice_index=i,
                time_range=time_range,
                data=current_slice_data,
                metadata={
                    'point_count': len(current_slice_data),
                    'start_time': start_time,
                    'end_time': end_time
                }
            )
            
            slices.append(slice_instance)
            
        system_logger.info(f"切片完成，共生成{len(slices)}个切片")
        return slices
