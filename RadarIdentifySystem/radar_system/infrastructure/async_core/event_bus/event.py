"""事件模块

本模块定义了事件总线中使用的事件基类。
"""
from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from radar_system.infrastructure.common.logging import system_logger

@dataclass
class Event:
    """事件基类
    
    系统中所有事件的基类，定义了事件的基本属性。
    
    Attributes:
        type (str): 事件类型
        data (Dict[str, Any]): 事件数据
        id (str): 事件唯一标识符
        timestamp (datetime): 事件创建时间
        source (str): 事件源标识
    """
    type: str
    data: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = field(default="")
    
    def __post_init__(self):
        """初始化后处理
        
        验证事件类型和数据的有效性。
        
        Raises:
            ValueError: 事件类型为空时抛出
        """
        if not self.type:
            raise ValueError("事件类型不能为空")
        
        if self.data is None:
            self.data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 事件的字典表示
        """
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """从字典创建事件
        
        Args:
            data: 事件数据字典
            
        Returns:
            Event: 创建的事件实例
            
        Raises:
            ValueError: 缺少必要字段时抛出
        """
        if "type" not in data:
            raise ValueError("缺少事件类型字段")
            
        return cls(
            type=data["type"],
            data=data.get("data", {}),
            id=data.get("id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            source=data.get("source", "")
        ) 