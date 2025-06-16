from PyQt5.QtCore import QThread, pyqtSignal
from cores.log_manager import LogManager
from cores.data_processor import DataProcessor
from cores.cluster_processor import ClusterProcessor
from cores.model_predictor import ModelPredictor
from typing import Tuple
import pandas as pd
import os

import numpy as np



class DataWorker(QThread):
    """数据加载工作线程。
    
    负责在独立线程中执行Excel文件的加载和数据预处理。
    """
    finished = pyqtSignal(bool, str, int, str, object)

    def __init__(self, file_path: str):
        """初始化数据工作线程。
        
        Args:
            file_path: Excel文件路径
        """
        super().__init__()
        self.file_path = file_path
        self.processor = DataProcessor()
        self.logger = LogManager()

    def run(self):
        """执行数据处理。
        
        加载Excel文件并进行预处理，完成后发送finished信号。
        """
        try:
            self.logger.info("工作线程开始处理数据...")
            success, message, data_count, band = self.processor.load_excel_file(self.file_path)
            self.finished.emit(success, message, data_count, band, self.processor.data)
            self.logger.info("处理数据线程关闭...")
        except Exception as e:
            self.logger.error(f"工作线程处理异常: {str(e)}")
            self.finished.emit(False, f"处理出错: {str(e)}", 0, None)


class IdentifyWorker(QThread):
    """识别处理工作线程。
    
    负责在独立线程中执行雷达信号的识别处理。
    """
    identify_started = pyqtSignal()  # 识别开始信号
    identify_finished = pyqtSignal(bool, int)

    def __init__(self, data_controller):
        """初始化识别工作线程。
        
        Args:
            data_controller: 数据控制器实例
        """
        super().__init__()
        self.data_controller = data_controller
        self.logger = LogManager()

    def run(self):
        """执行识别处理。
        
        对当前切片进行识别处理，完成后发送识别结果信号。
        """
        try:
            # 发送识别开始信号
            self.identify_started.emit()
            self.logger.info("开始识别线程...")

            # 执行识别处理
            success = self.data_controller._process_identify_current_slice()

            # 获取有效类别数量
            cluster_count = len(self.data_controller.valid_clusters) if success else 0

            # 发送识别完成信号
            self.identify_finished.emit(success, cluster_count)
            self.data_controller.process_finished.emit()
            self.logger.info("识别线程关闭...")

        except Exception as e:
            self.logger.error(f"识别处理线程出错: {str(e)}")
            self.identify_finished.emit(False, 0)


class SliceWorker(QThread):
    """切片处理工作线程。
    
    负责在独立线程中执行雷达信号数据的切片处理。
    """
    slice_finished = pyqtSignal(bool)  # 切片完成信号

    def __init__(self, data_controller):
        """初始化切片工作线程。
        
        Args:
            data_controller: 数据控制器实例
        """
        super().__init__()
        self.data_controller = data_controller
        self.logger = LogManager()

    def run(self):
        """执行切片处理。
        
        将雷达信号数据按时间窗口进行切片，并处理第一片数据。
        """
        try:
            self.logger.info("开始切片线程...")
            
            # 开始切片
            self.data_controller.processor.start_slice()
            self.data_controller.sliced_data = self.data_controller.processor.sliced_data
            self.data_controller.sliced_data_count = len(self.data_controller.processor.sliced_data)
            
            # 更新切片信息
            if self.data_controller.sliced_data_count_tmp != self.data_controller.sliced_data_count:
                empty_slice_count = (self.data_controller.sliced_data_count_tmp - 
                                   self.data_controller.sliced_data_count)
                self.data_controller.slice_info_updated2.emit(
                    f"共获得{self.data_controller.sliced_data_count}个250ms切片，以及"
                    f"<span style='color: red;'>{empty_slice_count}</span>个空切片"
                )
            else:
                self.data_controller.slice_info_updated2.emit(
                    f"共获得{self.data_controller.sliced_data_count}个250ms切片"
                )

            success = False
            if self.data_controller.sliced_data and len(self.data_controller.sliced_data) > 0:
                # 处理第一片
                success = self.data_controller.process_first_slice()
                if not success:
                    self.logger.error("处理第一片数据失败")

            self.slice_finished.emit(success)
            self.logger.info("切片线程关闭...")

        except Exception as e:
            self.logger.error(f"切片处理线程出错: {str(e)}")
            self.slice_finished.emit(False)



