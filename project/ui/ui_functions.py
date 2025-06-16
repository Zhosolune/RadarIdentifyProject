from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QProgressBar, QGroupBox,
    QRadioButton, QButtonGroup, QTableWidget, QHeaderView,
    QSizePolicy, QSpacerItem, QTableWidgetItem, QCheckBox,
    QTabWidget
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QTimer
from .plot_widget import PlotWidget, ScaleMode
from cores.log_manager import LogManager
from .switch_widget import Switch


def setup_ui(window) -> None:
    """设置主窗口UI"""
    logger = LogManager()
    logger.debug("开始设置主窗口UI")

    # 创建中央窗口部件
    central_widget = QWidget()
    window.setCentralWidget(central_widget)

    # 设置主窗口样式
    window.setStyleSheet(window.styles['main_window'])

    # 设置主布局的边距：上35px，其他10px
    main_layout = QHBoxLayout(central_widget)
    main_layout.setContentsMargins(10, 0, 10, 10)

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
    # column_widget3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    # 添加列到容器布局
    container_layout.addWidget(column_widget1, 1)
    container_layout.addWidget(column_widget2, 1)
    container_layout.addWidget(column_widget3)


def _create_left_column(window) -> QVBoxLayout:
    """创建左侧列布局"""
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

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

    # 图像标签文字，顺序决定标签和图像显示的顺序，因为图像显示的顺序依据于该列表的顺序
    # labels = ["载频", "脉宽", "幅度", "方位角", "一级差"]
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
        plot_widget = PlotWidget()
        if i == 0:  # 第一个图像
            plot_widget.plot_layout.setContentsMargins(0, 0, 0, 5)
        elif i == 4:  # 最后一个图像
            plot_widget.plot_layout.setContentsMargins(0, 5, 0, 0)
        else:  # 中间的图像
            plot_widget.plot_layout.setContentsMargins(0, 5, 0, 5)

        # 存储图像显示区域
        window.left_plots.append(plot_widget)  # 添加到列表

        # 添加标签和图像到行布局
        row_layout.addWidget(label)
        row_layout.addWidget(plot_widget, 1)

        # 添加行布局到主布局
        plots_layout.addLayout(row_layout)

    layout.addWidget(plots_container)
    return layout


def _create_middle_column(window) -> QVBoxLayout:
    """创建中列布局"""
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

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

    # 图像标签文字和对应的图像类型，顺序决定标签和图像显示的顺序，因为图像显示的顺序依据于该列表的顺序
    # labels_and_types = [
    #     ("载频", "CF"),
    #     ("脉宽", "PW"),
    #     ("幅度", "PA"),
    #     ("方位角", "DOA"),
    #     ("一级差", "DTOA")
    # ]
    labels_and_types = [
        ("载频", "CF"),
        ("脉宽", "PW"),
        ("幅度", "PA"),
        ("一级差", "DTOA"),
        ("方位角", "DOA")
    ]

    window.middle_plots = []  # 清空列表

    # 添加5个图像和对应的标签
    for i, (label_text, plot_type) in enumerate(labels_and_types):
        # 创建水平布局来放置标签和图像
        row_layout = QHBoxLayout()
        row_layout.setSpacing(window.dimensions['spacing_small'])  # 标签和图像之间的间距

        # 创建竖排标签
        vertical_text = '\n'.join(label_text)
        label = QLabel(vertical_text)
        label.setStyleSheet(window.styles['figure_label'])
        label.setFixedWidth(25)

        # 创建图像显示区域，使用STRETCH模式
        plot_widget = PlotWidget(scale_mode=ScaleMode.STRETCH)
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

    layout.addWidget(plots_container)
    return layout


def _create_right_column(window) -> QVBoxLayout:
    """创建右列布局"""
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 35, 0, 0)
    layout.setSpacing(0)

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

    # 标签页区域
    tab_widget = _create_tab_widget(window)
    # 修改标签页的大小策略，使其不会垂直拉伸
    tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    layout.addWidget(tab_widget)

    # 确保固定间距 10px
    layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # 表格
    table_layout = _create_table_widget(window)
    layout.addLayout(table_layout)

    # 添加弹性空间到底部
    # layout.addStretch()

    return layout


