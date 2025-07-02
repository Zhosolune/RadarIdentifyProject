# RadarIdentifySystem功能开发最佳实践指南

## 概述

本指南为开发者在RadarIdentifySystem中新增功能提供明确的指导。系统已完全移除事件总线，采用简化的架构设计，遵循YAGNI原则，只实现当前需要的功能，避免过度设计。

## 1. 架构层次流转规范

### 1.1 层次结构

```
┌─────────────────┐
│   UI层 (Interface)   │  ← 用户交互、界面显示、Qt信号槽
├─────────────────┤
│ 应用服务层 (Application) │  ← 业务流程协调、日志记录
├─────────────────┤
│ 领域服务层 (Domain)     │  ← 纯业务逻辑、算法实现
├─────────────────┤
│ 基础设施层 (Infrastructure) │  ← 数据持久化、外部服务
└─────────────────┘
```

### 1.2 调用关系规范

**✅ 允许的调用方向**：

- UI层 → 应用服务层
- 应用服务层 → 领域服务层
- 应用服务层 → 基础设施层
- 领域服务层 → 基础设施层（仅限数据访问）

**❌ 禁止的调用方向**：

- 下层调用上层（如领域层调用应用层）
- 跨层调用（如UI层直接调用领域层）

### 1.3 各层职责边界

#### UI层 (Interface)

**应该做**：

- 处理用户交互
- 显示数据和状态
- 发布UI状态信号（Qt信号槽）
- 直接调用应用服务

**不应该做**：

- 包含业务逻辑
- 直接调用领域服务
- 处理数据持久化

```python
# ✅ 正确示例
class MainWindow(QMainWindow):
    def _on_start_process(self):
        # 获取用户输入
        params = self._get_user_params()
        
        # 调用应用服务
        self.recognition_handler.start_recognition(self, params)
    
    def _on_recognition_completed(self, success, result):
        # 更新UI显示
        if success:
            self.result_label.setText(f"识别完成: {result}")
```

#### 应用服务层 (Application)

**应该做**：

- 协调业务流程
- 调用领域服务
- 记录日志信息
- 处理异常和错误

**不应该做**：

- 实现具体业务算法
- 直接操作UI组件
- 包含领域逻辑

```python
# ✅ 正确示例
class RecognitionService:
    def start_recognition_processing(self, params):
        try:
            # 记录开始日志
            system_logger.info(f"开始识别处理: {params}")

            # 调用领域服务
            result = self.recognizer.recognize(params)

            # 记录完成日志
            system_logger.info(f"识别处理完成: {result}")

            return True, "识别完成", result
        except Exception as e:
            error_msg = f"识别处理出错: {str(e)}"
            system_logger.error(error_msg)
            return False, error_msg, None
```

#### 领域服务层 (Domain)

**应该做**：

- 实现核心业务逻辑
- 包含算法和计算
- 操作领域实体

**不应该做**：

- 依赖UI框架
- 记录业务日志
- 处理持久化细节

```python
# ✅ 正确示例
class SignalRecognizer:
    def recognize(self, signal_data):
        # 纯业务逻辑
        features = self._extract_features(signal_data)
        prediction = self._classify(features)
        return self._create_result(prediction)
```

## 2. 数据流动模式

### 2.1 用户输入流动

```
用户操作 → UI组件 → 事件处理器 → 应用服务 → 领域服务 → 基础设施
```

### 2.2 结果返回流动

```
基础设施 → 领域服务 → 应用服务 → 事件发布 → UI事件监听 → 界面更新
```

### 2.3 数据传递格式

#### 参数传递

```python
# UI层到应用服务层
params = {
    "signal_id": "uuid-string",
    "algorithm_type": "svm",
    "threshold": 0.8
}

# 应用服务层到领域服务层
domain_params = ProcessingParams(
    signal_id=params["signal_id"],
    algorithm=AlgorithmType.SVM,
    threshold=params["threshold"]
)
```

#### 结果返回

```python
# 统一的结果格式
def process_data(self) -> Tuple[bool, str, Any]:
    """
    Returns:
        bool: 是否成功
        str: 消息描述
        Any: 结果数据（成功时）或None（失败时）
    """
    pass
```

