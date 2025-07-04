"""识别会话实体模块

本模块定义了识别会话实体，用于管理整个识别流程的状态和进度。
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from .enums import ProcessingStage
from .cluster_candidate import ClusterCandidate
from .recognition_result import RecognitionResult
from .recognition_params import RecognitionParams


class RecognitionSession:
    """识别会话实体
    
    管理整个识别流程的状态和进度，跟踪从CF聚类到参数提取的完整过程。
    
    Attributes:
        session_id (str): 会话唯一标识
        slice_id (str): 关联的信号切片ID
        slice_index (int): 切片索引
        current_stage (ProcessingStage): 当前处理阶段
        recognition_params (RecognitionParams): 识别参数
        cf_clusters (List[ClusterCandidate]): CF维度聚类候选列表
        pw_clusters (List[ClusterCandidate]): PW维度聚类候选列表
        cf_results (List[RecognitionResult]): CF维度识别结果列表
        pw_results (List[RecognitionResult]): PW维度识别结果列表
        final_params (Optional[Dict]): 最终提取的参数
        error_message (Optional[str]): 错误信息
        metadata (dict): 会话元数据
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
    """
    
    def __init__(
        self,
        slice_id: str,
        slice_index: int,
        recognition_params: RecognitionParams,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化识别会话实体
        
        Args:
            slice_id: 关联的信号切片ID
            slice_index: 切片索引
            recognition_params: 识别参数
            session_id: 会话唯一标识，默认自动生成
            metadata: 会话元数据，默认为空字典
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.slice_id = slice_id
        self.slice_index = slice_index
        self.current_stage = ProcessingStage.CF_CLUSTERING
        self.recognition_params = recognition_params
        
        # 初始化各阶段的数据容器
        self.cf_clusters: List[ClusterCandidate] = []
        self.pw_clusters: List[ClusterCandidate] = []
        self.cf_results: List[RecognitionResult] = []
        self.pw_results: List[RecognitionResult] = []
        
        self.final_params: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.metadata = metadata or {}
        
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.completed_at: Optional[datetime] = None
        
        # 验证数据有效性
        self._validate()
    
    def _validate(self):
        """验证识别会话的数据有效性"""
        if not self.slice_id:
            raise ValueError("切片ID不能为空")
        
        if self.slice_index < 0:
            raise ValueError(f"切片索引不能为负数，当前值: {self.slice_index}")
        
        if self.recognition_params is None:
            raise ValueError("识别参数不能为空")
    
    def _update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()
    
    @property
    def is_completed(self) -> bool:
        """判断识别是否已完成"""
        return self.current_stage in [ProcessingStage.COMPLETED, ProcessingStage.FAILED]
    
    @property
    def is_failed(self) -> bool:
        """判断识别是否失败"""
        return self.current_stage == ProcessingStage.FAILED
    
    @property
    def progress_percentage(self) -> float:
        """获取当前进度百分比"""
        return self.current_stage.progress_percentage
    
    @property
    def total_cf_clusters(self) -> int:
        """获取CF维度聚类总数"""
        return len(self.cf_clusters)
    
    @property
    def total_pw_clusters(self) -> int:
        """获取PW维度聚类总数"""
        return len(self.pw_clusters)
    
    @property
    def total_cf_results(self) -> int:
        """获取CF维度识别结果总数"""
        return len(self.cf_results)
    
    @property
    def total_pw_results(self) -> int:
        """获取PW维度识别结果总数"""
        return len(self.pw_results)
    
    @property
    def valid_cf_clusters(self) -> List[ClusterCandidate]:
        """获取有效的CF维度聚类"""
        return [cluster for cluster in self.cf_clusters if cluster.is_valid]
    
    @property
    def valid_pw_clusters(self) -> List[ClusterCandidate]:
        """获取有效的PW维度聚类"""
        return [cluster for cluster in self.pw_clusters if cluster.is_valid]
    
    @property
    def passed_cf_results(self) -> List[RecognitionResult]:
        """获取通过的CF维度识别结果"""
        return [result for result in self.cf_results if result.is_passed]
    
    @property
    def passed_pw_results(self) -> List[RecognitionResult]:
        """获取通过的PW维度识别结果"""
        return [result for result in self.pw_results if result.is_passed]
    
    def advance_stage(self, new_stage: ProcessingStage):
        """推进到下一个处理阶段
        
        Args:
            new_stage: 新的处理阶段
        """
        self.current_stage = new_stage
        self._update_timestamp()
        self.metadata[f'stage_{new_stage.value}_at'] = self.updated_at.isoformat()
    
    def set_error(self, error_message: str):
        """设置错误信息并标记为失败
        
        Args:
            error_message: 错误信息
        """
        self.error_message = error_message
        self.current_stage = ProcessingStage.FAILED
        self._update_timestamp()
        self.metadata['error_at'] = self.updated_at.isoformat()
    
    def add_cf_clusters(self, clusters: List[ClusterCandidate]):
        """添加CF维度聚类候选
        
        Args:
            clusters: CF维度聚类候选列表
        """
        self.cf_clusters.extend(clusters)
        self._update_timestamp()
        self.metadata['cf_clusters_count'] = len(self.cf_clusters)
    
    def add_pw_clusters(self, clusters: List[ClusterCandidate]):
        """添加PW维度聚类候选
        
        Args:
            clusters: PW维度聚类候选列表
        """
        self.pw_clusters.extend(clusters)
        self._update_timestamp()
        self.metadata['pw_clusters_count'] = len(self.pw_clusters)
    
    def add_cf_results(self, results: List[RecognitionResult]):
        """添加CF维度识别结果
        
        Args:
            results: CF维度识别结果列表
        """
        self.cf_results.extend(results)
        self._update_timestamp()
        self.metadata['cf_results_count'] = len(self.cf_results)
    
    def add_pw_results(self, results: List[RecognitionResult]):
        """添加PW维度识别结果
        
        Args:
            results: PW维度识别结果列表
        """
        self.pw_results.extend(results)
        self._update_timestamp()
        self.metadata['pw_results_count'] = len(self.pw_results)
    
    def set_final_params(self, params: Dict[str, Any]):
        """设置最终提取的参数
        
        Args:
            params: 最终提取的参数
        """
        self.final_params = params
        self._update_timestamp()
        self.metadata['params_extracted_at'] = self.updated_at.isoformat()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要信息
        
        Returns:
            Dict: 包含会话摘要信息的字典
        """
        return {
            'session_id': self.session_id,
            'slice_id': self.slice_id,
            'slice_index': self.slice_index,
            'current_stage': self.current_stage.value,
            'stage_display_name': self.current_stage.display_name,
            'progress_percentage': self.progress_percentage,
            'is_completed': self.is_completed,
            'is_failed': self.is_failed,
            'error_message': self.error_message,
            'statistics': {
                'cf_clusters_total': self.total_cf_clusters,
                'cf_clusters_valid': len(self.valid_cf_clusters),
                'pw_clusters_total': self.total_pw_clusters,
                'pw_clusters_valid': len(self.valid_pw_clusters),
                'cf_results_total': self.total_cf_results,
                'cf_results_passed': len(self.passed_cf_results),
                'pw_results_total': self.total_pw_results,
                'pw_results_passed': len(self.passed_pw_results),
                'has_final_params': self.final_params is not None
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_full_info(self) -> Dict[str, Any]:
        """获取完整的会话信息
        
        Returns:
            Dict: 包含完整会话信息的字典
        """
        summary = self.get_session_summary()
        summary.update({
            'recognition_params': self.recognition_params.to_dict(),
            'cf_clusters': [cluster.get_statistics() for cluster in self.cf_clusters],
            'pw_clusters': [cluster.get_statistics() for cluster in self.pw_clusters],
            'cf_results': [result.get_full_info() for result in self.cf_results],
            'pw_results': [result.get_full_info() for result in self.pw_results],
            'final_params': self.final_params,
            'metadata': self.metadata
        })
        return summary
    
    def __str__(self) -> str:
        """返回识别会话的字符串表示"""
        return (
            f"RecognitionSession(id={self.session_id[:8]}..., "
            f"slice_id={self.slice_id[:8]}..., "
            f"slice_index={self.slice_index}, "
            f"stage={self.current_stage.value}, "
            f"progress={self.progress_percentage:.1f}%, "
            f"cf_clusters={self.total_cf_clusters}, "
            f"pw_clusters={self.total_pw_clusters})"
        )
    
    def __repr__(self) -> str:
        """返回识别会话的详细表示"""
        return self.__str__()

    def mark_completed(self):
        """标记会话为已完成"""
        self.completed_at = datetime.now()
        self._update_timestamp()
