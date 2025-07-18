---
type: "always_apply"
---

# 异步处理和任务规范

## 异步处理模式
使用简化的Handler直接调用Service设计:

✅ **正确示例** - Handler直接调用Service:
```python
class SignalSliceHandler(ThreadSafeSignalEmitter):
    def __init__(self, signal_service: SignalService):
        super().__init__()
        self.signal_service = signal_service

    def start_slice(self, signal: SignalData, thread_pool):
        # 直接提交Service方法到线程池，消除Task抽象层
        future = thread_pool.submit(
            self.signal_service.start_slice_processing,
            signal
        )
        future.add_done_callback(self._handle_slice_result)
```

❌ **错误示例** - 过度抽象的Task层:
```python
class SignalSliceTask:
    # 避免不必要的Task抽象层
    def execute(self):
        return self.service.start_slice_processing(self.signal)
```

## AsyncExecutor使用规范
参考 [async_executor.py](mdc:RadarIdentifySystem/radar_system/infrastructure/common/async_executor.py):

✅ **正确示例** - 使用AsyncExecutor简化异步执行:
```python
class SignalImportHandler(ThreadSafeSignalEmitter):
    def import_data(self, window, file_path: str):
        AsyncExecutor.execute_async(
            window.signal_service.load_signal_file,
            self,
            "_handle_import_result_async",
            file_path
        )

    @pyqtSlot(object)
    def _handle_import_result_async(self, result):
        success, message, signal = result
        self.safe_emit_signal(self.import_completed, success, message)
```

❌ **错误示例** - 过度复杂的线程池封装:
```python
class ComplexThreadPoolManager:
    # 避免不必要的包装层，使用AsyncExecutor替代
    pass
```

## 任务结果处理
必须使用统一的结果处理模式:

✅ **正确示例** - 统一的结果处理:
```python
def _handle_task_result(self, future):
    try:
        success, message, result = future.result()
        if success:
            self.safe_emit_signal(self.operation_completed, True, result)
        else:
            self.safe_emit_signal(self.operation_failed, message)
    except Exception as e:
        error_msg = f"处理任务结果时出错: {str(e)}"
        self.safe_emit_signal(self.operation_failed, error_msg)
```

❌ **错误示例** - 不一致的结果处理:
```python
def _handle_task_result(self, future):
    result = future.result()  # 没有统一的错误处理
    self.update_ui(result)    # 直接UI更新，非线程安全
```

## 线程安全信号发射
所有Handler必须继承ThreadSafeSignalEmitter:

参考 [thread_safe_signal_emitter.py](mdc:RadarIdentifySystem/radar_system/infrastructure/common/thread_safe_signal_emitter.py):

✅ **正确示例**:
```python
class SignalImportHandler(ThreadSafeSignalEmitter):
    import_completed = pyqtSignal(bool, object)
    
    def _emit_import_completed(self, success: bool, result: Any):
        self.safe_emit_signal(self.import_completed, success, result)
```

## 异步处理生命周期管理
- **接收事件**: Handler接收UI事件
- **异步执行**: 使用AsyncExecutor创建线程执行Service方法
- **监听结果**: 通过线程安全回调处理Service执行结果
- **信号发射**: 使用线程安全方式发射信号到UI

## 操作类型规范
定义标准的操作类型常量:
```python
class OperationType:
    SIGNAL_IMPORT = "signal_import"
    SIGNAL_SLICE = "signal_slice"
    SIGNAL_RECOGNITION = "signal_recognition"
    DATA_EXPORT = "data_export"
```

## 异步操作最佳实践
1. 使用dataclass定义任务数据结构
2. 任务执行方法必须返回统一格式
3. 所有耗时操作必须在后台线程执行
4. UI更新必须通过线程安全信号发射
5. 任务失败时记录详细日志
6. 避免复杂的任务依赖关系

## Worker类设计
参考 [worker.py](mdc:RadarIdentifySystem/radar_system/infrastructure/async_core/worker.py):

简化的Worker设计，专注于任务执行:
```python
class TaskWorker:
    def __init__(self, task_queue):
        self._task_queue = task_queue
        
    def execute_task(self, task):
        return task.execute()
```
