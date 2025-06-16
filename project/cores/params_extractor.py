import numpy as np
from sklearn.cluster import DBSCAN

class ParamsExtractor:
    def __init__(self):
        pass

    def extract_grouped_values(self, data: list, eps: float = 0.5, min_samples: int = 3, threshold_ratio: float = 0.1) -> list:
        """使用DBSCAN算法对数据进行聚类分析并提取组群均值。

        Args:
            data (list): 需要进行聚类分析的数据列表
            eps (float): DBSCAN的邻域半径参数，默认0.5
            min_samples (int): DBSCAN的最小样本数参数，默认3
            threshold_ratio (float): 用于过滤簇大小的阈值比例，默认0.1

        Returns:
            list: 包含各个有效簇的均值的列表

        Raises:
            ValueError: 当输入数据为空或参数无效时抛出
        """
        # 将数据转换为二维数组
        data_reshaped = np.array(data).reshape(-1, 1)
        
        # 使用DBSCAN进行聚类
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(data_reshaped)
    
        # 获取聚类标签
        labels = db.labels_
        
        # 提取成组变化的值（排除噪声点）
        grouped_values = []
        # 计算每个组变值成立的阈值
        clusters_with_multiple_samples = sum(1 for label in set(labels) if label != -1 and np.sum(labels == label) >= 2)
        expected_min_size = len(data) / max(clusters_with_multiple_samples, 1) * threshold_ratio
        # expected_min_size = 2
        
        
        for label in set(labels):
            # 计算当前簇的大小
            current_cluster_size = np.sum(labels == label)
            if label != -1 and current_cluster_size > expected_min_size:
                # 获取当前簇的所有值
                cluster_values = [data[i] for i in range(len(data)) if labels[i] == label]
                # 使用均值来代表该簇
                cluster_mean = np.round(np.mean(cluster_values), 4)
                grouped_values.append(cluster_mean)
        
        return grouped_values
    
    def filter_related_numbers(self, numbers: list, tolerance: float = 0.4) -> list:
        """
        过滤掉数组中可能是其他数整数倍或其他数之和的数（抑制谐波）
        
        Args:
            numbers (list): 输入的一维数组
            tolerance (float): 判断误差容限，默认为0.4
            
        Returns:
            list: 过滤后的数组
        """
        if not numbers:
            return []
    
        # 将数组转换为numpy数组并排序
        arr = np.array(sorted(numbers))
        n = len(arr)
        mask = np.ones(n, dtype=bool)
        
        # 提前计算所有可能的整数倍数
        max_ratio = int(arr[-1] / arr[0] + 1) if arr[0] != 0 else 1
        possible_multiples = np.arange(1, max_ratio + 1)
        
        # 使用向量化操作检查整数倍关系
        for i in range(n - 1):
            if not mask[i]:
                continue
            
            # 计算所有可能的倍数值
            multiples = arr[i] * possible_multiples
            
            # 检查其他数是否接近这些倍数值
            for j in range(i + 1, n):
                if not mask[j]:
                    continue
                
                # 添加异常处理，确保multiples不为空
                if len(multiples) == 0:
                    continue
                
                # 找到最接近的倍数
                closest_multiple = multiples[np.argmin(np.abs(multiples - arr[j]))]
                if abs(arr[j] - closest_multiple) < tolerance:
                    mask[j] = False
        
        # 使用集合存储已检查过的和
        checked_sums = set()
        
        # 检查两数之和
        for i in range(n - 1):
            if not mask[i]:
                continue
            
            for j in range(i + 1, n):
                if not mask[j]:
                    continue
                
                sum_2 = arr[i] + arr[j]
                if sum_2 in checked_sums:
                    continue
                
                checked_sums.add(sum_2)
                
                # 只检查大于sum_2的数
                potential_matches = arr[arr > sum_2]
                if len(potential_matches) > 0:
                    relative_diff = np.abs(potential_matches - sum_2)
                    matches = np.where(relative_diff < tolerance)[0]
                    for idx in matches:
                        mask[np.where(arr == potential_matches[idx])[0][0]] = False
        
        # 检查三数之和
        max_value = arr[mask].max() if any(mask) else 0
        for i in range(n - 2):
            if not mask[i] or arr[i] * 3 > max_value:
                continue
            
            for j in range(i + 1, n - 1):
                if not mask[j] or arr[i] + arr[j] * 2 > max_value:
                    continue
                
                for k in range(j + 1, n):
                    if not mask[k]:
                        continue
                    
                    sum_3 = arr[i] + arr[j] + arr[k]
                    if sum_3 in checked_sums:
                        continue
                    
                    checked_sums.add(sum_3)
                    
                    # 只检查大于sum_3的数
                    potential_matches = arr[arr > sum_3]
                    if len(potential_matches) > 0:
                        relative_diff = np.abs(potential_matches - sum_3)
                        matches = np.where(relative_diff < tolerance)[0]
                        for idx in matches:
                            mask[np.where(arr == potential_matches[idx])[0][0]] = False
        
        return arr[mask].tolist()


