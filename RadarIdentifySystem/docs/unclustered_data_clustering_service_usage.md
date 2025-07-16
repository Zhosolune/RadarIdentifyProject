# 未聚类数据聚类服务使用指南

## 概述

本文档介绍如何使用`UnclusteredDataClusteringService`服务类来处理未聚类数据的二次聚类，特别是如何实现跨维度的聚类索引继承机制。

## 核心功能

`UnclusteredDataClusteringService`专门用于处理`UnclusteredPulseData`实体的二次聚类，主要功能包括：

1. **复用DBSCANClusteringService的核心聚类逻辑**
2. **实现聚类索引的跨维度继承**：确保不同维度的聚类结果有连续的索引
3. **正确处理dimension_category_index**：在每个维度重置为对应的维度索引
4. **提供专门的未聚类数据处理接口**

## 使用方法

### 1. 基本使用

```python
from radar_system.domain.recognition.services import UnclusteredDataClusteringService, ClusteringParams
from radar_system.domain.recognition.entities.cluster_result import UnclusteredPulseData

# 创建聚类服务
clustering_service = UnclusteredDataClusteringService()

# 创建聚类参数
clustering_params = ClusteringParams(
    eps=0.2,
    min_samples=3,
    dimension='PW'
)

# 执行未聚类数据聚类
clusters, remaining_unclustered = clustering_service.cluster_unclustered_data(
    unclustered_data, clustering_params
)

# 处理聚类结果
for cluster in clusters:
    print(f"聚类索引: {cluster.cluster_index}, 维度索引: {cluster.dimension_category_index}")
```

### 2. 在处理器中使用

```python
# PW聚类处理器示例
@register_processor("pw_clustering")
class PWClusteringProcessor(BaseProcessor):
    def __init__(self):
        # 使用专门的未聚类数据聚类服务
        self.clustering_service = UnclusteredDataClusteringService()
    
    def run(self, data: Dict, params: Dict) -> Dict:
        # 获取未聚类数据
        unclustered_data = data["unclustered_data"]
        
        # 创建聚类参数
        clustering_params = ClusteringParams(
            eps=params.get("epsilon_PW", 0.2),
            min_samples=params.get("min_pts", 3),
            dimension='PW'
        )
        
        # 执行PW聚类 - 使用专门的未聚类数据聚类服务
        pw_clusters, final_unclustered_data = self.clustering_service.cluster_unclustered_data(
            unclustered_data, clustering_params
        )
        
        return {
            "pw_clusters": pw_clusters,
            "pw_statistics": self._calculate_statistics(...),
            "final_unclustered_data": final_unclustered_data
        }
```

## 聚类索引继承机制

### 1. 索引继承原理

在多维度聚类流程中，为了确保每个聚类结果有唯一的索引，`UnclusteredDataClusteringService`实现了聚类索引的跨维度继承机制：

1. **cluster_index**：从前一维度的最大索引+1开始
   - 例如：如果CF维度有3个聚类（索引0,1,2），则PW维度的聚类索引从3开始
   - 使用`UnclusteredPulseData.successful_cluster_count`获取前一维度的聚类数量

2. **dimension_category_index**：在每个维度重置为对应的维度索引
   - CF维度：0
   - PW维度：1
   - DOA维度：2
   - 等等

### 2. 索引继承示例

```
CF维度聚类结果:
- Cluster 0 (dimension_category_index=0)
- Cluster 1 (dimension_category_index=0)
- Cluster 2 (dimension_category_index=0)

PW维度聚类结果:
- Cluster 3 (dimension_category_index=1)
- Cluster 4 (dimension_category_index=1)

DOA维度聚类结果:
- Cluster 5 (dimension_category_index=2)
```

## 实现细节

### 1. 聚类索引处理

