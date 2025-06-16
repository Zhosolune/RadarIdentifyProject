"""加载动画组件

本模块实现了一个加载动画组件，用于显示加载状态。
"""
from typing import Optional
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen
from radar_system.infrastructure.common.logging import ui_logger
from radar_system.interface.styles.style_sheets import StyleSheets

class LoadingSpinner(QWidget):
    """加载动画组件
    
    一个简单的旋转加载动画组件，用于显示加载状态。
    动画由8个逐渐变淡的线段组成，围绕中心点旋转。
    
    Attributes:
        angle (int): 当前旋转角度
        timer (QTimer): 控制旋转动画的定时器
        timer_resize (QTimer): 控制大小更新的定时器
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化加载动画组件
        
        Args:
            parent: 父级窗口部件
        """
        super().__init__(parent)
        
        try:
            # 获取当前主题颜色
            self.theme_colors = StyleSheets.get_theme_colors()
            
            # 设置窗口标志和属性
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_TransparentForMouseEvents)
            
            # 初始化旋转动画定时器
            self.angle = 0
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.rotate)
            self.timer.setInterval(50)  # 20fps的动画速度
            
            # 初始化大小跟踪定时器
            self.timer_resize = QTimer(self)
            self.timer_resize.timeout.connect(self.check_parent_size)
            self.timer_resize.setInterval(100)
            
            # 设置布局
            layout = QVBoxLayout()
            layout.setAlignment(Qt.AlignCenter)
            self.setLayout(layout)
            
            # 初始化时隐藏
            self.hide()
            ui_logger.debug("LoadingSpinner组件初始化完成")
            
        except Exception as e:
            ui_logger.error(f"LoadingSpinner初始化失败: {str(e)}")
            raise
    
    def check_parent_size(self) -> None:
        """检查并更新组件大小以匹配父级窗口"""
        try:
            if self.parent() and self.isVisible():
                self.resize(self.parent().size())
                ui_logger.debug("LoadingSpinner大小已更新")
        except Exception as e:
            ui_logger.error(f"更新LoadingSpinner大小失败: {str(e)}")
    
    def showEvent(self, event) -> None:
        """显示事件处理
        
        Args:
            event: 显示事件对象
        """
        try:
            if self.parent():
                self.resize(self.parent().size())
            self.timer_resize.start()
            super().showEvent(event)
            ui_logger.debug("LoadingSpinner显示并启动大小跟踪")
        except Exception as e:
            ui_logger.error(f"LoadingSpinner显示失败: {str(e)}")
    
    def hideEvent(self, event) -> None:
        """隐藏事件处理
        
        Args:
            event: 隐藏事件对象
        """
        try:
            self.timer_resize.stop()
            super().hideEvent(event)
            ui_logger.debug("LoadingSpinner隐藏并停止大小跟踪")
        except Exception as e:
            ui_logger.error(f"LoadingSpinner隐藏失败: {str(e)}")
    
    def rotate(self) -> None:
        """更新旋转角度并重绘"""
        try:
            self.angle = (self.angle + 45) % 360
            self.update()
        except Exception as e:
            ui_logger.error(f"LoadingSpinner旋转更新失败: {str(e)}")
    
    def start(self) -> None:
        """启动动画"""
        try:
            if self.parent():
                self.resize(self.parent().size())
            self.show()
            self.timer.start()
            ui_logger.debug("LoadingSpinner动画已启动")
        except Exception as e:
            ui_logger.error(f"启动LoadingSpinner动画失败: {str(e)}")
    
    def stop(self) -> None:
        """停止动画"""
        try:
            self.timer.stop()
            self.timer_resize.stop()
            self.hide()
            ui_logger.debug("LoadingSpinner动画已停止")
        except Exception as e:
            ui_logger.error(f"停止LoadingSpinner动画失败: {str(e)}")
    
    def paintEvent(self, event) -> None:
        """绘制事件处理
        
        Args:
            event: 绘制事件对象
        """
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 半透明背景使用主题背景色
            bg_color = QColor(self.theme_colors['background'])
            bg_color.setAlpha(180)
            painter.fillRect(self.rect(), bg_color)
            
            # 绘制加载动画
            painter.translate(self.width() / 2, self.height() / 2)
            painter.rotate(self.angle)
            
            # 设置画笔
            pen = QPen(QColor(self.theme_colors['primary']))
            pen.setWidth(4)
            painter.setPen(pen)
            
            # 绘制8个逐渐变淡的线段
            for i in range(8):
                painter.rotate(45)
                opacity = (i + 1) / 8.0
                painter.setOpacity(opacity)
                painter.drawLine(0, 20, 0, 40)
        except Exception as e:
            ui_logger.error(f"LoadingSpinner绘制失败: {str(e)}")
