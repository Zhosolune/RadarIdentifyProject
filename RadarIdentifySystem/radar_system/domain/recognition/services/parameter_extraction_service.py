"""参数提取领域服务模块

本模块提供参数提取相关的领域服务实现。
"""

from typing import List, Dict, Any, Optional
import numpy as np

from radar_system.domain.recognition.entities import (
    RecognitionResult, RecognitionStatus, RecognitionParams
)
from radar_system.infrastructure.analysis import ParameterExtractor
from radar_system.infrastructure.common.exceptions import (
    ValidationError, ProcessingError
)
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.thread_safe_signal_emitter import ThreadSafeSignalEmitter


class ParameterExtractionService:
    """参数提取领域服务
    
    负责协调参数提取过程，包括：
    - CF、PW、DOA、PRI参数提取
    - 参数验证和过滤
    - 参数统计分析
    - 参数质量评估
    """
    
    def __init__(
        self,
        recognition_params: Optional[RecognitionParams] = None,
        signal_emitter: Optional[ThreadSafeSignalEmitter] = None
    ):
        """初始化参数提取服务
        
        Args:
            recognition_params: 识别参数配置
            signal_emitter: 信号发射器
        """
        self._recognition_params = recognition_params or RecognitionParams()
        self._signal_emitter = signal_emitter or ThreadSafeSignalEmitter()
        
        # 初始化参数提取器
        self._extractor = ParameterExtractor()
        
        system_logger.info("参数提取服务初始化完成")
    
    def extract_parameters_from_result(
        self, 
        recognition_result: RecognitionResult
    ) -> Dict[str, List[float]]:
        """从识别结果中提取参数
        
        Args:
            recognition_result: 识别结果
            
        Returns:
            提取的参数字典
            
        Raises:
            ValidationError: 数据验证失败
            ProcessingError: 参数提取失败
        """
        try:
            # 验证识别结果
            self._validate_recognition_result(recognition_result)
            
            # 检查识别状态
            if recognition_result.status != RecognitionStatus.PASSED:
                system_logger.warning(f"跳过未通过识别的结果 - result_id: {recognition_result.result_id[:8]}...")
                return {}

            # 执行参数提取
            parameters = self._extractor.extract_parameters(recognition_result)

            # 验证和过滤参数
            filtered_parameters = self._filter_and_validate_parameters(parameters)

            # 更新识别结果中的参数
            recognition_result.extracted_params = filtered_parameters

            system_logger.info(f"参数提取完成 - result_id: {recognition_result.result_id[:8]}..., "
                              f"CF: {len(filtered_parameters.get('CF', []))}, "
                              f"PW: {len(filtered_parameters.get('PW', []))}, "
                              f"DOA: {len(filtered_parameters.get('DOA', []))}, "
                              f"PRI: {len(filtered_parameters.get('PRI', []))}")

            return filtered_parameters

        except Exception as e:
            error_msg = f"参数提取失败 - result_id: {recognition_result.result_id[:8]}...: {str(e)}"
            system_logger.error(error_msg)
            raise ProcessingError(error_msg) from e
    
    def batch_extract_parameters(
        self, 
        recognition_results: List[RecognitionResult]
    ) -> Dict[str, List[float]]:
        """批量提取参数
        
        Args:
            recognition_results: 识别结果列表
            
        Returns:
            合并的参数字典
        """
        merged_parameters = {
            'CF': [],
            'PW': [],
            'DOA': [],
            'PRI': []
        }
        
        successful_extractions = 0
        
        for i, result in enumerate(recognition_results):
            try:
                parameters = self.extract_parameters_from_result(result)
                
                # 合并参数
                for param_type, values in parameters.items():
                    if param_type in merged_parameters:
                        merged_parameters[param_type].extend(values)
                
                if parameters:
                    successful_extractions += 1
                
                # 发送进度信号
                progress = (i + 1) / len(recognition_results) * 100
                self._signal_emitter.emit_log_signal(
                    f"参数提取进度: {progress:.1f}% ({i + 1}/{len(recognition_results)})"
                )
                
            except Exception as e:
                system_logger.warning(f"跳过参数提取失败的结果 - result_id: {result.result_id[:8]}...: {str(e)}")
                continue

        # 对合并的参数进行最终处理
        final_parameters = self._post_process_merged_parameters(merged_parameters)

        system_logger.info(f"批量参数提取完成 - 总数: {len(recognition_results)}, "
                          f"成功: {successful_extractions}, "
                          f"最终参数 - CF: {len(final_parameters['CF'])}, "
                          f"PW: {len(final_parameters['PW'])}, "
                          f"DOA: {len(final_parameters['DOA'])}, "
                          f"PRI: {len(final_parameters['PRI'])}")
        
        return final_parameters
    
    def analyze_parameter_distribution(
        self, 
        parameters: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, float]]:
        """分析参数分布
        
        Args:
            parameters: 参数字典
            
        Returns:
            参数分布统计信息
        """
        distribution_stats = {}
        
        for param_type, values in parameters.items():
            if not values:
                distribution_stats[param_type] = {
                    'count': 0,
                    'mean': 0.0,
                    'std': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'median': 0.0
                }
                continue
            
            values_array = np.array(values)
            distribution_stats[param_type] = {
                'count': len(values),
                'mean': float(np.mean(values_array)),
                'std': float(np.std(values_array)),
                'min': float(np.min(values_array)),
                'max': float(np.max(values_array)),
                'median': float(np.median(values_array))
            }
        
        system_logger.info(f"参数分布分析完成 - 参数类型数: {len(distribution_stats)}")
        return distribution_stats
    
    def get_parameter_quality_metrics(
        self, 
        parameters: Dict[str, List[float]]
    ) -> Dict[str, float]:
        """获取参数质量指标
        
        Args:
            parameters: 参数字典
            
        Returns:
            参数质量指标
        """
        total_params = sum(len(values) for values in parameters.values())
        
        if total_params == 0:
            return {
                'total_parameters': 0,
                'parameter_density': 0.0,
                'cf_coverage': 0.0,
                'pw_coverage': 0.0,
                'doa_coverage': 0.0,
                'pri_coverage': 0.0
            }
        
        return {
            'total_parameters': total_params,
            'parameter_density': total_params / max(1, len([p for p in parameters.values() if p])),
            'cf_coverage': len(parameters.get('CF', [])) / total_params * 100,
            'pw_coverage': len(parameters.get('PW', [])) / total_params * 100,
            'doa_coverage': len(parameters.get('DOA', [])) / total_params * 100,
            'pri_coverage': len(parameters.get('PRI', [])) / total_params * 100
        }
    
    def _validate_recognition_result(self, recognition_result: RecognitionResult) -> None:
        """验证识别结果
        
        Args:
            recognition_result: 识别结果
            
        Raises:
            ValidationError: 验证失败
        """
        if recognition_result is None:
            raise ValidationError("识别结果不能为空")
        
        if recognition_result.cluster_candidate is None:
            raise ValidationError("识别结果中的聚类候选不能为空")
        
        if recognition_result.cluster_candidate.cluster_data is None:
            raise ValidationError("聚类数据不能为空")
    
    def _filter_and_validate_parameters(
        self, 
        parameters: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        """过滤和验证参数
        
        Args:
            parameters: 原始参数字典
            
        Returns:
            过滤后的参数字典
        """
        filtered_parameters = {}
        
        for param_type, values in parameters.items():
            if not values:
                filtered_parameters[param_type] = []
                continue
            
            # 移除异常值
            filtered_values = self._remove_outliers(values, param_type)
            
            # 应用参数范围限制
            range_limited_values = self._apply_parameter_ranges(filtered_values, param_type)
            
            filtered_parameters[param_type] = range_limited_values
        
        return filtered_parameters
    
    def _remove_outliers(self, values: List[float], param_type: str) -> List[float]:
        """移除异常值
        
        Args:
            values: 参数值列表
            param_type: 参数类型
            
        Returns:
            移除异常值后的参数列表
        """
        if len(values) < 3:
            return values
        
        values_array = np.array(values)
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        filtered_values = [v for v in values if lower_bound <= v <= upper_bound]
        
        if len(filtered_values) != len(values):
            system_logger.debug(f"{param_type}参数异常值移除: {len(values)} -> {len(filtered_values)}")

        return filtered_values
    
    def _apply_parameter_ranges(self, values: List[float], param_type: str) -> List[float]:
        """应用参数范围限制
        
        Args:
            values: 参数值列表
            param_type: 参数类型
            
        Returns:
            范围限制后的参数列表
        """
        # 根据参数类型应用不同的范围限制
        range_limits = {
            'CF': (0, 20000),  # MHz
            'PW': (0, 1000),   # μs
            'DOA': (-180, 180), # 度
            'PRI': (0, 10000)   # μs
        }
        
        if param_type not in range_limits:
            return values
        
        min_val, max_val = range_limits[param_type]
        filtered_values = [v for v in values if min_val <= v <= max_val]
        
        if len(filtered_values) != len(values):
            system_logger.debug(f"{param_type}参数范围过滤: {len(values)} -> {len(filtered_values)}")

        return filtered_values
    
    def _post_process_merged_parameters(
        self, 
        merged_parameters: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        """后处理合并的参数
        
        Args:
            merged_parameters: 合并的参数字典
            
        Returns:
            后处理的参数字典
        """
        processed_parameters = {}
        
        for param_type, values in merged_parameters.items():
            if not values:
                processed_parameters[param_type] = []
                continue
            
            # 去重
            unique_values = list(set(values))
            
            # 排序
            sorted_values = sorted(unique_values)
            
            processed_parameters[param_type] = sorted_values
        
        return processed_parameters
