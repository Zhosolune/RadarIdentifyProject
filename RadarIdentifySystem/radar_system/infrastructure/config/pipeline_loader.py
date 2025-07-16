"""管道配置加载器

本模块实现了管道配置文件的加载和验证功能，
支持YAML格式的配置文件加载和参数验证。
"""

import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path

from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.exceptions import ValidationError


class PipelineConfigLoader:
    """管道配置加载器
    
    负责加载和验证管道配置文件，提供配置文件的读取、
    验证和默认值处理功能。
    
    Attributes:
        config_path (Path): 配置文件路径
        _config_cache (Optional[Dict]): 配置缓存
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置加载器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 使用默认配置文件路径
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / "configs" / "recognition_pipelines.yaml"
        
        self.config_path = Path(config_path)
        self._config_cache: Optional[Dict] = None
        
        system_logger.info(f"管道配置加载器初始化，配置文件: {self.config_path}")
    
    def load_config(self, force_reload: bool = False) -> Dict:
        """加载配置文件
        
        Args:
            force_reload: 是否强制重新加载配置文件
            
        Returns:
            Dict: 配置字典
            
        Raises:
            ValidationError: 当配置文件不存在或格式错误时
        """
        if self._config_cache is not None and not force_reload:
            return self._config_cache
        
        try:
            if not self.config_path.exists():
                raise ValidationError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            if config is None:
                raise ValidationError("配置文件为空")
            
            # 验证配置格式
            self._validate_config(config)
            
            # 缓存配置
            self._config_cache = config
            
            system_logger.info(f"配置文件加载成功: {self.config_path}")
            return config
            
        except yaml.YAMLError as e:
            error_msg = f"配置文件格式错误: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg) from e
        except Exception as e:
            error_msg = f"配置文件加载失败: {str(e)}"
            system_logger.error(error_msg)
            raise ValidationError(error_msg) from e
    
    def get_pipeline_config(self, pipeline_name: str) -> Dict:
        """获取指定管道的配置
        
        Args:
            pipeline_name: 管道名称
            
        Returns:
            Dict: 管道配置字典
            
        Raises:
            ValidationError: 当管道不存在时
        """
        config = self.load_config()
        
        if "recognition_pipelines" not in config:
            raise ValidationError("配置文件中缺少 'recognition_pipelines' 节点")
        
        pipelines = config["recognition_pipelines"]
        
        if pipeline_name not in pipelines:
            available_pipelines = list(pipelines.keys())
            raise ValidationError(f"管道 '{pipeline_name}' 不存在，可用管道: {available_pipelines}")
        
        pipeline_config = pipelines[pipeline_name]
        
        # 验证管道配置
        self._validate_pipeline_config(pipeline_config, pipeline_name)
        
        return pipeline_config
    
    def list_available_pipelines(self) -> List[str]:
        """列出所有可用的管道
        
        Returns:
            List[str]: 管道名称列表
        """
        config = self.load_config()
        
        if "recognition_pipelines" not in config:
            return []
        
        return list(config["recognition_pipelines"].keys())
    
    def get_default_pipeline_name(self) -> str:
        """获取默认管道名称
        
        Returns:
            str: 默认管道名称
        """
        config = self.load_config()
        return config.get("default_pipeline", "default")
    
    def get_parameter_constraints(self) -> Dict:
        """获取参数约束配置
        
        Returns:
            Dict: 参数约束字典
        """
        config = self.load_config()
        return config.get("parameter_constraints", {})
    
    def validate_parameters(self, params: Dict) -> bool:
        """验证参数是否符合约束
        
        Args:
            params: 待验证的参数字典
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            ValidationError: 当参数不符合约束时
        """
        constraints = self.get_parameter_constraints()
        
        for param_name, param_value in params.items():
            if param_name in constraints:
                constraint = constraints[param_name]
                
                # 检查最小值
                if "min" in constraint and param_value < constraint["min"]:
                    raise ValidationError(f"参数 {param_name} 值 {param_value} 小于最小值 {constraint['min']}")
                
                # 检查最大值
                if "max" in constraint and param_value > constraint["max"]:
                    raise ValidationError(f"参数 {param_name} 值 {param_value} 大于最大值 {constraint['max']}")
        
        return True
    
    def _validate_config(self, config: Dict) -> None:
        """验证配置文件格式
        
        Args:
            config: 配置字典
            
        Raises:
            ValidationError: 当配置格式错误时
        """
        if "recognition_pipelines" not in config:
            raise ValidationError("配置文件中缺少 'recognition_pipelines' 节点")
        
        pipelines = config["recognition_pipelines"]
        if not isinstance(pipelines, dict):
            raise ValidationError("'recognition_pipelines' 必须是字典类型")
        
        if not pipelines:
            raise ValidationError("至少需要定义一个管道")
    
    def _validate_pipeline_config(self, pipeline_config: Dict, pipeline_name: str) -> None:
        """验证单个管道配置
        
        Args:
            pipeline_config: 管道配置字典
            pipeline_name: 管道名称
            
        Raises:
            ValidationError: 当管道配置错误时
        """
        required_fields = ["name", "description", "pipeline"]
        
        for field in required_fields:
            if field not in pipeline_config:
                raise ValidationError(f"管道 '{pipeline_name}' 缺少必需字段: {field}")
        
        pipeline_steps = pipeline_config["pipeline"]
        if not isinstance(pipeline_steps, list):
            raise ValidationError(f"管道 '{pipeline_name}' 的 'pipeline' 字段必须是列表类型")
        
        if not pipeline_steps:
            raise ValidationError(f"管道 '{pipeline_name}' 至少需要定义一个步骤")
        
        # 验证每个步骤
        for i, step in enumerate(pipeline_steps):
            self._validate_step_config(step, pipeline_name, i)
    
    def _validate_step_config(self, step: Dict, pipeline_name: str, step_index: int) -> None:
        """验证步骤配置
        
        Args:
            step: 步骤配置字典
            pipeline_name: 管道名称
            step_index: 步骤索引
            
        Raises:
            ValidationError: 当步骤配置错误时
        """
        required_fields = ["name", "processor", "input_from"]
        
        for field in required_fields:
            if field not in step:
                raise ValidationError(f"管道 '{pipeline_name}' 步骤 {step_index} 缺少必需字段: {field}")
        
        if not isinstance(step["input_from"], list):
            raise ValidationError(f"管道 '{pipeline_name}' 步骤 {step_index} 的 'input_from' 字段必须是列表类型")
