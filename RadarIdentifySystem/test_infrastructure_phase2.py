#!/usr/bin/env python3
"""第二阶段基础设施组件测试脚本

验证新创建的基础设施组件能够正确导入和初始化。
"""

import sys
import os
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有基础设施组件的导入"""
    print("=== 测试基础设施组件导入 ===")
    
    try:
        # 测试聚类组件导入
        from radar_system.infrastructure.clustering import DBSCANClusterer
        print("✅ DBSCANClusterer 导入成功")
        
        # 测试可视化组件导入
        from radar_system.infrastructure.visualization import ClusterImageGenerator
        print("✅ ClusterImageGenerator 导入成功")
        
        # 测试机器学习组件导入
        from radar_system.infrastructure.ml import ModelLoader, NeuralNetworkPredictor
        print("✅ ModelLoader, NeuralNetworkPredictor 导入成功")
        
        # 测试分析组件导入
        from radar_system.infrastructure.analysis import ParameterExtractor
        print("✅ ParameterExtractor 导入成功")
        
        # 测试领域实体导入
        from radar_system.domain.recognition.entities import (
            DimensionType, ClusterStatus, ProcessingStage,
            ClusterCandidate, RecognitionResult, RecognitionSession
        )
        print("✅ 领域实体导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_dbscan_clusterer():
    """测试DBSCAN聚类器"""
    print("\n=== 测试DBSCAN聚类器 ===")
    
    try:
        from radar_system.infrastructure.clustering import DBSCANClusterer
        from radar_system.domain.recognition.entities import DimensionType
        
        # 创建聚类器
        clusterer = DBSCANClusterer(epsilon_cf=2.0, epsilon_pw=0.2, min_samples=3)
        print("✅ DBSCAN聚类器创建成功")
        
        # 创建测试数据
        test_data = np.random.rand(50, 5) * 100  # 50个点，5个维度
        
        # 测试CF维度聚类
        cf_labels = clusterer.cluster_dimension(test_data, DimensionType.CF)
        print(f"✅ CF维度聚类完成，标签数量: {len(cf_labels)}")
        
        # 测试PW维度聚类
        pw_labels = clusterer.cluster_dimension(test_data, DimensionType.PW)
        print(f"✅ PW维度聚类完成，标签数量: {len(pw_labels)}")
        
        # 测试聚类提取
        cf_clusters = clusterer.extract_clusters(test_data, cf_labels, DimensionType.CF)
        print(f"✅ 聚类提取完成，聚类数量: {len(cf_clusters)}")
        
        return True
        
    except Exception as e:
        print(f"❌ DBSCAN聚类器测试失败: {e}")
        return False

def test_image_generator():
    """测试图像生成器"""
    print("\n=== 测试图像生成器 ===")
    
    try:
        from radar_system.infrastructure.visualization import ClusterImageGenerator
        from radar_system.domain.recognition.entities import ClusterCandidate, DimensionType, ClusterStatus
        
        # 创建临时目录
        temp_dir = project_root / "temp_test"
        temp_dir.mkdir(exist_ok=True)
        
        # 创建图像生成器
        generator = ClusterImageGenerator(
            output_dir=str(temp_dir / "output"),
            temp_dir=str(temp_dir / "temp")
        )
        print("✅ 图像生成器创建成功")
        
        # 创建测试聚类候选
        test_data = np.random.rand(20, 5) * 100
        from radar_system.domain.signal.entities.signal import TimeRange

        cluster_candidate = ClusterCandidate(
            cluster_data=test_data,
            dimension_type=DimensionType.CF,
            status=ClusterStatus.VALID,
            slice_index=0,
            cluster_index=1,
            time_range=TimeRange(start_time=0.0, end_time=1.0)
        )
        
        # 测试图像生成
        image_paths = generator.generate_cluster_images(cluster_candidate, for_prediction=True)
        print(f"✅ 图像生成完成，路径: {list(image_paths.keys())}")
        
        # 验证文件是否存在
        for image_type, path in image_paths.items():
            if Path(path).exists():
                print(f"✅ {image_type}图像文件存在: {Path(path).name}")
            else:
                print(f"❌ {image_type}图像文件不存在: {path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 图像生成器测试失败: {e}")
        return False

def test_parameter_extractor():
    """测试参数提取器"""
    print("\n=== 测试参数提取器 ===")
    
    try:
        from radar_system.infrastructure.analysis import ParameterExtractor
        from radar_system.domain.recognition.entities import (
            ClusterCandidate, DimensionType,
            ClusterStatus
        )
        
        # 创建参数提取器
        extractor = ParameterExtractor()
        print("✅ 参数提取器创建成功")
        
        # 创建测试数据
        test_data = np.random.rand(30, 5) * 100
        from radar_system.domain.signal.entities.signal import TimeRange

        # 创建测试聚类候选
        cluster_candidate = ClusterCandidate(
            cluster_data=test_data,
            dimension_type=DimensionType.CF,
            status=ClusterStatus.VALID,
            slice_index=0,
            cluster_index=1,
            time_range=TimeRange(start_time=0.0, end_time=1.0)
        )
        
        # 直接测试参数提取的内部方法
        # 测试成组值提取
        test_values = np.array([1.0, 1.1, 2.0, 2.1, 5.0, 5.1])
        grouped_values = extractor._extract_grouped_values(
            test_values, eps=0.5, min_samples=2, threshold_ratio=0.1
        )

        # 测试DOA值提取
        doa_values = extractor._extract_doa_values(test_data[:, 2])

        # 测试DTOA计算
        toa_data = test_data[:, 4] if test_data.shape[1] > 4 else np.array([1, 2, 3, 4, 5])
        dtoa_values = extractor._calculate_dtoa(toa_data)
        print(f"✅ 参数提取完成")
        print(f"   成组值提取结果: {len(grouped_values)} 个值")
        print(f"   DOA值提取结果: {len(doa_values)} 个值")
        print(f"   DTOA计算结果: {len(dtoa_values)} 个值")
        
        return True
        
    except Exception as e:
        print(f"❌ 参数提取器测试失败: {e}")
        return False

def test_neural_network_predictor():
    """测试神经网络预测器（仅测试初始化，不加载实际模型）"""
    print("\n=== 测试神经网络预测器 ===")
    
    try:
        from radar_system.infrastructure.ml import NeuralNetworkPredictor
        
        # 创建预测器（使用现有的ml目录）
        models_dir = project_root / "radar_system" / "infrastructure" / "ml"
        predictor = NeuralNetworkPredictor(str(models_dir))
        print("✅ 神经网络预测器创建成功")
        
        # 获取模型信息
        model_info = predictor.get_model_info()
        print(f"✅ 模型信息获取成功，初始化状态: {model_info['is_initialized']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 神经网络预测器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始第二阶段基础设施组件测试\n")
    
    test_results = []
    
    # 执行各项测试
    test_results.append(("导入测试", test_imports()))
    test_results.append(("DBSCAN聚类器", test_dbscan_clusterer()))
    test_results.append(("图像生成器", test_image_generator()))
    test_results.append(("参数提取器", test_parameter_extractor()))
    test_results.append(("神经网络预测器", test_neural_network_predictor()))
    
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
        print("🎉 所有测试通过！第二阶段基础设施组件实现成功。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关组件。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
