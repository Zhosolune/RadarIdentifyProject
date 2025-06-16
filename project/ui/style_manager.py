class StyleManager:
    """UI样式管理类"""
    
    @staticmethod
    def get_styles() -> dict:
        """获取所有样式定义"""
        return {
            'main_window': """
                QMainWindow {
                    background-color: #4772c3;
                    border: 3px;
                }
                QWidget#centralWidget {
                    border-radius: 3px;
                    background-color: #4772c3;
                }
                * {
                    font-family: "Microsoft YaHei";
                    font-size: 16px;
                }
            """,
            
            'menubar': """
                QMenuBar {
                    background-color: #4772c3;
                    color: white;
                    border: none;
                    padding: 2px;
                    font-size: 18px;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 15px;
                    border-radius: 3px;
                    margin: 3px;
                }
                QMenuBar::item:selected {
                    background-color: #5c8ad4;
                }
                QMenuBar::item:pressed {
                    background-color: #3c61a5;
                }
            """,
            
            'menu': """
                QMenu {
                    background-color: white;
                    /* border: 1px solid #4772c3;
                    border-radius: 3px; */
                }
                QMenu::item {
                    font-size: 16px;
                    padding: 8px 25px 8px 20px;
                    color: #4772c3;
                }
                QMenu::item:selected {
                    background-color: #e6f3ff;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #A8D4FF;
                    margin: 2px 10px;
                }
            """,
            
            'dialog': """
                QDialog {
                    background-color: white;
                    /*border: 1px solid #4772c3;
                    border-radius: 5px;*/
                }
                QLabel {
                    color: #4772c3;
                }
                QRadioButton {
                    color: #4772c3;
                }
                QPushButton {
                    background-color: #4772c3;
                    color: white;
                    border: 1px solid white;
                    padding: 2px;
                    border-radius: 5px;
                    min-width: 60px;
                    max-width: 60px;
                    min-height: 30px;
                    max-height: 30px;
                }
                QPushButton:hover {
                    background-color: #5c8ad4;
                }
                QPushButton:pressed {
                    background-color: #3c61a5;
                }
                QGroupBox {
                    border: 1px solid #A8D4FF;
                    border-radius: 3px;
                    margin-top: 20px;
                    padding: 10px;
                }
                QGroupBox::title {
                    color: #4772c3;
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                }
            """,
            
            'dialog_path_label': """
                QLabel {
                    border: 1px solid #4772c3;
                    /* border-radius: 3px; */
                    padding: 3px 5px;
                    background-color: white;
                    color: #4772c3;
                    min-height: 25px;
                }
            """,
            
            'container': """
                QWidget {
                    background-color: #ffffff;
                    border-radius: 3px;
                }
            """,
            
            'title_label': """
                QLabel {
                    color: #4772c3;
                    font-size: 18px;
                    padding: 0;
                    font-weight: bold;
                }
            """,
            
            'label': """
                QLabel {
                    font-size: 16px;
                    color: #4772c3;
                    margin: 0;
                }
            """,

            'middle_label': """
                QLabel {
                    font-size: 18px;
                    color: #4772c3;
                    margin: 0;
                }
            """,

            'figure_label': """
                QLabel {
                    font-size: 16px;
                    color: #4772c3;
                    margin: 0;
                    padding: 2px;
                    qproperty-alignment: AlignCenter;
                }
            """,

            'switch_label': """
                QLabel {
                    font-size: 16px;
                    color: #999999;
                    margin: 0;
                }
            """,
            
            'line_edit': """
                QLineEdit {
                    border: 1px solid #4772c3;
                    border-radius: 3px;
                    padding: 2px;
                    background-color: white;
                    color: #4772c3;
                    min-height: 25px;
                    max-height: 25px;
                    margin: 0;
                }
                QLineEdit:hover {
                    border: 2px solid #A8D4FF;
                    border-radius: 3px;
                }
                QLineEdit:focus {
                    border: 2px solid #4772c3;
                    border-radius: 3px;
                }
            """,
            
            'button': """
                QPushButton {
                    background-color: #4772c3;
                    color: white;
                    border: 1px solid white;
                    padding: 2px;
                    border-radius: 3px;
                    min-width: 60px;
                    max-width: 60px;
                    min-height: 27px;
                    max-height: 27px;
                }
                QPushButton:hover {
                    background-color: #5c8ad4;
                }
                QPushButton:pressed {
                    background-color: #3c61a5;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                    /*border: 1px solid #999999;*/
                }
            """,

            'middle_button': """
                QPushButton {
                    background-color: #4772c3;
                    color: white;
                    border: 1px solid white;
                    padding: 2px;
                    border-radius: 3px;
                    min-width: 80px;
                    max-width: 80px;
                    min-height: 27px;
                    max-height: 27px;
                }
                QPushButton:hover {
                    background-color: #5c8ad4;
                }
                QPushButton:pressed {
                    background-color: #3c61a5;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                    /*border: 1px solid #999999;*/
                }
            """,
            'large_button': """
                QPushButton {
                    background-color: #4772c3;
                    color: white;
                    border: 1px solid white;
                    padding: 2px;
                    border-radius: 3px;
                    min-width: 120px;
                    max-width: 120px;
                    min-height: 27px;
                    max-height: 27px;
                }
                QPushButton:hover {
                    background-color: #5c8ad4;
                }
                QPushButton:pressed {
                    background-color: #3c61a5;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                    /*border: 1px solid #999999;*/
                }
            """,
            'group_box': """
                QGroupBox {
                    border: 1px solid #A8D4FF;
                    border-radius: 3px;
                    margin-top: 19px;
                }
                QGroupBox::title {
                    color: #4772c3; 
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 0px;        /* 调整标题左边距 */
                    top: -3px;        /* 微调标题垂直位置 */
                    padding: 0;   /* 调整标题内边距 */
                }
            """,
            
            'progress_bar': """
                QProgressBar {
                    border: 1px solid #4772c3;
                    border-radius: 3px;
                    background-color: white;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4772c3;
                }
            """,
            
            'radio_button': """
                QRadioButton {
                    spacing: 5px;
                    color: #4772c3;
                    font-size: 16px;
                }
                QRadioButton::indicator {
                    width: 15px;
                    height: 15px;
                }
            """,
            
            'table': """
                QTableWidget {
                    border: 1px solid #4772c3;
                    border-left: 2px solid #4772c3;
                    gridline-color: #4772c3;
                    border-radius: 3px;
                }
                QTableWidget::item {
                    padding: 1px;
                    color: #4772c3;
                    font-size: 16px;
                    font-weight: bold;
                }
                QTableWidget::item:selected {
                    background-color: #e6f3ff;
                }
                QHeaderView::section {
                    background-color: #4772c3;
                    color: white;
                    padding: 5px;
                    border: none;
                    font-weight: bold;
                }
                QTableCornerButton::section {
                    background-color: #4772c3;
                    border: none;
                    border-top-right-radius: 3px;
                }
                QTableWidget QScrollBar:vertical {
                    border-top-right-radius: 3px;
                    border-bottom-right-radius: 3px;
                }
            """,
            
            'checkbox': """
                QCheckBox {
                    spacing: 5px;
                    color: #4772c3;
                    font-size: 16px;
                }
                /* QCheckBox::indicator {
                    width: 15px;
                    height: 15px;
                    border: 1px solid #4772c3;
                    border-radius: 2px;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #A8D4FF;
                }
                QCheckBox::indicator:checked {
                    background-color: #4772c3;
                    border: 1px solid #4772c3;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #5c8ad4;
                    border: 2px solid #A8D4FF;
                } */
            """,

            'tab_widgets': """
                QTabWidget::pane {
                    background-color: #ffffff;
                    border-top: 1px solid #d0d0d0;
                }
                QTabBar::tab {
                    padding: 6px 12px;
                    width: 80px;
                    font-size: 18px;
                    color: #666666;
                }
                QTabBar::tab:hover {
                    color: #4772c3;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    border-bottom: 2px solid #4772c3;
                    font-weight: bold;
                    color: #4772c3;
                }
                QTabBar::tab:!selected {
                    border: none;
                }
            """,
            
            'path_empty_label': """
                QLabel {
                    background-color: rgba(255, 200, 200, 0.45);
                    padding: 2px 5px;
                    color: #c34747;
                    border: 1px solid transparent;
                }
            """,
            
            'path_selected_label': """
                QLabel {
                    background-color: rgba(168, 212, 255, 0.1);
                    padding: 2px 5px;
                    color: #4772c3;
                    border: 1px solid transparent;
                }
            """,
            
            'path_error_label': """
                QLabel {
                    background-color: rgba(255, 168, 168, 0.25);
                    padding: 2px 5px;
                    color: #c34747;
                    border: 1px solid #ff5555;
                    border-radius: 2px;
                }
            """
        }
    
    @staticmethod
    def get_dimensions() -> dict:
        """获取固定尺寸定义"""
        return {
            'window_width': 1200,
            'window_height': 800,
            'label_height': 25,
            'label_width_large': 120,
            'label_width_middle': 100,
            'label_width_small': 80,
            'label_unit_width': 50,
            'line_max_height': 30, 
            'button_height': 28,
            'button_width': 60,
            'progress_height': 20,
            'input_height': 30,
            'input_width': 80,
            'group_box_height': 130,
            'spacing_tiny': 1,
            'spacing_small': 5,
            'spacing_medium': 10,
            'spacing_large': 15,
            'title_height': 35,
            'margin': 10,
        }