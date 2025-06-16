"""UI事件处理器模块

本模块实现了与UI交互相关的事件处理器。
"""
from typing import Optional, List, Dict
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication

from radar_system.domain.signal.entities.signal import SignalData, SignalSlice
from radar_system.application.tasks.signal_tasks import SignalImportTask, SignalSliceTask
from radar_system.infrastructure.common.logging import ui_logger
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus

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
        
    def browse_file(self, window) -> None:
        """处理浏览文件事件
        
        打开文件选择对话框，允许用户选择Excel文件。
        
        Args:
            window: 主窗口实例
        """
        try:
            # 确定起始目录
            start_dir = ""
            if self._last_directory and Path(self._last_directory).exists():
                start_dir = self._last_directory
            elif window.config_manager.ui.last_import_dir and Path(window.config_manager.ui.last_import_dir).exists():
                start_dir = window.config_manager.ui.last_import_dir
            
            file_path, _ = QFileDialog.getOpenFileName(
                window,
                "选择Excel文件",
                start_dir,
                "Excel Files (*.xlsx *.xls);;All Files (*)"
            )
            
            if file_path:
                path = Path(file_path)
                if path.suffix.lower() in ['.xlsx', '.xls']:
                    # 更新路径记忆
                    self._last_directory = str(path.parent)
                    window.config_manager.ui.last_import_dir = self._last_directory
                    # 发送文件选择信号
                    self.file_selected.emit(file_path)
                else:
                    QMessageBox.warning(window, "错误", "请选择Excel文件")
                    self.file_selected.emit("")
                    
        except Exception as e:
            ui_logger.error(f"浏览文件时出错: {str(e)}")
            QMessageBox.critical(window, "错误", f"浏览文件失败: {str(e)}")
            self.import_error.emit(str(e))
            
    def import_data(self, window) -> None:
        """处理数据导入事件
        
        从选择的Excel文件导入雷达信号数据。使用线程池处理IO密集型操作。
        
        Args:
            window: 主窗口实例
        """
        try:
            file_path = window.import_path.text()
            if not file_path:
                QMessageBox.warning(window, "警告", "请选择要导入的文件")
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
                
        except Exception as e:
            error_msg = f"导入数据时出错: {str(e)}"
            ui_logger.error(error_msg)
            QMessageBox.critical(window, "错误", error_msg)
            self.import_error.emit(error_msg)
            self.import_finished.emit(False)
            
    def _handle_import_result(self, future, window) -> None:
        """处理导入任务的执行结果
        
        Args:
            future: Future对象，包含任务执行结果
            window: 主窗口实例
        """
        # 检查当前线程
        is_main_thread = QThread.currentThread() is QApplication.instance().thread()
        
        try:
            success, message, signal = future.result()
            
            # 如果不在主线程，使用QMetaObject.invokeMethod触发信号
            if not is_main_thread:
                # 发送导入完成信号，让主窗口处理UI更新
                self.import_finished.emit(success)
                if not success:
                    self.import_error.emit(message)
                return
                
            # 在主线程中，直接处理UI更新
            if not success:
                QMessageBox.warning(window, "错误", message)
                self.import_error.emit(message)
            
            # 发送导入完成信号
            self.import_finished.emit(success)
            
        except Exception as e:
            error_msg = f"导入数据时出错: {str(e)}"
            ui_logger.error(error_msg)
            
            # 如果不在主线程，使用QMetaObject.invokeMethod触发信号
            if not is_main_thread:
                self.import_error.emit(error_msg)
                self.import_finished.emit(False)
                return
                
            # 在主线程中，直接处理错误
            QMessageBox.critical(window, "错误", error_msg)
            self.import_error.emit(error_msg)
            self.import_finished.emit(False)

