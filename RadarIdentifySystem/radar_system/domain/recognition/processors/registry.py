"""处理器注册机制模块

本模块实现了处理器的注册和管理功能，提供装饰器模式的注册机制。
"""

from typing import Dict, Type, Callable, Any

# 全局处理器注册表
PROCESSOR_REGISTRY: Dict[str, Type] = {}


def register_processor(name: str) -> Callable[[Type], Type]:
    """处理器注册装饰器
    
    用于将处理器类注册到全局注册表中。使用装饰器模式，
    可以在类定义时自动完成注册。
    
    Args:
        name (str): 处理器的注册名称，用于在配置中引用
        
    Returns:
        Callable[[Type], Type]: 装饰器函数
        
    Example:
        @register_processor("cf_clustering")
        class CFClusteringProcessor(BaseProcessor):
            pass
    """
    def decorator(cls: Type) -> Type:
        """装饰器内部函数
        
        Args:
            cls (Type): 被装饰的处理器类
            
        Returns:
            Type: 原始的处理器类（不做修改）
        """
        PROCESSOR_REGISTRY[name] = cls
        return cls
    
    return decorator


def get_processor(name: str) -> Type:
    """获取已注册的处理器类
    
    Args:
        name (str): 处理器的注册名称
        
    Returns:
        Type: 对应的处理器类
        
    Raises:
        KeyError: 当处理器名称未注册时
    """
    if name not in PROCESSOR_REGISTRY:
        raise KeyError(f"未找到名为 '{name}' 的处理器")
    return PROCESSOR_REGISTRY[name]


def list_processors() -> Dict[str, Type]:
    """列出所有已注册的处理器
    
    Returns:
        Dict[str, Type]: 处理器名称到类的映射字典
    """
    return PROCESSOR_REGISTRY.copy()
