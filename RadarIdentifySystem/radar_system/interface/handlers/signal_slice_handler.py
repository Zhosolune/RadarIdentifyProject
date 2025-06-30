"""信号切片处理器

基于实际需求的简化实现，避免过度设计。
"""

import uuid
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QApplication
from PyQt5.QtWidgets import QMessageBox

from radar_system.infrastructure.common.logging import ui_logger
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
from radar_system.infrastructure.async_core.event_bus.event_constants import SignalEvents
from radar_system.application.services.signal_service import SignalService
from radar_system.application.tasks.signal_tasks import SignalSliceTask
from radar_system.domain.signal.entities.signal import SignalData, SignalSlice


class SignalSliceHandler(QObject):
    """信号切片事件处理器
    
    只实现当前实际需要的功能，避免过度设计。
    
    主要功能：
    1. 监听切片处理事件
    2. 启动切片任务
    3. 管理切片状态
    4. 线程安全的UI更新
    """
    
    # 只定义实际需要的Qt信号
    slice_started = pyqtSignal()
    slice_completed = pyqtSignal(bool, int)  # 成功标志, 切片数量
    slice_failed = pyqtSignal(str)  # 错误信息
    
    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        
        # 切片状态管理
        self.current_slices: Optional[list] = None
        self.current_slice_index: int = -1
        
        # 订阅事件（只订阅实际需要的事件）
        self._subscribe_events()
        
        ui_logger.info("SignalSliceHandler 初始化完成")
    
    def _subscribe_events(self) -> None:
        """订阅事件"""
        self.event_bus.subscribe(SignalEvents.SLICE_PROCESSING_STARTED, self._on_slice_started)
        self.event_bus.subscribe(SignalEvents.SLICE_PROCESSING_COMPLETED, self._on_slice_completed)
        self.event_bus.subscribe(SignalEvents.SLICE_PROCESSING_FAILED, self._on_slice_failed)
    
    def _on_slice_started(self, data: Dict[str, Any]) -> None:
        """处理切片开始事件"""
        signal_id = data.get('signal_id', 'unknown')
        ui_logger.info(f"信号切片开始: {signal_id}")
        
        # 线程安全的UI更新
        self._safe_emit_signal(self.slice_started)
    
    def _on_slice_completed(self, data: Dict[str, Any]) -> None:
        """处理切片完成事件"""
        signal_id = data.get('signal_id', 'unknown')
        slice_count = data.get('slice_count', 0)
        
        ui_logger.info(f"信号切片完成: {signal_id}, 切片数量: {slice_count}")
        
        # 线程安全的UI更新
        self._safe_emit_signal(self.slice_completed, True, slice_count)
    
    def _on_slice_failed(self, data: Dict[str, Any]) -> None:
        """处理切片失败事件"""
        signal_id = data.get('signal_id', 'unknown')
        error = data.get('error', '未知错误')
        
        ui_logger.error(f"信号切片失败: {signal_id}, 错误: {error}")
        
        # 线程安全的UI更新
        self._safe_emit_signal(self.slice_failed, error)
    
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
            # 创建切片任务（简化版，不发布重复事件）
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
            
            ui_logger.info(f"信号切片任务已启动: {signal.id}")
            
        except Exception as e:
            error_msg = f"启动切片任务失败: {str(e)}"
            ui_logger.error(error_msg)
            self._show_message_box(window, "错误", error_msg, QMessageBox.Critical)
    
    def _handle_slice_result(self, future, window) -> None:
        """处理切片任务结果"""
        try:
            success, message, slices = future.result()
            
            if success and slices:
                # 保存切片结果
                self.current_slices = slices
                self.current_slice_index = -1
                ui_logger.info(f"切片任务完成，生成{len(slices)}个切片")
            else:
                ui_logger.error(f"切片任务失败: {message}")
                
        except Exception as e:
            error_msg = f"处理切片结果时出错: {str(e)}"
            ui_logger.error(error_msg)
            self._show_message_box(window, "错误", error_msg, QMessageBox.Critical)
    
    def _show_message_box(self, parent, title: str, message: str, icon) -> None:
        """线程安全的消息框显示"""
        if QThread.currentThread() is QApplication.instance().thread():
            # 在主线程中直接显示
            msg_box = QMessageBox(icon, title, message, QMessageBox.Ok, parent)
            msg_box.exec_()
        else:
            # 在非主线程中，使用QMetaObject.invokeMethod
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
        
        # 这里应该调用窗口的切片显示更新方法
        # 具体实现取决于窗口的接口设计
        
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
        # 取消事件订阅
        self.event_bus.unsubscribe(SignalEvents.SLICE_PROCESSING_STARTED, self._on_slice_started)
        self.event_bus.unsubscribe(SignalEvents.SLICE_PROCESSING_COMPLETED, self._on_slice_completed)
        self.event_bus.unsubscribe(SignalEvents.SLICE_PROCESSING_FAILED, self._on_slice_failed)
        
        ui_logger.info("SignalSliceHandler 资源已清理")
