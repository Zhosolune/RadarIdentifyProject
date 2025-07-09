# RadarIdentifySystem 项目开发规范文档

## 概述

本文档基于对RadarIdentifySystem项目导入功能和切片功能的深入分析，遵循YAGNI（You Aren't Gonna Need It）原则和简化架构的要求，制定了一套实用的开发规范。

### 核心设计理念

1. **简化优于复杂**：避免过度工程化，优先选择简单直接的解决方案
2. **实用性优先**：规范必须解决实际问题，而非追求理论完美
3. **YAGNI原则**：只实现当前确实需要的功能，避免为未来可能的需求过度设计

### 解决的核心问题

本规范专注于解决三个具体的架构问题：
- **数据存储重复**：Handler层和Service层重复存储业务数据
- **命名不一致**：信号和方法命名缺乏统一标准
- **信号发射不规范**：信号发射位置和时机不统一

### 简化架构的优势

通过移除过度设计的抽象层，本规范实现：
- 降低代码复杂性和学习成本
- 提高开发效率和维护便利性
- 保持架构灵活性，支持真正需要时的扩展

## 1. 数据存储层级规范

### 1.1 各层数据存储职责

#### UI层 (Interface)
**✅ 应该存储：**
- 临时UI状态（如当前选中项、输入框内容）
- 会话级配置（如窗口大小、用户偏好）
- 显示相关的缓存数据

**❌ 不应该存储：**
- 业务实体数据
- 处理结果数据
- 跨组件共享的状态

```python
# ✅ 正确示例
class SignalSliceHandler(ThreadSafeSignalEmitter):
    def __init__(self):
        super().__init__()
        # 只存储UI相关状态
        self._last_directory = None  # 会话级路径记忆
        self._ui_state = "idle"      # UI状态
        
    # ❌ 错误示例 - 不应在Handler中存储业务数据
    # self.current_slices = slices  # 违反层级职责
```

#### Service层 (Application)
**✅ 应该存储：**
- 当前处理的业务实体
- 服务级别的状态和配置
- 缓存的计算结果

**❌ 不应该存储：**
- UI相关状态
- 基础设施层的实现细节

```python
# ✅ 正确示例
class SignalService:
    def __init__(self):
        # 存储当前业务实体
        self.current_signal: Optional[SignalData] = None
        self.current_slices: Optional[List[SignalSlice]] = None
        
    def start_slice_processing(self, signal: SignalData):
        # 在Service层存储和管理业务数据
        slices = self.processor.slice_signal(signal)
        self.current_slices = slices  # ✅ 正确的存储位置
        return True, "切片处理完成", slices
```

### 1.2 数据传递标准模式

#### 直接参数传递原则
```python
# ✅ 简化方案：直接传递具体类型，避免不必要的转换
class SignalImportHandler:
    def start_import(self, window, file_path: str):
        # 直接传递具体参数，无需复杂的转换接口
        task = SignalImportTask(file_path=file_path, service=window.signal_service)
        future = window.thread_pool.submit(task.execute)

class SignalService:
    def load_signal_file(self, file_path: str) -> Tuple[bool, str, Optional[SignalData]]:
        # 直接接收具体类型，保持统一返回格式
        try:
            signal_data = self.excel_reader.read_file(file_path)
            return True, "导入成功", signal_data
        except Exception as e:
            return False, f"导入失败: {str(e)}", None
```

#### 统一的结果返回格式
```python
# 所有层间调用都使用统一的结果格式：Tuple[bool, str, Optional[Any]]
# bool: 操作是否成功
# str: 消息描述（成功或错误信息）
# Optional[Any]: 结果数据（成功时）或None（失败时）

# 示例
def process_signal(self, signal: SignalData) -> Tuple[bool, str, Optional[List[SignalSlice]]]:
    try:
        slices = self.processor.slice_signal(signal)
        return True, "处理完成", slices
    except Exception as e:
        return False, f"处理失败: {str(e)}", None
```

## 2. 依赖管理规范

