# 聚类处理器使用指南

## 概述

本文档介绍如何使用已实现的CF和PW聚类处理器，以及如何通过管道配置文件驱动两阶段聚类流程。

## 核心组件

### 1. CF聚类处理器 (CFClusteringProcessor)

执行CF（载频）维度的DBSCAN聚类，作为两阶段聚类的第一阶段。

```python
from radar_system.domain.recognition.processors.clustering import CFClusteringProcessor

# 创建处理器
cf_processor = CFClusteringProcessor()

# 准备输入数据
input_data = {"slice_data": signal_slice}  # SignalSlice实体
params = {
    "epsilon_CF": 2.0,  # CF维度邻域半径
    "min_pts": 3        # 最小点数
}

# 执行处理
result = cf_processor.run(input_data, params)

# 获取结果
cf_clusters = result["cf_clusters"]           # List[ClusterResult]
cf_statistics = result["cf_statistics"]       # Dict
unclustered_data = result["unclustered_data"] # UnclusteredPulseData
```

### 2. PW聚类处理器 (PWClusteringProcessor)

执行PW（脉宽）维度的DBSCAN聚类，处理CF聚类失败的数据。

```python
from radar_system.domain.recognition.processors.clustering import PWClusteringProcessor

# 创建处理器
pw_processor = PWClusteringProcessor()

# 准备输入数据（来自CF聚类的未聚类数据）
input_data = {"unclustered_data": unclustered_data}
params = {
    "epsilon_PW": 0.2,  # PW维度邻域半径
    "min_pts": 3        # 最小点数
}

# 执行处理
result = pw_processor.run(input_data, params)

# 获取结果
pw_clusters = result["pw_clusters"]                     # List[ClusterResult]
pw_statistics = result["pw_statistics"]                 # Dict
final_unclustered_data = result["final_unclustered_data"] # UnclusteredPulseData
```

## 管道配置驱动

### 1. 配置文件结构

配置文件位于 `configs/recognition_pipelines.yaml`：

```yaml
recognition_pipelines:
  default:
    name: "默认识别流程"
    description: "标准的CF-PW两阶段聚类识别流程"
    pipeline:
      - name: cf_clustering
        processor: cf_clustering
        input_from: [input]
        params:
          epsilon_CF: 2.0
          min_pts: 3
          
      - name: pw_clustering
        processor: pw_clustering
        input_from: [cf_clustering]
        params:
          epsilon_PW: 0.2
          min_pts: 3
```

### 2. 使用管道运行器

```python
from radar_system.domain.recognition.services.pipeline_runner import PipelineRunner
from radar_system.infrastructure.config.pipeline_loader import PipelineConfigLoader

# 加载管道配置
loader = PipelineConfigLoader()
pipeline_config = loader.get_pipeline_config("default")

# 创建管道运行器
runner = PipelineRunner(pipeline_config)

# 执行完整的聚类管道
initial_data = {"slice_data": signal_slice}
result = runner.run(initial_data)

# 获取各阶段结果
cf_result = result["cf_clustering"]
pw_result = result["pw_clustering"]
```

## 数据流程

### 1. 两阶段聚类流程

```
SignalSlice (输入)
    ↓
[CF聚类] → cf_clusters + unclustered_data
    ↓
[PW聚类] → pw_clusters + final_unclustered_data
    ↓
聚类结果 (输出)
```

### 2. 数据实体

- **输入**: `SignalSlice` - 信号切片实体
- **中间**: `UnclusteredPulseData` - 未聚类数据实体
- **输出**: `ClusterResult` - 聚类结果实体

### 3. 统计信息

每个处理器都会生成详细的统计信息：

```python
{
    "total_clusters": 3,           # 聚类总数
    "total_pulses": 100,           # 总脉冲数
    "clustered_pulses": 74,        # 已聚类脉冲数
    "unclustered_pulses": 26,      # 未聚类脉冲数
    "clustering_efficiency": 74.0, # 聚类效率(%)
    "average_cluster_size": 24.67, # 平均聚类大小
    "dimension": "CF",             # 聚类维度
    "slice_index": 0               # 切片索引
}
```

## 配置管理

### 1. 可用管道模式

- `default`: 标准CF-PW两阶段聚类
- `fast_mode`: 仅CF聚类的快速模式
- `precise_mode`: 使用更严格参数的精细模式
- `research_mode`: 用于算法研究的详细模式

### 2. 参数约束

配置文件中定义了参数范围约束：

```yaml
parameter_constraints:
  epsilon_CF:
    min: 0.1
    max: 10.0
    default: 2.0
  epsilon_PW:
    min: 0.01
    max: 2.0
    default: 0.2
  min_pts:
    min: 1
    max: 20
    default: 3
```

### 3. 参数验证

```python
# 验证参数是否符合约束
params = {"epsilon_CF": 2.0, "epsilon_PW": 0.2, "min_pts": 3}
is_valid = loader.validate_parameters(params)
```

## 错误处理

### 1. 输入验证

- 自动验证必需输入字段
- 检查数据类型和格式
- 验证参数范围

### 2. 异常处理

```python
try:
    result = processor.run(input_data, params)
except ValidationError as e:
    print(f"输入验证失败: {e}")
except Exception as e:
    print(f"处理失败: {e}")
```

### 3. 日志记录

所有处理过程都有详细的日志记录：

- 处理器初始化
- 聚类参数和进度
- 聚类结果统计
- 错误和异常信息

## 扩展指南

### 1. 添加新的聚类维度

```python
@register_processor("doa_clustering")
class DOAClusteringProcessor(BaseProcessor):
    required_inputs = ["unclustered_data"]
    output_fields = ["doa_clusters", "doa_statistics", "final_unclustered_data"]
    
    def run(self, data: Dict, params: Dict) -> Dict:
        # 实现DOA维度聚类逻辑
        pass
```

### 2. 自定义管道配置

在配置文件中添加新的管道模式：

```yaml
custom_mode:
  name: "自定义模式"
  description: "三阶段聚类流程"
  pipeline:
    - name: cf_clustering
      processor: cf_clustering
      input_from: [input]
    - name: pw_clustering
      processor: pw_clustering
      input_from: [cf_clustering]
    - name: doa_clustering
      processor: doa_clustering
      input_from: [pw_clustering]
```

## 性能优化

### 1. 参数调优

- **epsilon**: 控制聚类密度，值越小聚类越紧密
- **min_pts**: 控制聚类最小规模，值越大聚类越稳定
- 根据数据特征调整参数以获得最佳聚类效果

### 2. 内存管理

- 处理器会自动管理临时数据
- 大数据集建议分批处理
- 及时释放不需要的中间结果

这个聚类处理器框架为雷达信号识别系统提供了灵活、可扩展的两阶段聚类能力，完全符合增强式管道架构的设计理念。
