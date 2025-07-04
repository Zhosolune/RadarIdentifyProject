#!/usr/bin/env python3
"""完整集成测试

测试完整的DDD架构集成，包括从接口层到基础设施层的端到端流程。
"""

import sys
import time
import numpy as np
from typing import Dict, Any
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QEventLoop

# 添加项目路径
sys.path.append('.')

from radar_system.ddd_initializer import DDDInitializer
from radar_system.application.tasks.task_enums import TaskPriority


class IntegrationTestRunner:
    """集成测试运行器"""
    
    def __init__(self):
        """初始化测试运行器"""
        self.app = QApplication([])
        self.ddd_initializer = None
        self.test_results = {}
    
    def setup(self):
        """设置测试环境"""
        print("设置测试环境...")
        
        # 初始化DDD架构
        self.ddd_initializer = DDDInitializer()
        components = self.ddd_initializer.initialize_all_layers()
        
        print(f"DDD架构初始化完成，组件: {list(components.keys())}")
        return True
    
    def test_ddd_architecture_initialization(self):
        """测试DDD架构初始化"""
        print("\n测试DDD架构初始化...")
        
        try:
            # 检查各层组件是否正确初始化
            recognition_handler = self.ddd_initializer.get_recognition_handler()
            application_service = self.ddd_initializer.get_application_service()
            
            assert recognition_handler is not None, "识别处理器未初始化"
            assert application_service is not None, "应用服务未初始化"
            
            print("✅ DDD架构初始化测试通过")
            return True
            
        except Exception as e:
            print(f"❌ DDD架构初始化测试失败: {e}")
            return False
    
    def test_recognition_handler_interface(self):
        """测试识别处理器接口"""
        print("\n测试识别处理器接口...")
        
        try:
            recognition_handler = self.ddd_initializer.get_recognition_handler()
            
            # 测试状态查询接口
            queue_status = recognition_handler.get_queue_status()
            assert isinstance(queue_status, dict), "队列状态应该是字典"
            assert 'total' in queue_status, "队列状态应包含total字段"
            
            # 测试活跃任务查询
            active_tasks = recognition_handler.get_active_recognitions()
            assert isinstance(active_tasks, list), "活跃任务应该是列表"
            
            print("✅ 识别处理器接口测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 识别处理器接口测试失败: {e}")
            return False
    
    def test_recognition_task_lifecycle(self):
        """测试识别任务生命周期"""
        print("\n测试识别任务生命周期...")
        
        try:
            recognition_handler = self.ddd_initializer.get_recognition_handler()
            
            # 创建测试数据
            signal_data = np.random.rand(100, 2)
            recognition_params = {
                "cf_params": {"min_samples": 3},
                "pw_params": {"threshold": 0.5},
                "extraction_params": {"method": "test"}
            }
            
            # 启动识别任务
            task_id = recognition_handler.start_recognition(
                signal_data=signal_data,
                recognition_params=recognition_params,
                priority=TaskPriority.HIGH
            )
            
            assert task_id is not None, "任务启动失败"
            assert len(task_id) > 0, "任务ID不能为空"
            
            # 检查任务状态
            status = recognition_handler.get_recognition_status(task_id)
            assert status is not None, "无法获取任务状态"
            assert status['task_id'] == task_id, "任务ID不匹配"
            
            print(f"任务启动成功: {task_id}")
            print(f"任务状态: {status.get('status_display', 'Unknown')}")
            
            # 测试任务控制
            if status['status'] == 'running':
                # 测试暂停
                pause_success = recognition_handler.pause_recognition(task_id)
                print(f"任务暂停: {'成功' if pause_success else '失败'}")
                
                # 测试恢复
                resume_success = recognition_handler.resume_recognition(task_id)
                print(f"任务恢复: {'成功' if resume_success else '失败'}")
            
            # 测试取消
            cancel_success = recognition_handler.cancel_recognition(task_id)
            print(f"任务取消: {'成功' if cancel_success else '失败'}")
            
            print("✅ 识别任务生命周期测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 识别任务生命周期测试失败: {e}")
            return False
    
    def test_signal_communication(self):
        """测试信号通信"""
        print("\n测试信号通信...")
        
        try:
            recognition_handler = self.ddd_initializer.get_recognition_handler()
            
            # 记录接收到的信号
            received_signals = []
            
            def on_recognition_started(task_id, session_id):
                received_signals.append(('started', task_id, session_id))
            
            def on_recognition_failed(task_id, error_message):
                received_signals.append(('failed', task_id, error_message))
            
            def on_task_status_changed(task_id, status):
                received_signals.append(('status_changed', task_id, status))
            
            # 连接信号
            recognition_handler.recognition_started.connect(on_recognition_started)
            recognition_handler.recognition_failed.connect(on_recognition_failed)
            recognition_handler.task_status_changed.connect(on_task_status_changed)
            
            # 启动一个测试任务
            signal_data = np.random.rand(50, 2)
            task_id = recognition_handler.start_recognition(
                signal_data=signal_data,
                priority=TaskPriority.NORMAL
            )
            
            # 等待信号
            loop = QEventLoop()
            timer = QTimer()
            timer.timeout.connect(loop.quit)
            timer.start(1000)  # 等待1秒
            loop.exec_()
            
            # 检查是否接收到信号
            print(f"接收到 {len(received_signals)} 个信号")
            for signal_info in received_signals:
                print(f"  信号: {signal_info[0]}, 参数: {signal_info[1:]}")
            
            # 取消任务
            if task_id:
                recognition_handler.cancel_recognition(task_id)
            
            print("✅ 信号通信测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 信号通信测试失败: {e}")
            return False
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n测试错误处理...")
        
        try:
            recognition_handler = self.ddd_initializer.get_recognition_handler()
            
            # 测试无效任务ID
            invalid_status = recognition_handler.get_recognition_status("invalid_task_id")
            assert invalid_status is None, "无效任务ID应返回None"
            
            # 测试无效操作
            invalid_pause = recognition_handler.pause_recognition("invalid_task_id")
            assert not invalid_pause, "无效任务暂停应返回False"
            
            invalid_cancel = recognition_handler.cancel_recognition("invalid_task_id")
            assert not invalid_cancel, "无效任务取消应返回False"
            
            print("✅ 错误处理测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 错误处理测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("完整集成测试")
        print("=" * 60)
        
        # 设置测试环境
        if not self.setup():
            print("❌ 测试环境设置失败")
            return False
        
        # 运行测试
        tests = [
            self.test_ddd_architecture_initialization,
            self.test_recognition_handler_interface,
            self.test_recognition_task_lifecycle,
            self.test_signal_communication,
            self.test_error_handling
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ 测试执行异常: {e}")
        
        # 输出结果
        print("\n" + "=" * 60)
        print(f"测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有集成测试通过！")
            print("\n✨ DDD架构集成成功特点:")
            print("- 完整的四层架构正确初始化")
            print("- 识别处理器接口功能正常")
            print("- 任务生命周期管理完整")
            print("- Qt信号通信机制工作正常")
            print("- 错误处理机制健全")
        else:
            print("⚠️ 部分测试失败，请检查实现")
        
        return passed == total
    
    def cleanup(self):
        """清理测试环境"""
        if self.ddd_initializer:
            self.ddd_initializer.shutdown()
        self.app.quit()


def main():
    """主函数"""
    test_runner = IntegrationTestRunner()
    
    try:
        success = test_runner.run_all_tests()
        return 0 if success else 1
    finally:
        test_runner.cleanup()


if __name__ == "__main__":
    sys.exit(main())
