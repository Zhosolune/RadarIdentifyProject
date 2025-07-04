"""DDD架构初始化器

负责初始化和配置完整的DDD架构组件，包括依赖注入和组件连接。
"""

import logging
from typing import Dict, Any, Optional

# 基础设施层组件
from radar_system.infrastructure.ml import NeuralNetworkPredictor
from radar_system.infrastructure.analysis import ParameterExtractor

# 应用层服务
from radar_system.application.services.signal_service import SignalService

# 领域层服务
from radar_system.domain.recognition.services.clustering_service import ClusteringService
from radar_system.domain.recognition.services.recognition_service import RecognitionService
from radar_system.domain.recognition.services.parameter_extraction_service import ParameterExtractionService
from radar_system.domain.recognition.services.recognition_session_service import RecognitionSessionService

from radar_system.application.services.recognition_application_service import RecognitionApplicationService

from radar_system.interface.handlers.recognition_handler import RecognitionHandler


# 创建初始化器日志记录器
init_logger = logging.getLogger('system.initializer')


class DDDInitializer:
    """DDD架构初始化器
    
    负责按照正确的依赖顺序初始化所有DDD层次的组件：
    1. 基础设施层服务
    2. 领域层服务
    3. 应用层服务
    4. 接口层处理器
    """
    
    def __init__(self):
        """初始化DDD架构初始化器"""
        self._infrastructure_services: Dict[str, Any] = {}
        self._domain_services: Dict[str, Any] = {}
        self._application_services: Dict[str, Any] = {}
        self._interface_handlers: Dict[str, Any] = {}
        
        init_logger.info("DDD架构初始化器创建完成")
    
    def initialize_infrastructure_layer(self) -> Dict[str, Any]:
        """初始化基础设施层

        Returns:
            基础设施层服务字典
        """
        try:
            init_logger.info("开始初始化基础设施层...")

            # 导入基础设施组件
            from radar_system.infrastructure.persistence.excel.reader import ExcelReader
            from radar_system.domain.signal.services.processor import SignalProcessor
            from radar_system.domain.signal.services.plotter import SignalPlotter
            from radar_system.infrastructure.persistence.file.file_storage import FileStorage

            # 初始化基础设施组件
            excel_reader = ExcelReader()
            signal_processor = SignalProcessor()
            signal_plotter = SignalPlotter()
            file_storage = FileStorage()
            neural_network_predictor = NeuralNetworkPredictor(models_dir="models")
            parameter_extractor = ParameterExtractor()

            # 存储服务实例
            self._infrastructure_services = {
                'excel_reader': excel_reader,
                'signal_processor': signal_processor,
                'signal_plotter': signal_plotter,
                'file_storage': file_storage,
                'neural_network_predictor': neural_network_predictor,
                'parameter_extractor': parameter_extractor
            }

            init_logger.info("基础设施层初始化完成")
            return self._infrastructure_services

        except Exception as e:
            init_logger.error(f"基础设施层初始化失败: {str(e)}")
            raise
    
    def initialize_domain_layer(self) -> Dict[str, Any]:
        """初始化领域层

        Returns:
            领域层服务字典
        """
        try:
            init_logger.info("开始初始化领域层...")

            # 获取基础设施服务
            if not self._infrastructure_services:
                raise RuntimeError("基础设施层未初始化，请先调用 initialize_infrastructure_layer()")

            # 初始化聚类服务
            from radar_system.domain.recognition.entities import ClusteringParams
            clustering_params = ClusteringParams(
                epsilon_cf=2.0,
                epsilon_pw=0.2,
                min_pts=3
            )
            clustering_service = ClusteringService(clustering_params=clustering_params)

            # 初始化识别服务（需要模型和输出目录）
            from radar_system.domain.recognition.entities import RecognitionParams
            recognition_params = RecognitionParams(clustering_params=clustering_params)
            recognition_service = RecognitionService(
                models_dir="models",  # 可以从配置中获取
                output_dir="result",   # 可以从配置中获取
                recognition_params=recognition_params
            )

            # 初始化参数提取服务
            parameter_extraction_service = ParameterExtractionService(
                recognition_params=recognition_params
            )

            # 初始化会话服务
            recognition_session_service = RecognitionSessionService()

            # 存储服务实例
            self._domain_services = {
                'clustering_service': clustering_service,
                'recognition_service': recognition_service,
                'parameter_extraction_service': parameter_extraction_service,
                'recognition_session_service': recognition_session_service
            }

            init_logger.info("领域层初始化完成")
            return self._domain_services

        except Exception as e:
            init_logger.error(f"领域层初始化失败: {str(e)}")
            raise
    
    def initialize_application_layer(self) -> Dict[str, Any]:
        """初始化应用层

        Returns:
            应用层服务字典
        """
        try:
            init_logger.info("开始初始化应用层...")

            # 检查依赖
            if not self._domain_services or not self._infrastructure_services:
                raise RuntimeError("基础设施层和领域层未初始化，请先调用相应的初始化方法")

            # 初始化信号服务（应用层）
            signal_service = SignalService(
                processor=self._infrastructure_services['signal_processor'],
                excel_reader=self._infrastructure_services['excel_reader'],
                plotter=self._infrastructure_services['signal_plotter'],
                file_storage=self._infrastructure_services['file_storage']
            )

            # 初始化识别应用服务
            recognition_app_service = RecognitionApplicationService()

            # 设置领域服务依赖
            recognition_app_service.set_domain_services(
                clustering_service=self._domain_services['clustering_service'],
                recognition_service=self._domain_services['recognition_service'],
                parameter_extraction_service=self._domain_services['parameter_extraction_service'],
                session_service=self._domain_services['recognition_session_service']
            )

            # 存储服务实例
            self._application_services = {
                'signal_service': signal_service,
                'recognition_application_service': recognition_app_service
            }

            init_logger.info("应用层初始化完成")
            return self._application_services

        except Exception as e:
            init_logger.error(f"应用层初始化失败: {str(e)}")
            raise
    
    def initialize_interface_layer(self) -> Dict[str, Any]:
        """初始化接口层

        Returns:
            接口层处理器字典
        """
        try:
            init_logger.info("开始初始化接口层...")

            # 检查依赖
            if not self._application_services:
                raise RuntimeError("应用层未初始化，请先调用 initialize_application_layer()")

            # 初始化识别处理器
            recognition_handler = RecognitionHandler()

            # 设置领域服务依赖（通过应用层）
            recognition_handler.set_domain_services(
                clustering_service=self._domain_services['clustering_service'],
                recognition_service=self._domain_services['recognition_service'],
                parameter_extraction_service=self._domain_services['parameter_extraction_service'],
                session_service=self._domain_services['recognition_session_service']
            )

            # 存储处理器实例
            self._interface_handlers = {
                'recognition_handler': recognition_handler
            }

            init_logger.info("接口层初始化完成")
            return self._interface_handlers

        except Exception as e:
            init_logger.error(f"接口层初始化失败: {str(e)}")
            raise
    
    def initialize_all_layers(self) -> Dict[str, Dict[str, Any]]:
        """初始化所有DDD层次
        
        Returns:
            包含所有层次组件的字典
        """
        try:
            init_logger.info("开始初始化完整的DDD架构...")
            
            # 按依赖顺序初始化各层
            infrastructure = self.initialize_infrastructure_layer()
            domain = self.initialize_domain_layer()
            application = self.initialize_application_layer()
            interface = self.initialize_interface_layer()
            
            result = {
                'infrastructure': infrastructure,
                'domain': domain,
                'application': application,
                'interface': interface
            }
            
            init_logger.info("完整的DDD架构初始化完成")
            return result
            
        except Exception as e:
            init_logger.error(f"DDD架构初始化失败: {str(e)}")
            raise
    
    def get_recognition_handler(self) -> Optional[RecognitionHandler]:
        """获取识别处理器实例

        Returns:
            识别处理器实例，如果未初始化返回None
        """
        return self._interface_handlers.get('recognition_handler')

    def get_application_service(self) -> Optional[RecognitionApplicationService]:
        """获取识别应用服务实例

        Returns:
            识别应用服务实例，如果未初始化返回None
        """
        return self._application_services.get('recognition_application_service')

    def get_signal_service(self) -> Optional[SignalService]:
        """获取信号服务实例

        Returns:
            信号服务实例，如果未初始化返回None
        """
        return self._application_services.get('signal_service')
    
    def shutdown(self):
        """关闭所有组件，清理资源"""
        try:
            init_logger.info("开始关闭DDD架构组件...")
            
            # 关闭接口层
            for handler in self._interface_handlers.values():
                if hasattr(handler, 'shutdown'):
                    handler.shutdown()
            
            # 关闭应用层
            for service in self._application_services.values():
                if hasattr(service, 'shutdown'):
                    service.shutdown()
            
            # 关闭基础设施层
            for service in self._infrastructure_services.values():
                if hasattr(service, 'shutdown'):
                    service.shutdown()
            
            init_logger.info("DDD架构组件关闭完成")
            
        except Exception as e:
            init_logger.error(f"关闭DDD架构组件时发生错误: {str(e)}")
