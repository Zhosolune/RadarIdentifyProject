"""信号导入事件处理器

处理与信号数据导入相关的所有UI事件。
"""

from typing import Optional
from pathlib import Path
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from radar_system.application.tasks.signal_tasks import SignalImportTask
from radar_system.infrastructure.common.logging import ui_logger
from radar_system.infrastructure.common.thread_safe_signal_emitter import ThreadSafeSignalEmitter



class SignalImportHandler(ThreadSafeSignalEmitter):
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
    
    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self._last_directory = None  # 会话级路径记忆

        ui_logger.info("SignalImportHandler 初始化完成")
    

    

    
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
            
            # 创建导入任务（移除event_bus参数）
            import_task = SignalImportTask(
                file_path=file_path,
                service=window.signal_service
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
                # 发射导入成功信号
                self.safe_emit_signal(self.import_finished, True)
            else:
                ui_logger.error(f"导入任务失败: {message}")
                # 发射导入失败信号
                self.safe_emit_signal(self.import_error, message)
                self.safe_emit_signal(self.import_finished, False)

        except Exception as e:
            error_msg = f"处理导入结果时出错: {str(e)}"
            ui_logger.error(error_msg)
            self.safe_emit_signal(self.import_error, error_msg)
            self.safe_emit_signal(self.import_finished, False)

    def cleanup(self) -> None:
        """清理资源"""
        ui_logger.info("SignalImportHandler 资源已清理")
