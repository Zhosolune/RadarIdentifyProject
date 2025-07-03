"""任务队列模块

本模块实现了一个线程安全的任务队列，用于在线程池中管理待执行的任务。
"""
from typing import Optional, Any, Callable, Tuple, Dict
from queue import Queue, Empty
from dataclasses import dataclass
from datetime import datetime
import uuid

from radar_system.infrastructure.common.exceptions import ProcessingError

@dataclass
class Task:
    """任务类
    
    表示一个可执行的任务单元。
    
    Attributes:
        id (str): 任务唯一标识符
        target (Callable): 目标可调用对象
        args (Tuple): 位置参数
        kwargs (Dict): 关键字参数
        created_at (datetime): 任务创建时间
    """
    id: str
    target: Callable
    args: Tuple
    kwargs: Dict
    created_at: datetime
    
    @classmethod
    def create(cls, target: Callable, *args, **kwargs) -> 'Task':
        """创建新任务
        
        Args:
            target: 目标可调用对象
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Task: 新创建的任务实例
        """
        return cls(
            id=str(uuid.uuid4()),
            target=target,
            args=args,
            kwargs=kwargs,
            created_at=datetime.now()
        )
    
    def execute(self) -> Any:
        """执行任务
        
        Returns:
            Any: 任务执行结果
            
        Raises:
            Exception: 任务执行过程中的任何异常
        """
        return self.target(*self.args, **self.kwargs)

class TaskQueue:
    """任务队列
    
    提供线程安全的任务管理功能。
    
    Attributes:
        _queue (Queue): 内部队列实现
        _max_size (int): 队列最大容量
    """
    
    def __init__(self, max_size: int = 0):
        """初始化任务队列
        
        Args:
            max_size: 队列最大容量，0表示无限制
        """
        self._queue = Queue(maxsize=max_size)
        self._max_size = max_size
    
    def put(self, task: Task, block: bool = True, timeout: Optional[float] = None) -> None:
        """添加任务到队列
        
        Args:
            task: 要添加的任务
            block: 是否阻塞等待
            timeout: 等待超时时间（秒）
            
        Raises:
            queue.Full: 队列已满且非阻塞或等待超时
        """
        self._queue.put(task, block=block, timeout=timeout)
    
    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Task]:
        """从队列获取任务
        
        Args:
            block: 是否阻塞等待
            timeout: 等待超时时间（秒）
            
        Returns:
            Optional[Task]: 获取的任务，如果队列为空且非阻塞或等待超时则返回None
            
        Raises:
            queue.Empty: 队列为空且非阻塞或等待超时
        """
        try:
            return self._queue.get(block=block, timeout=timeout)
        except Empty:
            return None
    
    def empty(self) -> bool:
        """检查队列是否为空
        
        Returns:
            bool: 队列是否为空
        """
        return self._queue.empty()
    
    def full(self) -> bool:
        """检查队列是否已满
        
        Returns:
            bool: 队列是否已满
        """
        return self._queue.full()
    
    def qsize(self) -> int:
        """获取队列当前大小
        
        Returns:
            int: 队列中的任务数量
        """
        return self._queue.qsize()
    
    def clear(self) -> None:
        """清空队列
        
        注意：此操作不是原子的，在多线程环境下可能不可靠
        """
        while not self.empty():
            try:
                self._queue.get_nowait()
            except Empty:
                break
