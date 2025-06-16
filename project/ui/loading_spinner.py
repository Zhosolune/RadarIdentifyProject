from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen

class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置窗口标志
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化变量
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.setInterval(50)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        
        # 添加大小跟踪
        self.timer_resize = QTimer(self)
        self.timer_resize.timeout.connect(self.check_parent_size)
        self.timer_resize.setInterval(100)
        
        # 初始化时隐藏
        self.hide()
    
    def check_parent_size(self):
        """检查并更新大小"""
        if self.parent() and self.isVisible():
            self.resize(self.parent().size())
    
    def showEvent(self, event):
        """显示时更新大小"""
        if self.parent():
            self.resize(self.parent().size())
        self.timer_resize.start()
        super().showEvent(event)
    
    def hideEvent(self, event):
        """隐藏时停止检查"""
        self.timer_resize.stop()
        super().hideEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制半透明背景
        painter.fillRect(self.rect(), QColor(255, 255, 255, 180))
        
        # 绘制加载动画
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        
        # 设置画笔
        pen = QPen(QColor("#4772c3"))
        pen.setWidth(4)
        painter.setPen(pen)
        
        # 绘制圆弧
        for i in range(8):
            painter.rotate(45)
            opacity = (i + 1) / 8.0
            painter.setOpacity(opacity)
            painter.drawLine(0, 20, 0, 40)
    
    def rotate(self):
        self.angle = (self.angle + 45) % 360
        self.update()
    
    def start(self):
        if self.parent():
            self.resize(self.parent().size())
        self.show()
        self.timer.start()  # 启动旋转动画
    
    def stop(self):
        self.timer.stop()  # 停止旋转动画
        self.timer_resize.stop()  # 停止大小检查
        self.hide() 