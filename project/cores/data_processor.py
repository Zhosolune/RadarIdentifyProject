import numpy as np
import pandas as pd
from pathlib import Path
from .log_manager import LogManager
from .plot_manager import SignalPlotter

class DataProcessor:
    """数据处理器
    
    负责雷达信号数据的加载、预处理和切片操作。
    
    Attributes:
        slice_length (int): 切片长度，单位为ms，默认250ms
        slice_dim (int): 切片维度，默认为4（TOA维度）
        data (Optional[NDArray]): 原始数据数组
        sliced_data (Optional[List[NDArray]]): 切片后的数据列表
        time_ranges (List[Tuple[float, float]]): 每个切片的时间范围列表
        plotter (SignalPlotter): 信号绘图器实例
        logger (LogManager): 日志管理器实例
    """
    
    def __init__(self):
        # 基础参数设置
        self.slice_length = 250  # 250ms
        self.slice_dim = 4      # TOA维度
        self.data = None
        self.sliced_data = None
        self.time_ranges = []
        self.plotter = SignalPlotter()
        self.logger = LogManager()
        
    def load_excel_file(self, file_path: str) -> tuple[bool, str, int, str]:
        """加载Excel文件并进行初始预处理
        
        读取Excel文件中的雷达信号数据，进行单位转换和数据清洗，
        并更新绘图配置。
        
        Args:
            file_path (str): Excel文件路径
            
        Returns:
            tuple[bool, str, int, str]: 
                - bool: 是否加载成功
                - str: 处理信息或错误信息
                - int: 预计切片数量
                - str: 信号波段信息
                
        Notes:
            数据格式要求：
            - CF (列1): 载频，单位MHz
            - PW (列2): 脉宽，单位us
            - DOA (列4): 到达角，单位度
            - PA (列5): 脉冲幅度，单位dB
            - TOA (列7): 到达时间，单位0.1us，将转换为ms
        """
        try:
            self.logger.info(f"开始加载Excel文件: {file_path}")
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            self.logger.debug(f"Excel文件读取成功，原始数据形状: {df.shape}")
            
            # 数据格式重排和单位转换
            data_tmp = df.values
            CF = data_tmp[:, 1]                 # MHz
            PW = data_tmp[:, 2]                 # us
            DOA = data_tmp[:, 4]                # 度
            PA = data_tmp[:, 5]                 # dB
            TOA = data_tmp[:, 7] / 1e4          # 转换为ms
            
            # 确保数据单位与预测要求一致
            self.data = np.column_stack((
                CF,     # MHz
                PW,     # us
                DOA,    # 度
                PA,     # dB
                TOA     # ms
            ))
            self.logger.debug(f"数据重排后形状: {self.data.shape}")
            
            # 剔除错误数据
            original_length = len(self.data)
            self.data = self.data[self.data[:,3] != 255]  # 剔除PA无效值
            filtered_length = len(self.data)
            self.logger.info(f"剔除无效PA值后，数据量从{original_length}减少到{filtered_length}")

            time_data = self.data[:, self.slice_dim]
            
            # 计算时间范围
            time_range = max(time_data) - min(time_data)
            slice_count = int(np.ceil(time_range / self.slice_length))
            self.logger.info(f"时间范围: {time_range:.2f}ms, 预计切片数量: {slice_count}")
            
            # 更新绘图配置并获取波段信息
            band = self.plotter.update_configs(self.data)
            self.logger.debug(f"初始配置更新完成，当前波段: {band}")
            
            return True, "数据加载成功", slice_count, band
            
        except Exception as e:
            self.logger.error(f"数据加载失败: {str(e)}")
            return False, f"数据加载失败: {str(e)}", 0, None
        
    def start_slice(self):
        """开始数据切片处理
        
        调用内部的_slice_data方法进行数据切片，并更新sliced_data属性。
        切片结果将存储在实例的sliced_data属性中。
        """
        self.logger.info("开始数据切片处理")
        self.sliced_data = self._slice_data()
        if self.sliced_data:
            self.logger.info(f"切片完成，共生成{len(self.sliced_data)}个切片")
        else:
            self.logger.warning("切片处理未生成有效数据")
    
    def _slice_data(self) -> list:
        """将数据按时间切片
        
        根据预设的slice_length对数据进行时间维度的切片，
        同时记录每个切片的时间范围。
        
        Returns:
            list: 切片后的数据列表，每个元素为一个numpy数组，
                 表示一个时间窗口内的数据点。
                 如果没有有效数据，返回空列表。
        
        Notes:
            - 切片基于TOA（到达时间）维度进行
            - 空切片会被跳过
            - 每个切片的时间范围会被记录在time_ranges属性中
        """
        if self.data is None:
            self.logger.warning("没有可用的数据进行切片")
            return []
            
        # 获取时间维度的数据
        time_data = self.data[:, self.slice_dim]
        
        # 计算时间范围
        time_min = np.min(time_data)
        time_max = np.max(time_data)
        
        # 计算切片边界
        slice_boundaries = np.arange(
            time_min, 
            time_max + self.slice_length, 
            self.slice_length
        )
        
        # 存储切片结果和时间范围
        sliced_data = []
        
        # 进行切片
        for i in range(len(slice_boundaries) - 1):
            start_time = slice_boundaries[i]
            end_time = slice_boundaries[i + 1]
            
            # 提取当前时间窗口内的数据
            mask = (time_data >= start_time) & (time_data < end_time)
            current_slice = self.data[mask]

            if len(current_slice) == 0:
                continue
                
            sliced_data.append(current_slice)

            start_toa = current_slice[0][self.slice_dim]
            end_toa = current_slice[-1][self.slice_dim]
            self.time_ranges.append((start_toa, end_toa))
        
        return sliced_data 