class SignalSliceHandler(QObject):
    """信号切片事件处理器
    
    处理与信号数据切片相关的所有UI事件。
    
    Signals:
        slice_started: 切片开始信号
        slice_finished: 切片完成信号，携带成功标志
        slice_error: 切片错误信号，携带错误信息
        
    Attributes:
        event_bus (EventBus): 事件总线实例
    """
    
    # 定义Qt信号
    slice_started = pyqtSignal()
    slice_finished = pyqtSignal(bool)  # 参数为是否成功
    slice_error = pyqtSignal(str)  # 参数为错误信息
    
    def __init__(self, event_bus: EventBus):
        """初始化处理器
        
        Args:
            event_bus: 事件总线实例
        """
        super().__init__()
        self.event_bus = event_bus
        self.current_slice_index = -1
        self.slices = None
        
    def start_slice(self, window) -> None:
        """处理开始切片事件
        
        对当前信号数据进行切片处理。使用线程池进行异步处理。
        
        Args:
            window: 主窗口实例
        """
        try:
            # 获取当前信号数据
            signal = window.signal_service.get_current_signal()
            if signal is None:
                QMessageBox.warning(window, "警告", "没有可用的信号数据")
                return
                
            # 发送切片开始信号
            self.slice_started.emit()
            
            # 创建切片任务
            slice_task = SignalSliceTask(
                signal=signal,
                service=window.signal_service,
                event_bus=self.event_bus
            )
            
            # 提交任务到线程池
            future = window.thread_pool.submit(slice_task.execute)
            future.add_done_callback(
                lambda f: self._handle_slice_result(f, window)
            )
                
        except Exception as e:
            error_msg = f"切片处理出错: {str(e)}"
            ui_logger.error(error_msg)
            QMessageBox.critical(window, "错误", error_msg)
            self.slice_error.emit(error_msg)
            self.slice_finished.emit(False)
            
    def _handle_slice_result(self, future, window) -> None:
        """处理切片任务的执行结果
        
        Args:
            future: Future对象，包含任务执行结果
            window: 主窗口实例
        """
        # 检查当前线程
        is_main_thread = QThread.currentThread() is QApplication.instance().thread()
        
        try:
            success, message, slices = future.result()
            
            # 无论在哪个线程，都保存切片结果
            if success and slices:
                self.slices = slices
                self.current_slice_index = -1
            
            # 如果不在主线程，使用QMetaObject.invokeMethod触发信号
            if not is_main_thread:
                # 发送切片完成信号，让主窗口处理UI更新
                self.slice_finished.emit(success)
                if not success:
                    self.slice_error.emit(message)
                return
                
            # 在主线程中，直接处理UI更新
            if not success:
                QMessageBox.warning(window, "错误", message)
                self.slice_error.emit(message)
            else:
                # 处理第一个切片
                if self.slices and len(self.slices) > 0:
                    self.show_next_slice(window)
            
            # 发送切片完成信号
            self.slice_finished.emit(success)
            
        except Exception as e:
            error_msg = f"切片处理出错: {str(e)}"
            ui_logger.error(error_msg)
            
            # 如果不在主线程，使用QMetaObject.invokeMethod触发信号
            if not is_main_thread:
                self.slice_error.emit(error_msg)
                self.slice_finished.emit(False)
                return
                
            # 在主线程中，直接处理错误
            QMessageBox.critical(window, "错误", error_msg)
            self.slice_error.emit(error_msg)
            self.slice_finished.emit(False)
            
    def show_next_slice(self, window) -> bool:
        """显示下一个切片
        
        切换到下一个切片并更新UI显示。
        
        Args:
            window: 主窗口实例
            
        Returns:
            bool: 是否成功显示下一个切片
        """
        try:
            if not self.slices:
                return False
                
            if self.current_slice_index < len(self.slices) - 1:
                self.current_slice_index += 1
                current_slice = self.slices[self.current_slice_index]
                
                # 更新切片显示
                window._update_slice_display(current_slice)
                
                return True
                
            return False
            
        except Exception as e:
            error_msg = f"显示下一个切片时出错: {str(e)}"
            ui_logger.error(error_msg)
            QMessageBox.critical(window, "错误", error_msg)
            return False
            
    def get_current_slice(self) -> Optional[SignalSlice]:
        """获取当前切片
        
        Returns:
            Optional[SignalSlice]: 当前切片实例，如果没有则返回None
        """
        if not self.slices or self.current_slice_index < 0:
            return None
            
        if self.current_slice_index < len(self.slices):
            return self.slices[self.current_slice_index]
            
        return None
        
    def get_current_slice_index(self) -> int:
        """获取当前切片索引
        
        Returns:
            int: 当前切片索引，如果没有则返回-1
        """
        return self.current_slice_index
