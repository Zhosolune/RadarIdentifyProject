import numpy as np
from PIL import Image
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import time

# from cores.data_processor import DataProcessor
from .log_manager import LogManager

@dataclass
class BandConfig:
    """波段配置"""
    name: str
    min_freq: float
    max_freq: float
    plot_config: 'PlotConfig'

@dataclass
class PlotConfig:
    """绘图配置"""
    y_min: float
    y_max: float
    img_height: int
    img_width: int

class SignalPlotter:
    """信号绘图管理器
    
    负责雷达信号数据的可视化处理，支持多个维度（CF、PW、DOA、PA、DTOA）的图像生成。
    
    Attributes:
        BASE_CONFIGS (Dict[str, PlotConfig]): 基础绘图配置，包含各维度的默认配置
        BAND_CONFIGS (List[BandConfig]): 不同频段的配置列表，包括L、S、C、X波段
        logger (LogManager): 日志管理器实例
        time_ranges (List): 时间范围列表
        temp_dir (str): 临时文件目录
        save_dir (str): 图像保存目录
        slice_length (int): 切片长度，默认250ms
        configs (Dict[str, PlotConfig]): 当前使用的绘图配置
    """
    
    # 基础配置
    BASE_CONFIGS = {
        'PA': PlotConfig(y_min=40, y_max=120, img_height=80, img_width=400),
        'DTOA': PlotConfig(y_min=0, y_max=3000, img_height=250, img_width=500),
        # 'DTOA': PlotConfig(y_min=0, y_max=4000, img_height=250, img_width=500),
        # 'PW': PlotConfig(y_min=0, y_max=200, img_height=200, img_width=400),
        'PW': PlotConfig(y_min=0, y_max=300, img_height=200, img_width=400),
        'DOA': PlotConfig(y_min=0, y_max=360, img_height=120, img_width=400)
    }
    
    # 波段配置
    BAND_CONFIGS = [
        BandConfig(
            name="L波段",
            min_freq=1000,
            max_freq=2000,
            plot_config=PlotConfig(y_min=1000, y_max=2000, img_height=400, img_width=400)
        ),
        BandConfig(
            name="S波段",
            min_freq=2000,
            max_freq=4000,
            plot_config=PlotConfig(y_min=2000, y_max=4000, img_height=400, img_width=400)
        ),
        BandConfig(
            name="C波段",
            min_freq=4000,
            max_freq=8000,
            plot_config=PlotConfig(y_min=4000, y_max=8000, img_height=400, img_width=400)
        ),
        BandConfig(
            name="X波段",
            min_freq=8000,
            max_freq=12000,
            plot_config=PlotConfig(y_min=8000, y_max=12000, img_height=400, img_width=400)
        )
    ]
    
    def __init__(self):
        """初始化绘图管理器"""
        self.logger = LogManager()
        self.time_ranges = []
        self.temp_dir = None
        self.save_dir = None
        self.slice_length = 250
        
        # 初始化默认配置
        self.configs = self.BASE_CONFIGS.copy()
        self.configs['CF'] = PlotConfig(y_min=4000, y_max=8000, img_height=400, img_width=400)  # 默认C波段
        
    def detect_frequency_band(self, data: np.ndarray) -> Optional[BandConfig]:
        """检测数据所属的频率波段
        
        使用多重判断标准检测波段，包括：
        1. 数据中位数
        2. 数据范围
        3. 数据集中度
        
        Args:
            data (np.ndarray): 输入数据，形状为(n_samples, n_features)
            
        Returns:
            Optional[BandConfig]: 检测到的波段配置，如果未检测到则返回None
            
        Notes:
            - 若数据中位数在某波段范围内，且大部分数据集中，则判定为该波段
            - 若数据范围在某波段内，则判定为该波段
            - 检测到波段后，会剔除超出波段范围的异常值
        """
        try:
            cf_data = data[:, 0]  # CF维度数据
            
            # 计算统计指标
            cf_median = np.median(cf_data)
            cf_min = np.min(cf_data)
            cf_max = np.max(cf_data)
            q1, q3 = np.percentile(cf_data, [25, 75])
            iqr = q3 - q1  # 四分位距
            
            self.logger.debug(f"CF数据统计: 中位数={cf_median:.2f}, 范围={cf_min:.2f}-{cf_max:.2f}, IQR={iqr:.2f}")
            
            # 遍历波段配置进行判断
            for band_config in self.BAND_CONFIGS:
                band_center = (band_config.max_freq + band_config.min_freq) / 2
                band_width = band_config.max_freq - band_config.min_freq
                
                # 判断条件：
                # 1. 中位数在波段范围内且数据相对集中
                # 2. 或者数据范围完全在波段内
                is_median_in_band = (band_config.min_freq <= cf_median <= band_config.max_freq)
                is_data_concentrated = iqr <= band_width * 0.5  # 数据集中度阈值可调
                is_range_in_band = (cf_min >= band_config.min_freq and 
                                  cf_max <= band_config.max_freq)
                
                if (is_median_in_band and is_data_concentrated) or is_range_in_band:
                    self.logger.info(f"检测到{band_config.name}: "
                                   f"{band_config.min_freq}-{band_config.max_freq} MHz")
                    
                    # 如果需要，剔除异常值
                    if not is_range_in_band:
                        valid_mask = ((cf_data >= band_config.min_freq) & 
                                    (cf_data <= band_config.max_freq))
                        data = data[valid_mask]
                        self.logger.info(f"已剔除 {np.sum(~valid_mask)} 个超出波段范围的数据点")
                    
                    return band_config
            
            self.logger.warning(f"未找到匹配的波段配置: "
                              f"中位数={cf_median:.2f}, 范围={cf_min:.2f}-{cf_max:.2f}")
            return None
            
        except Exception as e:
            self.logger.error(f"波段检测出错: {str(e)}")
            return None

    def update_configs(self, data: np.ndarray) -> str:
        """更新绘图配置
        
        根据输入数据检测波段并更新所有相关配置。
        这是配置更新的唯一入口点，应在数据加载时调用一次。
        
        Args:
            data (np.ndarray): 输入数据，形状为(n_samples, n_features)
            
        Returns:
            str: 检测到的波段名称，默认为'C波段'
        """
        try:
            # 确保配置字典已初始化
            if self.configs is None:
                self.configs = self.BASE_CONFIGS.copy()
            
            # 检测波段
            band_config = self.detect_frequency_band(data)
            if band_config:
                # 重置为基础配置
                self.configs = self.BASE_CONFIGS.copy()
                # 更新CF配置
                self.configs['CF'] = band_config.plot_config
                
                # X波段特殊配置
                if band_config.name == "X波段":
                    self.configs['PW'] = PlotConfig(
                        y_min=self.BASE_CONFIGS['PW'].y_min,
                        y_max=50,  # X波段特殊值
                        img_height=self.BASE_CONFIGS['PW'].img_height,
                        img_width=self.BASE_CONFIGS['PW'].img_width
                    )
                    self.configs['DTOA'] = PlotConfig(
                        y_min=self.BASE_CONFIGS['DTOA'].y_min,
                        y_max=100,  # X波段特殊值
                        img_height=self.BASE_CONFIGS['DTOA'].img_height,
                        img_width=self.BASE_CONFIGS['DTOA'].img_width
                    )
                
                self.logger.info(
                    f"已更新绘图配置为{band_config.name}, "
                    f"CF范围: {band_config.plot_config.y_min}-{band_config.plot_config.y_max}"
                )
                if band_config.name == "X波段":
                    self.logger.info(
                        f"X波段特殊配置 - PW范围: [0-20], DTOA范围: [0-300]"
                    )
                return band_config.name
            else:
                # 使用默认C波段配置
                self.configs = self.BASE_CONFIGS.copy()
                self.configs['CF'] = PlotConfig(y_min=4000, y_max=8000, 
                                              img_height=400, img_width=400)
                self.logger.warning("使用默认C波段配置")
                return 'C波段'
                
        except Exception as e:
            self.logger.error(f"更新配置出错: {str(e)}")
            return 'C波段'
    
    def set_temp_dir(self, temp_dir: str):
        """设置临时文件目录
        
        Args:
            temp_dir (str): 临时文件目录路径
            
        Notes:
            如果目录不存在，会自动创建
        """
        self.temp_dir = temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            self.logger.debug(f"创建临时目录: {temp_dir}")
            
    def set_save_dir(self, save_dir: str):
        """设置图像保存目录
        
        Args:
            save_dir (str): 图像保存目录路径
            
        Notes:
            如果目录不存在，会自动创建
        """
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            self.logger.debug(f"创建保存目录: {save_dir}")
    
    def plot_cluster(self, cluster_data: dict, for_predict: bool = False) -> Dict[str, str]:
        """绘制聚类结果的所有维度图像
        
        Args:
            cluster_data (dict): 聚类数据字典，包含：
                - points: 数据点数组
                - time_ranges: 时间范围元组 (start_time, end_time)
                - slice_idx: 切片索引
                - dim_name: 维度名称
                - cluster_idx: 聚类编号
            for_predict (bool): 是否用于预测，默认False
            
        Returns:
            Dict[str, str]: 图像路径字典，键为维度名称，值为图像文件路径
            
        Notes:
            - 预测模式下只生成PA和DTOA维度的图像
            - 非预测模式下生成所有维度(CF,PW,DOA,PA,DTOA)的图像
            - 图像保存在临时目录或保存目录中
        """
        try:
            points = cluster_data['points']
            toa = points[:, 4]  # TOA数据
            
            # 获取当前切片的时间范围
            slice_start_time, slice_end_time = cluster_data.get('time_ranges', (0, 0))
            # self.logger.debug(f"当前切片时间范围: {slice_start_time:.2f} - {slice_end_time:.2f}")
            
            # 计算所需数据
            dtoa = np.diff(toa) * 1000  # 转换为us
            # dtoa = np.append(dtoa, 0)   # 补齐长度
            dtoa = np.append(dtoa, dtoa[-1])   # 补齐长度，用原dtoa序列最后一个值补全，避免绘图时0值影响模型识别
            # 调试用
            # if cluster_data.get('slice_idx', 0) == 3 and cluster_data.get('cluster_idx', 0) == 4 and cluster_data.get('dim_name', '?') == 'CF':
            #     print(dtoa)
            
            # 确定目标目录
            target_dir = self.temp_dir if for_predict else self.save_dir
            if not target_dir:
                self.logger.error("未设置目录")
                raise ValueError("未设置目录")
                
            # 生成基础文件名
            base_name = (f"temp_{np.random.randint(10000)}" if for_predict else 
                        f"slice{cluster_data.get('slice_idx', 0)}_"
                        f"{cluster_data.get('dim_name', '?')}_"
                        f"cluster{cluster_data.get('cluster_idx', 0)}")
            # self.logger.debug(f"开始绘制图像, 基础文件名: {base_name}")

            
            # 绘制并保存所有图像
            image_paths = {}
            
            # PA-TOA图
            image_paths['PA'] = self._plot_dimension(
                toa, points[:, 3], toa,  # PA数据
                'PA', base_name, target_dir,
                slice_start_time, slice_end_time
            )
            
            # DTOA-TOA图
            image_paths['DTOA'] = self._plot_dimension(
                toa, dtoa, toa,  # DTOA数据
                'DTOA', base_name, target_dir,
                slice_start_time, slice_end_time
            )
            
            # 预留其他维度的绘制
            if not for_predict:
                # CF-TOA图
                image_paths['CF'] = self._plot_dimension(
                    toa, points[:, 0], toa,  # CF数据
                    'CF', base_name, target_dir,
                    slice_start_time, slice_end_time
                )
                
                # PW-TOA图
                image_paths['PW'] = self._plot_dimension(
                    toa, points[:, 1], toa,  # PW数据
                    'PW', base_name, target_dir,
                    slice_start_time, slice_end_time
                )
                
                # DOA-TOA图
                image_paths['DOA'] = self._plot_dimension(
                    toa, points[:, 2], toa,  # DOA数据
                    'DOA', base_name, target_dir,
                    slice_start_time, slice_end_time
                )
            
            return image_paths
            
        except Exception as e:
            self.logger.error(f"绘制聚类图像出错: {str(e)}")
            return {}
    
    def _plot_dimension(self, data: np.ndarray, ydata: np.ndarray, 
                       xdata: np.ndarray, dim_name: str, 
                       base_name: str, save_dir: str,
                       slice_start_time: float = None,
                       slice_end_time: float = None) -> str:
        """绘制单个维度的二值化图像
        
        Args:
            data (np.ndarray): 原始TOA数据
            ydata (np.ndarray): Y轴数据
            xdata (np.ndarray): X轴数据（通常是TOA）
            dim_name (str): 维度名称
            base_name (str): 基础文件名
            save_dir (str): 保存目录
            slice_start_time (float, optional): 切片起始时间
            slice_end_time (float, optional): 切片结束时间
            
        Returns:
            str: 保存的图像文件路径，失败时返回空字符串
        """
        try:
            # 获取当前配置
            config = self.configs.get(dim_name)
            if not config:
                self.logger.error(f"未找到维度 {dim_name} 的配置")
                return ""
            
            # 确保数据类型为 numpy array
            data = np.asarray(data, dtype=np.float64)
            ydata = np.asarray(ydata, dtype=np.float64)
            xdata = np.asarray(xdata, dtype=np.float64)
            
            # 使用切片时间范围作为X轴范围
            x_min = slice_start_time if slice_start_time is not None else np.min(data)
            x_max = slice_end_time if slice_end_time is not None else x_min + 250
            
            # DTOA图像范围处理
            if dim_name == 'DTOA':
                count = 0
                # 判断在3000~4000之间有多少数据
                count = np.sum((ydata >= 3000) & (ydata <= 4000))
                if count > min(10, 0.2 * len(ydata)):
                    config.y_max = 4000
                    self.logger.debug(f"DTOA数据在3000~4000之间有{count}个，将图像范围设为0~4000")
                else:
                    config.y_max = 3000

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
            binary_image = np.zeros((config.img_height, config.img_width), dtype=int)
            
            # 绘制点
            valid_points = 0
            for i in range(len(scaled_x)):
                if 0 < scaled_x[i] <= config.img_width and 0 < scaled_y[i] <= config.img_height:
                    binary_image[scaled_y[i] - 1, scaled_x[i] - 1] = 1
                    valid_points += 1
            
            # 保存图像
            filename = os.path.join(save_dir, f"{base_name}_{dim_name.lower()}.png")
            Image.fromarray(binary_image.astype(np.uint8) * 255).save(filename)
            
            return filename
            
        except Exception as e:
            self.logger.error(f"绘制{dim_name}维度图像出错: {str(e)}")
            return ""
    
    def plot_slice(self, slice_data: np.ndarray, base_name: str) -> Dict[str, str]:
        """生成切片的所有维度图像
        
        Args:
            slice_data (np.ndarray): 切片数据，形状为(n_samples, n_features)
            base_name (str): 基础文件名
            
        Returns:
            Dict[str, str]: 图像路径字典，键为维度名称，值为图像文件路径
            
        Notes:
            - 生成5个维度的图像：CF、PW、DOA、PA、DTOA
            - DTOA通过计算相邻TOA的差值获得
            - 所有图像保存在save_dir目录下
        """
        try:
            self.logger.debug(f"开始绘制切片图像: {base_name}")
            
            toa = slice_data[:, 4]  # TOA数据
            
            # 计算DTOA
            dtoa = np.diff(toa) * 1000  # 转换为us
            dtoa = np.append(dtoa, 0)   # 补齐长度
            
            # 绘制并保存所有图像
            image_paths = {}
            
            # 绘制所有维度的图像
            dimensions = {
                'CF': (slice_data[:, 0], 'CF'),
                'PW': (slice_data[:, 1], 'PW'),
                'DOA': (slice_data[:, 2], 'DOA'),
                'PA': (slice_data[:, 3], 'PA'),
                'DTOA': (dtoa, 'DTOA')
            }
            
            for dim_name, (data, label) in dimensions.items():
                image_paths[dim_name] = self._plot_dimension(
                    toa, data, toa,
                    dim_name, base_name, self.save_dir,
                    toa[0], toa[-1]
                )
            return image_paths
            
        except Exception as e:
            self.logger.error(f"绘制切片图像出错: {str(e)}")
            return {}