"""信号切片处理器

统一的信号切片事件处理器，基于简化的事件系统实现。
"""

from typing import Optional
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QMessageBox

from radar_system.infrastructure.common.logging import ui_logger
from radar_system.infrastructure.common.thread_safe_signal_emitter import ThreadSafeSignalEmitter

from radar_system.application.tasks.signal_tasks import SignalSliceTask
from radar_system.domain.signal.entities.signal import SignalData, SignalSlice


class SignalSliceHandler(ThreadSafeSignalEmitter):
    """信号切片事件处理器
    
    只实现当前实际需要的功能，避免过度设计。
    
    主要功能：
    1. 监听切片处理事件
    2. 启动切片任务
    3. 管理切片状态
    4. 线程安全的UI更新
    """
    
    # 定义Qt信号（统一版本，每个功能只有一个信号）
    slice_started = pyqtSignal()                    # 切片开始
    slice_completed = pyqtSignal(bool, int)         # 切片完成(成功标志, 切片数量)
    slice_failed = pyqtSignal(str)                  # 切片失败(错误信息)
    
    def __init__(self):
        super().__init__()

        # 切片状态管理
        self.current_slices: Optional[list] = None
        self.current_slice_index: int = -1

        ui_logger.info("SignalSliceHandler 初始化完成")
    

    

    
    def start_slice(self, window, signal: SignalData) -> None:
        """启动信号切片处理
        
        Args:
            window: 主窗口实例
            signal: 待切片的信号数据
        """
        if not signal:
            self._show_message_box(window, "警告", "没有可用的信号数据", QMessageBox.Warning)
            return
        
        try:
            # 发射切片开始信号
            self.safe_emit_signal(self.slice_started)

            # 创建切片任务（移除event_bus参数）
            slice_task = SignalSliceTask(
                signal=signal,
                service=window.signal_service
            )
            
            # 提交任务到线程池
            future = window.thread_pool.submit(slice_task.execute)
            future.add_done_callback(
                lambda f: self._handle_slice_result(f, window)
            )
            
            ui_logger.info(f"信号切片任务已启动: {signal.id}")
            
        except Exception as e:
            error_msg = f"启动切片任务失败: {str(e)}"
            ui_logger.error(error_msg)
            self._show_message_box(window, "错误", error_msg, QMessageBox.Critical)
    
    def _handle_slice_result(self, future, window) -> None:
        """处理切片任务结果"""
        # 检查当前线程
        is_main_thread = QThread.currentThread() is QApplication.instance().thread()

        try:
            success, message, slices = future.result()

            # 无论在哪个线程，都保存切片结果
            if success and slices:
                self.current_slices = slices
                self.current_slice_index = -1
                ui_logger.info(f"切片任务完成，生成{len(slices)}个切片")

                # 如果在主线程且有切片，显示第一个切片
                if is_main_thread and len(slices) > 0:
                    self.show_next_slice(window)
            else:
                ui_logger.error(f"切片任务失败: {message}")

            # 发送切片完成信号
            if success:
                self.safe_emit_signal(self.slice_completed, True, len(slices) if slices else 0)
            else:
                self.safe_emit_signal(self.slice_failed, message)

        except Exception as e:
            error_msg = f"处理切片结果时出错: {str(e)}"
            ui_logger.error(error_msg)
            self.safe_emit_signal(self.slice_failed, error_msg)
    
    def _show_message_box(self, parent, title: str, message: str, icon) -> None:
        """线程安全的消息框显示"""
        if QThread.currentThread() is QApplication.instance().thread():
            # 在主线程中直接显示
            msg_box = QMessageBox(icon, title, message, QMessageBox.Ok, parent)
            msg_box.exec_()
        else:
            # 在非主线程中，使用QTimer.singleShot来确保在主线程中执行
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._show_message_box_in_main_thread(parent, title, message, icon))

    def _show_message_box_in_main_thread(self, parent, title: str, message: str, icon) -> None:
        """在主线程中显示消息框"""
        msg_box = QMessageBox(icon, title, message, QMessageBox.Ok, parent)
        msg_box.exec_()
    
    def show_next_slice(self, window) -> bool:
        """显示下一个切片"""
        if not self.current_slices:
            self._show_message_box(window, "提示", "没有可用的切片数据", QMessageBox.Information)
            return False
        
        if self.current_slice_index >= len(self.current_slices) - 1:
            self._show_message_box(window, "提示", "已经是最后一个切片", QMessageBox.Information)
            return False
        
        self.current_slice_index += 1
        current_slice = self.current_slices[self.current_slice_index]

        ui_logger.info(f"显示切片 {self.current_slice_index + 1}/{len(self.current_slices)}")

        # 调用窗口的切片显示更新方法（兼容旧版本接口）
        try:
            if hasattr(window, '_update_slice_display'):
                window._update_slice_display(current_slice)
            elif hasattr(window, 'update_slice_display'):
                window.update_slice_display(current_slice)
        except Exception as e:
            ui_logger.warning(f"更新切片显示失败: {str(e)}")

        return True
    
    def get_current_slice(self) -> Optional[SignalSlice]:
        """获取当前切片"""
        if self.current_slices and 0 <= self.current_slice_index < len(self.current_slices):
            return self.current_slices[self.current_slice_index]
        return None
    
    def get_current_slice_index(self) -> int:
        """获取当前切片索引"""
        return self.current_slice_index
    
    def get_slice_count(self) -> int:
        """获取切片总数"""
        return len(self.current_slices) if self.current_slices else 0

    def reset_slices(self) -> None:
        """重置切片状态"""
        self.current_slices = None
        self.current_slice_index = -1
        ui_logger.debug("切片状态已重置")



    def cleanup(self) -> None:
        """清理资源"""
        ui_logger.info("SignalSliceHandler 资源已清理")
