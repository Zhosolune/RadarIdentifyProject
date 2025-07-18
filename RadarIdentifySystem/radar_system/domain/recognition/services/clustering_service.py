"""DBSCAN聚类服务

本模块实现了基于DBSCAN算法的雷达信号聚类服务，支持CF维度和PW维度聚类。
遵循DDD架构原则，在Domain层实现核心聚类业务逻辑。
"""

from typing import List, Tuple, Dict, Optional, Any, Union
import numpy as np
from sklearn.cluster import DBSCAN
from dataclasses import dataclass

from radar_system.domain.signal.entities.signal import SignalSlice, TimeRange
from radar_system.domain.recognition.entities.cluster_result import ClusterResult, UnclusteredPulseData
from radar_system.infrastructure.common.config import ConfigManager
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.exceptions import ValidationError


@dataclass
class ClusteringParams:
    """聚类参数数据类
    
    Attributes:
        eps: DBSCAN邻域半径参数
        min_samples: DBSCAN最小样本数参数
        dimension: 聚类维度（'CF'或'PW'）
    """
    eps: float
    min_samples: int
    dimension: str
    
    def __post_init__(self):
        """参数验证"""
        if self.dimension not in ['CF', 'PW']:
            raise ValueError(f"聚类维度必须为'CF'或'PW'，当前值: {self.dimension}")
        if self.eps <= 0:
            raise ValueError(f"eps参数必须大于0，当前值: {self.eps}")
        if self.min_samples <= 0:
            raise ValueError(f"min_samples参数必须大于0，当前值: {self.min_samples}")


