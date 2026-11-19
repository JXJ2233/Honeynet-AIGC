"""
GA遗传算法优化（Genetic Algorithm for Deployment Optimization）

输入:
    candidate_nodes: list of str, 候选部署位置（斯坦纳树上的节点）
    network_graph: networkx.Graph, 网络拓扑
    detection_models: dict, 各节点检测模型（用于评估检测能力）
    objective_weights: dict, 目标权重 {cost, latency, coverage, detectability}
    population_size: int, 种群大小（默认100）
    generations: int, 进化代数（默认500）
    crossover_rate: float, 交叉概率（默认0.8）
    mutation_rate: float, 变异概率（默认0.1）

过程:
    1. 初始化种群：随机选择子集作为蜜罐部署方案
    2. 适应度函数：
        fitness = w1*(1 - deployment_cost) + w2*(1 - avg_detection_latency) 
                 + w3*coverage_score + w4*detectability_score
    3. 选择（轮盘赌或锦标赛）、交叉（单点/两点）、变异（位翻转）
    4. 精英保留（保留最优个体）
    5. 迭代直到达到最大代数或收敛
    6. 输出最优部署方案及其性能指标

输出:
    best_deployment: list of str, 最优的蜜罐部署节点ID列表
    best_fitness: float, 最优适应度值
    convergence_curve: list, 每代最佳适应度（用于绘图）
    tradeoff_metrics: dict, 包含成本、时延、覆盖率、检测率等详细指标
"""

"""
GA遗传算法优化（Genetic Algorithm for Deployment Optimization）

算法步骤：
1. 输入候选节点列表（由OSE输出）、网络拓扑图、检测模型、目标权重。
2. 初始化种群：随机选择子集作为蜜罐部署方案（二进制编码）。
3. 适应度函数：
   fitness = w1*(1 - deployment_cost) + w2*(1 - avg_detection_latency)
            + w3*coverage_score + w4*detectability_score
4. 选择：锦标赛选择。
5. 交叉：单点交叉（概率 crossover_rate）。
6. 变异：位翻转（概率 mutation_rate）。
7. 精英保留：保留 elite_ratio 的最优个体。
8. 迭代直到达到最大代数或收敛。
9. 输出最优部署方案及其性能指标。
"""

"""
GA遗传算法优化（Genetic Algorithm for Deployment Optimization）
增加退让地带机制（backup zone）
"""

import numpy as np
import random
from typing import List, Tuple, Dict, Any

# 条件导入租户隔离约束（若不存在则提供空实现）
try:
    from src.utils.constraints import TenantIsolationConstraint
except ImportError:
    class TenantIsolationConstraint:
        def __init__(self, tenant_id=None, host_tenant_map=None):
            pass
        def is_satisfied(self, selected_nodes):
            return True


