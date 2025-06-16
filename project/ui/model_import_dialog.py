from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from pathlib import Path
import os
import shutil
from cores.log_manager import LogManager

class ModelImportDialog(QDialog):
    """模型导入对话框
    
    提供PA模型和DTOA模型的导入功能
    """
    
    def __init__(self, parent=None, predictor=None, styles=None):
        """初始化模型导入对话框
        
        Args:
            parent: 父窗口
            predictor: 模型预测器实例
            styles: 样式表字典
        """
        super().__init__(parent)
        self.predictor = predictor
        self.styles = styles if styles else {}
        self.logger = LogManager()
        self.model_paths = {'pa': '', 'dtoa': ''}
        self.last_dir = str(Path.home())
        
        self.setWindowTitle("载入模型")
        self.setMinimumWidth(650)
        self.setMinimumHeight(300)
        if 'dialog' in self.styles:
            self.setStyleSheet(self.styles['dialog'])
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建PA模型模块
        self.pa_group = QGroupBox("PA模型")
        pa_layout = QVBoxLayout(self.pa_group)
        
        # PA模型路径布局
        pa_path_layout = QHBoxLayout()
        self.pa_path_label = QLabel()
        if 'dialog_path_label' in self.styles:
            self.pa_path_label.setStyleSheet(self.styles['dialog_path_label'])
        self.pa_path_label.setMinimumWidth(350)
        self.pa_path_label.setText("未选择文件")
        
        # PA模型按钮布局
        self.pa_browse_btn = QPushButton("浏览")
        # self.pa_browse_btn.setFixedWidth(80)
        self.pa_browse_btn.clicked.connect(self._browse_pa_model)
        
        self.pa_clear_btn = QPushButton("清除")
        # self.pa_clear_btn.setFixedWidth(80)
        self.pa_clear_btn.clicked.connect(self._clear_pa_model)
        
        self.pa_import_btn = QPushButton("导入")
        # self.pa_import_btn.setFixedWidth(80)
        self.pa_import_btn.clicked.connect(self._import_pa_model)
        self.pa_import_btn.setEnabled(False)  # 初始状态禁用
        
        pa_path_layout.addWidget(self.pa_path_label)
        pa_path_layout.addWidget(self.pa_browse_btn)
        pa_path_layout.addWidget(self.pa_clear_btn)
        pa_path_layout.addWidget(self.pa_import_btn)
        pa_layout.addLayout(pa_path_layout)
        
        # 创建DTOA模型模块
        self.dtoa_group = QGroupBox("DTOA模型")
        dtoa_layout = QVBoxLayout(self.dtoa_group)
        
        # DTOA模型路径布局
        dtoa_path_layout = QHBoxLayout()
        self.dtoa_path_label = QLabel()
        if 'dialog_path_label' in self.styles:
            self.dtoa_path_label.setStyleSheet(self.styles['dialog_path_label'])
        self.dtoa_path_label.setMinimumWidth(350)
        self.dtoa_path_label.setText("未选择文件")
        
        # DTOA模型按钮布局
        self.dtoa_browse_btn = QPushButton("浏览")
        self.dtoa_browse_btn.setFixedWidth(80)
        self.dtoa_browse_btn.clicked.connect(self._browse_dtoa_model)
        
        self.dtoa_clear_btn = QPushButton("清除")
        self.dtoa_clear_btn.setFixedWidth(80)
        self.dtoa_clear_btn.clicked.connect(self._clear_dtoa_model)
        
        self.dtoa_import_btn = QPushButton("导入")
        self.dtoa_import_btn.setFixedWidth(80)
        self.dtoa_import_btn.clicked.connect(self._import_dtoa_model)
        self.dtoa_import_btn.setEnabled(False)  # 初始状态禁用
        
        dtoa_path_layout.addWidget(self.dtoa_path_label)
        dtoa_path_layout.addWidget(self.dtoa_browse_btn)
        dtoa_path_layout.addWidget(self.dtoa_clear_btn)
        dtoa_path_layout.addWidget(self.dtoa_import_btn)
        dtoa_layout.addLayout(dtoa_path_layout)
        
        # 添加模块到主布局
        main_layout.addWidget(self.pa_group)
        main_layout.addWidget(self.dtoa_group)
        main_layout.addStretch()
        
        # 底部按钮布局
        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.confirm_btn = QPushButton("确定")
        self.confirm_btn.setFixedWidth(100)
        self.confirm_btn.clicked.connect(self._on_confirm)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.confirm_btn)
        main_layout.addLayout(button_layout)
    
    def _browse_pa_model(self):
        """浏览并选择PA模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PA模型文件",
            self.last_dir,
            "模型文件 (*.hdf5 *.h5 *.keras);;所有文件 (*)"
        )
        if file_path:
            self.pa_path_label.setText(file_path)
            self.model_paths['pa'] = file_path
            self.last_dir = str(Path(file_path).parent)
            self.pa_import_btn.setEnabled(True)  # 启用导入按钮
    
    def _browse_dtoa_model(self):
        """浏览并选择DTOA模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择DTOA模型文件",
            self.last_dir,
            "模型文件 (*.hdf5 *.h5 *.keras);;所有文件 (*)"
        )
        if file_path:
            self.dtoa_path_label.setText(file_path)
            self.model_paths['dtoa'] = file_path
            self.last_dir = str(Path(file_path).parent)
            self.dtoa_import_btn.setEnabled(True)  # 启用导入按钮
    
    def _clear_pa_model(self):
        """清除PA模型路径"""
        self.pa_path_label.setText("未选择文件")
        self.model_paths['pa'] = ''
        self.pa_import_btn.setEnabled(False)  # 禁用导入按钮
    
    def _clear_dtoa_model(self):
        """清除DTOA模型路径"""
        self.dtoa_path_label.setText("未选择文件")
        self.model_paths['dtoa'] = ''
        self.dtoa_import_btn.setEnabled(False)  # 禁用导入按钮
    
    def _import_pa_model(self):
        """导入单个PA模型"""
        try:
            if not self.model_paths['pa']:
                return
                
            model_dir = Path("model_wm")
            if not model_dir.exists():
                os.makedirs(model_dir, exist_ok=True)
                
            # 处理PA模型
            pa_model_path = self.model_paths['pa']
            pa_filename = Path(pa_model_path).name
            pa_target_path = model_dir / pa_filename
            
            # 复制模型文件
            shutil.copy2(pa_model_path, pa_target_path)
            
            # 加载PA模型
            if self.predictor and self.predictor.load_pa_model(str(pa_target_path)):
                QMessageBox.information(self, "模型导入", f"PA模型导入成功: {pa_filename}")
                self.logger.info(f"PA模型导入成功: {pa_filename}")
            else:
                QMessageBox.warning(self, "模型导入", "PA模型导入失败，请检查模型文件格式")
                self.logger.warning("PA模型导入失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"PA模型导入失败: {str(e)}")
            self.logger.error(f"PA模型导入失败: {str(e)}")
    
    def _import_dtoa_model(self):
        """导入单个DTOA模型"""
        try:
            if not self.model_paths['dtoa']:
                return
                
            model_dir = Path("model_wm")
            if not model_dir.exists():
                os.makedirs(model_dir, exist_ok=True)
                
            # 处理DTOA模型
            dtoa_model_path = self.model_paths['dtoa']
            dtoa_filename = Path(dtoa_model_path).name
            dtoa_target_path = model_dir / dtoa_filename
            
            # 复制模型文件
            shutil.copy2(dtoa_model_path, dtoa_target_path)
            
            # 加载DTOA模型
            if self.predictor and self.predictor.load_dtoa_model(str(dtoa_target_path)):
                QMessageBox.information(self, "模型导入", f"DTOA模型导入成功: {dtoa_filename}")
                self.logger.info(f"DTOA模型导入成功: {dtoa_filename}")
            else:
                QMessageBox.warning(self, "模型导入", "DTOA模型导入失败，请检查模型文件格式")
                self.logger.warning("DTOA模型导入失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"DTOA模型导入失败: {str(e)}")
            self.logger.error(f"DTOA模型导入失败: {str(e)}")
    
    def _on_confirm(self):
        """确认按钮点击事件"""
        try:
            has_import = False
            
            # 检查是否有选择模型文件
            if self.model_paths['pa'] or self.model_paths['dtoa']:
                model_dir = Path("model_wm")
                if not model_dir.exists():
                    os.makedirs(model_dir, exist_ok=True)
                
                # 处理PA模型
                has_error = False
                if self.model_paths['pa']:
                    pa_model_path = self.model_paths['pa']
                    pa_filename = Path(pa_model_path).name
                    pa_target_path = model_dir / pa_filename
                    
                    # 复制模型文件
                    shutil.copy2(pa_model_path, pa_target_path)
                    
                    # 加载PA模型
                    if not self.predictor.load_pa_model(str(pa_target_path)):
                        has_error = True
                    else:
                        has_import = True
                
                # 处理DTOA模型
                if self.model_paths['dtoa']:
                    dtoa_model_path = self.model_paths['dtoa']
                    dtoa_filename = Path(dtoa_model_path).name
                    dtoa_target_path = model_dir / dtoa_filename
                    
                    # 复制模型文件
                    shutil.copy2(dtoa_model_path, dtoa_target_path)
                    
                    # 加载DTOA模型
                    if not self.predictor.load_dtoa_model(str(dtoa_target_path)):
                        has_error = True
                    else:
                        has_import = True
                
                # 显示结果消息
                if has_error:
                    QMessageBox.warning(self, "模型导入", "部分模型导入失败，请检查模型文件格式")
                elif has_import:
                    QMessageBox.information(self, "模型导入", "模型导入成功")
                    self.accept()
            else:
                QMessageBox.warning(self, "模型导入", "未选择任何模型文件")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"模型导入失败: {str(e)}")
            self.logger.error(f"模型导入失败: {str(e)}") 