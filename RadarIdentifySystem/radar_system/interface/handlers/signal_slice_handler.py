"""信号切片处理器

统一的信号切片事件处理器，基于简化的事件系统实现。
"""

from typing import Optional, Tuple
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QMessageBox

from radar_system.infrastructure.common.logging import ui_logger
from radar_system.infrastructure.common.thread_safe_signal_emitter import ThreadSafeSignalEmitter

from radar_system.application.tasks.signal_tasks import SignalSliceTask
from radar_system.application.services.signal_service import SignalService
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
    slice_display_ready = pyqtSignal(object)        # 切片显示就绪(切片数据)
    
    def __init__(self, signal_service: SignalService):
        """初始化信号切片处理器

        通过构造函数注入SignalService，符合DDD分层架构原则。
        Handler层直接依赖Application层，避免通过UI层访问服务。

        Args:
            signal_service: 信号处理服务实例
        """
        super().__init__()
        self.signal_service = signal_service
        ui_logger.info("SignalSliceHandler 初始化完成")
    

    

    
    def start_slice(self, signal: SignalData, thread_pool, message_callback=None) -> None:
        """启动信号切片处理

        符合DDD分层架构：Handler层直接使用注入的SignalService，
        不再依赖UI层实例来访问Application层服务。

        Args:
            signal: 待切片的信号数据
            thread_pool: 线程池实例
            message_callback: 消息回调函数（可选，用于显示错误消息）
        """
        if not signal:
            if message_callback:
                message_callback("警告", "没有可用的信号数据", QMessageBox.Warning)
            return

        try:
            # 发射切片开始信号
            self.safe_emit_signal(self.slice_started)

            # 创建切片任务，使用注入的SignalService
            slice_task = SignalSliceTask(
                signal=signal,
                service=self.signal_service
            )

            # 提交任务到线程池
            future = thread_pool.submit(slice_task.execute)
            future.add_done_callback(
                lambda f: self._handle_slice_result(f)
            )

            ui_logger.info(f"信号切片任务已启动: {signal.id}")

        except Exception as e:
            error_msg = f"启动切片任务失败: {str(e)}"
            ui_logger.error(error_msg)
            if message_callback:
                message_callback("错误", error_msg, QMessageBox.Critical)
    
    def _handle_slice_result(self, future) -> None:
        """处理切片任务结果

        符合DDD分层架构：使用注入的SignalService，不依赖UI层实例。
        """
        try:
            success, message, slices = future.result()

            if success and slices:
                ui_logger.info(f"切片任务完成，生成{len(slices)}个切片")
                # 发送切片完成信号
                self.safe_emit_signal(self.slice_completed, True, len(slices))

                # ✅ 架构合规：直接使用注入的SignalService
                self.request_next_slice()
            else:
                ui_logger.error(f"切片任务失败: {message}")
                # 发送切片失败信号
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
    
    def request_next_slice(self) -> bool:
        """请求下一个切片数据

        Handler层专注于业务协调，通过信号机制通知UI层更新。
        实现预防性设计：如果没有更多切片，直接返回False，不发射信号。
        符合DDD分层架构原则：使用注入的SignalService，避免Handler层直接操作UI层。

        Returns:
            bool: 是否成功获取下一个切片
        """
        try:
            # ✅ 架构合规：使用注入的SignalService
            next_slice = self.signal_service.get_next_slice()
            if not next_slice:
                ui_logger.debug("没有更多切片可显示，请求被忽略")
                return False

            # 获取切片信息用于日志
            current_index, total_count = self.signal_service.get_slice_info()
            ui_logger.info(f"准备显示切片 {current_index}/{total_count}")

            # 发射切片显示就绪信号，由UI层负责界面更新
            self.safe_emit_signal(self.slice_display_ready, next_slice)
            return True

        except Exception as e:
            error_msg = f"获取下一个切片失败: {str(e)}"
            ui_logger.error(error_msg)
            # 只有真正的错误才记录，不发射UI信号
            return False
    
    def get_current_slice(self) -> Optional[SignalSlice]:
        """获取当前切片

        符合DDD分层架构：使用注入的SignalService。

        Returns:
            Optional[SignalSlice]: 当前切片，如果没有则返回None
        """
        return self.signal_service.get_current_slice()

    def get_slice_info(self) -> Tuple[int, int]:
        """获取切片信息

        符合DDD分层架构：使用注入的SignalService。

        Returns:
            Tuple[int, int]: (当前切片索引+1, 总切片数)
        """
        return self.signal_service.get_slice_info()



    def cleanup(self) -> None:
        """清理资源"""
        ui_logger.info("SignalSliceHandler 资源已清理")
