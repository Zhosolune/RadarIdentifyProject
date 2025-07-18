"""模块基类

本模块定义了模块化算法流程架构的基础模块类。
所有具体处理模块都应继承自该基类，并实现run方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseModule(ABC):
    """模块基类
    
    定义了模块的标准接口，所有具体处理模块都应继承自该基类，
    并实现run方法来执行具体的处理逻辑。
    
    Attributes:
        name (str): 模块名称
    """
    
    
    @abstractmethod
    def run(self, input_data: Any, context: Dict[str, Any]) -> Any:
        raise NotImplementedError
