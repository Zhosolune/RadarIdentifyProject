"""CF维度聚类处理器

本模块实现了CF（载频）维度的DBSCAN聚类处理器，
作为增强式管道架构中的第一阶段聚类处理组件。
"""

from typing import Dict, List, Optional
import numpy as np

from radar_system.domain.recognition.processors.base_processor import BaseProcessor
from radar_system.domain.recognition.processors.registry import register_processor
from radar_system.domain.recognition.services.clustering_service import DBSCANClusteringService, ClusteringParams
from radar_system.domain.signal.entities.signal import SignalSlice
from radar_system.domain.recognition.entities.cluster_result import ClusterResult, UnclusteredPulseData
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.exceptions import ValidationError


@register_processor("cf_clustering")
class CFClusteringProcessor(BaseProcessor):
    """CF维度聚类处理器
    
    执行CF（载频）维度的DBSCAN聚类，作为两阶段聚类流程的第一阶段。
    处理SignalSlice数据，输出聚类成功的结果和未聚类的数据。
    
    Attributes:
        required_inputs (List[str]): 必需输入字段 ["slice_data"]
        output_fields (List[str]): 输出字段 ["cf_clusters", "cf_statistics", "unclustered_data"]
    """
    
    required_inputs = ["slice_data"]
    output_fields = ["cf_clusters", "cf_statistics", "unclustered_data"]
    
    def __init__(self):
        """初始化CF聚类处理器"""
        self.clustering_service = DBSCANClusteringService()
        system_logger.info("CF聚类处理器初始化完成")
    
    def run(self, data: Dict, params: Dict) -> Dict:
        """执行CF维度聚类处理
        
        Args:
            data (Dict): 输入数据字典，必须包含:
                - slice_data: SignalSlice实体对象
            params (Dict): 处理参数字典，支持:
                - epsilon_CF: CF维度邻域半径，默认2.0
                - min_pts: 最小点数，默认3
                
        Returns:
            Dict: 处理结果字典，包含:
                - cf_clusters: List[ClusterResult] - CF聚类结果列表
                - cf_statistics: Dict - CF聚类统计信息
                - unclustered_data: Optional[UnclusteredPulseData] - 未聚类数据
                
        Raises:
            ValidationError: 当输入数据无效或聚类失败时
        """
        try:
            # 验证输入数据是否完整
            self.validate_inputs(data)
            
            # 获取输入数据
            slice_data = data["slice_data"]
            if not isinstance(slice_data, SignalSlice):
                raise ValidationError(f"slice_data必须是SignalSlice类型，实际类型: {type(slice_data)}")
            
            # 获取聚类参数
            epsilon_cf = params.get("epsilon_CF", 2.0)
            min_pts = params.get("min_pts", 3)
            
            system_logger.info(f"开始CF维度聚类，参数: epsilon_CF={epsilon_cf}, min_pts={min_pts}")
            
            # 创建聚类参数
            clustering_params = ClusteringParams(
                eps=epsilon_cf,
                min_samples=min_pts,
                dimension='CF'
            )
            
            # 执行CF聚类
            cf_clusters, unclustered_data = self.clustering_service.cluster_signal_slice(
                slice_data, clustering_params
            )
            
            # 计算统计信息
            cf_statistics = self._calculate_statistics(cf_clusters, unclustered_data, slice_data)
            
            # 记录聚类结果
            system_logger.info(f"CF聚类完成: 成功聚类{len(cf_clusters)}个，"
                             f"未聚类数据{unclustered_data.get_pulse_count() if unclustered_data else 0}个脉冲")
            
            return {
                "cf_clusters": cf_clusters,
                "cf_statistics": cf_statistics,
                "unclustered_data": unclustered_data
            }
            
        except Exception as e:
            error_msg = f"CF聚类处理失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg) from e
    
    def _calculate_statistics(self, 
                            cf_clusters: List[ClusterResult], 
                            unclustered_data: Optional[UnclusteredPulseData],
                            slice_data: SignalSlice) -> Dict:
        """计算CF聚类统计信息
        
        Args:
            cf_clusters: CF聚类结果列表
            unclustered_data: 未聚类数据
            slice_data: 原始切片数据
            
        Returns:
            Dict: 统计信息字典
        """
        total_pulses = slice_data.data.shape[0] if not slice_data.is_empty else 0
        clustered_pulses = sum(cluster.cluster_data.shape[0] for cluster in cf_clusters)
        unclustered_pulses = unclustered_data.get_pulse_count() if unclustered_data else 0
        
        # 计算聚类效率
        clustering_efficiency = (clustered_pulses / total_pulses * 100) if total_pulses > 0 else 0
        
        # 计算平均聚类大小
        avg_cluster_size = (clustered_pulses / len(cf_clusters)) if cf_clusters else 0
        
        statistics = {
            "total_clusters": len(cf_clusters),
            "total_pulses": total_pulses,
            "clustered_pulses": clustered_pulses,
            "unclustered_pulses": unclustered_pulses,
            "clustering_efficiency": round(clustering_efficiency, 2),
            "average_cluster_size": round(avg_cluster_size, 2),
            "dimension": "CF",
            "slice_index": slice_data.slice_index
        }
        
        return statistics
