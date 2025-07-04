#!/usr/bin/env python3
"""第四阶段应用层测试脚本

测试应用层的完整功能，包括：
1. 任务枚举和数据类
2. 识别任务类
3. 任务管理器
4. 识别工作流
5. 识别应用服务
"""

import sys
import time
import numpy as np
from typing import Dict, Any
from PyQt5.QtWidgets import QApplication

# 添加项目路径
sys.path.append('.')

from radar_system.application import (
    RecognitionApplicationService,
    RecognitionTask,
    TaskResult,
    TaskManager,
    TaskStatus,
    TaskPriority,
    RecognitionStage,
    RecognitionWorkflow
)


class ApplicationLayerTester:
    """应用层测试器"""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.test_results = []
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("第四阶段：应用层测试")
        print("=" * 60)
        
        # 测试类别
        test_categories = [
            ("任务枚举测试", self.test_task_enums),
            ("识别任务测试", self.test_recognition_task),
            ("任务管理器测试", self.test_task_manager),
            ("识别工作流测试", self.test_recognition_workflow),
            ("识别应用服务测试", self.test_recognition_application_service)
        ]
        
        for category_name, test_method in test_categories:
            print(f"\n{category_name}:")
            print("-" * 40)
            try:
                test_method()
                self.test_results.append((category_name, True, ""))
                print(f"✅ {category_name} 通过")
            except Exception as e:
                self.test_results.append((category_name, False, str(e)))
                print(f"❌ {category_name} 失败: {e}")
        
        # 输出测试总结
        self.print_test_summary()
    
    def test_task_enums(self):
        """测试任务枚举"""
        print("测试 TaskStatus 枚举...")
        
        # 测试状态属性
        assert TaskStatus.PENDING.display_name == "等待执行"
        assert TaskStatus.RUNNING.is_active == True
        assert TaskStatus.COMPLETED.is_finished == True
        assert TaskStatus.FAILED.is_finished == True
        
        print("测试 TaskPriority 枚举...")
        
        # 测试优先级
        assert TaskPriority.HIGH.value > TaskPriority.NORMAL.value
        assert TaskPriority.URGENT.display_name == "紧急"
        
        print("测试 RecognitionStage 枚举...")
        
        # 测试阶段权重
        total_weight = sum(stage.progress_weight for stage in RecognitionStage)
        assert abs(total_weight - 1.0) < 0.01, f"权重总和应为1.0，实际为{total_weight}"
        
        assert RecognitionStage.CF_CLUSTERING.display_name == "CF维度聚类"
        
        print("任务枚举测试完成")
    
    def test_recognition_task(self):
        """测试识别任务"""
        print("测试 RecognitionTask 创建...")
        
        # 创建测试数据
        signal_data = np.random.rand(1000, 2)
        recognition_params = {"param1": "value1", "param2": 42}
        
        # 创建任务
        task = RecognitionTask(
            signal_data=signal_data,
            recognition_params=recognition_params,
            priority=TaskPriority.HIGH
        )
        
        # 验证初始状态
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert task.overall_progress == 0.0
        assert task.current_stage == RecognitionStage.INITIALIZING
        
        print("测试任务状态更新...")
        
        # 测试阶段更新
        task.update_stage(RecognitionStage.CF_CLUSTERING, 0.5)
        assert task.current_stage == RecognitionStage.CF_CLUSTERING
        assert task.stage_progress == 0.5
        assert task.overall_progress > 0.0
        
        # 测试阶段完成
        stage_results = {"cluster_count": 3}
        task.complete_stage(RecognitionStage.CF_CLUSTERING, stage_results)
        
        # 测试任务摘要
        summary = task.get_summary()
        assert summary['task_id'] == task.task_id
        assert summary['status'] == TaskStatus.PENDING.value
        assert summary['priority'] == TaskPriority.HIGH.value
        
        print("识别任务测试完成")
    
    def test_task_manager(self):
        """测试任务管理器"""
        print("测试 TaskManager 创建...")
        
        # 创建任务管理器
        manager = TaskManager(max_concurrent_tasks=1)
        
        # 验证初始状态
        status = manager.get_queue_status()
        assert status['pending'] == 0
        assert status['running'] == 0
        assert status['total'] == 0
        
        print("测试任务提交...")
        
        # 创建测试任务
        signal_data = np.random.rand(500, 2)
        recognition_params = {"test": True}
        
        task = RecognitionTask(
            signal_data=signal_data,
            recognition_params=recognition_params,
            priority=TaskPriority.NORMAL
        )
        
        # 提交任务
        success = manager.submit_task(task)
        assert success == True
        
        # 验证队列状态
        status = manager.get_queue_status()
        assert status['total'] == 1
        
        # 获取任务
        retrieved_task = manager.get_task(task.task_id)
        assert retrieved_task is not None
        assert retrieved_task.task_id == task.task_id
        
        # 清理
        manager.shutdown()
        
        print("任务管理器测试完成")
    
    def test_recognition_workflow(self):
        """测试识别工作流"""
        print("测试 RecognitionWorkflow 创建...")
        
        # 创建工作流
        workflow = RecognitionWorkflow()
        
        # 设置模拟服务
        workflow.set_services(
            clustering_service="mock_clustering",
            recognition_service="mock_recognition", 
            parameter_extraction_service="mock_extraction",
            session_service="mock_session"
        )
        
        print("测试工作流执行...")
        
        # 创建测试任务
        signal_data = np.random.rand(100, 2)
        recognition_params = {"workflow_test": True}
        
        task = RecognitionTask(
            signal_data=signal_data,
            recognition_params=recognition_params
        )
        
        # 设置模拟执行回调
        def mock_callback(task):
            return workflow.execute(task)
        
        task.set_execution_callback(mock_callback)
        
        # 执行工作流
        result = workflow.execute(task)
        
        # 验证结果
        assert isinstance(result, TaskResult)
        assert result.success == True
        assert result.session_id is not None
        assert result.final_parameters is not None
        
        print("识别工作流测试完成")
    
    def test_recognition_application_service(self):
        """测试识别应用服务"""
        print("测试 RecognitionApplicationService 创建...")

        # 创建应用服务
        service = RecognitionApplicationService(max_concurrent_tasks=1)

        # 设置模拟领域服务
        service.set_domain_services(
            clustering_service="mock_clustering",
            recognition_service="mock_recognition",
            parameter_extraction_service="mock_extraction",
            session_service="mock_session"
        )

        print("测试识别任务启动...")

        # 创建测试数据
        signal_data = np.random.rand(200, 2)
        recognition_params = {
            "cf_params": {"min_samples": 5},
            "pw_params": {"threshold": 0.8},
            "extraction_params": {"method": "standard"}
        }

        # 启动识别
        task_id = service.start_recognition(
            signal_data=signal_data,
            recognition_params=recognition_params,
            priority=TaskPriority.HIGH
        )

        assert task_id is not None
        assert len(task_id) > 0

        print("测试状态查询...")

        # 获取任务状态
        status = service.get_recognition_status(task_id)
        assert status is not None
        assert status['task_id'] == task_id

        # 获取队列状态
        queue_status = service.get_queue_status()
        assert queue_status['total'] >= 1

        print("测试任务控制...")

        # 测试任务暂停（如果任务还在运行）
        if status['status'] == 'running':
            pause_success = service.pause_recognition(task_id)
            print(f"任务暂停: {'成功' if pause_success else '失败'}")

        # 测试任务取消
        cancel_success = service.cancel_recognition(task_id)
        print(f"任务取消: {'成功' if cancel_success else '失败'}")

        # 获取活跃任务列表
        active_tasks = service.get_active_recognitions()
        print(f"活跃任务数: {len(active_tasks)}")

        # 清理
        service.shutdown()

        print("识别应用服务测试完成")
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("第四阶段测试总结")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for category, success, error in self.test_results:
            status = "✅ 通过" if success else f"❌ 失败: {error}"
            print(f"{category}: {status}")
        
        print(f"\n总计: {passed}/{total} 个测试类别通过")
        
        if passed == total:
            print("🎉 第四阶段应用层实现完成！所有测试通过！")
        else:
            print("⚠️  部分测试失败，需要检查实现")


def main():
    """主函数"""
    tester = ApplicationLayerTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
