"""事件常量定义

定义系统中使用的事件常量，确保事件命名的一致性。
遵循YAGNI原则，只包含当前实际需要且有发布者和订阅者的事件。

事件命名规范：domain.action.status
- domain: 业务领域（signal, system）
- action: 具体操作（data.loading, slice.process）
- status: 操作状态（started, completed, failed）
"""

class SignalEvents:
    """信号处理相关事件常量"""

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
