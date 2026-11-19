"""
节点定义模块 - 增强版
添加物理容量约束和部署位置追踪
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
import yaml
import json
import math


@dataclass
class Node:
    """基础节点类 - 增强版"""
    node_id: str
    node_type: str  # gate, expert_real, expert_honeypot, steiner, router
    name: str = ""
    
    # 位置信息（可选）
    coordinates: Tuple[float, float] = (0.0, 0.0)
    rack_id: Optional[str] = None
    switch_id: Optional[str] = None
    layer: str = "access"  # core, aggregation, access (对应fat tree三层架构)
    
    # 资源属性 - 当前使用量
    resources_used: Dict[str, float] = field(default_factory=lambda: {
        "cpu": 0.0,
        "memory": 0.0,  # GB
        "bandwidth": 0.0,  # Gbps
        "storage": 0.0  # GB
    })
    
    # 物理容量 - 最大可用量（约束6：节点资源三维约束）
    physical_capacity: Dict[str, float] = field(default_factory=lambda: {
        "max_cpu": 0.0,  # CPU核心数
        "max_memory": 0.0,  # GB
        "max_bandwidth": 0.0,  # Gbps
        "max_storage": 0.0  # GB
    })
    
    # 资源使用上限比例（从配置加载）
    utilization_limits: Dict[str, float] = field(default_factory=lambda: {
        "cpu_limit": 0.3,      # CPU使用不超过30%
        "memory_limit": 0.2,   # 内存使用不超过20%
        "bandwidth_limit": 0.4  # 带宽使用不超过40%
    })
    
    # 成本属性
    costs: Dict[str, float] = field(default_factory=lambda: {
        "hardware": 0.0,      # 硬件采购成本
        "deployment": 0.0,    # 部署成本
        "maintenance": 0.0,   # 年维护成本
        "software": 0.0       # 软件许可成本
    })
    
    # 安全属性
    security: Dict[str, Any] = field(default_factory=lambda: {
        "vulnerabilities": [],
        "protection_level": 0.0,
        "is_protected": False,
        "security_group": "default"
    })
    
    # 拓扑属性
    connected_edges: List[str] = field(default_factory=list)
    neighbors: Set[str] = field(default_factory=set)
    
    # 部署追踪（约束1：服务唯一部署约束）
    deployed_services: List[str] = field(default_factory=list)  # 部署在该节点上的服务ID列表
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            self.name = f"{self.node_type}_{self.node_id}"
    
    def add_service_deployment(self, service_id: str) -> bool:
        """添加服务部署到该节点（约束1）"""
        if service_id not in self.deployed_services:
            self.deployed_services.append(service_id)
            return True
        return False
    
    def remove_service_deployment(self, service_id: str) -> bool:
        """移除服务部署"""
        if service_id in self.deployed_services:
            self.deployed_services.remove(service_id)
            return True
        return False
    
    def check_resource_constraints(self, 
                                 additional_cpu: float = 0,
                                 additional_memory: float = 0,
                                 additional_bandwidth: float = 0) -> Dict[str, bool]:
        """检查节点资源约束（约束2和约束6）"""
        results = {}
        
        # CPU约束检查
        cpu_used = self.resources_used.get("cpu", 0.0) + additional_cpu
        cpu_capacity = self.physical_capacity.get("max_cpu", 0.0)
        cpu_limit = self.utilization_limits.get("cpu_limit", 0.3)
        results["cpu"] = cpu_used <= cpu_capacity * cpu_limit
        
        # 内存约束检查
        memory_used = self.resources_used.get("memory", 0.0) + additional_memory
        memory_capacity = self.physical_capacity.get("max_memory", 0.0)
        memory_limit = self.utilization_limits.get("memory_limit", 0.2)
        results["memory"] = memory_used <= memory_capacity * memory_limit
        
        # 带宽约束检查
        bandwidth_used = self.resources_used.get("bandwidth", 0.0) + additional_bandwidth
        bandwidth_capacity = self.physical_capacity.get("max_bandwidth", 0.0)
        bandwidth_limit = self.utilization_limits.get("bandwidth_limit", 0.4)
        results["bandwidth"] = bandwidth_used <= bandwidth_capacity * bandwidth_limit
        
        # 总体约束
        results["all"] = all(results.values())
        
        return results
    
    def allocate_resources(self, 
                          cpu: float = 0,
                          memory: float = 0,
                          bandwidth: float = 0) -> bool:
        """分配资源并检查约束"""
        constraints = self.check_resource_constraints(cpu, memory, bandwidth)
        
        if constraints["all"]:
            self.resources_used["cpu"] += cpu
            self.resources_used["memory"] += memory
            self.resources_used["bandwidth"] += bandwidth
            return True
        
        return False
    
    def free_resources(self,
                      cpu: float = 0,
                      memory: float = 0,
                      bandwidth: float = 0) -> None:
        """释放资源"""
        self.resources_used["cpu"] = max(0, self.resources_used.get("cpu", 0) - cpu)
        self.resources_used["memory"] = max(0, self.resources_used.get("memory", 0) - memory)
        self.resources_used["bandwidth"] = max(0, self.resources_used.get("bandwidth", 0) - bandwidth)
    
    def calculate_distance(self, other_node: Node) -> float:
        """计算与另一个节点的距离（约束1：dist(t,s) ≤ 1）"""
        if not self.coordinates or not other_node.coordinates:
            return 1.0  # 默认距离为1（跳数）
        
        # 欧几里得距离
        x1, y1 = self.coordinates
        x2, y2 = other_node.coordinates
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # 转换为跳数（简化模型）
        # 距离 < 0.5：同一交换机，跳数=0
        # 0.5 ≤ 距离 < 1.5：同一机架，跳数=1
        # 距离 ≥ 1.5：不同机架，跳数=2
        if distance < 0.5:
            return 0
        elif distance < 1.5:
            return 1
        else:
            return 2
    
    def is_within_one_hop(self, other_node: Node) -> bool:
        """检查是否在一跳范围内（约束1：dist(t,s) ≤ 1）"""
        return self.calculate_distance(other_node) <= 1
    
    def get_total_cost(self, years: int = 1) -> float:
        """计算总成本（约束3：全生命周期预算约束）"""
        # 硬件成本
        hardware_cost = self.costs.get("hardware", 0.0)
        
        # 部署成本
        deployment_cost = self.costs.get("deployment", 0.0)
        
        # 维护成本（每年）
        maintenance_cost = self.costs.get("maintenance", 0.0)
        
        # 软件成本（如果有）
        software_cost = self.costs.get("software", 0.0)
        
        # 全生命周期总成本
        total_cost = hardware_cost + deployment_cost + software_cost
        
        # 加上多年维护成本
        for year in range(1, years + 1):
            # 维护成本可能逐年递减（例如，第一年10%，之后每年5%）
            if year == 1:
                total_cost += maintenance_cost * hardware_cost * 0.1
            else:
                total_cost += maintenance_cost * hardware_cost * 0.05
        
        return total_cost
    
    def get_resource_utilization(self) -> Dict[str, float]:
        """计算资源使用率（百分比）"""
        utilization = {}
        
        for resource_type in ["cpu", "memory", "bandwidth", "storage"]:
            used = self.resources_used.get(resource_type, 0.0)
            capacity = self.physical_capacity.get(f"max_{resource_type}", 1.0)
            
            if capacity > 0:
                utilization[resource_type] = min(100.0, (used / capacity) * 100)
            else:
                utilization[resource_type] = 0.0
        
        return utilization
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "coordinates": self.coordinates,
            "rack_id": self.rack_id,
            "switch_id": self.switch_id,
            "layer": self.layer,
            "resources_used": self.resources_used,
            "physical_capacity": self.physical_capacity,
            "utilization_limits": self.utilization_limits,
            "costs": self.costs,
            "security": self.security,
            "connected_edges": self.connected_edges,
            "neighbors": list(self.neighbors),
            "deployed_services": self.deployed_services
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> Node:
        """从字典创建节点"""
        return cls(**data)


@dataclass
class TerminalNode(Node):
    """终端节点（必须保护的关键资产）- 增强版"""
    
    # 终端节点特有属性
    critical_level: float = 1.0
    service_type: str = ""
    is_real: bool = True
    deployed_on: Optional[str] = None  # 物理节点ID
    covered_by: List[str] = field(default_factory=list)  # 覆盖此终端的斯坦纳节点列表
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        self.is_terminal = True  # 标记为终端节点
        
        # 服务类型默认为节点类型
        if not self.service_type:
            self.service_type = self.node_type
    
    def set_deployment(self, physical_node_id: str) -> bool:
        """设置部署位置（约束1）"""
        # 一个终端只能部署在一个物理节点上
        if not self.deployed_on or self.deployed_on == physical_node_id:
            self.deployed_on = physical_node_id
            return True
        return False
    
    def add_coverage(self, steiner_node_id: str) -> None:
        """添加覆盖此终端的斯坦纳节点"""
        if steiner_node_id not in self.covered_by:
            self.covered_by.append(steiner_node_id)
    
    def is_covered(self) -> bool:
        """检查是否被覆盖（约束1）"""
        return len(self.covered_by) > 0
    
    def get_coverage_distance(self, steiner_node: Node) -> float:
        """获取与斯坦纳节点的覆盖距离"""
        return self.calculate_distance(steiner_node)
    
    def __repr__(self) -> str:
        """改进的字符串表示"""
        return (f"TerminalNode(id={self.node_id}, type={self.node_type}, "
                f"critical={self.critical_level}, covered={self.is_covered()}, "
                f"deployed_on={self.deployed_on})")


@dataclass
class GateNode(TerminalNode):
    """门控节点"""
    routing_table: Dict[str, float] = field(default_factory=dict)
    load_balancing: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        self.node_type = "gate"
        self.critical_level = 1.0


@dataclass
class ExpertNode(TerminalNode):
    """专家节点"""
    expertise_domain: str = ""
    activation_probability: float = 0.0
    model_size: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        self.node_type = "expert_real" if self.is_real else "expert_honeypot"


@dataclass
class SteinerNode(Node):
    """斯坦纳节点（可部署蜜罐的潜在位置）- 增强版"""
    deployable: bool = True
    deployment_cost: float = 0.0
    honeypot_type: Optional[str] = None
    is_deployed: bool = False
    
    # 有效性检查（约束2）
    covered_terminals: List[str] = field(default_factory=list)  # 覆盖的终端节点ID
    is_on_critical_path: bool = False  # 是否在关键路径上
    
    def __post_init__(self):
        super().__post_init__()
        self.node_type = "steiner"
    
    def check_effectiveness_constraint(self) -> bool:
        """检查斯坦纳节点强有效性约束（约束2）"""
        # 1. 至少覆盖2个终端
        covers_enough = len(self.covered_terminals) >= 2
        
        # 2. 在关键路径上（或部署了蜜罐）
        on_critical_path = self.is_on_critical_path or self.is_deployed
        
        return covers_enough and on_critical_path
    
    def add_covered_terminal(self, terminal_id: str) -> None:
        """添加覆盖的终端"""
        if terminal_id not in self.covered_terminals:
            self.covered_terminals.append(terminal_id)
    
    def deploy_honeypot(self, honeypot_type: str, cost: float) -> bool:
        """部署蜜罐"""
        if not self.deployable:
            return False
        
        self.honeypot_type = honeypot_type
        self.deployment_cost = cost
        self.is_deployed = True
        self.node_type = f"honeypot_{honeypot_type}"
        return True
    
    def undeploy_honeypot(self) -> None:
        """卸载蜜罐"""
        self.honeypot_type = None
        self.deployment_cost = 0.0
        self.is_deployed = False
        self.node_type = "steiner"


@dataclass
class HoneypotNode(SteinerNode):
    """蜜罐节点（已部署的蜜罐）- 增强版"""
    deception_level: float = 0.0
    interaction_level: str = "low"  # low, medium, high
    simulated_expert: Optional[str] = None
    capture_rate: float = 0.0
    
    # 伪装有效性（约束8）
    similarity_score: float = 0.0
    simulation_features: Dict[str, Any] = field(default_factory=lambda: {
        "ports": [],
        "protocols": [],
        "response_patterns": [],
        "behavior_signatures": []
    })
    
    def __post_init__(self):
        super().__post_init__()
        self.node_type = "honeypot"
    
    def calculate_similarity(self, real_expert: ExpertNode) -> float:
        """计算与真实专家的相似度（约束8）"""
        similarity = 0.0
        features_matched = 0
        total_features = 0
        
        # 检查端口匹配
        if hasattr(real_expert, 'ports') and 'ports' in self.simulation_features:
            expert_ports = getattr(real_expert, 'ports', [])
            honeypot_ports = self.simulation_features.get('ports', [])
            matched_ports = len(set(expert_ports) & set(honeypot_ports))
            total_ports = len(set(expert_ports) | set(honeypot_ports))
            
            if total_ports > 0:
                similarity += (matched_ports / total_ports) * 0.3  # 30%权重
                features_matched += matched_ports
                total_features += total_ports
        
        # 检查协议匹配
        if hasattr(real_expert, 'protocols') and 'protocols' in self.simulation_features:
            expert_protocols = getattr(real_expert, 'protocols', [])
            honeypot_protocols = self.simulation_features.get('protocols', [])
            matched_protocols = len(set(expert_protocols) & set(honeypot_protocols))
            total_protocols = len(set(expert_protocols) | set(honeypot_protocols))
            
            if total_protocols > 0:
                similarity += (matched_protocols / total_protocols) * 0.3  # 30%权重
                features_matched += matched_protocols
                total_features += total_protocols
        
        # 检查响应包格式匹配
        if hasattr(real_expert, 'response_patterns') and 'response_patterns' in self.simulation_features:
            expert_patterns = getattr(real_expert, 'response_patterns', [])
            honeypot_patterns = self.simulation_features.get('response_patterns', [])
            matched_patterns = 0
            
            for pattern in honeypot_patterns:
                if any(self._pattern_similarity(pattern, exp_pattern) > 0.7 
                      for exp_pattern in expert_patterns):
                    matched_patterns += 1
            
            total_patterns = max(len(expert_patterns), len(honeypot_patterns), 1)
            similarity += (matched_patterns / total_patterns) * 0.4  # 40%权重
            features_matched += matched_patterns
            total_features += total_patterns
        
        # 计算总体相似度
        self.similarity_score = similarity
        
        # 计算特征重合度
        if total_features > 0:
            feature_similarity = features_matched / total_features
        else:
            feature_similarity = 0.5  # 默认值
        
        # 综合相似度（加权平均）
        final_similarity = similarity * 0.7 + feature_similarity * 0.3
        
        return min(final_similarity, 1.0)
    
    def _pattern_similarity(self, pattern1: Any, pattern2: Any) -> float:
        """计算模式相似度"""
        # 简化实现，实际应根据具体模式格式计算
        if isinstance(pattern1, dict) and isinstance(pattern2, dict):
            common_keys = set(pattern1.keys()) & set(pattern2.keys())
            all_keys = set(pattern1.keys()) | set(pattern2.keys())
            if all_keys:
                return len(common_keys) / len(all_keys)
        elif pattern1 == pattern2:
            return 1.0
        return 0.0
    
    def check_camouflage_constraint(self, real_expert: ExpertNode, threshold: float = 0.8) -> bool:
        """检查蜜罐伪装有效性约束（约束8）"""
        similarity = self.calculate_similarity(real_expert)
        return similarity >= threshold


# 节点工厂类
class NodeFactory:
    """节点工厂，用于创建不同类型的节点"""
    
    @staticmethod
    def create_terminal_node(
        node_id: str,
        node_type: str = "terminal",
        name: str = "",
        critical_level: float = 1.0,
        resources: Dict[str, float] = None,
        cost: float = 0.0,
        security_level: float = 0.0,
        threat_level: float = 0.0,
        position: Tuple[float, float] = (0.0, 0.0)
    ) -> TerminalNode:
        """创建终端节点"""
        if resources is None:
            resources = {
                "cpu": 4.0,
                "memory": 16.0,
                "bandwidth": 1000.0,
                "storage": 100.0
            }
        
        # 创建节点
        node = TerminalNode(
            node_id=node_id,
            node_type=node_type,
            name=name if name else f"{node_type}_{node_id}",
            coordinates=position,
            physical_capacity={
                "max_cpu": resources.get("cpu", 4.0),
                "max_memory": resources.get("memory", 16.0),
                "max_bandwidth": resources.get("bandwidth", 1000.0),
                "max_storage": resources.get("storage", 100.0)
            },
            costs={
                "hardware": cost,
                "deployment": cost * 0.2,  # 部署成本为硬件成本的20%
                "maintenance": cost * 0.1,  # 年维护成本为硬件成本的10%
                "software": cost * 0.3  # 软件许可成本为硬件成本的30%
            },
            security={
                "protection_level": security_level,
                "threat_level": threat_level,
                "vulnerabilities": [],
                "is_protected": False,
                "security_group": "terminal"
            },
            critical_level=critical_level,
            service_type=node_type
        )
        
        return node
    
    @staticmethod
    def create_steiner_node(
        node_id: str,
        name: str = "",
        position: Tuple[float, float] = (0.0, 0.0),
        deployable: bool = True,
        deployment_cost: float = 1000.0
    ) -> SteinerNode:
        """创建斯坦纳节点"""
        node = SteinerNode(
            node_id=node_id,
            node_type="steiner",
            name=name if name else f"steiner_{node_id}",
            coordinates=position,
            physical_capacity={
                "max_cpu": 8.0,
                "max_memory": 32.0,
                "max_bandwidth": 2000.0,
                "max_storage": 500.0
            },
            costs={
                "hardware": deployment_cost * 0.8,  # 硬件成本为部署成本的80%
                "deployment": deployment_cost,
                "maintenance": deployment_cost * 0.08,  # 年维护成本为部署成本的8%
                "software": 0.0  # 软件成本（如有）
            },
            security={
                "protection_level": 0.6,
                "threat_level": 0.2,
                "vulnerabilities": [],
                "is_protected": False,
                "security_group": "steiner"
            },
            deployable=deployable,
            deployment_cost=deployment_cost
        )
        
        return node
    
    @staticmethod
    def create_gate_node(
        node_id: str,
        name: str = "",
        position: Tuple[float, float] = (0.0, 0.0),
        load_balancing: bool = True
    ) -> GateNode:
        """创建门控节点"""
        node = GateNode(
            node_id=node_id,
            node_type="gate",
            name=name if name else f"gate_{node_id}",
            coordinates=position,
            physical_capacity={
                "max_cpu": 16.0,
                "max_memory": 64.0,
                "max_bandwidth": 5000.0,
                "max_storage": 200.0
            },
            costs={
                "hardware": 20000.0,
                "deployment": 5000.0,
                "maintenance": 2000.0,
                "software": 5000.0
            },
            security={
                "protection_level": 0.9,
                "threat_level": 0.1,
                "vulnerabilities": [],
                "is_protected": True,
                "security_group": "gate"
            },
            critical_level=1.0,
            service_type="gate",
            load_balancing=load_balancing
        )
        
        return node
    
    @staticmethod
    def create_expert_node(
        node_id: str,
        is_real: bool = True,
        name: str = "",
        position: Tuple[float, float] = (0.0, 0.0),
        expertise_domain: str = "general",
        activation_probability: float = 0.8
    ) -> ExpertNode:
        """创建专家节点"""
        node_type = "expert_real" if is_real else "expert_honeypot"
        cost = 15000.0 if is_real else 8000.0
        
        node = ExpertNode(
            node_id=node_id,
            node_type=node_type,
            name=name if name else f"{node_type}_{node_id}",
            coordinates=position,
            physical_capacity={
                "max_cpu": 12.0,
                "max_memory": 48.0,
                "max_bandwidth": 3000.0,
                "max_storage": 300.0
            },
            costs={
                "hardware": cost,
                "deployment": cost * 0.25,
                "maintenance": cost * 0.12,
                "software": cost * 0.35
            },
            security={
                "protection_level": 0.85 if is_real else 0.7,
                "threat_level": 0.15 if is_real else 0.3,
                "vulnerabilities": [],
                "is_protected": is_real,
                "security_group": "expert"
            },
            critical_level=0.9 if is_real else 0.6,
            service_type="expert",
            is_real=is_real,
            expertise_domain=expertise_domain,
            activation_probability=activation_probability,
            model_size=2.5  # GB
        )
        
        return node


# 遗传算法相关配置
class GeneticAlgorithmConfig:
    """遗传算法配置类"""
    
    DEFAULT_CONFIG = {
        "population_size": 100,        # 种群大小
        "generations": 200,            # 迭代代数
        "crossover_rate": 0.85,        # 交叉概率
        "mutation_rate": 0.15,         # 变异概率
        "elite_size": 10,              # 精英保留数量
        "tournament_size": 5,          # 锦标赛选择的大小
        "max_terminals_per_node": 3,   # 每个物理节点最多部署的终端数
        "min_coverage_ratio": 0.95,    # 最小覆盖比例
        "early_stop_generations": 50,   # 早停代数（如果没有改进）
        "min_fitness_improvement": 0.001,  # 最小适应度改进阈值
        "weight_security": 0.4,        # 安全权重
        "weight_cost": 0.3,            # 成本权重
        "weight_performance": 0.3,     # 性能权重
        "penalty_coverage": 100.0,     # 覆盖约束违反惩罚
        "penalty_resource": 50.0,      # 资源约束违反惩罚
        "penalty_distance": 30.0       # 距离约束违反惩罚
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化遗传算法配置"""
        if config_file and self._config_file_exists(config_file):
            self.config = self._load_config_from_file(config_file)
        else:
            self.config = self.DEFAULT_CONFIG.copy()
    
    def _config_file_exists(self, config_file: str) -> bool:
        """检查配置文件是否存在"""
        import os
        return os.path.exists(config_file)
    
    def _load_config_from_file(self, config_file: str) -> Dict:
        """从配置文件加载配置"""
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if config_data and "genetic_algorithm" in config_data:
                loaded_config = config_data["genetic_algorithm"]
                # 合并默认配置和加载的配置
                merged_config = self.DEFAULT_CONFIG.copy()
                merged_config.update(loaded_config)
                return merged_config
            
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f" 加载配置文件失败: {e}，使用默认配置")
            return self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config[key] = value
    
    def save_to_file(self, config_file: str) -> bool:
        """保存配置到文件"""
        try:
            config_data = {"genetic_algorithm": self.config}
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def __str__(self) -> str:
        """返回配置的字符串表示"""
        config_str = "遗传算法配置:\n"
        for key, value in self.config.items():
            config_str += f"  {key}: {value}\n"
        return config_str