## 3. 事件发布时机和规则

### 3.1 事件发布时机

**应该发布事件的情况**：

- 长时间运行的操作开始/完成/失败
- 重要的业务状态变化
- 需要通知多个组件的事件

**不应该发布事件的情况**：

- 简单的数据查询
- 内部计算步骤
- 临时状态变化

### 3.2 事件发布规则

#### 只有应用服务层发布业务事件

```python
# ✅ 在应用服务中发布
class RecognitionService:
    def start_processing(self, data):
        self.event_bus.publish(RecognitionEvents.PROCESSING_STARTED, {"data_id": data.id})
        # 处理逻辑...
        self.event_bus.publish(RecognitionEvents.PROCESSING_COMPLETED, {"result": result})

# ❌ 任务层不发布业务事件
class RecognitionTask:
    def execute(self):
        # 直接调用服务，不发布事件
        return self.service.start_processing(self.data)
```

### 3.3 事件数据规范

```python
# 事件数据应包含的信息
event_data = {
    "entity_id": "uuid-string",      # 相关实体ID
    "timestamp": "2024-01-01T00:00:00Z",  # 时间戳（可选）
    "user_id": "user123",            # 用户ID（如果相关）
    "additional_info": {...}         # 其他相关信息
}

# 错误事件的数据格式
error_data = {
    "entity_id": "uuid-string",
    "error": "具体错误描述",
    "error_code": "ERR_001",         # 错误代码（可选）
    "context": {...}                 # 错误上下文
}
```

### 3.4 事件发布代码模板

```python
# 标准事件发布模板
class MyService:
    def process_something(self, data):
        try:
            # 发布开始事件
            self.event_bus.publish(
                MyEvents.PROCESSING_STARTED,
                {"entity_id": data.id, "type": data.type}
            )
            
            # 执行业务逻辑
            result = self._do_processing(data)
            
            # 发布成功事件
            self.event_bus.publish(
                MyEvents.PROCESSING_COMPLETED,
                {"entity_id": data.id, "result_count": len(result)}
            )
            
            return True, "处理完成", result
            
        except Exception as e:
            # 发布失败事件
            self.event_bus.publish(
                MyEvents.PROCESSING_FAILED,
                {"entity_id": data.id, "error": str(e)}
            )
            return False, str(e), None
```

## 4. Qt信号槽使用场景

### 4.1 使用Qt信号槽的场景

**✅ 适合Qt信号槽**：

- UI组件间的直接通信
- 即时的界面反馈
- 用户交互事件
- 界面状态同步

```python
# UI组件间通信
class MyWidget(QWidget):
    data_changed = pyqtSignal(dict)  # 数据变化信号
    
    def update_data(self, data):
        self.data = data
        self.data_changed.emit(data)  # 通知其他组件

# 连接信号槽
widget.data_changed.connect(other_widget.on_data_changed)
```

### 4.2 使用事件总线的场景

**✅ 适合事件总线**：

- 跨层通信
- 业务状态广播
- 异步处理结果通知
- 解耦组件间通信

```python
# 业务状态广播
class RecognitionHandler(QObject):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        # 监听业务事件
        self.event_bus.subscribe(RecognitionEvents.PROCESSING_COMPLETED, self._on_completed)
    
    def _on_completed(self, data):
        # 更新UI状态
        self.update_ui_with_result(data)
```

### 4.3 线程安全的UI更新

```python
def _safe_update_ui(self, update_func, *args):
    """线程安全的UI更新"""
    if QThread.currentThread() is QApplication.instance().thread():
        # 在主线程中直接更新
        update_func(*args)
    else:
        # 在非主线程中，使用QMetaObject.invokeMethod
        from PyQt5.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(
            self, "_update_ui_in_main_thread",
            Qt.QueuedConnection,
            update_func, *args
        )

def _update_ui_in_main_thread(self, update_func, *args):
    """在主线程中更新UI"""
    update_func(*args)
```

## 5. 任务和实体设计规范

### 5.1 Task类设计规范

