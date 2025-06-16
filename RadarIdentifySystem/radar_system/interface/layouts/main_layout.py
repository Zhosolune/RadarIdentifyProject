"""主窗口布局模块

本模块负责实现主窗口的整体布局，包括：
1. 三列基本布局结构
2. 各个功能区域的布局管理
3. 组件的布局和排列
"""

from typing import Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSizePolicy, QSpacerItem, QPushButton, QLineEdit,
    QProgressBar, QGroupBox, QRadioButton, QButtonGroup,
    QCheckBox, QTableWidget, QHeaderView, QTableWidgetItem,
    QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

from radar_system.infrastructure.common.logging import ui_logger
from radar_system.interface.views.components.plot_widget import PlotWidget, ScaleMode
from radar_system.interface.views.components.switch_widget import Switch
from radar_system.interface.styles.style_sheets import StyleSheets, Theme


def setup_main_layout(window) -> None:
    """设置主窗口布局
    
    Args:
        window: 主窗口实例
    """
    ui_logger.debug("开始设置主窗口布局")
    
    try:
        # 设置默认主题
        StyleSheets.set_theme(Theme.FOREST)
        # 获取当前主题的样式和配色
        window.styles = StyleSheets.get_styles()
        window.theme_colors = StyleSheets.get_theme_colors()
        window.dimensions = StyleSheets.get_dimensions()
        
        # 应用主窗口样式
        window.setStyleSheet(window.styles['main_window'])
        
        # 创建中央窗口部件
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        
        # 设置主布局的边距：上35px，其他10px
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 35, 10, 10)
        
        # 创建白色背景容器
        container = QWidget()
        container.setStyleSheet(window.styles['container'])
        main_layout.addWidget(container)
        
        # 在白色容器内创建布局，统一设置10px的边距
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)  # 列之间的间距设为10px
        
        # 创建三列
        left_column = _create_left_column(window)  # 图像显示区域1
        middle_column = _create_middle_column(window)  # 图像显示区域2
        right_column = _create_right_column(window)  # 用户交互区域
        
        # 创建列容器并设置布局
        column_widget1 = QWidget()
        column_widget1.setLayout(left_column)
        column_widget1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        column_widget2 = QWidget()
        column_widget2.setLayout(middle_column)
        column_widget2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        column_widget3 = QWidget()
        column_widget3.setLayout(right_column)
        column_widget3.setFixedWidth(500)
        
        # 添加列到容器布局
        container_layout.addWidget(column_widget1, 1)
        container_layout.addWidget(column_widget2, 1)
        container_layout.addWidget(column_widget3)
        
        ui_logger.debug("主窗口布局设置完成")
        
    except Exception as e:
        ui_logger.error(f"设置主窗口布局时出错: {str(e)}")
        raise