### 2.1 简单依赖管理原则

#### 适合使用单例的组件
```python
# ✅ 配置管理 - 全局唯一
class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# ✅ 线程池管理 - 资源共享
class ThreadPoolManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.thread_pool = ThreadPoolExecutor(max_workers=4)
        return cls._instance
```

#### 不适合使用单例的组件
```python
# ❌ 业务服务 - 应支持多实例
class SignalService:
    def __init__(self, processor, excel_reader):
        self.processor = processor
        self.excel_reader = excel_reader

# ❌ UI处理器 - 应支持多实例
class SignalImportHandler:
    def __init__(self):
        super().__init__()
```

### 2.2 简单的构造函数注入

#### 直接依赖创建（推荐）
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 简单直接的依赖创建，避免复杂的注册机制
        self.config_manager = ConfigManager()  # 单例通过类本身管理
        self.thread_pool = ThreadPoolManager().thread_pool

        # 构造函数注入
        self.signal_service = SignalService(
            processor=SignalProcessor(),
            excel_reader=ExcelReader()
        )

        self.import_handler = SignalImportHandler()
        self.slice_handler = SignalSliceHandler()

class SignalService:
    def __init__(self, processor: SignalProcessor, excel_reader: ExcelReader):
        self.processor = processor
        self.excel_reader = excel_reader
        self.current_signal = None
        self.current_slices = None
```

## 3. 命名约定规范

### 3.1 统一的命名模式

#### 类名规范
```python
# Handler类：{Entity}{Action}Handler
class SignalImportHandler:     # ✅ 正确
class SignalSliceHandler:      # ✅ 正确

# Service类：{Domain}Service
class SignalService:           # ✅ 正确
class RecognitionService:      # ✅ 正确

# Task类：{Entity}{Action}Task
class SignalImportTask:        # ✅ 正确
class SignalSliceTask:         # ✅ 正确

# Entity类：{Domain}{Entity}
class SignalData:              # ✅ 正确
class SignalSlice:             # ✅ 正确
```

#### 方法名规范
```python
# 统一使用 start_{action} 格式
class SignalImportHandler:
    def start_import(self, window, file_path: str):  # ✅ 统一格式
        pass

class SignalSliceHandler:
    def start_slice(self, window, signal: SignalData):  # ✅ 统一格式
        pass

# 私有方法使用下划线前缀
def _handle_import_result(self, future, window):     # ✅ 正确
def _handle_slice_result(self, future, window):      # ✅ 正确
```

### 3.2 Qt信号标准命名格式

#### 信号命名规范：{功能}_{动作}_{状态}
```python
class SignalImportHandler(ThreadSafeSignalEmitter):
    # ✅ 统一的信号命名格式
    import_started = pyqtSignal()                    # 导入开始
    import_completed = pyqtSignal(bool)              # 导入完成
    import_failed = pyqtSignal(str)                  # 导入失败

class SignalSliceHandler(ThreadSafeSignalEmitter):
    # ✅ 统一的信号命名格式
    slice_started = pyqtSignal()                     # 切片开始
    slice_completed = pyqtSignal(bool, int)          # 切片完成
    slice_failed = pyqtSignal(str)                   # 切片失败
```

### 3.3 文件和目录组织规范
```
radar_system/
├── interface/
│   ├── handlers/
│   │   ├── signal_import_handler.py      # {entity}_{action}_handler.py
│   │   └── signal_slice_handler.py
│   └── views/
│       └── main_window.py
├── application/
│   ├── services/
│   │   └── signal_service.py             # {domain}_service.py
│   └── tasks/
│       └── signal_tasks.py               # {domain}_tasks.py
├── domain/
│   └── signal/
│       ├── entities/
│       │   └── signal.py                 # {entity}.py
│       └── services/
│           └── processor.py              # {service}.py
└── infrastructure/
    ├── persistence/
    │   └── excel/
    │       └── excel_reader.py           # {technology}_{purpose}.py
    └── common/
        └── logging.py
