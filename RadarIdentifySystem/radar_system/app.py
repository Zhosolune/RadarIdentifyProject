"""应用程序入口模块

本模块负责初始化和启动应用程序，包括设置日志系统、创建主窗口等。
"""
from pathlib import Path
import sys
from PyQt5.QtWidgets import QApplication

from radar_system.interface.views.main_window import MainWindow
from radar_system.infrastructure.common.logging import system_logger
from radar_system.infrastructure.common.config import ConfigManager

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

def main():
    """应用程序入口函数"""
    try:
        # 初始化日志系统
        init_logging()
        system_logger.info('雷达信号识别系统启动')
        
        # 初始化配置
        init_config()
        
        # 创建Qt应用程序
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行事件循环
        sys.exit(app.exec_())
        
    except Exception as e:
        system_logger.error(f"应用程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
