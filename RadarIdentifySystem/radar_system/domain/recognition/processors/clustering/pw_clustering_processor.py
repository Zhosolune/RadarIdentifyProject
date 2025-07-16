"""PW维度聚类处理器

本模块实现了PW（脉宽）维度的DBSCAN聚类处理器，
作为增强式管道架构中的第二阶段聚类处理组件。
"""

from typing import Dict, List, Optional
import numpy as np

from radar_system.domain.recognition.processors.base_processor import BaseProcessor
from radar_system.domain.recognition.processors.registry import register_processor
from radar_system.domain.recognition.services.clustering_service import ClusteringParams
from radar_system.domain.recognition.services.unclustered_data_clustering_service import UnclusteredDataClusteringService

from radar_system.domain.recognition.entities.cluster_result import ClusterResult, UnclusteredPulseData
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.exceptions import ValidationError


@register_processor("pw_clustering")
class PWClusteringProcessor(BaseProcessor):
    """PW维度聚类处理器
    
    执行PW（脉宽）维度的DBSCAN聚类，作为两阶段聚类流程的第二阶段。
    处理CF聚类失败的未聚类数据，输出PW聚类成功的结果和最终未聚类的数据。
    
    Attributes:
        required_inputs (List[str]): 必需输入字段 ["unclustered_data"]
        output_fields (List[str]): 输出字段 ["pw_clusters", "pw_statistics", "final_unclustered_data"]
    """
    
    required_inputs = ["unclustered_data"]
    output_fields = ["pw_clusters", "pw_statistics", "final_unclustered_data"]
    
    def __init__(self):
        """初始化PW聚类处理器"""
        self.clustering_service = UnclusteredDataClusteringService()
        system_logger.info("PW聚类处理器初始化完成")
    
    def run(self, data: Dict, params: Dict) -> Dict:
        """执行PW维度聚类处理
        
        Args:
            data (Dict): 输入数据字典，必须包含:
                - unclustered_data: UnclusteredPulseData实体对象（来自CF聚类）
            params (Dict): 处理参数字典，支持:
                - epsilon_PW: PW维度邻域半径，默认0.2
                - min_pts: 最小点数，默认3
                
        Returns:
            Dict: 处理结果字典，包含:
                - pw_clusters: List[ClusterResult] - PW聚类结果列表
                - pw_statistics: Dict - PW聚类统计信息
                - final_unclustered_data: Optional[UnclusteredPulseData] - 最终未聚类数据
                
        Raises:
            ValidationError: 当输入数据无效或聚类失败时
        """
        try:
            # 验证输入数据
            self.validate_inputs(data)
            
            # 获取输入数据
            unclustered_data = data["unclustered_data"]
            
            # 检查是否有未聚类数据需要处理
            if unclustered_data is None:
                system_logger.info("没有未聚类数据，跳过PW聚类处理")
                return {
                    "pw_clusters": [],
                    "pw_statistics": self._create_empty_statistics(),
                    "final_unclustered_data": None
                }
            
            if not isinstance(unclustered_data, UnclusteredPulseData):
                raise ValidationError(f"unclustered_data必须是UnclusteredPulseData类型，实际类型: {type(unclustered_data)}")
            
            # 检查数据是否准备好进行下一维度聚类
            if not unclustered_data.is_ready_for_next_dimension():
                system_logger.warning("未聚类数据未准备好进行PW维度聚类")
                return {
                    "pw_clusters": [],
                    "pw_statistics": self._create_empty_statistics(),
                    "final_unclustered_data": unclustered_data
                }
            
            # 获取聚类参数
            epsilon_pw = params.get("epsilon_PW", 0.2)
            min_pts = params.get("min_pts", 3)
            
            system_logger.info(f"开始PW维度聚类，参数: epsilon_PW={epsilon_pw}, min_pts={min_pts}")
            
            # 创建聚类参数
            clustering_params = ClusteringParams(
                eps=epsilon_pw,
                min_samples=min_pts,
                dimension='PW'
            )

            # 执行PW聚类 - 使用专门的未聚类数据聚类服务
            pw_clusters, final_unclustered_data = self.clustering_service.cluster_unclustered_data(
                unclustered_data, clustering_params
            )
            
            # 计算统计信息
            pw_statistics = self._calculate_statistics(pw_clusters, final_unclustered_data, unclustered_data)
            
            # 记录聚类结果
            system_logger.info(f"PW聚类完成: 成功聚类{len(pw_clusters)}个，"
                             f"最终未聚类数据{final_unclustered_data.get_pulse_count() if final_unclustered_data else 0}个脉冲")
            
            return {
                "pw_clusters": pw_clusters,
                "pw_statistics": pw_statistics,
                "final_unclustered_data": final_unclustered_data
            }
            
        except Exception as e:
            error_msg = f"PW聚类处理失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg) from e
    

    
    def _calculate_statistics(self, 
                            pw_clusters: List[ClusterResult], 
                            final_unclustered_data: Optional[UnclusteredPulseData],
                            original_unclustered_data: UnclusteredPulseData) -> Dict:
        """计算PW聚类统计信息
        
        Args:
            pw_clusters: PW聚类结果列表
            final_unclustered_data: 最终未聚类数据
            original_unclustered_data: 原始未聚类数据
            
        Returns:
            Dict: 统计信息字典
        """
        total_pulses = original_unclustered_data.get_pulse_count()
        clustered_pulses = sum(cluster.cluster_data.shape[0] for cluster in pw_clusters)
        final_unclustered_pulses = final_unclustered_data.get_pulse_count() if final_unclustered_data else 0
        
        # 计算聚类效率
        clustering_efficiency = (clustered_pulses / total_pulses * 100) if total_pulses > 0 else 0
        
        # 计算平均聚类大小
        avg_cluster_size = (clustered_pulses / len(pw_clusters)) if pw_clusters else 0
        
        statistics = {
            "total_clusters": len(pw_clusters),
            "total_pulses": total_pulses,
            "clustered_pulses": clustered_pulses,
            "final_unclustered_pulses": final_unclustered_pulses,
            "clustering_efficiency": round(clustering_efficiency, 2),
            "average_cluster_size": round(avg_cluster_size, 2),
            "dimension": "PW",
            "slice_index": original_unclustered_data.slice_index,
            "previous_successful_clusters": original_unclustered_data.successful_cluster_count
        }
        
        return statistics
    
    def _create_empty_statistics(self) -> Dict:
        """创建空的统计信息
        
        Returns:
            Dict: 空的统计信息字典
        """
        return {
            "total_clusters": 0,
            "total_pulses": 0,
            "clustered_pulses": 0,
            "final_unclustered_pulses": 0,
            "clustering_efficiency": 0.0,
            "average_cluster_size": 0.0,
            "dimension": "PW",
            "slice_index": -1,
            "previous_successful_clusters": 0
        }
