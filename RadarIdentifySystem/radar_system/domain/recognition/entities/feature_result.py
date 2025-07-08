"""特征和脉冲结果实体模块

本模块定义了雷达信号特征和脉冲结果相关的实体类。
包括信号特征基类和保存的脉冲结果实体。
"""
from dataclasses import dataclass
from typing import List, Dict
import numpy as np


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


@dataclass
class SavedPulseResult:
    """保存的脉冲结果实体类
    
    用于保存雷达信号识别过程中有价值算法节点的脉冲数据。
    该实体存储单个脉冲的完整参数信息，包括信号特征、分类信息和处理元数据。
    
    Attributes:
        CF (float): 载频，单位MHz
        PW (float): 脉宽，单位μs
        PA (float): 幅度，单位dB
        DTOA (float): 一级差，单位μs
        DOA (float): 方位角，单位度
        category_index (int): 所属类别索引
        pulse_index (int): 脉冲索引
        clustering_dimension (str): 聚类维度，值为"CF"或"PW"
        sequence_number (int): 序号
    """
    CF: float
    PW: float
    PA: float
    DTOA: float
    DOA: float
    category_index: int
    pulse_index: int
    clustering_dimension: str
    sequence_number: int
    
    def __post_init__(self):
        """初始化后验证数据有效性
        
        Raises:
            ValueError: 当数据不符合预期格式或范围时抛出异常
        """
        # 验证聚类维度
        if self.clustering_dimension not in ["CF", "PW"]:
            raise ValueError(f"clustering_dimension必须为'CF'或'PW'，当前值: {self.clustering_dimension}")
        
        # 验证索引和序号为非负整数
        if self.category_index < 0:
            raise ValueError(f"category_index必须为非负整数，当前值: {self.category_index}")
        if self.pulse_index < 0:
            raise ValueError(f"pulse_index必须为非负整数，当前值: {self.pulse_index}")
        if self.sequence_number < 0:
            raise ValueError(f"sequence_number必须为非负整数，当前值: {self.sequence_number}")
        
        # 验证信号参数范围（基本合理性检查）
        if self.CF <= 0:
            raise ValueError(f"CF载频必须为正数，当前值: {self.CF}")
        if self.PW <= 0:
            raise ValueError(f"PW脉宽必须为正数，当前值: {self.PW}")
        if not (0 <= self.DOA <= 360):
            raise ValueError(f"DOA方位角必须在0-360度范围内，当前值: {self.DOA}")
    
    def to_dict(self) -> Dict:
        """转换为字典格式
        
        将实体对象转换为字典格式，便于序列化和数据传输。
        
        Returns:
            Dict: 包含所有属性的字典
        """
        return {
            'CF': self.CF,
            'PW': self.PW,
            'PA': self.PA,
            'DTOA': self.DTOA,
            'DOA': self.DOA,
            'category_index': self.category_index,
            'pulse_index': self.pulse_index,
            'clustering_dimension': self.clustering_dimension,
            'sequence_number': self.sequence_number
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SavedPulseResult':
        """从字典创建SavedPulseResult实例
        
        从字典数据创建SavedPulseResult实体实例，支持数据反序列化。
        
        Args:
            data (Dict): 包含脉冲结果数据的字典，必须包含所有必需字段
        
        Returns:
            SavedPulseResult: 创建的实体实例
            
        Raises:
            KeyError: 当字典缺少必需字段时抛出异常
            ValueError: 当数据格式不正确时抛出异常
        """
        required_fields = [
            'CF', 'PW', 'PA', 'DTOA', 'DOA', 
            'category_index', 'pulse_index', 'clustering_dimension', 'sequence_number'
        ]
        
        # 检查必需字段
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise KeyError(f"字典缺少必需字段: {missing_fields}")
        
        return cls(
            CF=float(data['CF']),
            PW=float(data['PW']),
            PA=float(data['PA']),
            DTOA=float(data['DTOA']),
            DOA=float(data['DOA']),
            category_index=int(data['category_index']),
            pulse_index=int(data['pulse_index']),
            clustering_dimension=str(data['clustering_dimension']),
            sequence_number=int(data['sequence_number'])
        )

    def get_signal_parameters(self) -> Dict[str, float]:
        """获取信号参数

        提取并返回核心信号参数，便于信号处理算法使用。

        Returns:
            Dict[str, float]: 包含CF、PW、PA、DTOA、DOA的字典
        """
        return {
            'CF': self.CF,
            'PW': self.PW,
            'PA': self.PA,
            'DTOA': self.DTOA,
            'DOA': self.DOA
        }

    def get_metadata(self) -> Dict[str, any]:
        """获取元数据信息

        提取并返回处理相关的元数据信息。

        Returns:
            Dict[str, any]: 包含分类和处理信息的字典
        """
        return {
            'category_index': self.category_index,
            'pulse_index': self.pulse_index,
            'clustering_dimension': self.clustering_dimension,
            'sequence_number': self.sequence_number
        }

    def __str__(self) -> str:
        """字符串表示

        Returns:
            str: 脉冲结果的简洁字符串描述
        """
        return (f"SavedPulseResult(seq={self.sequence_number}, "
                f"CF={self.CF}MHz, PW={self.PW}μs, "
                f"dim={self.clustering_dimension}, cat={self.category_index})")

    def __repr__(self) -> str:
        """详细字符串表示

        Returns:
            str: 脉冲结果的详细字符串描述
        """
        return (f"SavedPulseResult(CF={self.CF}, PW={self.PW}, PA={self.PA}, "
                f"DTOA={self.DTOA}, DOA={self.DOA}, category_index={self.category_index}, "
                f"pulse_index={self.pulse_index}, clustering_dimension='{self.clustering_dimension}', "
                f"sequence_number={self.sequence_number})")