def _create_import_module(window) -> QHBoxLayout:
    """创建数据导入模块"""
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)

    # 创建导入路径标签和输入框
    # path_label = QLabel("导入路径:")
    # path_label.setFixedHeight(window.dimensions['label_height'])
    # path_label.setFixedWidth(window.dimensions['label_width_large'])
    # path_label.setStyleSheet(window.styles['label'])

    window.import_path = QLineEdit()
    window.import_path.setFixedHeight(window.dimensions['input_height'])
    window.import_path.setStyleSheet(window.styles['line_edit'])
    window.import_path.setFocusPolicy(Qt.ClickFocus)

    # 创建浏览和导入按钮
    window.browse_import_btn = QPushButton("浏览")
    window.import_btn = QPushButton("导入")
    for btn in [window.browse_import_btn, window.import_btn]:
        btn.setStyleSheet(window.styles['button'])
        btn.setFixedSize(window.dimensions['button_width'],
                         window.dimensions['button_height'])
        btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

    # 添加到布局
    # layout.addWidget(path_label)
    layout.addWidget(window.import_path)
    layout.addSpacing(5)
    layout.addWidget(window.browse_import_btn)
    layout.addSpacing(5)
    layout.addWidget(window.import_btn)

    return layout


def _create_slice_info_module(window) -> QHBoxLayout:
    """创建切片信息模块"""
    layout = QHBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

    # 创建标签
    window.slice_info_label1 = QLabel("数据包位于？波段，")
    window.slice_info_label1.setStyleSheet(window.styles['title_label'])
    window.slice_info_label1.setAlignment(Qt.AlignLeft)
    window.slice_info_label1.setFixedHeight(window.dimensions['line_max_height'])

    window.slice_info_label2 = QLabel("预计将获得  0  个250ms切片")
    window.slice_info_label2.setStyleSheet(window.styles['title_label'])
    window.slice_info_label2.setAlignment(Qt.AlignLeft)
    window.slice_info_label2.setFixedHeight(window.dimensions['line_max_height'])
    window.slice_info_label2.setTextFormat(Qt.RichText)  # 允许 HTML 格式

    layout.addWidget(window.slice_info_label1)
    layout.addWidget(window.slice_info_label2)
    layout.addStretch()

    return layout


def _create_cluster_params_module(window) -> QGroupBox:
    """创建聚类参数模块"""
    group = QGroupBox("聚类参数设置")
    group.setStyleSheet(window.styles['group_box'])
    group.setFixedHeight(window.dimensions['group_box_height'])

    layout = QVBoxLayout()
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(0)

    # 参数配置
    params = [
        ("epsilon_CF:", "2", "  MHz"),
        ("epsilon_PW:", "0.2", "  us"),
        ("min_pts:", "1", "")
    ]

    window.param_inputs = []

    for label_text, default_value, label_unit in params:
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setFixedHeight(window.dimensions['label_height'])
        label.setFixedWidth(window.dimensions['label_width_middle'])
        label.setStyleSheet(window.styles['label'])

        input_field = QLineEdit(default_value)
        input_field.setFixedHeight(window.dimensions['input_height'])
        input_field.setFixedWidth(window.dimensions['input_width'])
        input_field.setStyleSheet(window.styles['line_edit'])
        input_field.setFocusPolicy(Qt.ClickFocus)

        unit = QLabel(label_unit)
        unit.setFixedHeight(window.dimensions['label_height'])
        unit.setFixedWidth(window.dimensions['label_unit_width'])
        unit.setStyleSheet(window.styles['label'])

        window.param_inputs.append(input_field)

        row_layout.addWidget(label)
        row_layout.addWidget(input_field)
        row_layout.addWidget(unit)
        row_layout.addStretch()

        layout.addLayout(row_layout)
        # 添加固定间距（除了最后一个参数）
        if label_text != params[-1][0]:
            layout.addSpacing(5)

    group.setLayout(layout)
    return group


