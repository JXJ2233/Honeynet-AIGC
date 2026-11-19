"""
归一化模块 - 提供多种归一化方法
基于斯坦纳树的混合专家大模型蜜罐统一优化部署系统 - 归一化工具
"""

import numpy as np
from typing import Union, List, Tuple, Dict, Any
from enum import Enum


class NormalizationMethod(Enum):
    """归一化方法枚举"""
    Z_SCORE = "z_score"          # Z-score标准差归一化
    MIN_MAX = "min_max"          # 改进区间缩放法
    FUZZY = "fuzzy"              # 模糊隶属度归一化
    DECIMAL_SCALING = "decimal"  # 小数定标归一化


class Normalizer:
    """归一化器类 - 提供多种归一化方法"""
    
    def __init__(self, method: NormalizationMethod = NormalizationMethod.MIN_MAX):
        """初始化归一化器
        
        Args:
            method: 归一化方法
        """
        self.method = method
        self.params = {}  # 存储归一化参数，用于反向归一化
    
    def fit(self, data: Union[List[float], np.ndarray]) -> None:
        """拟合数据，计算归一化参数
        
        Args:
            data: 原始数据
        """
        if isinstance(data, list):
            data = np.array(data)
        
        if self.method == NormalizationMethod.Z_SCORE:
            # Z-score归一化: (x - μ) / σ
            self.params['mean'] = np.mean(data)
            self.params['std'] = np.std(data)
            # 避免除零
            if self.params['std'] == 0:
                self.params['std'] = 1e-10
        
        elif self.method == NormalizationMethod.MIN_MAX:
            # 改进区间缩放法: (x - min) / (max - min)
            self.params['min'] = np.min(data)
            self.params['max'] = np.max(data)
            # 避免除零
            if self.params['max'] - self.params['min'] == 0:
                self.params['max'] = self.params['min'] + 1e-10
        
        elif self.method == NormalizationMethod.FUZZY:
            # 模糊隶属度归一化: 适用于有明确阈值的安全指标
            # 这里我们使用Sigmoid函数进行归一化
            self.params['midpoint'] = np.median(data)
            self.params['steepness'] = 1.0 / (np.std(data) + 1e-10)
        
        elif self.method == NormalizationMethod.DECIMAL_SCALING:
            # 小数定标归一化: x / 10^k
            max_abs = np.max(np.abs(data))
            if max_abs == 0:
                self.params['divisor'] = 1
            else:
                self.params['divisor'] = 10 ** (np.ceil(np.log10(max_abs)))
    
    def transform(self, data: Union[List[float], np.ndarray]) -> np.ndarray:
        """转换数据（归一化）
        
        Args:
            data: 原始数据
            
        Returns:
            归一化后的数据
        """
        if isinstance(data, list):
            data = np.array(data)
        
        if not self.params:
            self.fit(data)
        
        if self.method == NormalizationMethod.Z_SCORE:
            # Z-score归一化
            result = (data - self.params['mean']) / self.params['std']
            # 将结果缩放到[0,1]区间
            return self._scale_to_01(result)
        
        elif self.method == NormalizationMethod.MIN_MAX:
            # 改进区间缩放法
            return (data - self.params['min']) / (self.params['max'] - self.params['min'])
        
        elif self.method == NormalizationMethod.FUZZY:
            # 模糊隶属度归一化（Sigmoid函数）
            result = 1 / (1 + np.exp(-self.params['steepness'] * (data - self.params['midpoint'])))
            return result
        
        elif self.method == NormalizationMethod.DECIMAL_SCALING:
            # 小数定标归一化
            return data / self.params['divisor']
        
        else:
            raise ValueError(f"未知的归一化方法: {self.method}")
    
    def inverse_transform(self, normalized_data: Union[List[float], np.ndarray]) -> np.ndarray:
        """反向转换（反归一化）
        
        Args:
            normalized_data: 归一化后的数据
            
        Returns:
            原始数据
        """
        if isinstance(normalized_data, list):
            normalized_data = np.array(normalized_data)
        
        if not self.params:
            raise ValueError("请先使用fit方法拟合数据")
        
        if self.method == NormalizationMethod.Z_SCORE:
            # Z-score反归一化
            # 首先将[0,1]区间还原到Z-score范围
            scaled_back = self._inverse_scale_from_01(normalized_data)
            return scaled_back * self.params['std'] + self.params['mean']
        
        elif self.method == NormalizationMethod.MIN_MAX:
            # 改进区间缩放法反归一化
            return normalized_data * (self.params['max'] - self.params['min']) + self.params['min']
        
        elif self.method == NormalizationMethod.FUZZY:
            # 模糊隶属度反归一化
            # Sigmoid反函数
            result = self.params['midpoint'] - (np.log(1 / normalized_data - 1) / self.params['steepness'])
            return result
        
        elif self.method == NormalizationMethod.DECIMAL_SCALING:
            # 小数定标反归一化
            return normalized_data * self.params['divisor']
        
        else:
            raise ValueError(f"未知的归一化方法: {self.method}")
    
    def fit_transform(self, data: Union[List[float], np.ndarray]) -> np.ndarray:
        """拟合并转换数据
        
        Args:
            data: 原始数据
            
        Returns:
            归一化后的数据
        """
        self.fit(data)
        return self.transform(data)
    
    def _scale_to_01(self, z_scores: np.ndarray) -> np.ndarray:
        """将Z-score结果缩放到[0,1]区间
        
        Args:
            z_scores: Z-score归一化结果
            
        Returns:
            [0,1]区间内的值
        """
        # 使用改进的Sigmoid函数进行缩放
        return 1 / (1 + np.exp(-z_scores))
    
    def _inverse_scale_from_01(self, scaled_data: np.ndarray) -> np.ndarray:
        """将[0,1]区间值还原到Z-score范围
        
        Args:
            scaled_data: [0,1]区间内的值
            
        Returns:
            Z-score范围的值
        """
        # Sigmoid反函数
        # 避免数值问题
        scaled_data = np.clip(scaled_data, 1e-10, 1 - 1e-10)
        return np.log(scaled_data / (1 - scaled_data))
    
    @staticmethod
    def z_score_normalize(data: Union[List[float], np.ndarray]) -> np.ndarray:
        """Z-score标准差归一化（静态方法）
        
        Args:
            data: 原始数据
            
        Returns:
            归一化后的数据
        """
        normalizer = Normalizer(NormalizationMethod.Z_SCORE)
        return normalizer.fit_transform(data)
    
    @staticmethod
    def min_max_normalize(data: Union[List[float], np.ndarray]) -> np.ndarray:
        """改进区间缩放法归一化（静态方法）
        
        Args:
            data: 原始数据
            
        Returns:
            归一化后的数据
        """
        normalizer = Normalizer(NormalizationMethod.MIN_MAX)
        return normalizer.fit_transform(data)
    
    @staticmethod
    def fuzzy_normalize(data: Union[List[float], np.ndarray], 
                        min_threshold: float = 0, 
                        max_threshold: float = 1) -> np.ndarray:
        """模糊隶属度归一化（静态方法）
        
        Args:
            data: 原始数据
            min_threshold: 最小阈值
            max_threshold: 最大阈值
            
        Returns:
            归一化后的数据
        """
        if isinstance(data, list):
            data = np.array(data)
        
        # 线性归一化到[0,1]
        normalized = (data - min_threshold) / (max_threshold - min_threshold)
        # 使用Sigmoid函数进行平滑
        return 1 / (1 + np.exp(-10 * (normalized - 0.5)))
    
    @staticmethod
    def normalize_by_type(data: Union[List[float], np.ndarray], 
                          data_type: str = "cost") -> np.ndarray:
        """根据数据类型选择合适的归一化方法
        
        Args:
            data: 原始数据
            data_type: 数据类型，可选值：
                      "cost" - 成本型指标（越小越好）
                      "benefit" - 效益型指标（越大越好）
                      "safety" - 安全指标（有明确阈值）
                      "delay" - 延迟指标（有行业标准）
            
        Returns:
            归一化后的数据
        """
        if isinstance(data, list):
            data = np.array(data)
        
        if data_type == "cost":
            # 成本型指标：使用改进区间缩放法，并取反（使越小越好变为越大越好）
            normalizer = Normalizer(NormalizationMethod.MIN_MAX)
            normalized = normalizer.fit_transform(data)
            return 1 - normalized  # 取反，使成本越低得分越高
        
        elif data_type == "benefit":
            # 效益型指标：使用改进区间缩放法
            normalizer = Normalizer(NormalizationMethod.MIN_MAX)
            return normalizer.fit_transform(data)
        
        elif data_type == "safety":
            # 安全指标：使用模糊隶属度归一化
            # 假设安全阈值：0-100分，70分以上为安全
            return Normalizer.fuzzy_normalize(data, min_threshold=0, max_threshold=100)
        
        elif data_type == "delay":
            # 延迟指标：使用改进区间缩放法，但需要设置合理的最大延迟
            # 假设最大延迟为100ms
            max_delay = 100.0
            data_clipped = np.clip(data, 0, max_delay)
            normalizer = Normalizer(NormalizationMethod.MIN_MAX)
            normalized = normalizer.fit_transform(data_clipped)
            return 1 - normalized  # 延迟越低越好，所以取反
        
        else:
            # 默认使用改进区间缩放法
            normalizer = Normalizer(NormalizationMethod.MIN_MAX)
            return normalizer.fit_transform(data)
    
    def get_params(self) -> Dict[str, Any]:
        """获取归一化参数
        
        Returns:
            归一化参数字典
        """
        return self.params.copy()


