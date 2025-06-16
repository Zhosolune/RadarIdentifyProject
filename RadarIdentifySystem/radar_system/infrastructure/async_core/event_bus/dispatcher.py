"""事件分发器模块

本模块实现了事件的异步分发功能。
"""
from typing import Optional
from queue import Queue, Empty
from threading import Thread, Event as ThreadEvent
from radar_system.infrastructure.async_core.event_bus.event import Event
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
from radar_system.infrastructure.common.logging import system_logger

class EventDispatcher(Thread):
    """事件分发器
    
    负责异步分发事件到事件总线。
    
    Attributes:
        _event_bus (EventBus): 事件总线实例
        _event_queue (Queue): 事件队列
        _stop_event (ThreadEvent): 停止事件
        _max_queue_size (int): 队列最大容量
    """
    
    def __init__(self, event_bus: EventBus, max_queue_size: int = 0):
        """初始化事件分发器
        
        Args:
            event_bus: 事件总线实例
            max_queue_size: 事件队列最大容量，0表示无限制
        """
        super().__init__(daemon=True)
        self._event_bus = event_bus
        self._event_queue = Queue(maxsize=max_queue_size)
        self._stop_event = ThreadEvent()
        self._max_queue_size = max_queue_size
    
    def run(self) -> None:
        """运行事件分发循环"""
        system_logger.info("事件分发器已启动")
        
        while not self._stop_event.is_set():
            try:
                # 使用较短的超时时间，以便及时响应停止信号
                event = self._event_queue.get(timeout=1.0)
                if event is not None:
                    try:
                        self._event_bus.publish(event)
                    except Exception as e:
                        system_logger.error(f"事件分发异常: {str(e)}")
                    finally:
                        self._event_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                system_logger.error(f"事件分发器异常: {str(e)}")
        
        system_logger.info("事件分发器已停止")
    
    def dispatch(self, event: Event, block: bool = True, timeout: Optional[float] = None) -> bool:
        """分发事件
        
        Args:
            event: 要分发的事件
            block: 是否阻塞等待
            timeout: 等待超时时间（秒）
            
        Returns:
            bool: 是否成功加入队列
            
        Raises:
            ValueError: 事件为None时抛出
        """
        if event is None:
            raise ValueError("事件不能为None")
            
        try:
            self._event_queue.put(event, block=block, timeout=timeout)
            return True
        except Exception as e:
            system_logger.error(f"事件入队异常: {str(e)}")
            return False
    
    def stop(self) -> None:
        """停止事件分发器"""
        self._stop_event.set()
    
    @property
    def queue_size(self) -> int:
        """获取当前队列大小
        
        Returns:
            int: 队列中的事件数量
        """
        return self._event_queue.qsize()
    
    @property
    def is_full(self) -> bool:
        """检查队列是否已满
        
        Returns:
            bool: 队列是否已满
        """
        return self._event_queue.full()
    
    def wait_empty(self, timeout: Optional[float] = None) -> bool:
        """等待队列清空
        
        Args:
            timeout: 等待超时时间（秒）
            
        Returns:
            bool: 是否成功等待队列清空
        """
        try:
            self._event_queue.join(timeout=timeout)
            return True
        except Exception:
            return False