```

## 4. 跨层调用规范

### 4.1 允许的调用关系
```
┌─────────────────┐
│   UI层 (Interface)   │  ← 用户交互、界面显示
├─────────────────┤      ↓ 允许调用
│ 应用服务层 (Application) │  ← 业务流程协调
├─────────────────┤      ↓ 允许调用
│ 领域服务层 (Domain)     │  ← 核心业务逻辑
├─────────────────┤      ↓ 允许调用
│ 基础设施层 (Infrastructure) │  ← 数据持久化、外部服务
└─────────────────┘
```

### 4.2 调用规则实施
```python
# ✅ 正确的调用链
class MainWindow(QMainWindow):
    def _on_start_slice(self):
        # UI层 → Handler层
        signal = self.signal_service.get_current_signal()
        self.slice_handler.start_slice(self, signal)

class SignalSliceHandler:
    def start_slice(self, window, signal: SignalData):
        # Handler层 → Task层 → Service层
        slice_task = SignalSliceTask(signal=signal, service=window.signal_service)
        future = window.thread_pool.submit(slice_task.execute)

class SignalSliceTask:
    def execute(self):
        # Task层 → Service层
        return self.service.start_slice_processing(self.signal)

class SignalService:
    def start_slice_processing(self, signal: SignalData):
        # Service层 → Domain层
        slices = self.processor.slice_signal(signal)
        return True, "切片处理完成", slices
```

### 4.3 实体属性访问规范
```python
# ✅ 通过公共接口访问
class SignalData:
    def __init__(self, id: str, raw_data: np.ndarray):
        self._id = id
        self._raw_data = raw_data
    
    @property
    def id(self) -> str:
        """获取信号ID"""
        return self._id
    
    @property
    def raw_data(self) -> np.ndarray:
        """获取原始数据"""
        return self._raw_data.copy()  # 返回副本保护数据

# ❌ 避免直接访问私有属性
# signal._raw_data  # 不推荐
```

## 5. Qt信号发射规范

### 5.1 信号发射时机和位置

#### 集中式信号发射架构
```python
# ✅ 只在Handler层发射Qt信号
class SignalImportHandler(ThreadSafeSignalEmitter):
    def _handle_import_result(self, future, window):
        """处理导入任务结果 - 统一的信号发射点"""
        try:
            success, message, signal = future.result()

            if success and signal:
                # 在Handler层发射信号
                self.safe_emit_signal(self.import_completed, True)
            else:
                self.safe_emit_signal(self.import_failed, message)
                self.safe_emit_signal(self.import_completed, False)
        except Exception as e:
            error_msg = f"处理导入结果时出错: {str(e)}"
            self.safe_emit_signal(self.import_failed, error_msg)

# ❌ 避免在Service层直接发射Qt信号
class SignalService:
    def load_signal_file(self, file_path: str):
        # Service层专注业务逻辑，不发射Qt信号
        # self.import_completed.emit(True)  # ❌ 错误做法
        return True, "导入完成", signal_data
```

### 5.2 线程安全的信号发射

#### 使用ThreadSafeSignalEmitter基类
```python
class ThreadSafeSignalEmitter(QObject):
    """线程安全的信号发射器基类"""

    def safe_emit_signal(self, signal, *args):
        """线程安全的信号发射"""
        if QThread.currentThread() is QApplication.instance().thread():
            # 在主线程中直接发射
            signal.emit(*args)
        else:
            # 在非主线程中使用QMetaObject.invokeMethod
            QMetaObject.invokeMethod(
                self, "_emit_signal_in_main_thread",
                Qt.QueuedConnection,
                Q_ARG(object, signal),
                Q_ARG(tuple, args)
            )

    @pyqtSlot(object, tuple)
    def _emit_signal_in_main_thread(self, signal, args):
        """在主线程中发射信号"""
        signal.emit(*args)
