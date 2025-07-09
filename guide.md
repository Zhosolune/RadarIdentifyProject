# 雷达信号多维参数联合智能分类系统
# 优化架构开发手册

## 目录

1. [简介](#1-简介)
2. [优化架构概述](#2-优化架构概述)
3. [优化后的项目结构](#3-优化后的项目结构)
4. [组件详解](#4-组件详解)
   1. [事件总线](#41-事件总线)
   2. [Qt信号槽集成](#42-qt信号槽集成)
   3. [UI处理器](#43-ui处理器)
   4. [线程池](#44-线程池)
   5. [应用服务](#45-应用服务)
   6. [领域服务](#46-领域服务)
5. [最佳实践](#5-最佳实践)
   1. [事件驱动开发](#51-事件驱动开发)
   2. [异步任务处理](#52-异步任务处理)
   3. [UI与业务逻辑分离](#53-ui与业务逻辑分离)
6. [迁移指南](#6-迁移指南)
7. [附录：原架构参考](#7-附录原架构参考)

## 1. 简介

### 1.1 文档目的

本手册旨在提供雷达信号多维参数联合智能分类系统优化后架构的详细说明，包括简化后的项目结构、组件功能和最佳实践。本文档将指导开发团队理解和应用优化后的架构，同时保持系统的核心功能和扩展性。

### 1.2 适用范围

- 系统开发人员
- 代码维护人员
- 质量测试人员
- AI代码编辑器

### 1.3 优化目标

- 降低架构复杂度，提高代码可读性
- 保持系统的松耦合特性
- 简化组件间通信机制
- 提高开发效率和维护性
- 保留系统的核心功能和扩展性

## 2. 优化架构概述

优化后的架构保留了原有系统的分层设计和领域驱动思想，同时简化了事件总线机制和组件间通信方式。主要优化点包括：

1. **优化事件总线**：将复杂的Event类和EventDispatcher整合，提供更直观的事件发布-订阅机制
2. **集成Qt信号槽**：更好地利用Qt框架的信号槽机制处理UI层通信
3. **UI处理器作为桥梁**：UI处理器同时处理Qt信号槽和事件总线事件，作为两者的桥梁
4. **优化线程池**：保留核心功能，优化接口和实现
5. **保持领域模型**：保持原有领域模型的完整性和职责划分

优化架构的核心理念是"简化不必要的复杂性，保留核心的灵活性"。

## 3. 优化后的项目结构

```
RadarIdentifySystem/
├── config.json                # 主配置文件
├── configs/                   # 配置文件目录
├── radar_system/              # 系统主目录
│   ├── app.py                 # 应用程序入口
│   ├── application/           # 应用服务层
│   │   ├── services/          # 应用服务
│   │   └── tasks/             # 任务定义
│   ├── domain/                # 领域层（保持不变）
│   │   ├── signal/            # 信号处理领域
│   │   └── recognition/       # 识别处理领域
│   ├── infrastructure/        # 基础设施层
│   │   ├── async_core/        # 异步核心
│   │   │   ├── event_bus/     # 事件总线
│   │   │   └── thread_pool/   # 线程池
│   │   ├── common/            # 通用组件
│   │   ├── ml/                # 机器学习组件
│   │   └── persistence/       # 持久化组件
│   └── interface/             # 界面层
│       ├── handlers/          # UI处理器（桥接Qt和事件总线）
│       ├── layouts/           # 布局定义
│       ├── styles/            # 样式定义
│       └── views/             # 视图组件
└── run.py                     # 启动脚本
```

### 3.1 主要组件说明

| 组件 | 职责 | 优化点 |
|------|------|--------|
| EventBus | 提供事件发布-订阅机制 | 替代原复杂的Event+Dispatcher组合 |
| UI处理器 | 处理UI事件，桥接Qt信号槽与事件总线 | 强化桥接器角色，简化事件流转 |
| 线程池 | 管理工作线程，执行异步任务 | 简化接口，保留核心功能 |
| 应用服务 | 协调业务流程，调用领域服务 | 简化事件发布逻辑 |
| 领域服务 | 实现核心业务逻辑 | 保持不变 |
| Qt信号槽 | 处理UI组件间通信 | 与事件总线协同工作 |

## 4. 组件详解

### 4.1 事件总线

#### 4.1.1 核心功能

事件总线提供基本的发布-订阅功能，移除了复杂的事件对象和异步分发器。

```python
class EventBus:
    """事件总线"""
    
    def __init__(self):
        """初始化事件总线"""
        self._handlers = {}  # 事件类型到处理器列表的映射
        self._lock = threading.Lock()  # 线程安全锁
    
    def subscribe(self, event_type, handler):
        """订阅事件
        
        Args:
            event_type: 事件类型字符串
            handler: 处理函数，接收事件数据作为参数
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type, handler):
        """取消订阅事件"""
        with self._lock:
            if event_type in self._handlers and handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
    
    def publish(self, event_type, data=None):
        """发布事件
        
        Args:
            event_type: 事件类型字符串
            data: 事件数据（可选）
        """
        handlers = []
        with self._lock:
            if event_type in self._handlers:
                handlers = self._handlers[event_type].copy()
        
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"事件处理异常: {str(e)}")
    
    def publish_async(self, event_type, data=None):
        """异步发布事件
        
        使用线程来异步处理事件
        
        Args:
            event_type: 事件类型字符串
            data: 事件数据（可选）
        """
        threading.Thread(
            target=self.publish,
            args=(event_type, data),
            daemon=True
        ).start()
```

#### 4.1.2 使用示例

```python
# 创建事件总线
event_bus = EventBus()

# 定义处理器
def on_signal_loaded(data):
    print(f"信号数据已加载: {data.get('file_path')}")

# 订阅事件
event_bus.subscribe("signal_loaded", on_signal_loaded)

# 发布事件
event_bus.publish("signal_loaded", {"file_path": "data.xlsx", "point_count": 1000})

# 异步发布
event_bus.publish_async("signal_processing_started", {"signal_id": "123"})
```

#### 4.1.3 最佳实践

- 使用明确的事件类型命名，如"signal_loaded"、"processing_completed"
- 事件数据使用字典格式，便于扩展
- 处理函数应该简短高效，避免阻塞
- 对于耗时操作，使用publish_async或在处理函数中使用线程池

### 4.2 Qt信号槽集成

#### 4.2.1 核心功能

Qt信号槽机制用于处理UI组件间的通信，与事件总线协同工作。

```python
from PyQt5.QtCore import QObject, pyqtSignal

class SignalHandlers(QObject):
    """信号处理器基类，集成Qt信号槽和事件总线"""
    
    # 定义Qt信号
    operationStarted = pyqtSignal()
    operationFinished = pyqtSignal(bool, object)
    operationError = pyqtSignal(str)
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
```

#### 4.2.2 使用示例

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建事件总线
        self.event_bus = EventBus()
        
        # 创建信号处理器
        self.import_handler = SignalImportHandler(self.event_bus)
        
        # 连接Qt信号到槽函数
        self.importButton.clicked.connect(self.onImportButtonClicked)
        self.import_handler.operationStarted.connect(self.showLoadingSpinner)
        self.import_handler.operationFinished.connect(self.updateUI)
        self.import_handler.operationError.connect(self.showError)
```

#### 4.2.3 最佳实践

- Qt信号槽用于UI内部通信和状态更新
- 使用明确的信号名称和参数类型
- 避免在槽函数中执行耗时操作
- 利用Qt的自动线程安全机制处理跨线程信号

### 4.3 UI处理器

#### 4.3.1 核心功能

UI处理器作为Qt信号槽和事件总线的桥梁，处理UI事件并协调业务流程。

```python
class SignalImportHandler(QObject):
    """信号导入处理器"""
    
    # 定义Qt信号
    importStarted = pyqtSignal()
    importFinished = pyqtSignal(bool, object)
    importError = pyqtSignal(str)
    
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        
        # 订阅事件总线事件
        self.event_bus.subscribe("import_completed", self.onImportCompleted)
        self.event_bus.subscribe("import_error", self.onImportError)
    
    def importData(self, file_path):
        """处理导入数据请求"""
        # 发布事件到事件总线
        self.event_bus.publish("import_started", {"file_path": file_path})
        # 发出Qt信号
        self.importStarted.emit()
    
    def onImportCompleted(self, data):
        """处理导入完成事件"""
        success = data.get("success", False)
        result = data.get("result")
        # 发出Qt信号，通知UI更新
        self.importFinished.emit(success, result)
    
    def onImportError(self, data):
        """处理导入错误事件"""
        error_msg = data.get("error", "未知错误")
        # 发出Qt信号，通知UI显示错误
        self.importError.emit(error_msg)
```

#### 4.3.2 最佳实践

- UI处理器应专注于处理UI事件和状态更新
- 使用事件总线与业务逻辑通信
- 使用Qt信号与UI组件通信
- 避免在UI处理器中实现业务逻辑

### 4.4 线程池

#### 4.4.1 核心功能

线程池提供异步任务执行功能，避免阻塞UI线程。

```python
class ThreadPool:
    """线程池"""
    
    def __init__(self, max_workers=4):
        """初始化线程池
        
        Args:
            max_workers: 最大工作线程数
        """
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="radar_worker"
        )
        self._shutdown = False
    
    def submit(self, func, *args, **kwargs):
        """提交任务到线程池
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Future: 任务执行的Future对象
        """
        if self._shutdown:
            raise RuntimeError("线程池已关闭")
        return self._executor.submit(func, *args, **kwargs)
    
    def shutdown(self, wait=True):
        """关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        if not self._shutdown:
            self._shutdown = True
            self._executor.shutdown(wait=wait)
```

#### 4.4.2 使用示例

```python
# 创建线程池
thread_pool = ThreadPool(max_workers=4)

# 提交任务
future = thread_pool.submit(process_data, data)

# 添加回调
future.add_done_callback(lambda f: handle_result(f.result()))
```

#### 4.4.3 最佳实践

- 使用线程池执行所有耗时操作
- 避免在UI线程中执行IO或计算密集型任务
- 使用回调处理任务结果，避免阻塞等待
- 适当设置最大工作线程数，避免资源过度占用

### 4.5 应用服务

#### 4.5.1 核心功能

应用服务协调业务流程，调用领域服务并发布事件。

```python
class SignalService:
    """信号服务"""
    
    def __init__(self, processor, repository, event_bus):
        self.processor = processor
        self.repository = repository
        self.event_bus = event_bus
    
    def load_signal_file(self, file_path):
        """加载信号文件"""
        try:
            # 发布开始事件
            self.event_bus.publish("import_started", {"file_path": file_path})
            
            # 读取和处理数据
            raw_data = self._read_file(file_path)
            signal = self._process_data(raw_data)
            
            # 保存数据
            self.repository.save(signal)
            
            # 发布完成事件
            self.event_bus.publish("import_completed", {
                "success": True,
                "signal_id": signal.id,
                "data_count": len(signal.data)
            })
            
            return True, signal
            
        except Exception as e:
            # 发布错误事件
            self.event_bus.publish("import_error", {"error": str(e)})
            return False, None
```

#### 4.5.2 最佳实践

- 应用服务应专注于协调业务流程
- 使用事件总线发布状态变化
- 委托领域服务执行具体业务逻辑
- 处理异常并发布相应事件

### 4.6 领域服务

领域服务实现核心业务逻辑，保持原有功能不变。

```python
class SignalProcessor:
    """信号处理服务"""
    
    def __init__(self, slice_length=250):
        self.slice_length = slice_length
    
    def slice_signal(self, signal):
        """对信号数据进行切片"""
        # 实现切片逻辑
        pass
    
    def validate_signal(self, signal):
        """验证信号数据有效性"""
        # 实现验证逻辑
        pass
```

## 5. 最佳实践

### 5.1 事件驱动开发

#### 5.1.1 事件类型定义

使用明确的事件类型命名，遵循以下规范：

- 使用动词_名词格式，如"import_started"、"processing_completed"
- 使用过去时表示已完成的事件，如"data_loaded"
- 使用现在时表示正在进行的事件，如"processing_starting"
- 使用特定前缀区分领域，如"signal_"、"recognition_"

#### 5.1.2 事件数据结构

事件数据使用字典格式，包含以下信息：

- 必要的标识信息，如ID、类型等
- 操作结果，如成功/失败标志
- 相关数据或引用
- 错误信息（如果有）

#### 5.1.3 事件处理

事件处理函数应遵循以下原则：

- 保持简短高效
- 避免阻塞操作
- 适当处理异常
- 避免循环依赖

### 5.2 异步任务处理

#### 5.2.1 任务定义

```python
class ImportTask:
    """导入任务"""
    
    def __init__(self, file_path, service, event_bus):
        self.file_path = file_path
        self.service = service
        self.event_bus = event_bus
    
    def execute(self):
        """执行任务"""
        return self.service.load_signal_file(self.file_path)
```

#### 5.2.2 任务提交

```python
# 创建任务
task = ImportTask(file_path, service, event_bus)

# 提交到线程池
future = thread_pool.submit(task.execute)

# 添加回调
future.add_done_callback(lambda f: handle_result(f.result()))
```

#### 5.2.3 结果处理

```python
def handle_result(result):
    """处理任务结果"""
    success, data = result
    if success:
        # 处理成功情况
        pass
    else:
        # 处理失败情况
        pass
```

### 5.3 UI与业务逻辑分离

#### 5.3.1 职责划分

- **UI组件**：负责界面显示和用户交互
- **UI处理器**：处理UI事件并与业务层通信
- **应用服务**：协调业务流程
- **领域服务**：实现核心业务逻辑

#### 5.3.2 通信方式

- **UI组件与UI处理器**：使用Qt信号槽
- **UI处理器与应用服务**：使用事件总线
- **应用服务与领域服务**：直接方法调用

#### 5.3.3 状态更新

- **业务状态变化**：通过事件总线发布
- **UI状态更新**：通过Qt信号槽触发

## 6. 迁移指南

### 6.1 事件总线迁移

从原有Event+EventBus组合迁移到优化后的EventBus：

1. 替换导入语句：
   ```python
   # 原代码
   from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
   from radar_system.infrastructure.async_core.event_bus.event import Event
   
   # 新代码
   from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
   ```

2. 替换事件发布代码：
   ```python
   # 原代码
   self.event_bus.publish(Event(
       type="signal_loading_started",
       data={"file_path": file_path}
   ))
   
   # 新代码
   self.event_bus.publish("signal_loading_started", {"file_path": file_path})
   ```

3. 替换事件订阅代码：
   ```python
   # 原代码
   def on_signal_loaded(self, event):
       data = event.data
       # 处理事件...
   
   self.event_bus.subscribe("signal_loaded", self.on_signal_loaded)
   
   # 新代码
   def on_signal_loaded(self, data):
       # 处理事件...
   
   self.event_bus.subscribe("signal_loaded", self.on_signal_loaded)
   ```

### 6.2 UI处理器迁移

1. 增强Qt信号定义：
   ```python
   # 原代码
   class SignalImportHandler(QObject):
       import_started = pyqtSignal()
       import_finished = pyqtSignal(bool)
   
   # 新代码
   class SignalImportHandler(QObject):
       importStarted = pyqtSignal()
       importFinished = pyqtSignal(bool, object)  # 增加数据参数
   ```

2. 添加事件总线桥接代码：
   ```python
   # 订阅事件总线事件
   self.event_bus.subscribe("import_completed", self.onImportCompleted)
   
   # 处理事件总线事件并发出Qt信号
   def onImportCompleted(self, data):
       success = data.get("success", False)
       result = data.get("result")
       self.importFinished.emit(success, result)
   ```

### 6.3 线程池迁移

1. 替换线程池创建：
   ```python
   # 原代码
   self.thread_pool = ThreadPool(
       max_workers=4,
       min_workers=2,
       idle_timeout=60
   )
   
   # 新代码
   self.thread_pool = ThreadPool(max_workers=4)
   ```

## 7. 附录：原架构参考

原架构的详细说明请参考 `docs/development_guide.md`。本文档中未明确修改的部分应保持与原架构一致。 