class FullSpeedWorker(QThread):
    # 信号声明
    slice_started = pyqtSignal()
    slice_finished = pyqtSignal(bool, int)
    current_slice_finished = pyqtSignal(int)
    start_save = pyqtSignal()
    process_finished = pyqtSignal(bool)

    def __init__(self, data_controller):
        super().__init__()
        self.data_controller = data_controller
        self.processor = self.data_controller.processor
        self.cluster_processor = self.data_controller.cluster_processor
        self.logger = LogManager()
        self.predictor = self.data_controller.predictor

        # 获取处理参数
        self.epsilon_CF = self.data_controller.epsilon_CF
        self.epsilon_PW = self.data_controller.epsilon_PW
        self.min_pts = self.data_controller.min_pts
        self.pa_weight = self.data_controller.pa_weight
        self.dtoa_weight = self.data_controller.dtoa_weight
        self.threshold = self.data_controller.threshold

        # 获取标签映射表
        self.PA_LABEL_NAMES = self.data_controller.PA_LABEL_NAMES
        self.DTOA_LABEL_NAMES = self.data_controller.DTOA_LABEL_NAMES

        # 其他必要数据
        self.save_dir = self.data_controller.get_save_dir()  # 使用getter方法获取保存目录
        self.last_file_path = self.data_controller.last_file_path if hasattr(self.data_controller, 'last_file_path') else None
        self.current_param_fingerprint = self.data_controller._generate_param_fingerprint()
        self.only_show_identify_result = self.data_controller.only_show_identify_result

        # 数据初始化
        self.slice_data = []
        self.slice_count = 0
        self.valid_clusters = []
        self.all_pulse_data_by_slice = {}

    def run(self):
        # 切片
        self._on_slice_fs()

        # 聚类、识别、提取参数
        all_valid_clusters = self._on_cluster_identify_fs()

        # 所有切片处理完成后，一次性保存所有结果
        save_success = False
        pulse_save_success = False
        if all_valid_clusters:
            # 发射开始保存信号
            self.start_save.emit()
            self.logger.info("开始保存识别结果...")
            self.valid_clusters = all_valid_clusters
            save_success, _ = self._on_save_result_fs(only_valid=True)
            if self.all_pulse_data_by_slice: # 检查脉冲数据是否存在
                self._on_save_pulse_data_fs() # 保存脉冲数据
            else:
                self.logger.warning("没有脉冲数据可保存，跳过保存脉冲数据步骤。")
        else:
            self.logger.warning("没有有效的聚类结果，跳过保存步骤。")

        # 发送处理完成信号 (根据主要结果保存是否成功)
        self.logger.info("全速处理完成所有切片")
        self.process_finished.emit(save_success) # 以概要结果保存成功与否为准

    def _on_slice_fs(self):
        """执行切片处理。
        
        将雷达信号数据按时间窗口进行切片，并处理第一片数据。
        """
        try:
            self.logger.info("开始切片...")
            self.slice_started.emit()
            
            # 开始切片
            self.processor.start_slice()
            self.slice_data = self.processor.sliced_data
            self.slice_count = len(self.processor.sliced_data)

            # 发送切片完成信号
            if self.slice_data is not None and len(self.slice_data) > 0:
                self.slice_finished.emit(True, self.slice_count)
            else:
                self.slice_finished.emit(False, 0)

            self.logger.info("切片完成...")

        except Exception as e:
            self.logger.error(f"切片处理出错: {str(e)}")


    def _on_cluster_identify_fs(self):
        """执行聚类处理。
        
        对当前切片进行聚类、识别处理。
        """
        try:
            # 用于存储所有切片的有效聚类结果
            all_valid_clusters = []
            self.all_pulse_data_by_slice = {}
            
            # 开始逐片聚类
            for slice_idx in range(len(self.slice_data)):
                # 开始处理第slice_idx+1个切片，向UI发送当前slice_idx，表示已经完成了slice_idx片，以刷新进度条
                self.current_slice_finished.emit(slice_idx)

                try:
                    # 获取当前切片
                    current_slice = self.slice_data[slice_idx]

                    # 数据完整性检查
                    if current_slice is None or len(current_slice) == 0:
                        self.logger.debug(f"切片 {slice_idx + 1} 数据无效")
                        continue
                    
                    # 设置当前切片数据和时间范围
                    self.cluster_processor.set_data(current_slice, slice_idx)
                    self.cluster_processor.set_slice_time_ranges(self.processor.time_ranges)
                    
                    # 初始化处理数据
                    self.valid_clusters = []
                    current_data = current_slice
                    recycled_data = []
                    dim_idx = {'CF': 0, 'PW': 0}
                    cluster_count = 0
                    cluster_count_by_save = 0
                    dimensions = ["CF", "PW"]
                    current_slice_pulse_data_valid = []
                    current_slice_pulse_data_invalid = []
                    current_slice_pulse_data_remaining = []
                    count_valid = 1
                    count_invalid = 1
                    count_remaining = 1
                    
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
                                    'slice_idx': slice_idx,
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
                                    
                                    # 创建聚类信息
                                    cluster_info = {
                                        'dim_name': dimension,
                                        'cluster_dim_idx': dim_idx[dimension] + 1,  # 每个维度下的类别索引
                                        'cluster_idx': len(self.valid_clusters) + 1,  # 通过识别的聚类索引
                                        'total_cluster_count': cluster_count + 1,  # 整体聚类结果中的索引
                                        'cluster_data': cluster,
                                        'is_valid': is_valid,  # 保存是否为有效雷达信号
                                        'prediction': {
                                            'pa_label': pa_label,
                                            'pa_conf': pa_conf,
                                            'dtoa_label': dtoa_label,
                                            'dtoa_conf': dtoa_conf,
                                            'joint_prob': joint_prob,
                                            'pa_dict': pa_conf_dict,
                                            'dtoa_dict': dtoa_conf_dict,
                                        },
                                        'CF': [],
                                        'PW': [],
                                        'PRI': [],
                                        'DOA': [],
                                    }
                                    # 提取并更新参数
                                    self.data_controller._extract_cluster_parameters(cluster_info)

                                    # 微观保存脉冲数据：收集脉冲数据
                                    last_toa = None
                                    cluster_points = cluster['points']
                                    for point in cluster_points:
                                        if last_toa is None:
                                            last_toa = point[4]
                                        pulse_data = {
                                            '类别': 'valid' if is_valid else 'invalid',
                                            '聚类维度': dimension,
                                            '序号': count_valid if is_valid else count_invalid,
                                            '切片内序号': cluster_info['total_cluster_count'],
                                            '载频': point[0],
                                            '脉宽': point[1],
                                            '方位角': point[2],
                                            '幅度': point[3],
                                            '到达时间': point[4],
                                            '到达时间差': (point[4] - last_toa) * 1000
                                        }
                                        last_toa = point[4]
                                        if is_valid:
                                            current_slice_pulse_data_valid.append(pulse_data)
                                        else:
                                            # 仅在PW维度下收集无效脉冲数据，避免重复收集脉冲
                                            if dimension == 'PW':
                                                current_slice_pulse_data_invalid.append(pulse_data)
                                    

                                    # 递增聚类序号
                                    cluster_count += 1

                                    # 宏观保存识别结果：收集所有结果
                                    if is_valid:
                                        cluster_count_by_save += 1
                                        # 将当前切片索引添加到cluster_info
                                        cluster_info['current_slice_idx'] = slice_idx
                                        cluster_info['cluster_idx_per_slice_to_save'] = cluster_count_by_save
                                        all_valid_clusters.append(cluster_info)
                                        count_valid += 1
                                    
                                    # 处理无效数据
                                    if not is_valid:
                                        recycled_data.extend(cluster['points'].tolist())
                                        if dimension == 'PW':
                                            count_invalid += 1
                                        
                                    # 保存聚类结果
                                    if not self.only_show_identify_result or is_valid:
                                        dim_idx[dimension] += 1
                                        self.valid_clusters.append(cluster_info)
                            
                            # 更新待处理数据
                            unprocessed_data = cluster_result.get('unprocessed_points', [])
                            if not isinstance(unprocessed_data, list):
                                unprocessed_data = unprocessed_data.tolist()
                            
                            # 合并回收数据和未聚类数据
                            # 对于CF维度，无效数据和未聚类数据合并，对于PW维度，只保留未聚类数据（因为无效数据已经保存过了）
                            if dimension == 'CF':
                                if recycled_data and unprocessed_data:
                                    current_data = np.vstack((recycled_data, unprocessed_data))
                                elif recycled_data:
                                    current_data = recycled_data
                                else:
                                    current_data = unprocessed_data
                            elif dimension == 'PW':
                                current_data = unprocessed_data

                    # 处理当前切片最终的剩余脉冲
                    last_toa = None
                    if current_data is not None and len(current_data) > 0:
                        # 确保 current_data 是 NumPy 数组
                        if not isinstance(current_data, np.ndarray):
                            try:
                                current_data = np.array(current_data)
                            except ValueError as ve:
                                self.logger.error(f"切片 {slice_idx + 1} 剩余数据无法转换为Numpy数组: {ve}")
                                current_data = None # 标记为无法处理

                        # 检查数据维度是否正确
                        if current_data.ndim == 2 and current_data.shape[1] >= 5:
                            for point in current_data:
                                if last_toa is None:
                                    last_toa = point[4]
                                current_slice_pulse_data_remaining.append({
                                    '类别': 'remaining',
                                    '聚类维度': '——',
                                    '序号': '——',
                                    '切片内序号': '——',
                                    '载频': point[0],
                                    '脉宽': point[1],
                                    '方位角': point[2],
                                    '幅度': point[3],
                                    '到达时间': point[4],
                                    '到达时间差': (point[4] - last_toa) * 1000
                                })
                                last_toa = point[4]
                        elif current_data.ndim == 1 and len(current_data) >= 5: # 单个脉冲数据
                            point = current_data
                            current_slice_pulse_data_remaining.append({
                                '类别': 'remaining',
                                '聚类维度': '——',
                                '序号': '——',
                                '切片内序号': '——',
                                '载频': point[0],
                                '脉宽': point[1],
                                '方位角': point[2],
                                '幅度': point[3],
                                '到达时间': point[4],
                                '到达时间差': 0
                            })
                        else:
                            self.logger.warning(f"切片 {slice_idx + 1} 的剩余脉冲数据格式不正确，无法保存。Shape: {current_data.shape}")

                    # 存储当前切片的脉冲数据
                    if current_slice_pulse_data_valid or current_slice_pulse_data_invalid or current_slice_pulse_data_remaining:
                        self.logger.info(f"切片 {slice_idx + 1} 存在脉冲数据")
                        self.all_pulse_data_by_slice[slice_idx] = current_slice_pulse_data_valid + current_slice_pulse_data_invalid + current_slice_pulse_data_remaining
                    else:
                        self.logger.info(f"切片 {slice_idx + 1} 没有脉冲数据")

                except Exception as e:
                    self.logger.error(f"处理切片数据时出错: {str(e)}")
                    continue
            
            return all_valid_clusters
            # # 所有切片处理完成后，一次性保存所有结果
            # if all_valid_clusters:
            #     self.valid_clusters = all_valid_clusters
            #     self._on_save_result_fs(only_valid=True)
                    
            # # 发送处理完成信号
            # self.logger.info("全速处理完成所有切片")
            # self.process_finished.emit(True)
            
        except Exception as e:
            self.logger.error(f"聚类处理出错: {str(e)}")
            self.process_finished.emit(False)


    def _on_save_result_fs(self, only_valid: bool = False) -> Tuple[bool, str]:
        """保存识别结果到Excel文件
        
        Args:
            only_valid (bool, optional): 是否只保存有效的雷达信号结果。默认为False。
            
        Returns:
            Tuple[bool, str]: 是否成功，以及相关消息
        """
        try:
            self.logger.info(f"开始保存全速处理识别结果到目录: {self.save_dir}")
            
            # 创建保存目录
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir, exist_ok=True)
                
            # 从原始文件路径提取数据包名称
            if self.last_file_path:
                # 提取文件名并去掉扩展名
                data_package_name = os.path.splitext(os.path.basename(self.last_file_path))[0]
                # 包含参数指纹的文件名
                file_name = f"{data_package_name}_{self.current_param_fingerprint}_result.xlsx"
            else:
                # 如果没有原始文件路径，使用默认名称
                file_name = f"result_{self.current_param_fingerprint}.xlsx"
                
            file_path = os.path.join(self.save_dir, file_name)
            
            # 准备数据
            results_data = []
            
            # 遍历所有切片的识别结果
            for cluster_idx, cluster_result in enumerate(self.valid_clusters):
                # 如果只保存有效结果，则检查是否为有效雷达信号
                # if only_valid:
                #     # 直接使用保存在聚类结果中的is_valid标志
                #     is_valid = cluster_result.get('is_valid', False)
                    
                #     # 如果为无效结果且只保存有效结果，则跳过此条
                #     if not is_valid:
                #         continue
                
                # 提取需要保存的数据
                dim_name = cluster_result.get('dim_name', '')
                prediction = cluster_result.get('prediction', {})
                
                row_data = {
                    '切片索引': cluster_result.get('current_slice_idx', 0) + 1,
                    '雷达序号': cluster_result.get('cluster_idx_per_slice_to_save', 0),
                    # '雷达序号': cluster_idx + 1,
                    '聚类ID': cluster_result.get('total_cluster_count', 0),
                    '聚类维度': dim_name,
                    '载频/MHz': f"{', '.join([f'{v:.0f}' for v in cluster_result.get('CF', [])])}",  # 载频，多值用逗号分隔
                    '脉宽/us': f"{', '.join([f'{v:.1f}' for v in cluster_result.get('PW', [])])}",  # 脉宽，多值用逗号分隔
                    'DOA/°': f"{np.mean(cluster_result.get('DOA', [])):.0f}",  # DOA取均值
                    'PRI/us': f"{', '.join([f'{v:.1f}' for v in cluster_result.get('PRI', [])])}",  # PRI，多值用逗号分隔
                    'PA预测结果': self.PA_LABEL_NAMES.get(prediction.get('pa_label', 5), '未知'),
                    'PA预测概率':  f"{'\n'.join([
                        f'{self.PA_LABEL_NAMES[label]}: {conf:.4f}' 
                        for label, conf in prediction.get('pa_dict', {}).items()
                    ])}",
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
                
                # 直接创建或覆盖文件，不使用追加模式
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='识别结果', index=False)
                    params_df.to_excel(writer, sheet_name='参数信息', index=False)
                
                self.logger.info(f"全速处理识别结果已保存到: {file_path}")
                return True, f"成功保存{len(results_data)}条识别结果"
            else:
                return False, "没有有效的识别结果可保存"
                
        except Exception as e:
            self.logger.error(f"保存识别结果出错: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            return False, f"保存失败: {str(e)}"
        
    def _on_save_pulse_data_fs(self):
        """保存每个切片的详细脉冲数据到Excel文件

        Returns:
            Tuple[bool, str]: 是否成功，以及相关消息
        """
        try:
            self.logger.info(f"开始保存全速处理脉冲数据到目录: {self.save_dir}")

            # 创建保存目录
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir, exist_ok=True)

            # 从原始文件路径提取数据包名称
            if self.last_file_path:
                # 提取文件名并去掉扩展名
                data_package_name = os.path.splitext(os.path.basename(self.last_file_path))[0]
                # 包含参数指纹的文件名
                file_name = f"{data_package_name}_{self.current_param_fingerprint}_pulse_data.xlsx"
            else:
                # 如果没有原始文件路径，使用默认名称
                file_name = f"pulse_data_{self.current_param_fingerprint}.xlsx"

            file_path = os.path.join(self.save_dir, file_name)

            # 检查是否有脉冲数据可保存
            if not hasattr(self, 'all_pulse_data_by_slice') or not self.all_pulse_data_by_slice:
                self.logger.warning("没有收集到脉冲数据可供保存。")
                return False, "没有脉冲数据可保存"
            
            # 使用 ExcelWriter 写入多个sheet
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 按照切片索引排序写入
                sorted_slice_indices = sorted(self.all_pulse_data_by_slice.keys())
                for slice_idx in sorted_slice_indices:
                    pulse_data_list = self.all_pulse_data_by_slice[slice_idx]
                    if pulse_data_list: # 确保列表不为空
                        # 创建DataFrame
                        df = pd.DataFrame(pulse_data_list)
                        # 确保列顺序
                        column_order = ['类别', '聚类维度', '序号', '切片内序号', '载频', '脉宽', '方位角', '幅度', '到达时间', '到达时间差']
                        # 检查DataFrame是否包含所有必须列
                        if all(col in df.columns for col in column_order):
                            # 重新排列列顺序
                            df = df[column_order]
                        else:
                            missing_cols = [col for col in column_order if col not in df.columns]
                            self.logger.warning(f"切片 {slice_idx + 1} 的脉冲数据DataFrame缺少列: {missing_cols}")
                        # 写入空列
                        sheet_name = f'Slice_{slice_idx + 1}'
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    else:
                        self.logger.debug(f"切片 {slice_idx + 1} 没有脉冲数据可保存。")

            self.logger.info(f"全速处理脉冲数据已保存到: {file_path}")
            return True, f"成功保存脉冲数据"
        
        except Exception as e:
            self.logger.error(f"保存脉冲数据出错: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            return False, f"保存脉冲数据失败: {str(e)}"
