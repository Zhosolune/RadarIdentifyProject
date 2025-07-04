"""神经网络预测器基础设施模块

本模块提供基于现有ModelLoader的神经网络预测功能，用于识别功能模块。
"""

import os
from typing import Dict, Tuple, Optional
from pathlib import Path
from radar_system.infrastructure.common.logging import model_logger
from radar_system.infrastructure.common.exceptions import ModelError, ResourceError
from radar_system.domain.recognition.entities import (
    ClusterCandidate, 
    PredictionInfo, 
    JointPrediction,
    RecognitionParams
)
from .model_loader import ModelLoader


class NeuralNetworkPredictor:
    """神经网络预测器
    
    基于现有ModelLoader提供识别功能的神经网络预测服务。
    
    Attributes:
        model_loader (ModelLoader): 模型加载器实例
        models_dir (Path): 模型文件目录
        is_initialized (bool): 是否已初始化
    """
    
    def __init__(self, models_dir: str):
        """初始化神经网络预测器
        
        Args:
            models_dir: 模型文件目录路径
        """
        self.models_dir = Path(models_dir)
        self.model_loader = ModelLoader()
        self.is_initialized = False
        
        model_logger.info(f"神经网络预测器初始化 - 模型目录: {self.models_dir}")
    
    def initialize_models(self) -> bool:
        """初始化并加载模型
        
        Returns:
            bool: 是否初始化成功
            
        Raises:
            ModelError: 模型初始化失败时抛出
        """
        try:
            if self.is_initialized:
                model_logger.info("模型已经初始化，跳过重复初始化")
                return True
            
            # 查找模型文件
            pa_model_path = self._find_model_file("PA")
            dtoa_model_path = self._find_model_file("DTOA")
            
            # 加载PA模型
            if pa_model_path:
                self.model_loader.load_model("PA", str(pa_model_path))
                model_logger.info(f"PA模型加载成功: {pa_model_path.name}")
            else:
                raise ModelError(
                    message="未找到PA模型文件",
                    code="PA_MODEL_NOT_FOUND",
                    details={"models_dir": str(self.models_dir)}
                )
            
            # 加载DTOA模型
            if dtoa_model_path:
                self.model_loader.load_model("DTOA", str(dtoa_model_path))
                model_logger.info(f"DTOA模型加载成功: {dtoa_model_path.name}")
            else:
                raise ModelError(
                    message="未找到DTOA模型文件",
                    code="DTOA_MODEL_NOT_FOUND",
                    details={"models_dir": str(self.models_dir)}
                )
            
            self.is_initialized = True
            model_logger.info("神经网络预测器初始化完成")
            return True
            
        except Exception as e:
            if not isinstance(e, ModelError):
                e = ModelError(
                    message=f"模型初始化失败: {str(e)}",
                    code="MODEL_INITIALIZATION_ERROR",
                    details={"models_dir": str(self.models_dir)}
                )
            model_logger.error(str(e), exc_info=True)
            raise e
    
    def _find_model_file(self, model_type: str) -> Optional[Path]:
        """查找指定类型的模型文件
        
        Args:
            model_type: 模型类型（PA或DTOA）
            
        Returns:
            Optional[Path]: 模型文件路径，未找到时返回None
        """
        # 查找包含模型类型名称的.hdf5文件
        pattern = f"*{model_type}*.hdf5"
        model_files = list(self.models_dir.glob(pattern))
        
        if model_files:
            # 如果有多个文件，选择最新的
            latest_file = max(model_files, key=lambda p: p.stat().st_mtime)
            return latest_file
        
        return None
    
    def predict_cluster(self, cluster_candidate: ClusterCandidate, 
                       image_paths: Dict[str, str],
                       recognition_params: RecognitionParams) -> JointPrediction:
        """对聚类候选进行神经网络预测
        
        Args:
            cluster_candidate: 聚类候选实体
            image_paths: 包含PA和DTOA图像路径的字典
            recognition_params: 识别参数
            
        Returns:
            JointPrediction: 联合预测结果
            
        Raises:
            ModelError: 预测失败时抛出
        """
        try:
            if not self.is_initialized:
                raise ModelError(
                    message="预测器未初始化",
                    code="PREDICTOR_NOT_INITIALIZED"
                )
            
            model_logger.debug(
                f"开始预测 - cluster_id: {cluster_candidate.cluster_id[:8]}..., "
                f"dimension: {cluster_candidate.dimension_type.value}"
            )
            
            # PA预测
            pa_prediction = self._predict_pa(image_paths['PA'])
            
            # DTOA预测
            dtoa_prediction = self._predict_dtoa(image_paths['DTOA'])
            
            # 计算联合概率
            joint_probability = recognition_params.calculate_joint_probability(
                pa_prediction.confidence,
                dtoa_prediction.confidence
            )
            
            # 创建联合预测结果
            joint_prediction = JointPrediction(
                pa_prediction=pa_prediction,
                dtoa_prediction=dtoa_prediction,
                joint_probability=joint_probability,
                pa_weight=recognition_params.pa_weight,
                dtoa_weight=recognition_params.dtoa_weight
            )
            
            model_logger.info(
                f"预测完成 - cluster_id: {cluster_candidate.cluster_id[:8]}..., "
                f"PA: {pa_prediction.label.value}({pa_prediction.confidence:.3f}), "
                f"DTOA: {dtoa_prediction.label.value}({dtoa_prediction.confidence:.3f}), "
                f"联合概率: {joint_probability:.3f}"
            )
            
            return joint_prediction
            
        except Exception as e:
            if not isinstance(e, ModelError):
                e = ModelError(
                    message=f"聚类预测失败: {str(e)}",
                    code="CLUSTER_PREDICTION_ERROR",
                    details={
                        "cluster_id": cluster_candidate.cluster_id,
                        "dimension_type": cluster_candidate.dimension_type.value
                    }
                )
            model_logger.error(str(e), exc_info=True)
            raise e
    
    def _predict_pa(self, image_path: str) -> PredictionInfo:
        """执行PA预测
        
        Args:
            image_path: PA图像路径
            
        Returns:
            PredictionInfo: PA预测信息
        """
        try:
            # 使用ModelLoader进行预测
            label, confidence = self.model_loader.predict("PA", image_path)
            
            # 创建PA预测信息
            pa_prediction = PredictionInfo.create_pa_prediction(
                label_value=label,
                confidence=confidence
            )
            
            return pa_prediction
            
        except Exception as e:
            raise ModelError(
                message=f"PA预测失败: {str(e)}",
                code="PA_PREDICTION_ERROR",
                details={"image_path": image_path}
            )
    
    def _predict_dtoa(self, image_path: str) -> PredictionInfo:
        """执行DTOA预测
        
        Args:
            image_path: DTOA图像路径
            
        Returns:
            PredictionInfo: DTOA预测信息
        """
        try:
            # 使用ModelLoader进行预测
            label, confidence = self.model_loader.predict("DTOA", image_path)
            
            # 创建DTOA预测信息
            dtoa_prediction = PredictionInfo.create_dtoa_prediction(
                label_value=label,
                confidence=confidence
            )
            
            return dtoa_prediction
            
        except Exception as e:
            raise ModelError(
                message=f"DTOA预测失败: {str(e)}",
                code="DTOA_PREDICTION_ERROR",
                details={"image_path": image_path}
            )
    
    def is_model_loaded(self, model_type: str) -> bool:
        """检查指定模型是否已加载
        
        Args:
            model_type: 模型类型（PA或DTOA）
            
        Returns:
            bool: 是否已加载
        """
        return model_type in self.model_loader.models
    
    def get_model_info(self) -> Dict[str, dict]:
        """获取模型信息
        
        Returns:
            Dict[str, dict]: 包含模型信息的字典
        """
        return {
            'is_initialized': self.is_initialized,
            'models_dir': str(self.models_dir),
            'loaded_models': list(self.model_loader.models.keys()),
            'model_configs': self.model_loader.model_configs
        }
