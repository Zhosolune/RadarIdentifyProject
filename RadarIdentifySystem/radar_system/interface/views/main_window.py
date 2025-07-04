"""主窗口模块

本模块实现了应用程序的主窗口，负责创建和管理用户界面。
"""
from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, 
    QMessageBox, QLineEdit, QTableWidgetItem, 
    QPushButton, QCheckBox, QApplication
)
from PyQt5.QtCore import Qt, QSettings, QThread, QTimer, QMetaObject
from pathlib import Path

from radar_system.interface.styles.style_sheets import StyleSheets
from radar_system.interface.layouts.main_layout import setup_main_layout
from radar_system.interface.views.components.loading_spinner import LoadingSpinner
from radar_system.interface.handlers.signal_import_handler import SignalImportHandler
from radar_system.interface.handlers.signal_slice_handler import SignalSliceHandler
from radar_system.infrastructure.common.logging import ui_logger
from radar_system.infrastructure.common.exceptions import UIError

from radar_system.domain.signal.services.validator import SignalValidator
from radar_system.infrastructure.persistence.excel.reader import ExcelReader
from radar_system.application.services.signal_service import SignalService
from radar_system.infrastructure.async_core.pool import ThreadPool
from radar_system.infrastructure.common.config import ConfigManager
from radar_system.domain.signal.entities.signal import SignalSlice
from radar_system.domain.signal.services.processor import SignalProcessor
from radar_system.domain.signal.services.plotter import SignalPlotter
from radar_system.domain.signal.repositories.signal_repository import SignalRepository
from radar_system.infrastructure.persistence.file.file_storage import FileStorage
from radar_system.domain.recognition.entities.recognition_params import RecognitionParams

