"""事件常量定义

定义系统中使用的事件常量，确保事件命名的一致性。
只包含当前实际需要的事件，避免过度设计。
"""

class SignalEvents:
    """信号处理相关事件常量"""
    
    # 信号数据导入事件
    DATA_IMPORT_STARTED = "signal.data.import.started"
    DATA_IMPORT_COMPLETED = "signal.data.import.completed"
    DATA_IMPORT_FAILED = "signal.data.import.failed"
    
    # 信号数据加载事件
    DATA_LOADING_STARTED = "signal.data.loading.started"
    DATA_LOADING_COMPLETED = "signal.data.loading.completed"
    DATA_LOADING_FAILED = "signal.data.loading.failed"
    
    # 信号数据验证事件
    DATA_VALIDATION_FAILED = "signal.data.validation.failed"
    
    # 信号切片处理事件
    SLICE_PROCESSING_STARTED = "signal.slice.process.started"
    SLICE_PROCESSING_COMPLETED = "signal.slice.process.completed"
    SLICE_PROCESSING_FAILED = "signal.slice.process.failed"


class SystemEvents:
    """系统级事件常量"""
    
    # 应用程序生命周期
    APP_STARTED = "system.app.lifecycle.started"
    APP_SHUTDOWN = "system.app.lifecycle.shutdown"
    
    # 错误和异常
    CRITICAL_ERROR = "system.error.critical.occurred"


# 旧事件名称到新事件名称的映射（用于迁移）
EVENT_MIGRATION_MAP = {
    # 移除的任务层事件
    "import_task_started": SignalEvents.DATA_IMPORT_STARTED,
    "import_task_completed": SignalEvents.DATA_IMPORT_COMPLETED,
    "import_task_failed": SignalEvents.DATA_IMPORT_FAILED,
    "slice_task_started": "DEPRECATED",  # 建议移除
    "slice_task_completed": "DEPRECATED",  # 建议移除
    "slice_task_failed": "DEPRECATED",  # 建议移除
    
    # 重命名的事件
    "signal_loading_started": SignalEvents.DATA_LOADING_STARTED,
    "signal_loading_completed": SignalEvents.DATA_LOADING_COMPLETED,
    "signal_loading_failed": SignalEvents.DATA_LOADING_FAILED,
    "signal_validation_failed": SignalEvents.DATA_VALIDATION_FAILED,
    "slice_processing_started": SignalEvents.SLICE_PROCESSING_STARTED,
    "slice_processing_completed": SignalEvents.SLICE_PROCESSING_COMPLETED,
    "slice_processing_failed": SignalEvents.SLICE_PROCESSING_FAILED,
}
