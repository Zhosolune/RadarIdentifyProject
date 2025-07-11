# DBSCAN聚类服务实现文档

## 概述

本文档描述了基于DBSCAN算法的雷达信号聚类服务的完整实现，该服务遵循DDD架构原则，在Domain层实现核心聚类业务逻辑。

## 架构设计

### 1. 模块结构

```
radar_system/domain/recognition/services/
├── __init__.py                           # 服务模块导出
├── clustering_service.py                 # 核心DBSCAN聚类服务
├── ui_params_parser.py                   # UI参数解析工具
└── clustering_integration_example.py     # 集成使用示例
```

### 2. 核心组件

#### 2.1 ClusteringParams 数据类
- **功能**: 封装聚类参数
- **属性**: eps（邻域半径）、min_samples（最小样本数）、dimension（聚类维度）
- **验证**: 自动验证参数有效性

#### 2.2 DBSCANClusteringService 核心服务
- **功能**: 提供通用的DBSCAN聚类功能
- **支持维度**: CF（载频）和PW（脉宽）
- **输入**: SignalSlice切片实体对象
- **输出**: ClusterResult列表 + UnclusteredPulseData实体

#### 2.3 UIParamsParser 参数解析器
- **功能**: 从UI控件解析聚类参数
- **特性**: 参数验证、默认值回退、错误处理

## 功能特性

### 1. 通用性设计
- 支持CF和PW两个维度的聚类
- 可扩展支持其他维度（DOA、PA等）
- 统一的接口设计

### 2. 参数管理
- 从UI控件动态获取参数
- 配置文件默认值回退
- 参数有效性验证

### 3. 错误处理
- 完整的异常处理机制
- 详细的日志记录
- 优雅的错误恢复

### 4. 性能优化
- 使用scikit-learn的高效DBSCAN实现
- NumPy向量化操作
- 内存友好的数据处理

## 使用方法

### 1. 基本使用

```python
from radar_system.domain.recognition.services import DBSCANClusteringService, ClusteringParams

# 创建聚类服务
clustering_service = DBSCANClusteringService()

# 创建聚类参数
cf_params = ClusteringParams(eps=2.0, min_samples=3, dimension='CF')

# 执行聚类
cluster_results, unclustered_data = clustering_service.cluster_signal_slice(
    signal_slice, cf_params
)
```

### 2. 从UI获取参数

```python
from radar_system.domain.recognition.services import UIParamsParser

# 从主窗口获取UI参数
ui_params = UIParamsParser.get_validated_params_dict(main_window)

# 获取聚类参数
cf_params = clustering_service.get_clustering_params_from_ui(ui_params, 'CF')
```

### 3. 集成使用

```python
from radar_system.domain.recognition.services.clustering_integration_example import ClusteringIntegrationService

# 创建集成服务
integration_service = ClusteringIntegrationService()

# 处理完整聚类流程
result = integration_service.process_signal_slice_clustering(signal_slice, main_window)
```

## 配置参数

### 1. 默认配置（config.json）

```json
{
    "clustering": {
        "epsilon_cf": 2.0,
        "epsilon_pw": 0.2,
        "min_pts": 1
    }
}
```

### 2. UI控件映射

| UI控件名 | 配置参数 | 描述 |
|---------|---------|------|
| epsilon_cf | epsilon_cf | CF维度邻域半径 |
| epsilon_pw | epsilon_pw | PW维度邻域半径 |
| min_pts | min_pts | 最小点数 |

## 数据流程

### 1. 输入数据
- **SignalSlice**: 信号切片实体
  - data: (N, 5) 数组 [CF, PW, DOA, PA, TOA]
  - time_range: 时间范围信息
  - slice_index: 切片索引

### 2. 处理流程
1. 参数验证和解析
2. 特征数据提取
3. DBSCAN聚类执行
4. 结果处理和分类
5. 统计信息记录

### 3. 输出数据
- **ClusterResult列表**: 成功聚类的结果
  - cluster_data: 聚类数据
  - dimension_category_index: 维度类别索引
- **UnclusteredPulseData**: 未聚类数据（可选）
  - pulse_data: 未聚类的脉冲数据
  - successful_cluster_count: 成功聚类数量

## 测试覆盖

### 1. 单元测试
- 参数验证测试
- 聚类功能测试
- 错误处理测试
- UI参数解析测试

### 2. 集成测试
- 完整聚类流程测试
- 多维度聚类测试
- 配置管理集成测试

### 3. 性能测试
- 大数据集聚类性能
- 内存使用效率
- 并发处理能力

## 扩展建议

### 1. 功能扩展
- 支持其他聚类算法（K-means、层次聚类等）
- 添加聚类质量评估指标
- 实现自适应参数调优

### 2. 性能优化
- 并行聚类处理
- 增量聚类支持
- GPU加速计算

### 3. 可视化支持
- 聚类结果可视化
- 参数调优界面
- 聚类质量监控

## 注意事项

### 1. 依赖要求
- scikit-learn >= 0.24.0
- numpy >= 1.19.0
- PyQt5 >= 5.15.0

### 2. 性能考虑
- 大数据集可能需要调整eps参数
- min_samples参数影响聚类敏感度
- 内存使用与数据规模成正比

### 3. 错误处理
- 空数据集会返回空结果
- 无效参数会使用默认值
- 聚类失败会记录详细日志

## 维护指南

### 1. 参数调优
- 根据数据特征调整eps值
- 根据噪声容忍度调整min_samples
- 监控聚类质量指标

### 2. 性能监控
- 记录聚类执行时间
- 监控内存使用情况
- 跟踪聚类成功率

### 3. 版本升级
- 保持向后兼容性
- 更新测试用例
- 文档同步更新
