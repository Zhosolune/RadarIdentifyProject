"""信号绘图服务

负责雷达信号数据的可视化处理，生成各维度（CF、PW、DOA、PA、DTOA）的二值化图像数据。
"""

from dataclasses import dataclass
import numpy as np
from typing import Dict, Optional

from radar_system.infrastructure.common.config import ConfigManager
from radar_system.infrastructure.common.logging import plotter_logger

@dataclass
class PlotConfig:
    """绘图配置
    
    Attributes:
        y_min (float): Y轴最小值
        y_max (float): Y轴最大值
        img_height (int): 图像高度
        img_width (int): 图像宽度
    """
    y_min: float
    y_max: float
    img_height: int
    img_width: int

class SignalPlotter:
    """信号绘图服务
    
    负责生成雷达信号数据的二值化图像。
    
    Attributes:
        configs (Dict[str, PlotConfig]): 各维度的绘图配置
    """
    
    def __init__(self):
        """初始化绘图服务"""
        self.config_manager = ConfigManager.get_instance()
        self.configs = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """从配置管理器加载绘图配置"""
        try:
            # 加载基础配置
            self.configs = self.config_manager.plotting.base_configs.copy()
            # 默认使用C波段配置
            for band_config in self.config_manager.plotting.band_configs:
                if band_config.name == "C波段":
                    self.configs['CF'] = band_config.plot_config
                    break
            plotter_logger.debug("绘图配置加载完成")
        except Exception as e:
            plotter_logger.error(f"加载绘图配置失败: {str(e)}")
            raise
    
    def update_band_config(self, band_name: str) -> None:
        """更新波段配置
        
        Args:
            band_name (str): 波段名称（'L波段', 'S波段', 'C波段', 'X波段'）
            
        Raises:
            ValueError: 当波段名称无效时
        """
        try:
            # 查找对应波段配置
            band_config = None
            for config in self.config_manager.plotting.band_configs:
                if config.name == band_name:
                    band_config = config
                    break
            
            if band_config is None:
                raise ValueError(f"无效的波段名称: {band_name}")
            
            # 更新配置
            self.configs = self.config_manager.plotting.base_configs.copy()
            self.configs['CF'] = band_config.plot_config
            
            plotter_logger.debug(f"波段配置已更新为: {band_name}")
            
        except Exception as e:
            plotter_logger.error(f"更新波段配置失败: {str(e)}")
            raise
    
    def _plot_dimension(self, data: np.ndarray, ydata: np.ndarray, 
                       xdata: np.ndarray, dim_name: str,
                       slice_start_time: float = None,
                       slice_end_time: float = None) -> np.ndarray:
        """生成单个维度的二值化图像
        
        Args:
            data (np.ndarray): 原始TOA数据
            ydata (np.ndarray): Y轴数据
            xdata (np.ndarray): X轴数据（通常是TOA）
            dim_name (str): 维度名称
            slice_start_time (float, optional): 切片起始时间
            slice_end_time (float, optional): 切片结束时间
            
        Returns:
            np.ndarray: 二值化图像数据数组
        """
        try:
            # 获取当前配置
            config = self.configs.get(dim_name)
            if not config:
                raise ValueError(f"未找到维度 {dim_name} 的配置")
            
            # 确保数据类型为 numpy array
            data = np.asarray(data, dtype=np.float64)
            ydata = np.asarray(ydata, dtype=np.float64)
            xdata = np.asarray(xdata, dtype=np.float64)
            
            # 使用切片时间范围作为X轴范围
            x_min = slice_start_time if slice_start_time is not None else np.min(data)
            x_max = slice_end_time if slice_end_time is not None else x_min + self.config_manager.data_processing.slice_length
            
            # 缩放Y轴数据并进行反转处理
            scaled_y = config.img_height - np.round(
                (ydata - config.y_min) / (config.y_max - config.y_min) * 
                (config.img_height - 1)
            ).astype(np.int32)
            
            # 缩放X轴数据
            scaled_x = np.round(
                (xdata - x_min) / (x_max - x_min) * 
                (config.img_width - 1)
            ).astype(np.int32) + 1
            
            # 创建图像
            binary_image = np.zeros((config.img_height, config.img_width), dtype=np.uint8)
            
            # 绘制点
            for i in range(len(scaled_x)):
                if 0 < scaled_x[i] <= config.img_width and 0 < scaled_y[i] <= config.img_height:
                    binary_image[scaled_y[i] - 1, scaled_x[i] - 1] = 1
            
            # 添加缩放结果检查的日志
            plotter_logger.debug(
                f"数据缩放检查 - 维度: {dim_name}, "
                f"原始数据范围: [{np.min(ydata):.2f}, {np.max(ydata):.2f}], "
                f"配置范围: [{config.y_min}, {config.y_max}], "
                f"缩放后范围: [{np.min(scaled_y)}, {np.max(scaled_y)}]"
            )
            
            return binary_image * 255
            
        except Exception as e:
            plotter_logger.error(f"生成{dim_name}维度图像失败: {str(e)}")
            raise
    
    def plot_slice(self, slice_data: np.ndarray) -> Dict[str, np.ndarray]:
        """生成切片的所有维度图像
        
        Args:
            slice_data (np.ndarray): 切片数据，形状为(n_samples, n_features)
            
        Returns:
            Dict[str, np.ndarray]: 图像数据字典，键为维度名称，值为二值化图像数组
        """
        try:
            toa = slice_data[:, 4]  # TOA数据
            
            # 计算DTOA
            dtoa = np.diff(toa) * 1000  # 转换为us
            dtoa = np.append(dtoa, 0)   # 补齐长度
            
            # 生成所有维度的图像
            image_data = {}
            dimensions = {
                'CF': slice_data[:, 0],
                'PW': slice_data[:, 1],
                'DOA': slice_data[:, 2],
                'PA': slice_data[:, 3],
                'DTOA': dtoa
            }
            
            for dim_name, data in dimensions.items():
                image_data[dim_name] = self._plot_dimension(
                    toa, data, toa,
                    dim_name, toa[0], toa[-1]
                )
            
            return image_data
            
        except Exception as e:
            plotter_logger.error(f"生成切片图像失败: {str(e)}")
            raise 