```python
# 任务类命名：{Entity}{Action}Task
class SignalRecognitionTask:
    """信号识别任务
    
    职责：执行具体的识别任务，不发布业务事件
    """
    
    def __init__(self, signal_data, service, event_bus):
        self.signal_data = signal_data
        self.service = service
        self.event_bus = event_bus  # 传递给服务使用
    
    def execute(self) -> Tuple[bool, str, Any]:
        """执行任务
        
        Returns:
            Tuple[bool, str, Any]: (成功标志, 消息, 结果数据)
        """
        try:
            # 直接调用应用服务，由服务发布事件
            return self.service.start_recognition_processing(self.signal_data)
        except Exception as e:
            return False, f"任务执行失败: {str(e)}", None
```

### 5.2 实体类设计规范

```python
# 实体类命名：{Domain}{Entity}
@dataclass
class RecognitionResult:
    """识别结果实体"""
    id: str
    signal_id: str
    algorithm_type: str
    confidence: float
    prediction: str
    features: Dict[str, Any]
    created_at: datetime
    
    def is_confident(self, threshold: float = 0.8) -> bool:
        """判断结果是否可信"""
        return self.confidence >= threshold
```

### 5.3 服务类职责划分

```python
# 应用服务：协调和流程控制
class RecognitionService:
    """识别应用服务"""
    
    def __init__(self, recognizer, repository, event_bus):
        self.recognizer = recognizer      # 领域服务
        self.repository = repository      # 基础设施
        self.event_bus = event_bus       # 事件发布

# 领域服务：核心业务逻辑
class SignalRecognizer:
    """信号识别领域服务"""
    
    def recognize(self, signal_data) -> RecognitionResult:
        """执行识别算法"""
        # 纯业务逻辑，不依赖外部服务
        pass
```

## 6. 命名约定

### 6.1 文件命名规范

```
# 服务类文件
{domain}_service.py          # signal_service.py
{domain}_{entity}_service.py # signal_recognition_service.py

# 任务类文件
{domain}_tasks.py           # signal_tasks.py

# 处理器文件
{entity}_handler.py         # signal_slice_handler.py

# 实体文件
{entity}.py                 # signal.py, recognition_result.py
```

### 6.2 类名规范

```python
# 服务类
class {Domain}Service:           # SignalService
class {Domain}{Entity}Service:   # SignalRecognitionService

# 任务类
class {Entity}{Action}Task:      # SignalSliceTask, RecognitionProcessTask

# 处理器类
class {Entity}{Action}Handler:   # SignalSliceHandler

# 实体类
class {Entity}:                  # Signal, RecognitionResult
class {Domain}{Entity}:          # SignalData, RecognitionResult
```

### 6.3 方法名规范

```python
# 公共方法：动词开头
def start_processing()
def get_current_data()
def validate_input()

# 私有方法：下划线开头
def _process_data()
def _validate_params()
def _handle_error()

# 事件处理方法
def _on_{event_name}()          # _on_slice_completed()
```

### 6.4 事件名称规范

基于 `domain.entity.action.status` 格式：

```python
class RecognitionEvents:
    # 识别处理事件
    PROCESSING_STARTED = "recognition.process.analyze.started"
    PROCESSING_COMPLETED = "recognition.process.analyze.completed"
    PROCESSING_FAILED = "recognition.process.analyze.failed"
    
    # 模型加载事件
    MODEL_LOADING_STARTED = "recognition.model.load.started"
    MODEL_LOADING_COMPLETED = "recognition.model.load.completed"
    MODEL_LOADING_FAILED = "recognition.model.load.failed"
```

## 7. 完整的功能实现示例

以"信号识别处理"功能为例，展示完整的实现流程。

### 7.1 第一步：扩展事件常量

```python
# 文件：infrastructure/async_core/event_bus/event_constants.py
class RecognitionEvents:
    """识别处理相关事件常量"""

    # 识别处理事件
    PROCESSING_STARTED = "recognition.process.analyze.started"
    PROCESSING_COMPLETED = "recognition.process.analyze.completed"
    PROCESSING_FAILED = "recognition.process.analyze.failed"

    # 模型加载事件
    MODEL_LOADING_STARTED = "recognition.model.load.started"
    MODEL_LOADING_COMPLETED = "recognition.model.load.completed"
    MODEL_LOADING_FAILED = "recognition.model.load.failed"
```

