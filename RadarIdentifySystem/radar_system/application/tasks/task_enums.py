"""任务相关枚举定义

本模块定义应用层任务管理相关的枚举类型。
"""

from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举
    
    定义任务在生命周期中的各种状态。
    """
    PENDING = "pending"           # 等待执行
    RUNNING = "running"           # 正在执行
    PAUSED = "paused"            # 已暂停
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 执行失败
    CANCELLED = "cancelled"       # 已取消
    
    @property
    def display_name(self) -> str:
        """返回状态的显示名称"""
        display_names = {
            TaskStatus.PENDING: "等待执行",
            TaskStatus.RUNNING: "正在执行", 
            TaskStatus.PAUSED: "已暂停",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "执行失败",
            TaskStatus.CANCELLED: "已取消"
        }
        return display_names[self]
    
    @property
    def is_active(self) -> bool:
        """判断任务是否处于活跃状态"""
        return self in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.PAUSED]
    
    @property
    def is_finished(self) -> bool:
        """判断任务是否已结束"""
        return self in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1      # 低优先级
    NORMAL = 2   # 普通优先级
    HIGH = 3     # 高优先级
    URGENT = 4   # 紧急优先级
    
    @property
    def display_name(self) -> str:
        """返回优先级的显示名称"""
        display_names = {
            TaskPriority.LOW: "低",
            TaskPriority.NORMAL: "普通",
            TaskPriority.HIGH: "高", 
            TaskPriority.URGENT: "紧急"
        }
        return display_names[self]


class RecognitionStage(Enum):
    """识别阶段枚举
    
    定义识别流程中的各个阶段。
    """
    INITIALIZING = "initializing"         # 初始化
    CF_CLUSTERING = "cf_clustering"       # CF维度聚类
    CF_RECOGNITION = "cf_recognition"     # CF维度识别
    PW_CLUSTERING = "pw_clustering"       # PW维度聚类
    PW_RECOGNITION = "pw_recognition"     # PW维度识别
    PARAMETER_EXTRACTION = "parameter_extraction"  # 参数提取
    FINALIZING = "finalizing"             # 完成处理
    
    @property
    def display_name(self) -> str:
        """返回阶段的显示名称"""
        display_names = {
            RecognitionStage.INITIALIZING: "初始化",
            RecognitionStage.CF_CLUSTERING: "CF维度聚类",
            RecognitionStage.CF_RECOGNITION: "CF维度识别",
            RecognitionStage.PW_CLUSTERING: "PW维度聚类", 
            RecognitionStage.PW_RECOGNITION: "PW维度识别",
            RecognitionStage.PARAMETER_EXTRACTION: "参数提取",
            RecognitionStage.FINALIZING: "完成处理"
        }
        return display_names[self]
    
    @property
    def progress_weight(self) -> float:
        """返回阶段在整体进度中的权重"""
        weights = {
            RecognitionStage.INITIALIZING: 0.05,
            RecognitionStage.CF_CLUSTERING: 0.20,
            RecognitionStage.CF_RECOGNITION: 0.25,
            RecognitionStage.PW_CLUSTERING: 0.20,
            RecognitionStage.PW_RECOGNITION: 0.25,
            RecognitionStage.PARAMETER_EXTRACTION: 0.04,
            RecognitionStage.FINALIZING: 0.01
        }
        return weights[self]
