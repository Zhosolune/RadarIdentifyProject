"""样式表模块

本模块负责定义和管理系统的所有UI样式，包括：
1. 主题管理
2. 颜色主题
3. 组件样式
4. 尺寸常量
5. 布局参数
"""

from enum import Enum, auto
from typing import Dict


class Theme(Enum):
    """主题枚举类
    
    定义系统支持的所有主题类型
    """
    DEFAULT = auto()      # 默认主题
    DARK = auto()         # 暗黑主题
    CYBERPUNK = auto()    # 赛博朋克主题
    SKYBLUE = auto()      # 晴空主题
    FOREST = auto()       # 森林主题
    SUNSET = auto()       # 日落主题


class ThemeColors:
    """主题配色类
    
    定义不同主题的配色方案
    """
    
    # 默认主题配色
    DEFAULT = {
        'primary': '#4772c3',      # 主色
        'primary_light': '#5c8ad4', # 主色亮
        'primary_dark': '#3c61a5',  # 主色暗
        'secondary': '#A8D4FF',    # 次要色
        'background': '#ffffff',   # 背景色
        'text': '#4772c3',        # 文本色
        'unselected_text': '#8ba6db',   # 未选中状态文本色（比主文本浅）
        'disabled': '#cccccc',     # 禁用色
        'disabled_text': '#666666', # 禁用文本色
        'disabled_border': '#999999', # 禁用边框色
        'border': '#4772c3',       # 边框色
        'selection': '#e6f3ff',    # 选中色
        'table_header_bg': '#e8e8e8', # 表格头部背景色
    }
    
    # 暗黑主题配色
    DARK = {
        'primary': '#2c3e50',
        'primary_light': '#34495e',
        'primary_dark': '#2c3e50',
        'secondary': '#7f8c8d',
        'background': '#2c3e50',
        'text': '#ecf0f1',
        'unselected_text': '#bdc3c7',   # 未选中状态文本色（比主文本浅）
        'disabled': '#95a5a6',
        'disabled_text': '#7f8c8d',
        'disabled_border': '#95a5a6',
        'border': '#34495e',
        'selection': '#34495e',
        'table_header_bg': '#1a252f',
    }
    
    # 赛博朋克主题配色
    CYBERPUNK = {
        'primary': '#1B2B2F',
        'primary_light': '#263B40',
        'primary_dark': '#152226',
        'secondary': '#FFD700',
        'background': '#0A1518',
        'text': '#E6B800',
        'unselected_text': '#FFE44D',   # 未选中状态文本色（比主文本浅）
        'disabled': '#3A4F54',
        'disabled_text': '#5C7378',
        'disabled_border': '#2D3F43',
        'border': '#FFD700',
        'selection': '#1F3337',
        'table_header_bg': '#152226',
    }
    
    # 晴空主题配色
    SKYBLUE = {
        'primary': '#87ceeb',
        'primary_light': '#b0e2ff',
        'primary_dark': '#4682b4',
        'secondary': '#b0c4de',
        'background': '#f0f8ff',
        'text': '#4682b4',
        'unselected_text': '#87ceeb',   # 未选中状态文本色（比主文本浅）
        'disabled': '#d3d3d3',
        'disabled_text': '#a9a9a9',
        'disabled_border': '#d3d3d3',
        'border': '#87ceeb',
        'selection': '#e6f3ff',
        'table_header_bg': '#e6f3ff',
    }

    # 森林主题配色
    FOREST = {
        'primary': '#2e8b57',
        'primary_light': '#3cb371',
        'primary_dark': '#006400',
        'secondary': '#98fb98',
        'background': '#f5fffa',
        'text': '#2e8b57',
        'unselected_text': '#85b59b',   # 调整为更暗淡的绿色，降低饱和度
        'disabled': '#c1cdc1',
        'disabled_text': '#838b83',
        'disabled_border': '#c1cdc1',
        'border': '#2e8b57',
        'selection': '#e0eee0',
        'table_header_bg': '#e0eee0',
    }

    # 日落主题配色
    SUNSET = {
        'primary': '#ff7f50',
        'primary_light': '#ffa07a',
        'primary_dark': '#ff4500',
        'secondary': '#ffdab9',
        'background': '#fff5ee',
        'text': '#ff7f50',
        'unselected_text': '#ffa07a',   # 未选中状态文本色（比主文本浅）
        'disabled': '#cdc5bf',
        'disabled_text': '#8b8682',
        'disabled_border': '#cdc5bf',
        'border': '#ff7f50',
        'selection': '#eee9e9',
        'table_header_bg': '#ffeee6',
    }


