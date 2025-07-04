"""识别任务类

本模块定义识别任务的封装，支持异步执行、进度跟踪和状态管理。
"""

import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from PyQt5.QtCore import QObject, pyqtSignal
from .task_enums import TaskStatus, TaskPriority, RecognitionStage


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    session_id: Optional[str] = None
    final_parameters: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    stage_results: Dict[RecognitionStage, Dict[str, Any]] = field(default_factory=dict)


class RecognitionTask(QObject):
    """识别任务类
    
    封装完整的雷达信号识别任务，支持异步执行、进度跟踪、暂停/恢复等功能。
    
    Signals:
        status_changed: 任务状态变化信号 (task_id: str, old_status: TaskStatus, new_status: TaskStatus)
        progress_updated: 进度更新信号 (task_id: str, stage: RecognitionStage, progress: float)
        stage_completed: 阶段完成信号 (task_id: str, stage: RecognitionStage, results: dict)
        task_completed: 任务完成信号 (task_id: str, result: TaskResult)
        task_failed: 任务失败信号 (task_id: str, error_message: str)
    """
    
    # Qt信号定义
    status_changed = pyqtSignal(str, TaskStatus, TaskStatus)  # task_id, old_status, new_status
    progress_updated = pyqtSignal(str, RecognitionStage, float)  # task_id, stage, progress
    stage_completed = pyqtSignal(str, RecognitionStage, dict)  # task_id, stage, results
    task_completed = pyqtSignal(str, TaskResult)  # task_id, result
    task_failed = pyqtSignal(str, str)  # task_id, error_message
    
    def __init__(
        self,
        signal_data: Any,
        recognition_params: Any,
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        parent: Optional[QObject] = None
    ):
        """初始化识别任务
        
        Args:
            signal_data: 待识别的信号数据
            recognition_params: 识别参数
            task_id: 任务ID，默认自动生成
            priority: 任务优先级
            parent: Qt父对象
        """
        super().__init__(parent)
        
        self.task_id = task_id or str(uuid.uuid4())
        self.signal_data = signal_data
        self.recognition_params = recognition_params
        self.priority = priority
        
        # 任务状态
        self._status = TaskStatus.PENDING
        self._current_stage = RecognitionStage.INITIALIZING
        self._overall_progress = 0.0
        self._stage_progress = 0.0
        
        # 执行控制
        self._execution_thread: Optional[threading.Thread] = None
        self._pause_event = threading.Event()
        self._cancel_event = threading.Event()
        self._pause_event.set()  # 初始状态为非暂停
        
        # 时间记录
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # 结果存储
        self._result: Optional[TaskResult] = None
        self._session_id: Optional[str] = None
        self._stage_results: Dict[RecognitionStage, Dict[str, Any]] = {}
        
        # 执行回调
        self._execution_callback: Optional[Callable] = None
    
    @property
    def status(self) -> TaskStatus:
        """获取任务状态"""
        return self._status
    
    @property
    def current_stage(self) -> RecognitionStage:
        """获取当前执行阶段"""
        return self._current_stage
    
    @property
    def overall_progress(self) -> float:
        """获取整体进度 (0.0-1.0)"""
        return self._overall_progress
    
    @property
    def stage_progress(self) -> float:
        """获取当前阶段进度 (0.0-1.0)"""
        return self._stage_progress
    
    @property
    def session_id(self) -> Optional[str]:
        """获取关联的会话ID"""
        return self._session_id
    
    @property
    def result(self) -> Optional[TaskResult]:
        """获取任务执行结果"""
        return self._result
    
    def set_execution_callback(self, callback: Callable):
        """设置任务执行回调函数
        
        Args:
            callback: 执行回调函数，签名为 callback(task: RecognitionTask) -> TaskResult
        """
        self._execution_callback = callback
    
    def start(self) -> bool:
        """启动任务执行
        
        Returns:
            是否成功启动
        """
        if self._status != TaskStatus.PENDING:
            return False
        
        if not self._execution_callback:
            self._set_status(TaskStatus.FAILED)
            self.task_failed.emit(self.task_id, "未设置执行回调函数")
            return False
        
        self._execution_thread = threading.Thread(target=self._execute, daemon=True)
        self._execution_thread.start()
        
        return True
    
    def pause(self) -> bool:
        """暂停任务执行
        
        Returns:
            是否成功暂停
        """
        if self._status != TaskStatus.RUNNING:
            return False
        
        self._pause_event.clear()
        self._set_status(TaskStatus.PAUSED)
        return True
    
    def resume(self) -> bool:
        """恢复任务执行
        
        Returns:
            是否成功恢复
        """
        if self._status != TaskStatus.PAUSED:
            return False
        
        self._pause_event.set()
        self._set_status(TaskStatus.RUNNING)
        return True
    
    def cancel(self) -> bool:
        """取消任务执行
        
        Returns:
            是否成功取消
        """
        if self._status.is_finished:
            return False
        
        self._cancel_event.set()
        self._pause_event.set()  # 确保线程能够检查取消状态
        self._set_status(TaskStatus.CANCELLED)
        return True
    
    def _execute(self):
        """执行任务的内部方法"""
        try:
            self.started_at = datetime.now()
            self._set_status(TaskStatus.RUNNING)
            
            # 执行任务
            result = self._execution_callback(self)
            
            # 检查是否被取消
            if self._cancel_event.is_set():
                self._set_status(TaskStatus.CANCELLED)
                return
            
            # 设置结果
            self.completed_at = datetime.now()
            self._result = result
            
            if result.success:
                self._set_status(TaskStatus.COMPLETED)
                self.task_completed.emit(self.task_id, result)
            else:
                self._set_status(TaskStatus.FAILED)
                self.task_failed.emit(self.task_id, result.error_message or "任务执行失败")
                
        except Exception as e:
            self.completed_at = datetime.now()
            self._set_status(TaskStatus.FAILED)
            error_msg = f"任务执行异常: {str(e)}"
            self.task_failed.emit(self.task_id, error_msg)
    
    def _set_status(self, new_status: TaskStatus):
        """设置任务状态并发出信号"""
        if new_status != self._status:
            old_status = self._status
            self._status = new_status
            self.status_changed.emit(self.task_id, old_status, new_status)
    
    def update_stage(self, stage: RecognitionStage, progress: float = 0.0):
        """更新当前执行阶段
        
        Args:
            stage: 新的执行阶段
            progress: 阶段内进度 (0.0-1.0)
        """
        self._current_stage = stage
        self._stage_progress = max(0.0, min(1.0, progress))
        
        # 计算整体进度
        self._calculate_overall_progress()
        
        self.progress_updated.emit(self.task_id, stage, self._stage_progress)
    
    def complete_stage(self, stage: RecognitionStage, results: Dict[str, Any]):
        """完成当前阶段
        
        Args:
            stage: 完成的阶段
            results: 阶段执行结果
        """
        self._stage_results[stage] = results
        self.stage_completed.emit(self.task_id, stage, results)
    
    def _calculate_overall_progress(self):
        """计算整体进度"""
        # 获取所有阶段的权重
        stages = list(RecognitionStage)
        current_index = stages.index(self._current_stage)
        
        # 计算已完成阶段的进度
        completed_progress = sum(
            stage.progress_weight for stage in stages[:current_index]
        )
        
        # 加上当前阶段的进度
        current_stage_progress = self._current_stage.progress_weight * self._stage_progress
        
        self._overall_progress = completed_progress + current_stage_progress
    
    def check_pause_and_cancel(self) -> bool:
        """检查暂停和取消状态
        
        Returns:
            True表示应该继续执行，False表示应该停止
        """
        # 检查取消
        if self._cancel_event.is_set():
            return False
        
        # 检查暂停
        self._pause_event.wait()
        
        # 再次检查取消（暂停期间可能被取消）
        return not self._cancel_event.is_set()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取任务摘要信息
        
        Returns:
            任务摘要字典
        """
        execution_time = None
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            execution_time = (end_time - self.started_at).total_seconds()
        
        return {
            'task_id': self.task_id,
            'status': self._status.value,
            'status_display': self._status.display_name,
            'priority': self.priority.value,
            'priority_display': self.priority.display_name,
            'current_stage': self._current_stage.value,
            'stage_display': self._current_stage.display_name,
            'overall_progress': self._overall_progress,
            'stage_progress': self._stage_progress,
            'session_id': self._session_id,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time': execution_time,
            'has_result': self._result is not None
        }
