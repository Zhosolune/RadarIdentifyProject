"""识别应用服务

本模块提供识别功能的应用层服务，协调领域服务完成完整的识别流程。
"""

import logging
from typing import Dict, Any, Optional, List
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

from ..tasks.recognition_task import RecognitionTask, TaskResult
from ..tasks.task_manager import TaskManager
from ..tasks.task_enums import TaskStatus, TaskPriority, RecognitionStage
from ..workflows.recognition_workflow import RecognitionWorkflow


# 创建应用服务日志记录器
app_logger = logging.getLogger('application')


class RecognitionApplicationService(QObject):
    """识别应用服务
    
    提供完整的雷达信号识别应用服务，包括：
    - 任务管理和调度
    - 工作流编排
    - 进度跟踪和状态通知
    - 错误处理和恢复
    
    Signals:
        recognition_started: 识别开始信号 (task_id: str, session_id: str)
        stage_progress_updated: 阶段进度更新信号 (task_id: str, stage: str, progress: float)
        stage_completed: 阶段完成信号 (task_id: str, stage: str, results: dict)
        recognition_completed: 识别完成信号 (task_id: str, success: bool, results: dict)
        recognition_failed: 识别失败信号 (task_id: str, error_message: str)
        queue_status_changed: 队列状态变化信号 (pending: int, running: int, completed: int)
    """
    
    # Qt信号定义
    recognition_started = pyqtSignal(str, str)  # task_id, session_id
    stage_progress_updated = pyqtSignal(str, str, float)  # task_id, stage, progress
    stage_completed = pyqtSignal(str, str, dict)  # task_id, stage, results
    recognition_completed = pyqtSignal(str, bool, dict)  # task_id, success, results
    recognition_failed = pyqtSignal(str, str)  # task_id, error_message
    queue_status_changed = pyqtSignal(int, int, int)  # pending, running, completed
    
    def __init__(
        self,
        max_concurrent_tasks: int = 2,
        parent: Optional[QObject] = None
    ):
        """初始化识别应用服务
        
        Args:
            max_concurrent_tasks: 最大并发任务数
            parent: Qt父对象
        """
        super().__init__(parent)
        
        # 初始化组件
        self._task_manager = TaskManager(
            max_concurrent_tasks=max_concurrent_tasks,
            execution_callback=self._execute_recognition_task,
            parent=self
        )
        self._workflow = RecognitionWorkflow()
        
        # 连接任务管理器信号
        self._connect_task_manager_signals()
        
        # 领域服务依赖（在实际使用时需要注入）
        self._clustering_service = None
        self._recognition_service = None
        self._parameter_extraction_service = None
        self._session_service = None
        
        app_logger.info("识别应用服务初始化完成")
    
    def set_domain_services(
        self,
        clustering_service: Any,
        recognition_service: Any,
        parameter_extraction_service: Any,
        session_service: Any
    ):
        """设置领域服务依赖
        
        Args:
            clustering_service: 聚类服务
            recognition_service: 识别服务
            parameter_extraction_service: 参数提取服务
            session_service: 会话管理服务
        """
        self._clustering_service = clustering_service
        self._recognition_service = recognition_service
        self._parameter_extraction_service = parameter_extraction_service
        self._session_service = session_service
        
        # 设置工作流的服务依赖
        self._workflow.set_services(
            clustering_service,
            recognition_service,
            parameter_extraction_service,
            session_service
        )
        
        app_logger.info("领域服务依赖设置完成")
    
    def start_recognition(
        self,
        signal_data: np.ndarray,
        recognition_params: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        task_id: Optional[str] = None
    ) -> str:
        """启动识别任务
        
        Args:
            signal_data: 待识别的信号数据
            recognition_params: 识别参数
            priority: 任务优先级
            task_id: 自定义任务ID
            
        Returns:
            任务ID
            
        Raises:
            ValueError: 参数无效时抛出
        """
        # 验证输入参数
        if signal_data is None:
            raise ValueError("信号数据不能为空")
        
        if not recognition_params:
            raise ValueError("识别参数不能为空")
        
        # 创建识别任务
        task = RecognitionTask(
            signal_data=signal_data,
            recognition_params=recognition_params,
            task_id=task_id,
            priority=priority,
            parent=self
        )
        
        # 连接任务信号
        self._connect_task_signals(task)
        
        # 提交任务到管理器
        if self._task_manager.submit_task(task):
            app_logger.info(f"识别任务已提交 - task_id: {task.task_id}")
            return task.task_id
        else:
            raise RuntimeError(f"任务提交失败 - task_id: {task.task_id}")
    
    def pause_recognition(self, task_id: str) -> bool:
        """暂停识别任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功暂停
        """
        success = self._task_manager.pause_task(task_id)
        if success:
            app_logger.info(f"识别任务已暂停 - task_id: {task_id}")
        else:
            app_logger.warning(f"识别任务暂停失败 - task_id: {task_id}")
        return success
    
    def resume_recognition(self, task_id: str) -> bool:
        """恢复识别任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功恢复
        """
        success = self._task_manager.resume_task(task_id)
        if success:
            app_logger.info(f"识别任务已恢复 - task_id: {task_id}")
        else:
            app_logger.warning(f"识别任务恢复失败 - task_id: {task_id}")
        return success
    
    def cancel_recognition(self, task_id: str) -> bool:
        """取消识别任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        success = self._task_manager.cancel_task(task_id)
        if success:
            app_logger.info(f"识别任务已取消 - task_id: {task_id}")
        else:
            app_logger.warning(f"识别任务取消失败 - task_id: {task_id}")
        return success
    
    def get_recognition_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取识别任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息，如果任务不存在则返回None
        """
        task = self._task_manager.get_task(task_id)
        if task:
            return task.get_summary()
        return None
    
    def get_active_recognitions(self) -> List[Dict[str, Any]]:
        """获取所有活跃的识别任务
        
        Returns:
            活跃任务状态列表
        """
        active_tasks = self._task_manager.get_active_tasks()
        return [task.get_summary() for task in active_tasks]
    
    def get_completed_recognitions(self) -> List[Dict[str, Any]]:
        """获取所有已完成的识别任务
        
        Returns:
            已完成任务状态列表
        """
        completed_tasks = self._task_manager.get_completed_tasks()
        return [task.get_summary() for task in completed_tasks]
    
    def get_queue_status(self) -> Dict[str, int]:
        """获取任务队列状态
        
        Returns:
            队列状态信息
        """
        return self._task_manager.get_queue_status()
    
    def clear_completed_tasks(self) -> int:
        """清理已完成的任务
        
        Returns:
            清理的任务数量
        """
        count = self._task_manager.clear_completed_tasks()
        app_logger.info(f"已清理 {count} 个已完成任务")
        return count
    
    def shutdown(self):
        """关闭应用服务"""
        app_logger.info("正在关闭识别应用服务...")
        self._task_manager.shutdown()
        app_logger.info("识别应用服务已关闭")
    
    def _execute_recognition_task(self, task: RecognitionTask) -> TaskResult:
        """执行识别任务的回调函数
        
        Args:
            task: 要执行的识别任务
            
        Returns:
            任务执行结果
        """
        app_logger.info(f"开始执行识别任务 - task_id: {task.task_id}")

        # 添加调试信息
        app_logger.info(f"任务信号数据形状: {task.signal_data.shape if task.signal_data is not None else 'None'}")
        app_logger.info(f"任务识别参数: {task.recognition_params}")
        app_logger.info(f"工作流对象: {self._workflow}")
        app_logger.info(f"领域服务状态: clustering={self._clustering_service is not None}, "
                       f"recognition={self._recognition_service is not None}, "
                       f"parameter_extraction={self._parameter_extraction_service is not None}, "
                       f"session={self._session_service is not None}")

        try:
            # 使用工作流执行任务
            app_logger.info(f"正在调用工作流执行任务...")
            result = self._workflow.execute(task)
            app_logger.info(f"工作流执行完成，结果: success={result.success}")
            
            if result.success:
                app_logger.info(f"识别任务执行成功 - task_id: {task.task_id}")
            else:
                app_logger.error(f"识别任务执行失败 - task_id: {task.task_id}, error: {result.error_message}")
            
            return result
            
        except Exception as e:
            error_msg = f"识别任务执行异常: {str(e)}"
            app_logger.error(f"识别任务执行异常 - task_id: {task.task_id}, error: {error_msg}")
            return TaskResult(success=False, error_message=error_msg)
    
    def _connect_task_manager_signals(self):
        """连接任务管理器信号"""
        self._task_manager.task_started.connect(self._on_task_started)
        self._task_manager.task_completed.connect(self._on_task_completed)
        self._task_manager.queue_status_changed.connect(self._on_queue_status_changed)
    
    def _connect_task_signals(self, task: RecognitionTask):
        """连接任务信号"""
        task.progress_updated.connect(self._on_stage_progress_updated)
        task.stage_completed.connect(self._on_stage_completed)
        task.task_completed.connect(self._on_recognition_completed)
        task.task_failed.connect(self._on_recognition_failed)
    
    def _on_task_started(self, task_id: str):
        """任务开始处理"""
        task = self._task_manager.get_task(task_id)
        if task and task.session_id:
            self.recognition_started.emit(task_id, task.session_id)
    
    def _on_task_completed(self, task_id: str, success: bool):
        """任务完成处理"""
        # 更新队列状态信号会自动发出
        pass
    
    def _on_queue_status_changed(self, pending: int, running: int):
        """队列状态变化处理"""
        status = self._task_manager.get_queue_status()
        self.queue_status_changed.emit(pending, running, status['completed'])
    
    def _on_stage_progress_updated(self, task_id: str, stage: RecognitionStage, progress: float):
        """阶段进度更新处理"""
        self.stage_progress_updated.emit(task_id, stage.value, progress)
    
    def _on_stage_completed(self, task_id: str, stage: RecognitionStage, results: dict):
        """阶段完成处理"""
        self.stage_completed.emit(task_id, stage.value, results)
    
    def _on_recognition_completed(self, task_id: str, result: TaskResult):
        """识别完成处理"""
        results = {
            'session_id': result.session_id,
            'final_parameters': result.final_parameters,
            'execution_time': result.execution_time
        }
        self.recognition_completed.emit(task_id, result.success, results)
    
    def _on_recognition_failed(self, task_id: str, error_message: str):
        """识别失败处理"""
        self.recognition_failed.emit(task_id, error_message)
