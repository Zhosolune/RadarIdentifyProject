"""识别功能相关的枚举定义模块

本模块定义了识别功能中使用的所有枚举类型，包括处理阶段、聚类状态、识别状态等。
"""

from enum import Enum


class ProcessingStage(Enum):
    """识别处理阶段枚举
    
    定义识别流程中的各个处理阶段，用于跟踪识别进度。
    """
    CF_CLUSTERING = "cf_clustering"
    CF_RECOGNITION = "cf_recognition"
    PW_CLUSTERING = "pw_clustering"
    PW_RECOGNITION = "pw_recognition"
    PARAMETER_EXTRACTION = "parameter_extraction"
    COMPLETED = "completed"
    FAILED = "failed"
    
    @property
    def display_name(self) -> str:
        """获取阶段的显示名称"""
        display_names = {
            self.CF_CLUSTERING: "CF维度聚类",
            self.CF_RECOGNITION: "CF维度识别",
            self.PW_CLUSTERING: "PW维度聚类", 
            self.PW_RECOGNITION: "PW维度识别",
            self.PARAMETER_EXTRACTION: "参数提取",
            self.COMPLETED: "识别完成",
            self.FAILED: "识别失败"
        }
        return display_names.get(self, self.value)
    
    @property
    def progress_percentage(self) -> float:
        """获取阶段对应的进度百分比"""
        progress_map = {
            self.CF_CLUSTERING: 10.0,
            self.CF_RECOGNITION: 30.0,
            self.PW_CLUSTERING: 50.0,
            self.PW_RECOGNITION: 70.0,
            self.PARAMETER_EXTRACTION: 90.0,
            self.COMPLETED: 100.0,
            self.FAILED: 0.0
        }
        return progress_map.get(self, 0.0)


class ClusterStatus(Enum):
    """聚类状态枚举
    
    定义聚类候选的状态：
    - VALID: 有效聚类 (对应业务流程中的A、E状态)
    - INVALID: 无效聚类 (对应业务流程中的B、F状态)
    """
    VALID = "valid"
    INVALID = "invalid"
    
    @property
    def display_name(self) -> str:
        """获取状态的显示名称"""
        display_names = {
            self.VALID: "有效聚类",
            self.INVALID: "无效聚类"
        }
        return display_names.get(self, self.value)


class RecognitionStatus(Enum):
    """识别状态枚举
    
    定义识别结果的状态：
    - PASSED: 识别通过 (对应业务流程中的C、G状态)
    - FAILED: 识别未通过 (对应业务流程中的D、H状态)
    """
    PASSED = "passed"
    FAILED = "failed"
    
    @property
    def display_name(self) -> str:
        """获取状态的显示名称"""
        display_names = {
            self.PASSED: "识别通过",
            self.FAILED: "识别未通过"
        }
        return display_names.get(self, self.value)


class DimensionType(Enum):
    """维度类型枚举
    
    定义聚类处理的维度类型。
    """
    CF = "CF"
    PW = "PW"
    
    @property
    def display_name(self) -> str:
        """获取维度的显示名称"""
        display_names = {
            self.CF: "载频维度",
            self.PW: "脉宽维度"
        }
        return display_names.get(self, self.value)
    
    @property
    def data_column_index(self) -> int:
        """获取维度在数据数组中的列索引"""
        column_map = {
            self.CF: 0,  # CF列
            self.PW: 1   # PW列
        }
        return column_map.get(self, 0)


class PredictionLabel(Enum):
    """预测标签枚举
    
    定义PA和DTOA的预测标签类型。
    """
    # PA标签
    PA_COMPLETE_ENVELOPE = 0      # 完整包络
    PA_INCOMPLETE_ENVELOPE = 1    # 残缺包络
    PA_PARTIAL_ENVELOPE = 2       # 部分包络
    PA_PHASE_SCAN = 3             # 相扫
    PA_SIDE_LOBE = 4              # 旁瓣
    PA_NON_RADAR = 5              # 非雷达信号
    
    # DTOA标签
    DTOA_REGULAR = 0              # 常规
    DTOA_PULSE_STAGGER = 1        # 脉间参差
    DTOA_GROUP_STAGGER = 2        # 脉组参差
    DTOA_PULSE_GROUP_STAGGER = 3  # 脉间脉组参差
    DTOA_NON_RADAR = 4            # 非雷达信号
    
    @property
    def display_name(self) -> str:
        """获取标签的显示名称"""
        display_names = {
            # PA标签显示名称
            self.PA_COMPLETE_ENVELOPE: "完整包络",
            self.PA_INCOMPLETE_ENVELOPE: "残缺包络",
            self.PA_PARTIAL_ENVELOPE: "部分包络",
            self.PA_PHASE_SCAN: "相扫",
            self.PA_SIDE_LOBE: "旁瓣",
            self.PA_NON_RADAR: "非雷达信号",
            
            # DTOA标签显示名称
            self.DTOA_REGULAR: "常规",
            self.DTOA_PULSE_STAGGER: "脉间参差",
            self.DTOA_GROUP_STAGGER: "脉组参差",
            self.DTOA_PULSE_GROUP_STAGGER: "脉间脉组参差",
            self.DTOA_NON_RADAR: "非雷达信号"
        }
        return display_names.get(self, str(self.value))
    
    @classmethod
    def get_pa_labels(cls) -> list:
        """获取所有PA标签"""
        return [
            cls.PA_COMPLETE_ENVELOPE,
            cls.PA_INCOMPLETE_ENVELOPE,
            cls.PA_PARTIAL_ENVELOPE,
            cls.PA_PHASE_SCAN,
            cls.PA_SIDE_LOBE,
            cls.PA_NON_RADAR
        ]
    
    @classmethod
    def get_dtoa_labels(cls) -> list:
        """获取所有DTOA标签"""
        return [
            cls.DTOA_REGULAR,
            cls.DTOA_PULSE_STAGGER,
            cls.DTOA_GROUP_STAGGER,
            cls.DTOA_PULSE_GROUP_STAGGER,
            cls.DTOA_NON_RADAR
        ]