def _create_recognition_params_module(window) -> QGroupBox:
    """创建识别参数模块"""
    group = QGroupBox("识别参数设置")
    group.setStyleSheet(window.styles['group_box'])
    group.setFixedHeight(window.dimensions['group_box_height'])

    layout = QVBoxLayout()
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(0)

    # 参数配置
    params = [
        ("PA判别权重:", "1"),
        ("DTOA判别权重:", "1"),
        ("联合判别门限:", "0.9")
    ]

    for label_text, default_value in params:
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setFixedHeight(window.dimensions['label_height'])
        label.setFixedWidth(window.dimensions['label_width_large'])
        label.setStyleSheet(window.styles['label'])

        input_field = QLineEdit(default_value)
        input_field.setFixedHeight(window.dimensions['input_height'])
        input_field.setFixedWidth(window.dimensions['input_width'])
        input_field.setStyleSheet(window.styles['line_edit'])
        input_field.setFocusPolicy(Qt.ClickFocus)

        window.param_inputs.append(input_field)

        row_layout.addWidget(label)
        row_layout.addWidget(input_field)
        row_layout.addStretch()

        layout.addLayout(row_layout)
        # 添加固定间距（除了最后一个参数）
        if label_text != params[-1][0]:
            layout.addSpacing(5)

    group.setLayout(layout)
    return group


def _create_tab_widget(window) -> QTabWidget:
    """创建标签页布局"""
    # 创建标签页容器
    tab_widget = QTabWidget()
    tab_widget.setStyleSheet(window.styles['tab_widgets'])
    
    # 设置标签页不会过度扩展，保持紧凑布局
    tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    # 创建切片处理标签页
    slice_proc_tab = QWidget()
    slice_proc_tab_layout = QVBoxLayout(slice_proc_tab)
    slice_proc_tab_layout.setContentsMargins(0, 10, 0, 0)
    slice_proc_tab_layout.setSpacing(0)

    # 添加切片处理模块到切片处理标签页
    slice_process_layout = _create_slice_process_module(window)
    slice_proc_tab_layout.addLayout(slice_process_layout)

    # 固定间距 10px
    slice_proc_tab_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # 添加图像显示模式模块到切片处理标签页
    figure_show_mode = _create_switch_module(window)
    slice_proc_tab_layout.addLayout(figure_show_mode)
    
    # 固定间距 10px
    slice_proc_tab_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # 添加重绘模块到切片处理标签页
    redraw_layout = _create_redraw_module(window)
    slice_proc_tab_layout.addLayout(redraw_layout)

    # 固定间距 10px
    slice_proc_tab_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # 添加保存模块到切片处理标签页
    save_layout = _create_save_slice_proc_module(window)
    slice_proc_tab_layout.addLayout(save_layout)

    # 切片处理标签页添加最小弹性空间
    slice_proc_tab_layout.addStretch(0)

    # 创建全速处理标签页
    full_speed_tab = QWidget()
    full_speed_layout = QVBoxLayout(full_speed_tab)
    full_speed_layout.setContentsMargins(0, 10, 0, 0)
    full_speed_layout.setSpacing(0)

    # 添加保存全速处理结果模块
    save_full_speed_layout = _create_save_full_speed_module(window)
    full_speed_layout.addLayout(save_full_speed_layout)

    # 固定间距 10px
    full_speed_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # 添加开始处理按钮模块
    start_process_layout = _create_full_speed_start_process_module(window)
    full_speed_layout.addLayout(start_process_layout)

    # 固定间距 10px
    full_speed_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

    # 添加进度条模块
    progress_layout = _create_progress_module(window)
    full_speed_layout.addLayout(progress_layout)

    # 添加处理详情标签
    process_detail_layout = _create_process_detail_module(window)
    full_speed_layout.addLayout(process_detail_layout)
    
    # 全速处理标签页添加最小弹性空间
    full_speed_layout.addStretch(0)

    # 添加标签页到标签页容器
    tab_widget.addTab(slice_proc_tab, "切片处理")
    tab_widget.addTab(full_speed_tab, "全速处理")
    
    # 保存标签页对象方便后续访问
    window.slice_proc_tab = slice_proc_tab
    window.full_speed_tab = full_speed_tab
    window.tab_widget = tab_widget
    
    # 标签页切换的事件处理
    def on_tab_changed(index):
        # 切换到切片处理标签页
        if index == 0:
            window.logger.debug("切换到切片处理标签页")
            # 在这里可以添加切换到切片处理标签页时的逻辑
        # 切换到全速处理标签页
        elif index == 1:
            window.logger.debug("切换到全速处理标签页")
            # 在这里可以添加切换到全速处理标签页时的逻辑
    
    # 连接标签页切换信号
    tab_widget.currentChanged.connect(on_tab_changed)
    
    # 获取标签页栏并设置光标
    tab_bar = tab_widget.tabBar()
    tab_bar.setCursor(Qt.PointingHandCursor)

    return tab_widget


