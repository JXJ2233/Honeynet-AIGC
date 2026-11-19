#!/usr/bin/env python3
"""
Random-K 算法实现
随机选择K个节点作为蜜罐部署位置
"""

import random
from typing import List, Dict, Any
import numpy as np


class RandomKAlgorithm:
    """Random-K 算法类"""
    
    def __init__(self, k: int = 5, random_seed: int = 42):
        self.k = k
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
    
    def select_nodes(self, steiner_candidates: List[Dict]) -> List[Dict]:
        if not steiner_candidates:
            return []
        if len(steiner_candidates) <= self.k:
            return steiner_candidates.copy()
        return random.sample(steiner_candidates, self.k)


class RandomKBenchmark:
    """Random-K 基准测试类"""
    
    def __init__(self, num_trials: int = 10, random_seed: int = 42):
        self.num_trials = num_trials
        self.random_seed = random_seed
