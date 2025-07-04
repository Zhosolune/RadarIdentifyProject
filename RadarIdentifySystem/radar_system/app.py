"""应用程序入口模块

本模块负责初始化和启动应用程序，包括设置日志系统、创建主窗口和DDD架构。
"""
from pathlib import Path
import sys
from PyQt5.QtWidgets import QApplication

from radar_system.interface.views.main_window import MainWindow
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.config import ConfigManager
from radar_system.ddd_initializer import DDDInitializer

def init_logging() -> None:
    """初始化日志系统"""
    system_logger.info('日志系统初始化完成')

def init_config() -> None:
    """初始化配置管理器"""
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        
        # 使用configs目录下的config.json作为默认配置文件
        config_path = project_root / "configs" / "config.json"
        
        # 确保configs目录存在
        config_dir = config_path.parent
        if not config_dir.exists():
            system_logger.info(f"配置目录 {config_dir} 不存在，将创建目录")
            config_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化全局配置管理器
        ConfigManager.initialize(str(config_path))
        system_logger.info('配置初始化完成')
        
    except Exception as e:
        system_logger.error(f'配置初始化失败: {str(e)}')
        raise

def init_ddd_architecture() -> DDDInitializer:
    """初始化DDD架构

    Returns:
        DDD架构初始化器实例
    """
    try:
        system_logger.info('开始初始化DDD架构...')

        # 创建DDD初始化器
        ddd_initializer = DDDInitializer()

        # 初始化所有层次
        ddd_components = ddd_initializer.initialize_all_layers()

        system_logger.info('DDD架构初始化完成')
        system_logger.info(f'已初始化组件: {list(ddd_components.keys())}')

        return ddd_initializer

    except Exception as e:
        system_logger.error(f'DDD架构初始化失败: {str(e)}')
        raise

def main():
    """应用程序入口函数"""
    ddd_initializer = None

    try:
        # 初始化日志系统
        init_logging()
        system_logger.info('雷达信号识别系统启动')

        # 初始化配置
        init_config()

        # 初始化DDD架构
        ddd_initializer = init_ddd_architecture()

        # 创建Qt应用程序
        app = QApplication(sys.argv)

        # 创建主窗口
        window = MainWindow()

        # 获取识别处理器并连接到主窗口
        recognition_handler = ddd_initializer.get_recognition_handler()
        if recognition_handler and hasattr(window, 'set_recognition_handler'):
            window.set_recognition_handler(recognition_handler)
            system_logger.info('识别处理器已连接到主窗口')

        window.show()

        # 运行事件循环
        exit_code = app.exec_()

        # 清理资源
        if ddd_initializer:
            ddd_initializer.shutdown()

        sys.exit(exit_code)

    except Exception as e:
        system_logger.error(f"应用程序启动失败: {str(e)}")

        # 清理资源
        if ddd_initializer:
            try:
                ddd_initializer.shutdown()
            except Exception as cleanup_error:
                system_logger.error(f"清理资源时发生错误: {str(cleanup_error)}")

        sys.exit(1)

if __name__ == "__main__":
    main()
