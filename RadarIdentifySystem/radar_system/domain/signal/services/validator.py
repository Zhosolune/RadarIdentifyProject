"""信号验证服务模块

本模块实现了雷达信号数据的验证服务，确保数据满足处理要求。
支持自动数据修复功能，以改善用户体验。
"""
from typing import Dict, Tuple, List
import numpy as np

from radar_system.domain.signal.entities.signal import SignalData
from radar_system.infrastructure.common.exceptions import ValidationError
from radar_system.infrastructure.common.logging import system_logger

class SignalValidator:
    """信号验证服务

    提供雷达信号数据的验证功能，包括数据格式、参数范围等验证。
    支持自动数据修复功能，以改善用户体验。
    """

    # 信号参数范围定义
    VALID_RANGES = {
        'CF': (1000.0, 12000.0),  # MHz
        'PW': (0.0, 400.0),      # us
        'DOA': (0.0, 360.0),   # degree
        'PA': (0.0, 110.0),      # dB?
        'TOA': (0.0, float('inf')) # ms
    }
    
    # 波段定义
    BAND_RANGES = {
        'L波段': (1000.0, 2000.0),
        'S波段': (2000.0, 4000.0),
        'C波段': (4000.0, 8000.0),
        'X波段': (8000.0, 12000.0)
    }

    def __init__(self,
                 enable_data_repair: bool = True,
                 remove_out_of_range: bool = True,
                 fix_toa_ordering: bool = True):
        """初始化信号验证器

        Args:
            enable_data_repair: 是否启用数据修复功能，默认True
            remove_out_of_range: 是否删除超出范围的数据，默认True
            fix_toa_ordering: 是否修复TOA非单调递增问题，默认True
        """
        self.enable_data_repair = enable_data_repair
        self.remove_out_of_range = remove_out_of_range
        self.fix_toa_ordering = fix_toa_ordering
    
    def validate_signal(self, signal: SignalData) -> Tuple[bool, str]:
        """验证信号数据

        执行完整的信号数据验证流程，支持自动修复功能。

        Args:
            signal: 待验证的信号数据

        Returns:
            tuple: (是否有效, 错误消息)
        """
        try:
            # 参数范围验证
            valid, message = self._validate_parameter_ranges(signal.raw_data)
            if not valid:
                # 如果启用了数据修复功能，尝试修复
                if self.enable_data_repair:
                    repaired_data, repair_messages = self.repair_signal_data(signal)
                    if repaired_data is not None:
                        # 修复成功，用修复后的数据替换原始数据
                        signal.raw_data = repaired_data.raw_data
                        signal.band_type = repaired_data.band_type

                        # 重新验证修复后的数据
                        valid, message = self._validate_parameter_ranges(signal.raw_data)
                        if not valid:
                            return False, f"数据修复后仍然验证失败: {message}"
                    else:
                        return False, f"数据修复失败: {message}"
                else:
                    return False, message

            # 确定频段类型（如果还没有确定）
            if not hasattr(signal, 'band_type') or signal.band_type is None:
                band_type = self._determine_band_type(signal.raw_data[:, 0])
                if band_type:
                    signal.band_type = band_type
                else:
                    return False, "无法确定信号频段类型"

            return True, "验证通过"

        except Exception as e:
            system_logger.error(f"信号验证出错: {str(e)}")
            return False, f"验证过程出错: {str(e)}"

    def repair_signal_data(self, signal_data: SignalData) -> Tuple[SignalData, List[str]]:
        """修复信号数据

        对信号数据执行自动修复操作，包括删除超出范围的数据和修复TOA排序问题。

        Args:
            signal_data: 待修复的信号数据

        Returns:
            tuple: (修复后的信号数据, 修复操作描述列表)，如果修复失败则返回(None, [])
        """
        try:
            data = signal_data.raw_data.copy()
            repair_messages = []
            original_rows = data.shape[0]

            # 1. 删除超出范围的数据
            if self.remove_out_of_range:
                data, range_messages = self._remove_out_of_range_data(data)
                repair_messages.extend(range_messages)

            # 2. 修复TOA排序问题
            if self.fix_toa_ordering:
                data, toa_messages = self._fix_toa_ordering(data)
                repair_messages.extend(toa_messages)

            # 检查修复后是否还有数据
            if data.shape[0] == 0:
                system_logger.warning("数据修复: 所有数据都被删除，修复失败")
                return None, ["所有数据都被删除，修复失败"]

            # 创建修复后的信号数据对象
            repaired_signal = SignalData(
                id=signal_data.id + '_repaired',
                raw_data=data,
                expected_slices=signal_data.expected_slices
            )

            # 确定频段类型
            band_type = self._determine_band_type(data[:, 0])
            if band_type:
                repaired_signal.band_type = band_type

            # 记录总体修复信息
            final_rows = data.shape[0]
            removed_rows = original_rows - final_rows
            if removed_rows > 0:
                summary_message = f"数据修复完成 - 原始行数: {original_rows}, 修复后行数: {final_rows}, 删除行数: {removed_rows}"
                system_logger.warning(summary_message)
                repair_messages.append(summary_message)

            return repaired_signal, repair_messages

        except Exception as e:
            error_message = f"数据修复过程出错: {str(e)}"
            system_logger.error(error_message)
            return None, [error_message]

    def _validate_parameter_range(self,
                                  data_column: np.ndarray,
                                  param_name: str,
                                  valid_range: Tuple[float, float],
                                  unit: str) -> Tuple[np.ndarray, List[str]]:
        """验证单个参数的范围

        Args:
            data_column: 参数数据列
            param_name: 参数名称（如'CF', 'PW'等）
            valid_range: 有效范围元组 (min_value, max_value)
            unit: 参数单位（如'MHz', 'μs', '度', 'dB', 'ms'）

        Returns:
            tuple: (有效数据的布尔掩码, 修复消息列表)
        """
        repair_messages = []

        # 对于TOA参数，只检查下限
        if param_name == 'TOA':
            valid_mask = data_column >= valid_range[0]
            invalid_count = np.sum(~valid_mask)
            if invalid_count > 0:
                message = f"数据修复: 删除超范围数据 - {param_name}小于{valid_range[0]}{unit} - 影响行数: {invalid_count}"
                system_logger.warning(message)
                repair_messages.append(message)
        else:
            # 对于其他参数，检查上下限
            valid_mask = (data_column >= valid_range[0]) & (data_column <= valid_range[1])
            invalid_count = np.sum(~valid_mask)
            if invalid_count > 0:
                message = f"数据修复: 删除超范围数据 - {param_name}超出{valid_range[0]}-{valid_range[1]}{unit}范围 - 影响行数: {invalid_count}"
                system_logger.warning(message)
                repair_messages.append(message)

        return valid_mask, repair_messages

    def _remove_out_of_range_data(self, data: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """删除超出范围的数据

        删除CF、PW、DOA、PA、TOA任一参数超出配置范围的整行数据。

        Args:
            data: 信号数据数组 (N, 5) [CF, PW, DOA, PA, TOA]

        Returns:
            tuple: (清理后的数据数组, 修复操作描述列表)
        """
        repair_messages = []

        # 创建有效数据的布尔掩码
        valid_mask = np.ones(data.shape[0], dtype=bool)

        # 参数配置：(列索引, 参数名, 单位)
        parameter_configs = [
            (0, 'CF', 'MHz'),
            (1, 'PW', 'μs'),
            (2, 'DOA', '度'),
            (3, 'PA', 'dB'),
            (4, 'TOA', 'ms')
        ]

        # 循环验证每个参数
        for col_index, param_name, unit in parameter_configs:
            param_valid_mask, param_messages = self._validate_parameter_range(
                data_column=data[:, col_index],
                param_name=param_name,
                valid_range=self.VALID_RANGES[param_name],
                unit=unit
            )

            # 更新总体有效掩码
            valid_mask &= param_valid_mask

            # 添加修复消息
            repair_messages.extend(param_messages)

        # 应用掩码，保留有效数据
        cleaned_data = data[valid_mask]

        return cleaned_data, repair_messages

    def _fix_toa_ordering(self, data: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """修复TOA排序问题

        对整个数据集按TOA列进行升序排序，确保TOA单调递增。

        Args:
            data: 信号数据数组 (N, 5) [CF, PW, DOA, PA, TOA]

        Returns:
            tuple: (排序后的数据数组, 修复操作描述列表)
        """
        repair_messages = []

        # 检查TOA是否已经单调递增
        toa_data = data[:, 4]
        if np.all(np.diff(toa_data) >= 0):
            # TOA已经单调递增，无需修复
            return data, repair_messages

        # 按TOA列进行升序排序
        sort_indices = np.argsort(data[:, 4])
        sorted_data = data[sort_indices]

        # 记录修复操作
        message = f"数据修复: TOA排序修复 - 对{data.shape[0]}行数据按TOA进行升序排序 - 影响行数: {data.shape[0]}"
        system_logger.warning(message)
        repair_messages.append(message)

        return sorted_data, repair_messages
    
    def _validate_parameter_ranges(self, data: np.ndarray) -> Tuple[bool, str]:
        """验证参数范围
        
        检查各个参数是否在有效范围内。
        
        Args:
            data: 信号数据数组
            
        Returns:
            tuple: (是否有效, 错误消息)
        """
        try:
            # 检查CF范围
            cf_data = data[:, 0]
            if not np.all((cf_data >= self.VALID_RANGES['CF'][0]) & 
                         (cf_data <= self.VALID_RANGES['CF'][1])):
                return False, "CF超出有效范围"
            
            # 检查PW范围
            pw_data = data[:, 1]
            if not np.all((pw_data >= self.VALID_RANGES['PW'][0]) & 
                         (pw_data <= self.VALID_RANGES['PW'][1])):
                return False, "PW超出有效范围"
            
            # 检查DOA范围
            doa_data = data[:, 2]
            if not np.all((doa_data >= self.VALID_RANGES['DOA'][0]) & 
                         (doa_data <= self.VALID_RANGES['DOA'][1])):
                return False, "DOA超出有效范围"
            
            # 检查PA范围
            pa_data = data[:, 3]
            if not np.all((pa_data >= self.VALID_RANGES['PA'][0]) & 
                         (pa_data <= self.VALID_RANGES['PA'][1])):
                return False, "PA超出有效范围"
            
            # 检查TOA范围
            toa_data = data[:, 4]
            if not np.all(toa_data >= self.VALID_RANGES['TOA'][0]):
                return False, "TOA超出有效范围"
            
            # 检查TOA是否单调递增
            if not np.all(np.diff(toa_data) >= 0):
                return False, "TOA不是单调递增"
            
            return True, "参数范围验证通过"
            
        except Exception as e:
            raise ValidationError(f"参数范围验证出错: {str(e)}")
    
    def _determine_band_type(self, cf_data: np.ndarray) -> str:
        """确定信号频段类型
        
        根据CF值确定信号所属的频段。
        
        Args:
            cf_data: CF数据数组
            
        Returns:
            str: 频段类型名称，如果无法确定则返回None
        """
        # 计算CF的中位数
        cf_median = np.median(cf_data)
        # 获取CF的最大值和最小值
        cf_max = np.max(cf_data)
        cf_min = np.min(cf_data)
        
        # 判断所属频段
        for band_name, (band_min, band_max) in self.BAND_RANGES.items():
            if (band_min <= cf_median <= band_max) and (cf_max <= band_max) and (cf_min >= band_min):
                return band_name
        
        return None