def _create_slice_process_module(window) -> QVBoxLayout:
    """创建切片处理模块"""
    main_layout = QVBoxLayout()  # 使用垂直布局

    # 创建水平布局1
    row_layout1 = QHBoxLayout()
    
    # 创建开始切片按钮
    window.start_slice_btn = QPushButton("开始切片")
    window.start_slice_btn.setStyleSheet(window.styles['button'])
    window.start_slice_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    window.start_slice_btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

    # 创建识别按钮
    window.identify_btn = QPushButton("识别")
    window.identify_btn.setStyleSheet(window.styles['button'])
    window.identify_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    window.identify_btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

    # 添加组件到第一行布局
    row_layout1.addWidget(window.start_slice_btn)  # 开始切片按钮
    row_layout1.addSpacing(8)
    row_layout1.addWidget(window.identify_btn)  # 识别按钮
    row_layout1.addStretch()

    # 创建下一片按钮
    window.next_slice_btn = QPushButton("下一片")
    window.next_slice_btn.setStyleSheet(window.styles['button'])
    window.next_slice_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    window.next_slice_btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

    # 创建下一类按钮
    window.next_cluster_btn = QPushButton("下一类")
    window.next_cluster_btn.setStyleSheet(window.styles['button'])
    window.next_cluster_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    window.next_cluster_btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

    # 创建重置当前切片按钮
    window.reset_slice_btn = QPushButton("重置当前切片")
    window.reset_slice_btn.setStyleSheet(window.styles['large_button'])
    window.reset_slice_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    window.reset_slice_btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

    # 创建复选框
    window.auto_identify_checkbox = QCheckBox("点击下一片后自动识别")
    window.auto_identify_checkbox.setStyleSheet(window.styles['checkbox'])
    window.auto_identify_checkbox.setChecked(True)
    window.auto_identify_checkbox.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

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

    return main_layout


def _create_progress_module(window) -> QHBoxLayout:
    """创建进度条模块"""
    layout = QHBoxLayout()

    # 创建进度条
    window.progress_bar = QProgressBar()
    window.progress_bar.setFixedHeight(window.dimensions['progress_height'])
    window.progress_bar.setStyleSheet(window.styles['progress_bar'])
    window.progress_bar.setAlignment(Qt.AlignCenter)
    window.progress_bar.setTextVisible(False)

    # 创建进度标签
    window.progress_label = QLabel("0%")
    window.progress_label.setStyleSheet(window.styles['title_label'])
    window.progress_label.setFixedWidth(60)
    window.progress_label.setFixedHeight(20)
    window.progress_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

    # 添加到布局
    layout.addWidget(window.progress_bar)
    layout.addWidget(window.progress_label)

    return layout

def _create_process_detail_module(window) -> QHBoxLayout:
    """创建处理详情模块"""
    layout = QHBoxLayout()

    # 创建标签
    window.process_detail_label = QLabel("")
    window.process_detail_label.setStyleSheet(window.styles['label'])
    window.process_detail_label.setFixedHeight(window.dimensions['input_height'])
    window.process_detail_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    # 添加到布局
    layout.addWidget(window.process_detail_label)

    return layout


