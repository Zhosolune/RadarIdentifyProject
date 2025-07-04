"""识别参数值对象模块

本模块定义了识别功能相关的参数值对象，用于封装识别过程中的各种配置参数。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ClusteringParams:
    """聚类参数值对象
    
    封装DBSCAN聚类算法的参数配置。
    
    Attributes:
        epsilon_cf (float): CF维度的邻域半径
        epsilon_pw (float): PW维度的邻域半径
        min_pts (int): 形成聚类的最小点数
    """
    epsilon_cf: float
    epsilon_pw: float
    min_pts: int
    
    def __post_init__(self):
        """验证聚类参数的有效性"""
        if self.epsilon_cf <= 0:
            raise ValueError(f"CF维度邻域半径必须大于0，当前值: {self.epsilon_cf}")
        
        if self.epsilon_pw <= 0:
            raise ValueError(f"PW维度邻域半径必须大于0，当前值: {self.epsilon_pw}")
        
        if self.min_pts < 1:
            raise ValueError(f"最小点数必须大于等于1，当前值: {self.min_pts}")
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'epsilon_cf': self.epsilon_cf,
            'epsilon_pw': self.epsilon_pw,
            'min_pts': self.min_pts
        }
    
    @classmethod
    def create_default(cls) -> 'ClusteringParams':
        """创建默认的聚类参数"""
        return cls(
            epsilon_cf=2.0,
            epsilon_pw=0.2,
            min_pts=1
        )


@dataclass(frozen=True)
class RecognitionParams:
    """识别参数值对象
    
    封装整个识别流程的参数配置。
    
    Attributes:
        clustering_params (ClusteringParams): 聚类参数
        pa_weight (float): PA预测权重
        dtoa_weight (float): DTOA预测权重
        threshold (float): 联合判别门限
        enable_parameter_extraction (bool): 是否启用参数提取
        max_clusters_per_dimension (Optional[int]): 每个维度的最大聚类数量限制
    """
    clustering_params: ClusteringParams
    pa_weight: float = 1.0
    dtoa_weight: float = 1.0
    threshold: float = 0.7
    enable_parameter_extraction: bool = True
    max_clusters_per_dimension: Optional[int] = None
    
    def __post_init__(self):
        """验证识别参数的有效性"""
        if self.pa_weight < 0:
            raise ValueError(f"PA权重不能为负数，当前值: {self.pa_weight}")
        
        if self.dtoa_weight < 0:
            raise ValueError(f"DTOA权重不能为负数，当前值: {self.dtoa_weight}")
        
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(f"判别门限必须在0.0-1.0之间，当前值: {self.threshold}")
        
        if self.max_clusters_per_dimension is not None and self.max_clusters_per_dimension < 1:
            raise ValueError(f"最大聚类数量必须大于等于1，当前值: {self.max_clusters_per_dimension}")
    
    @property
    def total_weight(self) -> float:
        """获取总权重"""
        return self.pa_weight + self.dtoa_weight
    
    @property
    def normalized_pa_weight(self) -> float:
        """获取归一化的PA权重"""
        total = self.total_weight
        return self.pa_weight / total if total > 0 else 0.5
    
    @property
    def normalized_dtoa_weight(self) -> float:
        """获取归一化的DTOA权重"""
        total = self.total_weight
        return self.dtoa_weight / total if total > 0 else 0.5
    
    def calculate_joint_probability(self, pa_confidence: float, dtoa_confidence: float) -> float:
        """计算联合概率
        
        Args:
            pa_confidence: PA预测置信度
            dtoa_confidence: DTOA预测置信度
            
        Returns:
            float: 联合概率
        """
        if self.total_weight == 0:
            return 0.0
        
        weighted_sum = (self.pa_weight * pa_confidence + 
                       self.dtoa_weight * dtoa_confidence)
        return weighted_sum / self.total_weight
    
    def is_above_threshold(self, joint_probability: float) -> bool:
        """判断联合概率是否超过门限
        
        Args:
            joint_probability: 联合概率
            
        Returns:
            bool: 是否超过门限
        """
        return joint_probability >= self.threshold
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'clustering_params': self.clustering_params.to_dict(),
            'pa_weight': self.pa_weight,
            'dtoa_weight': self.dtoa_weight,
            'threshold': self.threshold,
            'enable_parameter_extraction': self.enable_parameter_extraction,
            'max_clusters_per_dimension': self.max_clusters_per_dimension,
            'normalized_pa_weight': self.normalized_pa_weight,
            'normalized_dtoa_weight': self.normalized_dtoa_weight
        }
    
    @classmethod
    def create_default(cls) -> 'RecognitionParams':
        """创建默认的识别参数"""
        return cls(
            clustering_params=ClusteringParams.create_default(),
            pa_weight=1.0,
            dtoa_weight=1.0,
            threshold=0.7,
            enable_parameter_extraction=True,
            max_clusters_per_dimension=None
        )
    
    @classmethod
    def from_dict(cls, params_dict: dict) -> 'RecognitionParams':
        """从字典创建识别参数
        
        Args:
            params_dict: 参数字典
            
        Returns:
            RecognitionParams: 识别参数实例
        """
        clustering_params = ClusteringParams(
            epsilon_cf=params_dict.get('epsilon_cf', 2.0),
            epsilon_pw=params_dict.get('epsilon_pw', 0.2),
            min_pts=params_dict.get('min_pts', 1)
        )
        
        return cls(
            clustering_params=clustering_params,
            pa_weight=params_dict.get('pa_weight', 1.0),
            dtoa_weight=params_dict.get('dtoa_weight', 1.0),
            threshold=params_dict.get('threshold', 0.7),
            enable_parameter_extraction=params_dict.get('enable_parameter_extraction', True),
            max_clusters_per_dimension=params_dict.get('max_clusters_per_dimension')
        )
