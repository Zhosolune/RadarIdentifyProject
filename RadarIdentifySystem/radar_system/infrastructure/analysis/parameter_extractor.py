"""参数提取器基础设施模块

本模块提供雷达信号参数提取功能，从project/cores/params_extractor.py迁移而来。
"""

import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.cluster import DBSCAN
from radar_system.infrastructure.common.logging import model_logger
from radar_system.infrastructure.common.exceptions import ModelError
from radar_system.domain.recognition.entities import RecognitionResult


class ParameterExtractor:
    """参数提取器
    
    负责从识别结果中提取雷达信号参数，包括CF、PW、DOA、PRI等参数。
    
    Attributes:
        default_eps_cf (float): CF维度默认聚类半径
        default_eps_pw (float): PW维度默认聚类半径
        default_eps_pri (float): PRI维度默认聚类半径
        default_eps_doa (float): DOA维度默认聚类半径
        default_min_samples (int): 默认最小样本数
        default_threshold_ratio (float): 默认阈值比例
    """
    
    def __init__(self):
        """初始化参数提取器"""
        # 默认参数配置
        self.default_eps_cf = 2.0
        self.default_eps_pw = 0.2
        self.default_eps_pri = 0.2
        self.default_eps_doa = 10.0
        self.default_min_samples = 3
        self.default_threshold_ratio = 0.1
        
        model_logger.info("参数提取器初始化完成")
    
    def extract_parameters(self, recognition_result: RecognitionResult) -> Dict[str, List[float]]:
        """从识别结果中提取参数
        
        Args:
            recognition_result: 识别结果实体
            
        Returns:
            Dict[str, List[float]]: 提取的参数字典，包含CF、PW、DOA、PRI等
            
        Raises:
            ModelError: 参数提取失败时抛出
        """
        try:
            cluster_data = recognition_result.cluster_candidate.cluster_data
            
            if len(cluster_data) == 0:
                model_logger.warning("聚类数据为空，无法提取参数")
                return self._get_empty_parameters()
            
            model_logger.debug(
                f"开始参数提取 - result_id: {recognition_result.result_id[:8]}..., "
                f"data_points: {len(cluster_data)}"
            )
            
            # 提取各维度参数
            parameters = {}
            
            # 提取CF参数（载频）
            parameters['CF'] = self._extract_grouped_values(
                cluster_data[:, 0],  # CF列
                eps=self.default_eps_cf,
                min_samples=4,
                threshold_ratio=self.default_threshold_ratio
            )
            
            # 提取PW参数（脉宽）
            parameters['PW'] = self._extract_grouped_values(
                cluster_data[:, 1],  # PW列
                eps=self.default_eps_pw,
                min_samples=4,
                threshold_ratio=self.default_threshold_ratio
            )
            
            # 提取DOA参数（方位角）
            parameters['DOA'] = self._extract_doa_values(cluster_data[:, 2])  # DOA列
            
            # 计算并提取PRI参数（脉冲重复间隔）
            if cluster_data.shape[1] > 4:
                dtoa_values = self._calculate_dtoa(cluster_data[:, 4])  # TOA列
                parameters['PRI'] = self._extract_grouped_values(
                    dtoa_values,
                    eps=self.default_eps_pri,
                    min_samples=3,
                    threshold_ratio=self.default_threshold_ratio
                )
            else:
                parameters['PRI'] = []
            
            # 应用谐波抑制
            parameters = self._suppress_harmonics(parameters)
            
            model_logger.info(
                f"参数提取完成 - result_id: {recognition_result.result_id[:8]}..., "
                f"CF: {len(parameters['CF'])}, PW: {len(parameters['PW'])}, "
                f"DOA: {len(parameters['DOA'])}, PRI: {len(parameters['PRI'])}"
            )
            
            return parameters
            
        except Exception as e:
            error = ModelError(
                message=f"参数提取失败: {str(e)}",
                code="PARAMETER_EXTRACTION_ERROR",
                details={
                    "result_id": recognition_result.result_id,
                    "cluster_data_shape": cluster_data.shape if 'cluster_data' in locals() else None
                }
            )
            model_logger.error(str(error), exc_info=True)
            raise error
    
    def _extract_grouped_values(self, data: np.ndarray, eps: float, 
                               min_samples: int, threshold_ratio: float) -> List[float]:
        """提取成组变化的值
        
        Args:
            data: 输入数据数组
            eps: DBSCAN聚类半径
            min_samples: 最小样本数
            threshold_ratio: 阈值比例
            
        Returns:
            List[float]: 提取的成组值列表
        """
        try:
            if len(data) == 0:
                return []
            
            # 将数据转换为二维数组
            data_reshaped = np.array(data).reshape(-1, 1)
            
            # 使用DBSCAN进行聚类
            db = DBSCAN(eps=eps, min_samples=min_samples).fit(data_reshaped)
            labels = db.labels_
            
            # 提取成组变化的值（排除噪声点）
            grouped_values = []
            
            # 计算每个组变值成立的阈值
            clusters_with_multiple_samples = sum(
                1 for label in set(labels) 
                if label != -1 and np.sum(labels == label) >= 2
            )
            expected_min_size = len(data) / max(clusters_with_multiple_samples, 1) * threshold_ratio
            
            for label in set(labels):
                if label == -1:  # 跳过噪声点
                    continue
                
                cluster_mask = labels == label
                cluster_data = data[cluster_mask]
                
                # 检查聚类大小是否满足阈值
                if len(cluster_data) >= max(expected_min_size, 2):
                    # 使用聚类的均值作为代表值
                    grouped_values.append(float(np.mean(cluster_data)))
            
            # 排序并返回
            return sorted(grouped_values)
            
        except Exception as e:
            model_logger.warning(f"成组值提取失败: {str(e)}")
            return []
    
    def _extract_doa_values(self, doa_data: np.ndarray) -> List[float]:
        """提取DOA参数（方位角特殊处理）
        
        Args:
            doa_data: DOA数据数组
            
        Returns:
            List[float]: 提取的DOA值列表
        """
        try:
            # 首先尝试常规的成组值提取
            grouped_values = self._extract_grouped_values(
                doa_data,
                eps=self.default_eps_doa,
                min_samples=3,
                threshold_ratio=self.default_threshold_ratio
            )
            
            # 如果没有提取到成组值，使用特殊处理
            if not grouped_values and len(doa_data) > 2:
                # 排序并取中间值的均值
                sorted_doa = sorted(doa_data)
                middle_values = sorted_doa[1:-1]  # 去掉首尾值
                if middle_values:
                    grouped_values = [float(np.mean(middle_values))]
            
            return grouped_values
            
        except Exception as e:
            model_logger.warning(f"DOA值提取失败: {str(e)}")
            return []
    
    def _calculate_dtoa(self, toa_data: np.ndarray) -> np.ndarray:
        """计算DTOA（时间差）
        
        Args:
            toa_data: TOA数据数组
            
        Returns:
            np.ndarray: DTOA数据数组
        """
        try:
            if len(toa_data) <= 1:
                return np.array([])
            
            # 计算一阶差分
            dtoa = np.diff(toa_data)
            return dtoa
            
        except Exception as e:
            model_logger.warning(f"DTOA计算失败: {str(e)}")
            return np.array([])
    
    def _suppress_harmonics(self, parameters: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """抑制谐波
        
        Args:
            parameters: 原始参数字典
            
        Returns:
            Dict[str, List[float]]: 抑制谐波后的参数字典
        """
        try:
            # 对CF和PRI参数进行谐波抑制
            suppressed_params = parameters.copy()
            
            # CF谐波抑制
            if 'CF' in parameters and len(parameters['CF']) > 1:
                suppressed_params['CF'] = self._remove_harmonics(parameters['CF'])
            
            # PRI谐波抑制
            if 'PRI' in parameters and len(parameters['PRI']) > 1:
                suppressed_params['PRI'] = self._remove_harmonics(parameters['PRI'])
            
            return suppressed_params
            
        except Exception as e:
            model_logger.warning(f"谐波抑制失败: {str(e)}")
            return parameters
    
    def _remove_harmonics(self, values: List[float], tolerance: float = 0.1) -> List[float]:
        """移除谐波分量
        
        Args:
            values: 输入值列表
            tolerance: 谐波判断容差
            
        Returns:
            List[float]: 移除谐波后的值列表
        """
        try:
            if len(values) <= 1:
                return values
            
            sorted_values = sorted(values)
            filtered_values = [sorted_values[0]]  # 保留最小值
            
            for i in range(1, len(sorted_values)):
                current_value = sorted_values[i]
                is_harmonic = False
                
                # 检查是否为已有值的谐波
                for base_value in filtered_values:
                    if base_value > 0:
                        ratio = current_value / base_value
                        # 检查是否接近整数倍
                        if abs(ratio - round(ratio)) < tolerance:
                            is_harmonic = True
                            break
                
                if not is_harmonic:
                    filtered_values.append(current_value)
            
            return filtered_values
            
        except Exception as e:
            model_logger.warning(f"谐波移除失败: {str(e)}")
            return values
    
    def _get_empty_parameters(self) -> Dict[str, List[float]]:
        """获取空参数字典
        
        Returns:
            Dict[str, List[float]]: 空参数字典
        """
        return {
            'CF': [],
            'PW': [],
            'DOA': [],
            'PRI': []
        }
    
    def update_config(self, **kwargs):
        """更新配置参数
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self, f'default_{key}'):
                setattr(self, f'default_{key}', value)
                model_logger.debug(f"参数提取器配置已更新: {key} = {value}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            Dict[str, Any]: 当前配置字典
        """
        return {
            'eps_cf': self.default_eps_cf,
            'eps_pw': self.default_eps_pw,
            'eps_pri': self.default_eps_pri,
            'eps_doa': self.default_eps_doa,
            'min_samples': self.default_min_samples,
            'threshold_ratio': self.default_threshold_ratio
        }