def _create_redraw_module(window) -> QHBoxLayout:
    """创建重绘模块"""
    layout = QHBoxLayout()
    layout.setSpacing(0)

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
    window.redraw_btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

    # 添加到布局
    layout.addWidget(window.slice_select_label)
    layout.addSpacing(10)
    layout.addWidget(window.additional_input)
    layout.addSpacing(5)
    layout.addWidget(window.redraw_btn)

    return layout


def _create_save_slice_proc_module(window) -> QHBoxLayout:
    """创建保存模块"""
    layout = QHBoxLayout()
    layout.setSpacing(window.dimensions['spacing_small'])
    layout.setContentsMargins(0, 0, 0, 0)
    
    # 创建选择保存路径按钮
    window.browse_save_btn1 = QPushButton("选择路径")
    window.browse_save_btn1.setStyleSheet(window.styles['middle_button'])
    window.browse_save_btn1.setFixedHeight(window.dimensions['input_height'])
    window.browse_save_btn1.setFixedWidth(80)  # 缩短按钮宽度
    window.browse_save_btn1.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状
    
    # 创建路径显示标签
    window.save_path_label1 = QLabel()
    window.save_path_label1.setFixedHeight(window.dimensions['input_height'])
    # 默认为浅红色阴影样式（未选择路径）
    window.save_path_label1.setStyleSheet(window.styles['path_empty_label'])
    window.save_path_label1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    window.save_path_label1.setText("")  # 初始为空
    
    # 保存样式引用便于后续使用
    window.path_empty_style = window.styles['path_empty_label']
    window.path_selected_style = window.styles['path_selected_label']
    window.path_error_style = window.styles['path_error_label']
    
    # 创建保存按钮
    window.save_btn = QPushButton("保存")
    window.save_btn.setStyleSheet(window.styles['button'])
    window.save_btn.setFixedHeight(window.dimensions['input_height'])
    window.save_btn.setFixedWidth(60)
    window.save_btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状
    
    # 创建自动保存开关
    window.auto_save_switch = Switch()
    window.auto_save_switch.setChecked(False)  # 默认关闭自动保存（修改时也要修改main_window.py中的初始化部分：self.auto_save = False，以及下一行标签初始位置）
    window.auto_save_switch._pos = 0.0
    
    # 自动保存标签
    auto_save_label = QLabel("自动保存")
    auto_save_label.setStyleSheet(window.styles['switch_label'])
    auto_save_label.setFixedHeight(window.dimensions['input_height'])
    auto_save_label.setAlignment(Qt.AlignCenter)
    
    # 添加到布局
    layout.addWidget(window.browse_save_btn1)
    layout.addWidget(window.save_path_label1, 1)  # 设置伸展系数为1，使其占据所有可用空间
    layout.addWidget(window.save_btn)
    layout.addWidget(window.auto_save_switch)
    layout.addWidget(auto_save_label)
    
    # 设置文本滚动效果
    window.path_scroll_timer = QTimer(window)
    window.path_scroll_timer.setInterval(100)  # 滚动速度
    window.path_scroll_position = 0
    
    # 添加闪烁效果的定时器
    window.blink_timer = QTimer(window)
    window.blink_timer.setInterval(300)  # 闪烁速度
    window.blink_count = 0
    window.max_blink_count = 4  # 闪烁2次 = 4次状态变化
    
    # 创建工具类实例
    save_tools = SaveModuleTools(window)
    
    # 连接闪烁定时器
    window.blink_timer.timeout.connect(save_tools.blink_path_label)
    
    # 将工具函数添加到window对象
    window.trigger_path_label_blink = save_tools.trigger_blink
    window.update_path_label_style = save_tools.update_path_label_style
    
    # 连接滚动定时器
    window.path_scroll_timer.timeout.connect(save_tools.scroll_path_text)
    
    # 在标签大小变化时检查是否需要滚动
    window.save_path_label1.resizeEvent = save_tools.new_resize_event
    
    # 设置自动保存状态改变的事件处理
    window.auto_save_switch.stateChanged.connect(lambda checked: save_tools.on_auto_save_toggled(checked, auto_save_label))
    
    return layout

