"""文件存储管理器

负责管理文件的存储，包括创建目录、保存图像等功能。
"""

import os
from pathlib import Path
from PIL import Image
import numpy as np
from typing import Dict, Optional, Tuple
from radar_system.infrastructure.common.logging import persistence_logger
from radar_system.infrastructure.common.config import ConfigManager

class FileStorage:
    """文件存储管理器
    
    负责管理文件的存储，包括创建目录、保存图像等功能。
    """
    
    def __init__(self):
        """初始化文件存储管理器"""
        self.config_manager = ConfigManager.get_instance()
        
        # 确保目录存在
        if self.config_manager.plotting.temp_dir:
            self.ensure_dir_exists(self.config_manager.plotting.temp_dir)
        if self.config_manager.plotting.save_dir:
            self.ensure_dir_exists(self.config_manager.plotting.save_dir)
    
    def save_slice_images(self, image_data: Dict[str, np.ndarray], 
                         slice_idx: int, is_temp: bool = False) -> Dict[str, str]:
        """保存切片的所有维度图像
        
        Args:
            image_data (Dict[str, np.ndarray]): 图像数据字典，键为维度名称
            slice_idx (int): 切片索引
            is_temp (bool): 是否保存为临时文件，默认False
            
        Returns:
            Dict[str, str]: 图像路径字典，键为维度名称，值为图像文件路径
        """
        try:
            # 确定目标目录
            target_dir = (self.config_manager.plotting.temp_dir if is_temp 
                         else self.config_manager.plotting.save_dir)
            if not target_dir:
                persistence_logger.error("未设置目标目录")
                return {}
            
            # 生成基础文件名
            base_name = f"temp_{np.random.randint(10000)}" if is_temp else f"slice{slice_idx}"
            
            # 保存所有维度的图像
            image_paths = {}
            for dim_name, img_data in image_data.items():
                file_name = f"{base_name}_{dim_name.upper()}.png"
                file_path = self.save_image(img_data, file_name, is_temp)
                if file_path:
                    image_paths[dim_name] = file_path
            
            return image_paths
            
        except Exception as e:
            persistence_logger.error(f"保存切片图像失败: {str(e)}")
            return {}
    
    def save_cluster_images(self, image_data: Dict[str, np.ndarray],
                          slice_idx: int, cluster_idx: int,
                          dim_name: str, is_temp: bool = False) -> Dict[str, str]:
        """保存聚类结果的图像
        
        Args:
            image_data (Dict[str, np.ndarray]): 图像数据字典，键为维度名称
            slice_idx (int): 切片索引
            cluster_idx (int): 聚类编号
            dim_name (str): 聚类维度名称
            is_temp (bool): 是否保存为临时文件，默认False
            
        Returns:
            Dict[str, str]: 图像路径字典，键为维度名称，值为图像文件路径
        """
        try:
            # 确定目标目录
            target_dir = (self.config_manager.plotting.temp_dir if is_temp 
                         else self.config_manager.plotting.save_dir)
            if not target_dir:
                persistence_logger.error("未设置目标目录")
                return {}
            
            # 生成基础文件名
            base_name = (f"temp_{np.random.randint(10000)}" if is_temp else 
                        f"slice{slice_idx}_{dim_name}_cluster{cluster_idx}")
            
            # 保存所有维度的图像
            image_paths = {}
            for dim_name, img_data in image_data.items():
                file_name = f"{base_name}_{dim_name.lower()}.png"
                file_path = self.save_image(img_data, file_name, is_temp)
                if file_path:
                    image_paths[dim_name] = file_path
            
            return image_paths
            
        except Exception as e:
            persistence_logger.error(f"保存聚类图像失败: {str(e)}")
            return {}
    
    def save_image(self, image_data: np.ndarray, file_name: str, 
                  is_temp: bool = False) -> str:
        """保存图像文件
        
        Args:
            image_data (np.ndarray): 图像数据数组
            file_name (str): 文件名
            is_temp (bool): 是否保存为临时文件，默认False
            
        Returns:
            str: 保存的图像文件完整路径，失败时返回空字符串
            
        Notes:
            - 如果is_temp为True，则保存到临时目录
            - 如果is_temp为False，则保存到保存目录
            - 图像数据应为二维numpy数组，值范围0-1或0-255
        """
        try:
            # 确定目标目录
            target_dir = (self.config_manager.plotting.temp_dir if is_temp 
                         else self.config_manager.plotting.save_dir)
            if not target_dir:
                persistence_logger.error("未设置目标目录")
                return ""
                
            # 确保文件扩展名为.png
            if not file_name.lower().endswith('.png'):
                file_name += '.png'
                
            # 构建完整文件路径
            file_path = os.path.join(target_dir, file_name)
            
            # 将数据转换为8位无符号整数
            if image_data.dtype != np.uint8:
                if image_data.max() <= 1:
                    image_data = (image_data * 255).astype(np.uint8)
                else:
                    image_data = image_data.astype(np.uint8)
            
            # 保存图像
            Image.fromarray(image_data).save(file_path)
            persistence_logger.debug(f"图像已保存: {file_path}")
            
            return file_path
            
        except Exception as e:
            persistence_logger.error(f"保存图像失败: {str(e)}")
            return ""
            
    def ensure_dir_exists(self, dir_path: str) -> bool:
        """确保目录存在
        
        Args:
            dir_path (str): 目录路径
            
        Returns:
            bool: 目录是否存在或创建成功
        """
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                persistence_logger.debug(f"创建目录: {dir_path}")
            return True
        except Exception as e:
            persistence_logger.error(f"创建目录失败: {str(e)}")
            return False
