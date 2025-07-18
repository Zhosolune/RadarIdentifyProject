"""异步执行器模块

提供简化的异步执行功能，替代复杂的线程池实现。
专为单任务、低频使用的桌面应用设计，符合YAGNI原则。
"""

import threading
from typing import Callable, Any, Optional, Tuple
from PyQt5.QtCore import QObject, QMetaObject, Qt, Q_ARG

from radar_system.infrastructure.common.logging import system_logger


class AsyncExecutor:
    """简化的异步执行器
    
    替代线程池，提供基本的异步执行功能。
    使用普通线程按需创建，适合低频异步任务。
    
    特点：
    - 简单直接：直接使用threading.Thread
    - 按需创建：不占用常驻内存资源
    - 线程安全：支持安全的UI回调机制
    - 符合YAGNI：只实现实际需要的功能
    """
    
    @staticmethod
    def execute_async(
        func: Callable,
        callback_obj: QObject,
        callback_method: str,
        *args,
        **kwargs
    ) -> threading.Thread:
        """异步执行函数并回调结果
        
        创建新线程执行指定函数，完成后通过Qt的线程安全机制回调结果。
        适用于需要避免阻塞UI的耗时操作。
        
        Args:
            func: 要异步执行的函数
            callback_obj: 回调对象（通常是Handler实例）
            callback_method: 回调方法名（字符串）
            *args: 传递给func的位置参数
            **kwargs: 传递给func的关键字参数
            
        Returns:
            threading.Thread: 执行任务的线程对象
            
        Example:
            AsyncExecutor.execute_async(
                service.load_signal_file,
                self,
                "_handle_import_result",
                file_path
            )
        """
        def task():
            """线程任务函数"""
            try:
                system_logger.debug(f"开始异步执行: {func.__name__}")
                
                # 执行目标函数
                result = func(*args, **kwargs)
                
                system_logger.debug(f"异步执行完成: {func.__name__}")
                
                # 线程安全地调用回调方法
                AsyncExecutor._safe_callback(callback_obj, callback_method, result)
                
            except Exception as e:
                error_msg = f"异步执行失败 {func.__name__}: {str(e)}"
                system_logger.error(error_msg)
                
                # 错误情况下的回调，使用标准的(success, message, data)格式
                error_result = (False, error_msg, None)
                AsyncExecutor._safe_callback(callback_obj, callback_method, error_result)
        
        # 创建并启动线程
        thread = threading.Thread(
            target=task,
            name=f"AsyncTask-{func.__name__}",
            daemon=True  # 守护线程，主程序退出时自动结束
        )
        thread.start()
        
        system_logger.info(f"异步任务已启动: {func.__name__} (线程: {thread.name})")
        return thread
    
    @staticmethod
    def _safe_callback(callback_obj: QObject, callback_method: str, result: Any) -> None:
        """线程安全的回调执行
        
        使用Qt的QMetaObject.invokeMethod确保回调在主线程中执行，
        避免跨线程访问UI组件的问题。
        
        Args:
            callback_obj: 回调对象
            callback_method: 回调方法名
            result: 要传递给回调方法的结果
        """
        try:
            # 使用Qt的线程安全机制调用回调
            success = QMetaObject.invokeMethod(
                callback_obj,
                callback_method,
                Qt.QueuedConnection,
                Q_ARG(object, result)
            )
            
            if not success:
                system_logger.error(f"回调调用失败: {callback_obj.__class__.__name__}.{callback_method}")
                
        except Exception as e:
            system_logger.error(f"回调执行异常: {str(e)}")


class FutureWrapper:
    """Future包装器
    
    为了保持与现有Handler回调机制的兼容性，
    提供类似concurrent.futures.Future的接口。
    """
    
    def __init__(self, result: Any):
        """初始化Future包装器
        
        Args:
            result: 要包装的结果
        """
        self._result = result
    
    def result(self) -> Any:
        """获取结果
        
        Returns:
            包装的结果对象
        """
        return self._result


# 为了向后兼容，提供一个简化的异步执行辅助函数
def execute_async_with_future_callback(
    func: Callable,
    callback: Callable[[FutureWrapper], None],
    *args,
    **kwargs
) -> threading.Thread:
    """使用Future风格回调的异步执行
    
    为了保持与现有代码的兼容性，提供Future风格的回调接口。
    
    Args:
        func: 要执行的函数
        callback: 回调函数，接收FutureWrapper参数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        threading.Thread: 执行线程
    """
    def task():
        try:
            result = func(*args, **kwargs)
            future_wrapper = FutureWrapper(result)
            callback(future_wrapper)
        except Exception as e:
            error_result = (False, str(e), None)
            future_wrapper = FutureWrapper(error_result)
            callback(future_wrapper)
    
    thread = threading.Thread(target=task, daemon=True)
    thread.start()
    return thread
