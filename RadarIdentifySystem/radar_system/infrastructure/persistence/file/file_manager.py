import os
import shutil
from typing import List, Tuple, Optional
from pathlib import Path
from radar_system.infrastructure.common.logging import system_logger

class FileManager:
    """文件管理器
    
    负责文件系统相关操作，包括文件的创建、删除、移动等。
    
    Attributes:
        base_path (Path): 基础路径
    """
    
    def __init__(self, base_path: str = None):
        """初始化文件管理器
        
        Args:
            base_path (str, optional): 基础路径，默认为当前工作目录
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        system_logger.info(f"文件管理器初始化，基础路径: {self.base_path}")
        
    def ensure_directory(self, directory: str) -> Tuple[bool, str]:
        """确保目录存在，如不存在则创建
        
        Args:
            directory (str): 目录路径
            
        Returns:
            Tuple[bool, str]:
                - bool: 是否成功
                - str: 处理信息或错误信息
        """
        try:
            dir_path = self.base_path / directory
            if dir_path.exists():
                system_logger.debug(f"目录已存在: {dir_path}")
                return True, f"目录已就绪: {dir_path}"
                
            dir_path.mkdir(parents=True, exist_ok=True)
            system_logger.info(f"创建目录成功: {dir_path}")
            return True, f"目录已就绪: {dir_path}"
        except Exception as e:
            error_msg = f"目录创建失败: {str(e)}"
            system_logger.error(error_msg, exc_info=True)
            return False, error_msg
            
    def list_files(self, directory: str = ".", pattern: str = "*") -> List[str]:
        """列出指定目录下的文件
        
        Args:
            directory (str): 目录路径，默认为当前目录
            pattern (str): 文件匹配模式，默认为所有文件
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            dir_path = self.base_path / directory
            system_logger.debug(f"开始列出目录内容: {dir_path}, 匹配模式: {pattern}")
            
            files = [str(p.relative_to(self.base_path)) 
                    for p in dir_path.glob(pattern) if p.is_file()]
            
            system_logger.debug(f"找到{len(files)}个文件")
            return files
        except Exception as e:
            system_logger.error(f"列出文件失败: {str(e)}", exc_info=True)
            return []
            
    def move_file(self, source: str, destination: str) -> Tuple[bool, str]:
        """移动文件
        
        Args:
            source (str): 源文件路径
            destination (str): 目标路径
            
        Returns:
            Tuple[bool, str]:
                - bool: 是否成功
                - str: 处理信息或错误信息
        """
        try:
            src_path = self.base_path / source
            dst_path = self.base_path / destination
            
            system_logger.info(f"开始移动文件: {src_path} -> {dst_path}")
            
            # 确保目标目录存在
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            system_logger.info(f"文件移动成功: {source} -> {destination}")
            return True, f"文件已移动: {source} -> {destination}"
        except Exception as e:
            error_msg = f"文件移动失败: {str(e)}"
            system_logger.error(error_msg, exc_info=True)
            return False, error_msg
            
    def copy_file(self, source: str, destination: str) -> Tuple[bool, str]:
        """复制文件
        
        Args:
            source (str): 源文件路径
            destination (str): 目标路径
            
        Returns:
            Tuple[bool, str]:
                - bool: 是否成功
                - str: 处理信息或错误信息
        """
        try:
            src_path = self.base_path / source
            dst_path = self.base_path / destination
            
            system_logger.info(f"开始复制文件: {src_path} -> {dst_path}")
            
            # 确保目标目录存在
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(str(src_path), str(dst_path))
            system_logger.info(f"文件复制成功: {source} -> {destination}")
            return True, f"文件已复制: {source} -> {destination}"
        except Exception as e:
            error_msg = f"文件复制失败: {str(e)}"
            system_logger.error(error_msg, exc_info=True)
            return False, error_msg
            
    def delete_file(self, file_path: str) -> Tuple[bool, str]:
        """删除文件
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Tuple[bool, str]:
                - bool: 是否成功
                - str: 处理信息或错误信息
        """
        try:
            path = self.base_path / file_path
            system_logger.info(f"开始删除文件: {path}")
            
            if not path.exists():
                msg = f"文件不存在: {file_path}"
                system_logger.warning(msg)
                return False, msg
                
            path.unlink()
            system_logger.info(f"文件删除成功: {file_path}")
            return True, f"文件已删除: {file_path}"
        except Exception as e:
            error_msg = f"文件删除失败: {str(e)}"
            system_logger.error(error_msg, exc_info=True)
            return False, error_msg
            
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """获取文件信息
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Optional[dict]: 文件信息字典，包含大小、修改时间等，如果文件不存在则返回None
        """
        try:
            path = self.base_path / file_path
            system_logger.debug(f"获取文件信息: {path}")
            
            if not path.exists():
                system_logger.warning(f"文件不存在: {file_path}")
                return None
                
            stats = path.stat()
            info = {
                'size': stats.st_size,
                'created_time': stats.st_ctime,
                'modified_time': stats.st_mtime,
                'is_file': path.is_file(),
                'extension': path.suffix
            }
            
            system_logger.debug(f"文件信息获取成功: {info}")
            return info
        except Exception as e:
            system_logger.error(f"获取文件信息失败: {str(e)}", exc_info=True)
            return None
