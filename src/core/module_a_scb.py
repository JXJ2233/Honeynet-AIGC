"""
SCB因子筛选器 (Security-Cost-Balance Filter)
基于安全、成本、平衡因子筛选候选节点
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
    """节点类型枚举"""
    TERMINAL = "terminal"
    STEINER = "steiner_candidate"
    GATEWAY = "gateway"
    HONEYPOT = "honeypot"
    EXPERT = "expert"


@dataclass
class SCBScore:
    """SCB分数数据类"""
    node_id: str
    security_score: float
    cost_score: float
    balance_score: float
    total_score: float

    def __float__(self):
        return self.total_score

    def __str__(self):
        return f"SCBScore(node={self.node_id}, total={self.total_score:.3f})"


class SCBFilter:
    """SCB因子筛选器类"""

    def __init__(self, config_manager=None, **kwargs):
        """
        初始化SCB筛选器

        :param config_manager: 配置管理器（可选）
        :param kwargs: 可覆盖的参数
            - security_weight: 安全因子权重（默认0.4）
            - cost_weight: 成本因子权重（默认0.3）
            - balance_weight: 平衡因子权重（默认0.3）
            - keep_ratio: 保留比例（默认0.6）
        """
        self.config_manager = config_manager

        # 权重配置（支持外部传入）
        self.security_weight = kwargs.get('security_weight', 0.4)
        self.cost_weight = kwargs.get('cost_weight', 0.3)
        self.balance_weight = kwargs.get('balance_weight', 0.3)

        # 确保权重和为1
        total = self.security_weight + self.cost_weight + self.balance_weight
        if total > 0:
            self.security_weight /= total
            self.cost_weight /= total
            self.balance_weight /= total

        # 保留比例（保留前 keep_ratio 的节点）
        self.keep_ratio = kwargs.get('keep_ratio', 0.6)

        print(" SCBFilter 初始化完成")
        print(f"   安全权重: {self.security_weight:.2f}")
        print(f"   成本权重: {self.cost_weight:.2f}")
        print(f"   平衡权重: {self.balance_weight:.2f}")
        print(f"   保留比例: {self.keep_ratio:.2f}")

    def filter_nodes(self,
                     candidate_nodes: List,
                     terminal_nodes: List,
                     edges: List,
                     attack_vectors: List,
                     existing_deployments: Optional[List] = None,
                     keep_ratio: Optional[float] = None) -> Tuple[List, List[SCBScore]]:
        """
        筛选高潜力蜜罐部署节点

        :param candidate_nodes: 候选节点列表（每个元素应有 id, security_coverage, deployment_cost, cpu_capacity, memory_capacity 等属性）
        :param terminal_nodes: 终端节点列表（用于拓扑关联，当前未直接使用）
        :param edges: 网络边列表（当前未直接使用）
        :param attack_vectors: 攻击向量列表（用于安全因子计算，当前未直接使用）
        :param existing_deployments: 已有部署节点列表（用于避免重复部署，当前未使用）
        :param keep_ratio: 保留比例，若提供则覆盖实例设置
        :return: (筛选后的节点列表, 对应的SCB分数列表)
        """
        print(f" SCB筛选器开始工作:")
        print(f"  候选节点数: {len(candidate_nodes) if candidate_nodes else 0}")
        print(f"  终端节点数: {len(terminal_nodes) if terminal_nodes else 0}")

        if not candidate_nodes:
            print("候选节点为空，返回空结果")
            return [], []

        # 使用传入的保留比例或实例默认值
        ratio = keep_ratio if keep_ratio is not None else self.keep_ratio

        try:
            # 步骤1: 提取各节点的原始指标
            node_attrs = []
            for node in candidate_nodes:
                # 获取节点ID
                node_id = self._extract_id(node)

                # 安全因子原始值（取值范围一般 0~1，越大表示安全覆盖能力越强）
                security_raw = self._extract_security_raw(node)

                # 成本原始值（绝对值，越小越好）
                cost_raw = self._extract_cost_raw(node)

                # 平衡因子原始值（CPU与内存的比值接近1为佳）
                cpu = self._extract_cpu(node)
                memory = self._extract_memory(node)
                balance_raw = 1.0 - abs(cpu - memory) / max(cpu + memory, 0.01)

                node_attrs.append((node, node_id, security_raw, cost_raw, balance_raw))

            # 步骤2: 最大值归一化
            # 安全因子直接使用原始值（假设已在 0~1）
            sec_vals = [attr[2] for attr in node_attrs]
            sec_max = max(sec_vals) if sec_vals else 1.0
            sec_norm = [v / sec_max for v in sec_vals] if sec_max > 0 else [0.0] * len(sec_vals)

            # 成本因子：原始值越小越好，故取倒数后归一化
            cost_raw_vals = [attr[3] for attr in node_attrs]
            # 避免除零
            cost_inv = [1.0 / max(v, 0.1) for v in cost_raw_vals]
            cost_max = max(cost_inv) if cost_inv else 1.0
            cost_norm = [v / cost_max for v in cost_inv] if cost_max > 0 else [0.0] * len(cost_inv)

            # 平衡因子：原始值在 0~1，直接使用
            bal_vals = [attr[4] for attr in node_attrs]
            bal_max = max(bal_vals) if bal_vals else 1.0
            bal_norm = [v / bal_max for v in bal_vals] if bal_max > 0 else [0.0] * len(bal_vals)

            # 步骤3: 计算综合 SCB 分数
            scb_scores = []
            for i, (node, node_id, sec_raw, cost_raw, bal_raw) in enumerate(node_attrs):
                score = (self.security_weight * sec_norm[i] +
                         self.cost_weight * cost_norm[i] +
                         self.balance_weight * bal_norm[i])
                scb_scores.append(SCBScore(
                    node_id=node_id,
                    security_score=sec_norm[i],
                    cost_score=cost_norm[i],
                    balance_score=bal_norm[i],
                    total_score=score
                ))

            # 步骤4: 排序并选择前 keep_ratio 节点
            sorted_scores = sorted(scb_scores, key=lambda s: s.total_score, reverse=True)
            select_count = max(1, int(len(candidate_nodes) * ratio))
            selected_scores = sorted_scores[:select_count]
            selected_nodes = [node for node, _, _, _, _ in node_attrs if
                              self._extract_id(node) in {s.node_id for s in selected_scores}]

            print(f" SCB筛选完成: 从{len(candidate_nodes)}个节点中选择了{len(selected_nodes)}个")
            if selected_scores:
                print(f"  最高SCB分数: {max(s.total_score for s in selected_scores):.3f}, "
                      f"最低: {min(s.total_score for s in selected_scores):.3f}")

            return selected_nodes, selected_scores

        except Exception as e:
            print(f" SCB筛选过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return candidate_nodes, []

    # ------------------ 辅助方法：提取节点属性 ------------------
    @staticmethod
    def _extract_id(node) -> str:
        """提取节点ID"""
        if hasattr(node, 'id'):
            return node.id
        elif isinstance(node, dict) and 'id' in node:
            return node['id']
        return "unknown"

    @staticmethod
    def _extract_security_raw(node) -> float:
        """提取安全因子原始值（0~1），越大表示越安全"""
        if hasattr(node, 'security_coverage'):
            return max(0.0, min(1.0, node.security_coverage))
        elif isinstance(node, dict) and 'security_coverage' in node:
            return max(0.0, min(1.0, node['security_coverage']))
        # 默认中等安全
        return 0.5

    @staticmethod
    def _extract_cost_raw(node) -> float:
        """提取部署成本原始值（正值，越小越好）"""
        if hasattr(node, 'deployment_cost'):
            return max(0.0, node.deployment_cost)
        elif isinstance(node, dict) and 'deployment_cost' in node:
            return max(0.0, node['deployment_cost'])
        return 1000.0  # 默认高成本

    @staticmethod
    def _extract_cpu(node) -> float:
        """提取CPU容量（正整数）"""
        if hasattr(node, 'cpu_capacity'):
            return float(node.cpu_capacity)
        elif isinstance(node, dict) and 'cpu_capacity' in node:
            return float(node['cpu_capacity'])
        return 1.0

    @staticmethod
    def _extract_memory(node) -> float:
        """提取内存容量（正整数）"""
        if hasattr(node, 'memory_capacity'):
            return float(node.memory_capacity)
        elif isinstance(node, dict) and 'memory_capacity' in node:
            return float(node['memory_capacity'])
        return 1.0


# 为兼容性提供简单的节点类（已增加 honeypot_capability 属性）
class Node:
    def __init__(self, node_id, node_type=NodeType.TERMINAL, honeypot_capability=False, **kwargs):
        """
        节点类构造函数

        :param node_id: 节点ID
        :param node_type: 节点类型（NodeType枚举）
        :param honeypot_capability: 是否具有蜜罐能力（默认为 False）
        :param kwargs: 其他属性（如 security_coverage, deployment_cost, cpu_capacity, memory_capacity 等）
        """
        self.id = node_id
        self.type = node_type
        self.honeypot_capability = honeypot_capability
        for key, value in kwargs.items():
            setattr(self, key, value)


if __name__ == "__main__":
    # 测试示例
    candidate_nodes = [
        Node(f"Node{i}", NodeType.STEINER, honeypot_capability=(i % 2 == 0),
             security_coverage=0.3 + i * 0.1,
             deployment_cost=800 + i * 200,
             cpu_capacity=1.0 + i * 0.1,
             memory_capacity=1.0 - i * 0.05)
        for i in range(10)
    ]

    scb_filter = SCBFilter()
    filtered, scores = scb_filter.filter_nodes(candidate_nodes, [], [], [])
    print(f"\n测试完成，筛选出 {len(filtered)} 个节点")
    # 检查蜜罐能力是否保留
    if filtered:
        print(f"第一个筛选后节点 {filtered[0].id} 的蜜罐能力: {filtered[0].honeypot_capability}")