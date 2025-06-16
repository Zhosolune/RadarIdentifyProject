from typing import Tuple
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from cores.data_processor import DataProcessor
from cores.cluster_processor import ClusterProcessor
from pathlib import Path
import os
from cores.model_predictor import ModelPredictor
from cores.log_manager import LogManager
from cores.params_extractor import ParamsExtractor
import numpy as np
import pandas as pd
from cores.ThreadWorker import DataWorker, IdentifyWorker, SliceWorker, FullSpeedWorker

# 设置环境变量
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 设置日志级别

# # 过滤警告信息
# warnings.filterwarnings('ignore', category=UserWarning)
class DataController(QObject):
    """数据控制器
    
    负责管理雷达信号数据的加载、处理、聚类和识别流程，并与UI层交互。
    
    """

    PA_LABEL_NAMES = {
        0: "完整包络",
        1: "残缺包络",
        2: "部分包络",
        3: "相扫",
        4: "旁瓣",
        5: "非雷达信号"
    }
    DTOA_LABEL_NAMES = {
        0: "常规",
        1: "脉间参差",
        2: "脉组参差",
        3: "脉间脉组参差",
        4: "非雷达信号"
    }
    # DTOA_LABEL_NAMES = {
    #     0: "常规_短",
    #     1: "常规_长",
    #     2: "脉间参差",
    #     3: "脉组参差_短",
    #     4: "脉组参差_长",
    #     5: "脉间脉组参差",
    #     6: "非雷达信号"
    # }
    # DTOA_LABEL_NAMES = {
    #     0: "常规",
    #     1: "脉间参差",
    #     2: "脉组参差_短",
    #     3: "脉组参差_长",
    #     4: "脉间脉组参差",
    #     5: "非雷达信号"
    # }

    # 更新切片信息
    slice_info_updated1 = pyqtSignal(str)
    slice_info_updated2 = pyqtSignal(str)
    process_status = pyqtSignal(bool, str)

    process_started = pyqtSignal()  # 新增：处理开始信号
    process_finished = pyqtSignal()  # 新增：处理结束信号


    cluster_result_ready = pyqtSignal(str, str, str, dict)  # 维度名称, 类别序号, 聚类数据字典

    # 添加新的信号
    slice_images_ready = pyqtSignal(dict)  # 发送切片图像路径
    data_ready = pyqtSignal(bool)  # 添加新信号
    identify_ready = pyqtSignal(bool, int)  # 成功状态, 有效类别数量
    table_data_ready = pyqtSignal(dict)  # 添加新信号用于更新表格数据
    slice_finished = pyqtSignal(bool)  # 切片完成信号

    # 全速处理专用信号
    process_started_fs = pyqtSignal()  # 全速处理开始信号
    process_finished_fs = pyqtSignal(bool)  # 全速处理完成信号
    progress_updated_fs = pyqtSignal(int)  # 全速处理进度更新信号
    start_save_fs = pyqtSignal()  # 全速处理开始保存信号
    slice_finished_fs = pyqtSignal(bool, int)  # 全速处理切片完成信号
    def __init__(self):
        """初始化数据控制器
        
        - 初始化所有处理器实例（数据、聚类、预测、绘图）
        - 设置必要的目录结构
        - 加载深度学习模型
        - 初始化处理参数和状态变量
        """
        super().__init__()
        self.sliced_data = None
        self.current_slice_idx = 0
        self.logger = LogManager()
        self.settings = QSettings('Company', 'App')
        self.last_file_path = None  # 添加属性记录本次会话最后使用的路径
        self.last_save_path = None  # 添加属性记录本次会话最后使用的保存路径

        # 设置必要的目录
        self.results_dir = Path("results/figures")
        self.temp_dir = Path("temp")
        self.save_dir = None
        self._ensure_directories()

        # 初始化处理器和绘图器
        self.processor = DataProcessor()
        self.plotter = self.processor.plotter
        self.predictor = ModelPredictor()
        self.cluster_processor = ClusterProcessor()
        self.logger = LogManager()
        self.params_extractor = ParamsExtractor()
        # 设置绘图器的目录
        self.plotter.set_save_dir(str(self.results_dir))
        self.plotter.set_temp_dir(str(self.temp_dir))

        # 初始化数据相关属性
        self._workers = []
        self.worker = None
        self.identify_worker = None

        # 初始化数据相关属性
        self._workers = []  # 添加列表保持worker引用
        self.sliced_data_count_tmp = 0
        self.sliced_data_count = 0

        # 添加参数存储
        self.epsilon_CF = 2.0  # 默认值
        self.epsilon_PW = 0.2  # 默认值
        self.min_pts = 1  # 默认值

        # 添加判别参数
        self.pa_weight = 1.0  # PA判别权重
        self.dtoa_weight = 1.0  # DTOA判别权重
        self.threshold = 0.9  # 联合判别门限

        # 存储当前有效的聚类结果
        self.valid_clusters = []  # 存储通过判别的聚类结果
        # 初始化通过判别的聚类结果与相关信息
        self.final_cluster_results = {
            'slice_idx': 0,
            'clusters': None,
            'cf_dim_count': 0,
            'pw_dim_count': 0,
            'total_cluster_count': 0
        }
        self.current_cluster_idx = -1  # 当前显示的类别索引
        # self.only_show_identify_result = False  # 默认显示所有聚类结果
        self.only_show_identify_result = True  # 默认仅显示识别结果

        # 添加保存状态跟踪
        self.saved_states = {}  # 保存状态哈希映射
        self.current_param_fingerprint = self._generate_param_fingerprint()  # 当前参数指纹
        # 保存全速处理时的切片总数量，用来计算进度
        self.total_slice_count_fs = 0

        # 使用Path处理路径，确保跨平台兼容性
        try:
            # 获取当前文件所在目录
            current_dir = Path(__file__).parent.parent
            # 模型目录路径
            model_dir = current_dir / "model_wm"

            # 确保模型目录存在
            if not model_dir.exists():
                raise FileNotFoundError(f"模型目录不存在: {model_dir}")

            # 构建模型文件路径
            # dtoa_model = str(model_dir / "12.31_resnet_18_DTOA-checkpoint-70-accuracy1.00.hdf5")
            # dtoa_model = str(model_dir / "01.22_SRF_ResNet_DTOA-final-100-accuracy1.00-val_accuracy1.00.keras")
            # dtoa_model = str(model_dir / "03.08_SRF_ResNet_DTOA-final-100-accuracy0.99-val_accuracy0.99.keras")
            dtoa_model = str(model_dir / "03.18_ResNet_DTOA-final-100-accuracy1.00-val_accuracy0.99.keras")
            # pa_model = str(model_dir / "01.13_resnet_18_PA-checkpoint-115-accuracy1.00-val_accuracy1.00.keras")
            pa_model = str(model_dir / "01.16_ResNet_PA-final-150-accuracy1.00-val_accuracy1.00.keras")
            

            # 检查模型文件是否存在
            if not Path(dtoa_model).exists():
                raise FileNotFoundError(f"DTOA模型文件不存在: {dtoa_model}")
            if not Path(pa_model).exists():
                raise FileNotFoundError(f"PA模型文件不存在: {pa_model}")

            # 创建预测器并加载模型
            self.predictor = ModelPredictor()
            self.predictor.load_models(dtoa_model, pa_model)

        except Exception as e:
            print(f"模型加载失败: {str(e)}")

        # 设置临时目录
        self.predictor.set_temp_dir(os.path.join(os.path.dirname(__file__), "temp"))

        self.current_slice_images = {}  # 存储当前切片的图像路径
        self.slice_worker = None

    def _ensure_directories(self):
        """确保必要的目录存在
        
        创建并确保以下目录存在：
        - results: 结果保存目录
        - temp: 临时文件目录
        """
        try:
            # 创建结果目录
            self.results_dir.mkdir(exist_ok=True)
            # 创建临时目录
            self.temp_dir.mkdir(exist_ok=True)
            self.logger.debug("已确保必要目录存在")
        except Exception as e:
            self.logger.error(f"创建目录时出错: {str(e)}")

    def import_data(self, file_path: str) -> Tuple[bool, str]:
        """导入并处理雷达信号数据文件。

        在独立线程中异步加载和处理Excel格式的雷达信号数据文件。

        Args:
            file_path (str): Excel文件路径
            
        Returns:
            tuple: 包含两个元素：
                - bool: 是否成功启动导入处理
                - str: 状态消息或错误描述

        Raises:
            Exception: 创建工作线程失败时抛出
            
        """
        try:
            self.logger.info("开始导入数据...")
            self.process_started.emit()

            # 创建工作线程
            self.worker = DataWorker(file_path)
            self._workers.append(self.worker)  # 保持引用

            # 连接信号
            self.worker.finished.connect(self._on_import_finished)
            self.worker.start()

            return True, "正在导入数据..."

        except Exception as e:
            self.logger.error(f"创建工作线程失败: {str(e)}")
            return False, f"导入失败: {str(e)}"

    def _on_import_finished(self, success: bool, message: str, data_count: int, band: str, data: object) -> None:
        """处理数据导入完成的回调。

        处理DataWorker导入数据完成后的结果，更新数据状态并发送相关信号。

        Args:
            success (bool): 数据导入是否成功
            message (str): 处理结果消息
            data_count (int): 导入的数据点数量
            band (str): 信号频段名称
            data (object): 导入的雷达信号数据

        Raises:
            Exception: 处理回调过程中出错
        """
        try:
            if success and data is not None:
                self.data = data
                # 更新processor的数据
                self.processor.data = data
                
                # 同步plotter配置
                if hasattr(self.processor, 'plotter'):
                    self.plotter = self.processor.plotter
                    # 重新更新配置以确保同步
                    self.plotter.update_configs(data)
                
                self.data_ready.emit(True)
                # 更新切片信息
                self.slice_info_updated1.emit(f"数据包位于{band}，")
                self.slice_info_updated2.emit(f"预计将获得{data_count}个250ms切片")
                self.sliced_data_count_tmp = data_count
            else:
                self.logger.error(f"数据导入失败: {message}")
                self.data_ready.emit(False)
        except Exception as e:
            self.logger.error(f"导入完成处理出错: {str(e)}")
            self.data_ready.emit(False)
        finally:
            # 发送完成信号
            self.process_finished.emit()
            # 清理工作线程
            if self.worker in self._workers:
                self._workers.remove(self.worker)
            self.worker = None

    def start_slicing(self):
        """启动数据切片处理线程。

        重置处理状态并在独立线程中执行数据切片操作。

        Args:
            None

        Returns:
            bool: 切片处理启动是否成功

        Raises:
            Exception: 创建或启动切片线程失败时抛出
        """
        try:
            # 重置所有相关状态
            self.current_slice_idx = -1
            self.valid_clusters = []
            self.final_cluster_results = {
                'slice_idx': 0,
                'clusters': None,
                'cf_dim_count': 0,
                'pw_dim_count': 0,
                'total_cluster_count': 0
            }

            # 确保聚类处理器状态重置
            self.cluster_processor = ClusterProcessor()

            # 创建并启动切片线程
            self.slice_worker = SliceWorker(self)
            self.slice_worker.slice_finished.connect(self._on_slice_finished)
            self.slice_worker.start()
            
            return True

        except Exception as e:
            self.logger.error(f"切片处理出错: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            return False
            
    def _on_slice_finished(self, success: bool) -> None:
        """处理切片完成的回调。

        处理切片操作完成后的结果，发送相关状态信号。

        Args:
            success (bool): 切片处理是否成功

        Returns:
            None
        """
        self.process_finished.emit()  # 发送处理完成信号
        if success:
            self.data_ready.emit(True)  # 通知UI数据已准备就绪
            self.slice_finished.emit(True)  # 发送切片完成信号
        else:
            self.slice_finished.emit(False)

    def process_first_slice(self) -> bool:
        """处理第一个数据切片。

        对第一个数据切片进行处理，包括数据检查、状态重置、图像生成等操作。

        Args:
            None

        Returns:
            bool: 切片处理是否成功

        Raises:
            Exception: 处理切片数据时出错
        """
        try:
            # 1. 数据有效性检查
            if self.sliced_data is None:
                self.logger.error("切片数据为空")
                return False

            # 2. 重置状态
            self.valid_clusters = []
            self.current_cluster_idx = -1

            # 3. 确保聚类处理器状态正确
            if not hasattr(self, 'cluster_processor') or self.cluster_processor is None:
                self.logger.debug("重新初始化聚类处理器")
                self.cluster_processor = ClusterProcessor()

            # 4. 安全获取下一片数据
            if self.current_slice_idx < len(self.sliced_data) - 1:
                self.current_slice_idx += 1
                try:
                    current_slice = self.sliced_data[self.current_slice_idx]

                    # 5. 数据完整性检查
                    if current_slice is None or len(current_slice) == 0:
                        self.logger.error(f"切片 {self.current_slice_idx + 1} 数据无效")
                        return False

                    # 6. 设置数据到聚类处理器
                    self.cluster_processor.set_data(current_slice, self.current_slice_idx)

                    # 在绘制图像之前确保目录设置正确
                    if not hasattr(self.plotter, 'save_dir') or self.plotter.save_dir is None:
                        self.logger.debug("重新设置绘图保存目录")
                        self.plotter.set_save_dir(str(self.results_dir))

                    if not hasattr(self.plotter, 'temp_dir') or self.plotter.temp_dir is None:
                        self.logger.debug("重新设置绘图临时目录")
                        self.plotter.set_temp_dir(str(self.temp_dir))

                    # 生成基础文件名
                    base_name = f"slice_{self.current_slice_idx + 1}"

                    # 7. 绘制切片图像
                    image_paths = self.plotter.plot_slice(current_slice, base_name)
                    if image_paths:
                        # 发送处理开始信号
                        # self.process_started.emit()
                        # 发送图像路径，这会触发UI更新
                        self.slice_images_ready.emit(image_paths)
                        # 发送处理完成信号
                        # self.process_finished.emit()
                    else:
                        self.logger.warning("未能生成切片图像")

                    # 8. 重置识别相关状态
                    self.final_cluster_results = {
                        'slice_idx': self.current_slice_idx,
                        'clusters': None,
                        'cf_dim_count': 0,
                        'pw_dim_count': 0,
                        'total_cluster_count': 0
                    }

                    return True

                except Exception as e:
                    self.logger.error(f"处理切片数据时出错: {str(e)}")
                    return False
            else:
                self.logger.info("已经是最后一片数据")
                return False

        except Exception as e:
            self.logger.error(f"处理下一片数据出错: {str(e)}")
            return False

    def set_save_dir(self, save_dir: str):
        """设置保存目录
        
        Args:
            save_dir (str): 保存目录路径
        """
        self.save_dir = save_dir

    def get_save_dir(self) -> str:
        """获取保存目录
        
        Returns:
            str: 保存目录路径
        """
        return self.save_dir
    
    def get_last_directory(self) -> str:
        """获取上次使用的目录路径
        
        Returns:
            str: 上次使用的目录路径，如果不存在则返回空字符串
        """
        # 从设置中读取上次保存的路径
        last_path = self.settings.value('last_file_path', '')
        if last_path and os.path.exists(os.path.dirname(last_path)):
            return os.path.dirname(last_path)
        return ''
    
    def update_last_file_path(self, file_path: str):
        """更新最后使用的文件路径
        
        Args:
            file_path (str): 新的文件路径
        """
        self.last_file_path = file_path
    
    def save_settings(self):
        """保存应用程序设置
        
        将最后使用的文件路径保存到QSettings中
        """
        if self.last_file_path:
            self.settings.setValue('last_file_path', self.last_file_path)

    def save_directory(self, file_path: str):
        """保存当前访问的目录
        
        Args:
            file_path (str): 当前文件路径
        """
        directory = str(Path(file_path).parent)
        self.settings.setValue('last_directory', directory)

    def validate_file(self, file_path: str) -> bool:
        """验证文件有效性
        
        Args:
            file_path (str): 待验证的文件路径
            
        Returns:
            bool: 文件是否有效
        """
        if not file_path:
            self.process_status.emit(False, "未选择文件")
            return False

        path = Path(file_path)
        if not path.exists():
            self.process_status.emit(False, "文件不存在")
            return False

        if path.suffix.lower() not in ['.xlsx', '.xls']:
            self.process_status.emit(False, "请选择Excel文件")
            return False

        # self.current_file_path = str(path)
        # 保存当前目录
        self.save_directory(file_path)
        return True

    def set_cluster_params(self, epsilon_CF: float, epsilon_PW: float, min_pts: int) -> None:
        """设置聚类参数。

        更新聚类算法的参数设置，并同步更新聚类处理器的参数。

        Args:
            epsilon_CF (float): CF维度的邻域半径
            epsilon_PW (float): PW维度的邻域半径
            min_pts (int): 最小点数

        Returns:
            None
        """
        self.epsilon_CF = epsilon_CF
        self.epsilon_PW = epsilon_PW
        self.min_pts = min_pts
        # 更新聚类处理器的参数
        self.cluster_processor.set_cluster_params(epsilon_CF, epsilon_PW, min_pts)
        # 更新参数指纹
        self.update_param_fingerprint()

    def set_identify_params(self, pa_weight: float, dtoa_weight: float, threshold: float) -> None:
        """设置识别参数

        Args:
            pa_weight (float): PA判别权重
            dtoa_weight (float): DTOA判别权重
            threshold (float): 联合判别门限
        """
        self.pa_weight = pa_weight
        self.dtoa_weight = dtoa_weight
        self.threshold = threshold
        # 更新聚类处理器的参数
        self.cluster_processor.set_identify_params(pa_weight, dtoa_weight, threshold)
        # 更新参数指纹
        self.update_param_fingerprint()

    def set_judgment_params(self, pa_weight: float, dtoa_weight: float, threshold: float) -> None:
        """设置判别参数

        Args:
            pa_weight (float): PA判别权重
            dtoa_weight (float): DTOA判别权重
            threshold (float): 联合判别门限
        """
        self.pa_weight = pa_weight
        self.dtoa_weight = dtoa_weight
        self.threshold = threshold
        # 更新参数指纹
        self.update_param_fingerprint()

    def process_slice_images(self, slice_data: object) -> None:
        """处理切片数据并生成图像。

        根据输入的切片数据生成5维图像，并发送图像路径信号。

        Args:
            slice_data (object): 待处理的切片数据

        Returns:
            None

        Raises:
            Exception: 处理切片图像过程中出错
        """
        try:
            # 确保plotter已设置保存目录
            if not self.plotter.save_dir:
                self.plotter.set_save_dir("results")

            # 生成切片的5维图像
            image_paths = self.plotter.plot_slice(
                slice_data,
                f"slice_{self.current_slice_idx + 1}"
            )

            self.current_slice_images = image_paths
            self.slice_images_ready.emit(image_paths)

        except Exception as e:
            self.logger.error(f"处理切片图像出错: {str(e)}")  # 添加日志

    def show_next_slice(self) -> bool:
        """切换并显示下一个切片数据。

        切换到下一个切片，更新切片索引并处理新切片的图像数据。

        Args:
            None

        Returns:
            bool: 切片切换是否成功

        Raises:
            Exception: 切换切片过程中出错
        """
        try:
            self.logger.info(f"当前为切片{self.current_slice_idx + 1}, 总切片数: {len(self.sliced_data)}")
            if self.current_slice_idx < len(self.sliced_data) - 1:
                self.current_slice_idx += 1
                self.logger.info(f"切换到切片 {self.current_slice_idx + 1}")
                self.process_slice_images(self.sliced_data[self.current_slice_idx])
                return True
            return False
        except Exception as e:
            self.logger.error(f"切换切片出错: {str(e)}")
            return False

    def show_next_cluster(self) -> bool:
        """切换并显示下一个聚类结果。

        切换到下一个有效的聚类结果，更新聚类索引并发送相关信号。

        Args:
            None

        Returns:
            bool: 聚类结果切换是否成功

        Raises:
            Exception: 切换聚类结果过程中出错
        """
        try:
            if self.valid_clusters and self.current_cluster_idx < len(self.valid_clusters) - 1:
                self.current_cluster_idx += 1
                cluster_info = self.valid_clusters[self.current_cluster_idx]

                self.cluster_result_ready.emit(
                    cluster_info['dim_name'],
                    str(cluster_info['cluster_dim_idx']),
                    str(cluster_info['total_cluster_count']),
                    cluster_info
                )

                # 同步参数到表格
                self.sync_params_to_table(cluster_info)
                return True
            return False

        except Exception as e:
            self.logger.error(f"显示下一类出错: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            return False

    def check_next_available(self) -> tuple[bool, bool]:
        """检查是否存在下一个切片和聚类结果。

        检查当前数据中是否还有未处理的切片和聚类结果。

        Args:
            None

        Returns:
            tuple[bool, bool]: 包含两个布尔值的元组
                - 第一个值表示是否有下一个切片
                - 第二个值表示是否有下一个聚类结果
        """
        has_next_slice = self.current_slice_idx < len(self.sliced_data) - 1
        has_next_cluster = (self.valid_clusters and
                            self.current_cluster_idx < len(self.valid_clusters) - 1)
        return has_next_slice, has_next_cluster

    def _extract_cluster_parameters(self, cluster_info: dict) -> None:
        """提取聚类参数并发送更新信号。

        从聚类信息中提取各项参数，包括标签、置信度和信号特征参数，并发送表格更新信号。

        Args:
            cluster_info (dict): 包含预测结果和聚类数据的信息字典

        Returns:
            None

        Raises:
            KeyError: 访问字典中不存在的键时抛出
        """
        
        dtoa = np.diff(cluster_info['cluster_data']['points'][:, 4]) * 1000  # 转换为us
        dtoa = np.append(dtoa, 0)  # 补齐长度
        # 调试用
        # if self.current_slice_idx == 4 and cluster_info['cluster_idx'] == 3:
        #     print(f"DTOA: {dtoa}")

        # 获取分组值
        cf_grouped_values = self.params_extractor.extract_grouped_values(cluster_info['cluster_data']['points'][:, 0], eps=2, min_samples=4, threshold_ratio=0.1)
        pw_grouped_values = self.params_extractor.extract_grouped_values(cluster_info['cluster_data']['points'][:, 1], eps=0.2, min_samples=4, threshold_ratio=0.1)
        pri_grouped_values = self.params_extractor.extract_grouped_values(dtoa, eps=0.2, min_samples=3, threshold_ratio=0.1)
        doa_grouped_values = self.params_extractor.extract_grouped_values(cluster_info['cluster_data']['points'][:, 2], eps=10, min_samples=3, threshold_ratio=0.1)
        # 方位角特殊处理
        if not doa_grouped_values:
            doa_grouped_values = sorted(cluster_info['cluster_data']['points'][:, 2])
            doa_grouped_values = [np.mean(doa_grouped_values[1:-1])]
        # 抑制谐波
        if pri_grouped_values:
            pri_grouped_values = self.params_extractor.filter_related_numbers(pri_grouped_values)
        
        cluster_info['CF'] = cf_grouped_values
        cluster_info['PW'] = pw_grouped_values
        cluster_info['PRI'] = pri_grouped_values
        cluster_info['DOA'] = doa_grouped_values
        

    def sync_params_to_table(self, cluster_info: dict) -> None:
        """同步参数到表格
        
        Args:
            cluster_info (dict): 聚类信息字典
        """
        # 提取已有的参数
        params = {
            'pa_label': self.PA_LABEL_NAMES[cluster_info['prediction']['pa_label']],
            'pa_conf': f"{cluster_info['prediction']['pa_conf']:.4f}",
            'dtoa_label': self.DTOA_LABEL_NAMES[cluster_info['prediction']['dtoa_label']],
            'dtoa_conf': f"{cluster_info['prediction']['dtoa_conf']:.4f}",
            'joint_prob': f"{cluster_info['prediction']['joint_prob']:.4f}",
            'pa_dict': '\n'.join([f'{self.PA_LABEL_NAMES[label]}: {conf:.4f}' for label, conf in cluster_info['prediction']['pa_dict'].items()]),
            'dtoa_dict': '\n'.join([f'{self.DTOA_LABEL_NAMES[label]}: {conf:.4f}' for label, conf in cluster_info['prediction']['dtoa_dict'].items()]),
            'cf': ', '.join([f'{v:.0f}' for v in cluster_info['CF']]),  # 载频，多值用逗号分隔
            'pw': f"{', '.join([f'{v:.1f}' for v in cluster_info['PW']])}",  # 脉宽，多值用逗号分隔
            'pri': f"{', '.join([f'{v:.1f}' for v in cluster_info['PRI']])}",  # PRI，多值用逗号分隔
            'doa': f"{np.mean(cluster_info['DOA']):.0f}",  # DOA取均值
        }

        # 发送表格更新信号
        self.table_data_ready.emit(params)

    def get_current_cluster(self) -> dict | None:
        """获取当前聚类数据。

        返回当前选中的聚类数据，如果没有有效的聚类数据则返回None。

        Args:
            None

        Returns:
            dict | None: 当前聚类数据字典，无有效数据时返回None
        """
        if (self.valid_clusters and
                0 <= self.current_cluster_idx < len(self.valid_clusters)):
            return self.valid_clusters[self.current_cluster_idx]
        return None

    def start_identification(self) -> None:
        """启动信号识别处理线程。

        创建并启动识别工作线程，连接相关信号处理函数。

        Args:
            None

        Returns:
            None

        Raises:
            Exception: 创建或启动识别线程失败时抛出
        """
        try:
            # 创建并启动识别工作线程
            self.identify_worker = IdentifyWorker(self)

            # 连接信号
            self.identify_worker.identify_started.connect(self.process_started.emit)
            self.identify_worker.identify_finished.connect(
                lambda success: self.identify_ready.emit(success, len(self.valid_clusters))
            )

            # 启动线程
            self.identify_worker.start()

        except Exception as e:
            self.logger.error(f"启动识别处理出错: {str(e)}")
            self.process_finished.emit()

    def _on_identification_finished(self, success: bool) -> None:
        """处理识别完成的回调。

        发送识别完成相关信号并清理工作线程。

        Args:
            success (bool): 识别过程是否成功

        Returns:
            None

        Raises:
            Exception: 处理回调过程中出错
        """
        try:
            # 发送识别完成信号
            self.identify_ready.emit(success, len(self.valid_clusters))
            # 发送处理完成信号
            self.process_finished.emit()

            # 清理工作线程
            if self.identify_worker:
                self.identify_worker.deleteLater()
                self.identify_worker = None

        except Exception as e:
            self.logger.error(f"处理识别完成回调时出错: {str(e)}")

    def _process_identify_current_slice(self) -> bool:
        """识别当前切片的聚类结果
        
        对当前切片数据进行两阶段聚类和识别处理。处理顺序根据波段类型决定：
        - X波段：先PW后CF
        - 其他波段：先CF后PW
        
        Returns:
            bool: 识别处理是否成功
            
        Raises:
            Exception: 识别处理过程中出错
        """
        try:
            # 获取当前切片数据
            current_slice = self.sliced_data[self.current_slice_idx]
            
            # 确保配置同步
            # self.plotter.update_configs(current_slice)
            
            # 检测波段类型
            band_type = self.cluster_processor.detect_band(current_slice)
            
            # 确定处理顺序
            # dimensions = ["PW", "CF"] if band_type == "X波段" else ["CF", "PW"]
            dimensions = ["CF", "PW"] if band_type == "X波段" else ["CF", "PW"]
            
            # 重置处理状态
            self.valid_clusters = []
            self.current_cluster_idx = -1
            
            # 设置当前切片数据和时间范围
            self.cluster_processor.set_data([current_slice], self.current_slice_idx)
            self.cluster_processor.set_slice_time_ranges(self.processor.time_ranges)
            
            # 初始化处理数据
            current_data = current_slice
            recycled_data = []
            dim_idx = {'CF': 0, 'PW': 0}
            cluster_count = 0
            
            # 按顺序处理每个维度
            for dimension in dimensions:
                success, cluster_result = self.cluster_processor.process_dimension(dimension, current_data)
                
                if success and cluster_result:
                    # 处理聚类结果
                    for cluster in cluster_result['clusters']:
                        # 确保cluster包含必要的字段
                        cluster_data = {
                            'points': cluster['points'],
                            'time_ranges': self.cluster_processor.time_ranges,
                            'slice_idx': self.current_slice_idx,
                            'dim_name': dimension,
                            'cluster_idx': cluster_count + 1
                        }
                        
                        # 预测
                        success, pa_conf, dtoa_conf, pa_label, dtoa_label, pa_conf_dict, dtoa_conf_dict = self.predictor.predict(cluster_data)
                        
                        if success:
                            # 提取有效雷达标签对应概率
                            pa_conf_tmp = pa_conf if pa_label != 5 else 0.0
                            dtoa_conf_tmp = dtoa_conf if dtoa_label != 4 else 0.0
                            
                            # 计算联合概率
                            joint_prob = (pa_conf_tmp * self.pa_weight + dtoa_conf_tmp * self.dtoa_weight) / (
                                        self.pa_weight + self.dtoa_weight)
                            
                            # 判断是否为有效雷达信号（贪婪策略）
                            is_valid = (pa_label != 5 or dtoa_label != 4)

                            # 雷达有效时，对于脉间参差类别的特殊判别
                            if is_valid and dtoa_label == 1:
                                # 计算dtoa的集中度
                                dtoa = np.diff(cluster['points'][:, 4]) * 1000  # 转换为us
                                
                                # 计算统计指标
                                dtoa_median = np.median(dtoa)
                                dtoa_min = np.min(dtoa)
                                dtoa_max = np.max(dtoa)
                                
                                # 判断条件：
                                # 1. 数据范围不能超过1000us
                                # 2. 大部分数据应该在中位数/均值附近
                                data_range = dtoa_max - dtoa_min
                                is_range_valid = data_range <= 1000  # 范围阈值可调
                                
                                # 计算在中位数一定范围内的数据比例
                                center_range_ratio = 0.35  # 可调35%
                                in_center_count = np.sum(np.abs(dtoa - dtoa_median) <= center_range_ratio * dtoa_median)
                                center_ratio = in_center_count / len(dtoa)
                                is_centered = center_ratio >= 0.7  # 比例阈值可调
                                
                                # 综合判断
                                if not (is_range_valid or is_centered):
                                    is_valid = False

                            # 生成图像
                            image_paths = self.plotter.plot_cluster(cluster, for_predict=False)
                            
                            # 创建聚类信息
                            cluster_info = {
                                'dim_name': dimension,
                                'cluster_dim_idx': dim_idx[dimension] + 1,  # 通过识别的每个维度下的类别索引
                                'cluster_idx': len(self.valid_clusters) + 1,  # 通过识别的聚类索引
                                'total_cluster_count': cluster_count + 1,  # 当前维度聚类结果总数中的索引
                                'cluster_data': cluster,
                                'image_paths': image_paths,
                                'is_valid': is_valid,  # 保存是否为有效雷达信号
                                'prediction': {
                                    'pa_label': pa_label,
                                    'pa_conf': pa_conf,
                                    'dtoa_label': dtoa_label,
                                    'dtoa_conf': dtoa_conf,
                                    'joint_prob': joint_prob,
                                    'pa_dict': pa_conf_dict,
                                    'dtoa_dict': dtoa_conf_dict,
                                }
                            }
                            # 提取并更新参数
                            self._extract_cluster_parameters(cluster_info)

                            cluster_count += 1
                            
                            # 处理无效数据
                            if not is_valid:
                                recycled_data.extend(cluster['points'].tolist())
                                
                            # 保存聚类结果
                            if not self.only_show_identify_result or is_valid:
                                dim_idx[dimension] += 1
                                self.valid_clusters.append(cluster_info)
                    
                    # 更新待处理数据
                    unprocessed_data = cluster_result.get('unprocessed_points', [])
                    if not isinstance(unprocessed_data, list):
                        unprocessed_data = unprocessed_data.tolist()
                    
                    # 合并回收数据和未聚类数据
                    if recycled_data and unprocessed_data:
                        current_data = np.vstack((recycled_data, unprocessed_data))
                    elif recycled_data:
                        current_data = recycled_data
                    else:
                        current_data = unprocessed_data
            
            # 更新最终结果
            self.final_cluster_results.update({
                'slice_idx': self.current_slice_idx + 1,
                'clusters': self.valid_clusters,
                'cf_dim_count': sum(1 for c in self.valid_clusters if c['dim_name'] == 'CF'),
                'pw_dim_count': sum(1 for c in self.valid_clusters if c['dim_name'] == 'PW'),
                'total_cluster_count': len(self.valid_clusters)
            })
            
            # 显示第一个结果
            if self.valid_clusters:
                self.current_cluster_idx = -1
                self.show_next_cluster()
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"识别处理出错: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            return False

    def cleanup(self) -> None:
        """清理所有资源并重置状态。

        停止所有工作线程，清空数据，重置处理器状态，重新设置目录，并发送清空信号。

        Args:
            None

        Returns:
            None

        Raises:
            Exception: 清理资源过程中出错
        """
        try:
            # 停止所有工作线程
            if hasattr(self, '_workers'):
                for worker in self._workers:
                    if worker and worker.isRunning():
                        worker.quit()
                        worker.wait()

            # 清空存储的数据
            self.sliced_data = None
            self.current_slice_idx = -1
            self.valid_clusters = []
            self.current_cluster_idx = -1
            self.final_cluster_results = {
                'slice_idx': 0,
                'clusters': None,
                'cf_dim_count': 0,
                'pw_dim_count': 0,
                'total_cluster_count': 0
            }

            # 重置处理器状态
            if hasattr(self, 'processor'):
                self.processor = DataProcessor()
                self.plotter = self.processor.plotter  # 更新plotter引用
            if hasattr(self, 'cluster_processor'):
                self.cluster_processor = ClusterProcessor()

            # 确保目录存在并重新设置绘图器目录
            self._ensure_directories()
            if hasattr(self, 'plotter'):
                self.plotter.set_save_dir(str(self.results_dir))
                self.plotter.set_temp_dir(str(self.temp_dir))

            # 发送清空信号
            self.slice_info_updated2.emit("预计将获得 0 个250ms切片")
            self.table_data_ready.emit({})

        except Exception as e:
            self.logger.error(f"清理资源时出错: {str(e)}")

    def reset_current_slice(self):
        """重置当前切片的处理结果"""
        try:
            if self.sliced_data is None or self.current_slice_idx < 0:
                self.logger.warning("没有可重置的切片数据")
                return False

            # 获取当前切片数据
            current_slice = self.sliced_data[self.current_slice_idx]

            # 重置聚类相关状态
            self.valid_clusters = []
            self.current_cluster_idx = -1
            self.final_cluster_results = {
                'slice_idx': self.current_slice_idx,
                'clusters': None,
                'cf_dim_count': 0,
                'pw_dim_count': 0,
                'total_cluster_count': 0
            }

            # 重新初始化聚类处理器
            self.cluster_processor = ClusterProcessor()

            # 重新绘制原始切片图像
            base_name = f"slice_{self.current_slice_idx + 1}"
            image_paths = self.plotter.plot_slice(current_slice, base_name)

            if image_paths:
                # 发送图像更新信号
                self.slice_images_ready.emit(image_paths)
                # 更新切片信息
                # total_slices = len(self.sliced_data)
                # self.slice_info_updated.emit(f"当前切片: {self.current_slice_idx + 1}/{total_slices}")
                self.logger.info(f"切片 {self.current_slice_idx + 1} 已重置")
                return True

            return False

        except Exception as e:
            self.logger.error(f"重置当前切片时出错: {str(e)}")
            return False
        
    def set_display_mode(self, only_identified: bool):
        """设置显示模式"""
        self.only_show_identify_result = only_identified
        self.logger.info(f"显示模式已设置为: {'仅展示识别后结果' if only_identified else '展示所有结果'}")

    def redraw_current_slice(self, slice_num: int) -> bool:
        """重绘指定编号的切片并启动识别。

        根据给定的切片编号重新绘制切片图像，重置聚类状态，并启动识别处理。

        Args:
            slice_num (int): 目标切片编号（从1开始）

        Returns:
            bool: 重绘操作是否成功
                - True: 重绘成功并启动识别处理
                - False: 切片编号无效或重绘过程出错

        Raises:
            Exception: 重绘切片过程中出错
        """
        try:
            # 检查切片编号有效性
            if not self.sliced_data or slice_num < 1 or slice_num > len(self.sliced_data):
                self.logger.warning(f"无效的切片编号: {slice_num}")
                return False
            
            # 更新当前切片索引（切片编号从1开始，索引从0开始）
            self.current_slice_idx = slice_num - 1
            
            # 获取当前切片数据
            current_slice = self.sliced_data[self.current_slice_idx]
            
            # 确保使用正确的plotter实例
            if hasattr(self, 'processor'):
                self.plotter = self.processor.plotter
            
            # 重新绘制原始切片图像
            base_name = f"slice_{slice_num}"
            image_paths = self.plotter.plot_slice(current_slice, base_name)
            
            if image_paths:
                # 发送图像更新信号
                self.slice_images_ready.emit(image_paths)
                
                # 重置聚类相关状态
                self.valid_clusters = []
                self.current_cluster_idx = -1
                
                # 创建并启动识别工作线程
                self.identify_worker = IdentifyWorker(self)
                
                # 连接identify_ready信号
                self.identify_worker.identify_started.connect(self.process_started.emit)
                self.identify_worker.identify_finished.connect(
                    lambda success: self.identify_ready.emit(success, len(self.valid_clusters))
                )
                
                self.identify_worker.start()
                
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"重绘当前切片时出错: {str(e)}")
            return False

    def _generate_param_fingerprint(self) -> str:
        """生成当前聚类和识别参数的唯一指纹
        
        将所有参数组合成字符串并计算哈希值，用于唯一标识一组参数设置
        
        Returns:
            str: 参数指纹哈希值
        """
        import hashlib
        
        # 组合参数字符串
        param_string = f"CF{self.epsilon_CF}_PW{self.epsilon_PW}_MP{self.min_pts}_PA{self.pa_weight}_DTOA{self.dtoa_weight}_TH{self.threshold}"
        
        # 计算哈希值
        fingerprint = hashlib.md5(param_string.encode()).hexdigest()[:8]  # 取前8位作为简短指纹
        
        return fingerprint
        
    def is_current_slice_saved(self) -> bool:
        """检查当前切片是否已保存
        
        通过比较当前参数指纹与保存状态中的记录判断。
        
        Returns:
            bool: 当前切片是否已保存
        """
        try:
            # 如果没有切片数据，则返回False
            if not self.sliced_data or self.current_slice_idx >= len(self.sliced_data):
                return False
                
            # 获取当前切片和参数对应的键
            current_key = f"{self.current_slice_idx}_{self.current_param_fingerprint}"
            
            # 检查当前切片是否在保存状态中
            return self.saved_states.get(current_key, False)
        except Exception as e:
            self.logger.error(f"检查当前切片保存状态时出错: {str(e)}")
            return False
            
    def mark_current_slice_saved(self) -> None:
        """将当前切片在当前参数设置下标记为已保存
        
        更新保存状态哈希映射
        """
        # 生成当前切片和参数的唯一键
        key = f"{self.current_slice_idx}_{self.current_param_fingerprint}"
        
        # 更新保存状态
        self.saved_states[key] = True
        
    def update_param_fingerprint(self) -> bool:
        """更新当前参数指纹
        
        检查参数是否改变，如果改变则更新当前参数指纹
        
        Returns:
            bool: 参数是否发生变化
        """
        # 生成新的参数指纹
        new_fingerprint = self._generate_param_fingerprint()
        
        # 检查是否发生变化
        changed = new_fingerprint != self.current_param_fingerprint
        
        # 更新当前参数指纹
        self.current_param_fingerprint = new_fingerprint
        
        return changed

    def save_results(self, save_dir: str, only_valid: bool = False) -> Tuple[bool, str]:
        """保存识别结果到Excel文件
        
        Args:
            save_dir (str): 保存目录路径
            only_valid (bool, optional): 是否只保存有效的雷达信号结果。默认为False。
            
        Returns:
            Tuple[bool, str]: 是否成功，以及相关消息
        """
        try:
            
            self.logger.info(f"开始保存识别结果到目录: {save_dir}")
            
            # 检查是否存在识别结果
            if not hasattr(self, 'valid_clusters') or not self.valid_clusters:
                return False, "没有可保存的识别结果"
                
            # 检查当前切片是否已保存过
            if self.is_current_slice_saved():
                return False, f"切片 {self.current_slice_idx + 1} 在当前参数设置下已经保存过"
            
            # 创建保存目录
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
                
            # 从原始文件路径提取数据包名称
            if self.last_file_path:
                # 提取文件名并去掉扩展名
                data_package_name = os.path.splitext(os.path.basename(self.last_file_path))[0]
                # 包含参数指纹的文件名
                file_name = f"{data_package_name}_{self.current_param_fingerprint}_识别结果.xlsx"
            else:
                # 如果没有原始文件路径，使用默认名称
                file_name = f"识别结果_{self.current_param_fingerprint}.xlsx"
                
            file_path = os.path.join(save_dir, file_name)
            
            # 准备数据
            results_data = []
            
            # 遍历当前切片的识别结果
            current_slice_idx = self.current_slice_idx
            for cluster_idx, cluster_result in enumerate(self.valid_clusters):
                # 如果只保存有效结果，则检查是否为有效雷达信号
                if only_valid:
                    # 直接使用保存在聚类结果中的is_valid标志
                    is_valid = cluster_result.get('is_valid', False)
                    
                    # 如果为无效结果且只保存有效结果，则跳过此条
                    if not is_valid:
                        continue
                
                # 提取需要保存的数据
                dim_name = cluster_result.get('dim_name', '')
                prediction = cluster_result.get('prediction', {})
                
                row_data = {
                    '切片索引': current_slice_idx + 1,
                    '雷达序号': cluster_idx + 1,
                    '聚类ID': cluster_result.get('total_cluster_count', 0),
                    '聚类维度': dim_name,
                    '载频/MHz': f"{', '.join([f'{v:.0f}' for v in cluster_result.get('CF', [])])}",  # 载频，多值用逗号分隔
                    '脉宽/us': f"{', '.join([f'{v:.1f}' for v in cluster_result.get('PW', [])])}",  # 脉宽，多值用逗号分隔
                    'DOA/°': f"{np.mean(cluster_result.get('DOA', [])):.0f}",  # DOA取均值
                    'PRI/us': f"{', '.join([f'{v:.1f}' for v in cluster_result.get('PRI', [])])}",  # PRI，多值用逗号分隔
                    'PA预测结果': self.PA_LABEL_NAMES.get(prediction.get('pa_label', 5), '未知'),
                    'PA预测概率':  f"{'\n'.join(
                        [f'{self.PA_LABEL_NAMES[label]}: {conf:.4f}' 
                         for label, conf in prediction.get('pa_dict', {}).items()])}",
                    'DTOA预测结果': self.DTOA_LABEL_NAMES.get(prediction.get('dtoa_label', 4), '未知'),
                    'DTOA预测概率':  f"{'\n'.join(
                        [f'{self.DTOA_LABEL_NAMES[label]}: {conf:.4f}' 
                         for label, conf in prediction.get('dtoa_dict', {}).items()])}",
                }
                results_data.append(row_data)
            
            # 创建DataFrame并保存
            if results_data:
                df = pd.DataFrame(results_data)
                
                # 准备参数信息表
                params_info = {
                    '参数名': ['epsilon_CF', 'epsilon_PW', 'min_pts', 'pa_weight', 'dtoa_weight', 'threshold'],
                    '参数值': [self.epsilon_CF, self.epsilon_PW, self.min_pts, self.pa_weight, self.dtoa_weight, self.threshold]
                }
                params_df = pd.DataFrame(params_info)
                
                # 检查文件是否已存在
                if os.path.exists(file_path):
                    # 如果存在，读取现有数据
                    try:
                        with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                            df.to_excel(writer, sheet_name='识别结果', index=False, startrow=writer.sheets['识别结果'].max_row, header=False)
                    except Exception as e:
                        self.logger.warning(f"追加到现有文件出错，将创建新文件: {str(e)}")
                        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                            df.to_excel(writer, sheet_name='识别结果', index=False)
                            params_df.to_excel(writer, sheet_name='参数信息', index=False)
                else:
                    # 创建新文件
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='识别结果', index=False)
                        params_df.to_excel(writer, sheet_name='参数信息', index=False)
                
                # 标记当前切片为已保存
                self.mark_current_slice_saved()
                
                self.logger.info(f"识别结果已保存到: {file_path}")
                return True, f"成功保存{len(results_data)}条识别结果"
            else:
                return False, "没有有效的识别结果可保存"
                
        except Exception as e:
            self.logger.error(f"保存识别结果出错: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            return False, f"保存失败: {str(e)}"

    def full_speed_process(self):
        """全速处理方法
        
        开始全速处理流程，包括切片、聚类、识别、结果保存。
        使用线程进行后台处理，以避免阻塞UI。
        
        Returns:
            bool: 是否成功启动全速处理
        """
        # 检查必要条件
        if self.processor is None or self.processor.data is None or len(self.processor.data) == 0:
            self.logger.error("没有导入有效的雷达数据")
            return False
            
        if not hasattr(self, 'save_dir') or self.save_dir is None or self.save_dir == "":
            self.logger.error("未设置保存目录")
            return False

        # 新建全速处理线程
        self.full_speed_worker = FullSpeedWorker(self)

        # 连接信号
        self.full_speed_worker.slice_started.connect(self._on_slice_started_fs)
        self.full_speed_worker.slice_finished.connect(self._on_slice_finished_fs)
        self.full_speed_worker.current_slice_finished.connect(self._on_current_slice_finished_fs)
        self.full_speed_worker.process_finished.connect(self._on_process_finished_fs)
        self.full_speed_worker.start_save.connect(self._on_start_save_fs)
        
        # 启动全速处理线程
        self.full_speed_worker.start()
        
        return True
        

    def _on_slice_started_fs(self):
        """全速处理切片开始信号"""
        self.logger.info("全速处理开始")
        # 向UI发送切片开始信号
        self.process_started_fs.emit()


    def _on_slice_finished_fs(self, success: bool, slice_count: int):
        """全速处理切片完成信号
        
        Args:
            success (bool): 切片处理是否成功
            slice_count (int): 切片数量
        """
        if success:
            self.logger.info(f"全速处理切片完成，共获取{slice_count}个切片")
            # 保存全速处理时的切片总数量，用来计算进度
            self.total_slice_count_fs = slice_count
            # 向UI发送切片完成信号
            self.slice_finished_fs.emit(True, slice_count)
        else:
            self.logger.error("全速处理切片失败")
            # 向UI发送切片失败信号
            self.slice_finished_fs.emit(False, 0)

    def _on_current_slice_finished_fs(self, slice_idx: int):
        """全速处理当前切片完成信号
        
        Args:
            success (bool): 当前切片处理是否成功
            slice_idx (int): 当前切片序号
        """
        # 计算进度百分比
        progress = int((slice_idx + 1) / self.total_slice_count_fs * 100)
        # 更新UI进度条
        self.progress_updated_fs.emit(progress)

    def _on_start_save_fs(self):
        """全速处理开始保存信号"""
        self.logger.info("开始保存识别结果...")
        # 向UI发送开始保存信号
        self.start_save_fs.emit()
        
    def _on_process_finished_fs(self, success: bool):
        """全速处理完成信号
        
        Args:
            success (bool): 全速处理是否成功
        """
        self.logger.info(f"全速处理{'成功' if success else '失败'}")
        # 向UI发送处理完成信号
        self.process_finished_fs.emit(success)
        
        