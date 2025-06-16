"""信号处理任务模块

本模块实现了信号处理相关的异步任务。
"""
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass

from radar_system.application.services.signal_service import SignalService
from radar_system.domain.signal.entities.signal import SignalData, SignalSlice
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus
from radar_system.infrastructure.async_core.event_bus.event import Event

@dataclass
class SignalImportTask:
    """信号导入任务
    
    处理信号数据文件的导入和预处理。
    
    Attributes:
        file_path (str): 文件路径
        service (SignalService): 信号处理服务
        event_bus (EventBus): 事件总线
    """
    file_path: str
    service: SignalService
    event_bus: EventBus
    
    def execute(self) -> Tuple[bool, str, Optional[SignalData]]:
        """执行导入任务
        
        Returns:
            tuple: (是否成功, 消息, 信号数据)
        """
        try:
            # 发布任务开始事件
            self.event_bus.publish(Event(
                type="import_task_started",
                data={"file_path": self.file_path}
            ))
            
            # 加载文件
            success, message, signal = self.service.load_signal_file(self.file_path)
            if not success:
                return False, message, None
                
            # 发布任务完成事件
            self.event_bus.publish(Event(
                type="import_task_completed",
                data={
                    "signal_id": signal.id,
                    "data_count": signal.data_count,
                    "band_type": signal.band_type
                }
            ))
            
            return True, "导入完成", signal
            
        except Exception as e:
            error_msg = f"导入任务执行出错: {str(e)}"
            system_logger.error(error_msg)
            self.event_bus.publish(Event(
                type="import_task_failed",
                data={
                    "file_path": self.file_path,
                    "error": error_msg
                }
            ))
            return False, error_msg, None

@dataclass
class SignalSliceTask:
    """信号切片任务
    
    执行信号数据的切片处理。
    
    Attributes:
        signal (SignalData): 待切片的信号数据
        service (SignalService): 信号处理服务
        event_bus (EventBus): 事件总线
    """
    signal: SignalData
    service: SignalService
    event_bus: EventBus
    
    def execute(self) -> Tuple[bool, str, Optional[List[SignalSlice]]]:
        """执行切片任务
        
        Returns:
            tuple: (是否成功, 消息, 切片列表)
        """
        try:
            # 发布任务开始事件
            self.event_bus.publish(Event(
                type="slice_task_started",
                data={"signal_id": self.signal.id}
            ))
            
            # 执行切片
            success, message, slices = self.service.start_slice_processing(self.signal)
            if not success:
                return False, message, None
                
            # 发布任务完成事件
            self.event_bus.publish(Event(
                type="slice_task_completed",
                data={
                    "signal_id": self.signal.id,
                    "slice_count": len(slices)
                }
            ))
            
            return True, "切片完成", slices
            
        except Exception as e:
            error_msg = f"切片任务执行出错: {str(e)}"
            system_logger.error(error_msg)
            self.event_bus.publish(Event(
                type="slice_task_failed",
                data={
                    "signal_id": self.signal.id,
                    "error": error_msg
                }
            ))
            return False, error_msg, None


