"""识别处理器

处理与雷达信号识别相关的所有UI事件和交互。
"""

import logging
from typing import Dict, Any, Optional, List
import numpy as np

from PyQt5.QtCore import pyqtSignal, QObject

from radar_system.application.services.recognition_application_service import RecognitionApplicationService
from radar_system.application.tasks.task_enums import TaskStatus, TaskPriority, RecognitionStage
from radar_system.infrastructure.common.thread_safe_signal_emitter import ThreadSafeSignalEmitter


# 创建处理器日志记录器
handler_logger = logging.getLogger('interface.handlers')


class RecognitionHandler(ThreadSafeSignalEmitter):
    """识别处理器
    
    处理与雷达信号识别相关的所有UI事件，包括：
    - 启动识别任务
    - 控制任务执行（暂停/恢复/取消）
    - 查询任务状态和进度
    - 转发应用层信号到UI层
    
    Signals:
        recognition_started: 识别开始信号 (task_id: str, session_id: str)
        stage_progress_updated: 阶段进度更新信号 (task_id: str, stage_name: str, progress: float)
        stage_completed: 阶段完成信号 (task_id: str, stage_name: str, result: dict)
        recognition_completed: 识别完成信号 (task_id: str, success: bool, result: dict)
        recognition_failed: 识别失败信号 (task_id: str, error_message: str)
        task_status_changed: 任务状态变化信号 (task_id: str, status: str)
        queue_status_updated: 队列状态更新信号 (total: int, active: int)
    """
    
    # 定义Qt信号 - 统一命名格式：{功能}_{动作}_{状态}
    recognition_started = pyqtSignal(str, str)  # task_id, session_id
    stage_progress_updated = pyqtSignal(str, str, float)  # task_id, stage_name, progress
    stage_completed = pyqtSignal(str, str, dict)  # task_id, stage_name, result
    recognition_completed = pyqtSignal(str, bool, dict)  # task_id, success, result
    recognition_failed = pyqtSignal(str, str)  # task_id, error_message
    task_status_changed = pyqtSignal(str, str)  # task_id, status
    queue_status_updated = pyqtSignal(int, int)  # total, active
    
    def __init__(self):
        """初始化识别处理器"""
        super().__init__()
        
        # 创建应用服务实例
        self._recognition_service = RecognitionApplicationService()
        
        # 连接应用服务信号到处理器信号
        self._connect_application_signals()
        
        handler_logger.info("RecognitionHandler 初始化完成")
    
    def _connect_application_signals(self):
        """连接应用服务信号到处理器信号"""
        # 连接识别相关信号
        self._recognition_service.recognition_started.connect(
            lambda task_id, session_id: self.safe_emit_signal(
                self.recognition_started, task_id, session_id
            )
        )

        self._recognition_service.stage_progress_updated.connect(
            lambda task_id, stage_name, progress: self.safe_emit_signal(
                self.stage_progress_updated, task_id, stage_name, progress
            )
        )

        self._recognition_service.stage_completed.connect(
            lambda task_id, stage_name, result: self.safe_emit_signal(
                self.stage_completed, task_id, stage_name, result
            )
        )

        self._recognition_service.recognition_completed.connect(
            lambda task_id, success, result: self.safe_emit_signal(
                self.recognition_completed, task_id, success, result
            )
        )

        self._recognition_service.recognition_failed.connect(
            lambda task_id, error_message: self.safe_emit_signal(
                self.recognition_failed, task_id, error_message
            )
        )
        
        # 连接队列状态信号
        self._recognition_service.queue_status_changed.connect(
            lambda pending, running, completed: self.safe_emit_signal(
                self.queue_status_updated, pending + running, running
            )
        )
    
    def start_recognition(self, 
                         signal_data: np.ndarray,
                         recognition_params: Optional[Dict[str, Any]] = None,
                         priority: TaskPriority = TaskPriority.NORMAL) -> Optional[str]:
        """启动识别任务
        
        Args:
            signal_data: 信号数据
            recognition_params: 识别参数
            priority: 任务优先级
            
        Returns:
            任务ID，如果启动失败返回None
        """
        try:
            handler_logger.info(f"启动识别任务，数据形状: {signal_data.shape}, 优先级: {priority.display_name}")
            
            # 调用应用服务启动识别
            task_id = self._recognition_service.start_recognition(
                signal_data=signal_data,
                recognition_params=recognition_params or {},
                priority=priority
            )
            
            if task_id:
                handler_logger.info(f"识别任务启动成功: {task_id}")
            else:
                handler_logger.warning("识别任务启动失败")
                
            return task_id
            
        except Exception as e:
            error_msg = f"启动识别任务时发生错误: {str(e)}"
            handler_logger.error(error_msg)
            return None
    
    def pause_recognition(self, task_id: str) -> bool:
        """暂停识别任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否暂停成功
        """
        try:
            success = self._recognition_service.pause_recognition(task_id)
            if success:
                handler_logger.info(f"任务暂停成功: {task_id}")
            else:
                handler_logger.warning(f"任务暂停失败: {task_id}")
            return success
            
        except Exception as e:
            handler_logger.error(f"暂停任务时发生错误: {str(e)}")
            return False
    
    def resume_recognition(self, task_id: str) -> bool:
        """恢复识别任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否恢复成功
        """
        try:
            success = self._recognition_service.resume_recognition(task_id)
            if success:
                handler_logger.info(f"任务恢复成功: {task_id}")
            else:
                handler_logger.warning(f"任务恢复失败: {task_id}")
            return success
            
        except Exception as e:
            handler_logger.error(f"恢复任务时发生错误: {str(e)}")
            return False
    
    def cancel_recognition(self, task_id: str) -> bool:
        """取消识别任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        try:
            success = self._recognition_service.cancel_recognition(task_id)
            if success:
                handler_logger.info(f"任务取消成功: {task_id}")
            else:
                handler_logger.warning(f"任务取消失败: {task_id}")
            return success
            
        except Exception as e:
            handler_logger.error(f"取消任务时发生错误: {str(e)}")
            return False
    
    def get_recognition_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取识别任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息，如果任务不存在返回None
        """
        try:
            return self._recognition_service.get_recognition_status(task_id)
        except Exception as e:
            handler_logger.error(f"获取任务状态时发生错误: {str(e)}")
            return None
    
    def get_active_recognitions(self) -> List[Dict[str, Any]]:
        """获取所有活跃的识别任务
        
        Returns:
            活跃任务列表
        """
        try:
            return self._recognition_service.get_active_recognitions()
        except Exception as e:
            handler_logger.error(f"获取活跃任务时发生错误: {str(e)}")
            return []
    
    def get_queue_status(self) -> Dict[str, int]:
        """获取任务队列状态
        
        Returns:
            队列状态信息
        """
        try:
            return self._recognition_service.get_queue_status()
        except Exception as e:
            handler_logger.error(f"获取队列状态时发生错误: {str(e)}")
            return {"total": 0, "active": 0, "pending": 0}
    
    def set_domain_services(self, 
                           clustering_service: Any,
                           recognition_service: Any,
                           parameter_extraction_service: Any,
                           session_service: Any):
        """设置领域服务依赖
        
        Args:
            clustering_service: 聚类服务
            recognition_service: 识别服务
            parameter_extraction_service: 参数提取服务
            session_service: 会话服务
        """
        self._recognition_service.set_domain_services(
            clustering_service=clustering_service,
            recognition_service=recognition_service,
            parameter_extraction_service=parameter_extraction_service,
            session_service=session_service
        )
        handler_logger.info("领域服务依赖设置完成")
    
    def shutdown(self):
        """关闭处理器，清理资源"""
        try:
            self._recognition_service.shutdown()
            handler_logger.info("RecognitionHandler 关闭完成")
        except Exception as e:
            handler_logger.error(f"关闭处理器时发生错误: {str(e)}")