### 7.2 第二步：创建领域实体

```python
# 文件：domain/recognition/entities/recognition_result.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class RecognitionResult:
    """识别结果实体"""
    id: str
    signal_id: str
    algorithm_type: str
    confidence: float
    prediction: str
    features: Dict[str, Any]
    created_at: datetime

    def is_confident(self, threshold: float = 0.8) -> bool:
        """判断结果是否可信"""
        return self.confidence >= threshold

    def get_summary(self) -> str:
        """获取结果摘要"""
        return f"{self.prediction} (置信度: {self.confidence:.2f})"
```

### 7.3 第三步：创建领域服务

```python
# 文件：domain/recognition/services/recognizer.py
from typing import List, Dict, Any
import numpy as np

from radar_system.domain.signal.entities.signal import SignalData
from radar_system.domain.recognition.entities.recognition_result import RecognitionResult
from radar_system.infrastructure.common.logging import system_logger

class SignalRecognizer:
    """信号识别领域服务"""

    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self):
        """加载识别模型"""
        # 这里实现模型加载逻辑
        system_logger.info(f"加载识别模型: {self.model_path}")
        # self.model = load_model(self.model_path)

    def recognize(self, signal_data: SignalData) -> RecognitionResult:
        """执行信号识别

        Args:
            signal_data: 信号数据

        Returns:
            RecognitionResult: 识别结果
        """
        try:
            # 特征提取
            features = self._extract_features(signal_data)

            # 模型预测
            prediction, confidence = self._predict(features)

            # 创建结果实体
            result = RecognitionResult(
                id=str(uuid.uuid4()),
                signal_id=signal_data.id,
                algorithm_type="svm",  # 或从配置获取
                confidence=confidence,
                prediction=prediction,
                features=features,
                created_at=datetime.now()
            )

            system_logger.info(f"识别完成: {result.get_summary()}")
            return result

        except Exception as e:
            system_logger.error(f"识别失败: {str(e)}")
            raise

    def _extract_features(self, signal_data: SignalData) -> Dict[str, Any]:
        """提取信号特征"""
        # 实现特征提取算法
        return {
            "mean_frequency": np.mean(signal_data.raw_data[:, 0]),
            "max_amplitude": np.max(signal_data.raw_data[:, 3]),
            "duration": signal_data.raw_data[-1, 4] - signal_data.raw_data[0, 4]
        }

    def _predict(self, features: Dict[str, Any]) -> tuple:
        """执行模型预测"""
        # 实现预测逻辑
        # prediction = self.model.predict(features)
        # 临时返回模拟结果
        return "雷达信号", 0.85
```

### 7.4 第四步：创建应用服务

```python
# 文件：application/services/recognition_service.py
from typing import Tuple, Optional
import uuid

from radar_system.domain.signal.entities.signal import SignalData
from radar_system.domain.recognition.entities.recognition_result import RecognitionResult
from radar_system.domain.recognition.services.recognizer import SignalRecognizer
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
from radar_system.infrastructure.async_core.event_bus.event_constants import RecognitionEvents
from radar_system.infrastructure.common.logging import system_logger

class RecognitionService:
    """识别处理应用服务"""

    def __init__(self, recognizer: SignalRecognizer, event_bus: EventBus):
        self.recognizer = recognizer
        self.event_bus = event_bus
        self.current_result = None

    def start_recognition_processing(self, signal_data: SignalData) -> Tuple[bool, str, Optional[RecognitionResult]]:
        """开始识别处理

        Args:
            signal_data: 待识别的信号数据

        Returns:
            tuple: (是否成功, 消息, 识别结果)
        """
        try:
            # 发布开始识别事件
            self.event_bus.publish(
                RecognitionEvents.PROCESSING_STARTED,
                {"signal_id": signal_data.id}
            )

            # 执行识别
            result = self.recognizer.recognize(signal_data)
            if not result:
                return False, "识别处理未生成有效结果", None

            # 保存识别结果
            self.current_result = result

            # 发布识别完成事件
            self.event_bus.publish(
                RecognitionEvents.PROCESSING_COMPLETED,
                {
                    "signal_id": signal_data.id,
                    "result_id": result.id,
                    "prediction": result.prediction,
                    "confidence": result.confidence
                }
            )

            return True, "识别处理完成", result

        except Exception as e:
            error_msg = f"识别处理出错: {str(e)}"
            system_logger.error(error_msg)
            self.event_bus.publish(
                RecognitionEvents.PROCESSING_FAILED,
                {
                    "signal_id": signal_data.id,
                    "error": error_msg
                }
            )
            return False, error_msg, None

    def get_current_result(self) -> Optional[RecognitionResult]:
        """获取当前识别结果"""
        return self.current_result
```

