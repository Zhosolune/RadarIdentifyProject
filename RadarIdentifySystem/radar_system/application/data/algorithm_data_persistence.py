"""算法流程数据持久化管理器

管理整个识别算法流程的持久化存储数据。
使用单例模式确保全局唯一实例，为整个算法流程提供统一的数据持久化管理。

该类属于Application层，负责协调和管理算法流程中的持久化数据，
不直接访问Infrastructure层，遵循DDD架构原则。
"""

import threading
from dataclasses import dataclass, field
from typing import Optional, List

from .slice_processing_context import SliceProcessingContext


@dataclass
class AlgorithmDataPersistence:
    """算法流程数据持久化管理器
    
    使用单例模式管理整个识别算法流程的持久化存储数据。
    该类为识别算法流程提供统一的数据持久化管理，确保所有切片
    的处理上下文数据能够被正确存储和访问。
    
    数据结构：
    - 全局数据：List[SliceProcessingContext]，长度为切片数量
    - 每个元素对应一个切片的完整处理上下文
    
    使用场景：
    1. 存储每个切片的完整处理结果
    2. 提供跨切片的数据访问能力
    3. 支持算法流程的数据回溯和分析
    4. 为结果导出和保存提供数据源
    
    生命周期：
    - 随应用程序启动创建
    - 在信号切片处理开始时初始化数据结构
    - 在每个切片处理完成时保存上下文数据
    - 随应用程序关闭时销毁
    """
    
    # 单例模式相关
    _instance: Optional['AlgorithmDataPersistence'] = None
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _initialized: bool = field(default=False, init=False)
    
    # 全局持久化数据：所有切片的处理上下文
    all_slice_contexts: List[SliceProcessingContext] = field(default_factory=list)
    
    # 当前处理状态
    current_slice_index: int = -1
    total_slice_count: int = 0
    processing_completed: bool = False
    
    def __new__(cls) -> 'AlgorithmDataPersistence':
        """线程安全的单例实现
        
        使用双重检查锁定模式确保在多线程环境下的单例安全性。
        
        Returns:
            AlgorithmDataPersistence: 全局唯一的实例
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
    def get_instance(cls) -> 'AlgorithmDataPersistence':
        """获取单例实例
        
        提供显式的单例获取方法，便于代码的可读性和维护性。
        
        Returns:
            AlgorithmDataPersistence: 全局唯一的实例
        """
        return cls()
    
    def initialize_for_slices(self, slice_count: int) -> None:
        """为切片处理初始化数据结构
        
        在开始处理信号切片时调用，根据切片数量初始化数据结构。
        
        Args:
            slice_count: 总切片数量
        """
        self.total_slice_count = slice_count
        self.current_slice_index = -1
        self.processing_completed = False
        
        # 清空现有数据
        self.all_slice_contexts.clear()
        
        # 为每个切片创建独立的处理上下文
        for i in range(slice_count):
            # 注意：这里创建新的SliceProcessingContext实例，而不是使用单例
            # 因为每个切片需要独立的上下文数据
            slice_context = SliceProcessingContext.__new__(SliceProcessingContext)
            slice_context.__post_init__()
            self.all_slice_contexts.append(slice_context)
    
    def get_slice_context(self, slice_index: int) -> Optional[SliceProcessingContext]:
        """获取指定切片的处理上下文
        
        Args:
            slice_index: 切片索引（从0开始）
            
        Returns:
            Optional[SliceProcessingContext]: 切片处理上下文，如果索引无效则返回None
        """
        if 0 <= slice_index < len(self.all_slice_contexts):
            return self.all_slice_contexts[slice_index]
        return None
    
    def get_current_slice_context(self) -> Optional[SliceProcessingContext]:
        """获取当前切片的处理上下文
        
        Returns:
            Optional[SliceProcessingContext]: 当前切片处理上下文，如果没有当前切片则返回None
        """
        if self.current_slice_index >= 0:
            return self.get_slice_context(self.current_slice_index)
        return None
    
    def set_current_slice_index(self, slice_index: int) -> bool:
        """设置当前处理的切片索引
        
        Args:
            slice_index: 切片索引（从0开始）
            
        Returns:
            bool: 设置成功返回True，索引无效返回False
        """
        if 0 <= slice_index < len(self.all_slice_contexts):
            self.current_slice_index = slice_index
            return True
        return False
    
    def move_to_next_slice(self) -> bool:
        """移动到下一个切片
        
        Returns:
            bool: 成功移动到下一个切片返回True，已到达最后一个切片返回False
        """
        if self.current_slice_index < len(self.all_slice_contexts) - 1:
            self.current_slice_index += 1
            return True
        return False
    
    def is_processing_completed(self) -> bool:
        """检查是否完成了所有切片的处理
        
        Returns:
            bool: 所有切片处理完成返回True
        """
        return self.processing_completed
    
    def mark_processing_completed(self) -> None:
        """标记处理完成
        
        在所有切片处理完成后调用，标记整个算法流程处理完成。
        """
        self.processing_completed = True
    
    def get_processing_progress(self) -> tuple[int, int]:
        """获取处理进度
        
        Returns:
            tuple[int, int]: (当前切片索引, 总切片数量)
        """
        return (self.current_slice_index + 1, self.total_slice_count)
    
    def get_total_recognition_results_count(self) -> int:
        """获取所有切片的总识别结果数量
        
        Returns:
            int: 所有切片的识别结果总数量
        """
        total_count = 0
        for context in self.all_slice_contexts:
            total_count += context.get_total_recognition_results_count()
        return total_count
    
    def get_total_successful_recognition_results_count(self) -> int:
        """获取所有切片的成功识别结果数量
        
        Returns:
            int: 所有切片的成功识别结果总数量
        """
        total_count = 0
        for context in self.all_slice_contexts:
            total_count += context.get_successful_recognition_results_count()
        return total_count
    
    def get_total_extracted_features_count(self) -> int:
        """获取所有切片的提取特征总数量
        
        Returns:
            int: 所有切片的提取特征总数量
        """
        total_count = 0
        for context in self.all_slice_contexts:
            total_count += len(context.extracted_features)
        return total_count
    
    def clear_all_data(self) -> None:
        """清空所有数据
        
        在开始新的算法流程时调用，清空所有持久化数据。
        """
        self.all_slice_contexts.clear()
        self.current_slice_index = -1
        self.total_slice_count = 0
        self.processing_completed = False
