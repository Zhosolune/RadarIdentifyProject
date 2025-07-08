"""聚类结果实体模块

本模块定义了聚类处理相关的实体类，包括聚类结果和未聚类脉冲数据。
这些实体支持增强式管道架构中的CF和PW两阶段聚类数据流转。
"""
from dataclasses import dataclass
from typing import Dict
import numpy as np

from radar_system.domain.signal.entities.signal import TimeRange


class ClusterResult:
    """聚类结果实体类
    
    存储和管理单个聚类的结果信息。
    """
    def __init__(self,
                 cluster_data: np.ndarray,
                 slice_index: int,
                 cluster_index: int,
                 dim_name: str,
                 time_ranges: TimeRange,
                 dimension_category_index: int = 0):
        """初始化聚类结果
        
        Args:
            cluster_data: 聚类数据
            slice_index: 切片索引
            cluster_index: 聚类结果索引
            dim_name: 聚类维度名称（CF/PW）
            time_ranges: 时间范围对象，继承自SignalSlice切片数据实体，
                        在聚类过程中保持不变，主要用于后续的图像绘制功能
            dimension_category_index: 当前维度的类别索引，默认为0
            
        Raises:
            ValueError: 当参数不符合预期格式或范围时抛出异常
        """
        # 验证聚类维度
        if dim_name not in ["CF", "PW"]:
            raise ValueError(f"dim_name必须为'CF'或'PW'，当前值: {dim_name}")
        
        # 验证索引为非负整数
        if slice_index < 0:
            raise ValueError(f"slice_index必须为非负整数，当前值: {slice_index}")
        if cluster_index < 0:
            raise ValueError(f"cluster_index必须为非负整数，当前值: {cluster_index}")
        if dimension_category_index < 0:
            raise ValueError(f"dimension_category_index必须为非负整数，当前值: {dimension_category_index}")
        
        # 验证时间范围对象
        if not isinstance(time_ranges, TimeRange):
            raise ValueError(f"time_ranges必须为TimeRange对象，当前类型: {type(time_ranges)}")
        
        self.cluster_data = cluster_data
        self.slice_index = slice_index
        self.cluster_index = cluster_index
        self.dim_name = dim_name
        self.time_ranges = time_ranges
        self.dimension_category_index = dimension_category_index
    
    @classmethod
    def get_cluster_data(cls, data: Dict) -> np.ndarray:
        """获取聚类数据"""
        return data['cluster_data']

    def to_dict(self) -> Dict:
        """转换为字典格式
        
        Returns:
            Dict: 包含所有属性的字典
        """
        return {
            'cluster_data': self.cluster_data,
            'slice_index': self.slice_index,
            'cluster_index': self.cluster_index,
            'dim_name': self.dim_name,
            'time_ranges': {
                'start_time': self.time_ranges.start_time,
                'end_time': self.time_ranges.end_time
            },
            'dimension_category_index': self.dimension_category_index
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ClusterResult':
        """从字典创建聚类结果实例
        
        Args:
            data (Dict): 包含聚类结果数据的字典，必须包含所有必需字段
            
        Returns:
            ClusterResult: 创建的聚类结果实例
            
        Raises:
            KeyError: 当字典缺少必需字段时抛出异常
            ValueError: 当数据格式不正确时抛出异常
        """
        required_fields = ['cluster_data', 'slice_index', 'cluster_index', 'dim_name', 'time_ranges']
        
        # 检查必需字段
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise KeyError(f"字典缺少必需字段: {missing_fields}")
        
        # 处理时间范围数据
        time_ranges_data = data['time_ranges']
        if isinstance(time_ranges_data, dict):
            # 从字典创建TimeRange对象
            time_ranges = TimeRange(
                start_time=float(time_ranges_data['start_time']),
                end_time=float(time_ranges_data['end_time'])
            )
        elif isinstance(time_ranges_data, TimeRange):
            # 已经是TimeRange对象
            time_ranges = time_ranges_data
        else:
            raise ValueError(f"time_ranges数据格式不正确，期望dict或TimeRange，实际: {type(time_ranges_data)}")
        
        return cls(
            cluster_data=data['cluster_data'],
            slice_index=int(data['slice_index']),
            cluster_index=int(data['cluster_index']),
            dim_name=str(data['dim_name']),
            time_ranges=time_ranges,
            dimension_category_index=int(data.get('dimension_category_index', 0))
        )


@dataclass
class UnclusteredPulseData:
    """未聚类脉冲数据实体类
    
    用于存储聚类失败后的脉冲数据，该实体将用于下一维度的聚类处理。
    在增强式管道架构中，当某个维度的聚类处理无法对所有数据进行有效聚类时，
    未聚类的数据将通过此实体传递到下一个处理阶段。
    
    Attributes:
        pulse_data (np.ndarray): 未聚类成功的脉冲数据
        slice_index (int): 切片索引
        clustering_dimension (str): 当前聚类维度，值为"CF"或"PW"
        time_ranges (TimeRange): 时间范围对象，继承自SignalSlice切片数据实体，
                                在聚类过程中保持不变，主要用于后续的图像绘制功能
        successful_cluster_count (int): 已聚类成功的类别数量
    """
    pulse_data: np.ndarray
    slice_index: int
    clustering_dimension: str
    time_ranges: TimeRange
    successful_cluster_count: int
    
    def __post_init__(self):
        """初始化后验证数据有效性
        
        Raises:
            ValueError: 当数据不符合预期格式或范围时抛出异常
        """
        # 验证聚类维度
        if self.clustering_dimension not in ["CF", "PW"]:
            raise ValueError(f"clustering_dimension必须为'CF'或'PW'，当前值: {self.clustering_dimension}")
        
        # 验证索引和计数为非负整数
        if self.slice_index < 0:
            raise ValueError(f"slice_index必须为非负整数，当前值: {self.slice_index}")
        if self.successful_cluster_count < 0:
            raise ValueError(f"successful_cluster_count必须为非负整数，当前值: {self.successful_cluster_count}")
        
        # 验证时间范围对象
        if not isinstance(self.time_ranges, TimeRange):
            raise ValueError(f"time_ranges必须为TimeRange对象，当前类型: {type(self.time_ranges)}")
        
        # 验证脉冲数据不为空
        if self.pulse_data.size == 0:
            raise ValueError("pulse_data不能为空数组")
    
    def to_dict(self) -> Dict:
        """转换为字典格式

        将实体对象转换为字典格式，便于序列化和数据传输。

        Returns:
            Dict: 包含所有属性的字典
        """
        return {
            'pulse_data': self.pulse_data,
            'slice_index': self.slice_index,
            'clustering_dimension': self.clustering_dimension,
            'time_ranges': {
                'start_time': self.time_ranges.start_time,
                'end_time': self.time_ranges.end_time
            },
            'successful_cluster_count': self.successful_cluster_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UnclusteredPulseData':
        """从字典创建UnclusteredPulseData实例
        
        从字典数据创建UnclusteredPulseData实体实例，支持数据反序列化。
        
        Args:
            data (Dict): 包含未聚类脉冲数据的字典，必须包含所有必需字段
        
        Returns:
            UnclusteredPulseData: 创建的实体实例
            
        Raises:
            KeyError: 当字典缺少必需字段时抛出异常
            ValueError: 当数据格式不正确时抛出异常
        """
        required_fields = [
            'pulse_data', 'slice_index', 'clustering_dimension', 
            'time_ranges', 'successful_cluster_count'
        ]
        
        # 检查必需字段
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise KeyError(f"字典缺少必需字段: {missing_fields}")
        
        # 处理时间范围数据
        time_ranges_data = data['time_ranges']
        if isinstance(time_ranges_data, dict):
            # 从字典创建TimeRange对象
            time_ranges = TimeRange(
                start_time=float(time_ranges_data['start_time']),
                end_time=float(time_ranges_data['end_time'])
            )
        elif isinstance(time_ranges_data, TimeRange):
            # 已经是TimeRange对象
            time_ranges = time_ranges_data
        else:
            raise ValueError(f"time_ranges数据格式不正确，期望dict或TimeRange，实际: {type(time_ranges_data)}")

        return cls(
            pulse_data=np.array(data['pulse_data']),
            slice_index=int(data['slice_index']),
            clustering_dimension=str(data['clustering_dimension']),
            time_ranges=time_ranges,
            successful_cluster_count=int(data['successful_cluster_count'])
        )

    def get_pulse_count(self) -> int:
        """获取未聚类脉冲数量

        Returns:
            int: 未聚类的脉冲数量
        """
        return self.pulse_data.shape[0] if self.pulse_data.ndim > 1 else 1

    def get_time_duration(self) -> float:
        """获取时间范围持续时间

        Returns:
            float: 时间范围的持续时间
        """
        return self.time_ranges.duration()

    def is_ready_for_next_dimension(self) -> bool:
        """检查是否准备好进行下一维度聚类

        Returns:
            bool: 如果数据准备好进行下一维度聚类则返回True
        """
        return (self.pulse_data.size > 0 and
                self.clustering_dimension in ["CF", "PW"] and
                isinstance(self.time_ranges, TimeRange))

    def __str__(self) -> str:
        """字符串表示

        Returns:
            str: 未聚类脉冲数据的简洁字符串描述
        """
        return (f"UnclusteredPulseData(slice={self.slice_index}, "
                f"dim={self.clustering_dimension}, "
                f"pulses={self.get_pulse_count()}, "
                f"clustered={self.successful_cluster_count})")

    def __repr__(self) -> str:
        """详细字符串表示

        Returns:
            str: 未聚类脉冲数据的详细字符串描述
        """
        return (f"UnclusteredPulseData(pulse_data.shape={self.pulse_data.shape}, "
                f"slice_index={self.slice_index}, "
                f"clustering_dimension='{self.clustering_dimension}', "
                f"time_ranges={self.time_ranges}, "
                f"successful_cluster_count={self.successful_cluster_count})")
