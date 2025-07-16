"""聚类处理示例

演示如何使用增强式管道架构处理聚类结果的"一对多"数据流转。
"""

from typing import List, Dict
from radar_system.domain.recognition.entities.cluster_result import ClusterResult
from radar_system.domain.recognition.services.pipeline_runner import PipelineRunner
from radar_system.infrastructure.config.pipeline_loader import PipelineConfigLoader
from radar_system.infrastructure.common.logging import system_logger


class ClusterProcessingExample:
    """聚类处理示例类
    
    演示如何在应用层处理List[ClusterResult]的批量数据流转。
    """
    
    def __init__(self):
        """初始化示例"""
        # 加载聚类处理管道配置
        self.config_loader = PipelineConfigLoader()
        self.cluster_pipeline_config = self.config_loader.get_pipeline_config("cluster_processing")
        
        system_logger.info("聚类处理示例初始化完成")
    
    def process_single_cluster(self, cluster_result: ClusterResult) -> Dict:
        """处理单个聚类结果
        
        Args:
            cluster_result (ClusterResult): 单个聚类结果
            
        Returns:
            Dict: 处理结果，包含所有管道步骤的输出
        """
        try:
            # 创建管道运行器
            runner = PipelineRunner(self.cluster_pipeline_config)
            
            # 执行管道处理
            result = runner.run({"cluster_result": cluster_result})
            
            system_logger.info(
                f"聚类 {cluster_result.cluster_index} 处理完成: "
                f"步骤={list(result.keys())}"
            )
            
            return result
            
        except Exception as e:
            system_logger.error(f"聚类 {cluster_result.cluster_index} 处理失败: {str(e)}")
            raise
    
    def process_multiple_clusters(self, cluster_results: List[ClusterResult]) -> List[Dict]:
        """处理多个聚类结果
        
        这是解决"一对多"数据流转的核心方法：
        在应用层循环调用单元处理管道。
        
        Args:
            cluster_results (List[ClusterResult]): 聚类结果列表
            
        Returns:
            List[Dict]: 所有聚类的处理结果列表
        """
        try:
            if not cluster_results:
                system_logger.warning("聚类结果列表为空")
                return []
            
            system_logger.info(f"开始批量处理 {len(cluster_results)} 个聚类")
            
            all_results = []
            failed_clusters = []
            
            for i, cluster_result in enumerate(cluster_results):
                try:
                    # 处理单个聚类
                    result = self.process_single_cluster(cluster_result)
                    all_results.append(result)
                    
                    system_logger.debug(f"进度: {i+1}/{len(cluster_results)}")
                    
                except Exception as e:
                    failed_clusters.append(cluster_result.cluster_index)
                    system_logger.error(f"聚类 {cluster_result.cluster_index} 处理失败: {str(e)}")
                    # 继续处理其他聚类
                    continue
            
            success_count = len(all_results)
            system_logger.info(
                f"批量处理完成: 成功 {success_count}/{len(cluster_results)} 个聚类"
            )
            
            if failed_clusters:
                system_logger.warning(f"失败的聚类索引: {failed_clusters}")
            
            return all_results
            
        except Exception as e:
            system_logger.error(f"批量处理失败: {str(e)}")
            raise
    
    def extract_cluster_images(self, processing_results: List[Dict]) -> Dict[int, Dict[str, any]]:
        """从处理结果中提取聚类图像
        
        Args:
            processing_results (List[Dict]): 管道处理结果列表
            
        Returns:
            Dict[int, Dict[str, any]]: 以cluster_index为键的图像数据字典
        """
        try:
            cluster_images = {}
            
            for result in processing_results:
                # 从管道结果中提取图像数据
                if "plotting" in result and "cluster_images" in result["plotting"]:
                    plotting_result = result["plotting"]
                    images = plotting_result["cluster_images"]
                    
                    # 假设我们可以从输入数据中获取cluster_index
                    # 实际实现中可能需要在管道中传递更多元数据
                    if "input" in result and "cluster_result" in result["input"]:
                        cluster_index = result["input"]["cluster_result"].cluster_index
                        cluster_images[cluster_index] = images
            
            system_logger.info(f"提取到 {len(cluster_images)} 个聚类的图像数据")
            return cluster_images
            
        except Exception as e:
            system_logger.error(f"提取聚类图像失败: {str(e)}")
            raise


def main():
    """主函数 - 演示完整的聚类处理流程"""
    try:
        # 创建处理示例
        processor = ClusterProcessingExample()
        
        # 模拟聚类结果数据（实际使用中来自CF/PW聚类处理器）
        # cluster_results = get_cluster_results_from_clustering()
        
        # 处理多个聚类
        # processing_results = processor.process_multiple_clusters(cluster_results)
        
        # 提取图像数据
        # cluster_images = processor.extract_cluster_images(processing_results)
        
        system_logger.info("聚类处理示例演示完成")
        
    except Exception as e:
        system_logger.error(f"示例执行失败: {str(e)}")
        raise


if __name__ == "__main__":
    main()
