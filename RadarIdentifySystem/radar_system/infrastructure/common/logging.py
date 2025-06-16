"""
日志管理模块

本模块提供统一的日志记录机制，支持不同级别的日志记录和自定义格式化。
"""
import os
import logging
import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler
from .exceptions import ResourceError


class LogFormatter(logging.Formatter):
    """日志格式化器
    
    自定义的日志格式化器，提供更详细的日志信息。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            str: 格式化后的日志字符串
        """
        # 添加时间戳
        record.created_fmt = datetime.datetime.fromtimestamp(
            record.created
        ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 如果有额外信息，将其格式化
        if hasattr(record, 'extra_data') and record.extra_data:
            record.msg = f"{record.msg} | Extra: {record.extra_data}"
        
        return super().format(record)


class LogManager:
    """日志管理器
    
    负责管理系统的日志记录功能。
    
    Attributes:
        _instance: 单例实例
        _loggers: 日志器字典
        _default_level: 默认日志级别
    """
    
    _instance = None
    
    def __new__(cls) -> 'LogManager':
        """创建或返回单例实例
        
        Returns:
            LogManager: 日志管理器实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """初始化日志管理器"""
        if self._initialized:
            return
            
        self._loggers: Dict[str, logging.Logger] = {}
        self._default_level = logging.INFO
        self._log_dir = "logs"
        self._max_bytes = 10 * 1024 * 1024  # 10MB
        self._backup_count = 5
        
        # 确保日志目录存在
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
            
        self._initialized = True
    
    def get_logger(self, 
                   name: str, 
                   level: Optional[int] = None) -> logging.Logger:
        """获取或创建日志器
        
        Args:
            name: 日志器名称
            level: 日志级别，默认使用默认级别
            
        Returns:
            logging.Logger: 日志器实例
        """
        if name in self._loggers:
            return self._loggers[name]
            
        logger = logging.getLogger(name)
        level = level or self._default_level
        logger.setLevel(level)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = LogFormatter(
            '%(created_fmt)s | %(levelname)-8s | %(name)s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 添加文件处理器
        try:
            file_handler = RotatingFileHandler(
                filename=os.path.join(self._log_dir, f"{name}.log"),
                maxBytes=self._max_bytes,
                backupCount=self._backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_formatter = LogFormatter(
                '%(created_fmt)s | %(levelname)-8s | %(name)s | '
                '%(filename)s:%(lineno)d | %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            raise ResourceError(
                f"创建日志文件失败: {str(e)}",
                resource_type="log_file",
                resource_id=name
            )
        
        self._loggers[name] = logger
        return logger
    
    def set_level(self, name: str, level: int) -> None:
        """设置日志器的级别
        
        Args:
            name: 日志器名称
            level: 新的日志级别
        """
        if name in self._loggers:
            logger = self._loggers[name]
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)
    
    def add_extra_data(self, 
                      logger: logging.Logger, 
                      extra_data: Dict[str, Any]) -> None:
        """添加额外的日志信息
        
        Args:
            logger: 日志器实例
            extra_data: 额外信息字典
        """
        logger = logging.LoggerAdapter(logger, {'extra_data': extra_data})
        return logger


# 创建默认日志器
system_logger = LogManager().get_logger('system')
signal_logger = LogManager().get_logger('signal')
model_logger = LogManager().get_logger('model')
ui_logger = LogManager().get_logger('ui')
persistence_logger = LogManager().get_logger('persistence')
plotter_logger = LogManager().get_logger('plotter')
