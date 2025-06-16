"""事件总线模块

本模块实现了事件总线的核心功能，提供事件的发布-订阅机制。
"""
from typing import Dict, List, Callable, Any, Optional
from threading import Lock
from radar_system.infrastructure.async_core.event_bus.event import Event
from radar_system.infrastructure.common.logging import system_logger

EventHandler = Callable[[Event], None]

class EventBus:
    """事件总线
    
    提供事件的发布-订阅功能，支持异步事件处理。
    
    Attributes:
        _handlers (Dict[str, List[EventHandler]]): 事件处理器映射
        _lock (Lock): 线程安全锁
    """
    
    def __init__(self):
        """初始化事件总线"""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._lock = Lock()
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            
        Raises:
            ValueError: 事件类型为空或处理器为None时抛出
        """
        if not event_type:
            raise ValueError("事件类型不能为空")
        if handler is None:
            raise ValueError("事件处理器不能为None")
            
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                system_logger.debug(f"已添加事件处理器: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """取消事件订阅
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        with self._lock:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                    system_logger.debug(f"已移除事件处理器: {event_type}")
                except ValueError:
                    pass
                
                # 如果没有处理器了，删除该事件类型
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
    
    def publish(self, event: Event) -> None:
        """发布事件
        
        Args:
            event: 要发布的事件
            
        Raises:
            ValueError: 事件为None时抛出
        """
        if event is None:
            raise ValueError("事件不能为None")
            
        system_logger.debug(f"发布事件: {event.type}")
        
        handlers = self._get_handlers(event.type)
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                system_logger.error(f"事件处理器异常: {str(e)}")
    
    def _get_handlers(self, event_type: str) -> List[EventHandler]:
        """获取事件处理器列表
        
        Args:
            event_type: 事件类型
            
        Returns:
            List[EventHandler]: 处理器列表的副本
        """
        with self._lock:
            return self._handlers.get(event_type, [])[:]
    
    def clear(self) -> None:
        """清除所有事件订阅"""
        with self._lock:
            self._handlers.clear()
            system_logger.debug("已清除所有事件处理器")
    
    @property
    def event_types(self) -> List[str]:
        """获取所有已注册的事件类型
        
        Returns:
            List[str]: 事件类型列表
        """
        with self._lock:
            return list(self._handlers.keys())
    
    def get_handler_count(self, event_type: str) -> int:
        """获取指定事件类型的处理器数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            int: 处理器数量
        """
        with self._lock:
            return len(self._handlers.get(event_type, []))
