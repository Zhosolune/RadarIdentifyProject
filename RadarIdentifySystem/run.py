"""雷达信号识别系统启动脚本

作为程序的统一入口点，负责初始化和启动主应用程序。
"""

import sys
from radar_system.app import main

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        sys.exit(1) 