class MainWindow(QMainWindow):
    """主窗口类
    
    负责创建和管理主要的用户界面，处理用户交互。遵循界面与业务逻辑分离的原则，
    通过事件机制与应用层通信。
    
    Attributes:
        styles (Dict): UI样式字典
        dimensions (Dict): UI尺寸字典
        loading_spinner (LoadingSpinner): 加载动画实例
    """
    
    def __init__(self):
        """初始化主窗口类"""
        super().__init__()
        
        ui_logger.info("正在初始化主窗口...")
        
        try:
            # 获取配置管理器实例
            self.config_manager = ConfigManager.get_instance()
            
            # 初始化样式和尺寸
            self.styles = StyleSheets.get_styles()
            self.dimensions = StyleSheets.get_dimensions()
            

            # 初始化线程池
            self.thread_pool = ThreadPool(
                max_workers=4,  # 可以根据需要调整
                min_workers=2,
                idle_timeout=60  # 空闲线程的超时时间（秒）
            )
            
            # 初始化Infrastructure层组件
            self.signal_validator = SignalValidator()
            self.excel_reader = ExcelReader()
            self.signal_processor = SignalProcessor()
            self.signal_plotter = SignalPlotter()
            self.signal_repository = SignalRepository()
            self.file_storage = FileStorage()

            # 依赖注入：将Infrastructure组件注入到Application层
            # 符合DDD架构，UI层通过Application层访问Infrastructure层
            self.signal_service = SignalService(
                processor=self.signal_processor,
                excel_reader=self.excel_reader,
                plotter=self.signal_plotter,
                file_storage=self.file_storage
            )
            
            # 初始化事件处理器，注入SignalService符合DDD分层架构
            self.signal_import_handler = SignalImportHandler()
            self.slice_handler = SignalSliceHandler(self.signal_service)

            # 识别处理器将在app.py中通过set_recognition_handler方法设置
            self.recognition_handler = None
            
            # 设置窗口基本属性
            self._setup_window()
            
            # 设置UI布局
            self._setup_ui()
            
            # 创建加载动画
            self._setup_loading_spinner()
            
            # 设置信号连接
            self._setup_signals()
            
            ui_logger.info("主窗口初始化成功")
            
        except Exception as e:
            error_msg = "主窗口初始化失败"
            ui_logger.error(f"{error_msg}: {str(e)}")
            raise UIError(
                message=error_msg,
                code="INIT_FAILED",
                details={
                    "component": "MainWindow",
                    "action": "initialization",
                    "error": str(e)
                }
            ) from e
    
    def _setup_window(self) -> None:
        """设置窗口基本属性"""
        try:
            self.setWindowTitle("雷达信号识别系统")
            
            # 获取显示器分辨率
            screen = QApplication.primaryScreen().geometry()
            
            # 获取默认窗口大小
            default_width = self.dimensions.get("window_width", 1200)
            default_height = self.dimensions.get("window_height", 800)
            
            # 根据配置决定是否使用保存的窗口位置和大小
            if self.config_manager.ui.remember_window_position:
                window_width = self.config_manager.ui.window_width or default_width
                window_height = self.config_manager.ui.window_height or default_height
                window_x = self.config_manager.ui.window_x
                window_y = self.config_manager.ui.window_y
            else:
                window_width = default_width
                window_height = default_height
                window_x = None
                window_y = None
            
            # 计算默认的中心位置
            default_x = (screen.width() - window_width) // 2
            default_y = (screen.height() - window_height) // 2
            
            # 如果是首次启动（配置中没有位置信息）或位置在屏幕外，则使用中心位置
            if window_x is None or window_y is None or \
               window_x < 0 or window_x > screen.width() - window_width or \
               window_y < 0 or window_y > screen.height() - window_height:
                window_x = default_x
                window_y = default_y
            
            # 设置窗口位置和大小
            self.setGeometry(window_x, window_y, window_width, window_height)
            self.setStyleSheet(self.styles.get("main_window", ""))
            
            ui_logger.debug(f"窗口位置已设置: x={window_x}, y={window_y}, width={window_width}, height={window_height}")
            
        except Exception as e:
            raise UIError(
                message="窗口属性设置失败",
                code="WINDOW_SETUP_FAILED",
                details={
                    "component": "MainWindow",
                    "action": "setup_window",
                    "error": str(e)
                }
            ) from e
    
    def _setup_ui(self) -> None:
        """设置UI布局"""
        try:
            # 创建并设置中央窗口部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # 使用布局管理器设置布局
            setup_main_layout(self)
            
            # 设置初始状态
            self._update_buttons_state(False)
        except Exception as e:
            raise UIError(
                message="UI布局设置失败",
                code="UI_SETUP_FAILED",
                details={
                    "component": "MainWindow",
                    "action": "setup_ui",
                    "error": str(e)
                }
            ) from e
    
    def _setup_loading_spinner(self) -> None:
        """设置加载动画"""
        try:
            # 使用中央部件作为父窗口
            self.loading_spinner = LoadingSpinner(self.centralWidget())
            # 设置加载动画的初始大小和位置
            self.loading_spinner.resize(self.centralWidget().size())
            self.loading_spinner.move(0, 0)
            self.loading_spinner.hide()
        except Exception as e:
            raise UIError(
                message="加载动画设置失败",
                code="SPINNER_SETUP_FAILED",
                details={
                    "component": "MainWindow",
                    "action": "setup_loading_spinner",
                    "error": str(e)
                }
            ) from e
    
    def _update_buttons_state(self, enable: bool = True) -> None:
        """更新按钮状态
        
        批量设置所有操作按钮的状态（启用/禁用）。
        包括：开始切片、识别、下一片、下一类、重置当前切片等按钮。
        
        Args:
            enable: 是否启用按钮，True表示启用，False表示禁用
        """
        try:
            # 定义需要更新状态的按钮列表
            operation_buttons = [
                'start_slice_btn',    # 开始切片按钮
                'identify_btn',       # 识别按钮
                'next_slice_btn',     # 下一片按钮
                'next_cluster_btn',   # 下一类按钮
                'reset_slice_btn'     # 重置当前切片按钮
            ]
            
            # 批量更新按钮状态
            for btn_name in operation_buttons:
                if hasattr(self, btn_name):
                    button = getattr(self, btn_name)
                    button.setEnabled(enable)
            
            ui_logger.debug(f"批量{'启用' if enable else '禁用'}操作按钮")
            
        except Exception as e:
            ui_logger.error(f"更新按钮状态失败: {str(e)}")
            raise UIError(
                message="按钮状态更新失败",
                code="BUTTON_STATE_UPDATE_FAILED",
                details={
                    "component": "MainWindow",
                    "action": "update_buttons_state",
                    "error": str(e)
                }
            ) from e
    
    def mousePressEvent(self, event):
        """处理鼠标点击事件
        
        当点击非输入框区域时，清除当前输入框的焦点。
        
        Args:
            event: 鼠标事件对象
        """
        # 获取当前焦点控件
        focused_widget = QApplication.focusWidget()
        # 如果有控件被选中且是输入框
        if isinstance(focused_widget, QLineEdit):
            # 清除焦点
            focused_widget.clearFocus()
        # 调用父类的鼠标点击事件
        super().mousePressEvent(event) 

    def resizeEvent(self, event) -> None:
        """窗口大小改变事件处理
        
        Args:
            event: 窗口大小改变事件
        """
        try:
            super().resizeEvent(event)
            # 更新加载动画大小和位置
            if hasattr(self, 'loading_spinner') and self.loading_spinner.isVisible():
                self.loading_spinner.resize(self.centralWidget().size())
                self.loading_spinner.move(0, 0)
            # 根据配置决定是否保存窗口大小
            if self.config_manager.ui.remember_window_position:
                size = self.size()
                self.config_manager.ui.window_width = size.width()
                self.config_manager.ui.window_height = size.height()
        except Exception as e:
            ui_logger.error(f"窗口大小调整失败: {str(e)}")
    
    def closeEvent(self, event) -> None:
        """窗口关闭事件处理
        
        Args:
            event: 窗口关闭事件
        """
        try:
            reply = QMessageBox.question(
                self, '确认退出', 
                "确定要退出程序吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                ui_logger.info("用户确认退出程序")
                # 保存配置
                self.config_manager.save_config()
                # 清理资源
                self.cleanup_resources()
                event.accept()
            else:
                ui_logger.debug("用户取消退出")
                event.ignore()
        except Exception as e:
            ui_logger.error(f"窗口关闭处理失败: {str(e)}")
            event.accept()
    
    def cleanup_resources(self) -> None:
        """清理资源"""
        try:
            ui_logger.info("正在清理资源...")
            # 关闭线程池
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown()
        except Exception as e:
            ui_logger.error(f"资源清理失败: {str(e)}")
    
    def _setup_signals(self) -> None:
        """设置所有信号连接
        
        包括：
        1. 按钮点击信号
        2. 导入处理器信号
        3. 其他UI组件信号
        """
        try:
            # 导入相关按钮信号
            self.browse_btn.clicked.connect(self._on_browse_import)
            self.import_btn.clicked.connect(self._on_import_data)
            
            # 导入处理器信号 - 使用统一的信号命名
            self.signal_import_handler.import_started.connect(self._on_import_started)
            self.signal_import_handler.import_completed.connect(self._on_import_completed)
            self.signal_import_handler.import_failed.connect(self._on_import_error)
            self.signal_import_handler.file_selected.connect(self._on_file_selected)
            
            # 切片按钮信号
            self.start_slice_btn.clicked.connect(self._on_start_slice)
            self.next_slice_btn.clicked.connect(self._on_next_slice)

            # 识别按钮信号
            self.identify_btn.clicked.connect(self._on_identify)

            # 切片相关信号
            self.slice_handler.slice_started.connect(self._on_slice_started)
            self.slice_handler.slice_completed.connect(self._on_slice_completed)
            self.slice_handler.slice_failed.connect(self._on_slice_error)
            self.slice_handler.slice_display_ready.connect(self._on_slice_display_ready)
            
            ui_logger.debug("信号连接设置完成")
            
        except Exception as e:
            ui_logger.error(f"设置信号连接时出错: {str(e)}")
            raise UIError(
                message="信号连接设置失败",
                code="SIGNAL_SETUP_FAILED",
                details={
                    "component": "MainWindow",
                    "action": "signal_setup",
                    "error": str(e)
                }
            ) from e
    
    def _on_browse_import(self) -> None:
        """浏览文件按钮点击事件处理"""
        self.signal_import_handler.browse_file(self)
        
    def _on_import_data(self) -> None:
        """导入数据按钮点击事件处理"""
        # 从import_path控件获取文件路径
        file_path = self.import_path.text().strip()

        if not file_path:
            QMessageBox.warning(self, "警告", "请先选择要导入的文件")
            return

        # 调用导入处理器
        self.signal_import_handler.import_data(self, file_path)
        
    def _on_file_selected(self, file_path: str) -> None:
        """文件选择完成的槽函数
        
        Args:
            file_path: 选择的文件路径
        """
        self.import_path.setText(file_path)
        self.import_btn.setEnabled(bool(file_path))
        
    def _start_loading_animation(self) -> None:
        """启动加载动画
        
        显示加载动画并禁用相关按钮。
        """
        try:
            # 显示加载动画
            if hasattr(self, 'loading_spinner'):
                self.loading_spinner.resize(self.centralWidget().size())
                self.loading_spinner.move(0, 0)
                self.loading_spinner.raise_()
                self.loading_spinner.start()
            
            # 禁用按钮
            self.browse_btn.setEnabled(False)
            self.import_btn.setEnabled(False)
            
            # 强制更新界面
            QApplication.processEvents()
            
            ui_logger.debug("加载动画已启动")
            
        except Exception as e:
            ui_logger.error(f"启动加载动画失败: {str(e)}")
            
    def _stop_loading_animation(self) -> None:
        """停止加载动画
        
        隐藏加载动画并启用相关按钮。
        """
        try:
            # 停止并隐藏加载动画
            if hasattr(self, 'loading_spinner'):
                self.loading_spinner.stop()
            
            # 启用浏览按钮
            self.browse_btn.setEnabled(True)
            # 根据是否有文件路径决定导入按钮状态
            self.import_btn.setEnabled(bool(self.import_path.text()))
            
            ui_logger.debug("加载动画已停止")
            
        except Exception as e:
            ui_logger.error(f"停止加载动画失败: {str(e)}")
            
    def _on_import_started(self) -> None:
        """导入开始的槽函数"""
        self._clear_all_displays()
        self._start_loading_animation()
        
    def _on_import_completed(self, success: bool) -> None:
        """导入完成的槽函数
        
        处理导入完成后的所有UI更新操作，包括：
        1. 停止加载动画
        2. 更新按钮状态
        3. 更新波段和切片信息显示
        4. 显示结果对话框
        
        Args:
            success: 是否成功
        """
        try:
            # 确保在主线程中执行UI操作
            def update_ui():
                try:
                    # 停止加载动画
                    self._stop_loading_animation()
                    
                    # 更新按钮状态和数据显示
                    if success:
                        # 导入成功时，只启用开始切片按钮，其他操作按钮保持禁用
                        self._update_buttons_state(False)  # 先全部禁用
                        self.start_slice_btn.setEnabled(True)  # 仅启用开始切片按钮
                        
                        # 更新波段和切片信息显示
                        if hasattr(self, 'slice_info_label1') and hasattr(self, 'slice_info_label2'):
                            signal = self.signal_service.current_signal
                            self.slice_info_label1.setText(f"数据包位于{signal.band_type}，")
                            self.slice_info_label2.setText(f"预计将获得{signal.expected_slices}个250ms切片")
                            
                        ui_logger.debug("数据导入完成，已更新按钮状态和切片数量显示")
                    else:
                        # 导入失败，禁用所有按钮
                        self._update_buttons_state(False)
                        
                        # 更新切片数量显示为未知状态
                        if hasattr(self, 'slice_info_label1') and hasattr(self, 'slice_info_label2'):
                            self.slice_info_label1.setText("数据包位于?波段，")
                            self.slice_info_label2.setText("预计将获得?个250ms切片")
                            
                        ui_logger.debug("数据导入失败，已禁用所有按钮")
                    
                    # 使用延迟显示对话框，确保动画已经完全停止
                    QTimer.singleShot(100, lambda: self._show_import_result(success))
                    
                except Exception as e:
                    ui_logger.error(f"更新UI失败: {str(e)}")
            
            # 如果当前不在主线程，则通过事件循环调用
            if QThread.currentThread() is not QApplication.instance().thread():
                QMetaObject.invokeMethod(self, update_ui, Qt.QueuedConnection)
            else:
                update_ui()
                
        except Exception as e:
            ui_logger.error(f"导入完成处理失败: {str(e)}")
        
    def _on_import_error(self, error_msg: str) -> None:
        """导入错误的槽函数
        
        Args:
            error_msg: 错误信息
        """
        try:
            ui_logger.error(f"导入错误: {error_msg}")
            self._stop_loading_animation()
            QTimer.singleShot(100, lambda: self._show_import_result(False))
        except Exception as e:
            ui_logger.error(f"导入错误处理失败: {str(e)}")
            
    def _clear_all_displays(self) -> None:
        """清空所有显示内容"""
        try:
            # 清空左侧图像
            if hasattr(self, 'left_plots'):
                for plot in self.left_plots:
                    plot.clear()
                self.left_title.setText("第0个切片数据 原始图像")
                    
            # 清空中间图像
            if hasattr(self, 'middle_plots'):
                for plot in self.middle_plots:
                    plot.clear()
                self.middle_title.setText("CF/PW维度聚类 第0类")
                    
            # 清空表格数据
            if hasattr(self, 'table'):
                for row in range(self.table.rowCount()):
                    item = QTableWidgetItem(' ')
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 1, item)
                    
            # 禁用所有操作按钮
            self._update_buttons_state(False)
            
            ui_logger.debug("已清空所有显示内容")
            
        except Exception as e:
            ui_logger.error(f"清空显示内容时出错: {str(e)}")
            
    def _show_import_result(self, success: bool) -> None:
        """显示导入结果对话框"""
        try:
            if success:
                QMessageBox.information(self, "成功", "数据导入成功")
            else:
                QMessageBox.warning(self, "失败", "数据导入失败")
        except Exception as e:
            ui_logger.error(f"显示导入结果对话框失败: {str(e)}")

    def moveEvent(self, event) -> None:
        """窗口移动事件处理
        
        Args:
            event: 窗口移动事件
        """
        try:
            # 根据配置决定是否保存窗口位置
            if self.config_manager.ui.remember_window_position:
                pos = self.pos()
                self.config_manager.ui.window_x = pos.x()
                self.config_manager.ui.window_y = pos.y()
            super().moveEvent(event)
        except Exception as e:
            ui_logger.error(f"保存窗口位置失败: {str(e)}")

    def _on_slice_started(self) -> None:
        """切片开始的槽函数"""
        try:
            self._clear_all_displays()
            self._start_loading_animation()
            self._update_buttons_state(False)
        except Exception as e:
            ui_logger.error(f"处理切片开始事件时出错: {str(e)}")

    def _on_slice_completed(self, success: bool, slice_count: int) -> None:
        """切片完成的槽函数

        Args:
            success: 是否成功
            slice_count: 切片数量
        """
        try:
            self._stop_loading_animation()
            if success:
                # 更新按钮状态
                self.next_slice_btn.setEnabled(True)
                self.identify_btn.setEnabled(True)
                
                # 获取切片信息
                signal = self.signal_service.get_current_signal()
                if signal:
                    # 计算空切片数量
                    empty_slice_count = signal.expected_slices - slice_count

                    # 更新切片信息显示
                    if empty_slice_count > 0:
                        self.slice_info_label2.setText(
                            f"共获得{slice_count}个250ms切片，以及"
                            f"<span style='color: red;'>{empty_slice_count}</span>个空切片"
                        )
                    else:
                        self.slice_info_label2.setText(
                            f"共获得{slice_count}个250ms切片"
                        )
                    
                    # 显示第一个切片
                    current_index, _ = self.signal_service.get_slice_info()
                    if current_index == 0:  # 还没有显示任何切片
                        self.slice_handler.show_next_slice(self)
                        
        except Exception as e:
            ui_logger.error(f"处理切片完成事件时出错: {str(e)}")
            self.slice_info_label2.setText("切片处理出错")

    def _on_slice_error(self, error_msg: str) -> None:
        """切片错误的槽函数
        
        Args:
            error_msg: 错误信息
        """
        try:
            ui_logger.error(f"切片错误: {error_msg}")
            self._stop_loading_animation()
            QTimer.singleShot(100, lambda: self._show_slice_result(False))
        except Exception as e:
            ui_logger.error(f"切片错误处理失败: {str(e)}")

    def _on_start_slice(self) -> None:
        """开始切片按钮点击事件处理"""
        try:
            # 获取当前信号数据
            signal = self.signal_service.get_current_signal()
            if not signal:
                QMessageBox.warning(self, "警告", "请先导入信号数据")
                return

            # 调用切片处理器，符合DDD分层架构：不传递UI层实例
            self.slice_handler.start_slice(
                signal=signal,
                thread_pool=self.thread_pool,
                message_callback=self._show_message_box
            )
            
        except Exception as e:
            ui_logger.error(f"处理开始切片事件时出错: {str(e)}")

    def _on_next_slice(self) -> None:
        """下一个切片按钮点击事件处理

        UI层专注于用户交互，通过Handler层请求下一个切片数据。
        预防性设计：正常情况下按钮应该在最后一个切片时被禁用，
        因此这个方法不应该在没有更多切片时被调用。
        符合DDD分层架构原则。
        """
        try:
            # 预防性检查：按钮应该已经被禁用，这是额外的安全检查
            if self.signal_service.is_last_slice():
                ui_logger.warning("'下一片'按钮在最后一个切片时被点击，这不应该发生")
                self.next_slice_btn.setEnabled(False)
                return

            # 通过Handler层请求下一个切片，符合DDD分层架构
            success = self.slice_handler.request_next_slice()

            # 如果请求失败，记录日志但不显示错误对话框（预防性设计）
            if not success:
                ui_logger.debug("下一个切片请求失败，可能已到达最后一个切片")

        except Exception as e:
            ui_logger.error(f"处理下一个切片事件时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"切片导航出错: {str(e)}")

    def _show_slice_result(self, success: bool) -> None:
        """显示切片结果对话框

        Args:
            success: 是否成功
        """
        try:
            if not success:
                QMessageBox.warning(self, "警告", "切片处理失败")
        except Exception as e:
            ui_logger.error(f"显示切片结果对话框失败: {str(e)}")

    def _on_slice_display_ready(self, slice_data) -> None:
        """切片显示就绪的槽函数

        当Handler层准备好切片数据时，UI层负责更新界面显示。
        实现预防性按钮状态管理：检查是否为最后一个切片并相应设置按钮状态。
        符合DDD分层架构原则：UI层专注界面更新。

        Args:
            slice_data: 切片数据对象
        """
        try:
            # UI层专注于界面更新
            self.update_slice_display(slice_data)

            # 预防性按钮状态管理：检查是否为最后一个切片
            is_last = self.signal_service.is_last_slice()
            self.next_slice_btn.setEnabled(not is_last)

            # 记录按钮状态变化
            current_index, total_count = self.signal_service.get_slice_info()
            if is_last:
                ui_logger.debug(f"已显示最后一个切片 ({current_index}/{total_count})，禁用'下一片'按钮")
            else:
                ui_logger.debug(f"显示切片 ({current_index}/{total_count})，'下一片'按钮保持启用")

        except Exception as e:
            ui_logger.error(f"处理切片显示就绪事件时出错: {str(e)}")

    def _show_message_box(self, title: str, message: str, icon_type) -> None:
        """显示消息框的辅助方法

        用于Handler层回调显示消息，避免Handler层直接依赖UI组件。

        Args:
            title: 消息框标题
            message: 消息内容
            icon_type: 消息框图标类型
        """
        QMessageBox(icon_type, title, message, QMessageBox.Ok, self).exec_()



    def update_slice_display(self, slice_data: SignalSlice) -> None:
        """更新切片显示

        UI层专注于界面更新，业务流程协调由Application层（SignalService）负责。
        符合DDD分层架构和单一职责原则。

        Args:
            slice_data: 切片数据
        """
        try:
            # 通过Application层获取显示数据，遵循DDD分层原则
            display_data = self.signal_service.prepare_slice_display_data(slice_data)

            if not display_data['success']:
                ui_logger.error(f"获取切片显示数据失败: {display_data['error_message']}")
                return

            # UI层只负责界面组件更新
            self._update_left_slice_images(display_data)

            ui_logger.debug(f"切片显示更新完成: {display_data['current_index']}/{display_data['total_count']}")

        except Exception as e:
            ui_logger.error(f"切片显示更新失败: {str(e)}")
            # 不重新抛出异常，避免影响Handler层的流程

    def _update_left_slice_images(self, display_data: Dict[str, any]) -> None:
        """更新左侧切片图像显示区域

        私有方法，专门负责更新左侧切片图像显示区域，包括：
        - 切片标题文本
        - 5张切片图像（CF、PW、PA、DTOA、DOA）

        Args:
            display_data: 显示数据字典，包含标题和图像路径信息
        """
        try:
            # 更新左侧切片图像显示区域
            if hasattr(self, 'left_plots'):
                # 更新切片标题
                self.left_title.setText(display_data['title'])

                # 按顺序显示5张切片图像（CF、PW、PA、DTOA、DOA）
                plot_types = ['CF', 'PW', 'PA', 'DTOA', 'DOA']
                image_paths = display_data['image_paths']

                for i, plot_type in enumerate(plot_types):
                    if i < len(self.left_plots):
                        image_path = image_paths.get(plot_type)
                        if image_path:
                            self.left_plots[i].display_image(image_path)
                        else:
                            self.left_plots[i].clear()

        except Exception as e:
            ui_logger.error(f"更新左侧切片图像显示失败: {str(e)}")
            raise

    def set_recognition_handler(self, recognition_handler):
        """设置识别处理器

        Args:
            recognition_handler: 识别处理器实例
        """
        self.recognition_handler = recognition_handler

        # 连接识别处理器的信号到主窗口的处理函数
        if recognition_handler:
            recognition_handler.recognition_started.connect(self._on_recognition_started)
            recognition_handler.recognition_completed.connect(self._on_recognition_completed)
            recognition_handler.recognition_failed.connect(self._on_recognition_failed)

        ui_logger.info("识别处理器已设置并连接信号")

    def _on_identify(self) -> None:
        """识别按钮点击事件处理"""
        try:
            if self.recognition_handler is None:
                QMessageBox.warning(self, "警告", "识别处理器未初始化")
                return

            # 获取当前信号数据
            current_signal = self.signal_service.get_current_signal()
            if current_signal is None:
                QMessageBox.warning(self, "警告", "请先加载并切片信号数据")
                return

            # 获取当前切片
            current_slice = self.signal_service.get_current_slice()
            if current_slice is None:
                QMessageBox.warning(self, "警告", "请先进行信号切片")
                return

            ui_logger.info(f"开始识别处理 - 信号ID: {current_signal.id}, 切片索引: {current_slice.slice_index}")

            # 创建默认识别参数
            ui_logger.info("正在创建默认识别参数...")
            recognition_params = RecognitionParams.create_default()
            ui_logger.info("识别参数创建完成")

            # 禁用识别按钮，防止重复点击
            self.identify_btn.setEnabled(False)
            self.identify_btn.setText("识别中...")

            # 使用QTimer异步启动识别任务，避免阻塞主线程
            ui_logger.info("正在异步启动识别任务...")
            QTimer.singleShot(100, lambda: self._start_recognition_async(
                current_slice.data,
                recognition_params.to_dict()
            ))

        except Exception as e:
            ui_logger.error(f"识别按钮处理失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"识别处理失败: {str(e)}")
            # 恢复按钮状态
            self.identify_btn.setEnabled(True)
            self.identify_btn.setText("识别")

    def _start_recognition_async(self, signal_data, recognition_params):
        """异步启动识别任务"""
        try:
            ui_logger.info("正在调用识别处理器...")
            task_id = self.recognition_handler.start_recognition(
                signal_data=signal_data,
                recognition_params=recognition_params
            )
            ui_logger.info(f"识别处理器调用完成，返回task_id: {task_id}")

            if task_id:
                ui_logger.info(f"识别任务已启动: {task_id}")
            else:
                ui_logger.warning("启动识别任务失败")
                QMessageBox.warning(self, "警告", "启动识别任务失败")
                # 恢复按钮状态
                self.identify_btn.setEnabled(True)
                self.identify_btn.setText("识别")

        except Exception as e:
            ui_logger.error(f"异步启动识别任务失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"启动识别任务失败: {str(e)}")
            # 恢复按钮状态
            self.identify_btn.setEnabled(True)
            self.identify_btn.setText("识别")

    def _on_recognition_started(self, task_id: str, session_id: str):
        """识别开始事件处理"""
        ui_logger.info(f"识别已开始 - 任务ID: {task_id}, 会话ID: {session_id}")

    def _on_recognition_completed(self, task_id: str, success: bool, results: dict):
        """识别完成事件处理"""
        try:
            # 恢复识别按钮状态
            self.identify_btn.setEnabled(True)
            self.identify_btn.setText("识别")

            if success:
                ui_logger.info(f"识别完成 - 任务ID: {task_id}")
                QMessageBox.information(self, "成功", "信号识别完成！")
                # TODO: 显示识别结果
            else:
                ui_logger.warning(f"识别失败 - 任务ID: {task_id}")
                QMessageBox.warning(self, "警告", "信号识别失败")

        except Exception as e:
            ui_logger.error(f"处理识别完成事件失败: {str(e)}")

    def _on_recognition_failed(self, task_id: str, error_message: str):
        """识别失败事件处理"""
        try:
            # 恢复识别按钮状态
            self.identify_btn.setEnabled(True)
            self.identify_btn.setText("识别")

            ui_logger.error(f"识别失败 - 任务ID: {task_id}, 错误: {error_message}")
            QMessageBox.critical(self, "错误", f"识别失败: {error_message}")

        except Exception as e:
            ui_logger.error(f"处理识别失败事件失败: {str(e)}")
