"""DDD架构初始化器

负责初始化和配置完整的DDD架构组件，包括依赖注入和组件连接。
"""

import logging
from typing import Dict, Any, Optional

from radar_system.infrastructure.clustering.cf_clustering_service import CFClusteringService
from radar_system.infrastructure.clustering.pw_clustering_service import PWClusteringService
from radar_system.infrastructure.ml.neural_network_service import NeuralNetworkService
from radar_system.infrastructure.analysis.parameter_extraction_service import ParameterExtractionService
from radar_system.infrastructure.persistence.session_manager import SessionManager

from radar_system.domain.signal.signal_service import SignalService
from radar_system.domain.recognition.recognition_service import RecognitionService

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
            
            # 初始化聚类服务
            cf_clustering_service = CFClusteringService()
            pw_clustering_service = PWClusteringService()
            
            # 初始化机器学习服务
            neural_network_service = NeuralNetworkService()
            
            # 初始化参数提取服务
            parameter_extraction_service = ParameterExtractionService()
            
            # 初始化会话管理器
            session_manager = SessionManager()
            
            # 存储服务实例
            self._infrastructure_services = {
                'cf_clustering_service': cf_clustering_service,
                'pw_clustering_service': pw_clustering_service,
                'neural_network_service': neural_network_service,
                'parameter_extraction_service': parameter_extraction_service,
                'session_manager': session_manager
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
            
            # 初始化信号服务
            signal_service = SignalService(
                session_manager=self._infrastructure_services['session_manager']
            )
            
            # 初始化识别服务
            recognition_service = RecognitionService(
                cf_clustering_service=self._infrastructure_services['cf_clustering_service'],
                pw_clustering_service=self._infrastructure_services['pw_clustering_service'],
                neural_network_service=self._infrastructure_services['neural_network_service'],
                parameter_extraction_service=self._infrastructure_services['parameter_extraction_service']
            )
            
            # 存储服务实例
            self._domain_services = {
                'signal_service': signal_service,
                'recognition_service': recognition_service
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
            if not self._domain_services:
                raise RuntimeError("领域层未初始化，请先调用 initialize_domain_layer()")
            
            # 初始化识别应用服务
            recognition_app_service = RecognitionApplicationService()
            
            # 设置领域服务依赖
            recognition_app_service.set_domain_services(
                clustering_service=self._domain_services['recognition_service'],
                recognition_service=self._domain_services['recognition_service'],
                parameter_extraction_service=self._infrastructure_services['parameter_extraction_service'],
                session_service=self._domain_services['signal_service']
            )
            
            # 存储服务实例
            self._application_services = {
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
                clustering_service=self._domain_services['recognition_service'],
                recognition_service=self._domain_services['recognition_service'],
                parameter_extraction_service=self._infrastructure_services['parameter_extraction_service'],
                session_service=self._domain_services['signal_service']
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
