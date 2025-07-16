"""聚类结果绘图服务

负责为聚类结果生成PA和DTOA维度的二值化图像，复用SignalPlotter的核心绘图逻辑。
"""

import numpy as np
from typing import Dict

from radar_system.domain.signal.services.plotter import SignalPlotter
from radar_system.domain.recognition.entities.cluster_result import ClusterResult
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.exceptions import ValidationError


class ClusterPlottingService:
    """聚类结果绘图服务
    
    专门为ClusterResult实体生成PA和DTOA维度的二值化图像。
    复用SignalPlotter的核心绘图逻辑，确保图像生成的一致性。
    
    Attributes:
        signal_plotter (SignalPlotter): 信号绘图器实例，用于复用绘图逻辑
    """
    
    def __init__(self):
        """初始化聚类绘图服务"""
        self.signal_plotter = SignalPlotter()
        system_logger.info("聚类绘图服务初始化完成")
    
    def plot_cluster(self, cluster_result: ClusterResult) -> Dict[str, np.ndarray]:
        """为聚类结果生成PA和DTOA维度的二值化图像
        
        Args:
            cluster_result (ClusterResult): 聚类结果实体对象
            
        Returns:
            Dict[str, np.ndarray]: 图像数据字典，包含'PA'和'DTOA'两个维度的二值化图像
            
        Raises:
            ValidationError: 当聚类结果数据无效时
        """
        try:
            # 验证输入数据
            if not isinstance(cluster_result, ClusterResult):
                raise ValidationError(f"输入必须是ClusterResult类型，实际类型: {type(cluster_result)}")
            
            if cluster_result.cluster_data.size == 0:
                raise ValidationError("聚类数据为空，无法生成图像")
            
            # 提取聚类数据
            data = cluster_result.cluster_data
            
            # 验证数据维度
            if data.ndim != 2 or data.shape[1] < 5:
                raise ValidationError(f"聚类数据维度不正确，期望(n, >=5)，实际: {data.shape}")
            
            # 提取各维度数据
            toa = data[:, 4]  # TOA数据
            pa = data[:, 3]   # PA数据
            
            # 计算DTOA（脉冲间隔时间差）
            dtoa = np.diff(toa) * 1000  # 转换为微秒
            dtoa = np.append(dtoa, 0)   # 补齐长度，最后一个脉冲的DTOA设为0
            
            # 获取时间范围
            start_time = cluster_result.time_ranges.start_time
            end_time = cluster_result.time_ranges.end_time
            
            system_logger.debug(
                f"开始绘制聚类 {cluster_result.cluster_index}: "
                f"维度={cluster_result.dim_name}, "
                f"数据点数={len(toa)}, "
                f"时间范围=[{start_time:.1f}, {end_time:.1f}]ms"
            )
            
            # 生成图像数据
            images = {}
            
            # 生成PA维度图像
            images['PA'] = self.signal_plotter._plot_dimension(
                toa, pa, toa, 'PA', start_time, end_time
            )
            
            # 生成DTOA维度图像
            images['DTOA'] = self.signal_plotter._plot_dimension(
                toa, dtoa, toa, 'DTOA', start_time, end_time
            )
            
            system_logger.info(
                f"聚类 {cluster_result.cluster_index} 图像生成完成: "
                f"PA图像尺寸={images['PA'].shape}, DTOA图像尺寸={images['DTOA'].shape}"
            )
            
            return images
            
        except Exception as e:
            error_msg = f"聚类 {cluster_result.cluster_index if 'cluster_result' in locals() else 'unknown'} 图像生成失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg)
    
    def plot_multiple_clusters(self, cluster_results: list[ClusterResult]) -> Dict[int, Dict[str, np.ndarray]]:
        """为多个聚类结果生成图像
        
        Args:
            cluster_results (List[ClusterResult]): 聚类结果列表
            
        Returns:
            Dict[int, Dict[str, np.ndarray]]: 以cluster_index为键的图像数据字典
            
        Raises:
            ValidationError: 当任何聚类结果处理失败时
        """
        try:
            if not cluster_results:
                system_logger.warning("聚类结果列表为空")
                return {}
            
            system_logger.info(f"开始批量生成 {len(cluster_results)} 个聚类的图像")
            
            all_images = {}
            failed_clusters = []
            
            for cluster_result in cluster_results:
                try:
                    images = self.plot_cluster(cluster_result)
                    all_images[cluster_result.cluster_index] = images
                except Exception as e:
                    failed_clusters.append(cluster_result.cluster_index)
                    system_logger.error(f"聚类 {cluster_result.cluster_index} 图像生成失败: {str(e)}")
            
            success_count = len(all_images)
            system_logger.info(
                f"批量图像生成完成: 成功 {success_count}/{len(cluster_results)} 个聚类"
            )
            
            if failed_clusters:
                system_logger.warning(f"失败的聚类索引: {failed_clusters}")
            
            return all_images
            
        except Exception as e:
            error_msg = f"批量图像生成失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg)
    
    def update_band_config(self, band_name: str) -> None:
        """更新波段配置
        
        Args:
            band_name (str): 波段名称
        """
        try:
            self.signal_plotter.update_band_config(band_name)
            system_logger.info(f"聚类绘图服务波段配置已更新为: {band_name}")
        except Exception as e:
            system_logger.error(f"更新波段配置失败: {str(e)}")
            raise
