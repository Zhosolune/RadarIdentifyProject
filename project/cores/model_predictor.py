import tensorflow as tf
import numpy as np
from PIL import Image
import os
from typing import Tuple, Optional, Dict
from .plot_manager import SignalPlotter
from .log_manager import LogManager

class ModelPredictor:
    """模型预测器
    
    负责加载和管理深度学习模型，对雷达信号聚类结果进行PA和DTOA特征预测。
    
    Attributes:
        model_dtoa (tf.keras.Model): DTOA预测模型
        model_pa (tf.keras.Model): PA预测模型
        temp_dir (str): 临时文件目录
        plotter (SignalPlotter): 信号绘图器实例
        logger (LogManager): 日志管理器实例
        th_dtoa (float): DTOA预测阈值，默认0.91
        th_pa (float): PA预测阈值，默认0.9
        time_ranges (list): 时间范围列表
        dtoa_model_path (str): DTOA模型文件路径
        pa_model_path (str): PA模型文件路径
    """

    def __init__(self):
        """初始化模型预测器"""
        self.dtoa_model = None
        self.pa_model = None
        self.temp_dir = "temp"
        self.plotter = SignalPlotter()
        self.logger = LogManager()
        
        # 添加模型路径属性
        self.dtoa_model_path = None
        self.pa_model_path = None

        # 预测阈值
        self.th_dtoa = 0.91  # DTOA预测阈值
        self.th_pa = 0.9  # PA预测阈值

        self.time_ranges = []  # 初始化时间范围列表

    def set_time_ranges(self, time_ranges: list):
        """设置时间范围列表
        
        Args:
            time_ranges (list): 时间范围列表，每个元素为(start_time, end_time)元组
        """
        self.time_ranges = time_ranges
        self.logger.debug(f"设置时间范围列表: {self.time_ranges}")

    def load_models(self, dtoa_model_path: str, pa_model_path: str) -> bool:
        """加载深度学习模型
        
        Args:
            dtoa_model_path: DTOA模型文件路径
            pa_model_path: PA模型文件路径
            
        Returns:
            bool: 是否成功加载模型
        """
        try:
            # 使用 tensorflow 框架
            import tensorflow as tf
            
            self.logger.info("\n=== 开始加载模型 ===")
            
            self.dtoa_model = tf.keras.models.load_model(dtoa_model_path)
            self.logger.info("DTOA模型加载成功")
            self.logger.info(f"DTOA模型加载路径: {dtoa_model_path}")
            
            self.pa_model = tf.keras.models.load_model(pa_model_path)
            self.logger.info("PA模型加载成功")
            self.logger.info(f"PA模型加载路径: {pa_model_path}")
            
            # 保存模型路径
            self.dtoa_model_path = dtoa_model_path
            self.pa_model_path = pa_model_path
            
            return True
            
        except Exception as e:
            self.logger.error(f"加载模型时出错: {str(e)}")
            return False

    def set_temp_dir(self, temp_dir: str):
        """设置临时文件目录
        
        Args:
            temp_dir (str): 临时文件目录路径
            
        Notes:
            同时会更新plotter的临时目录和保存目录
        """
        self.temp_dir = temp_dir
        self.plotter.set_temp_dir(temp_dir)
        self.plotter.set_save_dir(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

    def predict(self, cluster_data: dict) -> Tuple[bool, float, float, int, int, dict, dict]:
        """预测单个聚类结果的PA和DTOA特征
        
        Args:
            cluster_data (dict): 聚类数据字典，包含：
                - slice_idx: 切片索引
                - time_ranges: 时间范围元组 (start_time, end_time)
                - dim_name: 维度名称
                - cluster_idx: 聚类编号
                - points: 聚类数据点

        Returns:
            Tuple[bool, float, float, int, int]: 
                - bool: 预测是否成功
                - float: PA预测置信度
                - float: DTOA预测置信度
                - int: PA预测标签 (0-5，5表示无效)
                - int: DTOA预测标签 (0-4，4表示无效)
                
        Notes:
            - PA预测使用400x80的图像输入
            - DTOA预测使用500x250的图像输入
            - 预测结果会根据置信度阈值进行后处理
            - 临时生成的图像文件会在预测后删除
        """
        try:
            if not self.pa_model:
                self.logger.error("PA模型未正确初始化")
            if not self.dtoa_model:
                self.logger.error("DTOA模型未正确初始化")
            if not self.temp_dir:
                self.logger.error("临时目录未正确初始化")
            if not self.pa_model or not self.dtoa_model or not self.temp_dir:
                self.logger.error("模型或临时目录未正确初始化")
                return False, 0.0, 0.0, -1, -1, {}, {}
            

            self.logger.info(f"预测 切片{cluster_data.get('slice_idx', '?')+1} - {cluster_data.get('dim_name', '?')}维度 - 聚类{cluster_data.get('cluster_idx', '?')}")

            # 使用plot_manager生成图像并获取路径
            image_paths = self.plotter.plot_cluster(cluster_data, for_predict=True)
            # self.logger.debug(f"预测图像绘制完成: {list(image_paths.keys())}")

            # DTOA预测
            dtoa_image = self._preprocess_image(image_paths['DTOA'])
            
            dtoa_pred = self.dtoa_model.predict(dtoa_image, verbose=0)
            
            # 长短类别整合
            dtoa_pred[0, 0] = dtoa_pred[0, 0] + dtoa_pred[0, 1]
            dtoa_pred[0, 1] = dtoa_pred[0, 2]
            dtoa_pred[0, 2] = dtoa_pred[0, 3] + dtoa_pred[0, 4]
            dtoa_pred[0, 3] = dtoa_pred[0, 5]
            dtoa_pred[0, 4] = np.sum(dtoa_pred[0, 6:])
            dtoa_pred[0, 5:] = 0
            
            dtoa_label = np.argmax(dtoa_pred, axis=1)[0]
            dtoa_conf = np.max(dtoa_pred, axis=1)[0]


            # DTOA后处理
            # if dtoa_conf < self.th_dtoa:
            #     dtoa_label = 6
            # if dtoa_label >= 4:
            #     dtoa_label = 4
            # dtoa_pred[0, 6] = np.sum(dtoa_pred[0, 6:])
            if np.round(dtoa_conf, 4) < self.th_dtoa:
                dtoa_label = 4
            if dtoa_label >= 4:
                dtoa_label = 4

            # 调试新增功能，后续删掉
            # 保存DTOA预测结果中置信度大于0的标签及其对应的置信度
            dtoa_conf_dict = {}
            for i, conf in enumerate(dtoa_pred[0, :5]):
                if np.round(conf, 4) > 0:
                    dtoa_conf_dict[i] = conf

            # PA预测
            pa_image = self._preprocess_image(image_paths['PA'])
            
            pa_pred = self.pa_model.predict(pa_image, verbose=0)
            pa_label = np.argmax(pa_pred, axis=1)[0]
            pa_conf = np.max(pa_pred, axis=1)[0]

            # PA后处理
            pa_pred[0, 5] = np.sum(pa_pred[0, 5:])
            if np.round(pa_conf, 4) < self.th_pa:
                pa_label = 9
            if pa_label >= 5:
                pa_label = 5

            # PA特殊处理
            if pa_label >= 5 and np.sum(pa_pred[0, :3]) > 0.99:
                top3_probs = pa_pred[0, :3]
                pa_label = np.argmax(top3_probs)
                pa_conf = np.sum(top3_probs)  # PA维度概率特殊处理
            
            # 保存PA预测结果中置信度大于0的标签及其对应的置信度
            pa_conf_dict = {}
            for i, conf in enumerate(pa_pred[0, :6]):
                if np.round(conf, 4) > 0:
                    pa_conf_dict[i] = conf

            # 清理临时文件
            for path in image_paths.values():
                if os.path.exists(path):
                    os.remove(path)

            # self.logger.info(f"最终预测结果:")
            self.logger.info(f"PA - 标签: {pa_label}, 置信度: {pa_conf:.4f}")
            self.logger.info(f"DTOA - 标签: {dtoa_label}, 置信度: {dtoa_conf:.4f}")

            return True, float(pa_conf), float(dtoa_conf), int(pa_label), int(dtoa_label), dict(pa_conf_dict), dict(dtoa_conf_dict)

        except Exception as e:
            self.logger.error(f"预测出错: {str(e)}")
            import traceback
            self.logger.error(f"错误详情:\n{traceback.format_exc()}")
            return False, 0.0, 0.0, -1, -1, {}, {}

    # def _preprocess_image(self, image_path: str, target_size: Tuple[int, int]) -> np.ndarray:
    #     """预处理图像用于模型输入
    #
    #     Args:
    #         image_path (str): 图像文件路径
    #         target_size (Tuple[int, int]): 目标尺寸 (height, width)
    #
    #     Returns:
    #         np.ndarray: 预处理后的图像数组，形状为(1, height, width, 3)
    #
    #     Notes:
    #         - 图像会被调整到指定尺寸
    #         - 像素值会被归一化到[0,1]范围
    #         - 返回的数组包含batch维度
    #     """
    #     img = Image.open(image_path)
    #     img = img.resize((target_size[1], target_size[0])).convert('RGB')
    #     img_array = np.array(img)
    #     img_array = img_array.astype('float32')
    #     img_array = img_array / 255.0  # 归一化
    #     return np.expand_dims(img_array, axis=0)  # 添加batch维度

    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """预处理图像用于模型输入

        Args:
            image_path (str): 图像文件路径

        Returns:
            np.ndarray: 预处理后的图像数组，形状为(1, height, width, 3)

        Notes:
            - 图像会被调整到指定尺寸
            - 像素值会被归一化到[0,1]范围
            - 返回的数组包含batch维度
        """
        img = Image.open(image_path)
        img = img.convert('RGB')
        img_array = np.array(img)
        img_array = img_array.astype('float32')
        img_array = img_array / 255.0  # 归一化
        return np.expand_dims(img_array, axis=0)  # 添加batch维度

    def load_pa_model(self, model_path: str) -> bool:
        """单独加载PA模型
        
        Args:
            model_path: PA模型文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            import tensorflow as tf
            import os
            
            self.logger.info(f"开始加载PA模型: {model_path}")
            
            # 检查文件是否存在
            if not os.path.exists(model_path):
                self.logger.error(f"PA模型文件不存在: {model_path}")
                return False
                
            # 释放之前的模型内存（如果有）
            if hasattr(self, 'pa_model') and self.pa_model is not None:
                del self.pa_model
                tf.keras.backend.clear_session()
                
            # 加载模型
            self.pa_model = tf.keras.models.load_model(model_path)
            self.pa_model_path = model_path
            
            self.logger.info(f"PA模型加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载PA模型时出错: {str(e)}")
            return False
            
    def load_dtoa_model(self, model_path: str) -> bool:
        """单独加载DTOA模型
        
        Args:
            model_path: DTOA模型文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            import tensorflow as tf
            import os
            
            self.logger.info(f"开始加载DTOA模型: {model_path}")
            
            # 检查文件是否存在
            if not os.path.exists(model_path):
                self.logger.error(f"DTOA模型文件不存在: {model_path}")
                return False
                
            # 释放之前的模型内存（如果有）
            if hasattr(self, 'dtoa_model') and self.dtoa_model is not None:
                del self.dtoa_model
                tf.keras.backend.clear_session()
                
            # 加载模型
            self.dtoa_model = tf.keras.models.load_model(model_path)
            self.dtoa_model_path = model_path
            
            self.logger.info(f"DTOA模型加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载DTOA模型时出错: {str(e)}")
            return False
