import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from pathlib import Path
from radar_system.infrastructure.common.logging import persistence_logger

class ExcelWriter:
    """Excel文件写入器
    
    负责将雷达信号数据保存为Excel文件。
    """
    
    def save_radar_data(self, data: np.ndarray, file_path: str, 
                       metadata: Dict[str, Any] = None) -> Tuple[bool, str]:
        """保存雷达信号数据到Excel文件
        
        Args:
            data (np.ndarray): 待保存的数据数组，包含 [CF, PW, DOA, PA, TOA]
            file_path (str): 保存文件路径
            metadata (Dict[str, Any], optional): 元数据信息，默认为None
            
        Returns:
            Tuple[bool, str]:
                - bool: 是否保存成功
                - str: 处理信息或错误信息
        """
        try:
            persistence_logger.info(f"开始保存数据到Excel文件: {file_path}")
            persistence_logger.debug(f"数据形状: {data.shape}, 是否包含元数据: {metadata is not None}")
            
            # 创建DataFrame
            df = pd.DataFrame(data, columns=['CF(MHz)', 'PW(us)', 'DOA(度)', 'PA(dB)', 'TOA(ms)'])
            
            # 添加元数据
            if metadata:
                persistence_logger.debug(f"元数据内容: {metadata}")
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='雷达数据', index=False)
                    
                    # 创建元数据sheet
                    meta_df = pd.DataFrame(list(metadata.items()), 
                                         columns=['参数', '值'])
                    meta_df.to_excel(writer, sheet_name='元数据', index=False)
            else:
                df.to_excel(file_path, index=False)
            
            persistence_logger.info(f"数据保存成功，共保存{len(data)}条记录")
            return True, "数据保存成功"
            
        except Exception as e:
            error_msg = f"数据保存失败: {str(e)}"
            persistence_logger.error(error_msg, exc_info=True)
            return False, error_msg
            
    def append_radar_data(self, data: np.ndarray, file_path: str) -> Tuple[bool, str]:
        """追加雷达信号数据到现有Excel文件
        
        Args:
            data (np.ndarray): 待追加的数据数组
            file_path (str): Excel文件路径
            
        Returns:
            Tuple[bool, str]:
                - bool: 是否追加成功
                - str: 处理信息或错误信息
        """
        try:
            persistence_logger.info(f"开始追加数据到Excel文件: {file_path}")
            persistence_logger.debug(f"待追加数据形状: {data.shape}")
            
            # 检查文件是否存在
            if not Path(file_path).exists():
                persistence_logger.info(f"目标文件不存在，将创建新文件: {file_path}")
                return self.save_radar_data(data, file_path)
            
            # 读取现有数据
            existing_df = pd.read_excel(file_path)
            persistence_logger.debug(f"现有数据形状: {existing_df.shape}")
            
            # 创建新数据DataFrame
            new_df = pd.DataFrame(data, columns=['CF(MHz)', 'PW(us)', 'DOA(度)', 'PA(dB)', 'TOA(ms)'])
            
            # 合并数据
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            persistence_logger.debug(f"合并后数据形状: {combined_df.shape}")
            
            # 保存合并后的数据
            combined_df.to_excel(file_path, index=False)
            
            persistence_logger.info(
                f"数据追加成功：原有数据量 {len(existing_df)}，"
                f"新增数据量 {len(data)}，"
                f"总数据量 {len(combined_df)}"
            )
            return True, "数据追加成功"
            
        except Exception as e:
            error_msg = f"数据追加失败: {str(e)}"
            persistence_logger.error(error_msg, exc_info=True)
            return False, error_msg
