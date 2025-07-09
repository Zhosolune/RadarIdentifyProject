"""线程池模块

本模块实现了线程池的核心功能，负责管理工作线程和任务分发。
"""
from typing import Optional, List, Any, Callable
from concurrent.futures import Future, ThreadPoolExecutor
import asyncio
import threading

from radar_system.infrastructure.async_core.worker import Worker
from radar_system.infrastructure.async_core.task_queue import TaskQueue, Task
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.exceptions import ProcessingError

class ThreadPool:
    """线程池类
    
    管理工作线程池，提供任务提交和执行功能。
    """
    
    def __init__(self, 
                 max_workers: int = 4,
                 min_workers: int = 2,
                 idle_timeout: int = 60):
        """初始化线程池
        
        Args:
            max_workers: 最大工作线程数
            min_workers: 最小工作线程数
            idle_timeout: 空闲线程超时时间（秒）
        """
        self._max_workers = max_workers
        self._min_workers = min_workers
        self._idle_timeout = idle_timeout
        self._shutdown = False
        
        # 创建线程池执行器
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="radar_worker"
        )
        
        system_logger.info(
            f"线程池初始化完成: 最大线程数={max_workers}, "
            f"最小线程数={min_workers}, "
            f"空闲超时={idle_timeout}秒"
        )
        
    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """提交任务到线程池
        
        将任务提交到线程池执行。
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Future: 任务执行的Future对象
            
        Raises:
            ProcessingError: 任务执行出错
        """
        if self._shutdown:
            raise ProcessingError("线程池已关闭")
            
        try:
            # 直接使用executor提交任务
            return self._executor.submit(func, *args, **kwargs)
            
        except Exception as e:
            system_logger.error(f"任务执行出错: {str(e)}")
            raise ProcessingError(f"任务执行失败: {str(e)}") from e
            
    def shutdown(self, wait: bool = True) -> None:
        """关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        if not self._shutdown:
            self._shutdown = True
            self._executor.shutdown(wait=wait)
            system_logger.info("线程池已关闭")
            
    @property
    def is_shutdown(self) -> bool:
        """检查线程池是否已关闭
        
        Returns:
            bool: 线程池是否已关闭
        """
        return self._shutdown
        
    def __enter__(self):
        """上下文管理器入口"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown(wait=True)
