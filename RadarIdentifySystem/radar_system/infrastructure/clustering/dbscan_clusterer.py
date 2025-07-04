"""DBSCAN聚类器基础设施模块

本模块提供DBSCAN聚类算法的基础设施实现，从project/cores/roughly_clustering.py迁移而来。
"""

import numpy as np
from typing import List, Tuple, Optional
from sklearn.cluster import DBSCAN
from radar_system.infrastructure.common.logging import model_logger
from radar_system.infrastructure.common.exceptions import ModelError
from radar_system.domain.recognition.entities import DimensionType, ClusterStatus


class DBSCANClusterer:
    """DBSCAN聚类器
    
    提供基于DBSCAN算法的聚类功能，支持CF和PW维度的聚类处理。
    
    Attributes:
        epsilon_cf (float): CF维度的邻域半径
        epsilon_pw (float): PW维度的邻域半径
        min_samples (int): 形成聚类的最小点数
    """
    
    def __init__(self, epsilon_cf: float, epsilon_pw: float, min_samples: int):
        """初始化DBSCAN聚类器
        
        Args:
            epsilon_cf: CF维度的邻域半径
            epsilon_pw: PW维度的邻域半径
            min_samples: 形成聚类的最小点数
        """
        self.epsilon_cf = epsilon_cf
        self.epsilon_pw = epsilon_pw
        self.min_samples = min_samples
        
        # 验证参数
        self._validate_parameters()
        
        model_logger.info(
            f"DBSCAN聚类器初始化完成 - "
            f"epsilon_cf: {epsilon_cf}, epsilon_pw: {epsilon_pw}, min_samples: {min_samples}"
        )
    
    def _validate_parameters(self):
        """验证聚类参数的有效性"""
        if self.epsilon_cf <= 0:
            raise ValueError(f"CF维度邻域半径必须大于0，当前值: {self.epsilon_cf}")
        
        if self.epsilon_pw <= 0:
            raise ValueError(f"PW维度邻域半径必须大于0，当前值: {self.epsilon_pw}")
        
        if self.min_samples < 1:
            raise ValueError(f"最小点数必须大于等于1，当前值: {self.min_samples}")
    
    def cluster_dimension(self, data: np.ndarray, dimension_type: DimensionType) -> np.ndarray:
        """对指定维度进行DBSCAN聚类
        
        Args:
            data: 输入数据数组，形状为(n_samples, n_features)
            dimension_type: 维度类型（CF或PW）
            
        Returns:
            np.ndarray: 聚类标签数组，-1表示噪声点
            
        Raises:
            ModelError: 聚类过程中出现错误
        """
        try:
            if len(data) == 0:
                model_logger.warning("输入数据为空")
                return np.array([])
            
            # 获取维度对应的参数
            epsilon = self.epsilon_cf if dimension_type == DimensionType.CF else self.epsilon_pw
            column_index = dimension_type.data_column_index
            
            # 提取指定维度的数据并重塑为二维数组
            if data.ndim == 1:
                dim_data = data.reshape(-1, 1)
            else:
                if column_index >= data.shape[1]:
                    raise ModelError(
                        message=f"数据维度不足，无法获取{dimension_type.value}维度数据",
                        code="INSUFFICIENT_DIMENSIONS",
                        details={
                            "required_column": column_index,
                            "available_columns": data.shape[1]
                        }
                    )
                dim_data = data[:, column_index].reshape(-1, 1)
            
            # 创建DBSCAN实例
            dbscan = DBSCAN(
                eps=epsilon,
                min_samples=self.min_samples,
                metric='euclidean',
                n_jobs=1
            )
            
            # 执行聚类
            model_logger.debug(
                f"开始{dimension_type.value}维度DBSCAN聚类 - "
                f"epsilon: {epsilon}, min_samples: {self.min_samples}, data_points: {len(data)}"
            )
            
            labels = dbscan.fit_predict(dim_data)
            
            # 统计聚类结果
            unique_labels = np.unique(labels)
            n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
            n_noise = np.sum(labels == -1)
            
            model_logger.info(
                f"{dimension_type.value}维度DBSCAN聚类完成 - "
                f"聚类数: {n_clusters}, 噪声点: {n_noise}, 总点数: {len(data)}"
            )
            
            return labels
            
        except Exception as e:
            if not isinstance(e, ModelError):
                e = ModelError(
                    message=f"{dimension_type.value}维度DBSCAN聚类失败: {str(e)}",
                    code="CLUSTERING_ERROR",
                    details={
                        "dimension_type": dimension_type.value,
                        "data_shape": data.shape if hasattr(data, 'shape') else None,
                        "epsilon": epsilon if 'epsilon' in locals() else None
                    }
                )
            model_logger.error(str(e), exc_info=True)
            raise e
    
    def extract_clusters(self, data: np.ndarray, labels: np.ndarray, 
                        dimension_type: DimensionType) -> List[Tuple[np.ndarray, List[int], ClusterStatus]]:
        """从聚类标签中提取聚类数据
        
        Args:
            data: 原始数据数组
            labels: 聚类标签数组
            dimension_type: 维度类型
            
        Returns:
            List[Tuple[np.ndarray, List[int], ClusterStatus]]: 聚类结果列表
                每个元组包含：(聚类数据, 数据点索引, 聚类状态)
        """
        try:
            clusters = []
            unique_labels = np.unique(labels)
            
            for label in unique_labels:
                if label == -1:  # 跳过噪声点
                    continue
                
                # 获取属于当前聚类的数据点
                cluster_mask = labels == label
                cluster_data = data[cluster_mask]
                cluster_indices = np.where(cluster_mask)[0].tolist()
                
                # 判断聚类状态（这里简化为根据聚类大小判断）
                # 实际业务中可能需要更复杂的判断逻辑
                cluster_size = len(cluster_data)
                status = ClusterStatus.VALID if cluster_size >= self.min_samples else ClusterStatus.INVALID
                
                clusters.append((cluster_data, cluster_indices, status))
                
                model_logger.debug(
                    f"{dimension_type.value}维度聚类{label} - "
                    f"大小: {cluster_size}, 状态: {status.value}"
                )
            
            model_logger.info(
                f"{dimension_type.value}维度聚类提取完成 - 总聚类数: {len(clusters)}"
            )
            
            return clusters
            
        except Exception as e:
            error = ModelError(
                message=f"聚类数据提取失败: {str(e)}",
                code="CLUSTER_EXTRACTION_ERROR",
                details={
                    "dimension_type": dimension_type.value,
                    "data_shape": data.shape if hasattr(data, 'shape') else None,
                    "labels_shape": labels.shape if hasattr(labels, 'shape') else None
                }
            )
            model_logger.error(str(error), exc_info=True)
            raise error
    
    def update_parameters(self, epsilon_cf: Optional[float] = None, 
                         epsilon_pw: Optional[float] = None, 
                         min_samples: Optional[int] = None):
        """更新聚类参数
        
        Args:
            epsilon_cf: 新的CF维度邻域半径，可选
            epsilon_pw: 新的PW维度邻域半径，可选
            min_samples: 新的最小点数，可选
        """
        if epsilon_cf is not None:
            self.epsilon_cf = epsilon_cf
        if epsilon_pw is not None:
            self.epsilon_pw = epsilon_pw
        if min_samples is not None:
            self.min_samples = min_samples
        
        # 重新验证参数
        self._validate_parameters()
        
        model_logger.info(
            f"DBSCAN聚类器参数已更新 - "
            f"epsilon_cf: {self.epsilon_cf}, epsilon_pw: {self.epsilon_pw}, min_samples: {self.min_samples}"
        )
    
    def get_parameters(self) -> dict:
        """获取当前聚类参数
        
        Returns:
            dict: 包含当前参数的字典
        """
        return {
            'epsilon_cf': self.epsilon_cf,
            'epsilon_pw': self.epsilon_pw,
            'min_samples': self.min_samples
        }
