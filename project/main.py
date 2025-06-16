import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.main_window import MainWindow


def main():
    """程序入口函数"""
    # 创建应用实例
    app = QApplication(sys.argv)

    # 设置应用程序图标
    app.setWindowIcon(QIcon('resources/icon.ico'))

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
