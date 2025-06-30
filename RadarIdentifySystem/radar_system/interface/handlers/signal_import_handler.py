"""信号导入事件处理器

处理与信号数据导入相关的所有UI事件。
"""

from typing import Optional, Dict, Any
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication

from radar_system.application.tasks.signal_tasks import SignalImportTask
from radar_system.infrastructure.common.logging import ui_logger
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
from radar_system.infrastructure.async_core.event_bus.event_constants import SignalEvents


class SignalImportHandler(QObject):
    """信号导入事件处理器
    
    处理与信号数据导入相关的所有UI事件。
    
    Signals:
        import_started: 导入开始信号
        import_finished: 导入完成信号，携带成功标志
        import_error: 导入错误信号，携带错误信息
        file_selected: 文件选择完成信号，携带文件路径
        
    Attributes:
        event_bus (EventBus): 事件总线实例
    """
    
    # 定义Qt信号
    import_started = pyqtSignal()
    import_finished = pyqtSignal(bool)  # 参数为是否成功
    import_error = pyqtSignal(str)  # 参数为错误信息
    file_selected = pyqtSignal(str)  # 参数为文件路径
    
    def __init__(self, event_bus: EventBus):
        """初始化处理器
        
        Args:
            event_bus: 事件总线实例
        """
        super().__init__()
        self.event_bus = event_bus
        self._last_directory = None  # 会话级路径记忆
        
        # 订阅事件总线事件（使用新的事件常量）
        self._subscribe_events()
        
        ui_logger.info("SignalImportHandler 初始化完成")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        self.event_bus.subscribe(SignalEvents.DATA_IMPORT_STARTED, self._on_import_started)
        self.event_bus.subscribe(SignalEvents.DATA_IMPORT_COMPLETED, self._on_import_completed)
        self.event_bus.subscribe(SignalEvents.DATA_IMPORT_FAILED, self._on_import_failed)
        self.event_bus.subscribe(SignalEvents.DATA_LOADING_STARTED, self._on_loading_started)
        self.event_bus.subscribe(SignalEvents.DATA_LOADING_COMPLETED, self._on_loading_completed)
        self.event_bus.subscribe(SignalEvents.DATA_LOADING_FAILED, self._on_loading_failed)
    
    def _on_import_started(self, data: Dict[str, Any]) -> None:
        """处理导入开始事件"""
        file_path = data.get("file_path", "unknown")
        ui_logger.info(f"信号导入开始: {file_path}")
        self._safe_emit_signal(self.import_started)
    
    def _on_import_completed(self, data: Dict[str, Any]) -> None:
        """处理导入完成事件"""
        signal_id = data.get("signal_id", "unknown")
        ui_logger.info(f"信号导入完成: {signal_id}")
        self._safe_emit_signal(self.import_finished, True)
    
    def _on_import_failed(self, data: Dict[str, Any]) -> None:
        """处理导入失败事件"""
        error = data.get("error", "未知错误")
        ui_logger.error(f"信号导入失败: {error}")
        self._safe_emit_signal(self.import_error, error)
        self._safe_emit_signal(self.import_finished, False)
    
    def _on_loading_started(self, data: Dict[str, Any]) -> None:
        """处理加载开始事件"""
        file_path = data.get("file_path", "unknown")
        ui_logger.debug(f"信号加载开始: {file_path}")
    
    def _on_loading_completed(self, data: Dict[str, Any]) -> None:
        """处理加载完成事件"""
        signal_id = data.get("signal_id", "unknown")
        ui_logger.debug(f"信号加载完成: {signal_id}")
    
    def _on_loading_failed(self, data: Dict[str, Any]) -> None:
        """处理加载失败事件"""
        error = data.get("error", "未知错误")
        ui_logger.error(f"信号加载失败: {error}")
        self._safe_emit_signal(self.import_error, error)
        self._safe_emit_signal(self.import_finished, False)
    
    def _safe_emit_signal(self, signal, *args) -> None:
        """线程安全的信号发射"""
        if QThread.currentThread() is QApplication.instance().thread():
            # 在主线程中直接发射
            signal.emit(*args)
        else:
            # 在非主线程中，使用QMetaObject.invokeMethod
            from PyQt5.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                self, "_emit_signal_in_main_thread",
                Qt.QueuedConnection,
                signal, *args
            )
    
    def _emit_signal_in_main_thread(self, signal, *args) -> None:
        """在主线程中发射信号"""
        signal.emit(*args)
    
    def browse_file(self, window) -> Optional[str]:
        """浏览文件方法
        
        Args:
            window: 主窗口实例
            
        Returns:
            Optional[str]: 选择的文件路径，如果取消则返回None
        """
        try:
            # 确定起始目录
            start_dir = self._last_directory or str(Path.home())
            
            # 打开文件选择对话框
            file_path, _ = QFileDialog.getOpenFileName(
                window,
                "选择信号数据文件",
                start_dir,
                "Excel文件 (*.xlsx *.xls);;所有文件 (*)"
            )
            
            if file_path:
                # 更新会话级路径记忆
                self._last_directory = str(Path(file_path).parent)
                
                # 发送文件选择信号
                self.file_selected.emit(file_path)
                
                ui_logger.info(f"用户选择文件: {file_path}")
                return file_path
                
            return None
            
        except Exception as e:
            error_msg = f"文件选择出错: {str(e)}"
            ui_logger.error(error_msg)
            QMessageBox.critical(window, "错误", error_msg)
            return None
    
    def import_data(self, window, file_path: str) -> None:
        """导入文件
        
        Args:
            window: 主窗口实例
            file_path: 要导入的文件路径
        """
        if not file_path:
            QMessageBox.warning(window, "警告", "请先选择要导入的文件")
            return
        
        try:
            # 验证文件存在
            if not Path(file_path).exists():
                error_msg = f"文件不存在: {file_path}"
                QMessageBox.warning(window, "警告", error_msg)
                return
            
            # 发送导入开始信号
            self.import_started.emit()
            
            # 创建导入任务
            import_task = SignalImportTask(
                file_path=file_path,
                service=window.signal_service,
                event_bus=self.event_bus
            )
            
            # 提交任务到线程池
            future = window.thread_pool.submit(import_task.execute)
            future.add_done_callback(
                lambda f: self._handle_import_result(f, window)
            )
            
            ui_logger.info(f"信号导入任务已启动: {file_path}")
            
        except Exception as e:
            error_msg = f"导入处理出错: {str(e)}"
            ui_logger.error(error_msg)
            QMessageBox.critical(window, "错误", error_msg)
            self.import_error.emit(error_msg)
    
    def _handle_import_result(self, future, window) -> None:
        """处理导入任务的执行结果
        
        Args:
            future: Future对象，包含任务执行结果
            window: 主窗口实例
        """
        try:
            success, message, signal = future.result()
            
            if success and signal:
                ui_logger.info(f"导入任务完成: {signal.id}")
            else:
                ui_logger.error(f"导入任务失败: {message}")
                
        except Exception as e:
            error_msg = f"处理导入结果时出错: {str(e)}"
            ui_logger.error(error_msg)
            self._safe_emit_signal(self.import_error, error_msg)
            self._safe_emit_signal(self.import_finished, False)

    def cleanup(self) -> None:
        """清理资源"""
        # 取消事件订阅
        self.event_bus.unsubscribe(SignalEvents.DATA_IMPORT_STARTED, self._on_import_started)
        self.event_bus.unsubscribe(SignalEvents.DATA_IMPORT_COMPLETED, self._on_import_completed)
        self.event_bus.unsubscribe(SignalEvents.DATA_IMPORT_FAILED, self._on_import_failed)
        self.event_bus.unsubscribe(SignalEvents.DATA_LOADING_STARTED, self._on_loading_started)
        self.event_bus.unsubscribe(SignalEvents.DATA_LOADING_COMPLETED, self._on_loading_completed)
        self.event_bus.unsubscribe(SignalEvents.DATA_LOADING_FAILED, self._on_loading_failed)

        ui_logger.info("SignalImportHandler 资源已清理")
