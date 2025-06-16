from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
from abc import ABC, abstractmethod

class Feature:
    """雷达信号特征基类
    
    定义雷达信号特征的基本属性和行为。
    """
    def __init__(self, 
                 CF: List[float],
                 PW: List[float],
                 PA: List[float],
                 DTOA: List[float],
                 DOA: float):
        """初始化特征参数
        
        Args:
            CF: 载频列表，单位MHz
            PW: 脉宽列表，单位us
            PA: 幅度列表，单位dB
            DTOA: 一级差列表，单位us
            DOA: 到达角，单位度
        """
        self.CF = CF
        self.PW = PW
        self.PA = PA
        self.DTOA = DTOA
        self.DOA = DOA

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'CF': self.CF,
            'PW': self.PW,
            'PA': self.PA,
            'DTOA': self.DTOA,
            'DOA': self.DOA
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Feature':
        """从字典创建特征实例"""
        return cls(
            CF=data['CF'],
            PW=data['PW'],
            PA=data['PA'],
            DTOA=data['DTOA'],
            DOA=data['DOA']
        )

class ClusterResult:
    """聚类结果实体类
    
    存储和管理单个聚类的结果信息。
    """
    def __init__(self,
                 cluster_data: np.ndarray,
                 slice_index: int,
                 cluster_index: int,
                 dim_name: str,
                 time_ranges: List[float]):
        """初始化聚类结果
        
        Args:
            cluster_data: 聚类数据
            slice_index: 切片索引
            cluster_index: 聚类结果索引
            dim_name: 聚类维度名称（CF/PW）
            time_ranges: 时间范围[start_time, end_time]
        """
        self.cluster_data = cluster_data
        self.slice_index = slice_index
        self.cluster_index = cluster_index
        self.dim_name = dim_name
        self.time_ranges = time_ranges
    
    @classmethod
    def get_cluster_data(cls, data: Dict) -> np.ndarray:
        """获取聚类数据"""
        return data['cluster_data']

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'cluster_data': self.cluster_data,
            'slice_index': self.slice_index,
            'cluster_index': self.cluster_index,
            'dim_name': self.dim_name,
            'time_ranges': self.time_ranges
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ClusterResult':
        """从字典创建聚类结果实例"""
        return cls(
            cluster_data=data['cluster_data'],
            slice_index=data['slice_index'],
            cluster_index=data['cluster_index'],
            dim_name=data['dim_name'],
            time_ranges=data['time_ranges']
        )

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
