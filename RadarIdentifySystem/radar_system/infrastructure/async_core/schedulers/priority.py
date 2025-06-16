"""优先级调度器模块

本模块实现了基于优先级的任务调度器。
"""
from typing import Optional, Dict
from queue import PriorityQueue
from threading import Lock
from .scheduler import BaseScheduler, ScheduledTask
from radar_system.infrastructure.common.logging import system_logger

class PriorityScheduler(BaseScheduler):
    """优先级调度器
    
    使用优先级队列实现任务的优先级调度。
    
    Attributes:
        _queue (PriorityQueue): 优先级队列
        _tasks (Dict[str, ScheduledTask]): 任务映射表
        _lock (Lock): 线程安全锁
    """
    
    def __init__(self, name: str = "PriorityScheduler"):
        """初始化优先级调度器
        
        Args:
            name: 调度器名称
        """
        super().__init__(name)
        self._queue = PriorityQueue()
        self._tasks: Dict[str, ScheduledTask] = {}
        self._lock = Lock()
    
    def schedule(self, task: ScheduledTask) -> None:
        """调度任务
        
        将任务加入优先级队列。
        
        Args:
            task: 要调度的任务
            
        Raises:
            ValueError: 任务为None或已存在时抛出
        """
        if task is None:
            raise ValueError("任务不能为None")
            
        with self._lock:
            if task.id in self._tasks:
                raise ValueError(f"任务 {task.id} 已存在")
                
            # 将任务加入队列和映射表
            self._queue.put((task.priority, task.created_at, task))
            self._tasks[task.id] = task
            
            system_logger.debug(f"已调度任务: {task.name} (ID: {task.id}, 优先级: {task.priority})")
    
    def next(self) -> Optional[ScheduledTask]:
        """获取下一个要执行的任务
        
        返回优先级最高的任务。
        
        Returns:
            Optional[ScheduledTask]: 下一个任务，如果没有任务则返回None
        """
        if self.empty():
            return None
            
        with self._lock:
            try:
                # 获取优先级最高的任务
                _, _, task = self._queue.get_nowait()
                # 从映射表中移除任务
                del self._tasks[task.id]
                
                system_logger.debug(f"获取任务: {task.name} (ID: {task.id})")
                return task
            except Exception as e:
                system_logger.error(f"获取任务失败: {str(e)}")
                return None
    
    def empty(self) -> bool:
        """检查是否有待执行的任务
        
        Returns:
            bool: 是否为空
        """
        return self._queue.empty()
    
    def clear(self) -> None:
        """清空所有待执行的任务"""
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except Exception:
                    pass
            self._tasks.clear()
            system_logger.debug("已清空所有任务")
    
    def task_count(self) -> int:
        """获取待执行的任务数量
        
        Returns:
            int: 任务数量
        """
        return self._queue.qsize()
    
    def contains(self, task_id: str) -> bool:
        """检查是否包含指定ID的任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否包含
        """
        return task_id in self._tasks
