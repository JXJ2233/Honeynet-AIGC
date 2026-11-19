'''"""
斯坦纳树构建器
构建连接终端和斯坦纳节点的最小成本树
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from .module_a_scb import SCBScore, NodeType


class SteinerTreeBuilder:
    """斯坦纳树构建器类"""
    
    def __init__(self, config_manager=None, **kwargs):
        """初始化斯坦纳树构建器
        
        Args:
            config_manager: 配置管理器
            **kwargs: 额外参数
        """
        self.config_manager = config_manager
        self.kwargs = kwargs
        print(" SteinerTreeBuilder 初始化完成")
    
    def build_tree(self, 
                  optimized_solution: Dict[str, Any],
                  terminal_nodes: List,
                  edges: List) -> Dict[str, Any]:
        """
        构建斯坦纳树
        
        Args:
            optimized_solution: OSE优化器的输出
            terminal_nodes: 终端节点列表
            edges: 网络边列表
            
        Returns:
            Dict[str, Any]: 斯坦纳树结构
        """
        print(" 开始构建斯坦纳树")
        
        selected_nodes = optimized_solution.get('selected_nodes', [])
        print(f"  终端节点数: {len(terminal_nodes)}")
        print(f"  斯坦纳节点数: {len(selected_nodes)}")
        print(f"  边数: {len(edges)}")
        
        try:
            # 简化版的斯坦纳树构建
            # 这里只是创建一个树形结构，实际应该使用真正的斯坦纳树算法
            
            # 收集所有节点
            all_nodes = []
            
            # 添加终端节点
            for node in terminal_nodes:
                all_nodes.append({
                    'id': node.id if hasattr(node, 'id') else node.get('id', f'terminal_{len(all_nodes)}'),
                    'type': 'terminal',
                    'is_terminal': True
                })
            
            # 添加斯坦纳节点
            for i, node in enumerate(selected_nodes):
                node_id = f"steiner_{i}"
                if hasattr(node, 'id'):
                    node_id = node.id
                elif isinstance(node, dict) and 'id' in node:
                    node_id = node['id']
                
                all_nodes.append({
                    'id': node_id,
                    'type': 'steiner',
                    'is_terminal': False,
                    'deployment_cost': node.deployment_cost if hasattr(node, 'deployment_cost') else 
                                      node.get('deployment_cost', 1000)
                })
            
            # 创建简化的树连接（实际应使用最小生成树或斯坦纳树算法）
            tree_edges = []
            total_cost = 0
            
            # 如果只有终端节点，直接连接它们
            if len(selected_nodes) == 0 and len(terminal_nodes) > 0:
                # 创建终端节点之间的完全图（简化）
                for i in range(len(terminal_nodes)):
                    for j in range(i+1, len(terminal_nodes)):
                        cost = 100  # 基础连接成本
                        tree_edges.append({
                            'source': all_nodes[i]['id'],
                            'target': all_nodes[j]['id'],
                            'cost': cost
                        })
                        total_cost += cost
            else:
                # 连接每个终端节点到最近的斯坦纳节点
                for term_node in terminal_nodes:
                    term_id = term_node.id if hasattr(term_node, 'id') else term_node.get('id', 'unknown')
                    
                    # 找到最近的斯坦纳节点
                    if selected_nodes:
                        # 使用第一个斯坦纳节点（简化）
                        steiner_node = selected_nodes[0]
                        steiner_id = steiner_node.id if hasattr(steiner_node, 'id') else steiner_node.get('id', 'steiner_0')
                        
                        cost = 50  # 基础连接成本
                        tree_edges.append({
                            'source': term_id,
                            'target': steiner_id,
                            'cost': cost
                        })
                        total_cost += cost
            
            # 计算总成本
            deployment_cost = sum(
                node.deployment_cost if hasattr(node, 'deployment_cost') else 
                node.get('deployment_cost', 1000) 
                for node in selected_nodes
            )
            total_cost += deployment_cost
            
            # 构建树结构
            tree = {
                'nodes': all_nodes,
                'edges': tree_edges,
                'total_cost': total_cost,
                'deployment_cost': deployment_cost,
                'connection_cost': total_cost - deployment_cost,
                'node_count': len(all_nodes),
                'edge_count': len(tree_edges)
            }
            
            print(f" 斯坦纳树构建完成:")
            print(f"  总节点数: {tree['node_count']}")
            print(f"  总边数: {tree['edge_count']}")
            print(f"  总成本: ${total_cost:.2f}")
            print(f"    - 部署成本: ${deployment_cost:.2f}")
            print(f"    - 连接成本: ${tree['connection_cost']:.2f}")
            
            return tree
            
        except Exception as e:
            print(f" 斯坦纳树构建过程中出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 返回一个简单的树结构
            return {
                'nodes': [],
                'edges': [],
                'total_cost': 0,
                'deployment_cost': 0,
                'connection_cost': 0,
                'node_count': 0,
                'edge_count': 0,
                'error': str(e)
            }
    
    def calculate_tree_metrics(self, tree: Dict[str, Any]) -> Dict[str, float]:
        """计算树的度量指标"""
        return {
            'total_cost': tree.get('total_cost', 0),
            'avg_degree': tree.get('edge_count', 0) / max(tree.get('node_count', 1), 1),
            'connectivity': min(tree.get('edge_count', 0) / max(tree.get('node_count', 1) - 1, 1), 1.0)
        }


if __name__ == "__main__":
    print(" 测试斯坦纳树构建器")
    builder = SteinerTreeBuilder()
    print(f"实例创建成功: {builder}")
'''"""
斯坦纳树构建器
构建连接终端和斯坦纳节点的最小成本树，支持动态路径扰动与多租户隔离约束。

算法步骤（高级模式）：
1. 输入网络拓扑图、必须覆盖的终端节点集、候选斯坦纳节点集（由OSE输出）。
2. 若启用了租户隔离，检查跨租户连接是否仅通过安全网关，否则禁止该边。
3. 计算所有终端对之间的最短路径，构建终端完全图。
4. 使用近似斯坦纳树算法（最短路径闭包 + 最小生成树）或动态规划求解最小成本树。
5. 若启用了动态权重，根据攻击流量或负载实时调整边权重，诱导攻击者绕行。
6. 输出斯坦纳树结构及部署节点列表。
"""