### 7.5 第五步：创建任务类

```python
# 文件：application/tasks/recognition_tasks.py
from dataclasses import dataclass
from typing import Tuple, Optional

from radar_system.domain.signal.entities.signal import SignalData
from radar_system.domain.recognition.entities.recognition_result import RecognitionResult
from radar_system.application.services.recognition_service import RecognitionService
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
from radar_system.infrastructure.common.logging import system_logger

@dataclass
class RecognitionTask:
    """识别处理任务"""
    signal_data: SignalData
    service: RecognitionService
    event_bus: EventBus

    def execute(self) -> Tuple[bool, str, Optional[RecognitionResult]]:
        """执行识别任务

        Returns:
            tuple: (是否成功, 消息, 识别结果)
        """
        try:
            # 直接调用应用服务，由服务层发布事件
            success, message, result = self.service.start_recognition_processing(self.signal_data)
            if not success:
                return False, message, None

            return True, "识别完成", result

        except Exception as e:
            error_msg = f"识别任务执行出错: {str(e)}"
            system_logger.error(error_msg)
            return False, error_msg, None
```

### 7.6 第六步：创建UI处理器

```python
# 文件：interface/handlers/recognition_handler.py
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QApplication
from PyQt5.QtWidgets import QMessageBox

from radar_system.infrastructure.common.logging import ui_logger
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
from radar_system.infrastructure.async_core.event_bus.event_constants import RecognitionEvents
from radar_system.application.services.recognition_service import RecognitionService
from radar_system.application.tasks.recognition_tasks import RecognitionTask
from radar_system.domain.signal.entities.signal import SignalData
from radar_system.domain.recognition.entities.recognition_result import RecognitionResult

class RecognitionHandler(QObject):
    """识别处理事件处理器"""

    # Qt信号定义
    recognition_started = pyqtSignal()
    recognition_completed = pyqtSignal(bool, str, float)  # 成功标志, 预测结果, 置信度
    recognition_failed = pyqtSignal(str)  # 错误信息

    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus

        # 识别状态管理
        self.current_result: Optional[RecognitionResult] = None

        # 订阅事件
        self._subscribe_events()

        ui_logger.info("RecognitionHandler 初始化完成")

    def _subscribe_events(self) -> None:
        """订阅事件"""
        self.event_bus.subscribe(RecognitionEvents.PROCESSING_STARTED, self._on_recognition_started)
        self.event_bus.subscribe(RecognitionEvents.PROCESSING_COMPLETED, self._on_recognition_completed)
        self.event_bus.subscribe(RecognitionEvents.PROCESSING_FAILED, self._on_recognition_failed)

    def _on_recognition_started(self, data: Dict[str, Any]) -> None:
        """处理识别开始事件"""
        signal_id = data.get('signal_id', 'unknown')
        ui_logger.info(f"信号识别开始: {signal_id}")

        # 线程安全的UI更新
        self._safe_emit_signal(self.recognition_started)

    def _on_recognition_completed(self, data: Dict[str, Any]) -> None:
        """处理识别完成事件"""
        signal_id = data.get('signal_id', 'unknown')
        prediction = data.get('prediction', 'unknown')
        confidence = data.get('confidence', 0.0)

        ui_logger.info(f"信号识别完成: {signal_id}, 结果: {prediction}, 置信度: {confidence}")

        # 线程安全的UI更新
        self._safe_emit_signal(self.recognition_completed, True, prediction, confidence)

    def _on_recognition_failed(self, data: Dict[str, Any]) -> None:
        """处理识别失败事件"""
        signal_id = data.get('signal_id', 'unknown')
        error = data.get('error', '未知错误')

        ui_logger.error(f"信号识别失败: {signal_id}, 错误: {error}")

        # 线程安全的UI更新
        self._safe_emit_signal(self.recognition_failed, error)

    def _safe_emit_signal(self, signal, *args) -> None:
        """线程安全的信号发射"""
        if QThread.currentThread() is QApplication.instance().thread():
            signal.emit(*args)
        else:
            from PyQt5.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                self, "_emit_signal_in_main_thread",
                Qt.QueuedConnection,
                signal, *args
            )

    def _emit_signal_in_main_thread(self, signal, *args) -> None:
        """在主线程中发射信号"""
        signal.emit(*args)

    def start_recognition(self, window, signal_data: SignalData) -> None:
        """启动信号识别处理"""
        if not signal_data:
            self._show_message_box(window, "警告", "没有可用的信号数据", QMessageBox.Warning)
            return

        try:
            # 创建识别任务
            recognition_task = RecognitionTask(
                signal_data=signal_data,
                service=window.recognition_service,
                event_bus=self.event_bus
            )

            # 提交任务到线程池
            future = window.thread_pool.submit(recognition_task.execute)
            future.add_done_callback(
                lambda f: self._handle_recognition_result(f, window)
            )

            ui_logger.info(f"信号识别任务已启动: {signal_data.id}")

        except Exception as e:
            error_msg = f"启动识别任务失败: {str(e)}"
            ui_logger.error(error_msg)
            self._show_message_box(window, "错误", error_msg, QMessageBox.Critical)

    def _handle_recognition_result(self, future, window) -> None:
        """处理识别任务结果"""
        try:
            success, message, result = future.result()

            if success and result:
                self.current_result = result
                ui_logger.info(f"识别任务完成: {result.get_summary()}")
            else:
                ui_logger.error(f"识别任务失败: {message}")

        except Exception as e:
            error_msg = f"处理识别结果时出错: {str(e)}"
            ui_logger.error(error_msg)
            self._show_message_box(window, "错误", error_msg, QMessageBox.Critical)

    def _show_message_box(self, parent, title: str, message: str, icon) -> None:
        """线程安全的消息框显示"""
        if QThread.currentThread() is QApplication.instance().thread():
            msg_box = QMessageBox(icon, title, message, QMessageBox.Ok, parent)
            msg_box.exec_()
        else:
            from PyQt5.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                self, "_show_message_box_in_main_thread",
                Qt.QueuedConnection,
                parent, title, message, icon
            )

    def _show_message_box_in_main_thread(self, parent, title: str, message: str, icon) -> None:
        """在主线程中显示消息框"""
        msg_box = QMessageBox(icon, title, message, QMessageBox.Ok, parent)
        msg_box.exec_()

    def get_current_result(self) -> Optional[RecognitionResult]:
        """获取当前识别结果"""
        return self.current_result

    def cleanup(self) -> None:
        """清理资源"""
        self.event_bus.unsubscribe(RecognitionEvents.PROCESSING_STARTED, self._on_recognition_started)
        self.event_bus.unsubscribe(RecognitionEvents.PROCESSING_COMPLETED, self._on_recognition_completed)
        self.event_bus.unsubscribe(RecognitionEvents.PROCESSING_FAILED, self._on_recognition_failed)

        ui_logger.info("RecognitionHandler 资源已清理")
```

