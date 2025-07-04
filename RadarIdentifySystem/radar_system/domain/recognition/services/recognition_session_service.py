"""识别会话管理领域服务模块

本模块提供识别会话管理相关的领域服务实现。
"""

import uuid
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

from radar_system.domain.recognition.entities import (
    RecognitionSession, ClusterCandidate, RecognitionResult,
    ProcessingStage, RecognitionParams, ClusteringParams
)
from radar_system.domain.signal.entities.signal import TimeRange
from radar_system.infrastructure.common.exceptions import (
    ValidationError, ProcessingError
)
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.thread_safe_signal_emitter import ThreadSafeSignalEmitter


class RecognitionSessionService:
    """识别会话管理领域服务
    
    负责管理整个识别会话的生命周期，包括：
    - 会话创建和初始化
    - 会话状态管理
    - 会话进度跟踪
    - 会话结果汇总
    - 会话数据持久化
    """
    
    def __init__(
        self,
        signal_emitter: Optional[ThreadSafeSignalEmitter] = None
    ):
        """初始化识别会话管理服务
        
        Args:
            signal_emitter: 信号发射器
        """
        self._signal_emitter = signal_emitter or ThreadSafeSignalEmitter()
        self._active_sessions: Dict[str, RecognitionSession] = {}
        
        system_logger.info("识别会话管理服务初始化完成")
    
    def create_session(
        self,
        signal_data: np.ndarray,
        time_range: TimeRange,
        recognition_params: Optional[RecognitionParams] = None,
        session_id: Optional[str] = None
    ) -> RecognitionSession:
        """创建新的识别会话
        
        Args:
            signal_data: 信号数据
            time_range: 时间范围
            recognition_params: 识别参数
            clustering_params: 聚类参数
            session_id: 会话ID（可选）
            
        Returns:
            创建的识别会话
            
        Raises:
            ValidationError: 数据验证失败
        """
        try:
            # 验证输入数据
            self._validate_session_data(signal_data, time_range)
            
            # 创建识别会话
            session = RecognitionSession(
                slice_id=f"slice_{uuid.uuid4().hex[:8]}",
                slice_index=0,
                recognition_params=recognition_params or RecognitionParams(),
                session_id=session_id
            )
            
            # 注册会话
            self._active_sessions[session.session_id] = session

            system_logger.info(f"识别会话创建成功 - session_id: {session.session_id[:8]}..., "
                              f"数据点数: {len(signal_data)}")

            return session

        except Exception as e:
            error_msg = f"识别会话创建失败: {str(e)}"
            system_logger.error(error_msg)
            raise ProcessingError(error_msg) from e
    
    def get_session(self, session_id: str) -> Optional[RecognitionSession]:
        """获取识别会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            识别会话或None
        """
        return self._active_sessions.get(session_id)
    
    def update_session_stage(
        self, 
        session_id: str, 
        new_stage: ProcessingStage
    ) -> bool:
        """更新会话处理阶段
        
        Args:
            session_id: 会话ID
            new_stage: 新的处理阶段
            
        Returns:
            更新是否成功
        """
        session = self._active_sessions.get(session_id)
        if not session:
            system_logger.warning(f"会话不存在 - session_id: {session_id[:8]}...")
            return False

        old_stage = session.current_stage
        session.current_stage = new_stage
        session.updated_at = datetime.now()

        system_logger.info(f"会话阶段更新 - session_id: {session_id[:8]}..., "
                          f"{old_stage.value} -> {new_stage.value}")

        return True
    
    def add_cluster_candidates(
        self, 
        session_id: str, 
        cluster_candidates: List[ClusterCandidate]
    ) -> bool:
        """添加聚类候选到会话
        
        Args:
            session_id: 会话ID
            cluster_candidates: 聚类候选列表
            
        Returns:
            添加是否成功
        """
        session = self._active_sessions.get(session_id)
        if not session:
            system_logger.warning(f"会话不存在 - session_id: {session_id[:8]}...")
            return False

        session.cluster_candidates.extend(cluster_candidates)
        session.updated_at = datetime.now()

        system_logger.info(f"聚类候选已添加 - session_id: {session_id[:8]}..., "
                          f"新增: {len(cluster_candidates)}, "
                          f"总数: {len(session.cluster_candidates)}")

        return True
    
    def add_recognition_results(
        self, 
        session_id: str, 
        recognition_results: List[RecognitionResult]
    ) -> bool:
        """添加识别结果到会话
        
        Args:
            session_id: 会话ID
            recognition_results: 识别结果列表
            
        Returns:
            添加是否成功
        """
        session = self._active_sessions.get(session_id)
        if not session:
            system_logger.warning(f"会话不存在 - session_id: {session_id[:8]}...")
            return False

        session.recognition_results.extend(recognition_results)
        session.updated_at = datetime.now()

        system_logger.info(f"识别结果已添加 - session_id: {session_id[:8]}..., "
                          f"新增: {len(recognition_results)}, "
                          f"总数: {len(session.recognition_results)}")

        return True
    
    def update_extracted_parameters(
        self, 
        session_id: str, 
        parameters: Dict[str, List[float]]
    ) -> bool:
        """更新会话的提取参数
        
        Args:
            session_id: 会话ID
            parameters: 提取的参数
            
        Returns:
            更新是否成功
        """
        session = self._active_sessions.get(session_id)
        if not session:
            system_logger.warning(f"会话不存在 - session_id: {session_id[:8]}...")
            return False

        session.extracted_parameters = parameters
        session.updated_at = datetime.now()

        total_params = sum(len(values) for values in parameters.values())
        system_logger.info(f"提取参数已更新 - session_id: {session_id[:8]}..., "
                          f"总参数数: {total_params}")

        return True
    
    def complete_session(self, session_id: str) -> bool:
        """完成识别会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            完成是否成功
        """
        session = self._active_sessions.get(session_id)
        if not session:
            system_logger.warning(f"会话不存在 - session_id: {session_id[:8]}...")
            return False

        session.current_stage = ProcessingStage.COMPLETED
        session.mark_completed()

        system_logger.info(f"识别会话已完成 - session_id: {session_id[:8]}..., "
                          f"耗时: {(session.completed_at - session.created_at).total_seconds():.2f}秒")

        return True
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话摘要信息
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return None
        
        # 计算统计信息
        total_clusters = len(session.cf_clusters) + len(session.pw_clusters)
        total_recognitions = len(session.cf_results) + len(session.pw_results)
        passed_recognitions = sum(1 for r in session.cf_results + session.pw_results
                                if r.status.value == 'PASSED')

        total_params = len(session.final_params) if session.final_params else 0
        
        duration = None
        if session.completed_at:
            duration = (session.completed_at - session.created_at).total_seconds()
        elif session.created_at:
            duration = (datetime.now() - session.created_at).total_seconds()
        
        return {
            'session_id': session.session_id,
            'current_stage': session.current_stage.value,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'duration_seconds': duration,
            'slice_id': session.slice_id,
            'slice_index': session.slice_index,
            'total_clusters': total_clusters,
            'total_recognitions': total_recognitions,
            'passed_recognitions': passed_recognitions,
            'recognition_pass_rate': passed_recognitions / max(1, total_recognitions) * 100,
            'total_extracted_parameters': total_params,
            'has_final_params': session.final_params is not None
        }
    
    def list_active_sessions(self) -> List[str]:
        """列出所有活跃会话ID
        
        Returns:
            活跃会话ID列表
        """
        return list(self._active_sessions.keys())
    
    def remove_session(self, session_id: str) -> bool:
        """移除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            移除是否成功
        """
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            system_logger.info(f"会话已移除 - session_id: {session_id[:8]}...")
            return True
        else:
            system_logger.warning(f"会话不存在，无法移除 - session_id: {session_id[:8]}...")
            return False
    
    def cleanup_completed_sessions(self) -> int:
        """清理已完成的会话
        
        Returns:
            清理的会话数量
        """
        completed_sessions = [
            session_id for session_id, session in self._active_sessions.items()
            if session.current_stage == ProcessingStage.COMPLETED
        ]
        
        for session_id in completed_sessions:
            del self._active_sessions[session_id]
        
        if completed_sessions:
            system_logger.info(f"已清理{len(completed_sessions)}个完成的会话")

        return len(completed_sessions)
    
    def _validate_session_data(self, signal_data: np.ndarray, time_range: TimeRange) -> None:
        """验证会话数据
        
        Args:
            signal_data: 信号数据
            time_range: 时间范围
            
        Raises:
            ValidationError: 验证失败
        """
        if signal_data is None or len(signal_data) == 0:
            raise ValidationError("信号数据不能为空")
        
        if signal_data.ndim != 2:
            raise ValidationError(f"信号数据必须是二维数组，当前维度: {signal_data.ndim}")
        
        if time_range is None:
            raise ValidationError("时间范围不能为空")
        
        if time_range.start_time >= time_range.end_time:
            raise ValidationError("时间范围无效：开始时间必须小于结束时间")
