"""
约束检查器 - 简化版本
"""
# src/utils/constraints.py

'''class TenantIsolationConstraint:
    """
    租户硬隔离约束：确保蜜罐节点所在的物理宿主机上不包含其他租户的蜜罐。
    """
    def __init__(self, tenant_id: str, host_tenant_map: Dict[str, str]):
        """
        :param tenant_id: 当前租户ID
        :param host_tenant_map: 映射 {host_id: tenant_id}
        """
        self.tenant_id = tenant_id
        self.host_tenant_map = host_tenant_map

    def is_satisfied(self, selected_nodes: List[str]) -> bool:
        """
        检查所选节点是否违反隔离约束。
        :param selected_nodes: 被选中的蜜罐节点ID列表
        :return: True 如果满足约束
        """
        # 获取每个节点所在的物理宿主机
        for node in selected_nodes:
            host = self._get_host_of_node(node)
            if host is None:
                continue
            # 如果该宿主机上已有其他租户的蜜罐，则违反
            if self.host_tenant_map.get(host) != self.tenant_id:
                return False
        return True

    def _get_host_of_node(self, node_id: str) -> str:
        # 根据实际节点元数据获取宿主机ID
        # 此处为示例，实际需从节点元数据中读取
        return node_metadata[node_id].get('host', None)
class ConstraintChecker:
    """约束检查器类"""
    
    def __init__(self, **kwargs):
        pass
    
    def check(self, solution, constraints):
        """检查约束 - 简化实现"""
        return {'passed': True, 'violations': []}

class ConstraintCheckResult:
    """约束检查结果类"""
    def __init__(self, passed=True, violations=None):
        self.passed = passed
        self.violations = violations or []

def check_deployment_feasibility(solution, constraints):
    """检查部署可行性 - 简化实现"""
    return True'''
"""
约束检查器 - 包含租户硬隔离约束
"""
"""
约束检查器 - 简化版本
"""
# src/utils/constraints.py

'''class TenantIsolationConstraint:
    """
    租户硬隔离约束：确保蜜罐节点所在的物理宿主机上不包含其他租户的蜜罐。
    """
    def __init__(self, tenant_id: str, host_tenant_map: Dict[str, str]):
        """
        :param tenant_id: 当前租户ID
        :param host_tenant_map: 映射 {host_id: tenant_id}
        """
        self.tenant_id = tenant_id
        self.host_tenant_map = host_tenant_map

    def is_satisfied(self, selected_nodes: List[str]) -> bool:
        """
        检查所选节点是否违反隔离约束。
        :param selected_nodes: 被选中的蜜罐节点ID列表
        :return: True 如果满足约束
        """
        # 获取每个节点所在的物理宿主机
        for node in selected_nodes:
            host = self._get_host_of_node(node)
            if host is None:
                continue
            # 如果该宿主机上已有其他租户的蜜罐，则违反
            if self.host_tenant_map.get(host) != self.tenant_id:
                return False
        return True

    def _get_host_of_node(self, node_id: str) -> str:
        # 根据实际节点元数据获取宿主机ID
        # 此处为示例，实际需从节点元数据中读取
        return node_metadata[node_id].get('host', None)
class ConstraintChecker:
    """约束检查器类"""
    
    def __init__(self, **kwargs):
        pass
    
    def check(self, solution, constraints):
        """检查约束 - 简化实现"""
        return {'passed': True, 'violations': []}

class ConstraintCheckResult:
    """约束检查结果类"""
    def __init__(self, passed=True, violations=None):
        self.passed = passed
        self.violations = violations or []

def check_deployment_feasibility(solution, constraints):
    """检查部署可行性 - 简化实现"""
    return True'''
"""
约束检查器 - 包含租户硬隔离约束
"""

"""
约束检查器 - 简化版本
"""
# src/utils/constraints.py

