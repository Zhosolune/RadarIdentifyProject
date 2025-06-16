import os
import tensorflow as tf
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path
from PIL import Image
from radar_system.infrastructure.common.logging import model_logger
from radar_system.infrastructure.common.exceptions import ModelError, ResourceError

class ModelLoader:
    """模型加载器
    
    负责加载和管理深度学习模型，提供模型加载、预处理和预测功能。
    
    Attributes:
        models (Dict[str, tf.keras.Model]): 已加载的模型字典
        model_configs (Dict[str, dict]): 模型配置字典
    """
    
    _instance = None
    
    def __new__(cls) -> 'ModelLoader':
        """创建或返回单例实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化模型加载器"""
        if self._initialized:
            return
            
        self.models: Dict[str, tf.keras.Model] = {}
        self.model_configs: Dict[str, dict] = {
            'PA': {
                'input_shape': (80, 400, 3),
                'threshold': 0.9,
                'num_classes': 5,
                'preprocessing': {
                    'target_size': (400, 80),
                    'normalize': True
                }
            },
            'DTOA': {
                'input_shape': (250, 500, 3),
                'threshold': 0.91,
                'num_classes': 4,
                'preprocessing': {
                    'target_size': (500, 250),
                    'normalize': True
                }
            }
        }
        self._initialized = True
        model_logger.info("模型加载器初始化完成")
    
    def load_model(self, model_type: str, model_path: str) -> bool:
        """加载指定类型的模型
        
        Args:
            model_type (str): 模型类型，'PA'或'DTOA'
            model_path (str): 模型文件路径
            
        Returns:
            bool: 是否加载成功
            
        Raises:
            ModelError: 模型加载失败时抛出
        """
        try:
            if model_type not in self.model_configs:
                raise ModelError(
                    message=f"不支持的模型类型: {model_type}",
                    code="UNSUPPORTED_MODEL_TYPE",
                    details={"supported_types": list(self.model_configs.keys())}
                )
            
            if not Path(model_path).exists():
                raise ResourceError(
                    message=f"模型文件不存在: {model_path}",
                    resource_type="model_file",
                    resource_id=model_path
                )
            
            model_logger.info(f"开始加载{model_type}模型: {model_path}")
            model = tf.keras.models.load_model(model_path)
            
            # 验证模型输入形状
            expected_shape = self.model_configs[model_type]['input_shape']
            actual_shape = model.input_shape[1:]
            if actual_shape != expected_shape:
                raise ModelError(
                    message=f"模型输入形状不匹配",
                    code="INVALID_INPUT_SHAPE",
                    details={
                        "expected": expected_shape,
                        "actual": actual_shape
                    }
                )
            
            self.models[model_type] = model
            model_logger.info(f"{model_type}模型加载成功")
            return True
            
        except Exception as e:
            if not isinstance(e, (ModelError, ResourceError)):
                e = ModelError(
                    message=f"模型加载失败: {str(e)}",
                    code="MODEL_LOAD_ERROR",
                    details={"model_type": model_type, "path": model_path}
                )
            model_logger.error(str(e), exc_info=True)
            raise e
    
    def predict(self, model_type: str, image_path: str) -> Tuple[int, float]:
        """使用指定模型进行预测
        
        Args:
            model_type (str): 模型类型，'PA'或'DTOA'
            image_path (str): 图像文件路径
            
        Returns:
            Tuple[int, float]: 
                - int: 预测标签
                - float: 预测置信度
                
        Raises:
            ModelError: 预测失败时抛出
        """
        try:
            if model_type not in self.models:
                raise ModelError(
                    message=f"模型未加载: {model_type}",
                    code="MODEL_NOT_LOADED",
                    details={"model_type": model_type}
                )
            
            model_logger.debug(f"开始{model_type}预测，图像路径: {image_path}")
            
            # 预处理图像
            config = self.model_configs[model_type]
            image = self._preprocess_image(
                image_path,
                config['preprocessing']['target_size'],
                config['preprocessing']['normalize']
            )
            
            # 进行预测
            predictions = self.models[model_type].predict(image, verbose=0)
            label = np.argmax(predictions[0])
            confidence = np.max(predictions[0])
            
            # 后处理
            threshold = config['threshold']
            num_classes = config['num_classes']
            
            if confidence < threshold:
                label = num_classes  # 无效类别
            elif label >= num_classes:
                label = num_classes - 1
            
            # PA特殊处理
            if model_type == 'PA' and label >= num_classes:
                top3_probs = predictions[0, :3]
                if np.sum(top3_probs) > 0.99:
                    label = np.argmax(top3_probs)
                    confidence = np.sum(top3_probs)
            
            model_logger.info(
                f"{model_type}预测结果 - "
                f"标签: {label}, 置信度: {confidence:.4f}"
            )
            return int(label), float(confidence)
            
        except Exception as e:
            if not isinstance(e, ModelError):
                e = ModelError(
                    message=f"预测失败: {str(e)}",
                    code="PREDICTION_ERROR",
                    details={
                        "model_type": model_type,
                        "image_path": image_path
                    }
                )
            model_logger.error(str(e), exc_info=True)
            raise e
    
    def _preprocess_image(self, 
                         image_path: str,
                         target_size: Tuple[int, int],
                         normalize: bool = True) -> np.ndarray:
        """预处理图像
        
        Args:
            image_path (str): 图像文件路径
            target_size (Tuple[int, int]): 目标尺寸 (width, height)
            normalize (bool): 是否归一化像素值
            
        Returns:
            np.ndarray: 预处理后的图像数组，形状为(1, height, width, 3)
            
        Raises:
            ResourceError: 图像文件不存在或无法读取时抛出
        """
        try:
            if not Path(image_path).exists():
                raise ResourceError(
                    message=f"图像文件不存在: {image_path}",
                    resource_type="image_file",
                    resource_id=image_path
                )
            
            # 读取并调整图像大小
            img = Image.open(image_path)
            img = img.resize(target_size).convert('RGB')
            
            # 转换为numpy数组
            img_array = np.array(img)
            img_array = img_array.astype('float32')
            
            # 归一化
            if normalize:
                img_array = img_array / 255.0
            
            # 添加batch维度
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
            
        except Exception as e:
            if not isinstance(e, ResourceError):
                e = ResourceError(
                    message=f"图像预处理失败: {str(e)}",
                    resource_type="image_file",
                    resource_id=image_path
                )
            model_logger.error(str(e), exc_info=True)
            raise e
