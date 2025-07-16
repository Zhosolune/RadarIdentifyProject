"""未聚类数据聚类服务

本模块实现了专门处理UnclusteredPulseData实体的聚类服务，
支持跨维度的聚类索引继承机制，确保多维度聚类结果的正确索引。
"""

from typing import List, Tuple, Optional
import numpy as np

from radar_system.domain.recognition.services.clustering_service import DBSCANClusteringService, ClusteringParams
from radar_system.domain.recognition.entities.cluster_result import ClusterResult, UnclusteredPulseData
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.exceptions import ValidationError


class UnclusteredDataClusteringService:
    """未聚类数据聚类服务
    
    专门处理UnclusteredPulseData实体的二次聚类，实现跨维度的聚类索引继承机制。
    确保在多维度聚类流程中，每个维度的聚类结果都有正确的索引标识。
    
    核心功能：
    1. 复用DBSCANClusteringService的核心聚类逻辑
    2. 实现聚类索引的跨维度继承
    3. 正确处理dimension_category_index的重置
    4. 提供专门的未聚类数据处理接口
    
    Attributes:
        base_clustering_service (DBSCANClusteringService): 基础聚类服务实例
    """
    
    def __init__(self):
        """初始化未聚类数据聚类服务"""
        self.base_clustering_service = DBSCANClusteringService()
        system_logger.info("未聚类数据聚类服务初始化完成")
    
    def cluster_unclustered_data(self, 
                                unclustered_data: UnclusteredPulseData,
                                clustering_params: ClusteringParams) -> Tuple[List[ClusterResult], Optional[UnclusteredPulseData]]:
        """对未聚类数据进行二次聚类
        
        Args:
            unclustered_data: 未聚类脉冲数据实体
            clustering_params: 聚类参数
            
        Returns:
            tuple: (聚类结果列表, 剩余未聚类数据实体)
                - 聚类结果列表：成功聚类的结果，cluster_index已正确继承
                - 剩余未聚类数据实体：仍然未聚类的数据，如果全部聚类成功则为None
                
        Raises:
            ValidationError: 当输入参数无效或聚类失败时
        """
        try:
            # 验证输入参数
            self._validate_inputs(unclustered_data, clustering_params)
            
            # 检查数据是否准备好进行聚类
            if not unclustered_data.is_ready_for_next_dimension():
                system_logger.warning(f"未聚类数据未准备好进行{clustering_params.dimension}维度聚类")
                return [], unclustered_data
            
            system_logger.info(f"开始{clustering_params.dimension}维度二次聚类，"
                             f"数据点数: {unclustered_data.get_pulse_count()}, "
                             f"前一维度成功聚类数: {unclustered_data.successful_cluster_count}")

            # 执行基础聚类 - 直接传入UnclusteredPulseData
            base_clusters, remaining_unclustered = self.base_clustering_service.cluster_signal_slice(
                unclustered_data, clustering_params
            )
            
            # 处理聚类索引继承
            processed_clusters = self._process_cluster_indices(
                base_clusters, unclustered_data, clustering_params
            )
            
            # 处理剩余未聚类数据
            final_unclustered_data = self._process_remaining_unclustered_data(
                remaining_unclustered, unclustered_data, len(processed_clusters)
            )
            
            # 记录聚类结果
            self._log_clustering_results(processed_clusters, final_unclustered_data, unclustered_data, clustering_params)
            
            return processed_clusters, final_unclustered_data
            
        except Exception as e:
            error_msg = f"{clustering_params.dimension}维度未聚类数据聚类失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg) from e
    
    def _validate_inputs(self, unclustered_data: UnclusteredPulseData, clustering_params: ClusteringParams) -> None:
        """验证输入参数
        
        Args:
            unclustered_data: 未聚类数据实体
            clustering_params: 聚类参数
            
        Raises:
            ValidationError: 当输入参数无效时
        """
        if not isinstance(unclustered_data, UnclusteredPulseData):
            raise ValidationError(f"unclustered_data必须是UnclusteredPulseData类型，实际类型: {type(unclustered_data)}")
        
        if not isinstance(clustering_params, ClusteringParams):
            raise ValidationError(f"clustering_params必须是ClusteringParams类型，实际类型: {type(clustering_params)}")
        
        if unclustered_data.pulse_data.size == 0:
            raise ValidationError("未聚类数据为空，无法进行聚类")
    

    
    def _process_cluster_indices(self, 
                               base_clusters: List[ClusterResult],
                               unclustered_data: UnclusteredPulseData,
                               clustering_params: ClusteringParams) -> List[ClusterResult]:
        """处理聚类索引继承
        
        实现跨维度的聚类索引继承机制：
        1. cluster_index从前一维度的最大索引+1开始
        2. dimension_category_index在每个维度重置为0开始
        
        Args:
            base_clusters: 基础聚类结果列表
            unclustered_data: 原始未聚类数据
            clustering_params: 聚类参数
            
        Returns:
            List[ClusterResult]: 处理后的聚类结果列表
        """
        processed_clusters = []
        
        # 计算起始聚类索引：前一维度成功聚类数量
        start_cluster_index = unclustered_data.successful_cluster_count
        
        # 确定dimension_category_index
        dimension_category_index = self._get_dimension_category_index(clustering_params.dimension)
        
        for i, cluster in enumerate(base_clusters):
            # 创建新的聚类结果，更新索引
            processed_cluster = ClusterResult(
                cluster_data=cluster.cluster_data,
                slice_index=cluster.slice_index,
                cluster_index=start_cluster_index + i,  # 继承前一维度的索引
                dim_name=cluster.dim_name,
                time_ranges=cluster.time_ranges,
                dimension_category_index=dimension_category_index  # 当前维度重置为0开始
            )
            processed_clusters.append(processed_cluster)
        
        system_logger.debug(f"聚类索引处理完成: 起始索引={start_cluster_index}, "
                          f"新增聚类数={len(processed_clusters)}, "
                          f"dimension_category_index={dimension_category_index}")
        
        return processed_clusters
    
    def _get_dimension_category_index(self, dimension: str) -> int:
        """获取维度类别索引
        
        Args:
            dimension: 聚类维度名称
            
        Returns:
            int: 维度类别索引
        """
        dimension_mapping = {
            'CF': 0,
            'PW': 1,
            'DOA': 2,
            'PA': 3,
            'TOA': 4
        }
        return dimension_mapping.get(dimension, 0)
    
    def _process_remaining_unclustered_data(self, 
                                          remaining_unclustered: Optional[UnclusteredPulseData],
                                          original_unclustered: UnclusteredPulseData,
                                          new_cluster_count: int) -> Optional[UnclusteredPulseData]:
        """处理剩余未聚类数据
        
        Args:
            remaining_unclustered: 基础聚类服务返回的剩余未聚类数据
            original_unclustered: 原始未聚类数据
            new_cluster_count: 新增聚类数量
            
        Returns:
            Optional[UnclusteredPulseData]: 最终未聚类数据实体
        """
        if remaining_unclustered is None:
            return None
        
        # 更新成功聚类数量：原有数量 + 新增数量
        updated_successful_count = original_unclustered.successful_cluster_count + new_cluster_count
        
        # 创建新的未聚类数据实体
        final_unclustered_data = UnclusteredPulseData(
            pulse_data=remaining_unclustered.pulse_data,
            slice_index=remaining_unclustered.slice_index,
            clustering_dimension=remaining_unclustered.clustering_dimension,
            time_ranges=remaining_unclustered.time_ranges,
            successful_cluster_count=updated_successful_count
        )
        
        return final_unclustered_data
    
    def _log_clustering_results(self, 
                              clusters: List[ClusterResult],
                              final_unclustered: Optional[UnclusteredPulseData],
                              original_unclustered: UnclusteredPulseData,
                              clustering_params: ClusteringParams) -> None:
        """记录聚类结果日志
        
        Args:
            clusters: 聚类结果列表
            final_unclustered: 最终未聚类数据
            original_unclustered: 原始未聚类数据
            clustering_params: 聚类参数
        """
        total_pulses = original_unclustered.get_pulse_count()
        clustered_pulses = sum(cluster.cluster_data.shape[0] for cluster in clusters)
        remaining_pulses = final_unclustered.get_pulse_count() if final_unclustered else 0
        
        clustering_efficiency = (clustered_pulses / total_pulses * 100) if total_pulses > 0 else 0
        
        system_logger.info(f"{clustering_params.dimension}维度二次聚类完成 - "
                         f"切片: {original_unclustered.slice_index}, "
                         f"维度: {clustering_params.dimension}, "
                         f"总数据点: {total_pulses}, "
                         f"聚类数: {len(clusters)}, "
                         f"已聚类点数: {clustered_pulses}, "
                         f"剩余未聚类点数: {remaining_pulses}, "
                         f"聚类效率: {clustering_efficiency:.1f}%")
