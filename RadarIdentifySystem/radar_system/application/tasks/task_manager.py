"""任务管理器

本模块提供任务队列管理、并发控制和任务生命周期管理功能。
"""

import threading
from typing import Dict, List, Optional, Callable
from queue import PriorityQueue, Empty
from dataclasses import dataclass
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal
from .recognition_task import RecognitionTask, TaskResult
from .task_enums import TaskStatus, TaskPriority


@dataclass
class TaskQueueItem:
    """任务队列项"""
    priority: int  # 优先级数值（越小优先级越高）
    created_at: datetime
    task: RecognitionTask
    
    def __lt__(self, other):
        """比较函数，用于优先队列排序"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at


class TaskManager(QObject):
    """任务管理器
    
    负责管理识别任务的队列、执行和生命周期。
    
    Signals:
        task_queued: 任务入队信号 (task_id: str)
        task_started: 任务开始执行信号 (task_id: str)
        task_completed: 任务完成信号 (task_id: str, success: bool)
        queue_status_changed: 队列状态变化信号 (pending_count: int, running_count: int)
    """
    
    # Qt信号定义
    task_queued = pyqtSignal(str)  # task_id
    task_started = pyqtSignal(str)  # task_id
    task_completed = pyqtSignal(str, bool)  # task_id, success
    queue_status_changed = pyqtSignal(int, int)  # pending_count, running_count
    
    def __init__(
        self,
        max_concurrent_tasks: int = 2,
        execution_callback: Optional[Callable] = None,
        parent: Optional[QObject] = None
    ):
        """初始化任务管理器
        
        Args:
            max_concurrent_tasks: 最大并发任务数
            execution_callback: 任务执行回调函数
            parent: Qt父对象
        """
        super().__init__(parent)
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self._execution_callback = execution_callback
        
        # 任务存储
        self._all_tasks: Dict[str, RecognitionTask] = {}
        self._pending_queue = PriorityQueue()
        self._running_tasks: Dict[str, RecognitionTask] = {}
        self._completed_tasks: Dict[str, RecognitionTask] = {}
        
        # 线程控制
        self._manager_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._queue_lock = threading.Lock()
        
        # 启动管理线程
        self._start_manager_thread()
    
    def set_execution_callback(self, callback: Callable):
        """设置任务执行回调函数
        
        Args:
            callback: 执行回调函数，签名为 callback(task: RecognitionTask) -> TaskResult
        """
        self._execution_callback = callback
    
    def submit_task(self, task: RecognitionTask) -> bool:
        """提交任务到队列
        
        Args:
            task: 要提交的识别任务
            
        Returns:
            是否成功提交
        """
        if task.task_id in self._all_tasks:
            return False
        
        # 设置执行回调
        if self._execution_callback:
            task.set_execution_callback(self._execution_callback)
        
        # 连接任务信号
        self._connect_task_signals(task)
        
        # 添加到队列
        with self._queue_lock:
            queue_item = TaskQueueItem(
                priority=task.priority.value,
                created_at=task.created_at,
                task=task
            )
            self._pending_queue.put(queue_item)
            self._all_tasks[task.task_id] = task
        
        self.task_queued.emit(task.task_id)
        self._emit_queue_status()
        
        return True
    
    def get_task(self, task_id: str) -> Optional[RecognitionTask]:
        """获取指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        return self._all_tasks.get(task_id)
    
    def pause_task(self, task_id: str) -> bool:
        """暂停指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功暂停
        """
        task = self._running_tasks.get(task_id)
        if task:
            return task.pause()
        return False
    
    def resume_task(self, task_id: str) -> bool:
        """恢复指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功恢复
        """
        task = self._running_tasks.get(task_id)
        if task:
            return task.resume()
        return False
    
    def cancel_task(self, task_id: str) -> bool:
        """取消指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        task = self._all_tasks.get(task_id)
        if task:
            return task.cancel()
        return False
    
    def get_queue_status(self) -> Dict[str, int]:
        """获取队列状态
        
        Returns:
            包含各种状态任务数量的字典
        """
        with self._queue_lock:
            pending_count = self._pending_queue.qsize()
            running_count = len(self._running_tasks)
            completed_count = len(self._completed_tasks)
            
            return {
                'pending': pending_count,
                'running': running_count,
                'completed': completed_count,
                'total': len(self._all_tasks)
            }
    
    def get_active_tasks(self) -> List[RecognitionTask]:
        """获取所有活跃任务
        
        Returns:
            活跃任务列表
        """
        active_tasks = []
        for task in self._all_tasks.values():
            if task.status.is_active:
                active_tasks.append(task)
        return active_tasks
    
    def get_completed_tasks(self) -> List[RecognitionTask]:
        """获取所有已完成任务
        
        Returns:
            已完成任务列表
        """
        return list(self._completed_tasks.values())
    
    def clear_completed_tasks(self) -> int:
        """清理已完成的任务
        
        Returns:
            清理的任务数量
        """
        with self._queue_lock:
            count = len(self._completed_tasks)
            for task_id in list(self._completed_tasks.keys()):
                del self._all_tasks[task_id]
            self._completed_tasks.clear()
        
        self._emit_queue_status()
        return count
    
    def shutdown(self):
        """关闭任务管理器"""
        self._stop_event.set()
        
        # 取消所有运行中的任务
        for task in list(self._running_tasks.values()):
            task.cancel()
        
        # 等待管理线程结束
        if self._manager_thread and self._manager_thread.is_alive():
            self._manager_thread.join(timeout=5.0)
    
    def _start_manager_thread(self):
        """启动管理线程"""
        self._manager_thread = threading.Thread(target=self._manage_tasks, daemon=True)
        self._manager_thread.start()
    
    def _manage_tasks(self):
        """任务管理主循环"""
        while not self._stop_event.is_set():
            try:
                # 检查是否可以启动新任务
                if len(self._running_tasks) < self.max_concurrent_tasks:
                    self._try_start_next_task()
                
                # 短暂休眠避免CPU占用过高
                self._stop_event.wait(0.1)
                
            except Exception as e:
                # 记录错误但继续运行
                print(f"任务管理器错误: {e}")
    
    def _try_start_next_task(self):
        """尝试启动下一个任务"""
        try:
            with self._queue_lock:
                if self._pending_queue.empty():
                    return
                
                queue_item = self._pending_queue.get_nowait()
                task = queue_item.task
                
                # 检查任务是否已被取消
                if task.status == TaskStatus.CANCELLED:
                    self._move_to_completed(task)
                    return
                
                # 启动任务
                if task.start():
                    self._running_tasks[task.task_id] = task
                    self.task_started.emit(task.task_id)
                    self._emit_queue_status()
                else:
                    # 启动失败，移到完成队列
                    self._move_to_completed(task)
                    
        except Empty:
            pass
    
    def _connect_task_signals(self, task: RecognitionTask):
        """连接任务信号"""
        task.task_completed.connect(self._on_task_completed)
        task.task_failed.connect(self._on_task_failed)
    
    def _on_task_completed(self, task_id: str, result: TaskResult):
        """任务完成处理"""
        task = self._running_tasks.pop(task_id, None)
        if task:
            self._move_to_completed(task)
            self.task_completed.emit(task_id, True)
            self._emit_queue_status()
    
    def _on_task_failed(self, task_id: str, error_message: str):
        """任务失败处理"""
        task = self._running_tasks.pop(task_id, None)
        if task:
            self._move_to_completed(task)
            self.task_completed.emit(task_id, False)
            self._emit_queue_status()
    
    def _move_to_completed(self, task: RecognitionTask):
        """将任务移到完成队列"""
        with self._queue_lock:
            self._completed_tasks[task.task_id] = task
    
    def _emit_queue_status(self):
        """发出队列状态变化信号"""
        status = self.get_queue_status()
        self.queue_status_changed.emit(status['pending'], status['running'])
