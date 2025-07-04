"""识别结果实体模块

本模块定义了识别结果实体，表示神经网络识别的结果。
对应业务流程中的C、D、G、H状态。
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from .enums import RecognitionStatus
from .cluster_candidate import ClusterCandidate
from .prediction_info import PredictionInfo, JointPrediction


class RecognitionResult:
    """识别结果实体
    
    表示神经网络识别的结果，统一表示业务流程中的：
    - C状态：CF维度识别通过
    - D状态：CF维度识别未通过
    - G状态：PW维度识别通过
    - H状态：PW维度识别未通过
    
    Attributes:
        result_id (str): 识别结果唯一标识
        cluster_candidate (ClusterCandidate): 关联的聚类候选
        joint_prediction (JointPrediction): 联合预测结果
        status (RecognitionStatus): 识别状态
        image_path (str): 生成的图像路径
        extracted_params (Optional[Dict]): 提取的参数
        metadata (dict): 识别元数据
        created_at (datetime): 创建时间
    """
    
    def __init__(
        self,
        cluster_candidate: ClusterCandidate,
        joint_prediction: JointPrediction,
        status: RecognitionStatus,
        image_path: str,
        result_id: Optional[str] = None,
        extracted_params: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化识别结果实体
        
        Args:
            cluster_candidate: 关联的聚类候选
            joint_prediction: 联合预测结果
            status: 识别状态
            image_path: 生成的图像路径
            result_id: 识别结果唯一标识，默认自动生成
            extracted_params: 提取的参数，默认为None
            metadata: 识别元数据，默认为空字典
        """
        self.result_id = result_id or str(uuid.uuid4())
        self.cluster_candidate = cluster_candidate
        self.joint_prediction = joint_prediction
        self.status = status
        self.image_path = image_path
        self.extracted_params = extracted_params
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        
        # 验证数据有效性
        self._validate()
    
    def _validate(self):
        """验证识别结果的数据有效性"""
        if self.cluster_candidate is None:
            raise ValueError("聚类候选不能为空")
        
        if self.joint_prediction is None:
            raise ValueError("联合预测结果不能为空")
        
        if not self.image_path:
            raise ValueError("图像路径不能为空")
    
    @property
    def is_passed(self) -> bool:
        """判断识别是否通过"""
        return self.status == RecognitionStatus.PASSED
    
    @property
    def confidence_score(self) -> float:
        """获取置信度分数"""
        return self.joint_prediction.joint_probability
    
    @property
    def pa_prediction(self) -> PredictionInfo:
        """获取PA预测信息"""
        return self.joint_prediction.pa_prediction
    
    @property
    def dtoa_prediction(self) -> PredictionInfo:
        """获取DTOA预测信息"""
        return self.joint_prediction.dtoa_prediction
    
    @property
    def business_state_code(self) -> str:
        """获取业务状态代码
        
        根据聚类候选的维度类型和识别状态返回对应的业务状态代码：
        - CF + PASSED = C
        - CF + FAILED = D
        - PW + PASSED = G
        - PW + FAILED = H
        """
        from .enums import DimensionType
        
        state_map = {
            (DimensionType.CF, RecognitionStatus.PASSED): 'C',
            (DimensionType.CF, RecognitionStatus.FAILED): 'D',
            (DimensionType.PW, RecognitionStatus.PASSED): 'G',
            (DimensionType.PW, RecognitionStatus.FAILED): 'H'
        }
        return state_map.get((self.cluster_candidate.dimension_type, self.status), 'UNKNOWN')
    
    @property
    def has_extracted_params(self) -> bool:
        """判断是否已提取参数"""
        return self.extracted_params is not None and len(self.extracted_params) > 0
    
    def set_extracted_params(self, params: Dict[str, Any]):
        """设置提取的参数
        
        Args:
            params: 提取的参数字典
        """
        self.extracted_params = params
        self.metadata['params_extracted_at'] = datetime.now().isoformat()
    
    def get_prediction_summary(self) -> Dict[str, Any]:
        """获取预测结果摘要
        
        Returns:
            Dict: 包含预测结果摘要信息
        """
        return {
            'pa_label': self.pa_prediction.label.value,
            'pa_label_name': self.pa_prediction.label_name,
            'pa_confidence': self.pa_prediction.confidence,
            'dtoa_label': self.dtoa_prediction.label.value,
            'dtoa_label_name': self.dtoa_prediction.label_name,
            'dtoa_confidence': self.dtoa_prediction.confidence,
            'joint_probability': self.confidence_score,
            'is_high_confidence': self.joint_prediction.is_high_confidence
        }
    
    def get_full_info(self) -> Dict[str, Any]:
        """获取完整的识别结果信息
        
        Returns:
            Dict: 包含完整识别结果信息的字典
        """
        return {
            'result_id': self.result_id,
            'cluster_info': self.cluster_candidate.get_statistics(),
            'prediction_summary': self.get_prediction_summary(),
            'joint_prediction': self.joint_prediction.to_dict(),
            'status': self.status.value,
            'business_state': self.business_state_code,
            'image_path': self.image_path,
            'extracted_params': self.extracted_params,
            'has_extracted_params': self.has_extracted_params,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }
    
    def copy(self) -> 'RecognitionResult':
        """创建识别结果的深拷贝
        
        Returns:
            RecognitionResult: 识别结果的深拷贝
        """
        return RecognitionResult(
            cluster_candidate=self.cluster_candidate.copy(),
            joint_prediction=self.joint_prediction,  # JointPrediction是不可变的
            status=self.status,
            image_path=self.image_path,
            result_id=self.result_id,  # 保持相同的ID
            extracted_params=self.extracted_params.copy() if self.extracted_params else None,
            metadata=self.metadata.copy() if self.metadata else None
        )
    
    def __str__(self) -> str:
        """返回识别结果的字符串表示"""
        return (
            f"RecognitionResult(id={self.result_id[:8]}..., "
            f"cluster_id={self.cluster_candidate.cluster_id[:8]}..., "
            f"status={self.status.value}, "
            f"business_state={self.business_state_code}, "
            f"confidence={self.confidence_score:.3f}, "
            f"pa_label={self.pa_prediction.label.value}, "
            f"dtoa_label={self.dtoa_prediction.label.value})"
        )
    
    def __repr__(self) -> str:
        """返回识别结果的详细表示"""
        return self.__str__()
