"""
线程安全信号发射器

基础设施层组件，提供线程安全的Qt信号发射功能。
遵循YAGNI原则，只实现当前需要的功能。
"""

from PyQt5.QtCore import QObject, QThread, QEvent
from PyQt5.QtWidgets import QApplication


class ThreadSafeSignalEmitter(QObject):
    """线程安全信号发射器
    
    基础设施组件，用于在多线程环境中安全地发射Qt信号。
    
    使用方法：
        1. 继承此类
        2. 调用 safe_emit_signal 方法发射信号
    
    设计原则：
        - 单一职责：只负责线程安全的信号发射
        - 简单实用：基于QApplication.postEvent的可靠实现
        - 易于使用：提供简单的API接口
    """
    
    def safe_emit_signal(self, signal, *args) -> None:
        """线程安全的信号发射
        
        Args:
            signal: 要发射的Qt信号
            *args: 信号参数
        """
        if QThread.currentThread() is QApplication.instance().thread():
            # 在主线程中直接发射
            signal.emit(*args)
        else:
            # 在非主线程中，使用 QApplication.postEvent 来发送自定义事件
            class SignalEvent(QEvent):
                def __init__(self, signal, args):
                    super().__init__(QEvent.User)
                    self.signal = signal
                    self.args = args
            
            # 发送事件到主线程
            event = SignalEvent(signal, args)
            QApplication.postEvent(self, event)
    
    def event(self, event):
        """处理自定义事件"""
        if event.type() == QEvent.User:
            # 在主线程中发射信号
            event.signal.emit(*event.args)
            return True
        return super().event(event)
