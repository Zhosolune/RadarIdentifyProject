"""识别结果实体统一导入入口

本模块作为识别结果相关实体类的统一导入入口，重新导出所有实体类。
这样的设计保持了向后兼容性，现有代码无需修改导入路径。

重构后的实体文件组织：
- cluster_result.py: 聚类结果相关实体（ClusterResult, UnclusteredPulseData）
- recognition_result.py: 识别结果实体（RecognitionResult）
- feature_result.py: 特征和脉冲结果实体（Feature, SavedPulseResult）
"""

# 导入聚类结果相关实体
from radar_system.domain.recognition.entities.cluster_result import (
    ClusterResult,
    UnclusteredPulseData
)

# 导入识别结果实体
from radar_system.domain.recognition.entities.recognition_result import (
    RecognitionResult
)

# 导入特征和脉冲结果实体
from radar_system.domain.recognition.entities.feature_result import (
    Feature,
    SavedPulseResult
)

# 声明公开的API
__all__ = [
    'ClusterResult',
    'UnclusteredPulseData', 
    'RecognitionResult',
    'Feature',
    'SavedPulseResult'
]