```python
def _process_cluster_indices(self, base_clusters, unclustered_data, clustering_params):
    processed_clusters = []
    
    # 计算起始聚类索引：前一维度成功聚类数量
    start_cluster_index = unclustered_data.successful_cluster_count
    
    # 确定dimension_category_index
    dimension_category_index = self._get_dimension_category_index(clustering_params.dimension)
    
    for i, cluster in enumerate(base_clusters):
        # 创建新的聚类结果，更新索引
        processed_cluster = ClusterResult(
            cluster_data=cluster.cluster_data,
            slice_index=cluster.slice_index,
            cluster_index=start_cluster_index + i,  # 继承前一维度的索引
            dim_name=cluster.dim_name,
            time_ranges=cluster.time_ranges,
            dimension_category_index=dimension_category_index  # 当前维度重置为0开始
        )
        processed_clusters.append(processed_cluster)
    
    return processed_clusters
```

### 2. 未聚类数据处理

```python
def _process_remaining_unclustered_data(self, remaining_unclustered, original_unclustered, new_cluster_count):
    if remaining_unclustered is None:
        return None
    
    # 更新成功聚类数量：原有数量 + 新增数量
    updated_successful_count = original_unclustered.successful_cluster_count + new_cluster_count
    
    # 创建新的未聚类数据实体
    final_unclustered_data = UnclusteredPulseData(
        pulse_data=remaining_unclustered.pulse_data,
        slice_index=remaining_unclustered.slice_index,
        clustering_dimension=remaining_unclustered.clustering_dimension,
        time_ranges=remaining_unclustered.time_ranges,
        successful_cluster_count=updated_successful_count
    )
    
    return final_unclustered_data
```

## 维度映射

服务内部使用以下维度映射来确定`dimension_category_index`：

```python
dimension_mapping = {
    'CF': 0,   # 载频
    'PW': 1,   # 脉宽
    'DOA': 2,  # 到达角
    'PA': 3,   # 脉冲幅度
    'TOA': 4   # 到达时间
}
```

## 错误处理

服务提供完善的错误处理机制：

1. **输入验证**：验证未聚类数据和聚类参数的有效性
2. **空数据处理**：检查未聚类数据是否为空
3. **维度检查**：验证聚类维度的有效性
4. **异常处理**：捕获并处理聚类过程中的异常

## 日志记录

服务会记录详细的聚类过程日志：

```
2025-07-15 15:46:03.237 | INFO | system | 开始PW维度二次聚类，数据点数: 26, 前一维度成功聚类数: 3
2025-07-15 15:46:03.239 | INFO | system | 聚类完成 - 切片: unclustered-slice-fd9762d3-047c-4a0b-9358-fba0fba1a8cc, 维度: PW, 总数据点: 26, 聚类数: 2, 已聚类点数: 26, 未聚类点数: 0
2025-07-15 15:46:03.240 | INFO | system | PW维度二次聚类完成 - 切片: 0, 维度: PW, 总数据点: 26, 聚类数: 2, 已聚类点数: 26, 剩余未聚类点数: 0, 聚类效率: 100.0%
```

## 扩展指南

### 1. 添加新的聚类维度

要添加新的聚类维度，只需在`_get_dimension_category_index`方法中添加新的维度映射：

```python
def _get_dimension_category_index(self, dimension: str) -> int:
    dimension_mapping = {
        'CF': 0,
        'PW': 1,
        'DOA': 2,
        'PA': 3,
        'TOA': 4,
        'NEW_DIMENSION': 5  # 添加新维度
    }
    return dimension_mapping.get(dimension, 0)
```

### 2. 自定义聚类处理

如果需要自定义聚类处理逻辑，可以继承`UnclusteredDataClusteringService`并重写相关方法：

```python
class CustomUnclusteredDataClusteringService(UnclusteredDataClusteringService):
    def _process_cluster_indices(self, base_clusters, unclustered_data, clustering_params):
        # 自定义索引处理逻辑
        pass
```

## 性能优化

1. **临时对象管理**：服务会自动管理临时SignalSlice对象
2. **索引计算优化**：使用高效的索引计算方法
3. **内存管理**：避免不必要的数据复制

## 总结

`UnclusteredDataClusteringService`为多维度聚类流程提供了专门的未聚类数据处理能力，确保了聚类结果的正确索引继承，是增强式管道架构中的重要组件。
