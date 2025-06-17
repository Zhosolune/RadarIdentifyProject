"""事件总线使用示例

本模块展示了如何使用简化后的事件总线API。
"""
import time
from radar_system.infrastructure.async_core.event_bus.event_bus import EventBus

def main():
    """主函数，展示事件总线的基本用法"""
    # 创建事件总线
    event_bus = EventBus()
    
    # 定义事件处理函数
    def on_signal_loaded(data):
        print(f"信号数据已加载: {data.get('file_path')}, 数据点数: {data.get('data_count')}")
    
    def on_processing_started(data):
        print(f"开始处理信号 {data.get('signal_id')}")
    
    def on_processing_completed(data):
        print(f"处理完成，切片数量: {data.get('slice_count')}")
    
    def on_error(data):
        print(f"错误: {data.get('error')}")
    
    # 订阅事件
    event_bus.subscribe("signal_loaded", on_signal_loaded)
    event_bus.subscribe("processing_started", on_processing_started)
    event_bus.subscribe("processing_completed", on_processing_completed)
    event_bus.subscribe("error", on_error)
    
    # 发布事件
    print("发布同步事件...")
    event_bus.publish("signal_loaded", {
        "file_path": "data.xlsx",
        "data_count": 1000
    })
    
    # 发布异步事件
    print("发布异步事件...")
    event_bus.publish_async("processing_started", {"signal_id": "123"})
    
    # 等待异步事件处理
    time.sleep(0.1)
    
    # 发布带有错误信息的事件
    event_bus.publish("error", {"error": "文件格式不正确"})
    
    # 发布处理完成事件
    event_bus.publish("processing_completed", {"slice_count": 5})
    
    # 取消订阅
    print("\n取消订阅 'signal_loaded' 事件...")
    event_bus.unsubscribe("signal_loaded", on_signal_loaded)
    
    # 再次发布事件，这次不会有响应
    print("再次发布 'signal_loaded' 事件（应该没有响应）...")
    event_bus.publish("signal_loaded", {"file_path": "another_data.xlsx", "data_count": 500})
    
    # 查看已注册的事件类型
    print(f"\n已注册的事件类型: {event_bus.event_types}")
    print(f"'processing_started' 事件的处理器数量: {event_bus.get_handler_count('processing_started')}")
    
    # 清除所有事件订阅
    print("\n清除所有事件订阅...")
    event_bus.clear()
    print(f"清除后的事件类型: {event_bus.event_types}")

if __name__ == "__main__":
    main() 