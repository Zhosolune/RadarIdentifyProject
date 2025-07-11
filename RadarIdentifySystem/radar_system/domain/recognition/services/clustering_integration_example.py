"""聚类服务集成示例

本模块展示如何在应用层集成DBSCAN聚类服务，包括：
1. 从UI获取聚类参数
2. 执行CF和PW维度聚类
3. 处理聚类结果和未聚类数据
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np

from radar_system.domain.signal.entities.signal import SignalSlice
from radar_system.domain.recognition.entities.cluster_result import ClusterResult, UnclusteredPulseData
from radar_system.domain.recognition.services.clustering_service import DBSCANClusteringService, ClusteringParams
from radar_system.domain.recognition.services.ui_params_parser import UIParamsParser
from radar_system.infrastructure.common.logging import system_logger


class ClusteringIntegrationService:
    """聚类集成服务
    
    提供完整的聚类处理流程，包括参数获取、聚类执行和结果处理。
    适用于Application层调用。
    """
    
    def __init__(self):
        """初始化聚类集成服务"""
        self.clustering_service = DBSCANClusteringService()
    
    def process_signal_slice_clustering(self, 
                                      signal_slice: SignalSlice,
                                      main_window) -> Dict[str, Any]:
        """处理信号切片的完整聚类流程
        
        Args:
            signal_slice: 信号切片实体
            main_window: 主窗口实例（用于获取UI参数）
            
        Returns:
            Dict[str, Any]: 聚类处理结果
                - success: 是否成功
                - cf_results: CF维度聚类结果列表
                - pw_results: PW维度聚类结果列表
                - cf_unclustered: CF维度未聚类数据
                - pw_unclustered: PW维度未聚类数据
                - error_message: 错误信息（如果有）
        """
        try:
            # 1. 从UI获取聚类参数
            ui_params = UIParamsParser.get_validated_params_dict(main_window)
            
            # 2. 执行CF维度聚类
            cf_params = self.clustering_service.get_clustering_params_from_ui(ui_params, 'CF')
            cf_results, cf_unclustered = self.clustering_service.cluster_signal_slice(
                signal_slice, cf_params
            )
            
            # 3. 执行PW维度聚类
            pw_params = self.clustering_service.get_clustering_params_from_ui(ui_params, 'PW')
            pw_results, pw_unclustered = self.clustering_service.cluster_signal_slice(
                signal_slice, pw_params
            )
            
            # 4. 记录聚类统计信息
            self._log_clustering_summary(signal_slice, cf_results, pw_results, cf_unclustered, pw_unclustered)
            
            return {
                'success': True,
                'cf_results': cf_results,
                'pw_results': pw_results,
                'cf_unclustered': cf_unclustered,
                'pw_unclustered': pw_unclustered,
                'error_message': None
            }
            
        except Exception as e:
            error_msg = f"信号切片聚类处理失败: {str(e)}"
            system_logger.error(error_msg)
            return {
                'success': False,
                'cf_results': [],
                'pw_results': [],
                'cf_unclustered': None,
                'pw_unclustered': None,
                'error_message': error_msg
            }
    
    def process_single_dimension_clustering(self,
                                          signal_slice: SignalSlice,
                                          dimension: str,
                                          main_window) -> Tuple[List[ClusterResult], Optional[UnclusteredPulseData]]:
        """处理单个维度的聚类
        
        Args:
            signal_slice: 信号切片实体
            dimension: 聚类维度（'CF'或'PW'）
            main_window: 主窗口实例
            
        Returns:
            tuple: (聚类结果列表, 未聚类数据实体)
        """
        try:
            # 从UI获取参数
            ui_params = UIParamsParser.get_validated_params_dict(main_window)
            
            # 获取聚类参数
            clustering_params = self.clustering_service.get_clustering_params_from_ui(ui_params, dimension)
            
            # 执行聚类
            cluster_results, unclustered_data = self.clustering_service.cluster_signal_slice(
                signal_slice, clustering_params
            )
            
            return cluster_results, unclustered_data
            
        except Exception as e:
            error_msg = f"{dimension}维度聚类失败: {str(e)}"
            system_logger.error(error_msg)
            return [], None
    
    def get_clustering_statistics(self, 
                                cluster_results: List[ClusterResult],
                                unclustered_data: Optional[UnclusteredPulseData]) -> Dict[str, int]:
        """获取聚类统计信息
        
        Args:
            cluster_results: 聚类结果列表
            unclustered_data: 未聚类数据
            
        Returns:
            Dict[str, int]: 统计信息字典
        """
        total_clusters = len(cluster_results)
        total_clustered_points = sum(len(result.cluster_data) for result in cluster_results)
        total_unclustered_points = len(unclustered_data.pulse_data) if unclustered_data else 0
        
        return {
            'total_clusters': total_clusters,
            'total_clustered_points': total_clustered_points,
            'total_unclustered_points': total_unclustered_points,
            'total_points': total_clustered_points + total_unclustered_points
        }
    
    def _log_clustering_summary(self,
                              signal_slice: SignalSlice,
                              cf_results: List[ClusterResult],
                              pw_results: List[ClusterResult],
                              cf_unclustered: Optional[UnclusteredPulseData],
                              pw_unclustered: Optional[UnclusteredPulseData]) -> None:
        """记录聚类汇总信息
        
        Args:
            signal_slice: 信号切片
            cf_results: CF聚类结果
            pw_results: PW聚类结果
            cf_unclustered: CF未聚类数据
            pw_unclustered: PW未聚类数据
        """
        cf_stats = self.get_clustering_statistics(cf_results, cf_unclustered)
        pw_stats = self.get_clustering_statistics(pw_results, pw_unclustered)
        
        system_logger.info(
            f"聚类处理完成 - 切片: {signal_slice.id}, "
            f"CF聚类: {cf_stats['total_clusters']}类/{cf_stats['total_clustered_points']}点, "
            f"PW聚类: {pw_stats['total_clusters']}类/{pw_stats['total_clustered_points']}点, "
            f"总数据点: {signal_slice.point_count}"
        )


# 使用示例
def example_usage():
    """使用示例"""
    
    # 假设已有信号切片和主窗口实例
    # signal_slice = ...
    # main_window = ...
    
    # 创建聚类集成服务
    clustering_integration = ClusteringIntegrationService()
    
    # 方式1: 处理完整的聚类流程
    # result = clustering_integration.process_signal_slice_clustering(signal_slice, main_window)
    # if result['success']:
    #     cf_results = result['cf_results']
    #     pw_results = result['pw_results']
    #     # 处理聚类结果...
    
    # 方式2: 处理单个维度聚类
    # cf_results, cf_unclustered = clustering_integration.process_single_dimension_clustering(
    #     signal_slice, 'CF', main_window
    # )
    
    pass
