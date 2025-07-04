#!/usr/bin/env python3
"""简化的第四阶段测试脚本"""

import sys
import os

# 添加项目路径
sys.path.append('.')

def test_imports():
    """测试导入"""
    print("测试导入...")
    
    try:
        from radar_system.application.tasks.task_enums import TaskStatus, TaskPriority, RecognitionStage
        print("✅ 任务枚举导入成功")
        
        from radar_system.application.tasks.recognition_task import RecognitionTask, TaskResult
        print("✅ 识别任务导入成功")
        
        from radar_system.application.tasks.task_manager import TaskManager
        print("✅ 任务管理器导入成功")
        
        from radar_system.application.workflows.recognition_workflow import RecognitionWorkflow
        print("✅ 识别工作流导入成功")
        
        from radar_system.application.services.recognition_application_service import RecognitionApplicationService
        print("✅ 识别应用服务导入成功")
        
        from radar_system.application import (
            RecognitionApplicationService as AppService,
            RecognitionTask as Task,
            TaskResult as Result,
            TaskManager as Manager,
            TaskStatus as Status,
            TaskPriority as Priority,
            RecognitionStage as Stage,
            RecognitionWorkflow as Workflow
        )
        print("✅ 应用层模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n测试基本功能...")
    
    try:
        from radar_system.application.tasks.task_enums import TaskStatus, TaskPriority, RecognitionStage
        
        # 测试枚举
        assert TaskStatus.PENDING.display_name == "等待执行"
        assert TaskPriority.HIGH.value > TaskPriority.NORMAL.value
        assert RecognitionStage.CF_CLUSTERING.display_name == "CF维度聚类"
        print("✅ 枚举功能正常")
        
        # 测试权重总和
        total_weight = sum(stage.progress_weight for stage in RecognitionStage)
        assert abs(total_weight - 1.0) < 0.01
        print("✅ 阶段权重总和正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("第四阶段简化测试")
    print("=" * 50)
    
    # 检查当前目录
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path[:3]}...")
    
    # 测试导入
    import_success = test_imports()
    
    if import_success:
        # 测试基本功能
        basic_success = test_basic_functionality()
        
        if basic_success:
            print("\n🎉 第四阶段应用层基本功能测试通过！")
            print("主要组件已成功实现：")
            print("- 任务枚举和数据类")
            print("- 识别任务类")
            print("- 任务管理器")
            print("- 识别工作流")
            print("- 识别应用服务")
        else:
            print("\n⚠️ 基本功能测试失败")
    else:
        print("\n❌ 导入测试失败，请检查实现")

if __name__ == "__main__":
    main()
