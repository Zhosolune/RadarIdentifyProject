from typing import Optional
from PyQt5.QtCore import Qt, QPropertyAnimation, QRectF, pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen
from radar_system.infrastructure.common.logging import ui_logger
from radar_system.interface.styles.style_sheets import StyleSheets

class Switch(QWidget):
    """自定义切换开关组件
    
    一个简单的开关控件，具有动画效果和状态变化信号。
    
    Signals:
        stateChanged: 当开关状态改变时发出的信号，携带新的状态值（bool）
    
    Attributes:
        _checked (bool): 当前开关状态
        _pos (float): 滑块位置（0.0-1.0）
        _track_color (QColor): 轨道颜色
        _thumb_color (QColor): 滑块颜色
        _track_opacity (float): 轨道透明度
        _border_color (QColor): 边框颜色
        animation (QPropertyAnimation): 滑块动画
    """
    
    # 添加状态改变信号
    stateChanged = pyqtSignal(bool)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化切换开关组件
        
        Args:
            parent: 父级窗口部件
        """
        super().__init__(parent)
        self._checked = False
        self._pos = 0.0
        
        # 设置固定大小
        self.setFixedSize(34, 16)
        
        # 获取当前主题颜色
        theme_colors = StyleSheets.get_theme_colors()
        
        # 使用主题颜色
        self._track_color = QColor(theme_colors['primary'])
        self._thumb_color = QColor(theme_colors['background'])
        self._track_opacity = 0.6
        self._border_color = QColor(theme_colors['secondary'])
        
        # 初始化动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(200)
        
        ui_logger.debug("Switch组件初始化完成")
    
    def isChecked(self) -> bool:
        """返回开关状态
        
        Returns:
            bool: 当前开关状态
        """
        return self._checked
    
    def setChecked(self, checked: bool) -> None:
        """设置开关状态并发送信号
        
        Args:
            checked: 新的开关状态
        """
        if self._checked != checked:
            self._checked = checked
            self._pos = 1.0 if checked else 0.0
            self.update()
            self.stateChanged.emit(self._checked)
            ui_logger.debug(f"Switch状态已更改为: {'开启' if checked else '关闭'}")
    
    def mousePressEvent(self, event) -> None:
        """鼠标按下事件处理
        
        Args:
            event: 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
            ui_logger.debug("Switch接收到鼠标点击事件")
    
    def paintEvent(self, event) -> None:
        """绘制事件处理
        
        Args:
            event: 绘制事件对象
        """
        try:
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
        except Exception as e:
            ui_logger.error(f"Switch绘制失败: {str(e)}")
