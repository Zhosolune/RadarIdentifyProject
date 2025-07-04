"""任务管理模块

本模块提供应用层任务管理功能，包括任务定义、队列管理和执行控制。
"""

from .recognition_task import RecognitionTask, TaskResult
from .task_manager import TaskManager
from .task_enums import TaskStatus, TaskPriority, RecognitionStage

__all__ = [
    'RecognitionTask',
    'TaskResult',
    'TaskManager',
    'TaskStatus',
    'TaskPriority',
    'RecognitionStage'
]