'''class TenantIsolationConstraint:
    """
    租户硬隔离约束：确保蜜罐节点所在的物理宿主机上不包含其他租户的蜜罐。
    """
    def __init__(self, tenant_id: str, host_tenant_map: Dict[str, str]):
        """
        :param tenant_id: 当前租户ID
        :param host_tenant_map: 映射 {host_id: tenant_id}
        """
        self.tenant_id = tenant_id
        self.host_tenant_map = host_tenant_map

    def is_satisfied(self, selected_nodes: List[str]) -> bool:
        """
        检查所选节点是否违反隔离约束。
        :param selected_nodes: 被选中的蜜罐节点ID列表
        :return: True 如果满足约束
        """
        # 获取每个节点所在的物理宿主机
        for node in selected_nodes:
            host = self._get_host_of_node(node)
            if host is None:
                continue
            # 如果该宿主机上已有其他租户的蜜罐，则违反
            if self.host_tenant_map.get(host) != self.tenant_id:
                return False
        return True

    def _get_host_of_node(self, node_id: str) -> str:
        # 根据实际节点元数据获取宿主机ID
        # 此处为示例，实际需从节点元数据中读取
        return node_metadata[node_id].get('host', None)
class ConstraintChecker:
    """约束检查器类"""
    
    def __init__(self, **kwargs):
        pass
    
    def check(self, solution, constraints):
        """检查约束 - 简化实现"""
        return {'passed': True, 'violations': []}

class ConstraintCheckResult:
    """约束检查结果类"""
    def __init__(self, passed=True, violations=None):
        self.passed = passed
        self.violations = violations or []

def check_deployment_feasibility(solution, constraints):
    """检查部署可行性 - 简化实现"""
    return True'''
"""
约束检查器 - 包含租户硬隔离约束
"""

from typing import List, Dict, Optional, Tuple, Any
import networkx as nx

# ========================= 新增：租户隔离检查函数 =========================

def tenant_isolation_constraint(steiner_tree: nx.Graph,
                                tenant_mapping: Dict[str, str],
                                host_to_tenant: Dict[str, str]) -> bool:
    """
    检查斯坦纳树中的节点是否违反了多租户隔离约束。
    约束：同一物理机上的容器不能属于不同租户，且不能共享敏感数据。
    :param steiner_tree: 斯坦纳树（nx.Graph）
    :param tenant_mapping: 节点 -> 租户ID 映射
    :param host_to_tenant: 宿主机 -> 租户ID 映射（会被修改，记录已分配宿主机）
    :return: True 如果满足隔离约束
    """
    for node in steiner_tree.nodes:
        if node not in tenant_mapping:
            continue
        node_tenant = tenant_mapping[node]
        host = _get_host_of_node(node)
        if host is None:
            continue
        # 如果该宿主机已被其他租户占用，则冲突
        if host in host_to_tenant and host_to_tenant[host] != node_tenant:
            return False
        # 记录该宿主机已被当前租户占用
        host_to_tenant[host] = node_tenant
    return True


def _get_host_of_node(node_id: str) -> Optional[str]:
    """
    根据节点ID获取所在物理宿主机ID。
    实际应从节点元数据中获取，此处为占位，用户需根据实际数据覆盖。
    示例：假设节点ID格式为 'node-1@host-01'，则提取 '@' 后面的部分。
    """
    if '@' in node_id:
        return node_id.split('@')[-1]
    return None


# ========================= 原有接口保留 =========================

class TenantIsolationConstraint:
    """
    租户硬隔离约束：确保蜜罐节点所在的物理宿主机上不包含其他租户的蜜罐。
    保留原有接口，但使用上述函数实现。
    """
    def __init__(self, tenant_id: str, host_tenant_map: Dict[str, str]):
        """
        :param tenant_id: 当前租户ID
        :param host_tenant_map: 映射 {host_id: tenant_id}
        """
        self.tenant_id = tenant_id
        self.host_tenant_map = host_tenant_map

    def is_satisfied(self, selected_nodes: List[str]) -> bool:
        """
        检查所选节点是否违反隔离约束。
        :param selected_nodes: 被选中的蜜罐节点ID列表
        :return: True 如果满足约束
        """
        # 构建临时树（只包含节点，无连接）
        tree = nx.Graph()
        tree.add_nodes_from(selected_nodes)
        # 构建 tenant_mapping：假设所有 selected_nodes 属于当前租户
        tenant_mapping = {node: self.tenant_id for node in selected_nodes}
        host_to_tenant = self.host_tenant_map.copy()
        return tenant_isolation_constraint(tree, tenant_mapping, host_to_tenant)

    def _get_host_of_node(self, node_id: str) -> Optional[str]:
        """
        获取节点所在的物理宿主机ID。
        修复：不再使用未定义的 node_metadata，而是调用全局辅助函数。
        """
        return _get_host_of_node(node_id)


