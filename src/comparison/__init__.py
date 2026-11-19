"""
对比算法模块
"""

try:
    from .random_k import RandomKAlgorithm, RandomKBenchmark
    from .k_medoids import KMedoidsAlgorithm
    from .benchmark import AlgorithmBenchmark
    from .visualizer import ComparisonVisualizer
    print("[OK] 对比算法模块导入成功")
except ImportError as e:
    print(f"[WARNING]  对比算法模块导入失败: {e}")
    # 提供占位类
    class RandomKAlgorithm:
        def __init__(self, k=5):
            self.k = k
        def select_nodes(self, nodes):
            import random
            return random.sample(nodes, min(self.k, len(nodes))) if nodes else []
    
    class RandomKBenchmark:
        def __init__(self, num_trials=10):
            self.num_trials = num_trials
    
    class KMedoidsAlgorithm:
        def __init__(self, k=5):
            self.k = k
        def select_nodes(self, nodes):
            import random
            return random.sample(nodes, min(self.k, len(nodes))) if nodes else []
    
    class AlgorithmBenchmark:
        def __init__(self):
            pass
    
    class ComparisonVisualizer:
        def __init__(self):
            pass

__all__ = [
    'RandomKAlgorithm',
    'RandomKBenchmark',
    'KMedoidsAlgorithm',
    'AlgorithmBenchmark',
    'ComparisonVisualizer'
]
