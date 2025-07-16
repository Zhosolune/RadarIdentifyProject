"""处理器抽象基类模块

本模块定义了增强式管道架构中处理器的抽象基类。
所有具体的处理器都必须继承此基类并实现其抽象方法。
"""

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseProcessor(ABC):
    """处理器抽象基类
    
    定义了管道处理器的标准接口。所有具体处理器都必须继承此类
    并实现run方法来执行具体的处理逻辑。
    
    Attributes:
        required_inputs (List[str]): 必需的输入字段列表
        optional_inputs (List[str]): 可选的输入字段列表  
        output_fields (List[str]): 输出字段列表
    """
    
    required_inputs: List[str] = []
    optional_inputs: List[str] = []
    output_fields: List[str] = []
    
    @abstractmethod
    def run(self, data: Dict, params: Dict) -> Dict:
        """执行处理逻辑
        
        Args:
            data (Dict): 输入数据字典
            params (Dict): 处理参数字典
            
        Returns:
            Dict: 处理结果字典
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        pass
    
    def validate_inputs(self, data: Dict) -> None:
        """验证输入数据
        
        检查输入数据是否包含所有必需的字段。
        
        Args:
            data (Dict): 待验证的输入数据字典
            
        Raises:
            KeyError: 当缺少必需输入字段时
        """
        for field in self.required_inputs:
            if field not in data:
                raise KeyError(f"缺少必需输入: {field}")
