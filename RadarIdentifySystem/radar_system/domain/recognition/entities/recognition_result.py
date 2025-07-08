"""识别结果实体模块

本模块定义了雷达信号识别结果相关的实体类。
该实体存储和管理单个聚类的识别结果信息，包括预测标签、置信度等。
"""
from typing import Dict
import numpy as np


class RecognitionResult:
    """识别结果实体类
    
    存储和管理单个聚类的识别结果信息。
    """
    def __init__(self,
                 dim: str,
                 dim_result_index: int,
                 total_result_index: int,
                 result_data: np.ndarray,
                 image_paths: Dict[str, str],
                 prediction: Dict[str, float]):
        """初始化识别结果
        
        Args:
            dim: 识别维度（CF/PW）
            dim_result_index: 当前维度下的识别结果索引
            total_result_index: 总识别结果索引
            result_data: 识别数据
            image_paths: 图像路径字典
            prediction: 预测信息字典，包含以下键值对：
                - pa_label: PA特征标签
                - pa_conf: PA特征置信度
                - dtoa_label: DTOA特征标签
                - dtoa_conf: DTOA特征置信度
                - joint_prob: 联合置信度
        """
        self.dim = dim
        self.dim_result_index = dim_result_index
        self.total_result_index = total_result_index
        self.result_data = result_data
        self.image_paths = image_paths
        
        # 验证prediction字典的完整性
        required_keys = {'pa_label', 'pa_conf', 'dtoa_label', 'dtoa_conf', 'joint_prob'}
        if not all(key in prediction for key in required_keys):
            raise ValueError("prediction字典缺少必要的键值对")
        self.prediction = prediction

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'dim': self.dim,
            'dim_result_index': self.dim_result_index,
            'total_result_index': self.total_result_index,
            'result_data': self.result_data,
            'image_paths': self.image_paths,
            'prediction': {
                'pa_label': self.prediction['pa_label'],
                'pa_conf': self.prediction['pa_conf'],
                'dtoa_label': self.prediction['dtoa_label'],
                'dtoa_conf': self.prediction['dtoa_conf'],
                'joint_prob': self.prediction['joint_prob']
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RecognitionResult':
        """从字典创建识别结果实例"""
        return cls(
            dim=data['dim'],
            dim_result_index=data['dim_result_index'],
            total_result_index=data['total_result_index'],
            result_data=data['result_data'],
            image_paths=data['image_paths'],
            prediction={
                'pa_label': data['prediction']['pa_label'],
                'pa_conf': data['prediction']['pa_conf'],
                'dtoa_label': data['prediction']['dtoa_label'],
                'dtoa_conf': data['prediction']['dtoa_conf'],
                'joint_prob': data['prediction']['joint_prob']
            }
        )