def _create_left_column(window) -> QVBoxLayout:
    """创建左侧列布局（图像显示区域1）
    
    Args:
        window: 主窗口实例
    
    Returns:
        QVBoxLayout: 左侧列布局
    """
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    
    try:
        # 创建标题
        window.left_title = QLabel("第0个切片数据  原始图像")
        window.left_title.setAlignment(Qt.AlignCenter)
        window.left_title.setStyleSheet(window.styles['title_label'])
        window.left_title.setFixedHeight(window.dimensions['title_height'])
        layout.addWidget(window.left_title)
        
        # 创建图像容器
        plots_container = QWidget()
        plots_layout = QVBoxLayout(plots_container)
        plots_layout.setSpacing(window.dimensions['spacing_small'])
        plots_layout.setContentsMargins(0, 0, 0, 0)
        
        # 图像标签文字，顺序决定标签和图像显示的顺序
        labels = ["载频", "脉宽", "幅度", "一级差", "方位角"]
        
        window.left_plots = []  # 初始化列表
        
        # 添加5个图像和对应的标签
        for i, label_text in enumerate(labels):
            # 创建水平布局来放置标签和图像
            row_layout = QHBoxLayout()
            row_layout.setSpacing(window.dimensions['spacing_small'])  # 标签和图像之间的间距
            
            # 创建竖排标签（通过在每个字符后添加换行符）
            vertical_text = '\n'.join(label_text)
            label = QLabel(vertical_text)
            label.setStyleSheet(window.styles['figure_label'])
            label.setFixedWidth(25)  # 设置标签宽度
            
            # 创建图像
            plot_widget = PlotWidget(scale_mode=ScaleMode.STRETCH)
            plot_widget.frame.setFrameShape(QFrame.Box)
            plot_widget.frame.setLineWidth(1)
            plot_widget.frame.setStyleSheet(window.styles['plot_frame'])
            if i == 0:  # 第一个图像
                plot_widget.plot_layout.setContentsMargins(0, 0, 0, 5)
            elif i == 4:  # 最后一个图像
                plot_widget.plot_layout.setContentsMargins(0, 5, 0, 0)
            else:  # 中间的图像
                plot_widget.plot_layout.setContentsMargins(0, 5, 0, 5)
            
            # 存储图像显示区域
            window.left_plots.append(plot_widget)
            
            # 添加标签和图像到行布局
            row_layout.addWidget(label)
            row_layout.addWidget(plot_widget, 1)
            
            # 添加行布局到主布局
            plots_layout.addLayout(row_layout)
        
        # 添加图像容器到主布局
        layout.addWidget(plots_container)
        
        ui_logger.debug("左侧图像显示区布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建左侧图像显示区布局时出错: {str(e)}")
        raise
    
    return layout


def _create_middle_column(window) -> QVBoxLayout:
    """创建中间列布局（图像显示区域2）
    
    Args:
        window: 主窗口实例
    
    Returns:
        QVBoxLayout: 中间列布局
    """
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    
    try:
        # 创建标题
        window.middle_title = QLabel("CF/PW 维度聚类 第0类")
        window.middle_title.setAlignment(Qt.AlignCenter)
        window.middle_title.setStyleSheet(window.styles['title_label'])
        window.middle_title.setFixedHeight(window.dimensions['title_height'])
        layout.addWidget(window.middle_title)
        
        # 创建图像容器
        plots_container = QWidget()
        plots_layout = QVBoxLayout(plots_container)
        plots_layout.setSpacing(window.dimensions['spacing_small'])
        plots_layout.setContentsMargins(0, 0, 0, 0)
        
        # 图像标签文字
        labels = ["载频", "脉宽", "幅度", "一级差", "方位角"]
        
        window.middle_plots = []  # 初始化列表
        
        # 添加5个图像和对应的标签
        for i, label_text in enumerate(labels):
            # 创建水平布局来放置标签和图像
            row_layout = QHBoxLayout()
            row_layout.setSpacing(window.dimensions['spacing_small'])
            
            # 创建竖排标签
            vertical_text = '\n'.join(label_text)
            label = QLabel(vertical_text)
            label.setStyleSheet(window.styles['figure_label'])
            label.setFixedWidth(25)
            
            # 创建图像显示区域，使用STRETCH模式
            plot_widget = PlotWidget(scale_mode=ScaleMode.STRETCH)
            plot_widget.frame.setFrameShape(QFrame.Box)
            plot_widget.frame.setLineWidth(1)
            plot_widget.frame.setStyleSheet(window.styles['plot_frame'])
            if i == 0:
                plot_widget.plot_layout.setContentsMargins(0, 0, 0, 5)
            elif i == 4:
                plot_widget.plot_layout.setContentsMargins(0, 5, 0, 0)
            else:
                plot_widget.plot_layout.setContentsMargins(0, 5, 0, 5)
            
            # 存储图像显示区域
            window.middle_plots.append(plot_widget)
            
            # 添加标签和图像到行布局
            row_layout.addWidget(label)
            row_layout.addWidget(plot_widget, 1)
            
            # 添加行布局到主布局
            plots_layout.addLayout(row_layout)
        
        # 添加图像容器到主布局
        layout.addWidget(plots_container)
        
        ui_logger.debug("中间图像显示区布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建中间图像显示区布局时出错: {str(e)}")
        raise
    
    return layout


