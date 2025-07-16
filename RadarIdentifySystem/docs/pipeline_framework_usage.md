# 增强式管道架构核心框架使用指南

## 概述

本文档介绍如何使用已实现的增强式管道架构核心框架，包括处理器基类、注册器机制和管道运行器的基本用法。

## 核心组件

### 1. 处理器基类 (BaseProcessor)

所有处理器都必须继承 `BaseProcessor` 并实现 `run` 方法：

```python
from radar_system.domain.recognition.processors.base_processor import BaseProcessor
from radar_system.domain.recognition.processors.registry import register_processor

@register_processor("my_processor")
class MyProcessor(BaseProcessor):
    """自定义处理器"""
    
    required_inputs = ["input_data"]  # 必需输入字段
    optional_inputs = ["config"]      # 可选输入字段
    output_fields = ["result"]        # 输出字段
    
    def run(self, data: Dict, params: Dict) -> Dict:
        """执行处理逻辑"""
        self.validate_inputs(data)  # 验证输入
        
        # 处理逻辑
        input_data = data["input_data"]
        result = self.process_data(input_data, params)
        
        return {"result": result}
```

### 2. 注册器机制

使用 `@register_processor` 装饰器自动注册处理器：

```python
from radar_system.domain.recognition.processors.registry import (
    register_processor, 
    PROCESSOR_REGISTRY,
    get_processor,
    list_processors
)

# 注册处理器
@register_processor("example_processor")
class ExampleProcessor(BaseProcessor):
    pass

# 获取已注册的处理器
processor_cls = get_processor("example_processor")

# 列出所有处理器
all_processors = list_processors()
```

### 3. 管道运行器 (PipelineRunner)

使用配置驱动的方式执行处理器管道：

```python
from radar_system.domain.recognition.services.pipeline_runner import PipelineRunner

# 定义管道配置
config = {
    "pipeline": [
        {
            "name": "step1",
            "processor": "my_processor",
            "input_from": ["input"],
            "params": {"param1": "value1"}
        },
        {
            "name": "step2", 
            "processor": "another_processor",
            "input_from": ["step1"],
            "params": {"param2": "value2"}
        }
    ]
}

# 创建并运行管道
runner = PipelineRunner(config)
result = runner.run({"input_data": "initial_data"})

# 获取特定步骤的结果
step1_result = runner.get_step_result("step1")
```

## 数据流机制

### 数据总线

管道运行器使用数据总线 (`cache`) 在步骤之间传递数据：

- `input`: 初始输入数据
- `step_name`: 每个步骤的输出数据
- 后续步骤可通过 `input_from` 引用前面步骤的输出

### 输入数据准备

`input_from` 字段指定数据来源：

```python
{
    "name": "current_step",
    "processor": "processor_name",
    "input_from": ["input", "previous_step"],  # 合并多个数据源
    "params": {}
}
```

## 错误处理

框架提供完善的错误处理机制：

1. **输入验证**: `validate_inputs()` 检查必需字段
2. **处理器查找**: 自动检查处理器是否已注册
3. **数据依赖**: 验证 `input_from` 中的数据源是否存在
4. **异常传播**: 将处理器异常包装为 `RuntimeError`

## 日志记录

框架集成了系统日志，自动记录：

- 管道初始化信息
- 步骤执行进度
- 错误和异常信息

## 最佳实践

1. **处理器设计**:
   - 明确定义 `required_inputs` 和 `output_fields`
   - 在 `run` 方法开始时调用 `validate_inputs()`
   - 返回包含所有 `output_fields` 的字典

2. **配置管理**:
   - 使用有意义的步骤名称
   - 合理设置处理器参数
   - 确保数据依赖关系正确

3. **错误处理**:
   - 在处理器中添加适当的异常处理
   - 使用日志记录重要信息
   - 提供有意义的错误消息

## 扩展指南

要添加新的处理器：

1. 继承 `BaseProcessor`
2. 使用 `@register_processor` 装饰器
3. 实现 `run` 方法
4. 定义输入输出字段
5. 在配置中引用处理器

框架设计遵循 YAGNI 原则，只实现当前明确需要的功能，为后续扩展提供了坚实的基础。