```

### 5.3 信号参数标准格式

#### 信号参数类型约定
```python
class StandardSignals:
    """标准信号定义"""

    # 开始信号：无参数
    operation_started = pyqtSignal()

    # 完成信号：bool(成功标志) + 可选的结果参数
    operation_completed = pyqtSignal(bool)                    # 简单完成
    operation_completed_with_count = pyqtSignal(bool, int)    # 带数量
    operation_completed_with_data = pyqtSignal(bool, object)  # 带数据

    # 失败信号：str(错误信息)
    operation_failed = pyqtSignal(str)

    # 进度信号：int(当前进度), int(总进度)
    operation_progress = pyqtSignal(int, int)
```

### 5.4 简单的信号连接管理

#### 依赖Qt自动管理（推荐）
```python
class MainWindow(QMainWindow):
    def _connect_signals(self):
        # 直接连接，Qt会自动管理生命周期
        # 当对象销毁时，Qt会自动断开相关连接
        self.import_handler.import_completed.connect(self._on_import_completed)
        self.slice_handler.slice_completed.connect(self._on_slice_completed)
        self.import_handler.import_failed.connect(self._on_import_failed)
        self.slice_handler.slice_failed.connect(self._on_slice_failed)

    # 只在特殊情况下手动断开（如动态创建的临时连接）
    def _disconnect_temporary_signals(self):
        if hasattr(self, '_temp_connection'):
            self.some_signal.disconnect(self._temp_slot)
            delattr(self, '_temp_connection')
```

## 6. 错误处理和日志规范

### 6.1 简单直接的错误处理

#### 基本异常类（按需使用）
```python
# 只保留确实需要的基本异常类
class DataValidationError(Exception):
    """数据验证错误"""
    pass

class ProcessingError(Exception):
    """处理错误"""
    pass
```

#### 直接的错误处理模式
```python
class SignalService:
    def load_signal_file(self, file_path: str) -> Tuple[bool, str, Optional[SignalData]]:
        """直接的错误处理，避免复杂的装饰器"""
        try:
            # 输入验证
            if not Path(file_path).exists():
                return False, "找不到指定的文件，请检查文件路径是否正确", None

            if not file_path.lower().endswith(('.xlsx', '.xls')):
                return False, "不支持的文件格式，请选择Excel文件", None

            # 执行业务逻辑
            signal_data = self.excel_reader.read_file(file_path)
            system_logger.info(f"信号文件导入成功: {file_path}")
            return True, "文件导入成功", signal_data

        except PermissionError:
            error_msg = "没有权限访问该文件，请检查文件权限"
            system_logger.error(f"文件权限错误: {file_path}")
            return False, error_msg, None
        except Exception as e:
            # 记录技术错误信息用于调试
            system_logger.error(f"文件导入技术错误: {str(e)}")
            # 返回用户友好的通用错误消息
            return False, "文件导入失败，请检查文件格式是否正确", None

    def start_slice_processing(self, signal: SignalData) -> Tuple[bool, str, Optional[List[SignalSlice]]]:
        """切片处理的错误处理示例"""
        try:
            if not signal or not signal.raw_data.size:
                return False, "信号数据为空，无法进行切片处理", None

            slices = self.processor.slice_signal(signal)
            self.current_slices = slices
            system_logger.info(f"信号切片处理完成，生成{len(slices)}个切片")
            return True, f"切片处理完成，共生成{len(slices)}个切片", slices

        except Exception as e:
            error_msg = f"切片处理失败: {str(e)}"
            system_logger.error(error_msg)
            return False, "切片处理失败，请重试", None
```

### 6.2 日志记录层级和内容标准

#### 日志级别使用规范
```python
class LoggingStandards:
    """日志记录标准"""

    @staticmethod
    def log_operation_start(logger, operation: str, entity_id: str = None):
        """记录操作开始"""
        context = {"entity_id": entity_id} if entity_id else {}
        logger.info(f"开始{operation}", extra=context)

    @staticmethod
    def log_operation_success(logger, operation: str, entity_id: str = None, result_info: dict = None):
        """记录操作成功"""
        context = {"entity_id": entity_id}
        if result_info:
            context.update(result_info)
        logger.info(f"{operation}成功完成", extra=context)

    @staticmethod
    def log_operation_error(logger, operation: str, error: str, entity_id: str = None):
        """记录操作错误"""
        context = {"entity_id": entity_id, "error": error}
        logger.error(f"{operation}失败", extra=context)

