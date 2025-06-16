from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize, QPoint
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor

class RectangleAnimation(QWidget):
    """矩形动画组件
    
    显示5个矩形的走马灯式动画效果
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置首选大小
        self.setFixedHeight(40)
        
        # 设置背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 矩形数量
        self.rect_count = 5
        
        # 矩形大小和间距
        self.rect_width = 15
        self.rect_height = 15
        self.rect_spacing = 10
        
        # 主题蓝色
        self.base_color = QColor(53, 129, 252)  # 蓝色
        
        # 当前活动的矩形索引
        self.active_rect = 0
        
        # 颜色变化计时器
        self.timer = QTimer(self)
        self.timer.setInterval(200)  # 每200毫秒变化一次
        self.timer.timeout.connect(self.update_active_rect)
        
        # 初始状态为隐藏
        self.hide()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算矩形绘制的起始x坐标（居中对齐）
        total_width = self.rect_count * self.rect_width + (self.rect_count - 1) * self.rect_spacing
        start_x = (self.width() - total_width) // 2
        center_y = self.height() // 2
        
        # 绘制每个矩形
        for i in range(self.rect_count):
            if i == self.active_rect:
                # 活动矩形使用100%不透明度
                color = self.base_color
            else:
                # 其他矩形使用30%不透明度
                color = QColor(self.base_color)
                color.setAlpha(77)  # 约30%不透明度
                
            x = start_x + i * (self.rect_width + self.rect_spacing)
            y = center_y - self.rect_height // 2
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRect(x, y, self.rect_width, self.rect_height)
    
    def update_active_rect(self):
        """更新活动矩形索引"""
        self.active_rect = (self.active_rect + 1) % self.rect_count
        self.update()  # 触发重绘
    
    def start(self):
        """开始动画"""
        self.show()
        self.timer.start()
    
    def stop(self):
        """停止动画"""
        self.timer.stop()
        self.hide() 