def _create_right_column(window) -> QVBoxLayout:
    """创建右侧列布局（用户交互区域）
    
    Args:
        window: 主窗口实例
    
    Returns:
        QVBoxLayout: 右侧列布局
    """
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 35, 0, 0)
    layout.setSpacing(0)
    
    try:
        # 数据导入模块
        import_layout = _create_import_module(window)
        layout.addLayout(import_layout)
        
        # 固定间距 10px
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # 切片信息模块
        slice_info_layout = _create_slice_info_module(window)
        layout.addLayout(slice_info_layout)
        
        # 固定间距 10px
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # 聚类参数模块和识别参数模块
        params_layout = QHBoxLayout()
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(10)
        cluster_module = _create_cluster_params_module(window)
        recognition_module = _create_recognition_params_module(window)
        # 调整两个模块的大小策略
        cluster_module.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        recognition_module.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 将两个模块添加到水平布局中
        params_layout.addWidget(cluster_module)
        params_layout.addWidget(recognition_module)
        # 将水平布局添加到主布局中
        layout.addLayout(params_layout)
        
        # 固定间距 10px
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # 单选按钮行
        radio_layout = _create_radio_module(window)
        layout.addLayout(radio_layout)
        
        # 固定间距 10px
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # 进度条模块
        progress_layout = _create_progress_module(window)
        layout.addLayout(progress_layout)
        
        # 固定间距 10px
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # 重绘输入行
        input_btn_layout = _create_redraw_module(window)
        layout.addLayout(input_btn_layout)
        
        # 固定间距 10px
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # 保存数据行
        save_layout = _create_save_module(window)
        layout.addLayout(save_layout)
        
        # 固定间距 10px
        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # 添加拨动开关模块
        switch_layout = _create_switch_module(window)
        layout.addLayout(switch_layout)
        
        # 固定间距 5px
        layout.addSpacerItem(QSpacerItem(0, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # 表格
        window.table = _create_table_widget(window)
        layout.addWidget(window.table)
        
        # 添加弹性空间到底部
        layout.addStretch()
        
        ui_logger.debug("右侧用户交互区布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建右侧用户交互区布局时出错: {str(e)}")
        raise
    
    return layout


def _create_import_module(window) -> QHBoxLayout:
    """创建数据导入模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QHBoxLayout: 数据导入模块布局
    """
    layout = QHBoxLayout()
    layout.setSpacing(0)
    
    try:
        # 创建导入路径输入框
        window.import_path = QLineEdit()
        window.import_path.setFixedHeight(window.dimensions['input_height'])
        window.import_path.setStyleSheet(window.styles['line_edit'])
        window.import_path.setFocusPolicy(Qt.ClickFocus)
        
        # 创建浏览和导入按钮
        window.browse_btn = QPushButton("浏览")
        window.import_btn = QPushButton("导入")
        
        for btn in [window.browse_btn, window.import_btn]:
            btn.setStyleSheet(window.styles['button'])
            btn.setFixedSize(window.dimensions['button_width'], 
                             window.dimensions['button_height'])
        
        # 添加到布局
        layout.addWidget(window.import_path)
        layout.addSpacing(5)
        layout.addWidget(window.browse_btn)
        layout.addSpacing(5)
        layout.addWidget(window.import_btn)
        
        ui_logger.debug("数据导入模块布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建数据导入模块布局时出错: {str(e)}")
        raise
    
    return layout


def _create_slice_info_module(window) -> QHBoxLayout:
    """创建切片信息模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QHBoxLayout: 切片信息模块布局
    """
    layout = QHBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

    try:
        # 创建两个标签
        window.slice_info_label1 = QLabel("数据包位于？波段，")
        window.slice_info_label1.setStyleSheet(window.styles['title_label'])
        window.slice_info_label1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        window.slice_info_label1.setFixedHeight(window.dimensions['line_max_height'])

        window.slice_info_label2 = QLabel("预计将获得 0 个250ms切片")
        window.slice_info_label2.setStyleSheet(window.styles['title_label'])
        window.slice_info_label2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        window.slice_info_label2.setFixedHeight(window.dimensions['line_max_height'])
        window.slice_info_label2.setTextFormat(Qt.RichText)  # 允许 HTML 格式
        # 添加到布局
        layout.addWidget(window.slice_info_label1)
        layout.addWidget(window.slice_info_label2)
        layout.addStretch()
        
        ui_logger.debug("切片信息模块布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建切片信息模块布局时出错: {str(e)}")
        raise
    
    return layout


def _create_cluster_params_module(window) -> QGroupBox:
    """创建聚类参数模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QGroupBox: 聚类参数模块组
    """
    try:
        # 创建组框
        window.cluster_params_group = QGroupBox("聚类参数设置")  # 保存引用
        window.cluster_params_group.setStyleSheet(window.styles['group_box'])
        window.cluster_params_group.setFixedHeight(window.dimensions['group_box_height'])
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建参数标签和输入框
        params = [
            ("epsilon_CF:", "epsilon_cf", "2", "  MHz"),
            ("epsilon_PW:", "epsilon_pw", "0.2", "  us"),
            ("min_pts:", "min_pts", "1", "")
        ]
        
        window.cluster_params = {}  # 存储参数输入框
        
        for label_text, param_name, default_value, unit in params:
            # 创建水平布局
            param_layout = QHBoxLayout()
            param_layout.setContentsMargins(0, 0, 0, 0)
            
            # 创建标签
            label = QLabel(label_text)
            label.setFixedHeight(window.dimensions['label_height'])
            label.setStyleSheet(window.styles['label'])
            label.setFixedWidth(window.dimensions['label_width_middle'])
            
            # 创建输入框
            input_field = QLineEdit(default_value)
            input_field.setFixedHeight(window.dimensions['input_height'])
            input_field.setFixedWidth(window.dimensions['input_width'])
            input_field.setStyleSheet(window.styles['line_edit'])
            input_field.setFocusPolicy(Qt.ClickFocus)
            
            # 创建单位标签
            unit_label = QLabel(unit)
            unit_label.setFixedHeight(window.dimensions['label_height'])
            unit_label.setFixedWidth(window.dimensions['label_unit_width'])
            unit_label.setStyleSheet(window.styles['label'])
            
            # 存储输入框引用
            window.cluster_params[param_name] = input_field
            
            # 添加到布局
            param_layout.addWidget(label)
            param_layout.addWidget(input_field)
            param_layout.addWidget(unit_label)
            param_layout.addStretch()

            # 添加到主布局
            layout.addLayout(param_layout)
            # 添加固定间距
            if label_text != params[-1][0]:
                layout.addSpacing(5)
        
        # 设置组框的布局
        window.cluster_params_group.setLayout(layout)
        
        ui_logger.debug("聚类参数模块布局创建完成")
        
        return window.cluster_params_group
        
    except Exception as e:
        ui_logger.error(f"创建聚类参数模块布局时出错: {str(e)}")
        raise


def _create_recognition_params_module(window) -> QGroupBox:
    """创建识别参数模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QGroupBox: 识别参数模块组
    """
    try:
        # 创建组框
        window.recognition_params_group = QGroupBox("识别参数设置")  # 保存引用
        window.recognition_params_group.setStyleSheet(window.styles['group_box'])
        window.recognition_params_group.setFixedHeight(window.dimensions['group_box_height'])
        
        # 创建布局
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建参数标签和输入框
        params = [
            ("PA判别权重:", "pa_weight", "1"),
            ("DTOA判别权重:", "dtoa_weight", "1"),
            ("联合判别门限:", "threshold", "0.9")
        ]
        
        window.recognition_params = {}  # 存储参数输入框
        
        for label_text, param_name, default_value in params:
            # 创建水平布局
            param_layout = QHBoxLayout()
            param_layout.setContentsMargins(0, 0, 0, 0)

            # 创建标签
            label = QLabel(label_text)
            label.setFixedHeight(window.dimensions['label_height'])
            label.setStyleSheet(window.styles['label'])
            label.setFixedWidth(window.dimensions['label_width_large'])
            
            # 创建输入框
            input_field = QLineEdit(default_value)
            input_field.setFixedHeight(window.dimensions['input_height'])
            input_field.setFixedWidth(window.dimensions['input_width'])
            input_field.setStyleSheet(window.styles['line_edit'])
            input_field.setFocusPolicy(Qt.ClickFocus)
            
            # 存储输入框引用
            window.recognition_params[param_name] = input_field
            
            # 添加到布局
            param_layout.addWidget(label)
            param_layout.addWidget(input_field)
            param_layout.addStretch()
            # 添加到主布局
            layout.addLayout(param_layout)
            # 添加固定间距
            if label_text != params[-1][0]:
                layout.addSpacing(5)
        
        # 设置组框的布局
        window.recognition_params_group.setLayout(layout)
        
        ui_logger.debug("识别参数模块布局创建完成")
        
        return window.recognition_params_group
        
    except Exception as e:
        ui_logger.error(f"创建识别参数模块布局时出错: {str(e)}")
        raise


def _create_radio_module(window) -> QVBoxLayout:
    """创建单选按钮模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QVBoxLayout: 单选按钮模块布局
    """
    main_layout = QVBoxLayout()  # 使用垂直布局
    
    try:
        # 创建按钮组
        window.radio_group = QButtonGroup()
        
        # 创建单选按钮
        window.radio1 = QRadioButton("切片处理")
        window.radio2 = QRadioButton("全速处理")
        window.radio1.setChecked(True)  # 默认选中第一个
        
        # 设置样式
        for radio in [window.radio1, window.radio2]:
            radio.setStyleSheet(window.styles['radio_button'])
        
        # 创建开始切片按钮
        window.start_slice_btn = QPushButton("开始切片")
        window.start_slice_btn.setStyleSheet(window.styles['button'])
        window.start_slice_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # 创建识别按钮
        window.identify_btn = QPushButton("识别")
        window.identify_btn.setStyleSheet(window.styles['button'])
        window.identify_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # 创建水平布局1
        row_layout1 = QHBoxLayout()
        row_layout1.addWidget(window.start_slice_btn)  # 开始切片按钮
        row_layout1.addSpacing(8)
        row_layout1.addWidget(window.identify_btn)  # 识别按钮
        row_layout1.addSpacing(30)
        row_layout1.addWidget(window.radio1)
        row_layout1.addWidget(window.radio2)
        
        # 创建下一片按钮
        window.next_slice_btn = QPushButton("下一片")
        window.next_slice_btn.setStyleSheet(window.styles['button'])
        window.next_slice_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # 创建下一类按钮
        window.next_cluster_btn = QPushButton("下一类")
        window.next_cluster_btn.setStyleSheet(window.styles['button'])
        window.next_cluster_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # 创建重置当前切片按钮
        window.reset_slice_btn = QPushButton("重置当前切片")
        window.reset_slice_btn.setStyleSheet(window.styles['large_button'])
        window.reset_slice_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # 创建复选框
        window.auto_identify_checkbox = QCheckBox("点击下一片后自动识别")
        window.auto_identify_checkbox.setStyleSheet(window.styles['checkbox'])
        window.auto_identify_checkbox.setChecked(True)
        
        # 创建水平布局2
        row_layout2 = QHBoxLayout()
        row_layout2.addWidget(window.next_cluster_btn)
        row_layout2.addSpacing(8)
        row_layout2.addWidget(window.next_slice_btn)
        row_layout2.addSpacing(8)
        row_layout2.addWidget(window.reset_slice_btn)
        row_layout2.addSpacing(30)
        row_layout2.addWidget(window.auto_identify_checkbox)
        
        # 添加到主布局
        main_layout.addLayout(row_layout1)
        main_layout.addSpacing(5)
        main_layout.addLayout(row_layout2)
        
        ui_logger.debug("单选按钮模块布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建单选按钮模块布局时出错: {str(e)}")
        raise
    
    return main_layout


def _create_progress_module(window) -> QHBoxLayout:
    """创建进度条模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QHBoxLayout: 进度条模块布局
    """
    layout = QHBoxLayout()
    
    try:
        # 创建进度条
        window.progress_bar = QProgressBar()
        window.progress_bar.setFixedHeight(window.dimensions['progress_height'])
        window.progress_bar.setStyleSheet(window.styles['progress_bar'])
        window.progress_bar.setAlignment(Qt.AlignCenter)
        
        # 创建进度标签
        window.progress_label = QLabel("0%")
        window.progress_label.setStyleSheet(window.styles['label'])
        window.progress_label.setFixedWidth(40)
        window.progress_label.setFixedHeight(20)
        window.progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 添加到布局
        layout.addWidget(window.progress_bar)
        layout.addWidget(window.progress_label)
        
        ui_logger.debug("进度条模块布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建进度条模块布局时出错: {str(e)}")
        raise
    
    return layout


def _create_redraw_module(window) -> QHBoxLayout:
    """创建重绘模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QHBoxLayout: 重绘模块布局
    """
    layout = QHBoxLayout()
    layout.setSpacing(0)
    
    try:
        # 创建选择切片标签
        window.slice_select_label = QLabel("输入切片编号:")
        window.slice_select_label.setFixedHeight(window.dimensions['label_height'])
        window.slice_select_label.setFixedWidth(window.dimensions['label_width_middle'])
        window.slice_select_label.setStyleSheet(window.styles['label'])
        
        # 创建输入框
        window.additional_input = QLineEdit()
        window.additional_input.setFixedHeight(window.dimensions['input_height'])
        window.additional_input.setStyleSheet(window.styles['line_edit'])
        window.additional_input.setFocusPolicy(Qt.ClickFocus)
        window.additional_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 创建重绘按钮
        window.redraw_btn = QPushButton("重绘")
        window.redraw_btn.setStyleSheet(window.styles['button'])
        window.redraw_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # 添加到布局
        layout.addWidget(window.slice_select_label)
        layout.addSpacing(10)
        layout.addWidget(window.additional_input)
        layout.addSpacing(5)
        layout.addWidget(window.redraw_btn)
        
        ui_logger.debug("重绘模块布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建重绘模块布局时出错: {str(e)}")
        raise
    
    return layout


def _create_save_module(window) -> QHBoxLayout:
    """创建保存模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QHBoxLayout: 保存模块布局
    """
    layout = QHBoxLayout()
    layout.setSpacing(0)
    
    try:
        # 创建保存路径输入框
        window.save_path = QLineEdit()
        window.save_path.setFixedHeight(window.dimensions['input_height'])
        window.save_path.setStyleSheet(window.styles['line_edit'])
        window.save_path.setFocusPolicy(Qt.ClickFocus)
        
        # 创建浏览和保存按钮
        window.browse_save_btn = QPushButton("浏览")
        window.save_btn = QPushButton("保存")
        
        for btn in [window.browse_save_btn, window.save_btn]:
            btn.setStyleSheet(window.styles['button'])
        
        # 添加到布局
        layout.addWidget(window.save_path)
        layout.addSpacing(5)
        layout.addWidget(window.browse_save_btn)
        layout.addSpacing(5)
        layout.addWidget(window.save_btn)
        
        ui_logger.debug("保存模块布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建保存模块布局时出错: {str(e)}")
        raise
    
    return layout


def _create_switch_module(window) -> QHBoxLayout:
    """创建拨动开关模块
    
    Args:
        window: 主窗口实例
    
    Returns:
        QHBoxLayout: 拨动开关模块布局
    """
    layout = QHBoxLayout()
    layout.setContentsMargins(5, 0, 5, 0)
    
    try:
        # 图像展示模式标签
        pic_show_mode_label = QLabel("图像展示模式:")
        pic_show_mode_label.setStyleSheet(window.styles['label'])
        pic_show_mode_label.setFixedWidth(window.dimensions['label_width_middle'])
        pic_show_mode_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 左侧标签
        left_label = QLabel("展示全部聚类结果")
        left_label.setStyleSheet(window.styles['label'])  # 默认选中左侧
        left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 左对齐
        
        # 拨动开关
        window.display_switch = Switch()
        window.display_switch.setChecked(False)  # 设置初始状态为左侧
        window.display_switch._pos = 0.0  # 初始化滑块位置
        
        # 右侧标签
        right_label = QLabel("仅展示识别后结果")
        right_label.setStyleSheet(window.styles['switch_label'])
        right_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 设置固定高度
        layout_height = window.dimensions['input_height']
        left_label.setFixedHeight(layout_height)
        right_label.setFixedHeight(layout_height)
        
        # 添加切换事件处理
        def on_switch_toggled(checked):
            # 更新标签样式
            if checked:
                left_label.setStyleSheet(window.styles['switch_label'])
                right_label.setStyleSheet(window.styles['label'])
            else:
                left_label.setStyleSheet(window.styles['label'])
                right_label.setStyleSheet(window.styles['switch_label'])
            # 更新 DataController 的显示模式
            # window.data_controller.set_display_mode(checked)
        
        # 连接开关的状态改变信号
        window.display_switch.stateChanged.connect(on_switch_toggled)
        
        # 添加到布局
        layout.addWidget(pic_show_mode_label)
        layout.addSpacing(5)
        layout.addWidget(left_label)
        layout.addSpacing(10)
        layout.addWidget(window.display_switch)
        layout.addSpacing(10)
        layout.addWidget(right_label)
        layout.addStretch()
        
        ui_logger.debug("拨动开关模块布局创建完成")
        
    except Exception as e:
        ui_logger.error(f"创建拨动开关模块布局时出错: {str(e)}")
        raise
    
    return layout


def _create_table_widget(window) -> QTableWidget:
    """创建表格组件
    
    Args:
        window: 主窗口实例
    
    Returns:
        QTableWidget: 表格组件
    """
    try:
        # 创建表格
        table = QTableWidget(9, 3)
        table.setStyleSheet(window.styles['table'])
        
        # 设置表头
        table.setHorizontalHeaderLabels(['雷达信号', '1', '2'])
        table.horizontalHeader().setFixedHeight(40)

        # 表格基本设置
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用垂直滚动条
        table.setShowGrid(True)  # 显示网格线
        table.verticalHeader().setVisible(False)  # 隐藏行号
        table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁用编辑
        table.setSelectionMode(QTableWidget.NoSelection)    # 禁用选择
        table.setWordWrap(True) # 启用自动换行
        
        # 设置行标签
        row_labels = [
            "载频/MHz",
            "脉宽/us",
            "PRI/us",
            "DOA/°",
            "PA预测分类",
            "PA预测概率",
            "DTOA预测分类",
            "DTOA预测概率",
            "联合预测概率"
        ]
        
        # 在第一列填充标签
        for i, label in enumerate(row_labels):
            item = QTableWidgetItem(label)
            # 设置文本居中对齐
            item.setTextAlignment(Qt.AlignCenter)
            # 设置第一列的背景色
            item.setBackground(QColor(window.theme_colors['table_header_bg']))
            table.setItem(i, 0, item)

        # 设置行高（除了PRI行）
        for i in range(9):
            if i != 2:  # 不是PRI行
                table.setRowHeight(i, 40)
                table.verticalHeader().setSectionResizeMode(i, QHeaderView.Fixed)
        
        # 设置第3行高度自适应
        table.verticalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 设置列宽策略
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.setColumnWidth(0, 130)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # 设置大小策略
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        size_policy.setVerticalStretch(1)  # 保持垂直方向的弹性
        size_policy.setHeightForWidth(table.sizePolicy().hasHeightForWidth())
        table.setSizePolicy(size_policy)

        # 设置表格最小高度为实际内容高度
        def update_table_height():
            header_height = table.horizontalHeader().height()
            content_height = sum(table.rowHeight(i) for i in range(table.rowCount()))
            total_height = header_height + content_height + 2

            # 计算最小高度（显示至少3行）
            min_row_height = 40  # 普通行的固定高度
            min_visible_rows = 3  # 最少显示3行
            min_height = header_height + (min_row_height * min_visible_rows)
            
            # 设置最小高度
            table.setMinimumHeight(min_height)
            
            # 如果有足够空间，则设置为完整高度
            if total_height > min_height:
                table.setMaximumHeight(total_height)
            else:
                table.setMaximumHeight(min_height)

        # 在行高变化后更新表格高度
        table.verticalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        # 监听内容变化
        table.itemChanged.connect(lambda: QTimer.singleShot(0, update_table_height))
        
        # 初始更新一次高度
        QTimer.singleShot(0, update_table_height)

        ui_logger.debug("表格组件创建完成")
        
        return table
        
    except Exception as e:
        ui_logger.error(f"创建表格组件时出错: {str(e)}")
        raise


def update_theme(window, theme: Theme) -> None:
    """更新主题样式
    
    Args:
        window: 主窗口实例
        theme: 要切换的主题
    """
    try:
        # 设置新主题
        StyleSheets.set_theme(theme)
        
        # 更新样式和配色
        window.styles = StyleSheets.get_styles()
        window.theme_colors = StyleSheets.get_theme_colors()
        
        # 更新主窗口样式
        window.setStyleSheet(window.styles['main_window'])
        
        # 更新所有组件样式
        # 标题标签
        window.left_title.setStyleSheet(window.styles['title_label'])
        window.middle_title.setStyleSheet(window.styles['title_label'])
        
        # 输入框
        window.import_path.setStyleSheet(window.styles['line_edit'])
        window.save_path.setStyleSheet(window.styles['line_edit'])
        window.additional_input.setStyleSheet(window.styles['line_edit'])
        
        # 按钮
        for btn in [window.browse_btn, window.import_btn,
                   window.browse_save_btn, window.save_btn,
                   window.start_slice_btn, window.identify_btn,
                   window.next_slice_btn, window.next_cluster_btn]:
            btn.setStyleSheet(window.styles['button'])
        
        window.reset_slice_btn.setStyleSheet(window.styles['large_button'])
        
        # 标签
        window.slice_info_label1.setStyleSheet(window.styles['label'])
        window.slice_info_label2.setStyleSheet(window.styles['label'])
        window.slice_select_label.setStyleSheet(window.styles['label'])
        window.progress_label.setStyleSheet(window.styles['label'])
        
        # 参数组
        window.cluster_params_group.setStyleSheet(window.styles['group_box'])
        window.recognition_params_group.setStyleSheet(window.styles['group_box'])
        
        # 单选按钮
        window.radio1.setStyleSheet(window.styles['radio_button'])
        window.radio2.setStyleSheet(window.styles['radio_button'])
        
        # 复选框
        window.auto_identify_checkbox.setStyleSheet(window.styles['checkbox'])
        
        # 进度条
        window.progress_bar.setStyleSheet(window.styles['progress_bar'])
        
        # 表格
        window.table.setStyleSheet(window.styles['table'])
        
        ui_logger.debug(f"主题已更新为: {theme.name}")
        
    except Exception as e:
        ui_logger.error(f"更新主题样式时出错: {str(e)}")
        raise
