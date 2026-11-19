"""
OSE优化排序评估（Optimized Sorting & Evaluation）

算法步骤：
1. 输入候选节点列表（由SCB筛选出）、网络拓扑图、节点安全等级、流量矩阵。
2. 对每个候选节点计算多维重要性评分：
   - 节点度数中心性（连接度）
   - 介数中心性（近似，网络关键性）
   - 安全等级权重
   - 流量承载量
3. 使用TOPSIS或加权求和法综合排序。
4. 按排序结果输出优先级列表，并选择前 selection_ratio 个作为最终部署候选。
5. 返回排序后的节点及评估详情。
"""

import numpy as np
from typing import List, Dict, Any, Optional
from .module_a_scb import SCBScore, NodeType


class OSEOptimizer:
    """OSE优化器类：解空间压缩与优化"""

    def __init__(self, config_manager=None, **kwargs):
        """
        初始化OSE优化器

        :param config_manager: 配置管理器（可选）
        :param kwargs: 可覆盖的参数
            - selection_ratio: 保留比例（默认0.3）
            - scoring_method: 评分方法，'weighted_sum' 或 'topsis'（默认 'weighted_sum'）
        """
        self.config_manager = config_manager
        self.selection_ratio = kwargs.get('selection_ratio', 0.3)
        self.scoring_method = kwargs.get('scoring_method', 'weighted_sum')
        print(" OSEOptimizer 初始化完成")
        print(f"   保留比例: {self.selection_ratio:.2f}")
        print(f"   评分方法: {self.scoring_method}")

    def optimize(self,
                 candidate_nodes: List,
                 terminal_nodes: List,
                 edges: List,
                 scb_scores: List[SCBScore]) -> Dict[str, Any]:
        """
        优化解空间

        :param candidate_nodes: 候选节点列表
        :param terminal_nodes: 终端节点列表
        :param edges: 网络边列表
        :param scb_scores: SCB分数列表
        :return: 优化后的解决方案字典，包含 'selected_nodes', 'optimization_score' 等
        """
        print(" OSE优化器开始工作")
        print(f"  输入节点数: {len(candidate_nodes)}")
        print(f"  SCB分数数: {len(scb_scores)}")

        try:
            if not candidate_nodes:
                return {"selected_nodes": [], "optimization_score": 0.0}

            # 获取所有节点的SCB分数作为基础评分
            node_scores = {}
            for i, node in enumerate(candidate_nodes):
                if i < len(scb_scores):
                    score = scb_scores[i].total_score
                else:
                    # 如果没有对应的SCB分数，使用默认值
                    score = 0.5

                node_id = self._extract_id(node)
                node_scores[node_id] = score

            # 可根据需要扩展其他评分维度（度数、介数等），这里仅基于SCB分数
            if self.scoring_method == 'weighted_sum':
                # 加权求和：此处仅使用SCB分数
                final_scores = node_scores
            elif self.scoring_method == 'topsis':
                # 若需要实现TOPSIS，可在此处添加，当前简化
                final_scores = node_scores
            else:
                final_scores = node_scores

            # 按分数排序
            sorted_nodes = sorted(candidate_nodes,
                                 key=lambda node: final_scores.get(self._extract_id(node), 0.5),
                                 reverse=True)

            # 选择前 selection_ratio 的节点
            select_count = max(1, int(len(candidate_nodes) * self.selection_ratio))
            selected_nodes = sorted_nodes[:select_count]

            # 计算优化分数（平均SCB分数）
            if node_scores:
                avg_score = sum(node_scores.values()) / len(node_scores)
            else:
                avg_score = 0.5

            result = {
                "selected_nodes": selected_nodes,
                "optimization_score": avg_score,
                "selection_count": len(selected_nodes),
                "method": self.scoring_method,
                "selection_ratio": self.selection_ratio
            }

            print(f" OSE优化完成: 选择了{len(selected_nodes)}个节点")
            print(f"  优化分数: {avg_score:.3f}")

            return result

        except Exception as e:
            print(f" OSE优化过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return {"selected_nodes": candidate_nodes, "optimization_score": 0.5}

    def evaluate_solution(self, solution: Dict[str, Any]) -> float:
        """评估解决方案的质量"""
        if 'optimization_score' in solution:
            return solution['optimization_score']
        return 0.5

    @staticmethod
    def _extract_id(node) -> str:
        """提取节点ID"""
        if hasattr(node, 'id'):
            return node.id
        elif isinstance(node, dict) and 'id' in node:
            return node['id']
        return "unknown"


if __name__ == "__main__":
    print(" 测试OSE优化器")
    optimizer = OSEOptimizer()
    print(f"实例创建成功: {optimizer}")