class DBSCANClusteringService:
    """DBSCAN聚类服务
    
    提供通用的DBSCAN聚类功能，支持CF维度和PW维度聚类。
    遵循DDD架构原则，实现核心聚类业务逻辑。
    
    Attributes:
        config_manager (ConfigManager): 配置管理器实例
        _dimension_indices (Dict[str, int]): 维度索引映射
    """
    
    # 维度索引映射：数据数组中各维度的列索引
    _dimension_indices = {
        'CF': 0,   # 载频
        'PW': 1,   # 脉宽
        'DOA': 2,  # 到达角
        'PA': 3,   # 脉冲幅度
        'TOA': 4   # 到达时间
    }
    
    def __init__(self):
        """初始化聚类服务"""
        try:
            self.config_manager = ConfigManager.get_instance()
            system_logger.info("DBSCAN聚类服务初始化完成")
        except Exception as e:
            error_msg = f"DBSCAN聚类服务初始化失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg) from e
    
    def cluster_signal_slice(self,
                           signal_data: Union[SignalSlice, UnclusteredPulseData],
                           clustering_params: ClusteringParams) -> Tuple[List[ClusterResult], Optional[UnclusteredPulseData]]:
        """对信号数据进行DBSCAN聚类

        支持两种输入类型：
        1. SignalSlice: 原始信号切片
        2. UnclusteredPulseData: 未聚类的脉冲数据

        Args:
            signal_data: 信号数据（SignalSlice或UnclusteredPulseData）
            clustering_params: 聚类参数

        Returns:
            tuple: (聚类结果列表, 未聚类数据实体)
                - 聚类结果列表：成功聚类的结果
                - 未聚类数据实体：聚类失败的数据，如果所有数据都成功聚类则为None

        Raises:
            ValidationError: 当输入参数无效或聚类失败时
        """
        try:
            # 验证输入参数
            self._validate_inputs(signal_data, clustering_params)

            # 根据输入类型提取数据
            if isinstance(signal_data, SignalSlice):
                system_logger.debug(f"处理SignalSlice类型输入，切片索引: {signal_data.slice_index}")
                data = signal_data.data
                slice_index = signal_data.slice_index
                time_range = signal_data.time_range
                is_empty = signal_data.is_empty
                data_id = signal_data.id
            else:  # UnclusteredPulseData
                system_logger.debug(f"处理UnclusteredPulseData类型输入，切片索引: {signal_data.slice_index}")
                data = signal_data.pulse_data
                slice_index = signal_data.slice_index
                time_range = signal_data.time_ranges
                is_empty = data.size == 0
                data_id = f"unclustered-{signal_data.slice_index}"

            # 检查数据是否为空
            if is_empty:
                system_logger.warning(f"数据 {data_id} 为空，无法进行聚类")
                return [], None

            # 提取聚类特征数据: CF/PW
            feature_data = self._extract_clustering_features(data, clustering_params.dimension)

            # 执行DBSCAN聚类
            cluster_labels = self._perform_dbscan_clustering(feature_data, clustering_params)

            # 处理聚类结果
            cluster_results, unclustered_data = self._process_clustering_results(
                data, slice_index, time_range, cluster_labels, clustering_params
            )

            # 记录聚类统计信息
            self._log_clustering_statistics(
                data, slice_index, cluster_results, unclustered_data, clustering_params
            )

            return cluster_results, unclustered_data
            
        except Exception as e:
            data_type = "SignalSlice" if isinstance(signal_data, SignalSlice) else "UnclusteredPulseData"
            error_msg = f"{data_type}聚类失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg) from e
    
    def get_clustering_params_from_ui(self, ui_params: Dict[str, Any], dimension: str) -> ClusteringParams:
        """从UI参数获取聚类参数
        
        Args:
            ui_params: UI控件参数字典
            dimension: 聚类维度（'CF'或'PW'）
            
        Returns:
            ClusteringParams: 聚类参数对象
        """
        try:
            # 根据维度确定参数键名
            eps_key = f"epsilon_{dimension.lower()}"
            
            # 从UI参数获取值，如果无效则使用配置文件默认值
            eps = self._parse_ui_parameter(ui_params.get(eps_key), 
                                         getattr(self.config_manager.clustering, eps_key))
            min_samples = self._parse_ui_parameter(ui_params.get("min_pts"), 
                                                 self.config_manager.clustering.min_pts)
            
            return ClusteringParams(eps=eps, min_samples=min_samples, dimension=dimension)
            
        except Exception as e:
            error_msg = f"解析UI聚类参数失败: {str(e)}"
            system_logger.error(error_msg)
            # 使用配置文件默认值作为回退
            return self._get_default_clustering_params(dimension)
    
    def _validate_inputs(self, signal_data: Union[SignalSlice, UnclusteredPulseData], clustering_params: ClusteringParams) -> None:
        """验证输入参数

        Args:
            signal_data: 信号数据（SignalSlice或UnclusteredPulseData）
            clustering_params: 聚类参数

        Raises:
            ValidationError: 参数验证失败时
        """
        if not isinstance(signal_data, (SignalSlice, UnclusteredPulseData)):
            raise ValidationError(f"signal_data必须为SignalSlice或UnclusteredPulseData类型，当前类型: {type(signal_data)}")

        if not isinstance(clustering_params, ClusteringParams):
            raise ValidationError(f"clustering_params必须为ClusteringParams类型，当前类型: {type(clustering_params)}")
    
    def _extract_clustering_features(self, data: np.ndarray, dimension: str) -> np.ndarray:
        """提取聚类特征数据
        
        Args:
            data: 原始信号数据 (N, 5) [CF, PW, DOA, PA, TOA]
            dimension: 聚类维度
            
        Returns:
            np.ndarray: 聚类特征数据
        """
        if dimension not in self._dimension_indices:
            raise ValidationError(f"不支持的聚类维度: {dimension}")
        
        # 获取指定维度的数据列索引
        dim_index = self._dimension_indices[dimension]
        
        # 提取特征数据（reshape为列向量以适配DBSCAN）
        feature_data = data[:, dim_index].reshape(-1, 1)
        
        system_logger.debug(f"提取{dimension}维度特征数据，形状: {feature_data.shape}")
        return feature_data
    
    def _perform_dbscan_clustering(self, feature_data: np.ndarray, params: ClusteringParams) -> np.ndarray:
        """执行DBSCAN聚类
        
        Args:
            feature_data: 特征数据
            params: 聚类参数
            
        Returns:
            np.ndarray: 聚类标签数组
        """
        try:
            # 创建DBSCAN聚类器
            dbscan = DBSCAN(eps=params.eps, min_samples=params.min_samples)
            
            # 执行聚类
            cluster_labels = dbscan.fit_predict(feature_data)
            
            system_logger.debug(f"DBSCAN聚类完成，参数: eps={params.eps}, min_samples={params.min_samples}")
            return cluster_labels
            
        except Exception as e:
            error_msg = f"DBSCAN聚类执行失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg) from e

    def _process_clustering_results(self,
                                  data: np.ndarray,
                                  slice_index: int,
                                  time_range: TimeRange,
                                  cluster_labels: np.ndarray,
                                  params: ClusteringParams) -> Tuple[List[ClusterResult], Optional[UnclusteredPulseData]]:
        """处理聚类结果

        Args:
            data: 原始数据数组
            slice_index: 切片索引
            time_range: 时间范围
            cluster_labels: DBSCAN聚类标签
            params: 聚类参数

        Returns:
            tuple: (聚类结果列表, 未聚类数据实体)
        """
        cluster_results = []
        unclustered_indices = []

        # 获取唯一的聚类标签（-1表示噪声点）
        unique_labels = np.unique(cluster_labels)

        # 处理每个聚类
        for label in unique_labels:
            if label == -1:
                # 噪声点（未聚类数据）
                unclustered_indices.extend(np.where(cluster_labels == label)[0])
            else:
                # 有效聚类
                cluster_indices = np.where(cluster_labels == label)[0]
                cluster_data = data[cluster_indices]

                # 创建聚类结果实体
                cluster_result = ClusterResult(
                    cluster_data=cluster_data,
                    slice_index=slice_index,
                    cluster_index=label,
                    dim_name=params.dimension,
                    time_ranges=time_range,
                    dimension_category_index=0  # 默认为0，可根据需要调整
                )
                cluster_results.append(cluster_result)

        # 处理未聚类数据
        unclustered_data = None
        if unclustered_indices:
            unclustered_pulse_data = data[unclustered_indices]
            unclustered_data = UnclusteredPulseData(
                pulse_data=unclustered_pulse_data,
                slice_index=slice_index,
                clustering_dimension=params.dimension,
                time_ranges=time_range,
                successful_cluster_count=len(cluster_results)
            )

        return cluster_results, unclustered_data

    def _log_clustering_statistics(self,
                                 data: np.ndarray,
                                 slice_index: int,
                                 cluster_results: List[ClusterResult],
                                 unclustered_data: Optional[UnclusteredPulseData],
                                 params: ClusteringParams) -> None:
        """记录聚类统计信息

        Args:
            data: 原始数据数组
            slice_index: 切片索引
            cluster_results: 聚类结果列表
            unclustered_data: 未聚类数据
            params: 聚类参数
        """
        total_points = data.shape[0]
        clustered_points = sum(len(result.cluster_data) for result in cluster_results)
        unclustered_points = len(unclustered_data.pulse_data) if unclustered_data else 0

        system_logger.info(
            f"聚类完成 - 切片索引: {slice_index}, 维度: {params.dimension}, "
            f"总数据点: {total_points}, 聚类数: {len(cluster_results)}, "
            f"已聚类点数: {clustered_points}, 未聚类点数: {unclustered_points}"
        )

    def _parse_ui_parameter(self, ui_value: Any, default_value: float) -> float:
        """解析UI参数值

        Args:
            ui_value: UI控件值
            default_value: 默认值

        Returns:
            float: 解析后的参数值
        """
        try:
            if ui_value is None or ui_value == "":
                return default_value

            # 尝试转换为浮点数
            parsed_value = float(ui_value)

            # 验证值的有效性
            if parsed_value <= 0:
                system_logger.warning(f"UI参数值无效 ({parsed_value})，使用默认值 {default_value}")
                return default_value

            return parsed_value

        except (ValueError, TypeError):
            system_logger.warning(f"UI参数解析失败 ({ui_value})，使用默认值 {default_value}")
            return default_value

    def _get_default_clustering_params(self, dimension: str) -> ClusteringParams:
        """获取默认聚类参数

        Args:
            dimension: 聚类维度

        Returns:
            ClusteringParams: 默认聚类参数
        """
        eps_key = f"epsilon_{dimension.lower()}"
        eps = getattr(self.config_manager.clustering, eps_key)
        min_samples = self.config_manager.clustering.min_pts

        return ClusteringParams(eps=eps, min_samples=min_samples, dimension=dimension)