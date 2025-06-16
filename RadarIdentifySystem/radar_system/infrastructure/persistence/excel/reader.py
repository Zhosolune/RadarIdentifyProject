"""Excel数据读取器

负责从Excel文件中读取雷达信号数据，并进行数据预处理。

Notes:
    数据格式要求：
    - CF (列1): 载频，单位MHz
    - PW (列2): 脉宽，单位us
    - DOA (列4): 到达角，单位度
    - PA (列5): 脉冲幅度，单位dB
    - TOA (列7): 到达时间，单位0.1us，将转换为ms
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Iterator
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from radar_system.infrastructure.common.logging import persistence_logger
from radar_system.infrastructure.common.config import ConfigManager
import os
import time

def process_chunk_info(chunk_info: dict) -> Tuple[np.ndarray, int]:
    """处理数据块信息
    
    Args:
        chunk_info: 数据块信息字典，包含文件路径、sheet名称、跳过行数等信息
        
    Returns:
        Tuple[np.ndarray, int]: 处理后的数据数组和进程ID
    """
    try:
        process_id = os.getpid()
        start_time = time.time()
        
        # 读取数据块
        chunk = pd.read_excel(
            chunk_info['file_path'],
            sheet_name=chunk_info['sheet_name'],
            usecols=chunk_info['usecols'],
            skiprows=chunk_info['skiprows'],
            nrows=chunk_info['nrows'],
            header=None
        )
        chunk.columns = chunk_info['columns']
        
        # 处理数据块
        processed = np.column_stack((
            chunk.iloc[:, 0],              # CF (MHz)
            chunk.iloc[:, 1],              # PW (us)
            chunk.iloc[:, 2],              # DOA (度)
            chunk.iloc[:, 3],              # PA (dB)
            chunk.iloc[:, 4] / 1e4         # TOA (转换为ms)
        ))
        
        end_time = time.time()
        persistence_logger.info(
            f"进程 {process_id} 完成数据块处理, "
            f"跳过行数: {chunk_info['skiprows']}, "
            f"处理行数: {chunk_info['nrows']}, "
            f"耗时: {end_time - start_time:.2f}秒"
        )
        
        return processed, process_id
        
    except Exception as e:
        persistence_logger.error(
            f"数据块处理失败 (skiprows={chunk_info['skiprows']}, "
            f"nrows={chunk_info['nrows']}): {str(e)}"
        )
        return np.array([]), -1

class ExcelReader:
    """Excel文件读取器
    
    负责读取和解析雷达信号Excel数据文件。
    支持大文件的分块读取和并行处理。
    """
    
    def __init__(self):
        """初始化Excel读取器"""
        self.config_manager = ConfigManager.get_instance()
        
    def _process_chunk(self, chunk: pd.DataFrame) -> np.ndarray:
        """处理数据块
        
        Args:
            chunk: 待处理的数据块
            
        Returns:
            np.ndarray: 处理后的数据数组
        """
        try:
            # 记录进程信息
            process_id = os.getpid()
            persistence_logger.info(
                f"进程 {process_id} 开始处理数据块, "
                f"数据块大小: {chunk.shape}"
            )
            
            start_time = time.time()
            
            # 转换为numpy数组并进行单位转换
            processed = np.column_stack((
                chunk.iloc[:, 0],              # CF (MHz)
                chunk.iloc[:, 1],              # PW (us)
                chunk.iloc[:, 2],              # DOA (度)
                chunk.iloc[:, 3],              # PA (dB)
                chunk.iloc[:, 4] / 1e4         # TOA (转换为ms)
            ))
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            persistence_logger.info(
                f"进程 {process_id} 完成数据块处理, "
                f"耗时: {processing_time:.2f}秒, "
                f"处理后数据形状: {processed.shape}"
            )
            
            return processed
            
        except Exception as e:
            persistence_logger.error(f"数据块处理失败: {str(e)}")
            return np.array([])
    
    def _simple_read_radar_data(self, file_path: str) -> Tuple[bool, np.ndarray, str]:
        """使用简单高效的方式读取雷达信号数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Tuple[bool, np.ndarray, str]:
                - bool: 是否读取成功
                - np.ndarray: 原始数据数组，包含 [CF, PW, DOA, PA, TOA]
                - str: 处理信息或错误信息
        """
        try:
            persistence_logger.info(f"开始读取Excel文件: {file_path}")
            start_time = time.time()
            
            # 检查文件是否存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 直接使用pandas读取
            df = pd.read_excel(
                file_path,
                usecols=list(self.config_manager.data_processing.data_columns.values()),
                header=0 if self.config_manager.data_processing.excel_has_header else None
            )
            
            # 处理数据
            processed_data = np.column_stack((
                df.iloc[:, 0],              # CF (MHz)
                df.iloc[:, 1],              # PW (us)
                df.iloc[:, 2],              # DOA (度)
                df.iloc[:, 3],              # PA (dB)
                df.iloc[:, 4] / 1e4         # TOA (转换为ms)
            ))
            
            end_time = time.time()
            persistence_logger.info(
                f"数据读取完成:\n"
                f"- 总耗时: {end_time - start_time:.2f}秒\n"
                f"- 数据形状: {processed_data.shape}"
            )
            
            return True, processed_data, "数据读取成功"
            
        except Exception as e:
            error_msg = f"数据读取失败: {str(e)}"
            persistence_logger.error(error_msg, exc_info=True)
            return False, np.array([]), error_msg
            
    def _parallel_read_radar_data(self, file_path: str) -> Tuple[bool, np.ndarray, str]:
        """使用并行处理方式读取雷达信号数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Tuple[bool, np.ndarray, str]:
                - bool: 是否读取成功
                - np.ndarray: 原始数据数组，包含 [CF, PW, DOA, PA, TOA]
                - str: 处理信息或错误信息
        """
        try:
            persistence_logger.info(f"开始并行读取Excel文件: {file_path}")
            start_total_time = time.time()
            
            # 检查文件是否存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 记录主进程信息
            main_process_id = os.getpid()
            max_processes = self.config_manager.data_processing.get_max_processes()
            persistence_logger.info(
                f"主进程ID: {main_process_id}, "
                f"CPU负载: {self.config_manager.data_processing.cpu_load:.1%}, "
                f"计划使用进程数: {max_processes}"
            )
            
            # 首先获取所有数据块的信息
            chunks_info = []
            excel_file = pd.ExcelFile(file_path)
            sheet_name = excel_file.sheet_names[0]
            
            # 获取总行数
            if excel_file.engine == 'openpyxl':
                total_rows = excel_file.book[sheet_name].max_row
            else:  # xlrd引擎
                total_rows = excel_file.book.sheet_by_index(0).nrows
            
            # 从配置获取参数
            has_header = self.config_manager.data_processing.excel_has_header
            chunk_size = self.config_manager.data_processing.excel_chunk_size
            
            # 如果有表头，调整总行数
            if has_header:
                total_rows -= 1
                initial_skip = 1
            else:
                initial_skip = 0
            
            # 准备分块信息
            for start_row in range(0, total_rows, chunk_size):
                rows_to_read = min(chunk_size, total_rows - start_row)
                actual_skip = initial_skip + start_row
                chunks_info.append({
                    'file_path': file_path,
                    'sheet_name': sheet_name,
                    'skiprows': actual_skip,
                    'nrows': rows_to_read,
                    'usecols': list(self.config_manager.data_processing.data_columns.values()),
                    'columns': list(self.config_manager.data_processing.data_columns.keys())
                })
            
            total_chunks = len(chunks_info)
            persistence_logger.info(f"文件将被分为 {total_chunks} 个数据块处理")
            
            # 使用进程池并行处理
            processed_chunks = []
            active_processes = set()
            
            with ProcessPoolExecutor(max_workers=max_processes) as executor:
                futures = [executor.submit(process_chunk_info, chunk_info) 
                          for chunk_info in chunks_info]
                
                for i, future in enumerate(futures, 1):
                    try:
                        result, process_id = future.result()
                        if result.size > 0:
                            processed_chunks.append(result)
                        # 记录实际工作的进程ID
                        if process_id > 0:
                            active_processes.add(process_id)
                        persistence_logger.info(
                            f"完成第 {i}/{total_chunks} 个数据块的处理, "
                            f"当前进度: {(i/total_chunks*100):.1f}%, "
                            f"处理进程: {process_id}"
                        )
                    except Exception as e:
                        persistence_logger.error(f"处理数据块 {i} 失败: {str(e)}")
            
            # 合并所有处理后的数据块
            if not processed_chunks:
                return False, np.array([]), "没有有效的数据"
                
            merge_start_time = time.time()
            processed_data = np.vstack(processed_chunks)
            merge_end_time = time.time()
            
            end_total_time = time.time()
            total_time = end_total_time - start_total_time
            
            persistence_logger.info(
                f"数据处理完成统计:\n"
                f"- 总耗时: {total_time:.2f}秒\n"
                f"- 数据合并耗时: {merge_end_time - merge_start_time:.2f}秒\n"
                f"- 最终数据形状: {processed_data.shape}\n"
                f"- 使用进程数: {len(active_processes)}\n"
                f"- 进程ID列表: {list(active_processes)}\n"
                f"- CPU负载: {self.config_manager.data_processing.cpu_load:.1%}"
            )
            
            return True, processed_data, "数据读取成功"
            
        except Exception as e:
            error_msg = f"数据读取失败: {str(e)}"
            persistence_logger.error(error_msg, exc_info=True)
            return False, np.array([]), error_msg

    def read_radar_data(self, file_path: str) -> Tuple[bool, np.ndarray, str]:
        """读取雷达信号数据
        
        根据配置选择使用简单读取或并行处理方式处理Excel文件。
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Tuple[bool, np.ndarray, str]:
                - bool: 是否读取成功
                - np.ndarray: 原始数据数组，包含 [CF, PW, DOA, PA, TOA]
                - str: 处理信息或错误信息
        """
        if self.config_manager.data_processing.use_parallel_reading:
            persistence_logger.info("使用并行读取策略")
            return self._parallel_read_radar_data(file_path)
        else:
            persistence_logger.info("使用简单高效的读取策略")
            return self._simple_read_radar_data(file_path)


