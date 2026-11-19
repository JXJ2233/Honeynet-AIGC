# src/core/path_perturbation.py

"""
动态路径扰动模块

根据网络负载、攻击者行为以及蜜罐状态，动态调整斯坦纳树中边的权重，
引导攻击路径发生偏移，提升蜜罐系统的主动防御能力。
"""

import random
import numpy as np
from typing import Dict, List, Tuple, Optional
import networkx as nx


class PathPerturbation:
    """
    动态路径扰动控制器

    维护网络拓扑的当前状态，根据负载和攻击行为计算边权重的调整量，
    返回调整后的边权重字典。
    """

    def __init__(self,
                 base_graph: nx.Graph,
                 perturbation_strength: float = 0.3,
                 load_threshold: float = 0.7,
                 behavior_influence: float = 0.4,
                 random_factor: float = 0.1):
        """
        初始化扰动控制器

        :param base_graph: 基础网络拓扑（无向图，边有'weight'属性）
        :param perturbation_strength: 最大相对权重增加比例
        :param load_threshold: 负载阈值，超过后开始增加出边权重
        :param behavior_influence: 攻击行为对权重的放大系数
        :param random_factor: 随机扰动的幅度（增加不可预测性）
        """
        self.base_graph = base_graph
        self.perturbation_strength = perturbation_strength
        self.load_threshold = load_threshold
        self.behavior_influence = behavior_influence
        self.random_factor = random_factor

    def update_weights(self,
                       load_vector: Dict[str, float],
                       attack_path: List[str],
                       detection_history: List[Tuple[str, str, float]]) -> Dict[Tuple[str, str], float]:
        """
        根据当前状态更新所有边的权重

        :param load_vector: 节点负载字典 {node_id: load (0~1)}
        :param attack_path: 当前攻击路径的节点列表（从起点到当前节点）
        :param detection_history: 检测历史记录，每个元素为 (source, target, confidence)
        :return: 调整后的边权重字典 {(u, v): new_weight}
        """
        adjusted_weights = {}
        for u, v, data in self.base_graph.edges(data=True):
            base_weight = data.get('weight', 1.0)

            # 1. 基于节点负载的惩罚
            load_penalty = self._compute_load_penalty(u, v, load_vector)

            # 2. 基于攻击行为的惩罚
            behavior_penalty = self._compute_behavior_penalty(u, v, attack_path, detection_history)

            # 3. 随机扰动（增加不可预测性）
            random_perturb = random.uniform(-self.random_factor, self.random_factor)

            # 综合调整因子 (≥1表示增加权重，<1表示减少)
            factor = 1.0 + load_penalty + behavior_penalty + random_perturb
            # 确保权重不会过小（最小为0.1）
            new_weight = base_weight * max(0.1, factor)

            adjusted_weights[(u, v)] = new_weight
        return adjusted_weights

    def _compute_load_penalty(self, u: str, v: str, load_vector: Dict[str, float]) -> float:
        """
        根据节点负载计算惩罚因子

        如果某节点负载过高，则增加以该节点为起点的边的权重，诱导攻击者绕行。
        :return: 惩罚值（0 ~ perturbation_strength）
        """
        penalty = 0.0
        for node in [u, v]:
            load = load_vector.get(node, 0.0)
            if load > self.load_threshold:
                # 负载越高，惩罚越大
                penalty += (load - self.load_threshold) / (1.0 - self.load_threshold) * self.perturbation_strength
        return penalty

    def _compute_behavior_penalty(self,
                                  u: str, v: str,
                                  attack_path: List[str],
                                  detection_history: List[Tuple[str, str, float]]) -> float:
        """
        根据攻击者行为计算惩罚因子

        - 如果边位于当前攻击路径上，且攻击者已表现出高置信度的检测，则增加该边的权重（使其更难走）。
        - 如果攻击者刚刚经过某条边，则临时提高该边的权重，引导其走向其他方向。
        """
        penalty = 0.0

        # 当前攻击路径上的边：路径上连续节点对
        path_edges = set()
        for i in range(len(attack_path) - 1):
            path_edges.add((attack_path[i], attack_path[i+1]))

        if (u, v) in path_edges or (v, u) in path_edges:
            # 攻击者刚刚走过这条边，增加权重，尝试让其转向
            penalty += self.perturbation_strength * 0.5

        # 历史检测高置信度边：如果某次检测显示该边是高危，也增加权重
        for src, tgt, conf in detection_history:
            if (src == u and tgt == v) or (src == v and tgt == u):
                if conf > 0.8:
                    penalty += self.perturbation_strength * self.behavior_influence

        return penalty


def dynamic_perturbation(steiner_tree: nx.Graph,
                         load_vector: Dict[str, float],
                         attack_path: List[str],
                         detection_history: List[Tuple[str, str, float]],
                         perturbation_strength: float = 0.3,
                         load_threshold: float = 0.7,
                         behavior_influence: float = 0.4,
                         random_factor: float = 0.1) -> Dict[Tuple[str, str], float]:
    """
    简化的动态扰动接口（兼容原有代码结构）

    直接返回调整后的边权重字典。

    :param steiner_tree: 斯坦纳树（网络图）
    :param load_vector: 节点负载字典
    :param attack_path: 当前攻击路径节点列表
    :param detection_history: 检测历史记录
    :param perturbation_strength: 扰动强度
    :param load_threshold: 负载阈值
    :param behavior_influence: 行为影响系数
    :param random_factor: 随机因子
    :return: 调整后的边权重字典
    """
    controller = PathPerturbation(
        base_graph=steiner_tree,
        perturbation_strength=perturbation_strength,
        load_threshold=load_threshold,
        behavior_influence=behavior_influence,
        random_factor=random_factor
    )
    return controller.update_weights(load_vector, attack_path, detection_history)


# 示例用法（如果直接运行此文件）
if __name__ == "__main__":
    # 创建一个简单的图用于测试
    G = nx.Graph()
    G.add_edge('A', 'B', weight=1.0)
    G.add_edge('B', 'C', weight=1.0)
    G.add_edge('C', 'D', weight=1.0)
    G.add_edge('A', 'D', weight=2.0)

    load = {'B': 0.9, 'C': 0.5}
    path = ['A', 'B', 'C']
    history = [('B', 'C', 0.95)]

    new_weights = dynamic_perturbation(G, load, path, history)
    print("Adjusted weights:", new_weights)