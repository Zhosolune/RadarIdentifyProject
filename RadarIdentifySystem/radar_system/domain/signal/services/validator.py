"""信号验证服务模块

本模块实现了雷达信号数据的验证服务，确保数据满足处理要求。
"""
from typing import Dict, Tuple
import numpy as np

from radar_system.domain.signal.entities.signal import SignalData
from radar_system.infrastructure.common.exceptions import ValidationError
from radar_system.infrastructure.common.logging import system_logger

class SignalValidator:
    """信号验证服务
    
    提供雷达信号数据的验证功能，包括数据格式、参数范围等验证。
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
    
    def validate_signal(self, signal: SignalData) -> Tuple[bool, str]:
        """验证信号数据
        
        执行完整的信号数据验证流程。
        
        Args:
            signal: 待验证的信号数据
            
        Returns:
            tuple: (是否有效, 错误消息)
        """
        try:            
            # 参数范围验证
            valid, message = self._validate_parameter_ranges(signal.raw_data)
            if not valid:
                return False, message
            
            # 确定频段类型
            band_type = self._determine_band_type(signal.raw_data[:, 0])
            if band_type:
                signal.band_type = band_type
            else:
                return False, "无法确定信号频段类型"
            
            return True, "验证通过"
            
        except Exception as e:
            system_logger.error(f"信号验证出错: {str(e)}")
            return False, f"验证过程出错: {str(e)}"
    
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
