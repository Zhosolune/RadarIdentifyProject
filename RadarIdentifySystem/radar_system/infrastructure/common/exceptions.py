"""
异常处理模块

本模块定义了系统中使用的所有异常类，提供统一的异常处理机制。
"""
from typing import Optional, Any, Dict


class RadarSystemException(Exception):
    """雷达系统基础异常类
    
    所有自定义异常的基类，提供基础的异常功能。
    
    Attributes:
        message: 异常信息
        code: 异常代码
        details: 详细信息字典
    """
    
    def __init__(self, 
                 message: str, 
                 code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None) -> None:
        """初始化异常实例
        
        Args:
            message: 异常信息
            code: 异常代码，默认为None
            details: 详细信息字典，默认为None
        """
        self.message = message
        self.code = code or "RADAR_SYSTEM_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """返回异常的字符串表示
        
        Returns:
            str: 格式化的异常信息
        """
        error_msg = f"[{self.code}] {self.message}"
        if self.details:
            error_msg += f"\nDetails: {self.details}"
        return error_msg


class ValidationError(RadarSystemException):
    """数据验证异常
    
    当数据验证失败时抛出此异常。
    """
    
    def __init__(self, 
                 message: str, 
                 field: Optional[str] = None, 
                 value: Any = None) -> None:
        """初始化验证异常
        
        Args:
            message: 验证错误信息
            field: 验证失败的字段名
            value: 导致验证失败的值
        """
        details = {
            "field": field,
            "invalid_value": value
        }
        super().__init__(message, "VALIDATION_ERROR", details)


class ConfigError(RadarSystemException):
    """配置错误异常
    
    当配置加载或验证失败时抛出此异常。
    """
    
    def __init__(self, 
                 message: str, 
                 config_key: Optional[str] = None) -> None:
        """初始化配置异常
        
        Args:
            message: 配置错误信息
            config_key: 出错的配置键
        """
        details = {"config_key": config_key} if config_key else {}
        super().__init__(message, "CONFIG_ERROR", details)


class ProcessingError(RadarSystemException):
    """处理错误异常
    
    当信号处理过程中发生错误时抛出此异常。
    """
    
    def __init__(self, 
                 message: str, 
                 step: Optional[str] = None, 
                 data_id: Optional[str] = None) -> None:
        """初始化处理异常
        
        Args:
            message: 处理错误信息
            step: 处理步骤名称
            data_id: 相关数据ID
        """
        details = {
            "processing_step": step,
            "data_id": data_id
        }
        super().__init__(message, "PROCESSING_ERROR", details)


class ResourceError(RadarSystemException):
    """资源错误异常
    
    当系统资源访问或管理出现问题时抛出此异常。
    """
    
    def __init__(self, 
                 message: str, 
                 resource_type: Optional[str] = None, 
                 resource_id: Optional[str] = None) -> None:
        """初始化资源异常
        
        Args:
            message: 资源错误信息
            resource_type: 资源类型
            resource_id: 资源标识
        """
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        super().__init__(message, "RESOURCE_ERROR", details)


class ModelError(RadarSystemException):
    """模型错误异常
    
    当模型加载或推理过程中出现错误时抛出此异常。
    """
    
    def __init__(self, 
                 message: str, 
                 model_name: Optional[str] = None, 
                 operation: Optional[str] = None) -> None:
        """初始化模型异常
        
        Args:
            message: 模型错误信息
            model_name: 模型名称
            operation: 操作类型
        """
        details = {
            "model_name": model_name,
            "operation": operation
        }
        super().__init__(message, "MODEL_ERROR", details)


class UIError(RadarSystemException):
    """UI错误异常
    
    当UI相关操作出现错误时抛出此异常。
    """
    
    def __init__(self, 
                 message: str, 
                 component: Optional[str] = None, 
                 action: Optional[str] = None) -> None:
        """初始化UI异常
        
        Args:
            message: UI错误信息
            component: UI组件名称
            action: 操作类型
        """
        details = {
            "component": component,
            "action": action
        }
        super().__init__(message, "UI_ERROR", details)


class RepositoryError(RadarSystemException):
    """仓储层错误异常
    
    当数据仓储操作出现错误时抛出此异常。
    """
    
    def __init__(self, 
                 message: str, 
                 operation: Optional[str] = None,
                 entity_type: Optional[str] = None,
                 entity_id: Optional[str] = None) -> None:
        """初始化仓储异常
        
        Args:
            message: 仓储错误信息
            operation: 操作类型(如save, find, update, delete等)
            entity_type: 实体类型
            entity_id: 实体ID
        """
        details = {
            "operation": operation,
            "entity_type": entity_type,
            "entity_id": entity_id
        }
        super().__init__(message, "REPOSITORY_ERROR", details)
