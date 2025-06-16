from typing import Optional, Tuple
from enum import Enum
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QSizePolicy
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from radar_system.infrastructure.common.logging import ui_logger

class ScaleMode(Enum):
    """缩放模式枚举
    
    定义图像显示的不同缩放模式。
    
    Attributes:
        FIT: 适应窗口（保持比例）
        STRETCH: 拉伸填充（可能变形）
        FILL: 填充（可能裁剪）
        CENTER: 居中显示（原始大小）
    """
    FIT = 1
    STRETCH = 2
    FILL = 3
    CENTER = 4

class PlotWidget(QWidget):
    """绘图组件
    
    用于显示和管理图像的自定义组件，支持多种缩放模式和图像处理功能。
    
    Attributes:
        scale_mode (ScaleMode): 当前的缩放模式
        plot_layout (QVBoxLayout): 主布局管理器
        frame (QFrame): 框架
        figure (Figure): Matplotlib图形对象
        canvas (FigureCanvas): Matplotlib画布
        ax (Axes): Matplotlib子图
        current_image (ndarray): 当前显示的图像数据
    """
    
    def __init__(self, scale_mode: ScaleMode = ScaleMode.STRETCH):
        """初始化绘图组件
        
        Args:
            scale_mode: 初始缩放模式，默认为STRETCH
        """
        super().__init__()
        self.scale_mode = scale_mode
        
        # 创建布局
        self.plot_layout = QVBoxLayout(self)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_layout.setSpacing(0)
        
        # 创建框架
        self.frame = QFrame()
        
        # 创建框架的布局
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(1, 1, 1, 1)
        frame_layout.setSpacing(0)
        
        # 创建Figure和Canvas，设置紧凑布局
        self.figure = Figure(facecolor='white', constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame_layout.addWidget(self.canvas)
        
        # 添加框架到主布局
        self.plot_layout.addWidget(self.frame)
        
        # 添加子图并设置边距
        self.ax = self.figure.add_subplot(111)
        self.ax.set_position([0, 0, 1, 1])
        
        # 移除坐标轴
        self.ax.axis('off')
        
        # 存储当前图像
        self.current_image = None
        
        # 连接重绘事件
        self.canvas.mpl_connect('resize_event', self.on_resize)
    
    def set_scale_mode(self, mode: ScaleMode) -> None:
        """设置缩放模式
        
        Args:
            mode: 新的缩放模式
        """
        self.scale_mode = mode
        self._update_image()
        self.canvas.draw()
    
    def display_image(self, image_path: str) -> None:
        """显示图像
        
        Args:
            image_path: 图像文件路径
        """
        try:
            ui_logger.debug(f"尝试显示图像: {image_path}")
            self.ax.clear()
            
            # 读取图像并检查
            self.current_image = plt.imread(image_path)
            if self.current_image is None:
                ui_logger.warning(f"警告：无法读取图像: {image_path}")
                return
            
            # 确保图像是二维的（如果是RGB图像，转换为灰度）
            if len(self.current_image.shape) > 2:
                self.current_image = np.mean(self.current_image, axis=2)
            
            # 更新图像显示
            self._update_image()
            self.canvas.draw_idle()
            
        except Exception as e:
            ui_logger.error(f"显示图像出错: {str(e)}")
    
    def _calculate_image_position(self, ratio: float) -> Tuple[float, float]:
        """计算图像位置和尺寸
        
        Args:
            ratio: 缩放比例
        
        Returns:
            Tuple[float, float]: x和y方向的偏移量
        """
        if not isinstance(self.current_image, np.ndarray):
            return 0, 0
            
        canvas_width, canvas_height = self.canvas.get_width_height()
        
        try:
            img_height, img_width = self.current_image.shape[:2]
            
            # 计算新尺寸
            new_width = img_width * ratio
            new_height = img_height * ratio
            
            # 计算偏移量
            x_offset = (canvas_width - new_width) / 2 / canvas_width
            y_offset = (canvas_height - new_height) / 2 / canvas_height
            
            return x_offset, y_offset
            
        except (AttributeError, IndexError) as e:
            ui_logger.error(f"计算图像位置时出错: {e}")
            return 0, 0
    
    def _update_image(self) -> None:
        """根据不同缩放模式更新图像显示"""
        if self.current_image is None or not isinstance(self.current_image, np.ndarray):
            return
        
        try:
            # 清除当前图像
            self.ax.clear()
            
            if self.scale_mode == ScaleMode.STRETCH:
                # 获取画布和图像尺寸
                canvas_width, canvas_height = self.canvas.get_width_height()
                img_height, img_width = self.current_image.shape[:2]
                
                # 计算缩放比例
                scale_x = canvas_width / img_width
                scale_y = canvas_height / img_height
                
                # 创建目标网格
                y, x = np.mgrid[0:canvas_height, 0:canvas_width]
                
                # 计算源图像坐标（向量化操作）
                source_x = np.clip(np.round(x / scale_x).astype(np.int32), 0, img_width - 1)
                source_y = np.clip(np.round(y / scale_y).astype(np.int32), 0, img_height - 1)
                
                # 一次性完成映射（向量化操作）
                stretched_image = self.current_image[source_y, source_x]
                
                # 显示拉伸后的图像
                self.ax.imshow(stretched_image,
                              aspect='auto',
                              interpolation='nearest',
                              extent=[0, 1, 0, 1],
                              cmap='gray')
                self.ax.set_position([0, 0, 1, 1])
            else:
                # 获取画布和图像尺寸
                canvas_width, canvas_height = self.canvas.get_width_height()
                img_height, img_width = self.current_image.shape[:2]
                
                if self.scale_mode == ScaleMode.FIT:
                    # 适应窗口（保持比例）
                    width_ratio = canvas_width / img_width
                    height_ratio = canvas_height / img_height
                    ratio = min(width_ratio, height_ratio)
                    x_offset, y_offset = self._calculate_image_position(ratio)
                    
                elif self.scale_mode == ScaleMode.FILL:
                    # 填充（可能裁剪）
                    width_ratio = canvas_width / img_width
                    height_ratio = canvas_height / img_height
                    ratio = max(width_ratio, height_ratio)
                    x_offset, y_offset = self._calculate_image_position(ratio)
                    
                elif self.scale_mode == ScaleMode.CENTER:
                    # 居中显示（原始大小）
                    scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
                    x_offset, y_offset = self._calculate_image_position(scale)
                
                # 显示图像
                self.ax.imshow(self.current_image, 
                              extent=(x_offset, 1-x_offset, y_offset, 1-y_offset),
                              cmap='gray')
            
            self.ax.axis('off')
            self.canvas.draw()
            
        except Exception as e:
            ui_logger.error(f"更新图像显示出错: {str(e)}")
    
    def on_resize(self, event) -> None:
        """窗口大小改变时重新调整图像
        
        Args:
            event: 窗口大小改变事件
        """
        self._update_image()
        self.canvas.draw()
    
    def clear(self) -> None:
        """清除当前图像"""
        if hasattr(self, 'ax'):
            self.ax.clear()
            self.ax.axis('off')
            self.current_image = None
            self.canvas.draw_idle()