# 使用示例
class SignalService:
    def start_slice_processing(self, signal: SignalData):
        LoggingStandards.log_operation_start(system_logger, "信号切片处理", signal.id)

        try:
            slices = self.processor.slice_signal(signal)
            LoggingStandards.log_operation_success(
                system_logger, "信号切片处理", signal.id,
                {"slice_count": len(slices)}
            )
            return True, "切片处理完成", slices
        except Exception as e:
            LoggingStandards.log_operation_error(
                system_logger, "信号切片处理", str(e), signal.id
            )
            return False, str(e), None
```

### 6.3 直接的用户友好错误提示

#### 在业务逻辑中直接返回用户友好消息
```python
class SignalService:
    def load_signal_file(self, file_path: str) -> Tuple[bool, str, Optional[SignalData]]:
        """直接返回用户友好的错误消息，避免复杂的错误码映射"""
        try:
            if not Path(file_path).exists():
                # 直接返回用户友好的错误消息
                return False, "找不到指定的文件，请检查文件路径是否正确", None

            signal_data = self.excel_reader.read_file(file_path)
            return True, "文件导入成功", signal_data

        except PermissionError:
            return False, "没有权限访问该文件，请检查文件权限", None
        except Exception as e:
            # 记录技术错误信息用于调试
            system_logger.error(f"文件导入技术错误: {str(e)}")
            # 返回用户友好的通用错误消息
            return False, "文件导入失败，请检查文件格式是否正确", None

# Handler层显示错误消息
class SignalImportHandler:
    def _handle_import_result(self, future, window):
        """处理导入结果并显示用户友好的错误信息"""
        try:
            success, message, signal = future.result()

            if success:
                self.safe_emit_signal(self.import_completed, True)
                # 显示成功消息（可选）
                QMessageBox.information(window, "导入成功", message)
            else:
                self.safe_emit_signal(self.import_failed, message)
                # 直接显示业务层返回的用户友好错误消息
                QMessageBox.critical(window, "导入失败", message)

        except Exception as e:
            error_msg = "处理导入结果时出现错误，请重试"
            self.safe_emit_signal(self.import_failed, error_msg)
            QMessageBox.critical(window, "系统错误", error_msg)
```

## 7. 任务和异步处理规范

### 7.1 异步任务标准实现模式

#### 任务基类定义
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional, Any

@dataclass
class BaseTask(ABC):
    """异步任务基类"""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @abstractmethod
    def execute(self) -> Tuple[bool, str, Optional[Any]]:
        """执行任务

        Returns:
            Tuple[bool, str, Optional[Any]]: (成功标志, 消息, 结果数据)
        """
        pass

    def validate_input(self) -> bool:
        """验证输入参数"""
        return True

    def get_task_name(self) -> str:
        """获取任务名称"""
        return self.__class__.__name__
```

#### 具体任务实现模板
```python
@dataclass
class SignalProcessingTask(BaseTask):
    """信号处理任务模板"""

    signal_data: SignalData
    service: SignalService
    operation_type: str

    def validate_input(self) -> bool:
        """验证输入参数"""
        if not self.signal_data:
            return False
        if not self.service:
            return False
        return True

    def execute(self) -> Tuple[bool, str, Optional[Any]]:
        """执行任务"""
        try:
            # 验证输入
            if not self.validate_input():
                return False, "任务参数验证失败", None

            # 执行具体操作
            if self.operation_type == "slice":
                return self.service.start_slice_processing(self.signal_data)
            elif self.operation_type == "import":
                return self.service.load_signal_file(self.signal_data.file_path)
            else:
                return False, f"不支持的操作类型: {self.operation_type}", None

        except Exception as e:
            error_msg = f"{self.get_task_name()}执行失败: {str(e)}"
            system_logger.error(error_msg)
            return False, error_msg, None
```

