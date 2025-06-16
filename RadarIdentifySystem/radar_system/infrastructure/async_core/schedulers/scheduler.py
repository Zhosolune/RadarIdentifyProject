"""调度器基类模块

本模块定义了调度器的基本接口和行为。
"""
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class ScheduledTask:
    """调度任务
    
    表示一个可调度的任务单元。
    
    Attributes:
        id (str): 任务唯一标识符
        name (str): 任务名称
        target (callable): 目标可调用对象
        args (tuple): 位置参数
        kwargs (dict): 关键字参数
        priority (int): 任务优先级，数值越小优先级越高
        quantum (int): 时间片大小（毫秒）
        created_at (datetime): 任务创建时间
        metadata (Dict[str, Any]): 任务元数据
    """
    name: str
    target: callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = 0
    quantum: int = 100
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def execute(self) -> Any:
        """执行任务
        
        Returns:
            Any: 任务执行结果
            
        Raises:
            Exception: 任务执行过程中的任何异常
        """
        return self.target(*self.args, **self.kwargs)

class BaseScheduler(ABC):
    """调度器基类
    
    定义调度器的基本接口。
    
    Attributes:
        name (str): 调度器名称
    """
    
    def __init__(self, name: str):
        """初始化调度器
        
        Args:
            name: 调度器名称
        """
        self.name = name
    
    @abstractmethod
    def schedule(self, task: ScheduledTask) -> None:
        """调度任务
        
        Args:
            task: 要调度的任务
            
        Raises:
            ValueError: 任务无效时抛出
        """
        pass
    
    @abstractmethod
    def next(self) -> Optional[ScheduledTask]:
        """获取下一个要执行的任务
        
        Returns:
            Optional[ScheduledTask]: 下一个任务，如果没有任务则返回None
        """
        pass
    
    @abstractmethod
    def empty(self) -> bool:
        """检查是否有待执行的任务
        
        Returns:
            bool: 是否为空
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空所有待执行的任务"""
        pass
    
    @abstractmethod
    def task_count(self) -> int:
        """获取待执行的任务数量
        
        Returns:
            int: 任务数量
        """
        pass
    
    @abstractmethod
    def contains(self, task_id: str) -> bool:
        """检查是否包含指定ID的任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否包含
        """
        pass 