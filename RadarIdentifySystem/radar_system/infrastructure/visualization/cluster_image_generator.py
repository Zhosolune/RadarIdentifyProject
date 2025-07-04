"""聚类图像生成器基础设施模块

本模块提供聚类数据的图像生成功能，用于神经网络预测。
"""

import os
import uuid
from typing import Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
from radar_system.infrastructure.common.logging import model_logger
from radar_system.infrastructure.common.exceptions import ResourceError
from radar_system.domain.recognition.entities import ClusterCandidate


class ClusterImageGenerator:
    """聚类图像生成器
    
    负责将聚类数据转换为用于神经网络预测的图像文件。
    
    Attributes:
        output_dir (Path): 图像输出目录
        temp_dir (Path): 临时文件目录
        image_configs (dict): 图像生成配置
    """
    
    def __init__(self, output_dir: str, temp_dir: Optional[str] = None):
        """初始化聚类图像生成器
        
        Args:
            output_dir: 图像输出目录
            temp_dir: 临时文件目录，默认为output_dir/temp
        """
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir) if temp_dir else self.output_dir / "temp"
        
        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 图像生成配置
        self.image_configs = {
            'PA': {
                'size': (400, 80),  # (width, height)
                'dpi': 100,
                'format': 'PNG'
            },
            'DTOA': {
                'size': (500, 250),  # (width, height)
                'dpi': 100,
                'format': 'PNG'
            }
        }
        
        model_logger.info(f"聚类图像生成器初始化完成 - 输出目录: {self.output_dir}")
    
    def generate_cluster_images(self, cluster_candidate: ClusterCandidate, 
                              for_prediction: bool = True) -> Dict[str, str]:
        """为聚类候选生成PA和DTOA图像
        
        Args:
            cluster_candidate: 聚类候选实体
            for_prediction: 是否用于预测（影响文件保存位置）
            
        Returns:
            Dict[str, str]: 包含PA和DTOA图像路径的字典
            
        Raises:
            ResourceError: 图像生成失败时抛出
        """
        try:
            image_paths = {}
            
            # 生成基础文件名
            base_name = self._generate_base_name(cluster_candidate)
            
            # 选择保存目录
            save_dir = self.temp_dir if for_prediction else self.output_dir
            
            # 生成PA图像
            pa_path = self._generate_pa_image(
                cluster_candidate.cluster_data,
                save_dir / f"{base_name}_PA.png"
            )
            image_paths['PA'] = str(pa_path)
            
            # 生成DTOA图像
            dtoa_path = self._generate_dtoa_image(
                cluster_candidate.cluster_data,
                save_dir / f"{base_name}_DTOA.png"
            )
            image_paths['DTOA'] = str(dtoa_path)
            
            model_logger.info(
                f"聚类图像生成完成 - cluster_id: {cluster_candidate.cluster_id[:8]}..., "
                f"PA: {pa_path.name}, DTOA: {dtoa_path.name}"
            )
            
            return image_paths
            
        except Exception as e:
            error = ResourceError(
                message=f"聚类图像生成失败: {str(e)}",
                resource_type="cluster_image",
                resource_id=cluster_candidate.cluster_id
            )
            model_logger.error(str(error), exc_info=True)
            raise error
    
    def _generate_base_name(self, cluster_candidate: ClusterCandidate) -> str:
        """生成基础文件名
        
        Args:
            cluster_candidate: 聚类候选实体
            
        Returns:
            str: 基础文件名
        """
        return (
            f"slice_{cluster_candidate.slice_index + 1}_"
            f"{cluster_candidate.dimension_type.value}_"
            f"cluster_{cluster_candidate.cluster_index}_"
            f"{cluster_candidate.cluster_id[:8]}"
        )
    
    def _generate_pa_image(self, cluster_data: np.ndarray, output_path: Path) -> Path:
        """生成PA图像
        
        Args:
            cluster_data: 聚类数据
            output_path: 输出路径
            
        Returns:
            Path: 生成的图像路径
        """
        try:
            # 提取PA数据（假设在第3列，索引为2）
            if cluster_data.shape[1] <= 2:
                raise ValueError("数据维度不足，无法提取PA数据")
            
            pa_data = cluster_data[:, 2]  # PA列
            
            # 生成PA图像（这里简化为基于数据生成二值化图像）
            config = self.image_configs['PA']
            image = self._create_signal_image(pa_data, config['size'])
            
            # 保存图像
            image.save(output_path, format=config['format'])
            
            model_logger.debug(f"PA图像已保存: {output_path}")
            return output_path
            
        except Exception as e:
            raise ResourceError(
                message=f"PA图像生成失败: {str(e)}",
                resource_type="pa_image",
                resource_id=str(output_path)
            )
    
    def _generate_dtoa_image(self, cluster_data: np.ndarray, output_path: Path) -> Path:
        """生成DTOA图像
        
        Args:
            cluster_data: 聚类数据
            output_path: 输出路径
            
        Returns:
            Path: 生成的图像路径
        """
        try:
            # 计算DTOA数据（基于TOA差值）
            if cluster_data.shape[1] <= 4:
                raise ValueError("数据维度不足，无法计算DTOA数据")
            
            toa_data = cluster_data[:, 4]  # TOA列
            
            # 计算一阶差分作为DTOA
            if len(toa_data) > 1:
                dtoa_data = np.diff(toa_data)
            else:
                dtoa_data = np.array([0.0])
            
            # 生成DTOA图像
            config = self.image_configs['DTOA']
            image = self._create_signal_image(dtoa_data, config['size'])
            
            # 保存图像
            image.save(output_path, format=config['format'])
            
            model_logger.debug(f"DTOA图像已保存: {output_path}")
            return output_path
            
        except Exception as e:
            raise ResourceError(
                message=f"DTOA图像生成失败: {str(e)}",
                resource_type="dtoa_image",
                resource_id=str(output_path)
            )
    
    def _create_signal_image(self, signal_data: np.ndarray, size: Tuple[int, int]) -> Image.Image:
        """创建信号图像
        
        Args:
            signal_data: 信号数据
            size: 图像尺寸 (width, height)
            
        Returns:
            Image.Image: 生成的PIL图像
        """
        width, height = size
        
        # 创建空白图像
        image_array = np.zeros((height, width, 3), dtype=np.uint8)
        
        if len(signal_data) == 0:
            # 如果没有数据，返回黑色图像
            return Image.fromarray(image_array)
        
        # 数据归一化
        if np.max(signal_data) != np.min(signal_data):
            normalized_data = (signal_data - np.min(signal_data)) / (np.max(signal_data) - np.min(signal_data))
        else:
            normalized_data = np.ones_like(signal_data) * 0.5
        
        # 将数据映射到图像坐标
        x_coords = np.linspace(0, width - 1, len(normalized_data)).astype(int)
        y_coords = ((1 - normalized_data) * (height - 1)).astype(int)
        
        # 在图像上绘制点
        for x, y in zip(x_coords, y_coords):
            if 0 <= x < width and 0 <= y < height:
                image_array[y, x] = [255, 255, 255]  # 白色点
        
        return Image.fromarray(image_array)
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """清理临时文件
        
        Args:
            max_age_hours: 文件最大保留时间（小时）
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            for file_path in self.temp_dir.glob("*.png"):
                if current_time - file_path.stat().st_mtime > max_age_seconds:
                    file_path.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                model_logger.info(f"清理了 {cleaned_count} 个临时图像文件")
                
        except Exception as e:
            model_logger.warning(f"清理临时文件时出错: {str(e)}")
    
    def get_config(self) -> dict:
        """获取当前配置
        
        Returns:
            dict: 包含当前配置的字典
        """
        return {
            'output_dir': str(self.output_dir),
            'temp_dir': str(self.temp_dir),
            'image_configs': self.image_configs
        }
