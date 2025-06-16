import logging
import os
from datetime import datetime
from pathlib import Path

class LogManager:
    """日志管理器
    
    使用单例模式实现的日志管理器，确保整个应用使用同一个日志实例。
    日志文件将保存在logs目录下，文件名格式为"debug_YYYYMMDD_HHMMSS.log"。
    
    Attributes:
        log_dir (Path): 日志文件目录
        logger (logging.Logger): logging模块的Logger实例
        
    Notes:
        - 使用单例模式确保只创建一个日志管理器实例
        - 日志级别设置为DEBUG
        - 日志格式：时间 - 级别 - 消息
        - 时间格式：YYYY-MM-DD HH:MM:SS
    """
    _instance = None
    
    def __new__(cls):
        """实现单例模式
        
        Returns:
            LogManager: 日志管理器的唯一实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器
        
        - 创建logs目录
        - 创建以当前时间命名的日志文件
        - 配置日志记录器
        - 设置日志格式和处理器
        
        Notes:
            如果实例已经初始化，则直接返回，避免重复初始化
        """
        if self._initialized:
            return
            
        # 创建logs目录
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志文件名（使用当前时间）
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"debug_{current_time}.log"
        
        # 配置日志记录器
        self.logger = logging.getLogger('RadarSignal')
        self.logger.setLevel(logging.DEBUG)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        
        self._initialized = True
    
    def debug(self, message: str):
        """记录调试信息
        
        Args:
            message (str): 调试信息内容
            
        Notes:
            日志级别：DEBUG
            用于记录详细的调试信息，帮助开发人员追踪程序运行状态
        """
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录一般信息
        
        Args:
            message (str): 一般信息内容
            
        Notes:
            日志级别：INFO
            用于记录程序的正常运行信息，如操作完成、状态更新等
        """
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告信息
        
        Args:
            message (str): 警告信息内容
            
        Notes:
            日志级别：WARNING
            用于记录可能的问题或异常情况，但不影响程序的主要功能
        """
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误信息
        
        Args:
            message (str): 错误信息内容
            
        Notes:
            日志级别：ERROR
            用于记录导致功能无法正常运行的错误
        """
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录严重错误信息
        
        Args:
            message (str): 严重错误信息内容
            
        Notes:
            日志级别：CRITICAL
            用于记录需要立即处理的严重问题，可能导致程序崩溃或数据丢失
        """
        self.logger.critical(message) 