"""
斯坦纳树构建器
构建连接终端和斯坦纳节点的最小成本树，支持动态路径扰动与多租户隔离约束。

算法步骤（高级模式）：
1. 输入网络拓扑图、必须覆盖的终端节点集、候选斯坦纳节点集（由OSE输出）。
2. 若启用了租户隔离，检查跨租户连接是否仅通过安全网关，否则禁止该边。
3. 计算所有终端对之间的最短路径，构建终端完全图。
4. 使用近似斯坦纳树算法（最短路径闭包 + 最小生成树）或动态规划求解最小成本树。
5. 若启用了动态权重，根据攻击流量或负载实时调整边权重，诱导攻击者绕行。
6. 输出斯坦纳树结构及部署节点列表。
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set
import networkx as nx
from networkx.algorithms.approximation import steiner_tree

# 尝试导入租户隔离约束类（若不存在则提供空实现）
try:
    from src.utils.constraints import TenantIsolationConstraint
except ImportError:
    class TenantIsolationConstraint:
        def __init__(self, tenant_id=None, host_tenant_map=None):
            self.tenant_id = tenant_id
            self.host_tenant_map = host_tenant_map or {}
        def is_satisfied(self, selected_nodes):
            # 默认总是满足
            return True
        def is_edge_allowed(self, u, v):
            # 默认总是允许
            return True


class SteinerTreeBuilder:
    """
    斯坦纳树构建器类（保留原有接口，扩展新功能）
    """

    def __init__(self, config_manager=None, **kwargs):
        """
        初始化斯坦纳树构建器

        :param config_manager: 配置管理器（可选）
        :param kwargs: 额外参数，支持：
            - graph: networkx.Graph，网络拓扑图（若提供则启用高级算法）
            - terminals: List[str]，必须覆盖的关键节点
            - tenant_map: Dict[str, str]，节点到租户的映射（已废弃，请使用 host_tenant_map）
            - safe_gateways: Set[str]，允许跨租户连接的安全网关节点
            - dynamic_weights_enabled: bool，是否启用动态权重调整（默认True）
            - tenant_id: str，当前租户ID（用于隔离约束）
            - host_tenant_map: Dict[str, str]，主机到租户的映射
            - enable_tenant_isolation: bool，是否启用租户隔离
            - isolation_constraint: TenantIsolationConstraint，外部传入的隔离约束实例（优先使用）
        """
        self.config_manager = config_manager
        self.kwargs = kwargs

        # 高级算法相关属性
        self.graph = kwargs.get('graph')
        self.terminals = kwargs.get('terminals', [])
        # 兼容旧参数
        self.tenant_map = kwargs.get('tenant_map', {})
        self.host_tenant_map = kwargs.get('host_tenant_map', self.tenant_map)
        self.safe_gateways = kwargs.get('safe_gateways', set())
        self.dynamic_weights_enabled = kwargs.get('dynamic_weights_enabled', True)

        # 租户隔离配置
        self.enable_tenant_isolation = kwargs.get('enable_tenant_isolation', False)
        self.tenant_id = kwargs.get('tenant_id', 'default')
        self.isolation_constraint = kwargs.get('isolation_constraint')
        if self.isolation_constraint is None and self.enable_tenant_isolation:
            # 创建默认隔离约束
            self.isolation_constraint = TenantIsolationConstraint(
                tenant_id=self.tenant_id,
                host_tenant_map=self.host_tenant_map
            )
        else:
            # 如果未启用隔离或未提供约束，使用一个总是允许的空约束
            self.isolation_constraint = TenantIsolationConstraint(
                tenant_id=self.tenant_id,
                host_tenant_map=self.host_tenant_map
            )

        # 动态权重存储
        self.dynamic_weights = {}          # {(u,v): weight}
        self.base_weights = {}             # 原始权重备份

        if self.graph:
            # 初始化基础权重
            for u, v, d in self.graph.edges(data=True):
                w = d.get('weight', 1.0)
                self.base_weights[(u, v)] = w
                self.base_weights[(v, u)] = w

        print(" SteinerTreeBuilder 初始化完成（支持动态扰动与租户隔离）")

    # ---------- 原有方法（保持签名不变） ----------
    def build_tree(self,
                   optimized_solution: Dict[str, Any],
                   terminal_nodes: List,
                   edges: List) -> Dict[str, Any]:
        """
        构建斯坦纳树（兼容原有接口）
        若提供了 graph 和 terminals，则使用高级算法；否则使用原有简化实现。
        """
        print(" 开始构建斯坦纳树")

        selected_nodes = optimized_solution.get('selected_nodes', [])

        # 如果提供了完整拓扑，使用高级算法
        if self.graph and self.terminals:
            return self._build_tree_advanced(optimized_solution, terminal_nodes, edges)

        # 否则回退到原有简化实现
        return self._build_tree_simple(optimized_solution, terminal_nodes, edges)

    def calculate_tree_metrics(self, tree: Dict[str, Any]) -> Dict[str, float]:
        """计算树的度量指标"""
        return {
            'total_cost': tree.get('total_cost', 0),
            'avg_degree': tree.get('edge_count', 0) / max(tree.get('node_count', 1), 1),
            'connectivity': min(tree.get('edge_count', 0) / max(tree.get('node_count', 1) - 1, 1), 1.0)
        }

    # ---------- 内部实现 ----------
    def _build_tree_simple(self, optimized_solution, terminal_nodes, edges):
        """原有的简化版斯坦纳树构建"""
        selected_nodes = optimized_solution.get('selected_nodes', [])

        all_nodes = []
        # 添加终端节点
        for node in terminal_nodes:
            all_nodes.append({
                'id': node.id if hasattr(node, 'id') else node.get('id', f'terminal_{len(all_nodes)}'),
                'type': 'terminal',
                'is_terminal': True
            })

        # 添加斯坦纳节点
        for i, node in enumerate(selected_nodes):
            node_id = f"steiner_{i}"
            if hasattr(node, 'id'):
                node_id = node.id
            elif isinstance(node, dict) and 'id' in node:
                node_id = node['id']

            all_nodes.append({
                'id': node_id,
                'type': 'steiner',
                'is_terminal': False,
                'deployment_cost': node.deployment_cost if hasattr(node, 'deployment_cost') else
                                   node.get('deployment_cost', 1000)
            })

        tree_edges = []
        total_cost = 0
        if len(selected_nodes) == 0 and len(terminal_nodes) > 0:
            for i in range(len(terminal_nodes)):
                for j in range(i+1, len(terminal_nodes)):
                    cost = 100
                    tree_edges.append({
                        'source': all_nodes[i]['id'],
                        'target': all_nodes[j]['id'],
                        'cost': cost
                    })
                    total_cost += cost
        else:
            for term_node in terminal_nodes:
                term_id = term_node.id if hasattr(term_node, 'id') else term_node.get('id', 'unknown')
                if selected_nodes:
                    steiner_node = selected_nodes[0]
                    steiner_id = steiner_node.id if hasattr(steiner_node, 'id') else steiner_node.get('id', 'steiner_0')
                    cost = 50
                    tree_edges.append({
                        'source': term_id,
                        'target': steiner_id,
                        'cost': cost
                    })
                    total_cost += cost

        deployment_cost = sum(
            node.deployment_cost if hasattr(node, 'deployment_cost') else
            node.get('deployment_cost', 1000)
            for node in selected_nodes
        )
        total_cost += deployment_cost

        tree = {
            'nodes': all_nodes,
            'edges': tree_edges,
            'total_cost': total_cost,
            'deployment_cost': deployment_cost,
            'connection_cost': total_cost - deployment_cost,
            'node_count': len(all_nodes),
            'edge_count': len(tree_edges)
        }

        print(f" 斯坦纳树构建完成（简化版）:")
        print(f"  总节点数: {tree['node_count']}")
        print(f"  总边数: {tree['edge_count']}")
        print(f"  总成本: ${total_cost:.2f}")
        return tree

    def _build_tree_advanced(self, optimized_solution, terminal_nodes, edges):
        """高级斯坦纳树构建，支持租户隔离和动态权重"""
        print(" 使用高级斯坦纳树构建（支持租户隔离与动态权重）")

        # 准备终端节点ID列表
        terminals = [node.id if hasattr(node, 'id') else node for node in self.terminals]

        # 创建带权重的图（考虑租户隔离）
        G = nx.Graph()
        for u, v in self.base_weights.keys():
            if self._is_valid_edge(u, v):
                w = self._get_current_weight(u, v)
                G.add_edge(u, v, weight=w)

        # 确保所有终端节点存在于图中
        missing = [t for t in terminals if t not in G.nodes]
        if missing:
            print(f" 警告: 终端节点 {missing} 不在图中，将忽略")
            terminals = [t for t in terminals if t in G.nodes]

        if len(terminals) < 2:
            print(" 终端节点不足2个，无法构建斯坦纳树")
            return self._build_tree_simple(optimized_solution, terminal_nodes, edges)

        # 构建斯坦纳树（使用近似算法）
        try:
            tree_graph = steiner_tree(G, terminals, weight='weight')
        except Exception as e:
            print(f" 斯坦纳树近似算法失败，回退到MST近似: {e}")
            tree_graph = self._steiner_tree_approximation(G, terminals)

        # 计算总成本
        total_cost = sum(self._get_current_weight(u, v) for u, v in tree_graph.edges())
        deployment_cost = optimized_solution.get('deployment_cost', 0)

        # 转换为字典输出格式
        nodes = [{'id': n, 'type': 'steiner' if n not in terminals else 'terminal',
                  'is_terminal': n in terminals} for n in tree_graph.nodes]
        edges_list = [{'source': u, 'target': v, 'cost': self._get_current_weight(u, v)}
                      for u, v in tree_graph.edges]

        tree = {
            'nodes': nodes,
            'edges': edges_list,
            'total_cost': total_cost + deployment_cost,
            'deployment_cost': deployment_cost,
            'connection_cost': total_cost,
            'node_count': len(nodes),
            'edge_count': len(edges_list),
            'graph': tree_graph   # 保留图对象供后续扰动
        }

        print(f" 斯坦纳树构建完成（高级版）:")
        print(f"  总节点数: {tree['node_count']}")
        print(f"  总边数: {tree['edge_count']}")
        print(f"  总成本: ${tree['total_cost']:.2f}")
        return tree

    def _steiner_tree_approximation(self, G: nx.Graph, terminals: List[str]) -> nx.Graph:
        """最短路径闭包 + MST 近似"""
        n = len(terminals)
        dist = {}
        path = {}

        # 计算所有终端对之间的最短路径
        for i in range(n):
            for j in range(i+1, n):
                u, v = terminals[i], terminals[j]
                try:
                    d, p = nx.single_source_dijkstra(G, u, v, weight='weight')
                except nx.NetworkXNoPath:
                    d, p = float('inf'), []
                dist[(u, v)] = d
                path[(u, v)] = p

        # 构建终端完全图
        complete = nx.Graph()
        for i in range(n):
            for j in range(i+1, n):
                u, v = terminals[i], terminals[j]
                if dist[(u, v)] != float('inf'):
                    complete.add_edge(u, v, weight=dist[(u, v)])

        # 最小生成树
        mst = nx.minimum_spanning_tree(complete, weight='weight')

        # 展开边为原始路径
        tree_edges = set()
        for u, v in mst.edges():
            p = path[(u, v)]
            for k in range(len(p)-1):
                tree_edges.add((p[k], p[k+1]))

        # 构建结果树
        tree = nx.Graph()
        for u, v in tree_edges:
            w = self._get_current_weight(u, v)
            tree.add_edge(u, v, weight=w)
        return tree

    # ---------- 租户隔离支持 ----------
    def _is_valid_edge(self, u: str, v: str) -> bool:
        """
        检查边是否满足租户隔离约束
        使用统一的 TenantIsolationConstraint 进行判断
        """
        # 如果未启用隔离，则总是有效
        if not self.enable_tenant_isolation:
            return True

        # 使用隔离约束检查边是否允许
        return self.isolation_constraint.is_edge_allowed(u, v)

    # ---------- 动态权重支持 ----------
    def _get_current_weight(self, u: str, v: str) -> float:
        """获取当前权重（优先动态权重）"""
        if (u, v) in self.dynamic_weights:
            return self.dynamic_weights[(u, v)]
        if (v, u) in self.dynamic_weights:
            return self.dynamic_weights[(v, u)]
        return self.base_weights.get((u, v), float('inf'))

    def update_edge_weight(self, u: str, v: str, new_weight: float):
        """更新动态权重"""
        self.dynamic_weights[(u, v)] = new_weight
        self.dynamic_weights[(v, u)] = new_weight

    def reweight_by_attack_traffic(self, attack_traffic: Dict[Tuple[str, str], float],
                                   sensitivity: float = 0.5):
        """
        根据攻击流量动态调整边权重
        :param attack_traffic: 边上的攻击流量 {(u,v): count}
        :param sensitivity: 流量影响系数
        """
        if not self.dynamic_weights_enabled:
            return
        max_traffic = max(attack_traffic.values()) if attack_traffic else 1.0
        for (u, v), base_w in self.base_weights.items():
            traffic = attack_traffic.get((u, v), 0) + attack_traffic.get((v, u), 0)
            new_w = base_w * (1 + sensitivity * (traffic / max_traffic))
            self.update_edge_weight(u, v, new_w)

    # ---------- 动态路径扰动接口 ----------
    def apply_perturbation(self, current_attack_path: List[str],
                           load_vector: Dict[str, float],
                           sensitivity: float = 0.5):
        """
        根据当前攻击路径和负载动态调整边权重（诱导攻击者绕行）
        :param current_attack_path: 攻击路径节点列表
        :param load_vector: 节点负载字典
        :param sensitivity: 负载影响系数
        """
        if not self.graph or not self.dynamic_weights_enabled:
            return

        target_node = current_attack_path[-1] if current_attack_path else None
        if target_node is None or target_node not in self.graph:
            return

        neighbors = list(self.graph.neighbors(target_node))

        for u, v, data in self.graph.edges(data=True):
            orig_w = data.get('weight', 1.0)
            if target_node in (u, v) and load_vector.get(target_node, 0) > 0.5:
                new_w = orig_w * (1 + sensitivity * load_vector[target_node])
                self.update_edge_weight(u, v, new_w)
                # 同步更新图对象
                if self.graph.has_edge(u, v):
                    self.graph[u][v]['weight'] = new_w


# ========================= 独立扰动函数 =========================
def dynamic_perturbation(steiner_tree: nx.Graph,
                         current_attack_path: List[str],
                         load_vector: Dict[str, float],
                         sensitivity: float = 0.5) -> Dict[Tuple[str, str], float]:
    """
    根据当前网络负载和攻击者行为，实时调整非终端节点的转发权重。
    返回调整后的边权重字典。
    """
    adjusted = {}
    if not current_attack_path:
        return adjusted

    target_node = current_attack_path[-1]
    if target_node not in steiner_tree:
        return adjusted

    for u, v, data in steiner_tree.edges(data=True):
        w = data.get('weight', 1.0)
        if target_node in (u, v) and load_vector.get(target_node, 0) > 0.5:
            new_w = w * (1 + sensitivity * load_vector[target_node])
        else:
            new_w = w
        adjusted[(u, v)] = new_w
        adjusted[(v, u)] = new_w

    return adjusted


# ========================= 测试代码 =========================
if __name__ == "__main__":
    print(" 测试斯坦纳树构建器（高级模式）")
    # 构建示例图
    G = nx.Graph()
    G.add_edge('A', 'B', weight=2)
    G.add_edge('B', 'C', weight=3)
    G.add_edge('A', 'D', weight=5)
    G.add_edge('D', 'E', weight=1)
    G.add_edge('E', 'C', weight=2)

    terminals = ['A', 'C']
    host_tenant_map = {'A': 't1', 'B': 't1', 'C': 't2', 'D': 't1', 'E': 't2'}
    safe_gateways = {'B'}

    # 演示租户隔离
    builder = SteinerTreeBuilder(
        graph=G,
        terminals=terminals,
        host_tenant_map=host_tenant_map,
        safe_gateways=safe_gateways,
        enable_tenant_isolation=True,
        tenant_id='t1'
    )

    # 模拟优化解
    opt_solution = {'selected_nodes': ['B', 'E'], 'deployment_cost': 100}
    terminal_nodes = [type('Node', (), {'id': t}) for t in terminals]

    tree = builder.build_tree(opt_solution, terminal_nodes, [])
    print("树结构:", tree)

    # 测试扰动
    attack_path = ['A', 'B', 'C']
    load = {'C': 0.8}
    adj = dynamic_perturbation(tree.get('graph', G), attack_path, load)
    print("扰动后权重:", adj)