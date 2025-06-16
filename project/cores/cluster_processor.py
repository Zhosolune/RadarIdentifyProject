import numpy as np
from typing import Optional, List, Tuple, Dict
from numpy.typing import NDArray
from .roughly_clustering import RoughClusterer
from .log_manager import LogManager
from .params_extractor import ParamsExtractor

class ClusterProcessor:
    """聚类处理类
    
    负责对雷达信号数据进行多维度聚类处理，包括CF维度和PW维度的聚类分析。
    
    Attributes:
        DIM_NAMES (List[str]): 维度名称列表 ['CF', 'PW']
        MIN_CLUSTER_SIZE (int): 最小聚类大小，默认为5
        sliced_data (Optional[NDArray]): 切片后的数据
        current_slice_idx (int): 当前切片索引
        current_dim (int): 当前处理维度（0:CF, 1:PW）
        epsilon_CF (float): CF维度邻域半径
        epsilon_PW (float): PW维度邻域半径
        min_pts (int): 最小点数
        points (Optional[NDArray]): 当前处理的数据点
        processed_points (set): 已处理的数据点索引集合
        time_ranges (List): 时间范围列表
        current_band (str): 当前波段标识
    """
    
    DIM_NAMES = ['CF', 'PW']  # 维度名称

    def __init__(self):
        # 数据相关
        self.sliced_data = None  # 切片后的数据
        self.current_slice_idx = 0  # 当前切片索引
        self.current_dim = 0  # 当前处理维度（0:CF, 1:PW）
        # self.current_cluster_results = []  # 当前切片的聚类结果
        
        # 聚类参数
        self.epsilon_CF = 2.0  # CF维度邻域半径
        self.epsilon_PW = 0.2  # PW维度邻域半径
        self.min_pts = 1  # 最小点数
        
        # 数据点
        self.points = None  # 当前处理的数据点
        self.processed_points = set()  # 已处理的数据点索引
        
        # 日志管理器
        self.logger = LogManager()
        # 参数提取器
        self.params_extractor = ParamsExtractor()
        
        self.time_ranges = []  # 添加时间范围属性
        
        self.current_band = None  # 添加波段标识
        
        self.slice_time_ranges = []  # 存储从DataProcessor获取的时间范围

        self.MIN_CLUSTER_SIZE = 8  # 最小聚类大小

        self.CF_CLUSTER_COUNT = 0  # 记录CF维度聚类结果数量
    
    def set_cluster_params(self, epsilon_CF: float, epsilon_PW: float, min_pts: int):
        """设置聚类参数
        
        Args:
            epsilon_CF (float): CF维度的邻域半径
            epsilon_PW (float): PW维度的邻域半径
            min_pts (int): 最小点数阈值
        """
        self.epsilon_CF = epsilon_CF
        self.epsilon_PW = epsilon_PW
        self.min_pts = min_pts

    def set_identify_params(self, pa_weight: float, dtoa_weight: float, threshold: float):
        """设置识别参数
        
        Args:
            pa_weight (float): PA特征权重
            dtoa_weight (float): DTOA特征权重
            threshold (float): 识别阈值
        """
        self.pa_weight = pa_weight
        self.dtoa_weight = dtoa_weight
        self.threshold = threshold
    
    def set_data(self, sliced_data: List[NDArray], sliced_data_idx: int):
        """设置切片数据
        
        Args:
            sliced_data (List[NDArray]): 当前切片的数据点列表
            sliced_data_idx (int): 切片索引
        """
        if isinstance(sliced_data, np.ndarray):
            self.sliced_data = sliced_data
        else:
            self.sliced_data = np.array(sliced_data)
        self.current_slice_idx = sliced_data_idx
        self.current_dim = 0
        self.processed_points = set()

    def _cluster_cf_dimension(self) -> List[Dict]:
        """CF维度聚类
        
        Returns:
            List[Dict]: 聚类结果列表，每个字典包含聚类的详细信息：
                - points: 数据点
                - points_indices: 数据点索引
                - cluster_size: 聚类大小
                - cluster_idx: 聚类编号
                - dim_name: 维度名称
                - slice_idx: 切片索引
                - time_ranges: 时间范围
        """
        try:
            # 创建聚类器
            clusterer = RoughClusterer(self.epsilon_CF, self.min_pts)
            
            # 进行聚类
            # labels = clusterer.fit(self.points, 0)  # CF维度
            labels = clusterer.fit_dbscan(self.points, 0)  # CF维度
            
            # 处理聚类结果
            clusters = []
            unique_labels = np.unique(labels)
            
            for label in unique_labels:
                if label == -1:  # 跳过噪声点
                    continue
                    
                # 获取当前类别的点索引
                mask = (labels == label)
                cluster_points = self.points[mask]

                dtoa = np.diff(cluster_points[:, 4], prepend=0) * 1000  # 转换为us
                dtoa = np.append(dtoa, 0)  # 补齐长度
                is_valid_dtoa = self.params_extractor.extract_grouped_values(dtoa, eps=0.2, min_samples=4, threshold_ratio=0.1)
                
                # 检查聚类大小与PRI有效性
                if len(cluster_points) <= self.MIN_CLUSTER_SIZE and not is_valid_dtoa:
                    continue
                else:
                    # 记录已处理的点
                    points_indices = np.where(mask)[0]
                    self.processed_points.update(points_indices)
                    
                    # 创建聚类结果字典
                    cluster_info = {
                        'points': cluster_points,
                        'points_indices': points_indices,
                        'cluster_size': len(cluster_points),
                        'cluster_idx': len(clusters) + 1,
                        'dim_name': 'CF',
                        'slice_idx': self.current_slice_idx + 1,
                        'time_ranges': self.time_ranges
                    }
                    clusters.append(cluster_info)
                    self.logger.info(f"切片{cluster_info['slice_idx']}{cluster_info['dim_name']}维类别{cluster_info['cluster_idx']} - 点数: {cluster_info['cluster_size']}")
            
            self.CF_CLUSTER_COUNT = len(clusters)

            return clusters
            
        except Exception as e:
            self.logger.error(f"CF维度聚类出错: {str(e)}")
            return []

    def _cluster_pw_dimension(self) -> List[Dict]:
        """PW维度聚类
        
        Returns:
            List[Dict]: 聚类结果列表，每个字典包含聚类的详细信息：
                - points: 聚类中的数据点
                - points_indices: 数据点索引
                - cluster_size: 聚类大小
                - cluster_idx: 聚类编号
                - dim_name: 维度名称
                - slice_idx: 切片索引
                - time_ranges: 时间范围
        """
        try:
            # 创建聚类器
            clusterer = RoughClusterer(self.epsilon_PW, self.min_pts)
            
            # 进行聚类
            # labels = clusterer.fit(self.points, 1)  # PW维度
            labels = clusterer.fit_dbscan(self.points, 1)  # PW维度
            
            # 处理聚类结果
            clusters = []
            unique_labels = np.unique(labels)
            
            for label in unique_labels:
                if label == -1:  # 跳过噪声点
                    continue
                    
                # 获取当前类别的点索引
                mask = (labels == label)
                cluster_points = self.points[mask]

                dtoa = np.diff(cluster_points[:, 4], prepend=0) * 1000  # 转换为us
                dtoa = np.append(dtoa, 0)  # 补齐长度
                is_valid_dtoa = self.params_extractor.extract_grouped_values(dtoa, eps=0.2, min_samples=4, threshold_ratio=0.1)

                # 检查聚类大小与PRI有效性
                if len(cluster_points) <= self.MIN_CLUSTER_SIZE and not is_valid_dtoa:
                    continue
                else:
                    # 记录已处理的点
                    points_indices = np.where(mask)[0]
                    self.processed_points.update(points_indices)
                    
                    # 创建聚类结果字典
                    cluster_info = {
                        'points': cluster_points,
                        'points_indices': points_indices,
                        'cluster_size': len(cluster_points),
                        'cluster_idx': len(clusters) + 1 + self.CF_CLUSTER_COUNT,
                        'dim_name': 'PW',
                        'slice_idx': self.current_slice_idx + 1,
                        'time_ranges': self.time_ranges
                    }
                    clusters.append(cluster_info)
                    self.logger.info(f"切片{cluster_info['slice_idx']}{cluster_info['dim_name']}维类别{cluster_info['cluster_idx']} - 点数: {cluster_info['cluster_size']}")
            
            self.logger.info(f"{'='*50}\n")
            
            return clusters
            
        except Exception as e:
            self.logger.error(f"PW维度聚类出错: {str(e)}")
            return []

    def _get_unprocessed_points(self) -> List[NDArray]:
        """获取未被聚类的数据点"""
        try:
            if self.points is None:
                return []
            
            # 获取所有未处理点的索引
            all_indices = set(range(len(self.points)))
            unprocessed_indices = list(all_indices - self.processed_points)
            
            # 返回未处理的点
            return self.points[unprocessed_indices]
            
        except Exception as e:
            self.logger.error(f"获取未处理点出错: {str(e)}")
            return []

    def detect_band(self, data: np.ndarray) -> str:
        """检测数据所属的频率波段
        
        Args:
            data (np.ndarray): 输入数据，形状为(n_samples, n_features)
            
        Returns:
            str: 检测到的波段名称 ('X波段' 或 '其他波段')
            
        Raises:
            ValueError: 当输入数据无效时抛出
        """
        try:
            # 确保数据是numpy数组
            data = np.array(data)
            # 获取CF维度数据（第一列）
            cf_data = data[:, 0] if len(data.shape) > 1 else data
            
            cf_min = np.min(cf_data)
            cf_max = np.max(cf_data)
            
            if 8000 <= cf_min <= 12000 and cf_max <= 12000:
                return "X波段"
            return "其他波段"
            
        except Exception as e:
            self.logger.error(f"波段检测出错: {str(e)}")
            return "其他波段"

    def process_dimension(self, dimension: str, data: np.ndarray) -> Tuple[bool, Optional[Dict]]:
        """通用的维度处理方法
        
        Args:
            dimension (str): 处理维度 ('CF' 或 'PW')
            data (np.ndarray): 输入数据
            
        Returns:
            Tuple[bool, Optional[Dict]]: 
                - bool: 处理是否成功
                - Optional[Dict]: 聚类结果字典，包含clusters和unprocessed_points
                
        Raises:
            ValueError: 当维度参数无效时抛出
        """
        try:
            if dimension not in self.DIM_NAMES:
                raise ValueError(f"无效的维度名称: {dimension}")
            
            # 确保数据是numpy数组
            self.points = np.array(data) if not isinstance(data, np.ndarray) else data
            self.processed_points = set()
            
            # 使用当前切片的时间范围
            if self.slice_time_ranges and self.current_slice_idx < len(self.slice_time_ranges):
                self.time_ranges = self.slice_time_ranges[self.current_slice_idx]
            else:
                self.logger.warning(f"切片{self.current_slice_idx}的时间范围未设置")
                # 如果没有设置时间范围，则使用数据中的时间范围
                if len(self.points) > 0:
                    self.time_ranges = [self.points[0][4], self.points[-1][4]]
            
            # 根据维度选择聚类方法
            if dimension == 'CF':
                clusters = self._cluster_cf_dimension()
            else:  # PW
                clusters = self._cluster_pw_dimension()
                
            if clusters:
                result = {
                    'clusters': clusters,
                    'unprocessed_points': self._get_unprocessed_points()
                }
                return True, result
                
            return False, None
            
        except Exception as e:
            self.logger.error(f"{dimension}维度处理出错: {str(e)}")
            return False, None

    def set_slice_time_ranges(self, time_ranges: list):
        """设置切片的时间范围
        
        Args:
            time_ranges: 从DataProcessor获取的时间范围列表
        """
        self.slice_time_ranges = time_ranges