### 7.7 第七步：集成到主窗口

```python
# 文件：interface/views/main_window.py (修改部分)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有初始化代码 ...

        # 初始化识别服务和处理器
        self._init_recognition_components()

        # 连接信号槽
        self._connect_recognition_signals()

    def _init_recognition_components(self):
        """初始化识别相关组件"""
        # 创建识别器
        recognizer = SignalRecognizer()

        # 创建识别服务
        self.recognition_service = RecognitionService(recognizer, self.event_bus)

        # 创建识别处理器
        self.recognition_handler = RecognitionHandler(self.event_bus)

    def _connect_recognition_signals(self):
        """连接识别相关信号"""
        # 连接识别按钮
        self.recognize_btn.clicked.connect(self._on_start_recognition)

        # 连接识别处理器信号
        self.recognition_handler.recognition_started.connect(self._on_recognition_started)
        self.recognition_handler.recognition_completed.connect(self._on_recognition_completed)
        self.recognition_handler.recognition_failed.connect(self._on_recognition_failed)

    def _on_start_recognition(self):
        """处理开始识别按钮点击"""
        # 获取当前信号数据
        signal = self.signal_service.get_current_signal()
        if signal is None:
            QMessageBox.warning(self, "警告", "请先加载信号数据")
            return

        # 启动识别处理
        self.recognition_handler.start_recognition(self, signal)

    def _on_recognition_started(self):
        """识别开始时的UI更新"""
        self.recognize_btn.setEnabled(False)
        self.status_label.setText("正在进行信号识别...")
        self.progress_bar.setVisible(True)

    def _on_recognition_completed(self, success: bool, prediction: str, confidence: float):
        """识别完成时的UI更新"""
        self.recognize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_label.setText(f"识别完成: {prediction} (置信度: {confidence:.2f})")
            self.result_label.setText(f"识别结果: {prediction}")
            self.confidence_label.setText(f"置信度: {confidence:.2f}")
        else:
            self.status_label.setText("识别失败")

    def _on_recognition_failed(self, error: str):
        """识别失败时的UI更新"""
        self.recognize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"识别失败: {error}")
        QMessageBox.critical(self, "识别失败", error)
```

