"""
配置管理模块

本模块负责系统配置的加载、验证和访问，提供统一的配置管理机制。
"""
import os
import json
from typing import Any, Dict, Optional, List
from .exceptions import ConfigError
from dataclasses import dataclass
from pathlib import Path
from .logging import system_logger
import multiprocessing as mp

@dataclass
class PlotConfig:
    """绘图配置类
    
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

@dataclass
class BandConfig:
    """波段配置类
    
    Attributes:
        name (str): 波段名称
        min_freq (float): 最小频率
        max_freq (float): 最大频率
        plot_config (PlotConfig): 绘图配置
    """
    name: str
    min_freq: float
    max_freq: float
    plot_config: PlotConfig

@dataclass
class PlottingConfig:
    """绘图系统配置类
    
    Attributes:
        base_configs (Dict[str, PlotConfig]): 基础绘图配置
        band_configs (List[BandConfig]): 波段配置列表
        temp_dir (Optional[str]): 临时文件目录
        save_dir (Optional[str]): 图像保存目录
    """
    base_configs: Dict[str, PlotConfig] = None
    band_configs: List[BandConfig] = None
    temp_dir: Optional[str] = None
    save_dir: Optional[str] = None
    
    def __post_init__(self):
        if self.base_configs is None:
            self.base_configs = {
                'PA': PlotConfig(y_min=40, y_max=120, img_height=80, img_width=400),
                'DTOA': PlotConfig(y_min=0, y_max=3000, img_height=250, img_width=500),
                'PW': PlotConfig(y_min=0, y_max=200, img_height=200, img_width=400),
                'DOA': PlotConfig(y_min=0, y_max=360, img_height=120, img_width=400)
            }
        if self.band_configs is None:
            self.band_configs = [
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
        
        # 设置默认目录
        if self.temp_dir is None:
            self.temp_dir = "temp"
        if self.save_dir is None:
            self.save_dir = "result"

    def to_dict(self) -> Dict:
        """将配置转换为字典格式"""
        return {
            "base_configs": {
                name: {
                    "y_min": cfg.y_min,
                    "y_max": cfg.y_max,
                    "img_height": cfg.img_height,
                    "img_width": cfg.img_width
                }
                for name, cfg in self.base_configs.items()
            },
            "band_configs": [
                {
                    "name": cfg.name,
                    "min_freq": cfg.min_freq,
                    "max_freq": cfg.max_freq,
                    "plot_config": {
                        "y_min": cfg.plot_config.y_min,
                        "y_max": cfg.plot_config.y_max,
                        "img_height": cfg.plot_config.img_height,
                        "img_width": cfg.plot_config.img_width
                    }
                }
                for cfg in self.band_configs
            ],
            "temp_dir": self.temp_dir,
            "save_dir": self.save_dir
        }
    
    def from_dict(self, data: Dict) -> None:
        """从字典加载配置"""
        # 加载基础绘图配置
        if "base_configs" in data:
            self.base_configs = {
                name: PlotConfig(**cfg)
                for name, cfg in data["base_configs"].items()
            }
        
        # 加载波段配置
        if "band_configs" in data:
            self.band_configs = []
            for band_cfg in data["band_configs"]:
                plot_cfg = PlotConfig(**band_cfg["plot_config"])
                band_cfg["plot_config"] = plot_cfg
                self.band_configs.append(BandConfig(**band_cfg))
        
        # 加载目录配置
        self.temp_dir = data.get("temp_dir")
        self.save_dir = data.get("save_dir")
        
        # 如果没有配置，使用默认值
        if not self.base_configs or not self.band_configs:
            self.__post_init__()

@dataclass
class DataProcessingConfig:
    """数据处理配置类
    
    Attributes:
        slice_length (int): 切片长度，单位ms
        slice_dim (int): 切片维度，用于TOA
        data_columns (Dict[str, int]): 数据列映射配置
        data_units (Dict[str, str]): 数据单位配置
        excel_has_header (bool): Excel文件是否包含表头
        excel_chunk_size (int): Excel文件分块读取时的块大小
        cpu_load (float): 并行处理时的CPU负载百分比（0.0-1.0），默认0.5表示50%负载
        use_parallel_reading (bool): 是否使用并行读取策略，默认False使用简单高效的读取策略
    """
    slice_length: int = 250
    slice_dim: int = 4
    data_columns: Dict[str, int] = None
    data_units: Dict[str, str] = None
    excel_has_header: bool = False  # 默认Excel文件不包含表头
    excel_chunk_size: int = 40000  # 默认分块大小
    cpu_load: float = 0.5  # 默认使用50%的CPU负载
    use_parallel_reading: bool = False  # 默认使用简单高效的读取策略
    
    def __post_init__(self):
        # 验证CPU负载百分比的范围
        if not 0.0 <= self.cpu_load <= 1.0:
            system_logger.warning(f"CPU负载百分比 {self.cpu_load} 超出范围[0.0-1.0]，将使用默认值0.5")
            self.cpu_load = 0.5
            
        if self.data_columns is None:
            self.data_columns = {
                'CF': 1,    # MHz，载频
                'PW': 2,    # us，脉宽
                'DOA': 4,   # 度，到达角
                'PA': 5,    # dB，脉冲幅度
                'TOA': 7    # 0.1us，到达时间
            }
        if self.data_units is None:
            self.data_units = {
                'CF': 'MHz',
                'PW': 'us',
                'DOA': 'deg',
                'PA': 'dB',
                'TOA': '0.1us'
            }
    
    def to_dict(self) -> Dict:
        """将配置转换为字典格式"""
        return {
            "slice_length": self.slice_length,
            "slice_dim": self.slice_dim,
            "data_columns": self.data_columns,
            "data_units": self.data_units,
            "excel_has_header": self.excel_has_header,
            "excel_chunk_size": self.excel_chunk_size,
            "cpu_load": self.cpu_load,
            "use_parallel_reading": self.use_parallel_reading
        }
    
    def from_dict(self, data: Dict) -> None:
        """从字典加载配置"""
        self.slice_length = data.get("slice_length", 250)
        self.slice_dim = data.get("slice_dim", 4)
        self.data_columns = data.get("data_columns", None)
        self.data_units = data.get("data_units", None)
        self.excel_has_header = data.get("excel_has_header", False)
        self.excel_chunk_size = data.get("excel_chunk_size", 40000)
        self.cpu_load = data.get("cpu_load", 0.5)
        self.use_parallel_reading = data.get("use_parallel_reading", False)
        self.__post_init__()

    def get_max_processes(self) -> int:
        """计算基于CPU负载的最大进程数
        
        Returns:
            int: 最大进程数
        """
        available_cores = mp.cpu_count() - 1  # 保留一个核心给系统
        max_processes = max(1, int(available_cores * self.cpu_load))
        system_logger.debug(
            f"CPU核心数: {mp.cpu_count()}, "
            f"负载率: {self.cpu_load:.1%}, "
            f"最大进程数: {max_processes}"
        )
        return max_processes

@dataclass
class ClusterConfig:
    """聚类配置类
    
    Attributes:
        min_cluster_size (int): 最小聚类大小
        epsilon_cf (float): CF维度邻域半径
        epsilon_pw (float): PW维度邻域半径
        min_pts (int): 最小点数
        pa_weight (float): PA特征权重
        dtoa_weight (float): DTOA特征权重
        threshold (float): 识别阈值
    """
    min_cluster_size: int = 8
    epsilon_cf: float = 2.0
    epsilon_pw: float = 0.2
    min_pts: int = 1
    pa_weight: float = 0.5
    dtoa_weight: float = 0.5
    threshold: float = 0.8
    
    def to_dict(self) -> Dict:
        """将配置转换为字典格式"""
        return {
            "min_cluster_size": self.min_cluster_size,
            "epsilon_cf": self.epsilon_cf,
            "epsilon_pw": self.epsilon_pw,
            "min_pts": self.min_pts,
            "pa_weight": self.pa_weight,
            "dtoa_weight": self.dtoa_weight,
            "threshold": self.threshold
        }
    
    def from_dict(self, data: Dict) -> None:
        """从字典加载配置"""
        self.min_cluster_size = data.get("min_cluster_size", 8)
        self.epsilon_cf = data.get("epsilon_cf", 2.0)
        self.epsilon_pw = data.get("epsilon_pw", 0.2)
        self.min_pts = data.get("min_pts", 1)
        self.pa_weight = data.get("pa_weight", 0.5)
        self.dtoa_weight = data.get("dtoa_weight", 0.5)
        self.threshold = data.get("threshold", 0.8)

@dataclass
class UIConfig:
    """UI配置类
    
    用于存储UI相关的配置信息，如窗口位置、大小等。
    
    Attributes:
        window_x (Optional[int]): 窗口X坐标
        window_y (Optional[int]): 窗口Y坐标
        window_width (Optional[int]): 窗口宽度
        window_height (Optional[int]): 窗口高度
        last_import_dir (Optional[str]): 上次导入文件的目录
        remember_window_position (bool): 是否记住窗口位置
    """
    window_x: Optional[int] = 1200
    window_y: Optional[int] = 800
    window_width: Optional[int] = None
    window_height: Optional[int] = None
    last_import_dir: Optional[str] = None
    remember_window_position: bool = False  # 默认不记住窗口位置
    
    def to_dict(self) -> Dict:
        """将配置转换为字典格式
        
        Returns:
            Dict: 配置字典
        """
        return {
            "window_x": self.window_x,
            "window_y": self.window_y,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "last_import_dir": self.last_import_dir,
            "remember_window_position": self.remember_window_position
        }
        
    def from_dict(self, data: Dict) -> None:
        """从字典加载配置
        
        Args:
            data: 配置字典
        """
        self.window_x = data.get("window_x")
        self.window_y = data.get("window_y")
        self.window_width = data.get("window_width")
        self.window_height = data.get("window_height")
        self.last_import_dir = data.get("last_import_dir")
        self.remember_window_position = data.get("remember_window_position", False)

class ConfigManager:
    """配置管理器
    
    负责加载、验证和管理系统配置。
    使用单例模式确保整个应用程序只有一个配置实例。
    
    Attributes:
        _instance (Optional[ConfigManager]): 单例实例
        _initialized (bool): 是否已初始化
        _config_path (Path): 配置文件路径
        data_processing (DataProcessingConfig): 数据处理配置
        clustering (ClusterConfig): 聚类配置
        plotting (PlottingConfig): 绘图配置
        ui (UIConfig): UI配置
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, config_path: Optional[str] = None):
        """创建或获取单例实例
        
        Args:
            config_path: 配置文件路径，仅在首次创建实例时使用
            
        Returns:
            ConfigManager: 配置管理器实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，仅在首次初始化时使用
            
        Notes:
            由于是单例模式，__init__可能被多次调用，但只有首次调用会真正初始化
        """
        # 避免重复初始化
        if self._initialized:
            return
            
        self._config_path = Path(config_path) if config_path else None
        
        # 获取项目根目录
        if self._config_path:
            self.project_root = self._config_path.parent.parent
        else:
            self.project_root = Path(__file__).parent.parent.parent.parent
        
        # 初始化配置对象
        self.data_processing = DataProcessingConfig()
        self.clustering = ClusterConfig()
        self.plotting = PlottingConfig()
        self.ui = UIConfig()
        
        # 确保目录存在
        self._ensure_directories()
        
        if self._config_path:
            try:
                self.load_config()
                system_logger.info(f"成功从 {self._config_path} 加载配置")
            except ConfigError as e:
                system_logger.warning(f"加载配置文件失败: {str(e)}，将使用默认配置")
        else:
            system_logger.info("未指定配置文件路径，使用默认配置")
            
        self._initialized = True
    
    def _ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        try:
            # 确保临时目录存在
            temp_dir = self.project_root / self.plotting.temp_dir
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.plotting.temp_dir = str(temp_dir)
            
            # 确保保存目录存在
            save_dir = self.project_root / self.plotting.save_dir
            save_dir.mkdir(parents=True, exist_ok=True)
            self.plotting.save_dir = str(save_dir)
            
            system_logger.info(
                f"目录创建完成:\n"
                f"临时目录: {self.plotting.temp_dir}\n"
                f"保存目录: {self.plotting.save_dir}"
            )
            
        except Exception as e:
            error_msg = f"创建目录失败: {str(e)}"
            system_logger.error(error_msg)
            raise ConfigError(error_msg) from e
    
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """获取配置管理器实例
        
        Returns:
            ConfigManager: 配置管理器实例
            
        Raises:
            ConfigError: 如果实例未初始化
        """
        if cls._instance is None:
            raise ConfigError("配置管理器未初始化")
        return cls._instance
    
    @classmethod
    def initialize(cls, config_path: str) -> 'ConfigManager':
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            ConfigManager: 配置管理器实例
        """
        return cls(config_path)
    
    def load_config(self) -> None:
        """从文件加载配置
        
        如果配置文件路径为None，则使用默认配置。
        
        Raises:
            ConfigError: 配置文件格式错误时抛出
        """
        if not self._config_path:
            system_logger.info("配置文件路径为None，使用默认配置")
            return
            
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 加载数据处理配置
            if 'data_processing' in config_data:
                self.data_processing.from_dict(config_data['data_processing'])
                system_logger.debug("已加载数据处理配置")
            
            # 加载聚类配置
            if 'clustering' in config_data:
                self.clustering.from_dict(config_data['clustering'])
                system_logger.debug("已加载聚类配置")
            
            # 加载绘图配置
            if 'plotting' in config_data:
                self.plotting.from_dict(config_data['plotting'])
                system_logger.debug("已加载绘图配置")
                
            # 加载UI配置
            if 'ui' in config_data:
                self.ui.from_dict(config_data['ui'])
                system_logger.debug("已加载UI配置")
                
        except FileNotFoundError:
            system_logger.warning(f"配置文件不存在: {self._config_path}，将使用默认配置")
            self.save_config()  # 保存默认配置
        except json.JSONDecodeError as e:
            error_msg = f"配置文件格式错误: {str(e)}"
            system_logger.error(error_msg)
            raise ConfigError(error_msg) from e
        except Exception as e:
            error_msg = f"加载配置文件失败: {str(e)}"
            system_logger.error(error_msg)
            raise ConfigError(error_msg) from e
    
    def save_config(self) -> None:
        """保存配置到文件
        
        如果配置文件路径为None，则不执行保存操作。
        
        Raises:
            ConfigError: 保存配置文件失败时抛出
        """
        if not self._config_path:
            system_logger.info("配置文件路径为None，跳过保存")
            return
            
        try:
            # 构建配置数据
            config_data = {
                "data_processing": self.data_processing.to_dict(),
                "clustering": self.clustering.to_dict(),
                "plotting": self.plotting.to_dict(),
                "ui": self.ui.to_dict()
            }
            
            # 保存配置
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
                
            system_logger.info(f"配置已保存到: {self._config_path}")
            
        except Exception as e:
            error_msg = f"保存配置文件失败: {str(e)}"
            system_logger.error(error_msg)
            raise ConfigError(error_msg) from e
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            Dict[str, Any]: 当前配置的字典表示
        """
        # 转换绘图配置为可序列化格式
        plot_config = {
            'base_configs': {
                key: vars(cfg) for key, cfg in self.plotting.base_configs.items()
            },
            'band_configs': [
                {
                    'name': band.name,
                    'min_freq': band.min_freq,
                    'max_freq': band.max_freq,
                    'plot_config': vars(band.plot_config)
                }
                for band in self.plotting.band_configs
            ],
            'temp_dir': self.plotting.temp_dir,
            'save_dir': self.plotting.save_dir
        }
        
        config = {
            'data_processing': {
                'slice_length': self.data_processing.slice_length,
                'slice_dim': self.data_processing.slice_dim,
                'data_columns': self.data_processing.data_columns,
                'data_units': self.data_processing.data_units,
                'excel_has_header': self.data_processing.excel_has_header,
                'excel_chunk_size': self.data_processing.excel_chunk_size,
                'cpu_load': self.data_processing.cpu_load
            },
            'clustering': {
                'min_cluster_size': self.clustering.min_cluster_size,
                'epsilon_cf': self.clustering.epsilon_cf,
                'epsilon_pw': self.clustering.epsilon_pw,
                'min_pts': self.clustering.min_pts,
                'pa_weight': self.clustering.pa_weight,
                'dtoa_weight': self.clustering.dtoa_weight,
                'threshold': self.clustering.threshold
            },
            'plotting': plot_config,
            'ui': {
                'window_x': self.ui.window_x,
                'window_y': self.ui.window_y,
                'window_width': self.ui.window_width,
                'window_height': self.ui.window_height,
                'last_import_dir': self.ui.last_import_dir,
                'remember_window_position': self.ui.remember_window_position
            }
        }
        
        return config
