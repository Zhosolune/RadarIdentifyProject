# 简化的事件系统改进方案

## 问题回顾

原始问题：
1. 事件命名不统一（如`slice_task_started` vs `slice_processing_started`）
2. 任务层和应用服务层重复发布相同语义的事件
3. 事件处理逻辑简单，主要是日志记录

## 简化解决方案

### 1. 统一事件命名 (`simple_event_constants.py`)

```python
class SignalEvents:
    # 信号数据导入事件
    DATA_IMPORT_STARTED = "signal.data.import.started"
    DATA_IMPORT_COMPLETED = "signal.data.import.completed"
    DATA_IMPORT_FAILED = "signal.data.import.failed"
    
    # 信号切片处理事件
    SLICE_PROCESSING_STARTED = "signal.slice.process.started"
    SLICE_PROCESSING_COMPLETED = "signal.slice.process.completed"
    SLICE_PROCESSING_FAILED = "signal.slice.process.failed"
```

**核心原则**：
- 只定义当前实际需要的事件
- 使用清晰的命名格式：`domain.entity.action.status`
- 避免定义未来可能用到但当前不需要的事件

### 2. 消除重复事件发布

**任务层简化**：
```python
# 旧方式 - 任务层发布事件
def execute(self):
    self.event_bus.publish("slice_task_started", data)  # 重复！
    result = self.service.start_slice_processing(signal)
    self.event_bus.publish("slice_task_completed", data)  # 重复！
    return result

# 新方式 - 任务层专注执行
def execute(self):
    # 直接调用服务，由服务层发布事件
    return self.service.start_slice_processing(signal)
```

**职责明确**：
- **任务层**：专注任务执行，不发布事件
- **应用服务层**：发布业务事件
- **UI层**：监听业务事件，发布UI状态信号

### 3. 简化事件处理器 (`simple_signal_slice_handler.py`)

```python
class SimpleSignalSliceHandler(QObject):
    # 只定义实际需要的Qt信号
    slice_started = pyqtSignal()
    slice_completed = pyqtSignal(bool, int)  # 成功标志, 切片数量
    slice_failed = pyqtSignal(str)  # 错误信息
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        self._subscribe_events()
    
    def _subscribe_events(self):
        # 只订阅实际需要的事件
        self.event_bus.subscribe(SignalEvents.SLICE_PROCESSING_STARTED, self._on_slice_started)
        self.event_bus.subscribe(SignalEvents.SLICE_PROCESSING_COMPLETED, self._on_slice_completed)
        self.event_bus.subscribe(SignalEvents.SLICE_PROCESSING_FAILED, self._on_slice_failed)
```

**移除的过度设计**：
- ❌ 进度更新信号（没有接收者）
- ❌ 复杂的事件处理基类
- ❌ 性能监控功能
- ❌ 复杂的数据验证

## 实施步骤

### 1. 更新事件常量

```python
# 在 signal_service.py 中
from radar_system.infrastructure.async_core.event_bus.simple_event_constants import SignalEvents

# 替换事件名称
self.event_bus.publish(SignalEvents.SLICE_PROCESSING_STARTED, data)
```

### 2. 简化任务层

```python
# 在 signal_tasks.py 中
def execute(self):
    # 移除事件发布，专注执行
    return self.service.start_slice_processing(self.signal)
```

### 3. 更新UI处理器

```python
# 使用简化的处理器
from radar_system.interface.handlers.simple_signal_slice_handler import SimpleSignalSliceHandler

# 在主窗口中
self.slice_handler = SimpleSignalSliceHandler(self.event_bus)
```

## 核心改进

### ✅ 解决的问题

1. **事件命名统一**：使用一致的命名规范
2. **消除重复发布**：任务层不再发布业务事件
3. **简化架构**：移除不必要的抽象和复杂性
4. **职责明确**：每层只做自己该做的事

### ✅ 保留的功能

1. **事件总线机制**：UI和业务逻辑解耦
2. **线程安全**：确保UI更新的安全性
3. **错误处理**：基本的异常处理和日志记录
4. **向后兼容**：提供事件迁移映射

### ❌ 移除的过度设计

1. 复杂的事件处理基类
2. 性能监控功能
3. 详细的事件数据验证
4. 不必要的抽象模板
5. 没有接收者的信号

## 使用示例

### 启动切片处理

```python
# 在主窗口中
def _on_start_slice(self):
    signal = self.signal_service.get_current_signal()
    self.slice_handler.start_slice(self, signal)

# 监听切片完成
self.slice_handler.slice_completed.connect(self._on_slice_completed)

def _on_slice_completed(self, success, slice_count):
    if success:
        self.status_label.setText(f"切片完成，生成{slice_count}个切片")
    else:
        self.status_label.setText("切片失败")
```

### 事件流程

```
用户点击按钮 → UI处理器 → 创建任务 → 任务执行 → 应用服务 → 发布事件 → UI处理器 → 更新界面
```

## 总结

这个简化方案：

1. **解决了核心问题**：事件命名统一、消除重复发布
2. **保持简单实用**：只实现当前需要的功能
3. **易于维护**：代码清晰，职责明确
4. **避免过度设计**：不添加当前用不到的功能

**核心原则**：YAGNI（You Aren't Gonna Need It）- 只实现当前需要的功能，避免为未来可能的需求过度设计。