class GASolver:
    """
    遗传算法求解器，用于优化蜜罐部署方案
    """

    def __init__(self, network: Any, terminals: List[str], candidates: List[str], config: Dict = None):
        """
        初始化遗传算法求解器

        Args:
            network: 网络拓扑图（networkx.Graph）
            terminals: 终端节点ID列表
            candidates: 候选部署节点ID列表（斯坦纳树上的节点）
            config: 配置字典，包含以下可选键：
                - population_size: int, 种群大小（默认100）
                - generations: int, 进化代数（默认50）
                - crossover_rate: float, 交叉概率（默认0.8）
                - mutation_rate: float, 变异概率（默认0.1）
                - elite_ratio: float, 精英保留比例（默认0.1）
                - objective_weights: dict, 目标权重（默认 {'cost':0.25, 'latency':0.25, 'coverage':0.25, 'detectability':0.25}）
                - coverage_threshold: int, 覆盖距离阈值（默认2）
                - tenant_id: str, 租户ID（默认 'default_tenant'）
                - host_tenant_map: dict, 主机到租户的映射（默认 {}）
                - backup_weight: float, 退让地带惩罚权重（默认0.0）
                - backup_radius: int, 退让地带半径（默认2）
        """
        self.network = network
        self.terminals = terminals
        self.candidates = candidates
        self.config = config or {}

        # 遗传算法参数
        self.population_size = self.config.get('population_size', 100)
        self.generations = self.config.get('generations', 50)
        self.crossover_rate = self.config.get('crossover_rate', 0.8)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.elite_ratio = self.config.get('elite_ratio', 0.1)
        self.elite_num = int(self.population_size * self.elite_ratio)

        # 适应度权重
        self.weights = self.config.get('objective_weights', {
            'cost': 0.25,
            'latency': 0.25,
            'coverage': 0.25,
            'detectability': 0.25
        })

        # 覆盖距离阈值（跳数）
        self.coverage_threshold = self.config.get('coverage_threshold', 2)

        # 租户隔离约束
        self.tenant_id = self.config.get('tenant_id', 'default_tenant')
        self.host_tenant_map = self.config.get('host_tenant_map', {})
        self.isolation_constraint = TenantIsolationConstraint(
            tenant_id=self.tenant_id,
            host_tenant_map=self.host_tenant_map
        )

        # 退让地带参数
        self.backup_weight = self.config.get('backup_weight', 0.0)
        self.backup_radius = self.config.get('backup_radius', 2)

        # 辅助数据：预计算候选节点的属性（成本、检测能力等）
        self._precompute_node_attributes()
        # 预计算节点间距离矩阵（用于退让地带惩罚）
        self._precompute_distances()

    def _precompute_node_attributes(self):
        """
        预计算每个候选节点的部署成本、检测能力及蜜罐能力
        """
        self.node_cost = {}
        self.node_detectability = {}
        self.node_honeypot = {}  # 新增：记录节点是否具有蜜罐能力
        for node_id in self.candidates:
            # 假设节点有 'deployment_cost' 属性，否则使用默认值1000
            cost = self.network.nodes[node_id].get('deployment_cost', 1000)
            self.node_cost[node_id] = cost
            # 假设节点有 'detectability' 属性，否则使用随机值（0.5~1.0）
            detect = self.network.nodes[node_id].get('detectability', random.uniform(0.5, 1.0))
            self.node_detectability[node_id] = detect
            # 读取蜜罐能力（关键修改）
            self.node_honeypot[node_id] = self.network.nodes[node_id].get('honeypot_capability', False)

        # 预计算每个终端到所有候选节点的最短路径长度（用于时延估计）
        self.distances = {}  # dict: terminal -> {candidate: distance}
        try:
            import networkx as nx
            for term in self.terminals:
                if term not in self.network:
                    continue
                # 使用 networkx 计算单源最短路径
                lengths = nx.single_source_dijkstra_path_length(self.network, term)
                self.distances[term] = {node: lengths.get(node, float('inf')) for node in self.candidates}
        except ImportError:
            # 如果没有 networkx，使用简单距离估计（实际应确保已安装）
            print("  networkx 未安装，使用默认距离 1")
            for term in self.terminals:
                self.distances[term] = {node: 1 for node in self.candidates}

    def _precompute_distances(self):
        """
        预计算所有候选节点之间的最短路径长度，用于退让地带惩罚。
        """
        try:
            import networkx as nx
            self.candidate_dist_matrix = {}
            for node in self.candidates:
                lengths = nx.single_source_dijkstra_path_length(self.network, node)
                self.candidate_dist_matrix[node] = {c: lengths.get(c, float('inf')) for c in self.candidates}
        except ImportError:
            # 如果没有 networkx，使用简单估计（跳数为1）
            self.candidate_dist_matrix = {}
            for u in self.candidates:
                self.candidate_dist_matrix[u] = {v: 1 if u != v else 0 for v in self.candidates}

    def optimize(self) -> Tuple[List[str], float]:
        """
        运行遗传算法，返回最优部署方案及其适应度

        Returns:
            Tuple[List[str], float]: (选中的节点ID列表, 最佳适应度)
        """
        print(" 开始遗传算法优化")
        print(f"  候选节点数: {len(self.candidates)}")
        print(f"  终端节点数: {len(self.terminals)}")
        print(f"  种群大小: {self.population_size}")
        print(f"  最大代数: {self.generations}")
        if self.backup_weight > 0:
            print(f"  退让地带惩罚权重: {self.backup_weight}, 半径: {self.backup_radius}")

        gene_length = len(self.candidates)

        # 1. 初始化种群
        population = [self._random_chromosome(gene_length) for _ in range(self.population_size)]

        # 2. 评估初始种群
        fitness = [self._evaluate_fitness(chrom) for chrom in population]

        # 记录最佳适应度和个体
        best_fitness = max(fitness)
        best_index = np.argmax(fitness)
        best_chrom = population[best_index].copy()
        print(f"  初始最佳适应度: {best_fitness:.4f}")

        # 3. 进化迭代
        for gen in range(self.generations):
            # 排序
            sorted_indices = np.argsort(fitness)[::-1]  # 降序
            population = [population[i] for i in sorted_indices]
            fitness = [fitness[i] for i in sorted_indices]

            # 精英保留
            elites = [pop.copy() for pop in population[:self.elite_num]]

            # 生成新一代
            new_pop = elites.copy()
            while len(new_pop) < self.population_size:
                # 锦标赛选择父代
                parent1 = self._tournament_selection(population, fitness)
                parent2 = self._tournament_selection(population, fitness)

                # 交叉
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()

                # 变异
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1)
                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2)

                new_pop.extend([child1, child2])

            # 截断至种群大小
            population = new_pop[:self.population_size]

            # 评估新种群
            fitness = [self._evaluate_fitness(chrom) for chrom in population]

            # 更新全局最佳
            current_best = max(fitness)
            if current_best > best_fitness:
                best_fitness = current_best
                best_index = np.argmax(fitness)
                best_chrom = population[best_index].copy()
                print(f"  Gen {gen+1}: 发现新最佳适应度 {best_fitness:.4f}")

            # 可选：打印进度
            if (gen + 1) % 10 == 0:
                print(f"  Gen {gen+1}/{self.generations}: 当前最佳适应度 = {max(fitness):.4f}")

        # 4. 解码最优个体
        best_nodes = [self.candidates[i] for i, bit in enumerate(best_chrom) if bit == 1]
        print(f" 遗传算法优化完成:")
        print(f"  最佳适应度: {best_fitness:.4f}")
        print(f"  选中节点数: {len(best_nodes)}")
        print(f"  选中节点: {best_nodes}")

        return best_nodes, best_fitness

    def _random_chromosome(self, length: int) -> List[int]:
        """
        生成随机二进制染色体，确保至少选择一个节点，并且尽量包含至少一个蜜罐节点
        """
        chrom = [random.randint(0, 1) for _ in range(length)]
        # 确保至少有一个节点被选中
        if sum(chrom) == 0:
            chrom[random.randint(0, length - 1)] = 1
        # 可选：如果所有候选节点都没有蜜罐能力，则忽略下面的检查
        # 否则，如果生成的染色体中没有蜜罐节点，且存在蜜罐候选，则强制将某个蜜罐节点设为1
        if any(self.node_honeypot.values()):  # 存在蜜罐候选
            if not any(bit == 1 and self.node_honeypot[self.candidates[i]] for i, bit in enumerate(chrom)):
                # 随机选择一个蜜罐节点，将其设为1
                honeypot_indices = [i for i, nid in enumerate(self.candidates) if self.node_honeypot[nid]]
                if honeypot_indices:
                    idx = random.choice(honeypot_indices)
                    chrom[idx] = 1
        return chrom

    def _tournament_selection(self, pop: List[List[int]], fitness: List[float], k: int = 3) -> List[int]:
        """锦标赛选择"""
        indices = random.sample(range(len(pop)), k)
        best_idx = max(indices, key=lambda i: fitness[i])
        return pop[best_idx].copy()

    def _crossover(self, a: List[int], b: List[int]) -> Tuple[List[int], List[int]]:
        """单点交叉"""
        point = random.randint(1, len(a) - 1)
        child1 = a[:point] + b[point:]
        child2 = b[:point] + a[point:]
        return child1, child2

    def _mutate(self, chrom: List[int]) -> List[int]:
        """位翻转变异，并确保变异后至少有一个蜜罐节点（如果可能）"""
        idx = random.randint(0, len(chrom) - 1)
        chrom[idx] = 1 - chrom[idx]
        # 确保变异后至少有一个1
        if sum(chrom) == 0:
            chrom[random.randint(0, len(chrom) - 1)] = 1
        # 确保至少有一个蜜罐节点（如果存在蜜罐候选）
        if any(self.node_honeypot.values()):
            if not any(bit == 1 and self.node_honeypot[self.candidates[i]] for i, bit in enumerate(chrom)):
                # 如果没有蜜罐节点，则随机将一个蜜罐节点设为1
                honeypot_indices = [i for i, nid in enumerate(self.candidates) if self.node_honeypot[nid]]
                if honeypot_indices:
                    idx = random.choice(honeypot_indices)
                    chrom[idx] = 1
        return chrom

    def _evaluate_fitness(self, individual: List[int]) -> float:
        """
        评估个体的适应度（包含退让地带惩罚）

        Args:
            individual: 二进制列表，1表示选择对应候选节点

        Returns:
            float: 适应度值（越大越好），如果违反约束则返回0
        """
        # 解码选中节点
        selected_nodes = [self.candidates[i] for i, bit in enumerate(individual) if bit == 1]

        # 如果没有选中任何节点，适应度为0
        if not selected_nodes:
            return 0.0

        # 【新增】强制至少一个蜜罐节点
        # 如果存在蜜罐候选节点但当前解中没有蜜罐节点，则给予极低适应度，使其被淘汰
        if any(self.node_honeypot.values()):
            if not any(self.node_honeypot[node] for node in selected_nodes):
                return 1e-6   # 极小的正数，确保该个体不会被选中

        # 租户隔离约束检查
        if not self.isolation_constraint.is_satisfied(selected_nodes):
            return 0.0

        # 计算各项指标
        cost_score = self._calculate_cost_score(selected_nodes)
        latency_score = self._calculate_latency_score(selected_nodes)
        coverage_score = self._calculate_coverage_score(selected_nodes)
        detectability_score = self._calculate_detectability_score(selected_nodes)

        # 基础适应度（加权求和）
        base_fitness = (self.weights.get('cost', 0.25) * cost_score +
                        self.weights.get('latency', 0.25) * latency_score +
                        self.weights.get('coverage', 0.25) * coverage_score +
                        self.weights.get('detectability', 0.25) * detectability_score)

        # 退让地带惩罚：若两个选中节点的距离 <= backup_radius，则扣除惩罚
        if self.backup_weight > 0 and len(selected_nodes) > 1:
            penalty = 0.0
            # 遍历所有节点对（避免重复计算）
            for i in range(len(selected_nodes)):
                node_i = selected_nodes[i]
                for j in range(i + 1, len(selected_nodes)):
                    node_j = selected_nodes[j]
                    dist = self.candidate_dist_matrix.get(node_i, {}).get(node_j, float('inf'))
                    if dist <= self.backup_radius:
                        # 惩罚与半径成反比（距离越近惩罚越大）
                        penalty += self.backup_weight * (self.backup_radius - dist + 1)
            fitness = max(0.0, base_fitness - penalty)
        else:
            fitness = base_fitness

        return fitness

    def _calculate_cost_score(self, selected_nodes: List[str]) -> float:
        """
        计算成本得分（归一化后，成本越低得分越高）
        """
        total_cost = sum(self.node_cost.get(node, 1000) for node in selected_nodes)
        # 假设最大成本为所有候选节点成本之和，最小为0
        max_possible_cost = sum(self.node_cost.values())
        if max_possible_cost == 0:
            return 1.0  # 避免除零
        # 成本得分 = 1 - (实际成本 / 最大成本)，但确保不出现负数
        score = max(0.0, 1.0 - total_cost / max_possible_cost)
        return score

    def _calculate_latency_score(self, selected_nodes: List[str]) -> float:
        """
        计算检测时延得分：每个终端到最近部署节点的最短路径长度越小越好
        """
        if not self.terminals:
            return 1.0  # 无终端，默认满分

        total_distance = 0.0
        for term in self.terminals:
            if term not in self.distances:
                continue
            # 找到该终端到所有选中节点的最短距离
            min_dist = min(self.distances[term].get(node, float('inf')) for node in selected_nodes)
            # 若无法到达，给予很大惩罚（距离设为无穷大）
            if min_dist == float('inf'):
                total_distance += 1e6
            else:
                total_distance += min_dist

        # 归一化：假设最大距离为网络直径（可预先计算或使用估计值）
        # 这里简单使用候选节点到终端的最大距离作为分母
        max_distance = 1.0
        if hasattr(self, '_max_distance'):
            max_distance = self._max_distance
        else:
            # 计算候选节点到终端的最大距离（用于归一化）
            all_dists = []
            for term in self.terminals:
                for node in self.candidates:
                    d = self.distances.get(term, {}).get(node, float('inf'))
                    if d != float('inf'):
                        all_dists.append(d)
            if all_dists:
                max_distance = max(all_dists)
            else:
                max_distance = 1.0
            self._max_distance = max_distance

        # 时延得分 = 1 - (平均距离 / 最大距离)
        avg_distance = total_distance / len(self.terminals)
        score = max(0.0, 1.0 - avg_distance / max_distance)
        return score

    def _calculate_coverage_score(self, selected_nodes: List[str]) -> float:
        """
        计算覆盖率得分：部署节点能够覆盖的终端节点比例
        这里定义：如果一个终端到任一部署节点的距离 <= threshold 则认为被覆盖
        """
        if not self.terminals:
            return 1.0

        covered = 0
        for term in self.terminals:
            for node in selected_nodes:
                dist = self.distances.get(term, {}).get(node, float('inf'))
                if dist <= self.coverage_threshold:
                    covered += 1
                    break
        return covered / len(self.terminals)

    def _calculate_detectability_score(self, selected_nodes: List[str]) -> float:
        """
        计算检测能力得分：部署节点的平均检测能力（归一化）
        """
        if not selected_nodes:
            return 0.0
        total_detect = sum(self.node_detectability.get(node, 0.5) for node in selected_nodes)
        avg_detect = total_detect / len(selected_nodes)
        return avg_detect  # 已经是0-1范围


if __name__ == "__main__":
    # 简单测试（需安装networkx）
    try:
        import networkx as nx
        G = nx.Graph()
        G.add_node('A', deployment_cost=100, detectability=0.9, honeypot_capability=True)
        G.add_node('B', deployment_cost=200, detectability=0.7, honeypot_capability=False)
        G.add_node('C', deployment_cost=150, detectability=0.8, honeypot_capability=True)
        G.add_edge('A', 'B', weight=2)
        G.add_edge('B', 'C', weight=3)
        terminals = ['A', 'C']
        candidates = ['A', 'B', 'C']
        config = {'population_size': 20, 'generations': 10, 'backup_weight': 0.1, 'backup_radius': 2}
        solver = GASolver(G, terminals, candidates, config)
        best_nodes, best_fitness = solver.optimize()
        print("最优部署:", best_nodes)
        print("最佳适应度:", best_fitness)
    except ImportError:
        print("需安装networkx以运行测试")

# 向后兼容别名
GeneticAlgorithmSolver = GASolver