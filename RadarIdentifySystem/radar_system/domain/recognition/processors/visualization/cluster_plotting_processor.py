"""聚类绘图处理器

本模块实现了聚类结果的图像生成处理器，
作为增强式管道架构中的可视化处理组件。
"""

from typing import Dict

from radar_system.domain.recognition.processors.base_processor import BaseProcessor
from radar_system.domain.recognition.processors.registry import register_processor
from radar_system.domain.recognition.services.cluster_plotting_service import ClusterPlottingService
from radar_system.domain.recognition.entities.cluster_result import ClusterResult
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.exceptions import ValidationError


@register_processor("cluster_plotting")
class ClusterPlottingProcessor(BaseProcessor):
    """聚类绘图处理器
    
    负责为单个ClusterResult生成PA和DTOA维度的二值化图像。
    生成的图像将作为后续图像识别流程的输入。
    
    Attributes:
        required_inputs (List[str]): 必需输入字段 ["cluster_result"]
        output_fields (List[str]): 输出字段 ["cluster_images"]
    """
    
    required_inputs = ["cluster_result"]
    output_fields = ["cluster_images"]
    
    def __init__(self):
        """初始化聚类绘图处理器"""
        self.plotting_service = ClusterPlottingService()
        system_logger.info("聚类绘图处理器初始化完成")
    
    def run(self, data: Dict, params: Dict) -> Dict:
        """执行聚类图像生成处理
        
        Args:
            data (Dict): 输入数据字典，必须包含:
                - cluster_result: ClusterResult实体对象
            params (Dict): 处理参数字典，支持:
                - band_name: 波段名称，用于更新绘图配置（可选）
                
        Returns:
            Dict: 处理结果字典，包含:
                - cluster_images: Dict[str, np.ndarray] - 包含PA和DTOA维度的图像数据
                
        Raises:
            ValidationError: 当输入数据无效或图像生成失败时
        """
        try:
            # 验证输入数据是否完整
            self.validate_inputs(data)
            
            # 获取输入数据
            cluster_result = data["cluster_result"]
            if not isinstance(cluster_result, ClusterResult):
                raise ValidationError(f"cluster_result必须是ClusterResult类型，实际类型: {type(cluster_result)}")
            
            # 更新波段配置（如果提供）
            band_name = params.get("band_name")
            if band_name:
                self.plotting_service.update_band_config(band_name)
                system_logger.debug(f"已更新波段配置为: {band_name}")
            
            system_logger.info(
                f"开始生成聚类图像: cluster_index={cluster_result.cluster_index}, "
                f"dim_name={cluster_result.dim_name}, "
                f"data_points={cluster_result.cluster_data.shape[0]}"
            )
            
            # 生成聚类图像
            cluster_images = self.plotting_service.plot_cluster(cluster_result)
            
            # 验证输出结果
            if not cluster_images or not all(key in cluster_images for key in ['PA', 'DTOA']):
                raise ValidationError("图像生成失败：缺少必需的PA或DTOA维度图像")
            
            system_logger.info(
                f"聚类图像生成完成: cluster_index={cluster_result.cluster_index}, "
                f"生成维度={list(cluster_images.keys())}"
            )
            
            return {
                "cluster_images": cluster_images
            }
            
        except Exception as e:
            error_msg = f"聚类绘图处理失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg)