def _create_save_full_speed_module(window) -> QVBoxLayout:
    """创建保存全速处理结果模块"""
    # 创建垂直布局
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)

    save_label_layout = QVBoxLayout()
    
    window.start_process_label = QLabel("全速处理之前必须指定结果保存路径！")
    window.start_process_label.setStyleSheet(window.styles['title_label'])
    window.start_process_label.setFixedHeight(window.dimensions['input_height'])
    window.start_process_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    save_label_layout.addWidget(window.start_process_label)

    save_layout = QHBoxLayout()
    save_layout.setSpacing(window.dimensions['spacing_small'])
    
    # 创建选择保存路径按钮
    window.browse_save_btn2 = QPushButton("选择保存路径")
    window.browse_save_btn2.setStyleSheet(window.styles['large_button'])
    window.browse_save_btn2.setFixedHeight(window.dimensions['input_height'])
    window.browse_save_btn2.setFixedWidth(80)  # 缩短按钮宽度
    window.browse_save_btn2.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状
    
    # 创建路径显示标签
    window.save_path_label2 = QLabel()
    window.save_path_label2.setFixedHeight(window.dimensions['input_height'])
    # 默认为浅红色阴影样式（未选择路径）
    window.save_path_label2.setStyleSheet(window.styles['path_empty_label'])
    window.save_path_label2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    window.save_path_label2.setText("")  # 初始为空
    
    # 保存样式引用便于后续使用
    window.path_empty_style = window.styles['path_empty_label']
    window.path_selected_style = window.styles['path_selected_label']
    window.path_error_style = window.styles['path_error_label']
    
    # 添加到布局
    save_layout.addWidget(window.browse_save_btn2)
    save_layout.addWidget(window.save_path_label2, 1)  # 设置伸展系数为1，使其占据所有可用空间

    main_layout.addLayout(save_label_layout)
    main_layout.addSpacing(10)
    main_layout.addLayout(save_layout)

    return main_layout

def _create_full_speed_start_process_module(window) -> QVBoxLayout:
    """创建全速处理开始按钮模块"""
    
    # 添加开始处理按钮
    button_layout = QVBoxLayout()

    # 创建开始处理按钮
    window.start_process_btn = QPushButton("开始处理")
    window.start_process_btn.setStyleSheet(window.styles['middle_button'])
    window.start_process_btn.setFixedHeight(window.dimensions['button_height'])
    window.start_process_btn.setCursor(Qt.PointingHandCursor)  # 设置鼠标悬停时为手指形状

    # TODO: 创建暂停按钮
    pass

    # TODO: 创建继续按钮
    pass

    # TODO: 创建终止按钮
    pass

    button_layout.addWidget(window.start_process_btn)

    return button_layout

def _create_switch_module(window) -> QHBoxLayout:
    """创建拨动开关模块"""
    layout = QHBoxLayout()
    
    # 图像展示模式标签
    pic_show_mode_label = QLabel("图像展示模式:")
    pic_show_mode_label.setStyleSheet(window.styles['label'])
    pic_show_mode_label.setFixedWidth(window.dimensions['label_width_middle'])
    pic_show_mode_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
    # 左侧标签
    left_label = QLabel("展示全部聚类结果")
    # left_label.setStyleSheet(window.styles['label'])  # 默认选中左侧
    left_label.setStyleSheet(window.styles['switch_label'])  # 默认选中右侧
    left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 左对齐
    
    # 拨动开关
    window.display_switch = Switch()
    # window.display_switch.setChecked(False)  # 设置初始状态为左侧
    # window.display_switch._pos = 0.0  # 初始化滑块位置
    window.display_switch.setChecked(True)  # 设置初始状态为右侧
    window.display_switch._pos = 1.0  # 初始化滑块位置
    
    # 右侧标签
    right_label = QLabel("仅展示识别后结果")
    # right_label.setStyleSheet(window.styles['switch_label'])
    right_label.setStyleSheet(window.styles['label'])
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
        window.data_controller.set_display_mode(checked)
    
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
    
    return layout