## 8. 开发检查清单

在实现新功能时，请按照以下检查清单确保符合最佳实践：

### ✅ 架构检查

- [ ] 是否遵循了正确的层次调用关系？
- [ ] 每一层是否只做自己该做的事情？
- [ ] 是否避免了跨层调用？

### ✅ 事件检查

- [ ] 是否只在应用服务层发布业务事件？
- [ ] 任务层是否避免了重复的事件发布？
- [ ] 事件命名是否符合规范？
- [ ] 事件数据是否包含足够的上下文信息？

### ✅ 代码质量检查

- [ ] 文件和类命名是否符合规范？
- [ ] 是否提供了适当的错误处理？
- [ ] 是否添加了必要的日志记录？
- [ ] UI更新是否线程安全？

### ✅ 功能检查

- [ ] 是否实现了完整的用户交互流程？
- [ ] 是否提供了适当的用户反馈？
- [ ] 是否处理了异常情况？

## 9. 常见问题和解决方案

### Q1: 什么时候使用事件总线，什么时候使用Qt信号槽？

**A**:

- **事件总线**：跨层通信、业务状态广播、异步处理结果通知
- **Qt信号槽**：UI组件间直接通信、即时界面反馈、用户交互事件

### Q2: 如何确保UI更新的线程安全？

**A**: 使用提供的`_safe_emit_signal`模板方法，或者使用`QMetaObject.invokeMethod`。

### Q3: 任务层应该发布事件吗？

**A**: 不应该。任务层专注于执行，由应用服务层发布业务事件，避免重复。

### Q4: 如何处理复杂的业务流程？

**A**: 在应用服务层协调多个领域服务，使用事务边界管理一致性。

### Q5: 领域服务可以调用基础设施层吗？

**A**: 可以，但仅限于数据访问。不应该调用外部服务或发布事件。

## 10. 总结

本指南基于简化后的事件总线系统，提供了在RadarIdentifySystem中开发新功能的完整指导。核心原则是：

1. **遵循YAGNI原则** - 只实现当前需要的功能
2. **保持简单性** - 避免过度设计和不必要的抽象
3. **明确职责边界** - 每层只做自己该做的事情
4. **统一规范** - 遵循命名约定和代码规范

通过遵循这些最佳实践，可以确保代码的可维护性、可扩展性和一致性。
