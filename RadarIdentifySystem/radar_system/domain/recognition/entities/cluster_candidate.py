"""聚类候选实体模块

本模块定义了聚类候选实体，表示聚类处理过程中的候选聚类。
对应业务流程中的A、B、E、F状态。
"""

import uuid
from typing import Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

from .enums import ClusterStatus, DimensionType
from radar_system.domain.signal.entities.signal import TimeRange


class ClusterCandidate:
    """聚类候选实体
    
    表示聚类处理过程中的候选聚类，统一表示业务流程中的：
    - A状态：CF维度有效聚类
    - B状态：CF维度无效聚类  
    - E状态：PW维度有效聚类
    - F状态：PW维度无效聚类
    
    Attributes:
        cluster_id (str): 聚类唯一标识
        cluster_data (np.ndarray): 聚类中的数据点
        dimension_type (DimensionType): 维度类型
        cluster_index (int): 聚类编号
        slice_index (int): 所属切片索引
        status (ClusterStatus): 聚类状态
        time_range (TimeRange): 时间范围
        metadata (dict): 聚类元数据
        created_at (datetime): 创建时间
    """
    
    def __init__(
        self,
        cluster_data: np.ndarray,
        dimension_type: DimensionType,
        cluster_index: int,
        slice_index: int,
        status: ClusterStatus,
        time_range: TimeRange,
        cluster_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化聚类候选实体
        
        Args:
            cluster_data: 聚类中的数据点
            dimension_type: 维度类型
            cluster_index: 聚类编号
            slice_index: 所属切片索引
            status: 聚类状态
            time_range: 时间范围
            cluster_id: 聚类唯一标识，默认自动生成
            metadata: 聚类元数据，默认为空字典
        """
        self.cluster_id = cluster_id or str(uuid.uuid4())
        self.cluster_data = cluster_data
        self.dimension_type = dimension_type
        self.cluster_index = cluster_index
        self.slice_index = slice_index
        self.status = status
        self.time_range = time_range
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        
        # 验证数据有效性
        self._validate()
    
    def _validate(self):
        """验证聚类候选的数据有效性"""
        if self.cluster_data is None or len(self.cluster_data) == 0:
            raise ValueError("聚类数据不能为空")
        
        if self.cluster_index < 0:
            raise ValueError(f"聚类编号不能为负数，当前值: {self.cluster_index}")
        
        if self.slice_index < 0:
            raise ValueError(f"切片索引不能为负数，当前值: {self.slice_index}")
    
    @property
    def is_valid(self) -> bool:
        """判断聚类是否有效"""
        return self.status == ClusterStatus.VALID
    
    @property
    def point_count(self) -> int:
        """获取聚类中的数据点数量"""
        return len(self.cluster_data) if self.cluster_data is not None else 0
    
    @property
    def memory_size(self) -> int:
        """获取聚类数据占用的内存大小（字节）"""
        return self.cluster_data.nbytes if self.cluster_data is not None else 0
    
    @property
    def business_state_code(self) -> str:
        """获取业务状态代码
        
        根据维度类型和状态返回对应的业务状态代码：
        - CF + VALID = A
        - CF + INVALID = B
        - PW + VALID = E
        - PW + INVALID = F
        """
        state_map = {
            (DimensionType.CF, ClusterStatus.VALID): 'A',
            (DimensionType.CF, ClusterStatus.INVALID): 'B',
            (DimensionType.PW, ClusterStatus.VALID): 'E',
            (DimensionType.PW, ClusterStatus.INVALID): 'F'
        }
        return state_map.get((self.dimension_type, self.status), 'UNKNOWN')
    
    def get_image_data(self) -> Dict[str, Any]:
        """获取用于图像生成的数据
        
        Returns:
            Dict: 包含图像生成所需的数据和元数据
        """
        return {
            'data': self.cluster_data,
            'dimension_type': self.dimension_type.value,
            'cluster_index': self.cluster_index,
            'slice_index': self.slice_index,
            'time_range': {
                'start': self.time_range.start_time,
                'end': self.time_range.end_time
            },
            'metadata': self.metadata
        }
    
    def get_dimension_data(self) -> np.ndarray:
        """获取指定维度的数据
        
        Returns:
            np.ndarray: 指定维度的数据列
        """
        if self.cluster_data is None or len(self.cluster_data) == 0:
            return np.array([])
        
        column_index = self.dimension_type.data_column_index
        if column_index < self.cluster_data.shape[1]:
            return self.cluster_data[:, column_index]
        else:
            raise ValueError(f"数据维度不足，无法获取{self.dimension_type.value}维度数据")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取聚类的统计信息
        
        Returns:
            Dict: 包含聚类的各种统计信息
        """
        if self.point_count == 0:
            return {
                'cluster_id': self.cluster_id,
                'point_count': 0,
                'dimension_type': self.dimension_type.value,
                'status': self.status.value,
                'business_state': self.business_state_code,
                'is_empty': True
            }
        
        dimension_data = self.get_dimension_data()
        
        return {
            'cluster_id': self.cluster_id,
            'point_count': self.point_count,
            'dimension_type': self.dimension_type.value,
            'status': self.status.value,
            'business_state': self.business_state_code,
            'cluster_index': self.cluster_index,
            'slice_index': self.slice_index,
            'time_range': {
                'start': self.time_range.start_time,
                'end': self.time_range.end_time,
                'duration': self.time_range.duration()
            },
            'dimension_stats': {
                'min': float(np.min(dimension_data)),
                'max': float(np.max(dimension_data)),
                'mean': float(np.mean(dimension_data)),
                'std': float(np.std(dimension_data))
            },
            'memory_size': self.memory_size,
            'created_at': self.created_at.isoformat(),
            'is_empty': False
        }
    
    def copy(self) -> 'ClusterCandidate':
        """创建聚类候选的深拷贝
        
        Returns:
            ClusterCandidate: 聚类候选的深拷贝
        """
        return ClusterCandidate(
            cluster_data=np.copy(self.cluster_data) if self.cluster_data is not None else None,
            dimension_type=self.dimension_type,
            cluster_index=self.cluster_index,
            slice_index=self.slice_index,
            status=self.status,
            time_range=self.time_range,
            cluster_id=self.cluster_id,  # 保持相同的ID
            metadata=self.metadata.copy() if self.metadata else None
        )
    
    def __str__(self) -> str:
        """返回聚类候选的字符串表示"""
        return (
            f"ClusterCandidate(id={self.cluster_id[:8]}..., "
            f"dimension={self.dimension_type.value}, "
            f"status={self.status.value}, "
            f"business_state={self.business_state_code}, "
            f"points={self.point_count}, "
            f"cluster_idx={self.cluster_index}, "
            f"slice_idx={self.slice_index})"
        )
    
    def __repr__(self) -> str:
        """返回聚类候选的详细表示"""
        return self.__str__()