def _create_table_widget(window) -> QVBoxLayout:
    """创建表格模块"""
    layout = QVBoxLayout()

    # 创建表格标签
    table_label = QLabel("雷达信号识别结果：")
    table_label.setStyleSheet(window.styles['title_label'])
    table_label.setFixedHeight(window.dimensions['input_height'])
    table_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    # 创建表格部件
    window.table = QTableWidget(9, 3)

    # 设置表头
    window.table.setHorizontalHeaderLabels(['雷达信号', '1', '2'])
    window.table.horizontalHeader().setFixedHeight(40)

    # 启用自动换行
    window.table.setWordWrap(True)

    # 设置行标签
    # row_labels = [
    #     "载频/MHz",
    #     "脉宽/us",
    #     "PRI/us",
    #     "DOA/°",
    #     "PA预测分类",
    #     "PA预测概率",
    #     "DTOA预测分类",
    #     "DTOA预测概率",
    #     "联合预测概率"
    # ]
    row_labels = [
        "载频/MHz",
        "脉宽/us",
        "PRI/us",
        "DOA/°",
        "PA预测结果",
        "PA预测分类",
        "DTOA预测结果",
        "DTOA预测分类",
        "联合预测概率"
    ]

    # 在第一列填充标签
    for i, label in enumerate(row_labels):
        item = QTableWidgetItem(label)
        # 设置单元格不可编辑
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        # 设置文本居中对齐
        item.setTextAlignment(Qt.AlignCenter)
        # 可以设置背景色使其更像标签
        item.setBackground(QColor(240, 240, 240))
        window.table.setItem(i, 0, item)

    # 设置固定行高
    for i in range(9):
        if i != 2 and i != 4 and i != 6:  # 除了第3行（索引为2）外的所有行
            window.table.setRowHeight(i, 40)
            window.table.verticalHeader().setSectionResizeMode(i, QHeaderView.Fixed)
    
    # 设置第3行高度自适应
    window.table.verticalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    window.table.verticalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
    window.table.verticalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)

    # 表格基本设置
    window.table.setShowGrid(True)  # 显示网格线
    window.table.verticalHeader().setVisible(False)  # 隐藏行号

    # 设置列宽策略
    window.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # 第一列固定宽度
    window.table.setColumnWidth(0, 130)  # 设置第一列宽度为130
    window.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 第二列自适应
    window.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # 第三列自适应

    window.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
    window.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用垂直滚动条

    # 设置表格样式
    window.table.setStyleSheet(window.styles['table'])

    # 修改大小策略
    # size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    # size_policy.setVerticalStretch(1)  # 保持垂直方向的弹性
    # table.setSizePolicy(size_policy)

    # 修改大小策略
    size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    size_policy.setVerticalStretch(1)  # 保持垂直方向的弹性
    size_policy.setHeightForWidth(window.table.sizePolicy().hasHeightForWidth())
    window.table.setSizePolicy(size_policy)

    # 设置表格的最小高度为实际内容高度
    def update_table_height():
        header_height = window.table.horizontalHeader().height()
        content_height = sum(window.table.rowHeight(i) for i in range(window.table.rowCount()))
        total_height = header_height + content_height + 2
        
        # 计算最小高度（显示至少3行）
        min_row_height = 40  # 普通行的固定高度
        min_visible_rows = 3  # 最少显示3行
        min_height = header_height + (min_row_height * min_visible_rows)
        
        # 设置最小高度
        window.table.setMinimumHeight(min_height)
        
        # 如果有足够空间，则设置为完整高度
        if total_height > min_height:
            window.table.setMaximumHeight(total_height)
        else:
            window.table.setMaximumHeight(min_height)

    # 在行高变化后更新表格高度
    window.table.verticalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    window.table.verticalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
    window.table.verticalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
    # 监听内容变化
    window.table.itemChanged.connect(lambda: QTimer.singleShot(0, update_table_height))
    
    # 初始更新一次高度
    QTimer.singleShot(0, update_table_height)

    # 添加标签到布局
    layout.addWidget(table_label)

    # 添加表格部件到布局
    layout.addWidget(window.table)
    layout.addStretch()

    return layout



