#!/usr/bin/env python3
"""第三阶段领域服务测试脚本

验证新创建的领域服务能够正确工作。
"""

import sys
import os
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有领域服务的导入"""
    print("=== 测试领域服务导入 ===")
    
    try:
        # 测试领域服务导入
        from radar_system.domain.recognition.services import (
            ClusteringService, RecognitionService,
            ParameterExtractionService, RecognitionSessionService
        )
        print("✅ 领域服务导入成功")
        
        # 测试领域实体导入
        from radar_system.domain.recognition.entities import (
            DimensionType, ClusterStatus, ProcessingStage, RecognitionStatus,
            ClusterCandidate, RecognitionResult, RecognitionSession,
            RecognitionParams, ClusteringParams
        )
        print("✅ 领域实体导入成功")
        
        # 测试基础设施组件导入
        from radar_system.infrastructure.clustering import DBSCANClusterer
        from radar_system.infrastructure.visualization import ClusterImageGenerator
        from radar_system.infrastructure.ml import NeuralNetworkPredictor
        from radar_system.infrastructure.analysis import ParameterExtractor
        print("✅ 基础设施组件导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_clustering_service():
    """测试聚类服务"""
    print("\n=== 测试聚类服务 ===")
    
    try:
        from radar_system.domain.recognition.services import ClusteringService
        from radar_system.domain.recognition.entities import ClusteringParams
        from radar_system.domain.signal.entities.signal import TimeRange
        
        # 创建聚类参数
        clustering_params = ClusteringParams(
            epsilon_cf=2.0,
            epsilon_pw=0.2,
            min_pts=3
        )
        
        # 创建聚类服务
        clustering_service = ClusteringService(clustering_params=clustering_params)
        print("✅ 聚类服务创建成功")
        
        # 创建测试数据
        test_data = np.random.rand(50, 5) * 100
        time_range = TimeRange(start_time=0.0, end_time=1.0)
        
        # 测试CF维度聚类
        cf_candidates = clustering_service.cluster_cf_dimension(
            signal_data=test_data,
            slice_index=0,
            time_range=time_range
        )
        print(f"✅ CF维度聚类完成，候选数量: {len(cf_candidates)}")
        
        # 测试PW维度聚类
        pw_candidates = clustering_service.cluster_pw_dimension(
            signal_data=test_data,
            slice_index=0,
            time_range=time_range
        )
        print(f"✅ PW维度聚类完成，候选数量: {len(pw_candidates)}")
        
        # 测试聚类统计
        all_candidates = cf_candidates + pw_candidates
        stats = clustering_service.get_clustering_statistics(all_candidates)
        print(f"✅ 聚类统计完成，总聚类数: {stats['total_clusters']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 聚类服务测试失败: {e}")
        return False

def test_recognition_service():
    """测试识别服务"""
    print("\n=== 测试识别服务 ===")
    
    try:
        from radar_system.domain.recognition.services import RecognitionService
        from radar_system.domain.recognition.entities import (
            ClusterCandidate, DimensionType, ClusterStatus,
            RecognitionParams, ClusteringParams
        )
        from radar_system.domain.signal.entities.signal import TimeRange
        
        # 创建临时目录
        temp_dir = project_root / "temp_test"
        temp_dir.mkdir(exist_ok=True)
        models_dir = project_root / "radar_system" / "infrastructure" / "ml"
        
        # 创建识别参数
        clustering_params = ClusteringParams(
            epsilon_cf=2.0,
            epsilon_pw=0.2,
            min_pts=3
        )
        recognition_params = RecognitionParams(clustering_params=clustering_params)

        # 创建识别服务
        recognition_service = RecognitionService(
            models_dir=str(models_dir),
            output_dir=str(temp_dir / "output"),
            recognition_params=recognition_params
        )
        print("✅ 识别服务创建成功")
        
        # 测试模型信息获取
        model_info = recognition_service.get_model_info()
        print(f"✅ 模型信息获取成功，初始化状态: {model_info['is_initialized']}")
        
        # 创建测试聚类候选
        test_data = np.random.rand(20, 5) * 100
        cluster_candidate = ClusterCandidate(
            cluster_data=test_data,
            dimension_type=DimensionType.CF,
            status=ClusterStatus.VALID,
            slice_index=0,
            cluster_index=1,
            time_range=TimeRange(start_time=0.0, end_time=1.0)
        )
        
        # 注意：这里不执行实际的识别，因为需要真实的模型文件
        print("✅ 识别服务基本功能验证完成（跳过实际识别）")
        
        return True
        
    except Exception as e:
        print(f"❌ 识别服务测试失败: {e}")
        return False

def test_parameter_extraction_service():
    """测试参数提取服务"""
    print("\n=== 测试参数提取服务 ===")
    
    try:
        from radar_system.domain.recognition.services import ParameterExtractionService
        from radar_system.domain.recognition.entities import RecognitionParams, ClusteringParams

        # 创建参数提取服务
        clustering_params = ClusteringParams(
            epsilon_cf=2.0,
            epsilon_pw=0.2,
            min_pts=3
        )
        recognition_params = RecognitionParams(clustering_params=clustering_params)
        extraction_service = ParameterExtractionService(
            recognition_params=recognition_params
        )
        print("✅ 参数提取服务创建成功")
        
        # 测试参数分布分析
        test_parameters = {
            'CF': [1000.0, 1100.0, 1200.0, 1050.0],
            'PW': [10.0, 12.0, 11.0, 13.0],
            'DOA': [45.0, 50.0, 48.0, 52.0],
            'PRI': [100.0, 105.0, 102.0, 108.0]
        }
        
        distribution_stats = extraction_service.analyze_parameter_distribution(test_parameters)
        print(f"✅ 参数分布分析完成，参数类型数: {len(distribution_stats)}")
        
        # 测试参数质量指标
        quality_metrics = extraction_service.get_parameter_quality_metrics(test_parameters)
        print(f"✅ 参数质量指标计算完成，总参数数: {quality_metrics['total_parameters']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 参数提取服务测试失败: {e}")
        return False

def test_recognition_session_service():
    """测试识别会话管理服务"""
    print("\n=== 测试识别会话管理服务 ===")
    
    try:
        from radar_system.domain.recognition.services import RecognitionSessionService
        from radar_system.domain.recognition.entities import (
            ProcessingStage, RecognitionParams, ClusteringParams
        )
        from radar_system.domain.signal.entities.signal import TimeRange
        
        # 创建会话管理服务
        session_service = RecognitionSessionService()
        print("✅ 识别会话管理服务创建成功")
        
        # 创建测试会话
        test_data = np.random.rand(100, 5) * 100
        time_range = TimeRange(start_time=0.0, end_time=2.0)
        
        # 创建参数
        clustering_params = ClusteringParams(
            epsilon_cf=2.0,
            epsilon_pw=0.2,
            min_pts=3
        )
        recognition_params = RecognitionParams(clustering_params=clustering_params)

        session = session_service.create_session(
            signal_data=test_data,
            time_range=time_range,
            recognition_params=recognition_params
        )
        print(f"✅ 识别会话创建成功，session_id: {session.session_id[:8]}...")
        
        # 测试会话状态更新
        success = session_service.update_session_stage(
            session.session_id, 
            ProcessingStage.CF_CLUSTERING
        )
        print(f"✅ 会话状态更新成功: {success}")
        
        # 测试会话摘要
        summary = session_service.get_session_summary(session.session_id)
        print(f"✅ 会话摘要获取成功，当前阶段: {summary['current_stage']}")
        
        # 测试会话列表
        active_sessions = session_service.list_active_sessions()
        print(f"✅ 活跃会话列表获取成功，会话数: {len(active_sessions)}")
        
        # 测试会话完成
        session_service.complete_session(session.session_id)
        print("✅ 会话完成标记成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 识别会话管理服务测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始第三阶段领域服务测试\n")
    
    test_results = []
    
    # 执行各项测试
    test_results.append(("导入测试", test_imports()))
    test_results.append(("聚类服务", test_clustering_service()))
    test_results.append(("识别服务", test_recognition_service()))
    test_results.append(("参数提取服务", test_parameter_extraction_service()))
    test_results.append(("会话管理服务", test_recognition_session_service()))
    
    # 汇总结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！第三阶段领域服务实现成功。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关服务。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
