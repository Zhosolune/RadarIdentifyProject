"""UI参数解析工具

本模块提供从UI控件解析聚类参数的工具函数。
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QLineEdit

from radar_system.infrastructure.common.logging import system_logger


class UIParamsParser:
    """UI参数解析器
    
    负责从主窗口的UI控件中解析聚类参数。
    """
    
    @staticmethod
    def extract_clustering_params_from_window(window) -> Dict[str, Any]:
        """从主窗口提取聚类参数
        
        Args:
            window: 主窗口实例，包含cluster_params属性
            
        Returns:
            Dict[str, Any]: 聚类参数字典
                - epsilon_cf: CF维度邻域半径
                - epsilon_pw: PW维度邻域半径  
                - min_pts: 最小点数
        """
        try:
            params = {}
            
            # 检查窗口是否有cluster_params属性
            if not hasattr(window, 'cluster_params'):
                system_logger.warning("主窗口缺少cluster_params属性，返回空参数字典")
                return params
            
            # 提取各个参数
            param_mappings = {
                'epsilon_cf': 'epsilon_cf',
                'epsilon_pw': 'epsilon_pw', 
                'min_pts': 'min_pts'
            }
            
            for ui_key, param_key in param_mappings.items():
                if ui_key in window.cluster_params:
                    widget = window.cluster_params[ui_key]
                    if isinstance(widget, QLineEdit):
                        value = widget.text().strip()
                        params[param_key] = value
                        system_logger.debug(f"提取UI参数: {param_key} = {value}")
                    else:
                        system_logger.warning(f"UI控件 {ui_key} 不是QLineEdit类型: {type(widget)}")
                else:
                    system_logger.warning(f"UI控件 {ui_key} 不存在于cluster_params中")
            
            return params
            
        except Exception as e:
            error_msg = f"从UI提取聚类参数失败: {str(e)}"
            system_logger.error(error_msg)
            return {}
    
    @staticmethod
    def validate_clustering_param_value(value: str, param_name: str) -> Optional[float]:
        """验证聚类参数值
        
        Args:
            value: 参数值字符串
            param_name: 参数名称
            
        Returns:
            Optional[float]: 验证后的浮点数值，无效时返回None
        """
        try:
            if not value or value.strip() == "":
                return None
            
            # 转换为浮点数
            float_value = float(value.strip())
            
            # 验证值的合理性
            if float_value <= 0:
                system_logger.warning(f"参数 {param_name} 的值必须大于0，当前值: {float_value}")
                return None
            
            # 对特定参数进行额外验证
            if param_name == 'min_pts' and float_value != int(float_value):
                system_logger.warning(f"参数 {param_name} 必须为整数，当前值: {float_value}")
                return None
            
            return float_value
            
        except ValueError:
            system_logger.warning(f"参数 {param_name} 的值无法转换为数字: {value}")
            return None
        except Exception as e:
            system_logger.error(f"验证参数 {param_name} 时出错: {str(e)}")
            return None
    
    @staticmethod
    def get_validated_params_dict(window) -> Dict[str, float]:
        """获取验证后的参数字典
        
        Args:
            window: 主窗口实例
            
        Returns:
            Dict[str, float]: 验证后的参数字典，只包含有效的参数
        """
        raw_params = UIParamsParser.extract_clustering_params_from_window(window)
        validated_params = {}
        
        for param_name, param_value in raw_params.items():
            validated_value = UIParamsParser.validate_clustering_param_value(param_value, param_name)
            if validated_value is not None:
                # min_pts需要转换为整数
                if param_name == 'min_pts':
                    validated_params[param_name] = int(validated_value)
                else:
                    validated_params[param_name] = validated_value
        
        system_logger.debug(f"验证后的聚类参数: {validated_params}")
        return validated_params
