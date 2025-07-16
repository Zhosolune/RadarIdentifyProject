"""处理器模块

本模块包含增强式管道架构的处理器相关组件。
"""

from .base_processor import BaseProcessor
from .registry import PROCESSOR_REGISTRY, register_processor

__all__ = [
    'BaseProcessor',
    'PROCESSOR_REGISTRY', 
    'register_processor'
]
