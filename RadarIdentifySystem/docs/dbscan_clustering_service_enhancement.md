# DBSCANClusteringService 增强功能使用指南

## 概述

`DBSCANClusteringService`已经增强，现在支持两种输入类型：
1. `SignalSlice` - 原始信号切片
2. `UnclusteredPulseData` - 未聚类的脉冲数据

这个增强功能简化了多维度聚类流程，避免了创建临时对象的开销，提高了代码效率和简洁性。

## 功能特性

### 1. 统一的聚类接口

```python
from radar_system.domain.recognition.services import DBSCANClusteringService, ClusteringParams

# 创建聚类服务
service = DBSCANClusteringService()

# 方法签名（支持两种输入类型）
def cluster_signal_slice(self, 
                        signal_data: Union[SignalSlice, UnclusteredPulseData],
                        clustering_params: ClusteringParams) -> Tuple[List[ClusterResult], Optional[UnclusteredPulseData]]
```

### 2. 自动类型检测

服务内部使用`isinstance()`自动检测输入类型并相应处理：

```python
# 根据输入类型提取数据
if isinstance(signal_data, SignalSlice):
    system_logger.debug(f"处理SignalSlice类型输入，切片索引: {signal_data.slice_index}")
    data = signal_data.data
    slice_index = signal_data.slice_index
    time_range = signal_data.time_range
    is_empty = signal_data.is_empty
    data_id = signal_data.id
else:  # UnclusteredPulseData
    system_logger.debug(f"处理UnclusteredPulseData类型输入，切片索引: {signal_data.slice_index}")
    data = signal_data.pulse_data
    slice_index = signal_data.slice_index
    time_range = signal_data.time_ranges
    is_empty = data.size == 0
    data_id = f"unclustered-{signal_data.slice_index}"
```

## 使用方法

### 1. 使用SignalSlice进行聚类

```python
from radar_system.domain.signal.entities.signal import SignalSlice
from radar_system.domain.recognition.services import DBSCANClusteringService, ClusteringParams

# 创建聚类服务
service = DBSCANClusteringService()

# 创建聚类参数
clustering_params = ClusteringParams(
    eps=2.0,
    min_samples=3,
    dimension='CF'
)

# 执行聚类
clusters, unclustered_data = service.cluster_signal_slice(
    signal_slice, clustering_params
)

print(f"聚类结果: {len(clusters)}个聚类")
print(f"未聚类数据: {unclustered_data.get_pulse_count() if unclustered_data else 0}个脉冲")
```

### 2. 使用UnclusteredPulseData进行聚类

```python
from radar_system.domain.recognition.entities.cluster_result import UnclusteredPulseData

# 假设从前一阶段聚类获得了未聚类数据
unclustered_data = previous_clustering_result["unclustered_data"]

# 创建聚类参数
clustering_params = ClusteringParams(
    eps=0.2,
    min_samples=3,
    dimension='PW'
)

# 直接对未聚类数据进行聚类
clusters, remaining_unclustered = service.cluster_signal_slice(
    unclustered_data, clustering_params
)

print(f"二次聚类结果: {len(clusters)}个聚类")
print(f"剩余未聚类数据: {remaining_unclustered.get_pulse_count() if remaining_unclustered else 0}个脉冲")
```

### 3. 两阶段聚类流程

```python
# 第一阶段：CF聚类
cf_params = ClusteringParams(eps=2.0, min_samples=3, dimension='CF')
cf_clusters, unclustered_data = service.cluster_signal_slice(signal_slice, cf_params)

# 第二阶段：PW聚类（如果有未聚类数据）
if unclustered_data:
    pw_params = ClusteringParams(eps=0.2, min_samples=3, dimension='PW')
    pw_clusters, final_unclustered = service.cluster_signal_slice(unclustered_data, pw_params)
    
    print(f"CF聚类: {len(cf_clusters)}个")
    print(f"PW聚类: {len(pw_clusters)}个")
    print(f"最终未聚类: {final_unclustered.get_pulse_count() if final_unclustered else 0}个脉冲")
```

## 数据提取逻辑

### SignalSlice类型
- **数据源**: `signal_slice.data`
- **切片索引**: `signal_slice.slice_index`
- **时间范围**: `signal_slice.time_range`
- **空检查**: `signal_slice.is_empty`
- **标识**: `signal_slice.id`

### UnclusteredPulseData类型
- **数据源**: `unclustered_data.pulse_data`
- **切片索引**: `unclustered_data.slice_index`
- **时间范围**: `unclustered_data.time_ranges`
- **空检查**: `data.size == 0`
- **标识**: `f"unclustered-{slice_index}"`

## 日志记录

服务会自动记录处理的数据类型：

```
2025-07-15 16:36:51.223 | DEBUG | system | 处理SignalSlice类型输入，切片索引: 0
2025-07-15 16:36:51.223 | INFO  | system | 聚类完成 - 切片索引: 0, 维度: CF, 总数据点: 100, 聚类数: 3, 已聚类点数: 74, 未聚类点数: 26

2025-07-15 16:36:51.224 | DEBUG | system | 处理UnclusteredPulseData类型输入，切片索引: 0
2025-07-15 16:36:51.225 | INFO  | system | 聚类完成 - 切片索引: 0, 维度: PW, 总数据点: 20, 聚类数: 3, 已聚类点数: 19, 未聚类点数: 1
```

## 错误处理

增强的错误处理会根据输入类型提供更精确的错误信息：

```python
try:
    clusters, unclustered = service.cluster_signal_slice(signal_data, params)
except ValidationError as e:
    # 错误信息会指明是SignalSlice还是UnclusteredPulseData聚类失败
    print(f"聚类失败: {e}")
```

## 性能优化

### 1. 避免临时对象创建
- 不再需要为UnclusteredPulseData创建临时SignalSlice对象
- 减少内存分配和对象创建开销
- 提高聚类处理效率

### 2. 统一的数据处理流程
- 所有聚类逻辑集中在一个方法中
- 减少代码重复和维护成本
- 提供一致的聚类行为

## 向后兼容性

这个增强完全向后兼容：
- 现有使用SignalSlice的代码无需修改
- 方法签名保持一致（只是参数类型扩展）
- 返回值格式不变

## 简化的UnclusteredDataClusteringService

由于DBSCANClusteringService现在直接支持UnclusteredPulseData，UnclusteredDataClusteringService变得更加简洁：

```python
# 之前需要创建临时SignalSlice
temp_slice = self._create_temp_signal_slice(unclustered_data)
base_clusters, remaining_unclustered = self.base_clustering_service.cluster_signal_slice(
    temp_slice, clustering_params
)

# 现在直接传入UnclusteredPulseData
base_clusters, remaining_unclustered = self.base_clustering_service.cluster_signal_slice(
    unclustered_data, clustering_params
)
```

## 最佳实践

1. **类型检查**: 在调用前确保传入正确的数据类型
2. **参数验证**: 使用适当的聚类参数
3. **错误处理**: 捕获并处理ValidationError异常
4. **日志监控**: 关注聚类过程的日志输出
5. **性能监控**: 监控聚类效率和内存使用

## 总结

这个增强功能显著简化了多维度聚类流程，提高了代码效率和可维护性。通过统一的接口支持两种输入类型，为雷达信号识别系统的聚类处理提供了更加灵活和高效的解决方案。
