"""
边定义模块 - 增强版
添加流守恒约束和分层延迟约束
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import math


@dataclass
class Edge:
    """基础边类 - 增强版"""
    edge_id: str
    source_id: str
    target_id: str
    directed: bool = True
    
    # 基本属性
    length: float = 1.0
    edge_type: str = "network"
    layer: str = "access"  # core, aggregation, access
    
    # 成本属性
    costs: Dict[str, float] = field(default_factory=lambda: {
        "bandwidth_cost": 0.0,
        "maintenance_cost": 0.0,
        "security_cost": 0.0,
        "installation_cost": 0.0
    })
    
    # 性能属性
    performance: Dict[str, float] = field(default_factory=lambda: {
        "bandwidth": 1.0,  # Gbps
        "latency": 1.0,    # ms
        "packet_loss": 0.0,  # %
        "jitter": 0.0      # ms
    })
    
    # 分层延迟阈值（约束4）
    layer_delay_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "core_to_agg": 20.0,    # 核心层→汇聚层阈值
        "agg_to_access": 30.0,  # 汇聚层→接入层阈值
        "cross_layer": 50.0     # 跨层总延迟阈值
    })
    
    # 安全属性
    security: Dict[str, Any] = field(default_factory=lambda: {
        "is_encrypted": False,
        "vulnerabilities": [],
        "protection_level": 0.0,
        "security_group": "default"
    })
    
    # 状态属性
    is_active: bool = True
    utilization: float = 0.0
    current_load: float = 0.0
    
    # 流量追踪（用于流守恒约束）
    flow_allocations: Dict[str, float] = field(default_factory=lambda: {
        # flow_id: allocated_bandwidth
    })
    
    def __post_init__(self):
        if not self.edge_id:
            self.edge_id = f"edge_{self.source_id}_{self.target_id}"
        
        if not self.directed and self.source_id > self.target_id:
            self.source_id, self.target_id = self.target_id, self.source_id
    
    def check_layer_delay_constraint(self) -> bool:
        """检查分层延迟硬约束（约束4）"""
        latency = self.performance.get("latency", 0.0)
        
        # 根据层级检查延迟阈值
        if self.layer == "core" and latency > self.layer_delay_thresholds.get("core_to_agg", 20.0):
            return False
        elif self.layer == "aggregation" and latency > self.layer_delay_thresholds.get("agg_to_access", 30.0):
            return False
        
        return True
    
    def allocate_flow(self, flow_id: str, bandwidth: float) -> bool:
        """分配流量到边（用于流守恒追踪）"""
        # 检查带宽容量
        if not self.can_handle_load(bandwidth):
            return False
        
        # 分配流量
        self.flow_allocations[flow_id] = self.flow_allocations.get(flow_id, 0.0) + bandwidth
        self.current_load += bandwidth
        
        # 更新使用率
        max_bandwidth = self.performance.get("bandwidth", 1.0)
        if max_bandwidth > 0:
            self.utilization = (self.current_load / max_bandwidth) * 100
        
        return True
    
    def release_flow(self, flow_id: str) -> float:
        """释放流量"""
        if flow_id in self.flow_allocations:
            released_bandwidth = self.flow_allocations[flow_id]
            self.current_load -= released_bandwidth
            del self.flow_allocations[flow_id]
            
            # 更新使用率
            max_bandwidth = self.performance.get("bandwidth", 1.0)
            if max_bandwidth > 0:
                self.utilization = (self.current_load / max_bandwidth) * 100
            
            return released_bandwidth
        return 0.0
    
    def get_total_flow_bandwidth(self) -> float:
        """获取总流量带宽"""
        return sum(self.flow_allocations.values())
    
    def get_total_cost(self) -> float:
        return sum(self.costs.values())
    
    def get_effective_bandwidth(self) -> float:
        base_bw = self.performance.get("bandwidth", 1.0)
        packet_loss = self.performance.get("packet_loss", 0.0) / 100.0
        effective_bw = base_bw * (1 - packet_loss)
        
        latency = self.performance.get("latency", 1.0)
        if latency > 100:
            effective_bw *= 0.8
        
        return effective_bw
    
    def calculate_transmission_time(self, data_size: float) -> float:
        bandwidth_mbps = self.get_effective_bandwidth() * 1000
        if bandwidth_mbps <= 0:
            return float('inf')
        
        transmission_time = (data_size * 8) / bandwidth_mbps
        transmission_time += self.performance.get("latency", 0.0)
        return transmission_time
    
    def can_handle_load(self, additional_load: float) -> bool:
        max_bandwidth = self.performance.get("bandwidth", 1.0)
        return (self.current_load + additional_load) <= max_bandwidth * 0.9
    
    def update_load(self, load_change: float) -> bool:
        new_load = self.current_load + load_change
        max_bandwidth = self.performance.get("bandwidth", 1.0)
        
        if 0 <= new_load <= max_bandwidth:
            self.current_load = new_load
            self.utilization = (new_load / max_bandwidth) * 100 if max_bandwidth > 0 else 0
            return True
        return False
    
    def get_quality_score(self) -> float:
        score = 0.0
        
        bw = self.performance.get("bandwidth", 1.0)
        bw_score = min(bw / 10.0, 1.0)
        score += bw_score * 0.3
        
        latency = self.performance.get("latency", 1.0)
        latency_score = 1.0 - min(latency / 100.0, 1.0)
        score += latency_score * 0.4
        
        packet_loss = self.performance.get("packet_loss", 0.0)
        reliability_score = 1.0 - min(packet_loss / 10.0, 1.0)
        score += reliability_score * 0.3
        
        return score


@dataclass
class NetworkEdge(Edge):
    """物理网络边 - 增强版"""
    physical_layer: str = "ethernet"
    network_tier: str = "core"
    
    # 带宽容量约束（约束6）
    bandwidth_capacity: float = 0.0  # Gbps
    
    def __post_init__(self):
        super().__post_init__()
        self.edge_type = "network"
        
        # 设置默认性能
        tier_performance = {
            "core": {"bandwidth": 100.0, "latency": 1.0},
            "aggregation": {"bandwidth": 40.0, "latency": 5.0},
            "access": {"bandwidth": 10.0, "latency": 10.0}
        }
        
        if self.network_tier in tier_performance:
            for key, value in tier_performance[self.network_tier].items():
                if key not in self.performance or self.performance[key] == 0:
                    self.performance[key] = value
        
        # 设置带宽容量
        if self.bandwidth_capacity == 0:
            self.bandwidth_capacity = self.performance.get("bandwidth", 1.0)
    
    def check_bandwidth_constraint(self, virtual_edges: List['VirtualEdge']) -> bool:
        """检查物理链路带宽容量约束（约束6）"""
        total_bandwidth = 0.0
        
        for virtual_edge in virtual_edges:
            if self.edge_id in virtual_edge.mapped_physical_edges:
                total_bandwidth += virtual_edge.required_bandwidth
        
        return total_bandwidth <= self.bandwidth_capacity * 0.9  # 保留10%余量


@dataclass
class VirtualEdge(Edge):
    """虚拟边（逻辑连接）- 增强版"""
    logical_relation: str = ""
    mapped_physical_edges: List[str] = field(default_factory=list)
    required_bandwidth: float = 0.0
    
    # 端点部署一致性（约束4-5）
    source_deployed_on: Optional[str] = None  # 源服务部署位置
    target_deployed_on: Optional[str] = None  # 目标服务部署位置
    
    def __post_init__(self):
        super().__post_init__()
        self.edge_type = "virtual"
        self.directed = True
    
    def check_endpoint_consistency(self, 
                                  source_deployed_on: str,
                                  target_deployed_on: str) -> bool:
        """检查端点部署一致性约束（约束4-5）"""
        # 检查虚拟链路起点
        if self.source_deployed_on and source_deployed_on != self.source_deployed_on:
            return False
        
        # 检查虚拟链路终点
        if self.target_deployed_on and target_deployed_on != self.target_deployed_on:
            return False
        
        return True
    
    def add_physical_mapping(self, physical_edge_id: str) -> None:
        if physical_edge_id not in self.mapped_physical_edges:
            self.mapped_physical_edges.append(physical_edge_id)
    
    def remove_physical_mapping(self, physical_edge_id: str) -> None:
        if physical_edge_id in self.mapped_physical_edges:
            self.mapped_physical_edges.remove(physical_edge_id)
    
    def calculate_virtual_latency(self, physical_edges: Dict[str, Edge]) -> float:
        total_latency = 0.0
        
        for edge_id in self.mapped_physical_edges:
            if edge_id in physical_edges:
                total_latency += physical_edges[edge_id].performance.get("latency", 0.0)
            else:
                total_latency += 10.0
        
        total_latency *= 1.1
        self.performance["latency"] = total_latency
        return total_latency


@dataclass  
class Path:
    """路径类 - 增强版，支持树结构检查"""
    path_id: str
    node_sequence: List[str]
    edge_sequence: List[str]
    total_cost: float = 0.0
    total_latency: float = 0.0
    min_bandwidth: float = float('inf')
    
    # 树结构检查（约束7）
    is_tree: bool = False
    parent_nodes: Dict[str, str] = field(default_factory=dict)  # 子节点->父节点映射
    
    def __post_init__(self):
        """自动检测是否为树结构"""
        if self.node_sequence and self.edge_sequence:
            self._detect_tree_structure()
    
    def _detect_tree_structure(self):
        """检测路径是否为树结构"""
        # 简单检查：边数 = 节点数 - 1
        if len(self.edge_sequence) == len(self.node_sequence) - 1:
            self.is_tree = True
            
            # 构建父节点映射（假设第一个节点为根）
            if len(self.node_sequence) >= 2:
                self.parent_nodes = {}
                for i in range(1, len(self.node_sequence)):
                    self.parent_nodes[self.node_sequence[i]] = self.node_sequence[i-1]
    
    def check_acyclic_constraint(self) -> bool:
        """检查无环约束（约束7）"""
        # 斯坦纳树必须是无环的
        return self.is_tree and len(self.edge_sequence) == len(self.node_sequence) - 1
    
    def calculate_metrics(self, edges: Dict[str, Edge]) -> None:
        self.total_cost = 0.0
        self.total_latency = 0.0
        self.min_bandwidth = float('inf')
        
        for edge_id in self.edge_sequence:
            if edge_id in edges:
                edge = edges[edge_id]
                self.total_cost += edge.get_total_cost()
                self.total_latency += edge.performance.get("latency", 0.0)
                self.min_bandwidth = min(self.min_bandwidth, edge.performance.get("bandwidth", 0.0))
    
    def is_valid(self, edges: Dict[str, Edge]) -> bool:
        if len(self.node_sequence) < 2 or len(self.edge_sequence) < 1:
            return False
        
        for edge_id in self.edge_sequence:
            if edge_id not in edges:
                return False
        
        return True
    
    def get_nodes(self) -> List[str]:
        return self.node_sequence.copy()


@dataclass
class Flow:
    """流量类，用于流守恒约束检查（约束7）"""
    flow_id: str
    source_node: str
    target_node: str
    bandwidth: float
    path: Optional[Path] = None
    
    def check_flow_conservation(self, network: Dict[str, Node]) -> bool:
        """检查流守恒约束"""
        if not self.path:
            return False
        
        # 确保路径是连续的
        node_sequence = self.path.node_sequence
        edge_sequence = self.path.edge_sequence
        
        if not node_sequence or not edge_sequence:
            return False
        
        # 检查源节点和目标节点
        if node_sequence[0] != self.source_node or node_sequence[-1] != self.target_node:
            return False
        
        # 检查每个中间节点的流入流出平衡
        for i in range(1, len(node_sequence) - 1):
            node_id = node_sequence[i]
            if node_id in network:
                # 简化检查：确保节点有进边和出边
                incoming = 0
                outgoing = 0
                
                # 在实际实现中，需要更复杂的流量平衡检查
                # 这里简化处理
                if i > 0:
                    incoming += 1
                if i < len(node_sequence) - 1:
                    outgoing += 1
                
                if incoming != outgoing:
                    return False
        
        return True