class StyleSheets:
    """UI样式管理类
    
    负责提供统一的UI样式定义，确保界面风格的一致性。
    包括主题管理、颜色、字体、边框、间距等样式属性。
    """
    
    _current_theme = Theme.DEFAULT
    _theme_colors = ThemeColors.DEFAULT
    
    # 主题到配色方案的映射字典
    _theme_map = {
        Theme.DEFAULT: ThemeColors.DEFAULT,
        Theme.DARK: ThemeColors.DARK,
        Theme.CYBERPUNK: ThemeColors.CYBERPUNK,
        Theme.SKYBLUE: ThemeColors.SKYBLUE,
        Theme.FOREST: ThemeColors.FOREST,
        Theme.SUNSET: ThemeColors.SUNSET
    }
    
    @classmethod
    def set_theme(cls, theme: Theme) -> None:
        """设置当前主题
        
        Args:
            theme: 要设置的主题
        """
        cls._current_theme = theme
        cls._theme_colors = cls._theme_map.get(theme, ThemeColors.DEFAULT)  # 如果找不到对应主题，使用默认主题
    
    @classmethod
    def get_current_theme(cls) -> Theme:
        """获取当前主题
        
        Returns:
            Theme: 当前主题
        """
        return cls._current_theme
    
    @classmethod
    def get_theme_colors(cls) -> Dict[str, str]:
        """获取当前主题的配色方案
        
        Returns:
            Dict[str, str]: 当前主题的配色方案
        """
        return cls._theme_colors
    
    @classmethod
    def get_styles(cls) -> Dict[str, str]:
        """获取所有样式定义
        
        Returns:
            Dict[str, str]: 样式定义字典，键为样式名称，值为样式表字符串
        """
        colors = cls._theme_colors
        return {
            'main_window': f"""
                QMainWindow {{
                    background-color: {colors['primary']};
                    border: 3px;
                }}
                QWidget#centralWidget {{
                    border-radius: 3px;
                    background-color: {colors['primary']};
                }}
                * {{
                    font-family: "Microsoft YaHei";
                    font-size: 16px;
                }}
            """,
            
            'container': f"""
                QWidget {{
                    background-color: {colors['background']};
                    border-radius: 3px;
                }}
            """,
            
            'plot_frame': f"""
                QFrame {{
                    border: 1px solid {colors['border']};
                    background-color: {colors['background']};
                }}
            """,
            
            'title_label': f"""
                QLabel {{
                    color: {colors['text']};
                    font-size: 18px;
                    padding: 0;
                    font-weight: bold;
                }}
            """,
            
            'label': f"""
                QLabel {{
                    font-size: 16px;
                    color: {colors['text']};
                    margin: 0;
                }}
            """,

            'figure_label': f"""
                QLabel {{
                    font-size: 16px;
                    color: {colors['text']};
                    margin: 0;
                    padding: 2px;
                    qproperty-alignment: AlignCenter;
                }}
            """,

            'switch_label': f"""
                QLabel {{
                    font-size: 16px;
                    color: {colors['unselected_text']};
                    margin: 0;
                }}
            """,
            
            'line_edit': f"""
                QLineEdit {{
                    border: 1px solid {colors['border']};
                    border-radius: 3px;
                    padding: 2px;
                    background-color: {colors['background']};
                    color: {colors['text']};
                    min-height: 25px;
                    max-height: 25px;
                    margin: 0;
                }}
                QLineEdit:hover {{
                    border: 2px solid {colors['secondary']};
                    border-radius: 3px;
                    box-shadow: 0 0 3px {colors['secondary']};
                }}
                QLineEdit:focus {{
                    border: 2px solid {colors['primary']};
                    border-radius: 3px;
                }}
            """,
            
            'button': f"""
                QPushButton {{
                    background-color: {colors['primary']};
                    color: {colors['background']};
                    border: 1px solid {colors['background']};
                    padding: 2px;
                    border-radius: 3px;
                    min-width: 60px;
                    max-width: 60px;
                    min-height: 27px;
                    max-height: 27px;
                }}
                QPushButton:hover {{
                    background-color: {colors['primary_light']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['primary_dark']};
                }}
                QPushButton:disabled {{
                    background-color: {colors['disabled']};
                    color: {colors['disabled_text']};
                    border: 1px solid {colors['disabled_border']};
                }}
            """,

            'large_button': f"""
                QPushButton {{
                    background-color: {colors['primary']};
                    color: {colors['background']};
                    border: 1px solid {colors['background']};
                    padding: 2px;
                    border-radius: 3px;
                    min-width: 120px;
                    max-width: 120px;
                    min-height: 27px;
                    max-height: 27px;
                }}
                QPushButton:hover {{
                    background-color: {colors['primary_light']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['primary_dark']};
                }}
                QPushButton:disabled {{
                    background-color: {colors['disabled']};
                    color: {colors['disabled_text']};
                    border: 1px solid {colors['disabled_border']};
                }}
            """,
            
            'group_box': f"""
                QGroupBox {{
                    border: 1px solid {colors['secondary']};
                    border-radius: 3px;
                    margin-top: 19px;
                }}
                QGroupBox::title {{
                    color: {colors['text']}; 
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 0px;
                    top: -3px;
                    padding: 0;
                }}
            """,
            
            'progress_bar': f"""
                QProgressBar {{
                    border: 1px solid {colors['border']};
                    border-radius: 3px;
                    background-color: {colors['background']};
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: {colors['primary']};
                }}
            """,
            
            'radio_button': f"""
                QRadioButton {{
                    spacing: 5px;
                    color: {colors['text']};
                    font-size: 16px;
                }}
                QRadioButton::indicator {{
                    width: 15px;
                    height: 15px;
                }}
            """,
            
            'table': f"""
                QTableWidget {{
                    border: 1px solid {colors['border']};
                    border-left: 2px solid {colors['border']};
                    gridline-color: {colors['border']};
                    border-radius: 3px;
                }}
                QTableWidget::item {{
                    padding: 1px;
                    color: {colors['text']};
                    font-size: 16px;
                    font-weight: bold;
                }}
                QTableWidget::item:selected {{
                    background-color: {colors['selection']};
                }}
                QHeaderView::section {{
                    background-color: {colors['primary']};
                    color: {colors['background']};
                    padding: 5px;
                    border: none;
                    font-weight: bold;
                }}
                QTableCornerButton::section {{
                    background-color: {colors['primary']};
                    border: none;
                    border-top-right-radius: 3px;
                }}
                QTableWidget QScrollBar:vertical {{
                    border-top-right-radius: 3px;
                    border-bottom-right-radius: 3px;
                }}
            """,
            
            'checkbox': f"""
                QCheckBox {{
                    spacing: 5px;
                    color: {colors['text']};
                    font-size: 16px;
                }}
            """
        }
    
    @staticmethod
    def get_dimensions() -> Dict[str, int]:
        """获取固定尺寸定义
        
        Returns:
            Dict[str, int]: 尺寸定义字典，键为尺寸名称，值为像素值
        """
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
            'progress_height': 15,
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
