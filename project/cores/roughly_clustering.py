import numpy as np
from numpy.typing import NDArray
from .log_manager import LogManager
from sklearn.cluster import DBSCAN

class RoughClusterer:
    """一维密度聚类器
    
    用于对一维数据进行密度聚类分析，支持自定义实现和DBSCAN两种方式。
    
    Attributes:
        epsilon (float): 邻域半径，CF维度时单位为MHz，PW维度时单位为us
        min_pts (int): 最小点数，用于判定核心点
        logger (LogManager): 日志管理器实例
    """
    
    def __init__(self, epsilon: float, min_pts: int):
        """初始化聚类器
        
        Args:
            epsilon: float, 邻域半径
                CF维度时单位为MHz
                PW维度时单位为us
            min_pts: int, 最小点数
        """
        self.epsilon = epsilon
        self.min_pts = min_pts
        self.logger = LogManager()
        self.logger.debug(f"{'='*50}")
        self.logger.debug(f"初始化聚类器: epsilon={epsilon}, min_pts={min_pts}")
    
    def fit(self, data: NDArray, dim: int) -> NDArray:
        """对指定维度进行聚类
        
        Args:
            data: NDArray, 输入数据
            dim: int, 聚类维度 (0:CF, 1:PW)
        
        Returns:
            NDArray: 聚类标签，-1表示噪声点
        """
        if len(data) == 0:
            self.logger.warning("输入数据为空")
            return np.array([])
            
        # 获取指定维度的数据
        dim_data = data[:, dim]
        
        # 初始化标签（-1表示噪声点）
        labels = np.full(len(data), -1)
        
        # 当前聚类标签
        current_label = 0
        
        # 遍历所有点
        for i in range(len(data)):
            if labels[i] != -1:
                continue
                
            # 获取邻域点
            neighbors = self._get_neighbors(dim_data, i)
            
            # 如果邻域点数小于min_pts，标记为噪声点
            if len(neighbors) < self.min_pts:
                continue
                
            # 扩展聚类
            labels = self._expand_cluster(dim_data, labels, i, neighbors, current_label)
            current_label += 1
        return labels
    
    def fit_dbscan(self, data: NDArray, dim: int) -> NDArray:
        """使用DBSCAN算法对指定维度进行聚类
        
        Args:
            data: NDArray, 输入数据
            dim: int, 聚类维度 (0:CF, 1:PW)
        
        Returns:
            NDArray: 聚类标签，-1表示噪声点
        
        Raises:
            Exception: DBSCAN聚类过程中的异常
        """
        try:
            if len(data) == 0:
                self.logger.warning("输入数据为空")
                return np.array([])
                
            # 获取指定维度的数据并重塑为二维数组
            dim_data = data[:, dim].reshape(-1, 1)
            
            # 创建DBSCAN实例
            dbscan = DBSCAN(
                eps=self.epsilon,
                min_samples=self.min_pts,
                metric='euclidean',
                n_jobs=1
            )
            
            # 执行聚类
            # print(f"开始DBSCAN聚类，epsilon={self.epsilon}, min_samples={self.min_pts}")
            labels = dbscan.fit_predict(dim_data)
            
            self.logger.debug(f"DBSCAN聚类完成，共{len(np.unique(labels))-1}个类别")
            return labels
            
        except Exception as e:
            self.logger.error(f"DBSCAN聚类出错: {str(e)}")
            return np.full(len(data), -1)  # 出错时返回全部为噪声点的标签
    
    def _get_neighbors(self, data: NDArray, point_idx: int) -> NDArray:
        """获取邻域点
        
        Args:
            data: NDArray, 一维数据数组
            point_idx: int, 目标点的索引
        
        Returns:
            NDArray: 邻域点的索引数组
        """
        distances = np.abs(data - data[point_idx])
        neighbors = np.where(distances <= self.epsilon)[0]
        return neighbors
    
    def _expand_cluster(self, data: NDArray, labels: NDArray, 
                       point_idx: int, neighbors: NDArray, 
                       current_label: int) -> NDArray:
        """扩展聚类
        
        Args:
            data: NDArray, 一维数据数组
            labels: NDArray, 当前的标签数组
            point_idx: int, 核心点的索引
            neighbors: NDArray, 核心点的邻域点索引数组
            current_label: int, 当前聚类的标签值
        
        Returns:
            NDArray: 更新后的标签数组
        """
        # 标记当前点
        labels[point_idx] = current_label
        
        # 标记所有邻域点
        labels[neighbors] = current_label
        
        # 扩展聚类
        k = 0
        expanded_points = 0
        while k < len(neighbors):
            current_point = neighbors[k]
            
            # 获取当前点的邻域
            current_neighbors = self._get_neighbors(data, current_point)
            
            # 如果当前点是核心点
            if len(current_neighbors) >= self.min_pts:
                # 遍历当前点的邻域
                for neighbor in current_neighbors:
                    # 如果邻域点未被访问过，添加到邻域列表
                    if labels[neighbor] == -1:
                        neighbors = np.append(neighbors, neighbor)
                        labels[neighbor] = current_label
                        expanded_points += 1
            k += 1
        
        return labels