# 测试函数
def test_node_creation():
    """测试节点创建"""
    print("测试节点创建...")
    print("=" * 50)
    
    # 测试终端节点
    terminal = NodeFactory.create_terminal_node(
        node_id="terminal_001",
        node_type="database",
        name="主数据库节点",
        critical_level=0.9,
        resources={"cpu": 8.0, "memory": 32.0, "bandwidth": 2000.0, "storage": 500.0},
        cost=20000.0,
        security_level=0.85,
        threat_level=0.2,
        position=(10.5, 20.3)
    )
    
    print(f" 终端节点创建成功: {terminal.name}")
    print(f"  节点ID: {terminal.node_id}")
    print(f"  节点类型: {terminal.node_type}")
    print(f"  物理容量: {terminal.physical_capacity}")
    print(f"  成本: {terminal.costs}")
    
    # 测试斯坦纳节点
    steiner = NodeFactory.create_steiner_node(
        node_id="steiner_001",
        name="斯坦纳节点1",
        position=(15.2, 18.7),
        deployable=True,
        deployment_cost=5000.0
    )
    
    print(f"\n 斯坦纳节点创建成功: {steiner.name}")
    print(f"  可部署蜜罐: {steiner.deployable}")
    print(f"  部署成本: {steiner.deployment_cost}")
    
    # 测试专家节点
    expert_real = NodeFactory.create_expert_node(
        node_id="expert_001",
        is_real=True,
        name="真实专家节点",
        position=(5.1, 12.3),
        expertise_domain="security",
        activation_probability=0.9
    )
    
    print(f"\n 专家节点创建成功: {expert_real.name}")
    print(f"  是否为真实节点: {expert_real.is_real}")
    print(f"  专家领域: {expert_real.expertise_domain}")
    
    # 测试遗传算法配置
    ga_config = GeneticAlgorithmConfig()
    print(f"\n{ga_config}")
    
    # 检查关键参数
    critical_params = ['population_size', 'generations', 'crossover_rate', 'mutation_rate']
    print("\n关键参数检查:")
    for param in critical_params:
        value = ga_config.get(param)
        if param == 'population_size' and value < 50:
            print(f"    {param}: {value} (建议 >= 50)")
        elif param == 'generations' and value < 100:
            print(f"    {param}: {value} (建议 >= 100)")
        else:
            print(f"   {param}: {value}")
    
    print("\n" + "=" * 50)
    print(" 所有测试通过")


if __name__ == "__main__":
    test_node_creation()