### 7.2 线程池使用和资源管理

#### 线程池管理器
```python
class ThreadPoolManager:
    """线程池管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.thread_pool = ThreadPoolExecutor(
                max_workers=4,
                thread_name_prefix="RadarSystem"
            )
            self._active_futures = set()
            self._initialized = True

    def submit_task(self, task: BaseTask) -> Future:
        """提交任务到线程池"""
        future = self.thread_pool.submit(task.execute)
        self._active_futures.add(future)

        # 添加完成回调来清理Future引用
        future.add_done_callback(self._cleanup_future)
        return future

    def _cleanup_future(self, future: Future):
        """清理完成的Future"""
        self._active_futures.discard(future)

    def shutdown(self, wait: bool = True):
        """关闭线程池"""
        self.thread_pool.shutdown(wait=wait)
        self._active_futures.clear()
```

### 7.3 统一任务结果处理机制

#### 任务结果处理器
```python
class TaskResultHandler:
    """任务结果处理器"""

    def __init__(self, handler_instance):
        self.handler = handler_instance

    def handle_task_result(self, future: Future, window, success_signal, error_signal):
        """统一的任务结果处理"""
        try:
            success, message, result = future.result()

            if success:
                # 成功处理
                self.handler.safe_emit_signal(success_signal, True, result)
                ui_logger.info(f"任务完成: {message}")
            else:
                # 失败处理
                self.handler.safe_emit_signal(error_signal, message)
                self.handler.safe_emit_signal(success_signal, False, None)
                ui_logger.error(f"任务失败: {message}")

        except Exception as e:
            error_msg = f"处理任务结果时出错: {str(e)}"
            ui_logger.error(error_msg)
            self.handler.safe_emit_signal(error_signal, error_msg)
            self.handler.safe_emit_signal(success_signal, False, None)

# 使用示例
class SignalSliceHandler(ThreadSafeSignalEmitter):
    def __init__(self):
        super().__init__()
        self.result_handler = TaskResultHandler(self)

    def start_slice(self, window, signal: SignalData):
        slice_task = SignalSliceTask(signal=signal, service=window.signal_service)
        future = window.thread_pool.submit(slice_task.execute)

        # 使用统一的结果处理器
        future.add_done_callback(
            lambda f: self.result_handler.handle_task_result(
                f, window, self.slice_completed, self.slice_failed
            )
        )
```

## 8. 实施指导和代码示例

### 8.1 重构现有代码的步骤

#### 第一步：统一信号命名
```python
# 重构前 - 不一致的命名
class SignalImportHandler:
    import_finished = pyqtSignal(bool)  # ❌ 不一致
    import_error = pyqtSignal(str)      # ❌ 不一致

class SignalSliceHandler:
    slice_completed = pyqtSignal(bool, int)  # ❌ 不一致
    slice_failed = pyqtSignal(str)           # ❌ 不一致

# 重构后 - 统一命名
class SignalImportHandler:
    import_started = pyqtSignal()           # ✅ 统一格式
    import_completed = pyqtSignal(bool)     # ✅ 统一格式
    import_failed = pyqtSignal(str)         # ✅ 统一格式

class SignalSliceHandler:
    slice_started = pyqtSignal()            # ✅ 统一格式
    slice_completed = pyqtSignal(bool, int) # ✅ 统一格式
    slice_failed = pyqtSignal(str)          # ✅ 统一格式
```

#### 第二步：移除Handler层数据存储
```python
# 重构前 - Handler层存储业务数据
class SignalSliceHandler:
    def __init__(self):
        super().__init__()
        self.current_slices = None      # ❌ 违反层级职责
        self.current_slice_index = -1   # ❌ 违反层级职责

# 重构后 - 只在Service层存储
class SignalSliceHandler:
    def __init__(self):
        super().__init__()
        # 只存储UI相关状态，业务数据由Service层管理

    def get_current_slice(self, service):
        # 通过Service层获取数据
        return service.get_current_slice()

class SignalService:
    def __init__(self, processor, excel_reader):
        self.processor = processor
        self.excel_reader = excel_reader
        self.current_slices = None      # ✅ 正确的存储位置
        self.current_slice_index = -1   # ✅ 正确的存储位置
```

