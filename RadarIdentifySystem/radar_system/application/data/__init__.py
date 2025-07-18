"""Application层数据管理模块

本模块包含用于管理识别算法流程中数据状态的管理类。
遵循DDD架构原则，提供应用层的数据管理服务。

主要组件：
- AlgorithmDataPersistence: 算法流程数据持久化管理器
- SliceProcessingContext: 切片处理上下文管理器
"""

from .algorithm_data_persistence import AlgorithmDataPersistence
from .slice_processing_context import SliceProcessingContext

__all__ = [
    'AlgorithmDataPersistence',
    'SliceProcessingContext'
]