class ConstraintChecker:
    """约束检查器类（保留原有接口）"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def check(self, solution, constraints):
        """
        检查约束 - 扩展支持租户隔离
        :param solution: 解结构，应包含 'nodes' 或 'graph' 字段
        :param constraints: 约束字典，可包含 'tenant_isolation' 键
        :return: ConstraintCheckResult
        """
        violations = []

        # 提取解中的节点列表
        if isinstance(solution, dict):
            if 'graph' in solution and isinstance(solution['graph'], nx.Graph):
                nodes = list(solution['graph'].nodes)
            elif 'nodes' in solution:
                nodes = [n.get('id') if isinstance(n, dict) else n for n in solution['nodes']]
            else:
                nodes = []
        else:
            nodes = []

        for name, constr in constraints.items():
            if name == 'tenant_isolation':
                # 假设 constr 包含 tenant_id 和 host_tenant_map
                tenant_id = constr.get('tenant_id')
                host_tenant_map = constr.get('host_tenant_map', {})
                if tenant_id is not None:
                    # 构建临时树
                    tree = nx.Graph()
                    tree.add_nodes_from(nodes)
                    tenant_mapping = {node: tenant_id for node in nodes}
                    if not tenant_isolation_constraint(tree, tenant_mapping, host_tenant_map.copy()):
                        violations.append(f"租户隔离约束违反: {constr}")
            # 可扩展其他约束

        return ConstraintCheckResult(passed=len(violations) == 0, violations=violations)


class ConstraintCheckResult:
    """约束检查结果类"""
    def __init__(self, passed=True, violations=None):
        self.passed = passed
        self.violations = violations or []


def check_deployment_feasibility(solution, constraints):
    """检查部署可行性 - 简化实现，但使用 ConstraintChecker"""
    checker = ConstraintChecker()
    result = checker.check(solution, constraints)
    return result.passed


# ========================= 测试代码 =========================
if __name__ == "__main__":
    print(" 测试约束检查器")
    # 创建示例树
    tree = nx.Graph()
    tree.add_nodes_from(['node1@hostA', 'node2@hostA', 'node3@hostB'])
    tree.add_edges_from([('node1@hostA', 'node2@hostA')])

    tenant_mapping = {
        'node1@hostA': 'tenant1',
        'node2@hostA': 'tenant1',
        'node3@hostB': 'tenant2'
    }
    host_tenant_map = {}
    result = tenant_isolation_constraint(tree, tenant_mapping, host_tenant_map)
    print("租户隔离检查结果:", result)  # 应为 True，因为不同租户不在同一宿主机

    # 测试冲突情况
    tree.add_node('node4@hostA')
    tenant_mapping['node4@hostA'] = 'tenant2'
    host_tenant_map = {}
    result2 = tenant_isolation_constraint(tree, tenant_mapping, host_tenant_map)
    print("冲突检查结果:", result2)  # 应为 False

    # 测试原有 ConstraintChecker
    checker = ConstraintChecker()
    solution = {'nodes': ['node1@hostA', 'node2@hostA', 'node3@hostB']}
    constraints = {
        'tenant_isolation': {
            'tenant_id': 'tenant1',
            'host_tenant_map': {}
        }
    }
    res = checker.check(solution, constraints)
    print("ConstraintChecker 结果:", res.passed, res.violations)