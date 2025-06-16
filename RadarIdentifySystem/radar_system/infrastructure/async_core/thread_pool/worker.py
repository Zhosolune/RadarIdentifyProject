"""工作线程模块

本模块实现了线程池的工作线程，负责从任务队列获取并执行任务。
"""
from threading import Thread, Event
from typing import Optional
from datetime import datetime
import time

from radar_system.infrastructure.async_core.thread_pool.task_queue import TaskQueue, Task
from radar_system.infrastructure.common.logging import system_logger

class Worker(Thread):
    """工作线程
    
    继承自Thread类，负责执行任务队列中的任务。
    
    Attributes:
        _task_queue (TaskQueue): 任务队列
        _stop_event (Event): 停止事件
        _idle_timeout (float): 空闲超时时间（秒）
        _last_active (datetime): 最后活动时间
    """
    
    def __init__(self, task_queue: TaskQueue, idle_timeout: float = 60.0):
        """初始化工作线程
        
        Args:
            task_queue: 任务队列
            idle_timeout: 空闲超时时间（秒），默认60秒
        """
        super().__init__(daemon=True)
        self._task_queue = task_queue
        self._stop_event = Event()
        self._idle_timeout = idle_timeout
        self._last_active = datetime.now()
        
    def run(self) -> None:
        """线程运行函数
        
        持续从任务队列获取并执行任务，直到收到停止信号。
        """
        system_logger.info(f"工作线程 {self.name} 已启动")
        
        while not self._stop_event.is_set():
            # 尝试获取任务
            task = self._get_task()
            
            if task is None:
                # 检查空闲超时
                if self._check_idle_timeout():
                    system_logger.info(f"工作线程 {self.name} 空闲超时，退出")
                    break
                continue
            
            # 更新最后活动时间
            self._last_active = datetime.now()
            
            try:
                # 执行任务
                system_logger.debug(f"工作线程 {self.name} 开始执行任务 {task.id}")
                task.execute()
                system_logger.debug(f"工作线程 {self.name} 完成任务 {task.id}")
                
            except Exception as e:
                system_logger.error(f"工作线程 {self.name} 执行任务 {task.id} 出错: {str(e)}")
                
            finally:
                # 标记任务完成
                self._task_queue._queue.task_done()
        
        system_logger.info(f"工作线程 {self.name} 已停止")
    
    def stop(self) -> None:
        """停止工作线程
        
        设置停止事件，通知线程退出。
        """
        self._stop_event.set()
    
    def _get_task(self) -> Optional[Task]:
        """获取任务
        
        从任务队列获取任务，带有超时机制。
        
        Returns:
            Optional[Task]: 获取到的任务，如果队列为空则返回None
        """
        try:
            # 使用较短的超时时间，以便及时响应停止信号
            return self._task_queue.get(timeout=1.0)
        except Exception:
            return None
    
    def _check_idle_timeout(self) -> bool:
        """检查是否空闲超时
        
        Returns:
            bool: 是否已超时
        """
        if self._idle_timeout <= 0:
            return False
            
        idle_time = (datetime.now() - self._last_active).total_seconds()
        return idle_time >= self._idle_timeout
    
    @property
    def is_idle(self) -> bool:
        """检查线程是否空闲
        
        Returns:
            bool: 线程是否空闲
        """
        return self._task_queue.empty()
    
    @property
    def idle_time(self) -> float:
        """获取线程空闲时间
        
        Returns:
            float: 空闲时间（秒）
        """
        return (datetime.now() - self._last_active).total_seconds()
