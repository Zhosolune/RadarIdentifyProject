"""识别领域服务模块

本模块提供神经网络识别相关的领域服务实现。
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path

from radar_system.domain.recognition.entities import (
    ClusterCandidate, RecognitionResult, RecognitionStatus,
    PredictionInfo, JointPrediction, RecognitionParams
)
from radar_system.infrastructure.visualization import ClusterImageGenerator
from radar_system.infrastructure.ml import NeuralNetworkPredictor
from radar_system.infrastructure.common.exceptions import (
    ValidationError, ProcessingError
)
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.thread_safe_signal_emitter import ThreadSafeSignalEmitter


class RecognitionService:
    """识别领域服务
    
    负责协调神经网络识别过程，包括：
    - 聚类图像生成
    - 神经网络预测
    - 识别结果生成和验证
    - 识别状态管理
    """
    
    def __init__(
        self,
        models_dir: str,
        output_dir: str,
        recognition_params: Optional[RecognitionParams] = None,
        signal_emitter: Optional[ThreadSafeSignalEmitter] = None
    ):
        """初始化识别服务
        
        Args:
            models_dir: 模型文件目录
            output_dir: 输出文件目录
            recognition_params: 识别参数配置
            signal_emitter: 信号发射器
        """
        self._models_dir = models_dir
        self._output_dir = output_dir
        self._recognition_params = recognition_params or RecognitionParams()
        self._signal_emitter = signal_emitter or ThreadSafeSignalEmitter()
        
        # 初始化图像生成器
        self._image_generator = ClusterImageGenerator(
            output_dir=output_dir,
            temp_dir=str(Path(output_dir) / "temp")
        )
        
        # 初始化神经网络预测器
        self._predictor = NeuralNetworkPredictor(
            models_dir=models_dir
        )
        
        system_logger.info(f"识别服务初始化完成 - 模型目录: {models_dir}, 输出目录: {output_dir}")

    def recognize_cluster(self, cluster_candidate: ClusterCandidate) -> RecognitionResult:
        """识别单个聚类候选

        Args:
            cluster_candidate: 聚类候选

        Returns:
            识别结果

        Raises:
            ValidationError: 数据验证失败
            ProcessingError: 识别处理失败
        """
        try:
            # 验证聚类候选
            self._validate_cluster_candidate(cluster_candidate)

            # 生成聚类图像
            image_paths = self._image_generator.generate_cluster_images(
                cluster_candidate, for_prediction=True
            )

            # 执行神经网络预测
            joint_prediction = self._predictor.predict_cluster(
                cluster_candidate, image_paths
            )

            # 确定识别状态
            recognition_status = self._determine_recognition_status(
                joint_prediction, cluster_candidate.dimension_type
            )

            # 创建识别结果
            recognition_result = RecognitionResult(
                cluster_candidate=cluster_candidate,
                joint_prediction=joint_prediction,
                status=recognition_status,
                image_path=image_paths.get('PA', ''),
                metadata={
                    'image_paths': image_paths,
                    'recognition_params': self._recognition_params.to_dict(),
                    'prediction_confidence': joint_prediction.joint_probability
                }
            )

            system_logger.info(f"聚类识别完成 - cluster_id: {cluster_candidate.cluster_id[:8]}..., "
                              f"状态: {recognition_status.value}, "
                              f"置信度: {joint_prediction.joint_probability:.3f}")

            return recognition_result

        except Exception as e:
            error_msg = f"聚类识别失败 - cluster_id: {cluster_candidate.cluster_id[:8]}...: {str(e)}"
            system_logger.error(error_msg)
            raise ProcessingError(error_msg) from e
    
    def batch_recognize_clusters(
        self, 
        cluster_candidates: List[ClusterCandidate]
    ) -> List[RecognitionResult]:
        """批量识别聚类候选
        
        Args:
            cluster_candidates: 聚类候选列表
            
        Returns:
            识别结果列表
        """
        recognition_results = []
        
        for i, candidate in enumerate(cluster_candidates):
            try:
                result = self.recognize_cluster(candidate)
                recognition_results.append(result)
                
                # 发送进度信号
                progress = (i + 1) / len(cluster_candidates) * 100
                self._signal_emitter.emit_log_signal(
                    f"批量识别进度: {progress:.1f}% ({i + 1}/{len(cluster_candidates)})"
                )
                
            except Exception as e:
                system_logger.warning(f"跳过识别失败的聚类 - cluster_id: {candidate.cluster_id[:8]}...: {str(e)}")
                continue

        system_logger.info(f"批量识别完成 - 总数: {len(cluster_candidates)}, "
                          f"成功: {len(recognition_results)}, "
                          f"失败: {len(cluster_candidates) - len(recognition_results)}")
        
        return recognition_results
    
    def initialize_models(self) -> bool:
        """初始化神经网络模型
        
        Returns:
            初始化是否成功
        """
        try:
            success = self._predictor.initialize_models()
            if success:
                system_logger.info("神经网络模型初始化成功")
            else:
                system_logger.warning("神经网络模型初始化失败")
            return success

        except Exception as e:
            system_logger.error(f"神经网络模型初始化异常: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息
        
        Returns:
            模型信息字典
        """
        return self._predictor.get_model_info()
    
    def update_recognition_parameters(self, new_params: RecognitionParams) -> None:
        """更新识别参数
        
        Args:
            new_params: 新的识别参数
        """
        self._recognition_params = new_params
        system_logger.info("识别参数已更新")
    
    def get_recognition_statistics(
        self, 
        recognition_results: List[RecognitionResult]
    ) -> Dict[str, Any]:
        """获取识别统计信息
        
        Args:
            recognition_results: 识别结果列表
            
        Returns:
            识别统计信息
        """
        if not recognition_results:
            return {
                'total_recognitions': 0,
                'passed_recognitions': 0,
                'failed_recognitions': 0,
                'average_confidence': 0.0
            }
        
        passed_count = sum(1 for r in recognition_results if r.status == RecognitionStatus.PASSED)
        failed_count = len(recognition_results) - passed_count
        
        confidences = [r.joint_prediction.joint_probability for r in recognition_results 
                      if r.joint_prediction]
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        return {
            'total_recognitions': len(recognition_results),
            'passed_recognitions': passed_count,
            'failed_recognitions': failed_count,
            'pass_rate': passed_count / len(recognition_results) * 100,
            'average_confidence': avg_confidence,
            'confidence_std': np.std(confidences) if confidences else 0.0
        }
    
    def _validate_cluster_candidate(self, cluster_candidate: ClusterCandidate) -> None:
        """验证聚类候选
        
        Args:
            cluster_candidate: 聚类候选
            
        Raises:
            ValidationError: 验证失败
        """
        if cluster_candidate is None:
            raise ValidationError("聚类候选不能为空")
        
        if cluster_candidate.cluster_data is None or len(cluster_candidate.cluster_data) == 0:
            raise ValidationError("聚类数据不能为空")
        
        if cluster_candidate.cluster_data.ndim != 2:
            raise ValidationError(f"聚类数据必须是二维数组，当前维度: {cluster_candidate.cluster_data.ndim}")
        
        min_points = self._recognition_params.min_cluster_size_for_recognition
        if len(cluster_candidate.cluster_data) < min_points:
            raise ValidationError(f"聚类数据点数不足，需要至少{min_points}个点")
    
    def _determine_recognition_status(
        self, 
        joint_prediction: JointPrediction, 
        dimension_type
    ) -> RecognitionStatus:
        """确定识别状态
        
        Args:
            joint_prediction: 联合预测结果
            dimension_type: 维度类型
            
        Returns:
            识别状态
        """
        # 根据联合概率和阈值确定识别状态
        threshold = self._recognition_params.recognition_threshold
        
        if joint_prediction.joint_probability >= threshold:
            return RecognitionStatus.PASSED
        else:
            return RecognitionStatus.FAILED
    
    def cleanup_temp_files(self) -> None:
        """清理临时文件"""
        try:
            self._image_generator.cleanup_temp_files()
            system_logger.info("临时文件清理完成")
        except Exception as e:
            system_logger.warning(f"临时文件清理失败: {str(e)}")