class SaveModuleTools:
    """保存模块工具类"""
    def __init__(self, window):
        self.window = window
        # 保存原始的resize事件处理函数
        self.original_resize_event = self.window.save_path_label1.resizeEvent
        
    def blink_path_label(self):
        """路径标签闪烁效果"""
        if self.window.blink_count >= self.window.max_blink_count:
            self.window.blink_timer.stop()
            self.window.blink_count = 0
            # 恢复到未选择路径的样式
            self.window.save_path_label1.setStyleSheet(self.window.path_empty_style)
            return
            
        # 切换样式
        if self.window.blink_count % 2 == 0:
            self.window.save_path_label1.setStyleSheet(self.window.path_error_style)
        else:
            self.window.save_path_label1.setStyleSheet(self.window.path_empty_style)
            
        self.window.blink_count += 1
    
    def trigger_blink(self):
        """触发路径标签闪烁效果"""
        self.window.blink_count = 0
        self.window.blink_timer.start()
    
    def update_path_label_style(self, has_path=False):
        """更新路径标签样式"""
        if self.window.blink_timer.isActive():
            # 如果正在闪烁，不更新样式
            return
            
        if has_path:
            self.window.save_path_label1.setStyleSheet(self.window.path_selected_style)
            self.window.save_path_label2.setStyleSheet(self.window.path_selected_style)
        else:
            self.window.save_path_label1.setStyleSheet(self.window.path_empty_style)
            self.window.save_path_label2.setStyleSheet(self.window.path_empty_style)
    
    def scroll_path_text(self):
        """滚动显示路径文本"""
        label = self.window.save_path_label1
        text = label.text()
        if not text:
            return
            
        # 获取文本宽度和标签宽度
        metrics = label.fontMetrics()
        text_width = metrics.width(text)
        label_width = label.width() - 10  # 考虑内边距
        
        # 如果文本宽度小于标签宽度，不需要滚动
        if text_width <= label_width:
            return
            
        # 文本太长，需要滚动
        self.window.path_scroll_position = (self.window.path_scroll_position + 1) % (text_width + label_width)
        
        # 计算可见文本
        if self.window.path_scroll_position < text_width:
            # 找到从当前位置开始的字符
            visible_start = 0
            current_width = 0
            for i, char in enumerate(text):
                char_width = metrics.width(char)
                if current_width >= self.window.path_scroll_position:
                    visible_start = i
                    break
                current_width += char_width
                
            visible_text = text[visible_start:]
            if metrics.width(visible_text) > label_width:
                # 截断超出显示区域的文本
                visible_text = visible_text[:30] + "..."  # 简单处理
        else:
            # 显示文本开头
            visible_text = text
            
        # 更新显示
        label.setText(visible_text)
    
    def check_scroll_needed(self):
        """检查是否需要滚动显示"""
        label = self.window.save_path_label1
        text = label.text()
        if not text:
            if self.window.path_scroll_timer.isActive():
                self.window.path_scroll_timer.stop()
            return
            
        metrics = label.fontMetrics()
        if metrics.width(text) > label.width() - 10:
            if not self.window.path_scroll_timer.isActive():
                self.window.path_scroll_position = 0
                self.window.path_scroll_timer.start()
        else:
            if self.window.path_scroll_timer.isActive():
                self.window.path_scroll_timer.stop()
    
    def new_resize_event(self, event):
        """标签大小变化事件处理"""
        # 调用原始的resize事件处理函数
        if self.original_resize_event is not None:
            self.original_resize_event(event)
        # 检查是否需要滚动
        self.check_scroll_needed()
    
    def on_auto_save_toggled(self, checked, auto_save_label):
        """处理自动保存状态改变"""
        self.window.auto_save = checked
        # 更新标签样式
        if checked:
            auto_save_label.setStyleSheet(self.window.styles['label'])
        else:
            auto_save_label.setStyleSheet(self.window.styles['switch_label'])
        self.window.logger.info(f"自动保存设置已{'启用' if checked else '禁用'}")

    