"""
攻击定义模块
定义MoE系统中的攻击类型、威胁等级和攻击向量
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
from enum import Enum
import random
from datetime import datetime, timedelta


class ThreatLevel(Enum):
    """威胁等级枚举"""
    LOW = 1      # 低风险 (CVSS < 4.0)
    MEDIUM = 2   # 中风险 (4.0 ≤ CVSS < 7.0)
    HIGH = 3     # 高风险 (CVSS ≥ 7.0)
    CRITICAL = 4 # 关键风险 (CVSS ≥ 9.0)
    
    @classmethod
    def from_cvss_score(cls, score: float) -> ThreatLevel:
        """根据CVSS评分确定威胁等级"""
        if score >= 9.0:
            return cls.CRITICAL
        elif score >= 7.0:
            return cls.HIGH
        elif score >= 4.0:
            return cls.MEDIUM
        else:
            return cls.LOW
    
    def get_coverage_requirement(self) -> float:
        """获取该威胁等级所需的覆盖度要求"""
        requirements = {
            ThreatLevel.LOW: 0.6,
            ThreatLevel.MEDIUM: 0.75,
            ThreatLevel.HIGH: 0.9,
            ThreatLevel.CRITICAL: 0.95
        }
        return requirements.get(self, 0.6)
    
    def get_weight(self) -> float:
        """获取威胁权重"""
        weights = {
            ThreatLevel.LOW: 0.1,
            ThreatLevel.MEDIUM: 0.3,
            ThreatLevel.HIGH: 0.6,
            ThreatLevel.CRITICAL: 0.9
        }
        return weights.get(self, 0.1)


class AttackVector(Enum):
    """攻击向量枚举"""
    GATE_PROBING = "gate_probing"           # 门控探测
    EXPERT_STEALING = "expert_stealing"     # 专家窃取
    DOS = "dos"                             # 拒绝服务攻击
    DATA_POISONING = "data_poisoning"       # 数据投毒
    BACKDOOR_INSERTION = "backdoor_insertion" # 后门植入
    MODEL_INVERSION = "model_inversion"     # 模型逆向
    MEMBERSHIP_INFERENCE = "membership_inference" # 成员推理
    SCANNING = "scanning"                   # 扫描探测
    
    def get_difficulty(self) -> float:
        """获取攻击难度（0-1，越高越难）"""
        difficulties = {
            AttackVector.SCANNING: 0.1,
            AttackVector.GATE_PROBING: 0.3,
            AttackVector.EXPERT_STEALING: 0.6,
            AttackVector.DOS: 0.4,
            AttackVector.DATA_POISONING: 0.7,
            AttackVector.BACKDOOR_INSERTION: 0.8,
            AttackVector.MODEL_INVERSION: 0.5,
            AttackVector.MEMBERSHIP_INFERENCE: 0.6
        }
        return difficulties.get(self, 0.5)
    
    def get_success_rate(self, security_level: float) -> float:
        """根据安全级别计算攻击成功率"""
        base_rate = 1.0 - self.get_difficulty()
        # 安全级别越高，成功率越低
        adjusted_rate = base_rate * (1.0 - security_level * 0.8)  # 安全级别影响最多80%
        return max(0.0, min(1.0, adjusted_rate))


@dataclass
class Vulnerability:
    """漏洞定义"""
    cve_id: str
    description: str
    cvss_score: float
    affected_components: List[str]  # 受影响的组件类型列表
    exploit_available: bool = False
    patch_available: bool = True
    
    def get_threat_level(self) -> ThreatLevel:
        """获取漏洞的威胁等级"""
        return ThreatLevel.from_cvss_score(self.cvss_score)
    
    def is_exploitable(self, component_type: str) -> bool:
        """检查是否对特定组件类型可利用"""
        return (self.exploit_available and 
                component_type in self.affected_components)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "cve_id": self.cve_id,
            "description": self.description,
            "cvss_score": self.cvss_score,
            "affected_components": self.affected_components,
            "exploit_available": self.exploit_available,
            "patch_available": self.patch_available
        }


@dataclass
class Attack:
    """攻击实例"""
    attack_id: str
    attack_vector: AttackVector
    source_node: Optional[str] = None  # 攻击源节点ID
    target_nodes: List[str] = field(default_factory=list)  # 目标节点ID列表
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: float = 0.0  # 持续时间（秒）
    
    # 攻击参数
    parameters: Dict[str, Any] = field(default_factory=lambda: {
        "intensity": 1.0,  # 攻击强度
        "stealth_level": 0.5,  # 隐蔽程度
        "persistence": 0.3,  # 持久性
    })
    
    # 攻击结果
    success: bool = False
    detected: bool = False
    intercepted: bool = False
    damage_level: float = 0.0  # 造成的损害程度（0-1）
    
    # 攻击路径
    attack_path: List[str] = field(default_factory=list)  # 攻击经过的节点ID列表
    exploited_vulnerabilities: List[Vulnerability] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.attack_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.attack_id = f"attack_{self.attack_vector.value}_{timestamp}"
    
    def start(self):
        """开始攻击"""
        self.start_time = datetime.now()
    
    def end(self, success: bool = False, detected: bool = False):
        """结束攻击"""
        self.end_time = datetime.now()
        self.success = success
        self.detected = detected
        
        if self.start_time and self.end_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    def add_to_path(self, node_id: str):
        """添加节点到攻击路径"""
        if node_id not in self.attack_path:
            self.attack_path.append(node_id)
    
    def add_vulnerability(self, vulnerability: Vulnerability):
        """添加被利用的漏洞"""
        if vulnerability not in self.exploited_vulnerabilities:
            self.exploited_vulnerabilities.append(vulnerability)
    
    def calculate_damage(self) -> float:
        """计算攻击造成的损害"""
        # 基础损害基于攻击向量
        base_damage = {
            AttackVector.GATE_PROBING: 0.3,
            AttackVector.EXPERT_STEALING: 0.8,
            AttackVector.DOS: 0.5,
            AttackVector.DATA_POISONING: 0.7,
            AttackVector.BACKDOOR_INSERTION: 0.9,
            AttackVector.MODEL_INVERSION: 0.4,
            AttackVector.MEMBERSHIP_INFERENCE: 0.6,
            AttackVector.SCANNING: 0.1
        }.get(self.attack_vector, 0.3)
        
        # 考虑攻击强度
        intensity = self.parameters.get("intensity", 1.0)
        base_damage *= intensity
        
        # 考虑是否成功
        if not self.success:
            base_damage *= 0.1  # 失败攻击的损害降低
        
        # 考虑是否被检测到
        if self.detected:
            base_damage *= 0.5  # 被检测到的攻击损害降低
        
        # 考虑漏洞利用
        vuln_multiplier = 1.0
        for vuln in self.exploited_vulnerabilities:
            vuln_multiplier *= (1.0 + vuln.cvss_score / 10.0)
        
        self.damage_level = min(1.0, base_damage * vuln_multiplier)
        return self.damage_level
    
    def get_attack_cost(self, node_costs: Dict[str, float]) -> float:
        """计算攻击成本（对防御方造成的成本）"""
        base_cost = 0.0
        
        # 遍历攻击路径上的节点
        for node_id in self.attack_path:
            if node_id in node_costs:
                # 如果节点被攻击，产生相应成本
                node_cost = node_costs[node_id]
                
                # 根据攻击类型调整成本
                if self.attack_vector == AttackVector.DOS:
                    base_cost += node_cost * 0.5  # DoS攻击造成50%节点成本损失
                elif self.attack_vector == AttackVector.EXPERT_STEALING:
                    base_cost += node_cost * 0.8  # 专家窃取造成80%损失
                else:
                    base_cost += node_cost * 0.3  # 其他攻击造成30%损失
        
        # 考虑攻击成功与否
        if self.success:
            base_cost *= 2.0
        
        return base_cost
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "attack_id": self.attack_id,
            "attack_vector": self.attack_vector.value,
            "source_node": self.source_node,
            "target_nodes": self.target_nodes,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "parameters": self.parameters,
            "success": self.success,
            "detected": self.detected,
            "intercepted": self.intercepted,
            "damage_level": self.damage_level,
            "attack_path": self.attack_path,
            "exploited_vulnerabilities": [v.to_dict() for v in self.exploited_vulnerabilities]
        }


@dataclass
class AttackScenario:
    """攻击场景（一组相关攻击）"""
    scenario_id: str
    description: str
    attack_vectors: List[AttackVector]
    target_types: List[str]  # 目标类型列表
    probability: float = 0.5  # 场景发生概率
    
    # 场景参数
    min_attacks: int = 1
    max_attacks: int = 10
    time_window_hours: int = 24  # 攻击时间窗口
    
    # 攻击生成参数
    attack_interval_min: int = 60  # 攻击最小间隔（秒）
    attack_interval_max: int = 3600  # 攻击最大间隔（秒）
    
    def generate_attacks(self, 
                        available_targets: List[str],
                        start_time: datetime = None,
                        num_attacks: int = None) -> List[Attack]:
        """生成该场景下的攻击序列"""
        if not start_time:
            start_time = datetime.now()
        
        if num_attacks is None:
            num_attacks = random.randint(self.min_attacks, self.max_attacks)
        
        attacks = []
        current_time = start_time
        
        for i in range(num_attacks):
            # 选择攻击向量
            attack_vector = random.choice(self.attack_vectors)
            
            # 选择目标（可能有多个）
            num_targets = random.randint(1, min(3, len(available_targets)))
            target_nodes = random.sample(available_targets, num_targets)
            
            # 创建攻击
            attack = Attack(
                attack_id=f"{self.scenario_id}_attack_{i+1}",
                attack_vector=attack_vector,
                target_nodes=target_nodes,
                start_time=current_time,
                parameters={
                    "intensity": random.uniform(0.5, 1.0),
                    "stealth_level": random.uniform(0.3, 0.8),
                    "persistence": random.uniform(0.2, 0.6),
                }
            )
            
            attacks.append(attack)
            
            # 更新时间
            interval = random.randint(self.attack_interval_min, self.attack_interval_max)
            current_time += timedelta(seconds=interval)
        
        return attacks
    
    def get_risk_score(self, system_security_level: float) -> float:
        """计算场景风险评分"""
        # 基础风险 = 场景概率 * 攻击向量平均难度
        avg_difficulty = sum(av.get_difficulty() for av in self.attack_vectors) / len(self.attack_vectors)
        base_risk = self.probability * avg_difficulty
        
        # 调整风险（安全级别越高，风险越低）
        adjusted_risk = base_risk * (1.0 - system_security_level * 0.7)
        
        return min(1.0, adjusted_risk)


class AttackSimulator:
    """攻击模拟器"""
    
    def __init__(self, scenarios: List[AttackScenario]):
        self.scenarios = scenarios
        self.attack_log: List[Attack] = []
        self.current_time = datetime.now()
    
    def simulate_attacks(self, 
                        duration_hours: int = 24,
                        target_nodes: List[str] = None) -> List[Attack]:
        """模拟一段时间内的攻击"""
        end_time = self.current_time + timedelta(hours=duration_hours)
        all_attacks = []
        
        # 根据场景概率决定哪些场景会发生
        for scenario in self.scenarios:
            if random.random() < scenario.probability:
                # 该场景会发生，生成攻击
                scenario_attacks = scenario.generate_attacks(
                    available_targets=target_nodes or [],
                    start_time=self.current_time
                )
                all_attacks.extend(scenario_attacks)
        
        # 按时间排序
        all_attacks.sort(key=lambda x: x.start_time)
        
        # 模拟攻击过程
        for attack in all_attacks:
            # 模拟攻击结果（这里简化处理，实际应根据系统防御能力计算）
            attack.success = random.random() > 0.5  # 50%成功率
            attack.detected = random.random() < 0.3  # 30%检测率
            attack.intercepted = attack.detected and random.random() < 0.7  # 检测到的情况下70%被拦截
            
            # 计算损害
            attack.calculate_damage()
            
            self.attack_log.append(attack)
        
        self.current_time = end_time
        return all_attacks
    
    def get_attack_statistics(self) -> Dict:
        """获取攻击统计信息"""
        if not self.attack_log:
            return {}
        
        total_attacks = len(self.attack_log)
        successful_attacks = sum(1 for a in self.attack_log if a.success)
        detected_attacks = sum(1 for a in self.attack_log if a.detected)
        intercepted_attacks = sum(1 for a in self.attack_log if a.intercepted)
        
        # 按攻击向量分类
        by_vector = {}
        for attack in self.attack_log:
            vec = attack.attack_vector.value
            if vec not in by_vector:
                by_vector[vec] = 0
            by_vector[vec] += 1
        
        # 计算平均损害
        avg_damage = sum(a.damage_level for a in self.attack_log) / total_attacks
        
        return {
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "success_rate": successful_attacks / total_attacks if total_attacks > 0 else 0,
            "detection_rate": detected_attacks / total_attacks if total_attacks > 0 else 0,
            "interception_rate": intercepted_attacks / total_attacks if total_attacks > 0 else 0,
            "attacks_by_vector": by_vector,
            "average_damage": avg_damage,
            "total_damage": sum(a.damage_level for a in self.attack_log)
        }


# 预定义攻击场景
class MoEAttackScenarios:
    """MoE系统预定义攻击场景"""
    
    @staticmethod
    def get_scenarios() -> List[AttackScenario]:
        """获取所有预定义攻击场景"""
        return [
            AttackScenario(
                scenario_id="scenario_1",
                description="门控探测与专家窃取组合攻击",
                attack_vectors=[
                    AttackVector.GATE_PROBING,
                    AttackVector.EXPERT_STEALING
                ],
                target_types=["gate", "expert_real"],
                probability=0.7,
                min_attacks=2,
                max_attacks=5
            ),
            AttackScenario(
                scenario_id="scenario_2",
                description="大规模DoS攻击",
                attack_vectors=[AttackVector.DOS],
                target_types=["gate", "expert_real"],
                probability=0.4,
                min_attacks=10,
                max_attacks=50,
                attack_interval_min=10,
                attack_interval_max=300
            ),
            AttackScenario(
                scenario_id="scenario_3",
                description="隐蔽的数据投毒与后门植入",
                attack_vectors=[
                    AttackVector.DATA_POISONING,
                    AttackVector.BACKDOOR_INSERTION
                ],
                target_types=["expert_real"],
                probability=0.3,
                min_attacks=1,
                max_attacks=3
            ),
            AttackScenario(
                scenario_id="scenario_4",
                description="扫描与信息收集",
                attack_vectors=[AttackVector.SCANNING],
                target_types=["gate", "expert_real", "steiner"],
                probability=0.9,
                min_attacks=5,
                max_attacks=20,
                attack_interval_min=30,
                attack_interval_max=600
            )
        ]


# 测试代码
if __name__ == "__main__":
    # 测试攻击定义
    attack = Attack(
        attack_id="test_attack_1",
        attack_vector=AttackVector.GATE_PROBING,
        target_nodes=["gate_1", "expert_1"]
    )
    print(f"创建攻击: {attack.attack_id}, 攻击向量: {attack.attack_vector.value}")
    
    # 测试漏洞
    vuln = Vulnerability(
        cve_id="CVE-2024-12345",
        description="MoE门控路由信息泄露漏洞",
        cvss_score=7.5,
        affected_components=["gate"],
        exploit_available=True
    )
    print(f"漏洞威胁等级: {vuln.get_threat_level()}")
    
    # 测试攻击场景
    scenarios = MoEAttackScenarios.get_scenarios()
    print(f"预定义攻击场景数量: {len(scenarios)}")