# 创建全局归一化器实例
_default_normalizer = Normalizer()

# 提供便捷函数
def normalize(data: Union[List[float], np.ndarray], 
              method: str = "min_max") -> np.ndarray:
    """便捷归一化函数
    
    Args:
        data: 原始数据
        method: 归一化方法，可选值："z_score", "min_max", "fuzzy"
        
    Returns:
        归一化后的数据
    """
    method_map = {
        "z_score": NormalizationMethod.Z_SCORE,
        "min_max": NormalizationMethod.MIN_MAX,
        "fuzzy": NormalizationMethod.FUZZY
    }
    
    if method not in method_map:
        method = "min_max"
    
    normalizer = Normalizer(method_map[method])
    return normalizer.fit_transform(data)


# 测试代码
if __name__ == "__main__":
    print(" 测试归一化模块")
    
    # 测试数据
    test_data = [10, 20, 30, 40, 50]
    
    print(f"原始数据: {test_data}")
    
    # 测试不同归一化方法
    methods = ["min_max", "z_score", "fuzzy"]
    
    for method in methods:
        result = normalize(test_data, method)
        print(f"{method}归一化: {result}")
    
    print("\n 归一化模块创建完成")

# 兼容性：NormalizationSystem 是 Normalizer 的别名
NormalizationSystem = Normalizer
