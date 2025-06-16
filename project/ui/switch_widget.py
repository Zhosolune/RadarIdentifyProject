from PyQt5.QtCore import Qt, QPropertyAnimation, QRectF, pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen

class Switch(QWidget):
    # 添加状态改变信号
    stateChanged = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._pos = 0.0
        
        # 设置固定大小
        self.setFixedSize(34, 16)
        
        # 颜色设置
        self._track_color = QColor("#4772c3")
        self._thumb_color = QColor("#ffffff")
        self._track_opacity = 0.6
        self._border_color = QColor("#A8D4FF")  # 添加浅蓝色边框颜色
        
        # 初始化动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(200)
        
        # 设置鼠标悬停样式为手指
        self.setCursor(Qt.PointingHandCursor)
        
    def isChecked(self) -> bool:
        """返回开关状态"""
        return self._checked
        
    def setChecked(self, checked: bool):
        """设置开关状态并发送信号"""
        if self._checked != checked:
            self._checked = checked
            self._pos = 1.0 if checked else 0.0
            self.update()
            self.stateChanged.emit(self._checked)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)  # 使用setChecked方法来改变状态
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制轨道
        painter.setOpacity(self._track_opacity)
        track_path = QPainterPath()
        track_rect = QRectF(0, 0, self.width(), self.height())
        track_path.addRoundedRect(track_rect, self.height() / 2, self.height() / 2)
        painter.fillPath(track_path, self._track_color)
        
        # 绘制轨道边框
        painter.setOpacity(1.0)
        pen = QPen(self._border_color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(track_path)
        
        # 绘制滑块
        thumb_rect = QRectF(
            self._pos * (self.width() - self.height()),
            0,
            self.height(),
            self.height()
        )
        thumb_path = QPainterPath()
        thumb_path.addEllipse(thumb_rect)
        painter.fillPath(thumb_path, self._thumb_color)
        
        # 绘制滑块边框
        painter.drawPath(thumb_path) 