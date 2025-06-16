"""信号数据仓储模块

实现信号数据的内存存储和管理。
"""
from typing import Dict, Optional, List
import threading
import time
from weakref import WeakValueDictionary
from radar_system.domain.signal.entities.signal import SignalData
from radar_system.infrastructure.common.exceptions import RepositoryError

class SignalRepository:
    """信号数据仓储类
    
    实现基于内存的信号数据存储和管理。
    
    Attributes:
        _signals_cache: 信号数据缓存字典
        _access_times: 记录信号访问时间
        _max_cache_size: 最大缓存数量
        _lock: 线程锁
    """
    
    def __init__(self, max_cache_size: int = 100):
        """初始化信号仓储
        
        Args:
            max_cache_size: 最大缓存信号数量，默认100
        """
        self._signals_cache = WeakValueDictionary()  # 使用弱引用字典存储信号
        self._access_times = {}  # 记录访问时间
        self._max_cache_size = max_cache_size
        self._lock = threading.RLock()  # 可重入锁
        
    def save(self, signal: SignalData) -> bool:
        """保存信号数据
        
        Args:
            signal: 要保存的信号数据实体
            
        Returns:
            bool: 保存是否成功
            
        Raises:
            RepositoryError: 保存过程中出现错误
        """
        try:
            with self._lock:
                # 检查并清理缓存
                self._evict_if_needed()
                
                # 保存信号数据的副本
                self._signals_cache[signal.id] = signal.copy()
                self._access_times[signal.id] = time.time()
                return True
                
        except Exception as e:
            raise RepositoryError(f"保存信号数据失败: {str(e)}")
            
    def find_by_id(self, signal_id: str) -> Optional[SignalData]:
        """根据ID查找信号
        
        Args:
            signal_id: 信号ID
            
        Returns:
            Optional[SignalData]: 找到的信号数据，未找到返回None
        """
        with self._lock:
            signal = self._signals_cache.get(signal_id)
            if signal:
                self._access_times[signal_id] = time.time()
            return signal
            
    def update(self, signal: SignalData) -> bool:
        """更新信号数据
        
        Args:
            signal: 更新后的信号数据
            
        Returns:
            bool: 更新是否成功
        """
        return self.save(signal)  # 直接覆盖保存
        
    def delete(self, signal_id: str) -> bool:
        """删除信号数据
        
        Args:
            signal_id: 要删除的信号ID
            
        Returns:
            bool: 删除是否成功
        """
        with self._lock:
            if signal_id in self._signals_cache:
                del self._signals_cache[signal_id]
                self._access_times.pop(signal_id, None)
                return True
            return False
            
    def _evict_if_needed(self) -> None:
        """必要时清理缓存
        
        当缓存数量达到最大限制时，移除最早访问的信号数据。
        """
        if len(self._signals_cache) >= self._max_cache_size:
            # 按最后访问时间排序
            sorted_signals = sorted(
                self._access_times.items(),
                key=lambda x: x[1]
            )
            # 移除最早访问的信号
            oldest_signal_id = sorted_signals[0][0]
            self.delete(oldest_signal_id)
            
    def clear_cache(self) -> None:
        """清空缓存
        
        清除所有缓存的信号数据。
        """
        with self._lock:
            self._signals_cache.clear()
            self._access_times.clear()