#### 第三步：错误处理
```python
# 直接的错误处理
def load_signal_file(self, file_path: str) -> Tuple[bool, str, Optional[SignalData]]:
    try:
        if not Path(file_path).exists():
            return False, "找不到指定的文件，请检查文件路径是否正确", None

        signal_data = self.excel_reader.read_file(file_path)
        return True, "文件导入成功", signal_data
    except Exception as e:
        system_logger.error(f"文件导入错误: {str(e)}")
        return False, "文件导入失败，请检查文件格式是否正确", None
```

### 8.2 简化的新功能开发模板

#### 功能开发检查清单
```python
class SimplifiedFeatureDevelopmentTemplate:
    """简化的新功能开发模板"""

    # 1. 定义实体类（如果需要）
    @dataclass
    class NewFeatureEntity:
        id: str
        data: Any

    # 2. 创建应用服务（核心业务逻辑）
    class NewFeatureService:
        def __init__(self, processor):
            self.processor = processor
            self.current_entity = None

        def start_processing(self, data) -> Tuple[bool, str, Optional[Any]]:
            """直接的业务处理，避免过度抽象"""
            try:
                # 输入验证
                if not data:
                    return False, "数据不能为空", None

                # 执行处理
                result = self.processor.process(data)
                self.current_entity = result
                return True, "处理完成", result

            except Exception as e:
                system_logger.error(f"新功能处理错误: {str(e)}")
                return False, "处理失败，请重试", None

    # 3. 创建Handler（UI交互层）
    class NewFeatureHandler(ThreadSafeSignalEmitter):
        # 统一的信号命名格式
        feature_started = pyqtSignal()
        feature_completed = pyqtSignal(bool)
        feature_failed = pyqtSignal(str)

        def start_feature(self, window, data):
            """启动功能处理"""
            self.safe_emit_signal(self.feature_started)

            # 创建任务并提交到线程池
            task = NewFeatureTask(data=data, service=window.new_feature_service)
            future = window.thread_pool.submit(task.execute)
            future.add_done_callback(lambda f: self._handle_result(f, window))

        def _handle_result(self, future, window):
            """处理任务结果"""
            try:
                success, message, result = future.result()
                if success:
                    self.safe_emit_signal(self.feature_completed, True)
                else:
                    self.safe_emit_signal(self.feature_failed, message)
            except Exception as e:
                self.safe_emit_signal(self.feature_failed, "处理结果时出错")

    # 4. 集成到主窗口（简单的依赖创建）
    class MainWindow:
        def __init__(self):
            super().__init__()
            # 直接创建依赖，避免复杂的注册机制
            self.new_feature_service = NewFeatureService(processor=NewFeatureProcessor())
            self.new_feature_handler = NewFeatureHandler()
            self._connect_new_feature_signals()

        def _connect_new_feature_signals(self):
            """连接信号槽"""
            self.new_feature_handler.feature_completed.connect(self._on_feature_completed)
            self.new_feature_handler.feature_failed.connect(self._on_feature_failed)
```

### 8.3 代码质量检查工具

#### 自动化检查脚本
```python
class CodeQualityChecker:
    """代码质量检查器"""

    def check_naming_conventions(self, file_path: str) -> List[str]:
        """检查命名约定"""
        issues = []

        # 检查类名
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name):
            issues.append(f"类名 {class_name} 不符合命名规范")

        # 检查方法名
        if not re.match(r'^[a-z_][a-z0-9_]*$', method_name):
            issues.append(f"方法名 {method_name} 不符合命名规范")

        return issues

    def check_layer_violations(self, file_path: str) -> List[str]:
        """检查层级调用违规"""
        issues = []

        # 检查是否有跨层调用
        if self._is_ui_layer(file_path) and self._calls_domain_layer(file_path):
            issues.append("UI层不应直接调用Domain层")

        return issues

    def check_signal_naming(self, file_path: str) -> List[str]:
        """检查信号命名规范"""
        issues = []

        # 检查信号命名格式
        signal_pattern = r'^[a-z_]+_(started|completed|failed)$'
        if not re.match(signal_pattern, signal_name):
            issues.append(f"信号名 {signal_name} 不符合命名规范")

        return issues
```

