"""管道运行器模块

本模块实现了增强式管道架构的核心执行引擎。
管道运行器负责按配置顺序调用处理器，并管理数据总线。
"""

from typing import Dict, List, Optional, Any

from radar_system.domain.recognition.processors.registry import PROCESSOR_REGISTRY
from radar_system.infrastructure.common.logging import system_logger


class PipelineRunner:
    """管道运行器 - 基于数据总线的流程编排
    
    负责执行管道流程，按照配置中定义的步骤顺序调用处理器。
    使用数据总线机制在处理器之间传递数据。
    
    Attributes:
        steps (List[Dict]): 管道步骤配置列表
        cache (Dict): 数据总线，存储各步骤的输出数据
    """
    
    def __init__(self, config: Dict):
        """初始化管道运行器
        
        Args:
            config (Dict): 管道配置字典，必须包含"pipeline"键
            
        Raises:
            KeyError: 当配置中缺少"pipeline"键时
        """
        if "pipeline" not in config:
            raise KeyError("配置中缺少 'pipeline' 键")
        
        self.steps: List[Dict] = config["pipeline"]
        self.cache: Dict[str, Any] = {}
        
        system_logger.info(f"管道运行器初始化完成，包含 {len(self.steps)} 个步骤")
    
    def run(self, initial_data: Optional[Dict] = None) -> Dict:
        """执行管道流程
        
        按照配置中定义的步骤顺序执行处理器，使用数据总线
        在步骤之间传递数据。
        
        Args:
            initial_data (Optional[Dict]): 初始输入数据
            
        Returns:
            Dict: 包含所有步骤输出的数据总线缓存
            
        Raises:
            RuntimeError: 当任何步骤执行失败时
        """
        # 初始化数据总线
        if initial_data:
            self.cache["input"] = initial_data
            system_logger.info("初始数据已加载到数据总线")
        
        # 按顺序执行各个步骤
        for step in self.steps:
            step_name = step["name"]
            processor_name = step["processor"]
            
            try:
                # 获取处理器实例
                processor_cls = PROCESSOR_REGISTRY[processor_name]
                processor = processor_cls()
                
                system_logger.info(f"开始执行步骤 '{step_name}' (处理器: {processor_name})")
                
                # 准备输入数据
                input_data = self._prepare_input_data(step)
                
                # 执行处理
                result = processor.run(input_data, step.get("params", {}))
                
                # 存入数据总线
                self.cache[step_name] = result
                
                system_logger.info(f"步骤 '{step_name}' 完成")
                
            except KeyError as e:
                if processor_name not in PROCESSOR_REGISTRY:
                    error_msg = f"步骤 '{step_name}' 失败: 未找到处理器 '{processor_name}'"
                else:
                    error_msg = f"步骤 '{step_name}' 失败: {str(e)}"
                system_logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            except Exception as e:
                error_msg = f"步骤 '{step_name}' 失败: {str(e)}"
                system_logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        
        system_logger.info("管道执行完成")
        return self.cache
    
    def _prepare_input_data(self, step: Dict) -> Dict:
        """准备输入数据
        
        根据步骤配置中的input_from字段，从数据总线中收集
        所需的输入数据。
        
        Args:
            step (Dict): 步骤配置字典
            
        Returns:
            Dict: 合并后的输入数据字典
            
        Raises:
            ValueError: 当依赖的数据源不存在时
        """
        input_from = step.get("input_from", [])
        input_data = {}
        
        for source in input_from:
            if source in self.cache:
                # 合并数据源的所有数据
                source_data = self.cache[source]
                if isinstance(source_data, dict):
                    input_data.update(source_data)
                else:
                    # 如果数据源不是字典，使用源名称作为键
                    input_data[source] = source_data
            else:
                raise ValueError(f"依赖数据源 '{source}' 不存在")
        
        return input_data
    
    def get_step_result(self, step_name: str) -> Optional[Any]:
        """获取指定步骤的结果
        
        Args:
            step_name (str): 步骤名称
            
        Returns:
            Optional[Any]: 步骤结果，如果步骤不存在则返回None
        """
        return self.cache.get(step_name)
    
    def clear_cache(self) -> None:
        """清空数据总线缓存"""
        self.cache.clear()
        system_logger.info("数据总线缓存已清空")
