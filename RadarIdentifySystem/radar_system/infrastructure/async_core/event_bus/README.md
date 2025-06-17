# 简化版事件总线

本目录实现了雷达信号多维参数联合智能分类系统中的简化版事件总线机制。

## 主要改进

1. **简化API**：移除了复杂的Event类和EventDispatcher，提供更直观的事件发布-订阅机制
2. **统一事件处理**：事件处理器直接接收事件数据，无需从Event对象中提取
3. **增强异步支持**：添加publish_async方法，简化异步事件发布
4. **更好的与Qt集成**：UI处理器同时处理Qt信号槽和事件总线事件，作为两者的桥梁

## 核心组件

- **EventBus**：提供事件的发布-订阅功能，支持同步和异步事件处理

## 使用方法

### 创建事件总线

```python
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus

# 创建事件总线
event_bus = EventBus()
```

### 订阅事件

```python
# 定义事件处理函数
def on_signal_loaded(data):
    print(f"信号数据已加载: {data.get('file_path')}")

# 订阅事件
event_bus.subscribe("signal_loaded", on_signal_loaded)
```

### 发布事件

```python
# 同步发布
event_bus.publish("signal_loaded", {
    "file_path": "data.xlsx",
    "data_count": 1000
})

# 异步发布
event_bus.publish_async("processing_started", {"signal_id": "123"})
```

### 取消订阅

```python
event_bus.unsubscribe("signal_loaded", on_signal_loaded)
```

### 清除所有订阅

```python
event_bus.clear()
```

## 与UI集成

UI处理器（如SignalImportHandler和SignalSliceHandler）通过以下方式与事件总线集成：

1. 订阅事件总线事件
2. 处理事件并发出Qt信号
3. 处理UI事件并发布事件到事件总线

例如：

```python
class SignalImportHandler(QObject):
    # 定义Qt信号
    import_started = pyqtSignal()
    import_finished = pyqtSignal(bool)
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        
        # 订阅事件总线事件
        self.event_bus.subscribe("import_task_completed", self._on_import_task_completed)
    
    def _on_import_task_completed(self, data):
        # 处理事件并发出Qt信号
        self.import_finished.emit(True)
    
    def import_data(self, file_path):
        # 处理UI事件并发布事件到事件总线
        self.event_bus.publish("import_task_started", {"file_path": file_path})
```

## 事件命名规范

- 使用动词_名词格式，如"import_started"、"processing_completed"
- 使用过去时表示已完成的事件，如"data_loaded"
- 使用现在时表示正在进行的事件，如"processing_starting"
- 使用特定前缀区分领域，如"signal_"、"recognition_"

## 事件数据规范

事件数据使用字典格式，包含以下信息：

- 必要的标识信息，如ID、类型等
- 操作结果，如成功/失败标志
- 相关数据或引用
- 错误信息（如果有） 