## 9. 总结和实施建议

### 9.1 简化架构的核心原则

#### YAGNI原则的体现
本规范基于YAGNI（You Aren't Gonna Need It）原则，移除了以下过度设计：

1. **移除的复杂抽象**：
   - 复杂的数据传输接口 → 直接参数传递
   - 服务注册器机制 → 简单构造函数注入
   - 信号连接管理器 → Qt自带管理
   - 装饰器错误处理 → 直接try-catch
   - 错误码映射系统 → 直接用户友好消息

2. **保留的核心功能**：
   - 层级职责划分（解决数据存储重复）
   - 统一命名规范（解决命名不一致）
   - 集中式信号发射（解决信号发射不规范）
   - ThreadSafeSignalEmitter基类
   - 统一返回格式

### 9.2 规范实施优先级

#### 高优先级（立即实施）
1. **统一信号命名** - 修复API不一致问题
2. **移除Handler层数据存储** - 修复架构违规
3. **简化错误处理** - 提升代码可读性

#### 中优先级（逐步实施）
1. **统一任务结果处理** - 减少重复代码
2. **标准化日志记录** - 提升可维护性
3. **简化依赖管理** - 提升代码清晰度

#### 低优先级（按需实施）
1. **代码质量检查** - 自动化质量保证
2. **文档完善** - 团队协作支持

### 9.3 简化后的实施策略

#### 直接重构方法
```python
# 简化的重构策略：直接修改，避免复杂的迁移机制

class SimpleRefactoringApproach:
    """简化的重构方法"""

    def step_1_fix_signal_naming(self):
        """第一步：统一信号命名"""
        # 直接修改信号定义，保持一致性
        # import_finished → import_completed
        # import_error → import_failed
        pass

    def step_2_move_data_storage(self):
        """第二步：移动数据存储位置"""
        # 从Handler层移除业务数据存储
        # 确保只在Service层管理业务状态
        pass

    def step_3_simplify_error_handling(self):
        """第三步：简化错误处理"""
        # 移除复杂的装饰器和异常层次
        # 使用直接的try-catch和用户友好消息
        pass
```

### 9.4 简化架构的优势

#### 实际效益
通过简化架构，项目获得：

1. **降低复杂性**：
   - 减少约60%的抽象层
   - 提高代码可读性
   - 降低学习成本

2. **保持功能性**：
   - 仍然解决原始架构问题
   - 保持代码质量
   - 支持未来扩展

3. **提升效率**：
   - 更快的开发速度
   - 更容易的维护
   - 更简单的测试

#### 长期价值
- **避免过度工程化**：只实现当前需要的功能
- **保持架构灵活性**：在真正需要时再添加复杂性
- **提升团队效率**：专注于业务价值而非技术复杂性

### 9.5 持续改进原则

#### 规范演进策略
- **基于实际需求调整**：只在遇到具体问题时增加规范
- **定期简化审查**：移除不再需要的规范和抽象
- **保持实用性**：确保规范服务于实际开发需求
- **避免规范膨胀**：抵制为了完整性而添加不必要的规范

通过遵循这套简化的开发规范，RadarIdentifySystem项目将具备：
- **简洁清晰的架构设计**
- **易于理解和维护的代码结构**
- **实用高效的开发流程**
- **符合YAGNI原则的实现方式**

这种简化的方法既解决了原始的架构问题，又避免了过度工程化，为项目的健康发展提供了坚实的基础。
```
