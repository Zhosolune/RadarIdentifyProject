"""切片处理上下文管理器

管理当前切片在识别算法流程中各个节点的数据状态。
使用单例模式确保全局唯一实例，为算法流程提供统一的数据状态管理。

该类属于Application层，负责协调和管理算法流程中的数据状态，
不直接访问Infrastructure层，遵循DDD架构原则。
"""

import threading
from dataclasses import dataclass, field
from typing import Optional, List

from radar_system.domain.signal.entities.signal import SignalSlice
from radar_system.domain.recognition.entities.cluster_result import ClusterResult, UnclusteredPulseData
from radar_system.domain.recognition.entities.recognition_result import RecognitionResult
from radar_system.domain.recognition.entities.feature_result import Feature, SavedPulseResult


@dataclass
class SliceProcessingContext:
    """切片处理上下文管理器
    
    使用单例模式管理当前切片在算法流程中各个节点的数据状态。
    该类为识别算法流程提供统一的数据状态管理，确保数据在各个
    处理阶段之间的正确传递和状态维护。
    
    数据流程：
    1. 基础数据：当前处理的信号切片
    2. CF维度处理：聚类结果、识别结果、剩余数据
    3. PW维度处理：聚类结果、识别结果、剩余数据
    4. 结果数据：提取的特征、保存的脉冲结果
    
    生命周期：
    - 随应用程序启动创建
    - 在每个切片处理开始时重置状态
    - 随应用程序关闭时销毁
    """
    
    # 单例模式相关
    _instance: Optional['SliceProcessingContext'] = None
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _initialized: bool = field(default=False, init=False)
    
    # 基础数据
    current_slice: Optional[SignalSlice] = None
    
    # CF维度处理数据
    cf_cluster_results: List[ClusterResult] = field(default_factory=list)
    cf_unclustered_data: Optional[UnclusteredPulseData] = None
    cf_all_recognition_results: List[RecognitionResult] = field(default_factory=list)
    cf_successful_recognition_results: List[RecognitionResult] = field(default_factory=list)
    cf_remaining_data: Optional[UnclusteredPulseData] = None
    
    # PW维度处理数据
    pw_cluster_results: List[ClusterResult] = field(default_factory=list)
    pw_unclustered_data: Optional[UnclusteredPulseData] = None
    pw_all_recognition_results: List[RecognitionResult] = field(default_factory=list)
    pw_successful_recognition_results: List[RecognitionResult] = field(default_factory=list)
    pw_remaining_data: Optional[UnclusteredPulseData] = None
    
    # 结果数据
    extracted_features: List[Feature] = field(default_factory=list)
    valid_saved_pulse_results: List[SavedPulseResult] = field(default_factory=list)
    invalid_saved_pulse_results: List[SavedPulseResult] = field(default_factory=list)
    
    def __new__(cls) -> 'SliceProcessingContext':
        """线程安全的单例实现
        
        使用双重检查锁定模式确保在多线程环境下的单例安全性。
        
        Returns:
            SliceProcessingContext: 全局唯一的实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __post_init__(self):
        """初始化后处理
        
        确保单例实例只初始化一次，避免重复初始化导致的数据丢失。
        """
        if not self._initialized:
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'SliceProcessingContext':
        """获取单例实例
        
        提供显式的单例获取方法，便于代码的可读性和维护性。
        
        Returns:
            SliceProcessingContext: 全局唯一的实例
        """
        return cls()
    
    def reset_context(self) -> None:
        """重置上下文状态
        
        在开始处理新切片时调用，清空所有处理状态，
        为新的算法流程准备干净的数据环境。
        
        注意：该方法会清空所有数据状态，请谨慎使用。
        """
        # 基础数据重置
        self.current_slice = None
        
        # CF维度数据重置
        self.cf_cluster_results.clear()
        self.cf_unclustered_data = None
        self.cf_all_recognition_results.clear()
        self.cf_successful_recognition_results.clear()
        self.cf_remaining_data = None
        
        # PW维度数据重置
        self.pw_cluster_results.clear()
        self.pw_unclustered_data = None
        self.pw_all_recognition_results.clear()
        self.pw_successful_recognition_results.clear()
        self.pw_remaining_data = None
        
        # 结果数据重置
        self.extracted_features.clear()
        self.valid_saved_pulse_results.clear()
        self.invalid_saved_pulse_results.clear()
    
    def has_cf_processing_data(self) -> bool:
        """检查是否有CF维度处理数据
        
        Returns:
            bool: 如果有CF维度的聚类结果或识别结果则返回True
        """
        return (len(self.cf_cluster_results) > 0 or 
                len(self.cf_all_recognition_results) > 0)
    
    def has_pw_processing_data(self) -> bool:
        """检查是否有PW维度处理数据
        
        Returns:
            bool: 如果有PW维度的聚类结果或识别结果则返回True
        """
        return (len(self.pw_cluster_results) > 0 or 
                len(self.pw_all_recognition_results) > 0)
    
    def has_final_results(self) -> bool:
        """检查是否有最终结果数据
        
        Returns:
            bool: 如果有提取的特征或保存的脉冲结果则返回True
        """
        return (len(self.extracted_features) > 0 or 
                len(self.valid_saved_pulse_results) > 0 or
                len(self.invalid_saved_pulse_results) > 0)
    
    def get_total_recognition_results_count(self) -> int:
        """获取总识别结果数量
        
        Returns:
            int: CF和PW维度所有识别结果的总数量
        """
        return (len(self.cf_all_recognition_results) + 
                len(self.pw_all_recognition_results))
    
    def get_successful_recognition_results_count(self) -> int:
        """获取成功识别结果数量
        
        Returns:
            int: CF和PW维度成功识别结果的总数量
        """
        return (len(self.cf_successful_recognition_results) + 
                len(self.pw_successful_recognition_results))
