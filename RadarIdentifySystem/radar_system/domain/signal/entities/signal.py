"""信号数据实体模块

定义了雷达信号数据的实体类。
"""
from typing import Optional, Tuple, List
import numpy as np
from dataclasses import dataclass

@dataclass
class TimeRange:
    """时间范围值对象
    
    Attributes:
        start_time (float): 开始时间（ms）
        end_time (float): 结束时间（ms）
    """
    start_time: float
    end_time: float
    
    def __post_init__(self):
        """验证时间范围的有效性"""
        if self.start_time > self.end_time:
            raise ValueError("开始时间不能大于结束时间")
    
    def contains(self, time: float) -> bool:
        """检查给定时间是否在范围内"""
        return self.start_time <= time <= self.end_time
    
    def duration(self) -> float:
        """获取时间范围的持续时间"""
        return self.end_time - self.start_time

class SignalData:
    """雷达信号数据实体类
    
    Attributes:
        id (str): 信号数据唯一标识
        raw_data (np.ndarray): 原始数据数组，包含 [CF, PW, DOA, PA, TOA]
        band_type (str): 频段类型
        is_valid (bool): 数据是否有效
        expected_slices (int): 预计切片数量
    """
    
    def __init__(
        self,
        id: str,
        raw_data: np.ndarray,
        expected_slices: int,
        band_type: Optional[str] = None,
        is_valid: bool = False
    ):
        """初始化信号数据实体
        
        Args:
            id: 信号数据唯一标识
            raw_data: 原始数据数组
            expected_slices: 预计切片数量
            band_type: 频段类型，默认为None
            is_valid: 数据是否有效，默认为False
        """
        self.id = id
        self.raw_data = raw_data
        self.band_type = band_type
        self.is_valid = is_valid
        self.expected_slices = expected_slices
        
    @property
    def data_count(self) -> int:
        """获取数据点数量"""
        return len(self.raw_data) if self.raw_data is not None else 0
    
    @property
    def memory_size(self) -> int:
        """获取信号数据占用的内存大小（字节）"""
        return self.raw_data.nbytes if self.raw_data is not None else 0
    
    def copy(self) -> 'SignalData':
        """创建信号数据的深拷贝
        
        Returns:
            SignalData: 信号数据的深拷贝
        """
        return SignalData(
            id=self.id,
            raw_data=np.copy(self.raw_data) if self.raw_data is not None else None,
            expected_slices=self.expected_slices,
            band_type=self.band_type,
            is_valid=self.is_valid
        )
        
    def __str__(self) -> str:
        """返回实体的字符串表示"""
        return (
            f"SignalData(id={self.id}, "
            f"data_count={self.data_count}, "
            f"band_type={self.band_type}, "
            f"is_valid={self.is_valid}, "
            f"expected_slices={self.expected_slices})"
        )

class SignalSlice:
    """雷达信号切片实体类
    
    表示一个时间窗口内的雷达信号数据切片。
    
    Attributes:
        id (str): 切片唯一标识
        parent_signal_id (str): 所属原始信号ID
        slice_index (int): 切片序号
        time_range (TimeRange): 时间范围
        data (np.ndarray): 切片数据数组
        metadata (dict): 切片元数据
    """
    
    def __init__(
        self,
        id: str,
        parent_signal_id: str,
        slice_index: int,
        time_range: TimeRange,
        data: np.ndarray,
        metadata: Optional[dict] = None
    ):
        """初始化信号切片实体
        
        Args:
            id: 切片唯一标识
            parent_signal_id: 所属原始信号ID
            slice_index: 切片序号
            time_range: 时间范围
            data: 切片数据数组
            metadata: 切片元数据，默认为None
        """
        self.id = id
        self.parent_signal_id = parent_signal_id
        self.slice_index = slice_index
        self.time_range = time_range
        self.data = data
        self.metadata = metadata or {}
        
    @property
    def is_empty(self) -> bool:
        """判断切片是否为空"""
        return len(self.data) == 0 if self.data is not None else True
    
    @property
    def point_count(self) -> int:
        """获取切片中的数据点数量"""
        return len(self.data) if self.data is not None else 0
    
    @property
    def memory_size(self) -> int:
        """获取切片数据占用的内存大小（字节）"""
        return self.data.nbytes if self.data is not None else 0
    
    def copy(self) -> 'SignalSlice':
        """创建切片数据的深拷贝"""
        return SignalSlice(
            id=self.id,
            parent_signal_id=self.parent_signal_id,
            slice_index=self.slice_index,
            time_range=self.time_range,
            data=np.copy(self.data) if self.data is not None else None,
            metadata=self.metadata.copy() if self.metadata else None
        )
    
    def get_statistics(self) -> dict:
        """获取切片的统计信息
        
        Returns:
            dict: 包含切片的各种统计信息
        """
        if self.is_empty:
            return {
                'is_empty': True,
                'point_count': 0,
                'time_range': None,
                'memory_size': 0
            }
            
        return {
            'is_empty': False,
            'point_count': self.point_count,
            'time_range': {
                'start': self.time_range.start_time,
                'end': self.time_range.end_time,
                'duration': self.time_range.duration()
            },
            'memory_size': self.memory_size
        }
    
    def __str__(self) -> str:
        """返回切片的字符串表示"""
        return (
            f"SignalSlice(id={self.id}, "
            f"parent_signal_id={self.parent_signal_id}, "
            f"slice_index={self.slice_index}, "
            f"point_count={self.point_count}, "
            f"time_range=[{self.time_range.start_time}, {self.time_range.end_time}])"
        )
