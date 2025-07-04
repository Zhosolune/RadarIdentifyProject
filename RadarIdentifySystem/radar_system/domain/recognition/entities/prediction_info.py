"""预测信息值对象模块

本模块定义了预测相关的值对象，用于封装神经网络预测结果。
"""

from dataclasses import dataclass
from typing import Dict, Optional
from .enums import PredictionLabel


@dataclass(frozen=True)
class PredictionInfo:
    """预测信息值对象
    
    封装神经网络预测的结果信息，包括预测标签、置信度和详细的置信度分布。
    
    Attributes:
        label (PredictionLabel): 预测的标签
        confidence (float): 预测的置信度 (0.0-1.0)
        confidence_distribution (Dict[int, float]): 各标签的置信度分布
        prediction_type (str): 预测类型 ('PA' 或 'DTOA')
    """
    label: PredictionLabel
    confidence: float
    confidence_distribution: Dict[int, float]
    prediction_type: str
    
    def __post_init__(self):
        """验证预测信息的有效性"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"置信度必须在0.0-1.0之间，当前值: {self.confidence}")
        
        if self.prediction_type not in ['PA', 'DTOA']:
            raise ValueError(f"预测类型必须是'PA'或'DTOA'，当前值: {self.prediction_type}")
        
        # 验证置信度分布的总和应该接近1.0
        if self.confidence_distribution:
            total_confidence = sum(self.confidence_distribution.values())
            if not 0.95 <= total_confidence <= 1.05:  # 允许小的浮点误差
                raise ValueError(f"置信度分布总和应该接近1.0，当前值: {total_confidence}")
    
    @property
    def is_high_confidence(self) -> bool:
        """判断是否为高置信度预测"""
        return self.confidence >= 0.8
    
    @property
    def is_low_confidence(self) -> bool:
        """判断是否为低置信度预测"""
        return self.confidence < 0.5
    
    @property
    def label_name(self) -> str:
        """获取标签的显示名称"""
        return self.label.display_name
    
    def get_top_n_predictions(self, n: int = 3) -> list:
        """获取置信度最高的前N个预测结果
        
        Args:
            n: 返回的预测结果数量
            
        Returns:
            list: 包含(标签值, 置信度)元组的列表，按置信度降序排列
        """
        if not self.confidence_distribution:
            return [(self.label.value, self.confidence)]
        
        sorted_predictions = sorted(
            self.confidence_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_predictions[:n]
    
    def to_dict(self) -> Dict:
        """转换为字典格式
        
        Returns:
            Dict: 包含预测信息的字典
        """
        return {
            'label': self.label.value,
            'label_name': self.label_name,
            'confidence': self.confidence,
            'confidence_distribution': self.confidence_distribution,
            'prediction_type': self.prediction_type,
            'is_high_confidence': self.is_high_confidence,
            'is_low_confidence': self.is_low_confidence
        }
    
    @classmethod
    def create_pa_prediction(cls, label_value: int, confidence: float, 
                           confidence_distribution: Optional[Dict[int, float]] = None) -> 'PredictionInfo':
        """创建PA预测信息
        
        Args:
            label_value: PA标签值 (0-5)
            confidence: 置信度
            confidence_distribution: 置信度分布，可选
            
        Returns:
            PredictionInfo: PA预测信息实例
        """
        # 根据标签值获取对应的枚举
        pa_labels = PredictionLabel.get_pa_labels()
        if 0 <= label_value < len(pa_labels):
            label = pa_labels[label_value]
        else:
            raise ValueError(f"无效的PA标签值: {label_value}")
        
        return cls(
            label=label,
            confidence=confidence,
            confidence_distribution=confidence_distribution or {label_value: confidence},
            prediction_type='PA'
        )
    
    @classmethod
    def create_dtoa_prediction(cls, label_value: int, confidence: float,
                             confidence_distribution: Optional[Dict[int, float]] = None) -> 'PredictionInfo':
        """创建DTOA预测信息
        
        Args:
            label_value: DTOA标签值 (0-4)
            confidence: 置信度
            confidence_distribution: 置信度分布，可选
            
        Returns:
            PredictionInfo: DTOA预测信息实例
        """
        # 根据标签值获取对应的枚举
        dtoa_labels = PredictionLabel.get_dtoa_labels()
        if 0 <= label_value < len(dtoa_labels):
            label = dtoa_labels[label_value]
        else:
            raise ValueError(f"无效的DTOA标签值: {label_value}")
        
        return cls(
            label=label,
            confidence=confidence,
            confidence_distribution=confidence_distribution or {label_value: confidence},
            prediction_type='DTOA'
        )


@dataclass(frozen=True)
class JointPrediction:
    """联合预测结果值对象
    
    封装PA和DTOA的联合预测结果。
    
    Attributes:
        pa_prediction (PredictionInfo): PA预测信息
        dtoa_prediction (PredictionInfo): DTOA预测信息
        joint_probability (float): 联合概率
        pa_weight (float): PA权重
        dtoa_weight (float): DTOA权重
    """
    pa_prediction: PredictionInfo
    dtoa_prediction: PredictionInfo
    joint_probability: float
    pa_weight: float = 1.0
    dtoa_weight: float = 1.0
    
    def __post_init__(self):
        """验证联合预测的有效性"""
        if not 0.0 <= self.joint_probability <= 1.0:
            raise ValueError(f"联合概率必须在0.0-1.0之间，当前值: {self.joint_probability}")
        
        if self.pa_weight < 0 or self.dtoa_weight < 0:
            raise ValueError("权重值不能为负数")
    
    @property
    def is_high_confidence(self) -> bool:
        """判断联合预测是否为高置信度"""
        return self.joint_probability >= 0.7
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'pa_prediction': self.pa_prediction.to_dict(),
            'dtoa_prediction': self.dtoa_prediction.to_dict(),
            'joint_probability': self.joint_probability,
            'pa_weight': self.pa_weight,
            'dtoa_weight': self.dtoa_weight,
            'is_high_confidence': self.is_high_confidence
        }
