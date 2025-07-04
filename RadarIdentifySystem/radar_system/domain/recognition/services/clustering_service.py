"""聚类领域服务模块

本模块提供聚类相关的领域服务实现，协调DBSCAN聚类过程。
"""

from typing import List, Dict, Any, Optional
import numpy as np

from radar_system.domain.recognition.entities import (
    ClusterCandidate, DimensionType, ClusterStatus, 
    RecognitionParams, ClusteringParams
)
from radar_system.domain.signal.entities.signal import TimeRange
from radar_system.infrastructure.clustering import DBSCANClusterer
from radar_system.infrastructure.common.exceptions import (
    ValidationError, ProcessingError
)
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.thread_safe_signal_emitter import ThreadSafeSignalEmitter


class ClusteringService:
    """聚类领域服务
    
    负责协调聚类处理过程，包括：
    - CF维度聚类处理
    - PW维度聚类处理
    - 聚类候选生成和验证
    - 聚类状态管理
    """
    
    def __init__(
        self,
        clustering_params: Optional[ClusteringParams] = None,
        signal_emitter: Optional[ThreadSafeSignalEmitter] = None
    ):
        """初始化聚类服务
        
        Args:
            clustering_params: 聚类参数配置
            signal_emitter: 信号发射器
        """
        self._clustering_params = clustering_params or ClusteringParams()
        self._signal_emitter = signal_emitter or ThreadSafeSignalEmitter()
        
        # 初始化DBSCAN聚类器
        self._clusterer = DBSCANClusterer(
            epsilon_cf=self._clustering_params.epsilon_cf,
            epsilon_pw=self._clustering_params.epsilon_pw,
            min_samples=self._clustering_params.min_pts
        )
        
        system_logger.info(f"聚类服务初始化完成 - CF epsilon: {self._clustering_params.epsilon_cf}, "
                           f"PW epsilon: {self._clustering_params.epsilon_pw}")
    
    def cluster_cf_dimension(
        self,
        signal_data: np.ndarray,
        slice_index: int,
        time_range: TimeRange
    ) -> List[ClusterCandidate]:
        """执行CF维度聚类
        
        Args:
            signal_data: 信号数据
            slice_index: 切片索引
            time_range: 时间范围
            
        Returns:
            CF维度聚类候选列表
            
        Raises:
            ValidationError: 数据验证失败
            ProcessingError: 聚类处理失败
        """
        try:
            # 验证输入数据
            self._validate_signal_data(signal_data, DimensionType.CF)
            
            # 执行CF维度聚类
            cluster_labels = self._clusterer.cluster_dimension(signal_data, DimensionType.CF)
            
            # 提取聚类数据
            clusters_data = self._clusterer.extract_clusters(
                signal_data, cluster_labels, DimensionType.CF
            )
            
            # 生成聚类候选
            cluster_candidates = []
            for cluster_index, cluster_data in enumerate(clusters_data):
                # 验证聚类有效性
                status = self._validate_cluster_quality(cluster_data, DimensionType.CF)
                
                candidate = ClusterCandidate(
                    cluster_data=cluster_data,
                    dimension_type=DimensionType.CF,
                    cluster_index=cluster_index,
                    slice_index=slice_index,
                    status=status,
                    time_range=time_range,
                    metadata={
                        'cluster_size': len(cluster_data),
                        'clustering_params': self._clustering_params.to_dict()
                    }
                )
                cluster_candidates.append(candidate)
            
            system_logger.info(f"CF维度聚类完成 - 切片{slice_index}, 聚类数: {len(cluster_candidates)}")
            return cluster_candidates

        except Exception as e:
            error_msg = f"CF维度聚类失败 - 切片{slice_index}: {str(e)}"
            system_logger.error(error_msg)
            raise ProcessingError(error_msg) from e
    
    def cluster_pw_dimension(
        self,
        signal_data: np.ndarray,
        slice_index: int,
        time_range: TimeRange
    ) -> List[ClusterCandidate]:
        """执行PW维度聚类
        
        Args:
            signal_data: 信号数据
            slice_index: 切片索引
            time_range: 时间范围
            
        Returns:
            PW维度聚类候选列表
            
        Raises:
            ValidationError: 数据验证失败
            ProcessingError: 聚类处理失败
        """
        try:
            # 验证输入数据
            self._validate_signal_data(signal_data, DimensionType.PW)
            
            # 执行PW维度聚类
            cluster_labels = self._clusterer.cluster_dimension(signal_data, DimensionType.PW)
            
            # 提取聚类数据
            clusters_data = self._clusterer.extract_clusters(
                signal_data, cluster_labels, DimensionType.PW
            )
            
            # 生成聚类候选
            cluster_candidates = []
            for cluster_index, cluster_data in enumerate(clusters_data):
                # 验证聚类有效性
                status = self._validate_cluster_quality(cluster_data, DimensionType.PW)
                
                candidate = ClusterCandidate(
                    cluster_data=cluster_data,
                    dimension_type=DimensionType.PW,
                    cluster_index=cluster_index,
                    slice_index=slice_index,
                    status=status,
                    time_range=time_range,
                    metadata={
                        'cluster_size': len(cluster_data),
                        'clustering_params': self._clustering_params.to_dict()
                    }
                )
                cluster_candidates.append(candidate)
            
            system_logger.info(f"PW维度聚类完成 - 切片{slice_index}, 聚类数: {len(cluster_candidates)}")
            return cluster_candidates

        except Exception as e:
            error_msg = f"PW维度聚类失败 - 切片{slice_index}: {str(e)}"
            system_logger.error(error_msg)
            raise ProcessingError(error_msg) from e
    
    def update_clustering_parameters(self, new_params: ClusteringParams) -> None:
        """更新聚类参数
        
        Args:
            new_params: 新的聚类参数
        """
        self._clustering_params = new_params
        self._clusterer.update_parameters(
            epsilon_cf=new_params.epsilon_cf,
            epsilon_pw=new_params.epsilon_pw,
            min_samples=new_params.min_pts
        )
        system_logger.info(f"聚类参数已更新 - CF epsilon: {new_params.epsilon_cf}, "
                           f"PW epsilon: {new_params.epsilon_pw}")
    
    def get_clustering_statistics(self, candidates: List[ClusterCandidate]) -> Dict[str, Any]:
        """获取聚类统计信息
        
        Args:
            candidates: 聚类候选列表
            
        Returns:
            聚类统计信息
        """
        if not candidates:
            return {
                'total_clusters': 0,
                'valid_clusters': 0,
                'invalid_clusters': 0,
                'cf_clusters': 0,
                'pw_clusters': 0
            }
        
        valid_count = sum(1 for c in candidates if c.status == ClusterStatus.VALID)
        invalid_count = len(candidates) - valid_count
        cf_count = sum(1 for c in candidates if c.dimension_type == DimensionType.CF)
        pw_count = sum(1 for c in candidates if c.dimension_type == DimensionType.PW)
        
        return {
            'total_clusters': len(candidates),
            'valid_clusters': valid_count,
            'invalid_clusters': invalid_count,
            'cf_clusters': cf_count,
            'pw_clusters': pw_count,
            'average_cluster_size': np.mean([len(c.cluster_data) for c in candidates])
        }
    
    def _validate_signal_data(self, signal_data: np.ndarray, dimension_type: DimensionType) -> None:
        """验证信号数据
        
        Args:
            signal_data: 信号数据
            dimension_type: 维度类型
            
        Raises:
            ValidationError: 数据验证失败
        """
        if signal_data is None or len(signal_data) == 0:
            raise ValidationError("信号数据不能为空")
        
        if signal_data.ndim != 2:
            raise ValidationError(f"信号数据必须是二维数组，当前维度: {signal_data.ndim}")
        
        min_points = self._clustering_params.min_pts
        if len(signal_data) < min_points:
            raise ValidationError(f"信号数据点数不足，需要至少{min_points}个点，当前: {len(signal_data)}")
    
    def _validate_cluster_quality(
        self, 
        cluster_data: np.ndarray, 
        dimension_type: DimensionType
    ) -> ClusterStatus:
        """验证聚类质量
        
        Args:
            cluster_data: 聚类数据
            dimension_type: 维度类型
            
        Returns:
            聚类状态
        """
        # 检查聚类大小
        min_size = self._clustering_params.min_pts
        if len(cluster_data) < min_size:
            return ClusterStatus.INVALID
        
        # 基本质量检查：确保聚类数据是有效的numpy数组
        if not isinstance(cluster_data, np.ndarray):
            return ClusterStatus.INVALID

        if cluster_data.ndim != 2 or cluster_data.shape[1] < 2:
            return ClusterStatus.INVALID
        
        return ClusterStatus.VALID
