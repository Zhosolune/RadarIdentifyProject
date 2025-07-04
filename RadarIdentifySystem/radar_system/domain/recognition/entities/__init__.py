"""识别领域实体模块

本模块包含识别功能相关的所有领域实体类和枚举定义。
"""

from .enums import (
    ProcessingStage,
    ClusterStatus,
    RecognitionStatus,
    DimensionType
)

from .cluster_candidate import ClusterCandidate
from .recognition_result import RecognitionResult
from .recognition_session import RecognitionSession
from .prediction_info import PredictionInfo, JointPrediction
from .recognition_params import RecognitionParams, ClusteringParams

__all__ = [
    # 枚举
    'ProcessingStage',
    'ClusterStatus',
    'RecognitionStatus',
    'DimensionType',

    # 实体
    'ClusterCandidate',
    'RecognitionResult',
    'RecognitionSession',
    'PredictionInfo',
    'JointPrediction',
    'RecognitionParams',
    'ClusteringParams'
]