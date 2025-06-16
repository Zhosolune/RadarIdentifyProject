"""轮询调度器模块

本模块实现了基于轮询的任务调度器。
"""
from typing import Optional, Dict, Deque
from collections import deque
from threading import Lock
from .scheduler import BaseScheduler, ScheduledTask
from radar_system.infrastructure.common.logging import system_logger

class RoundRobinScheduler(BaseScheduler):
    """轮询调度器
    
    使用循环队列实现任务的轮询调度。
    
    Attributes:
        _queue (Deque[ScheduledTask]): 任务队列
        _tasks (Dict[str, ScheduledTask]): 任务映射表
        _lock (Lock): 线程安全锁
        _quantum (int): 默认时间片大小（毫秒）
    """
    
    def __init__(self, name: str = "RoundRobinScheduler", quantum: int = 100):
        """初始化轮询调度器
        
        Args:
            name: 调度器名称
            quantum: 默认时间片大小（毫秒）
        """
        super().__init__(name)
        self._queue: Deque[ScheduledTask] = deque()
        self._tasks: Dict[str, ScheduledTask] = {}
        self._lock = Lock()
        self._quantum = quantum
    
    def schedule(self, task: ScheduledTask) -> None:
        """调度任务
        
        将任务加入循环队列。
        
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
                
            # 如果任务没有指定时间片，使用默认值
            if task.quantum <= 0:
                task.quantum = self._quantum
                
            # 将任务加入队列和映射表
            self._queue.append(task)
            self._tasks[task.id] = task
            
            system_logger.debug(f"已调度任务: {task.name} (ID: {task.id}, 时间片: {task.quantum}ms)")
    
    def next(self) -> Optional[ScheduledTask]:
        """获取下一个要执行的任务
        
        按照先进先出的顺序返回任务。
        
        Returns:
            Optional[ScheduledTask]: 下一个任务，如果没有任务则返回None
        """
        if self.empty():
            return None
            
        with self._lock:
            try:
                # 从队列头部获取任务
                task = self._queue.popleft()
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
        return len(self._queue) == 0
    
    def clear(self) -> None:
        """清空所有待执行的任务"""
        with self._lock:
            self._queue.clear()
            self._tasks.clear()
            system_logger.debug("已清空所有任务")
    
    def task_count(self) -> int:
        """获取待执行的任务数量
        
        Returns:
            int: 任务数量
        """
        return len(self._queue)
    
    def contains(self, task_id: str) -> bool:
        """检查是否包含指定ID的任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否包含
        """
        return task_id in self._tasks
    
    @property
    def quantum(self) -> int:
        """获取默认时间片大小
        
        Returns:
            int: 时间片大小（毫秒）
        """
        return self._quantum
    
    @quantum.setter
    def quantum(self, value: int) -> None:
        """设置默认时间片大小
        
        Args:
            value: 时间片大小（毫秒）
            
        Raises:
            ValueError: 时间片大小小于等于0时抛出
        """
        if value <= 0:
            raise ValueError("时间片大小必须大于0")
        self._quantum = value
