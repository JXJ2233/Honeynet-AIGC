'''import random
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set, Deque
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime
from collections import defaultdict, deque
import warnings
import math
from heapq import heappush, heappop

warnings.filterwarnings('ignore')


class AttackType(Enum):
    """攻击类型枚举"""
    SCANNING = "scanning"
    LATERAL_MOVEMENT = "lateral"
    PRIVILEGE_ESCALATION = "priv"
    DATA_EXFILTRATION = "exfil"
    DDOS = "ddos"
    ZERO_DAY = "zero_day"  # 零日攻击
    RANSOMWARE = "ransomware"  # 勒索软件攻击


class ExpertType(Enum):
    """MoE专家类型枚举"""
    SCANNING_EXPERT = "scanning_expert"
    LATERAL_EXPERT = "lateral_expert"
    PRIVILEGE_EXPERT = "privilege_expert"
    DATA_EXFIL_EXPERT = "data_exfil_expert"
    DDOS_EXPERT = "ddos_expert"
    ZERO_DAY_EXPERT = "zero_day_expert"  # 零日攻击专家
    RANSOMWARE_EXPERT = "ransomware_expert"  # 勒索软件专家
    HYBRID_EXPERT = "hybrid_expert"  # 混合专家
    ANOMALY_EXPERT = "anomaly_expert"  # 异常检测专家
    GENERAL_EXPERT = "general_expert"


@dataclass
class AttackContext:
    """攻击上下文信息"""
    attacker_id: str
    attack_path: List[str]
    attack_pattern: str
    attack_intensity: float
    time_of_day: float  # 0-24小时
    previous_actions: List[str]
    resources_accessed: Set[str]


@dataclass
class AttackAction:
    """攻击动作"""
    attack_id: str
    attack_type: AttackType
    source_node: str
    target_node: str
    timestamp: float
    success: bool
    context: Optional[AttackContext] = None
    detected_by: Optional[str] = None
    detection_latency: float = 0.0
    false_positive: bool = False
    false_negative: bool = False
    confidence_score: float = 0.0  # 检测置信度


@dataclass
class AttackPath:
    """攻击路径"""
    path_id: str
    attacker_id: str
    start_node: str
    target_node: str
    actions: List[AttackAction]
    total_steps: int
    captured: bool = False
    capture_step: int = -1
    expert_type_detected: Optional[str] = None
    detection_confidence: float = 0.0
    evasive_actions: int = 0


class CollaborativeDetectionSystem:
    """协同检测系统"""

    def __init__(self):
        self.shared_knowledge = defaultdict(dict)
        self.attack_patterns = defaultdict(list)
        self.suspicious_nodes = set()
        self.threat_intelligence = {
            'recent_attacks': deque(maxlen=100),
            'attack_correlations': defaultdict(float),
            'node_risk_scores': defaultdict(float)
        }
        self.network = None  # 需要在外部设置

    def share_information(self, node_id: str, attack_type: AttackType,
                         timestamp: float, confidence: float):
        """共享威胁信息"""
        key = f"{node_id}_{attack_type.value}_{timestamp}"
        self.shared_knowledge[key] = {
            'node_id': node_id,
            'attack_type': attack_type,
            'timestamp': timestamp,
            'confidence': confidence
        }

    def get_relevant_threats(self, node_id: str, time_window: float = 300) -> List[Dict]:
        """获取相关威胁信息"""
        current_time = datetime.now().timestamp()
        relevant_threats = []

        for key, threat in self.shared_knowledge.items():
            if current_time - threat['timestamp'] <= time_window:
                # 计算威胁相关性
                distance = self.calculate_network_distance(node_id, threat['node_id'])
                if distance <= 3:  # 3跳以内的威胁相关
                    threat['distance'] = distance
                    relevant_threats.append(threat)

        return relevant_threats

    def calculate_network_distance(self, node1: str, node2: str) -> int:
        """计算网络距离"""
        if self.network is None:
            return float('inf')
        try:
            return len(nx.shortest_path(self.network, node1, node2)) - 1
        except:
            return float('inf')

    def update_attack_patterns(self, attack_path: AttackPath):
        """更新攻击模式"""
        attack_types = [action.attack_type for action in attack_path.actions]
        pattern_key = "_".join([at.value for at in attack_types[:3]])
        self.attack_patterns[pattern_key].append(attack_path.attacker_id)

    def detect_pattern_anomaly(self, current_actions: List[AttackType]) -> float:
        """检测模式异常"""
        pattern_key = "_".join([at.value for at in current_actions[:3]])
        if pattern_key in self.attack_patterns:
            frequency = len(self.attack_patterns[pattern_key])
            return 1.0 - math.exp(-frequency / 10.0)  # 常见模式置信度更高
        else:
            # 新模式的异常分数
            return 0.7


class AdaptiveMoEExpertHoneypot:
    """自适应MoE专家蜜罐"""

    def __init__(self, node_id: str, expert_type: ExpertType,
                 detection_threshold: float = 0.6, learning_rate: float = 0.05):
        self.node_id = node_id
        self.expert_type = expert_type
        self.base_threshold = detection_threshold
        self.detection_threshold = detection_threshold
        self.learning_rate = learning_rate

        # 统计信息
        self.detection_counts = 0
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.detection_history = deque(maxlen=100)

        # 自适应参数
        self.attack_type_stats = defaultdict(lambda: {'detected': 0, 'total': 0})
        self.context_weights = {
            'time_of_day': 0.1,
            'attack_pattern': 0.3,
            'intensity': 0.2,
            'path_length': 0.1,
            'node_importance': 0.2,
            'threat_intelligence': 0.1
        }

        # 优化的专家能力映射
        self.expert_capabilities = self._init_enhanced_capabilities()

        # 协同检测系统
        self.collaboration_system = None

    def set_collaboration_system(self, system: CollaborativeDetectionSystem):
        """设置协同检测系统"""
        self.collaboration_system = system

    def _init_enhanced_capabilities(self) -> Dict[AttackType, float]:
        """初始化增强的专家能力映射"""
        if self.expert_type == ExpertType.SCANNING_EXPERT:
            return {
                AttackType.SCANNING: 0.92,
                AttackType.LATERAL_MOVEMENT: 0.40,
                AttackType.PRIVILEGE_ESCALATION: 0.25,
                AttackType.DATA_EXFILTRATION: 0.30,
                AttackType.DDOS: 0.20,
                AttackType.ZERO_DAY: 0.15,
                AttackType.RANSOMWARE: 0.20
            }
        elif self.expert_type == ExpertType.LATERAL_EXPERT:
            return {
                AttackType.SCANNING: 0.45,
                AttackType.LATERAL_MOVEMENT: 0.88,
                AttackType.PRIVILEGE_ESCALATION: 0.50,
                AttackType.DATA_EXFILTRATION: 0.40,
                AttackType.DDOS: 0.30,
                AttackType.ZERO_DAY: 0.25,
                AttackType.RANSOMWARE: 0.35
            }
        elif self.expert_type == ExpertType.PRIVILEGE_EXPERT:
            return {
                AttackType.SCANNING: 0.30,
                AttackType.LATERAL_MOVEMENT: 0.50,
                AttackType.PRIVILEGE_ESCALATION: 0.90,
                AttackType.DATA_EXFILTRATION: 0.40,
                AttackType.DDOS: 0.25,
                AttackType.ZERO_DAY: 0.30,
                AttackType.RANSOMWARE: 0.40
            }
        elif self.expert_type == ExpertType.DATA_EXFIL_EXPERT:
            return {
                AttackType.SCANNING: 0.40,
                AttackType.LATERAL_MOVEMENT: 0.45,
                AttackType.PRIVILEGE_ESCALATION: 0.50,
                AttackType.DATA_EXFILTRATION: 0.85,
                AttackType.DDOS: 0.35,
                AttackType.ZERO_DAY: 0.35,
                AttackType.RANSOMWARE: 0.45
            }
        elif self.expert_type == ExpertType.DDOS_EXPERT:
            return {
                AttackType.SCANNING: 0.20,
                AttackType.LATERAL_MOVEMENT: 0.30,
                AttackType.PRIVILEGE_ESCALATION: 0.20,
                AttackType.DATA_EXFILTRATION: 0.30,
                AttackType.DDOS: 0.92,
                AttackType.ZERO_DAY: 0.25,
                AttackType.RANSOMWARE: 0.30
            }
        elif self.expert_type == ExpertType.ZERO_DAY_EXPERT:
            return {
                AttackType.SCANNING: 0.35,
                AttackType.LATERAL_MOVEMENT: 0.40,
                AttackType.PRIVILEGE_ESCALATION: 0.45,
                AttackType.DATA_EXFILTRATION: 0.40,
                AttackType.DDOS: 0.30,
                AttackType.ZERO_DAY: 0.85,
                AttackType.RANSOMWARE: 0.50
            }
        elif self.expert_type == ExpertType.RANSOMWARE_EXPERT:
            return {
                AttackType.SCANNING: 0.30,
                AttackType.LATERAL_MOVEMENT: 0.45,
                AttackType.PRIVILEGE_ESCALATION: 0.55,
                AttackType.DATA_EXFILTRATION: 0.60,
                AttackType.DDOS: 0.25,
                AttackType.ZERO_DAY: 0.40,
                AttackType.RANSOMWARE: 0.88
            }
        elif self.expert_type == ExpertType.HYBRID_EXPERT:
            return {
                AttackType.SCANNING: 0.70,
                AttackType.LATERAL_MOVEMENT: 0.75,
                AttackType.PRIVILEGE_ESCALATION: 0.70,
                AttackType.DATA_EXFILTRATION: 0.70,
                AttackType.DDOS: 0.65,
                AttackType.ZERO_DAY: 0.60,
                AttackType.RANSOMWARE: 0.65
            }
        elif self.expert_type == ExpertType.ANOMALY_EXPERT:
            return {
                AttackType.SCANNING: 0.65,
                AttackType.LATERAL_MOVEMENT: 0.70,
                AttackType.PRIVILEGE_ESCALATION: 0.65,
                AttackType.DATA_EXFILTRATION: 0.70,
                AttackType.DDOS: 0.60,
                AttackType.ZERO_DAY: 0.75,  # 异常检测擅长零日攻击
                AttackType.RANSOMWARE: 0.75  # 异常检测擅长勒索软件
            }
        else:  # GENERAL_EXPERT
            return {
                AttackType.SCANNING: 0.65,
                AttackType.LATERAL_MOVEMENT: 0.70,
                AttackType.PRIVILEGE_ESCALATION: 0.65,
                AttackType.DATA_EXFILTRATION: 0.65,
                AttackType.DDOS: 0.60,
                AttackType.ZERO_DAY: 0.55,
                AttackType.RANSOMWARE: 0.60
            }

    def detect_attack_with_context(self, attack_type: AttackType,
                                 attack_intensity: float = 1.0,
                                 context: Optional[AttackContext] = None) -> Tuple[bool, bool, bool, float]:
        """
        上下文感知的检测逻辑
        """
        # 基础检测能力
        base_detection_rate = self.expert_capabilities.get(attack_type, 0.5)

        # 考虑攻击强度
        intensity_factor = min(attack_intensity, 1.5)
        adjusted_rate = base_detection_rate * intensity_factor

        # 专家特性加成
        expert_bias = self._calculate_expert_bias(attack_type)
        adjusted_rate *= expert_bias

        # 上下文分析
        context_bonus = 0.0
        if context:
            context_bonus = self._analyze_context(context, attack_type)

        adjusted_rate += context_bonus

        # 协同检测加成
        collaboration_bonus = 0.0
        if self.collaboration_system:
            collaboration_bonus = self._get_collaboration_bonus(attack_type)

        adjusted_rate += collaboration_bonus

        # 自适应阈值调整
        self._adjust_threshold_based_on_history(attack_type)

        # 加入合理随机性
        detection_prob = adjusted_rate + random.uniform(-0.05, 0.05)
        detection_prob = max(0.15, min(0.95, detection_prob))

        # 判断检测结果
        detected = detection_prob > self.detection_threshold

        # 更新统计
        self.attack_type_stats[attack_type]['total'] += 1

        # 误报和漏报逻辑
        false_positive = False
        false_negative = False
        confidence_score = detection_prob

        if detected:
            self.detection_counts += 1
            self.attack_type_stats[attack_type]['detected'] += 1

            # 计算误报率（动态调整）
            fp_rate = self._calculate_fp_rate(attack_type, expert_bias)

            if random.random() < fp_rate:
                false_positive = True
                self.false_positives += 1
                confidence_score *= 0.7  # 误报置信度降低
            else:
                self.true_positives += 1
                confidence_score *= 1.1  # 正确检测置信度增加
        else:
            # 计算漏报率
            fn_rate = self._calculate_fn_rate(attack_type, expert_bias)

            if random.random() < fn_rate:
                false_negative = True
                self.false_negatives += 1

            # 即使未检测到，但如果有强上下文证据，仍标记为低置信度检测
            if context_bonus > 0.15 and detection_prob > self.detection_threshold * 0.8:
                detected = True
                confidence_score = detection_prob * 0.8  # 低置信度检测

        # 记录检测历史
        self.detection_history.append({
            'attack_type': attack_type,
            'detected': detected,
            'fp': false_positive,
            'fn': false_negative,
            'confidence': confidence_score,
            'timestamp': datetime.now().timestamp()
        })

        return detected, false_positive, false_negative, confidence_score

    def _calculate_expert_bias(self, attack_type: AttackType) -> float:
        """计算专家偏置"""
        expert_specializations = {
            ExpertType.SCANNING_EXPERT: AttackType.SCANNING,
            ExpertType.LATERAL_EXPERT: AttackType.LATERAL_MOVEMENT,
            ExpertType.PRIVILEGE_EXPERT: AttackType.PRIVILEGE_ESCALATION,
            ExpertType.DATA_EXFIL_EXPERT: AttackType.DATA_EXFILTRATION,
            ExpertType.DDOS_EXPERT: AttackType.DDOS,
            ExpertType.ZERO_DAY_EXPERT: AttackType.ZERO_DAY,
            ExpertType.RANSOMWARE_EXPERT: AttackType.RANSOMWARE,
            ExpertType.ANOMALY_EXPERT: AttackType.ZERO_DAY  # 异常专家擅长零日攻击
        }

        if self.expert_type in expert_specializations:
            if expert_specializations[self.expert_type] == attack_type:
                return 1.25  # 专家擅长领域加成25%

        # 混合专家对多种攻击有更好表现
        if self.expert_type == ExpertType.HYBRID_EXPERT:
            return 1.15

        return 1.0

    def _analyze_context(self, context: AttackContext, attack_type: AttackType) -> float:
        """分析上下文信息"""
        context_score = 0.0

        # 时间模式分析
        if 2 <= context.time_of_day <= 6:  # 凌晨攻击更可疑
            context_score += 0.05

        # 攻击路径分析
        if len(context.attack_path) > 5:  # 长路径更可疑
            context_score += 0.03

        # 攻击模式分析
        if context.attack_pattern == "aggressive":
            context_score += 0.04
        elif context.attack_pattern == "stealthy":
            context_score += 0.02

        # 资源访问分析
        if len(context.resources_accessed) > 3:
            context_score += 0.03

        return context_score

    def _get_collaboration_bonus(self, attack_type: AttackType) -> float:
        """获取协同检测加成"""
        if not self.collaboration_system:
            return 0.0

        relevant_threats = self.collaboration_system.get_relevant_threats(self.node_id)
        if relevant_threats:
            # 根据相关威胁数量和质量计算加成
            threat_count = len(relevant_threats)
            avg_confidence = sum(t['confidence'] for t in relevant_threats) / threat_count
            return min(0.15, threat_count * 0.02 + avg_confidence * 0.05)

        return 0.0

    def _adjust_threshold_based_on_history(self, attack_type: AttackType):
        """基于历史调整检测阈值"""
        if len(self.detection_history) < 10:
            return

        # 计算最近10次检测的性能
        recent_detections = list(self.detection_history)[-10:]
        tp_count = sum(1 for d in recent_detections if d['detected'] and not d['fp'])
        fp_count = sum(1 for d in recent_detections if d['fp'])

        accuracy = tp_count / max(1, tp_count + fp_count)

        # 动态调整阈值
        if accuracy < 0.8:
            # 准确率低，降低阈值以增加检测
            self.detection_threshold *= (1 - self.learning_rate)
        elif accuracy > 0.95:
            # 准确率高，提高阈值以减少误报
            self.detection_threshold *= (1 + self.learning_rate)

        # 保持在合理范围内
        self.detection_threshold = max(self.base_threshold * 0.7,
                                     min(self.detection_threshold, self.base_threshold * 1.3))

    def _calculate_fp_rate(self, attack_type: AttackType, expert_bias: float) -> float:
        """计算动态误报率"""
        base_fp_rate = 0.03

        # 专家对擅长领域误报率更低
        if expert_bias > 1.2:
            base_fp_rate = 0.01

        # 根据攻击类型调整
        if attack_type in [AttackType.ZERO_DAY, AttackType.RANSOMWARE]:
            base_fp_rate += 0.02  # 新型攻击误报率稍高

        # 根据历史性能调整
        total_detections = self.attack_type_stats[attack_type]['total']
        if total_detections > 0:
            detection_rate = self.attack_type_stats[attack_type]['detected'] / total_detections
            if detection_rate > 0.9:
                base_fp_rate *= 0.8  # 高检测率时降低误报率

        return base_fp_rate

    def _calculate_fn_rate(self, attack_type: AttackType, expert_bias: float) -> float:
        """计算动态漏报率"""
        base_fn_rate = 0.05

        # 专家对擅长领域漏报率更低
        if expert_bias > 1.2:
            base_fn_rate = 0.02

        # 根据攻击类型调整
        if attack_type in [AttackType.ZERO_DAY, AttackType.RANSOMWARE]:
            base_fn_rate += 0.03  # 新型攻击漏报率稍高

        return base_fn_rate


class AdvancedDynamicAttackSimulator:
    """高级动态攻击模拟器"""

    def __init__(self,
                 network_graph: nx.Graph,
                 honeypot_nodes: Dict[str, ExpertType],
                 random_seed: Optional[int] = None):

        if not isinstance(network_graph, nx.Graph):
            raise TypeError("network_graph 必须是 networkx.Graph 实例")

        if not honeypot_nodes:
            raise ValueError("honeypot_nodes 不能为空")

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        self.network = network_graph

        # 协同检测系统
        self.collaboration_system = CollaborativeDetectionSystem()
        self.collaboration_system.network = self.network

        # 初始化专家蜜罐
        self.expert_honeypots: Dict[str, AdaptiveMoEExpertHoneypot] = {}
        for node_id, expert_type in honeypot_nodes.items():
            if node_id in self.network.nodes():
                honeypot = AdaptiveMoEExpertHoneypot(node_id, expert_type)
                honeypot.set_collaboration_system(self.collaboration_system)
                self.expert_honeypots[node_id] = honeypot

        # 优化的攻击参数
        self.attack_parameters = self._init_attack_parameters()

        # 攻击者智能模型
        self.attacker_models = self._init_attacker_models()

        # 初始化统计信息
        self.attack_logs: List[AttackPath] = []
        self.metrics = self._initialize_metrics()

        # 网络结构信息
        self._analyze_network_structure()

        print(f" 高级版MoE动态攻击模拟器初始化完成")
        print(f"   网络节点数: {self.network.number_of_nodes()}")
        print(f"   专家蜜罐数: {len(self.expert_honeypots)}")
        print(f"   协同检测系统: 已启用")

    def _init_attack_parameters(self) -> Dict[AttackType, Dict]:
        """初始化攻击参数"""
        return {
            AttackType.SCANNING: {
                'success_rate': 0.70,
                'intensity': 0.7,
                'max_steps': 30,
                'behavior': 'random',
                'target_preference': 0.2,
                'honeypot_avoidance': 0.3,
                'stealth_level': 0.4,
                'resource_consumption': 0.2
            },
            AttackType.LATERAL_MOVEMENT: {
                'success_rate': 0.60,
                'intensity': 0.8,
                'max_steps': 40,
                'behavior': 'targeted',
                'target_preference': 0.7,
                'honeypot_avoidance': 0.4,
                'stealth_level': 0.6,
                'resource_consumption': 0.3
            },
            AttackType.PRIVILEGE_ESCALATION: {
                'success_rate': 0.45,
                'intensity': 0.9,
                'max_steps': 25,
                'behavior': 'focused',
                'target_preference': 0.6,
                'honeypot_avoidance': 0.5,
                'stealth_level': 0.7,
                'resource_consumption': 0.4
            },
            AttackType.DATA_EXFILTRATION: {
                'success_rate': 0.55,
                'intensity': 0.85,
                'max_steps': 35,
                'behavior': 'stealthy',
                'target_preference': 0.5,
                'honeypot_avoidance': 0.4,
                'stealth_level': 0.8,
                'resource_consumption': 0.5
            },
            AttackType.DDOS: {
                'success_rate': 0.80,
                'intensity': 0.95,
                'max_steps': 20,
                'behavior': 'aggressive',
                'target_preference': 0.4,
                'honeypot_avoidance': 0.2,
                'stealth_level': 0.2,
                'resource_consumption': 0.9
            },
            AttackType.ZERO_DAY: {
                'success_rate': 0.65,
                'intensity': 0.9,
                'max_steps': 30,
                'behavior': 'stealthy',
                'target_preference': 0.8,
                'honeypot_avoidance': 0.6,
                'stealth_level': 0.9,
                'resource_consumption': 0.3
            },
            AttackType.RANSOMWARE: {
                'success_rate': 0.50,
                'intensity': 0.85,
                'max_steps': 25,
                'behavior': 'aggressive',
                'target_preference': 0.7,
                'honeypot_avoidance': 0.3,
                'stealth_level': 0.5,
                'resource_consumption': 0.7
            }
        }

    def _init_attacker_models(self) -> Dict[str, Dict]:
        """初始化攻击者模型"""
        return {
            'script_kiddie': {
                'skill_level': 0.3,
                'persistence': 0.2,
                'adaptability': 0.1,
                'stealth': 0.2,
                'target_selection': 'random',
                'target_selection_weight': 0.5
            },
            'hacker': {
                'skill_level': 0.7,
                'persistence': 0.5,
                'adaptability': 0.6,
                'stealth': 0.7,
                'target_selection': 'strategic',
                'target_selection_weight': 1.0
            },
            'apt_group': {
                'skill_level': 0.9,
                'persistence': 0.9,
                'adaptability': 0.8,
                'stealth': 0.9,
                'target_selection': 'focused',
                'target_selection_weight': 1.2
            },
            'insider_threat': {
                'skill_level': 0.6,
                'persistence': 0.4,
                'adaptability': 0.5,
                'stealth': 0.8,  # 内部威胁更隐蔽
                'target_selection': 'precise',
                'target_selection_weight': 1.1
            }
        }

    def _initialize_metrics(self) -> Dict[str, Any]:
        """初始化统计指标"""
        metrics = {
            'total_attacks': 0,
            'captured_attacks': 0,
            'total_steps': 0,
            'capture_latency': [],
            'attack_type_distribution': defaultdict(int),
            'expert_performance': {},
            'attacker_type_distribution': defaultdict(int),
            'true_positives': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'touch_probability': 0.0,
            'attack_success_rate': 0.0,
            'total_successful_actions': 0,
            'total_action_steps': 0,
            'early_detection_rate': 0.0,  # 新增：早期检测率
            'collaborative_detections': 0,  # 新增：协同检测次数
            'evasion_rate': 0.0  # 新增：攻击规避率
        }

        # 初始化专家性能统计
        for node_id in self.expert_honeypots.keys():
            metrics['expert_performance'][node_id] = {
                'detection_counts': 0,
                'true_positives': 0,
                'false_positives': 0,
                'false_negatives': 0,
                'expert_type': self.expert_honeypots[node_id].expert_type.value,
                'attack_type_detections': defaultdict(int),
                'confidence_scores': [],
                'context_aware_detections': 0
            }

        return metrics

    def _analyze_network_structure(self):
        """分析网络结构"""
        # 计算节点重要性
        self.node_importance = {}

        # 度数中心性
        degree_centrality = nx.degree_centrality(self.network)

        # 介数中心性（对大网络可能耗时，使用近似）
        try:
            betweenness = nx.betweenness_centrality(self.network, k=min(20, self.network.number_of_nodes()))
        except:
            betweenness = {node: 0.0 for node in self.network.nodes()}

        # 接近中心性
        try:
            closeness = nx.closeness_centrality(self.network)
        except:
            closeness = {node: 0.0 for node in self.network.nodes()}

        # 计算综合重要性
        for node in self.network.nodes():
            importance = (
                degree_centrality[node] * 0.3 +
                betweenness[node] * 0.4 +
                closeness[node] * 0.3
            )
            self.node_importance[node] = importance

        # 识别关键节点（前20%）
        sorted_nodes = sorted(self.node_importance.items(), key=lambda x: x[1], reverse=True)
        cutoff = int(len(sorted_nodes) * 0.2)
        self.critical_nodes = {node for node, _ in sorted_nodes[:cutoff]}

    def simulate_attack(self,
                       start_node: str,
                       target_node: str,
                       attack_type: AttackType,
                       attacker_model: str = 'hacker') -> AttackPath:
        """
        智能化的攻击模拟
        """
        if start_node not in self.network.nodes():
            raise ValueError(f"起始节点 {start_node} 不存在")
        if target_node not in self.network.nodes():
            raise ValueError(f"目标节点 {target_node} 不存在")

        path_id = f"attack_{len(self.attack_logs)}_{datetime.now().strftime('%H%M%S')}"
        current_node = start_node

        # 初始化攻击上下文
        context = AttackContext(
            attacker_id=f"attacker_{random.randint(1000, 9999)}",
            attack_path=[current_node],
            attack_pattern=self.attack_parameters[attack_type]['behavior'],
            attack_intensity=self.attack_parameters[attack_type]['intensity'],
            time_of_day=random.uniform(0, 24),  # 随机时间
            previous_actions=[],
            resources_accessed=set()
        )

        path = AttackPath(
            path_id=path_id,
            attacker_id=context.attacker_id,
            start_node=start_node,
            target_node=target_node,
            actions=[],
            total_steps=0
        )

        attack_params = self.attack_parameters[attack_type]
        max_steps = attack_params['max_steps']
        attack_behavior = attack_params['behavior']
        attack_intensity = attack_params['intensity']
        target_preference = attack_params['target_preference']
        honeypot_avoidance = attack_params['honeypot_avoidance']
        stealth_level = attack_params['stealth_level']

        # 攻击者模型参数
        attacker_params = self.attacker_models[attacker_model]

        step = 0
        captured = False
        expert_detected = None
        successful_actions = 0
        evasive_actions = 0
        detection_confidence = 0.0

        # 记录已访问节点
        visited_nodes = set([current_node])

        # 攻击模拟循环
        while step < max_steps and current_node != target_node:
            # 更新攻击上下文
            context.attack_path.append(current_node)

            # 智能选择下一个节点
            next_node = self._intelligent_select_next_node(
                current_node, target_node, attack_type, attack_behavior,
                target_preference, honeypot_avoidance, visited_nodes,
                attacker_params, stealth_level
            )

            visited_nodes.add(next_node)

            # 执行攻击动作
            action_success = self._execute_intelligent_attack(
                current_node, next_node, attack_type, attack_params['success_rate'],
                attacker_params['skill_level']
            )

            if action_success:
                successful_actions += 1
                # 记录访问的资源
                if random.random() < 0.3:
                    context.resources_accessed.add(next_node)

            # 更新攻击者行为（学习）
            self._update_attacker_behavior(attacker_params, step, captured)

            # 检查蜜罐检测
            detected_by = None
            detection_latency = 0.0
            false_positive = False
            false_negative = False
            confidence = 0.0

            if next_node in self.expert_honeypots:
                honeypot = self.expert_honeypots[next_node]
                detected, fp, fn, conf = honeypot.detect_attack_with_context(
                    attack_type, attack_intensity, context
                )

                confidence = conf

                if detected and not fp:  # 真正检测到（非误报）
                    # 检查是否是早期检测（前5步）
                    if step <= 5:
                        self.metrics['early_detection_rate'] += 1

                    # 检查是否是协同检测
                    if conf > 0.8 and self._is_collaborative_detection(next_node, attack_type):
                        self.metrics['collaborative_detections'] += 1

                    captured = True
                    detected_by = next_node
                    expert_detected = honeypot.expert_type.value
                    detection_latency = step + random.uniform(0.5, 3.0)
                    detection_confidence = conf

                    # 更新专家统计
                    if detected_by in self.metrics['expert_performance']:
                        self.metrics['expert_performance'][detected_by]['detection_counts'] += 1
                        self.metrics['expert_performance'][detected_by]['true_positives'] += 1
                        self.metrics['expert_performance'][detected_by]['attack_type_detections'][attack_type.value] += 1
                        self.metrics['expert_performance'][detected_by]['confidence_scores'].append(conf)

                        # 上下文感知检测计数
                        if conf > 0.85:  # 高置信度检测
                            self.metrics['expert_performance'][detected_by]['context_aware_detections'] += 1

                # 记录误报/漏报
                if fp:
                    self.metrics['false_positives'] += 1
                    if next_node in self.metrics['expert_performance']:
                        self.metrics['expert_performance'][next_node]['false_positives'] += 1
                if fn:
                    self.metrics['false_negatives'] += 1
                    if next_node in self.metrics['expert_performance']:
                        self.metrics['expert_performance'][next_node]['false_negatives'] += 1

                false_positive = fp
                false_negative = fn

            # 攻击者可能采取规避动作
            if not captured and step > 3 and random.random() < attacker_params['adaptability'] * 0.3:
                evasive_actions += 1
                # 模拟规避行为（如改变攻击模式）
                context.attack_pattern = "evasive"

            # 记录攻击动作
            action = AttackAction(
                attack_id=f"{path_id}_step_{step}",
                attack_type=attack_type,
                source_node=current_node,
                target_node=next_node,
                timestamp=datetime.now().timestamp() + step,
                success=action_success,
                context=context,
                detected_by=detected_by,
                detection_latency=detection_latency,
                false_positive=false_positive,
                false_negative=false_negative,
                confidence_score=confidence
            )

            path.actions.append(action)
            step += 1
            current_node = next_node

            # 共享威胁情报
            if detected_by:
                self.collaboration_system.share_information(
                    detected_by, attack_type,
                    datetime.now().timestamp(), confidence
                )

            # 如果被捕获，结束攻击
            if captured:
                path.captured = True
                path.capture_step = step
                path.expert_type_detected = expert_detected
                path.detection_confidence = detection_confidence
                path.evasive_actions = evasive_actions
                break

        # 更新路径信息
        path.total_steps = step
        self.attack_logs.append(path)

        # 更新攻击模式库
        self.collaboration_system.update_attack_patterns(path)

        # 更新全局统计
        self._update_metrics(path, attack_type, captured, successful_actions, step, evasive_actions)

        # 更新攻击者类型分布
        self.metrics['attacker_type_distribution'][attacker_model] += 1

        return path

    def _intelligent_select_next_node(self,
                                    current_node: str,
                                    target_node: str,
                                    attack_type: AttackType,
                                    behavior: str,
                                    target_preference: float,
                                    honeypot_avoidance: float,
                                    visited_nodes: Set[str],
                                    attacker_params: Dict,
                                    stealth_level: float) -> str:
        """
        智能化的下一个节点选择
        """
        try:
            neighbors = list(self.network.neighbors(current_node))
        except Exception:
            return current_node

        if not neighbors:
            return current_node

        # 计算每个邻居的得分
        neighbor_scores = []

        for neighbor in neighbors:
            score = 0.0

            # 1. 目标导向得分（考虑攻击者技能）
            if neighbor == target_node:
                score += 5.0 * attacker_params['skill_level']
            else:
                try:
                    distance = nx.shortest_path_length(self.network, neighbor, target_node)
                    if distance > 0:
                        distance_score = 2.0 / distance * target_preference
                        score += distance_score * attacker_params.get('target_selection_weight', 1.0)
                except:
                    pass

            # 2. 蜜罐处理策略（智能规避）
            if neighbor in self.expert_honeypots:
                honeypot = self.expert_honeypots[neighbor]
                honeypot_type = honeypot.expert_type

                # 根据攻击者技能调整规避策略
                avoidance_factor = honeypot_avoidance * attacker_params['stealth']

                # 特定攻击的规避策略
                if attack_type == AttackType.SCANNING and honeypot_type == ExpertType.SCANNING_EXPERT:
                    score -= 3.0 * avoidance_factor
                elif attack_type == AttackType.LATERAL_MOVEMENT and honeypot_type == ExpertType.LATERAL_EXPERT:
                    score -= 4.0 * avoidance_factor
                elif attack_type == AttackType.DATA_EXFILTRATION and honeypot_type == ExpertType.DATA_EXFIL_EXPERT:
                    score -= 5.0 * avoidance_factor
                elif attack_type == AttackType.PRIVILEGE_ESCALATION and honeypot_type == ExpertType.PRIVILEGE_EXPERT:
                    score -= 4.0 * avoidance_factor
                elif attack_type == AttackType.ZERO_DAY and honeypot_type in [ExpertType.ZERO_DAY_EXPERT, ExpertType.ANOMALY_EXPERT]:
                    score -= 4.5 * avoidance_factor
                else:
                    score -= 2.0 * avoidance_factor

            # 3. 节点价值评估
            node_value = self.node_importance.get(neighbor, 0.5)

            # 高价值节点吸引力（但可能防御更强）
            if node_value > 0.7:
                attraction = node_value * 2.0
                # 但高价值节点可能有更强防御
                defense_penalty = node_value * 0.5 if stealth_level < 0.7 else 0
                score += attraction - defense_penalty
            else:
                score += node_value

            # 4. 攻击路径多样性（避免重复访问）
            if neighbor in visited_nodes:
                penalty = -1.5 if attack_type != AttackType.SCANNING else -0.5
                score += penalty

            # 5. 网络拓扑考虑（选择桥接节点）
            neighbor_degree = self.network.degree(neighbor)
            if neighbor_degree >= 3:  # 连接度高的节点
                if attack_type in [AttackType.LATERAL_MOVEMENT, AttackType.DATA_EXFILTRATION]:
                    score += 0.5

            # 6. 攻击者特定策略
            if attacker_params['target_selection'] == 'strategic':
                # 战略型攻击者偏好关键节点
                if neighbor in self.critical_nodes:
                    score += 1.0

            # 7. 随机性（根据攻击类型和攻击者适应性调整）
            adaptability = attacker_params['adaptability']
            if attack_type == AttackType.SCANNING:
                randomness = random.uniform(-0.3, 0.5) * (1 - adaptability * 0.5)
            elif attack_type == AttackType.DDOS:
                randomness = random.uniform(-0.1, 0.3)
            else:
                randomness = random.uniform(-0.2, 0.3) * (1 - adaptability * 0.3)

            score += randomness

            neighbor_scores.append((neighbor, score))

        if not neighbor_scores:
            return current_node

        # 使用softmax选择，考虑攻击者策略
        scores = np.array([score for _, score in neighbor_scores])

        # 温度参数调整（攻击者越聪明，选择越确定）
        temperature = 1.0 - attacker_params['skill_level'] * 0.5
        exp_scores = np.exp(scores / temperature - np.max(scores / temperature))
        probabilities = exp_scores / exp_scores.sum()

        # 根据攻击类型和攻击者模型选择策略
        if attacker_params['skill_level'] > 0.7:
            # 高技能攻击者更确定性选择
            if random.random() < 0.8:
                selected_idx = np.argmax(probabilities)
            else:
                selected_idx = np.random.choice(len(neighbor_scores), p=probabilities)
        else:
            # 低技能攻击者更随机
            selected_idx = np.random.choice(len(neighbor_scores), p=probabilities)

        return neighbor_scores[selected_idx][0]

    def _execute_intelligent_attack(self,
                                  source: str,
                                  target: str,
                                  attack_type: AttackType,
                                  base_success_rate: float,
                                  skill_level: float) -> bool:
        """
        智能化的攻击执行
        """
        # 获取边属性
        reliability = 0.8
        security_level = 1
        if self.network.has_edge(source, target):
            edge_data = self.network[source][target]
            reliability = edge_data.get('reliability', 0.8)
            security_level = edge_data.get('security_level', 1)

        # 攻击类型专业性加成
        type_multiplier = 1.0
        if attack_type == AttackType.SCANNING:
            type_multiplier = 1.15
        elif attack_type == AttackType.DDOS:
            type_multiplier = 1.10
        elif attack_type == AttackType.PRIVILEGE_ESCALATION:
            type_multiplier = 0.85
        elif attack_type == AttackType.ZERO_DAY:
            type_multiplier = 1.25  # 零日攻击成功率更高
        elif attack_type == AttackType.RANSOMWARE:
            type_multiplier = 0.90

        # 攻击者技能加成
        skill_multiplier = 0.8 + skill_level * 0.4  # 技能水平影响0.8-1.2倍

        # 计算成功率
        security_factor = max(0.5, 1.0 / max(security_level, 0.5))
        success_rate = (base_success_rate * reliability * security_factor *
                       type_multiplier * skill_multiplier)

        # 节点重要性影响（重要节点防御更强）
        target_importance = self.node_importance.get(target, 0.5)
        if target_importance > 0.7:
            success_rate *= (1 - target_importance * 0.3)

        # 加入合理随机性
        success_rate += random.uniform(-0.08, 0.08)
        success_rate = max(0.2, min(0.9, success_rate))

        return random.random() < success_rate

    def _update_attacker_behavior(self, attacker_params: Dict, step: int, captured: bool):
        """更新攻击者行为（学习）"""
        if captured and step > 5:
            # 被捕获后攻击者会学习
            attacker_params['stealth'] = min(1.0, attacker_params['stealth'] + 0.05)
            attacker_params['adaptability'] = min(1.0, attacker_params['adaptability'] + 0.03)

    def _is_collaborative_detection(self, node_id: str, attack_type: AttackType) -> bool:
        """判断是否是协同检测"""
        if not self.collaboration_system:
            return False

        # 检查是否有相关威胁情报
        relevant_threats = self.collaboration_system.get_relevant_threats(node_id)
        if len(relevant_threats) >= 2:
            # 检查是否是相同攻击类型
            same_type_count = sum(1 for t in relevant_threats if t['attack_type'] == attack_type)
            return same_type_count >= 1

        return False

    def _update_metrics(self, path: AttackPath, attack_type: AttackType,
                       captured: bool, successful_actions: int,
                       total_steps: int, evasive_actions: int):
        """更新统计指标"""
        self.metrics['total_attacks'] += 1

        if captured:
            self.metrics['captured_attacks'] += 1
            self.metrics['capture_latency'].append(path.capture_step)
            self.metrics['true_positives'] += 1

        self.metrics['total_steps'] += total_steps

        # 更新攻击类型分布
        self.metrics['attack_type_distribution'][attack_type.value] += 1

        # 计算触碰概率
        self.metrics['touch_probability'] = \
            self.metrics['captured_attacks'] / max(1, self.metrics['total_attacks'])

        # 计算攻击成功率
        if total_steps > 0:
            self.metrics['total_successful_actions'] += successful_actions
            self.metrics['total_action_steps'] += total_steps
            self.metrics['attack_success_rate'] = \
                self.metrics['total_successful_actions'] / max(1, self.metrics['total_action_steps'])

        # 更新规避率
        if evasive_actions > 0:
            self.metrics['evasion_rate'] = \
                sum(p.evasive_actions for p in self.attack_logs) / max(1, len(self.attack_logs))

    def run_batch_attacks(self,
                         num_attacks: int = 500) -> Dict[str, Any]:
        """
        运行批量攻击模拟
        """
        # 合理的攻击类型分布
        attack_type_dist = {
            AttackType.SCANNING: 0.30,
            AttackType.LATERAL_MOVEMENT: 0.25,
            AttackType.PRIVILEGE_ESCALATION: 0.15,
            AttackType.DATA_EXFILTRATION: 0.10,
            AttackType.DDOS: 0.08,
            AttackType.ZERO_DAY: 0.07,
            AttackType.RANSOMWARE: 0.05
        }

        # 攻击者类型分布
        attacker_type_dist = {
            'script_kiddie': 0.30,
            'hacker': 0.45,
            'apt_group': 0.15,
            'insider_threat': 0.10
        }

        # 重置统计
        self.attack_logs = []
        self.metrics = self._initialize_metrics()

        # 运行攻击模拟
        all_nodes = list(self.network.nodes())

        for i in range(num_attacks):
            # 选择攻击类型
            attack_type = self._select_by_distribution(attack_type_dist)

            # 选择攻击者类型
            attacker_type = self._select_by_distribution(attacker_type_dist)

            # 选择起始和目标节点
            start_node = random.choice(all_nodes)
            target_node = random.choice(all_nodes)

            # 确保起始和目标不同且距离合理
            attempts = 0
            while (target_node == start_node or
                   self._calculate_node_distance(start_node, target_node) < 2) and attempts < 5:
                target_node = random.choice(all_nodes)
                attempts += 1

            # 模拟攻击
            try:
                self.simulate_attack(start_node, target_node, attack_type, attacker_type)
            except Exception as e:
                print(f"  攻击模拟失败: {e}")
                continue

            # 每100次攻击显示进度
            if (i + 1) % 100 == 0:
                print(f"   进度: {i + 1}/{num_attacks} 攻击完成")

        # 计算最终指标
        return self.get_metrics()

    def _select_by_distribution(self, distribution: Dict) -> Any:
        """根据分布选择"""
        items = list(distribution.keys())
        probabilities = list(distribution.values())

        total = sum(probabilities)
        normalized_probs = [p / total for p in probabilities]

        return random.choices(items, weights=normalized_probs, k=1)[0]

    def _calculate_node_distance(self, node1: str, node2: str) -> int:
        """计算节点距离"""
        try:
            return nx.shortest_path_length(self.network, node1, node2)
        except:
            return float('inf')

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        # 计算平均捕获时延
        capture_latency = self.metrics['capture_latency']
        if capture_latency:
            capture_latency_mean = float(np.mean(capture_latency))
            capture_latency_std = float(np.std(capture_latency))
        else:
            capture_latency_mean = 0.0
            capture_latency_std = 0.0

        # 计算平均攻击步数
        total_attacks = self.metrics['total_attacks']
        if total_attacks > 0:
            average_steps_per_attack = self.metrics['total_steps'] / total_attacks
        else:
            average_steps_per_attack = 0.0

        # 计算误报率和漏报率
        total_detections = self.metrics['true_positives'] + self.metrics['false_positives']
        false_positive_rate = 0.0
        if total_detections > 0:
            false_positive_rate = self.metrics['false_positives'] / total_detections

        false_negative_rate = 0.0
        total_attacks_without_detection = self.metrics['total_attacks'] - self.metrics['captured_attacks']
        if total_attacks_without_detection > 0:
            false_negative_rate = self.metrics['false_negatives'] / total_attacks_without_detection

        # 计算早期检测率
        early_detection_rate = 0.0
        if self.metrics['captured_attacks'] > 0:
            early_detection_rate = self.metrics['early_detection_rate'] / self.metrics['captured_attacks']

        # 计算协同检测率
        collaborative_detection_rate = 0.0
        if self.metrics['captured_attacks'] > 0:
            collaborative_detection_rate = self.metrics['collaborative_detections'] / self.metrics['captured_attacks']

        # 计算平均检测置信度
        avg_confidence_scores = {}
        for node_id, perf in self.metrics['expert_performance'].items():
            if perf['confidence_scores']:
                avg_confidence_scores[node_id] = np.mean(perf['confidence_scores'])

        # 构建结果
        result = {
            'total_attacks': self.metrics['total_attacks'],
            'captured_attacks': self.metrics['captured_attacks'],
            'touch_probability': float(self.metrics['touch_probability']),
            'capture_latency_mean': capture_latency_mean,
            'capture_latency_std': capture_latency_std,
            'average_steps_per_attack': float(average_steps_per_attack),
            'attack_success_rate': float(self.metrics['attack_success_rate']),
            'false_positive_rate': float(false_positive_rate),
            'false_negative_rate': float(false_negative_rate),
            'early_detection_rate': float(early_detection_rate),
            'collaborative_detection_rate': float(collaborative_detection_rate),
            'evasion_rate': float(self.metrics['evasion_rate']),
            'precision': self.metrics['true_positives'] / max(1, self.metrics['true_positives'] + self.metrics['false_positives']),
            'recall': self.metrics['true_positives'] / max(1, self.metrics['true_positives'] + self.metrics['false_negatives']),
            'f1_score': 2 * (self.metrics['true_positives']) / max(1, 2 * self.metrics['true_positives'] + self.metrics['false_positives'] + self.metrics['false_negatives']),
            'attack_type_distribution': dict(self.metrics['attack_type_distribution']),
            'attacker_type_distribution': dict(self.metrics['attacker_type_distribution']),
            'expert_performance': {},
            'avg_confidence_scores': avg_confidence_scores
        }

        # 处理专家性能数据
        for node_id, perf in self.metrics['expert_performance'].items():
            result['expert_performance'][node_id] = {
                'detection_counts': perf['detection_counts'],
                'true_positives': perf['true_positives'],
                'false_positives': perf['false_positives'],
                'false_negatives': perf['false_negatives'],
                'expert_type': perf['expert_type'],
                'attack_type_detections': dict(perf['attack_type_detections']),
                'avg_confidence': np.mean(perf['confidence_scores']) if perf['confidence_scores'] else 0.0,
                'context_aware_detections': perf['context_aware_detections'],
                'context_aware_rate': perf['context_aware_detections'] / max(1, perf['detection_counts'])
            }

        return result


def create_advanced_steiner_honeypots(network: nx.Graph, num_honeypots: int = 15) -> Dict[str, ExpertType]:
    """高级斯坦纳树蜜罐部署策略"""
    honeypot_deployment = {}

    # 1. 网络社区检测
    try:
        communities = list(nx.community.greedy_modularity_communities(network))
    except:
        # 如果社区检测失败，使用简化方法
        communities = [set(network.nodes())]

    print(f"   检测到 {len(communities)} 个网络社区")

    # 2. 计算节点重要性
    degree_centrality = nx.degree_centrality(network)
    betweenness_centrality = nx.betweenness_centrality(network, k=min(20, network.number_of_nodes()))

    node_scores = {}
    for node in network.nodes():
        score = (degree_centrality[node] * 0.4 +
                betweenness_centrality[node] * 0.6)
        node_scores[node] = score

    # 3. 在每个社区内部署专家
    expert_assignments = []

    for i, community in enumerate(communities):
        community_nodes = list(community)
        if len(community_nodes) < 3:
            continue

        # 选择社区内重要节点
        community_scores = {node: node_scores[node] for node in community_nodes}
        top_community_nodes = sorted(community_scores.items(), key=lambda x: x[1], reverse=True)

        # 部署社区边界专家
        boundary_nodes = []
        for node in community_nodes:
            neighbors = list(network.neighbors(node))
            # 检查是否有邻居在其他社区
            external_neighbors = [n for n in neighbors if n not in community]
            if len(external_neighbors) > 0:
                boundary_nodes.append(node)

        # 根据社区类型分配专家
        if i == 0:  # 第一个社区（通常是核心区）
            # 核心区部署权限专家和混合专家
            for node, _ in top_community_nodes[:2]:
                if len(expert_assignments) < num_honeypots:
                    expert_assignments.append((node, ExpertType.PRIVILEGE_EXPERT))

            # 在边界部署横向专家
            for node in boundary_nodes[:1]:
                if len(expert_assignments) < num_honeypots:
                    expert_assignments.append((node, ExpertType.LATERAL_EXPERT))

        elif i == 1:  # 第二个社区（通常是DMZ区）
            # DMZ区部署扫描专家和DDoS专家
            for node, _ in top_community_nodes[:2]:
                if len(expert_assignments) < num_honeypots:
                    if network.degree(node) > 3:
                        expert_assignments.append((node, ExpertType.SCANNING_EXPERT))
                    else:
                        expert_assignments.append((node, ExpertType.DDOS_EXPERT))

        else:  # 其他社区（用户区）
            # 用户区部署数据专家和勒索软件专家
            for node, _ in top_community_nodes[:1]:
                if len(expert_assignments) < num_honeypots:
                    expert_assignments.append((node, ExpertType.DATA_EXFIL_EXPERT))

            # 部署异常检测专家在重要边界
            for node in boundary_nodes[:1]:
                if len(expert_assignments) < num_honeypots:
                    expert_assignments.append((node, ExpertType.ANOMALY_EXPERT))

    # 4. 部署全局关键节点的专家
    global_top_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)

    # 添加零日攻击专家在高价值节点
    for node, _ in global_top_nodes:
        if node not in [n for n, _ in expert_assignments] and len(expert_assignments) < num_honeypots:
            # 选择连接度高且中心性高的节点
            if network.degree(node) >= 4 and betweenness_centrality[node] > 0.1:
                expert_assignments.append((node, ExpertType.ZERO_DAY_EXPERT))
                break

    # 添加勒索软件专家
    for node, _ in global_top_nodes:
        if node not in [n for n, _ in expert_assignments] and len(expert_assignments) < num_honeypots:
            # 选择可能存储重要数据的节点（度数适中但重要性高）
            if 3 <= network.degree(node) <= 6 and node_scores[node] > 0.3:
                expert_assignments.append((node, ExpertType.RANSOMWARE_EXPERT))
                break

    # 5. 填充剩余位置为混合专家
    remaining_nodes = []
    for node, score in global_top_nodes:
        if node not in [n for n, _ in expert_assignments]:
            remaining_nodes.append((node, score))

    for node, _ in remaining_nodes:
        if len(expert_assignments) < num_honeypots:
            expert_assignments.append((node, ExpertType.HYBRID_EXPERT))
        else:
            break

    # 6. 转换为字典
    honeypot_deployment = dict(expert_assignments)

    print(f"   蜜罐部署完成: {len(honeypot_deployment)} 个蜜罐")

    # 统计专家类型分布
    expert_count = defaultdict(int)
    for _, expert in honeypot_deployment.items():
        expert_count[expert.value] += 1

    print("   专家分布:")
    for expert_type, count in sorted(expert_count.items()):
        print(f"     - {expert_type}: {count}个")

    return honeypot_deployment


def create_advanced_random_honeypots(network: nx.Graph, num_honeypots: int = 15) -> Dict[str, ExpertType]:
    """高级随机蜜罐部署（基线方法）"""
    all_nodes = list(network.nodes())

    # 带权重的随机选择（重要节点更可能被选中）
    degree_centrality = nx.degree_centrality(network)
    weights = [1 + degree_centrality[node] * 2 for node in all_nodes]

    selected_nodes = random.choices(all_nodes, weights=weights, k=num_honeypots)

    honeypot_deployment = {}

    # 专家类型分布（基线方法更依赖通用专家）
    expert_types = list(ExpertType)
    # 降低专业专家权重，提高通用专家权重
    type_weights = [
        0.08,  # SCANNING_EXPERT
        0.08,  # LATERAL_EXPERT
        0.08,  # PRIVILEGE_EXPERT
        0.08,  # DATA_EXFIL_EXPERT
        0.08,  # DDOS_EXPERT
        0.05,  # ZERO_DAY_EXPERT
        0.05,  # RANSOMWARE_EXPERT
        0.10,  # HYBRID_EXPERT
        0.10,  # ANOMALY_EXPERT
        0.30   # GENERAL_EXPERT (最高权重)
    ]

    for node in selected_nodes:
        expert_type = random.choices(expert_types, weights=type_weights, k=1)[0]
        honeypot_deployment[node] = expert_type

    return honeypot_deployment


def run_advanced_simulation():
    """
    运行高级攻击模拟实验
    """
    print("=" * 60)
    print("高级版MoE SHD动态攻击模拟实验")
    print("=" * 60)

    # 1. 创建复杂网络拓扑
    print("\n1. 创建网络拓扑...")

    # 创建层次化网络（核心-汇聚-接入）
    network = nx.Graph()

    # 添加节点（50个节点）
    for i in range(50):
        network.add_node(i,
                        type='core' if i < 5 else
                             'aggregation' if i < 15 else
                             'access',
                        security_level=random.randint(1, 5))

    # 添加边（创建层次结构）
    # 核心层全连接
    for i in range(5):
        for j in range(i + 1, 5):
            network.add_edge(i, j,
                           reliability=random.uniform(0.95, 0.99),
                           security_level=5,
                           bandwidth=1000)

    # 汇聚层连接到核心层
    for i in range(5, 15):
        # 每个汇聚节点连接到2个核心节点
        core_connections = random.sample(range(5), 2)
        for core in core_connections:
            network.add_edge(i, core,
                           reliability=random.uniform(0.90, 0.95),
                           security_level=4,
                           bandwidth=500)

        # 汇聚节点间部分连接
        if i < 14 and random.random() < 0.5:
            network.add_edge(i, i + 1,
                           reliability=random.uniform(0.85, 0.90),
                           security_level=3,
                           bandwidth=100)

    # 接入层连接到汇聚层
    for i in range(15, 50):
        # 每个接入节点连接到1-2个汇聚节点
        agg_connections = random.sample(range(5, 15), random.randint(1, 2))
        for agg in agg_connections:
            network.add_edge(i, agg,
                           reliability=random.uniform(0.80, 0.90),
                           security_level=2,
                           bandwidth=100)

        # 接入节点间少量连接（模拟部门内连接）
        if random.random() < 0.3:
            potential_peers = range(15, 50)
            peer = random.choice(potential_peers)
            if peer != i and not network.has_edge(i, peer):
                network.add_edge(i, peer,
                               reliability=random.uniform(0.75, 0.85),
                               security_level=1,
                               bandwidth=10)

    print(f"   网络类型: 层次化网络（核心-汇聚-接入）")
    print(f"   节点数: {network.number_of_nodes()}")
    print(f"   边数: {network.number_of_edges()}")
    print(f"   核心节点: 5个")
    print(f"   汇聚节点: 10个")
    print(f"   接入节点: 35个")

    # 2. 创建蜜罐部署
    print("\n2. 创建蜜罐部署...")
    steiner_deployment = create_advanced_steiner_honeypots(network, 15)
    random_deployment = create_advanced_random_honeypots(network, 15)

    # 3. 运行MoE SHD部署模拟
    print("\n3. 运行MoE SHD部署模拟...")
    moe_simulator = AdvancedDynamicAttackSimulator(
        network_graph=network,
        honeypot_nodes=steiner_deployment,
        random_seed=42
    )

    moe_results = moe_simulator.run_batch_attacks(num_attacks=1000)

    print("\n MoE SHD部署结果:")
    print(f"   - 总攻击次数: {moe_results['total_attacks']}")
    print(f"   - 捕获攻击次数: {moe_results['captured_attacks']}")
    print(f"   - 触碰概率: {moe_results['touch_probability']:.3f}")
    print(f"   - 平均捕获步数: {moe_results['capture_latency_mean']:.1f}")
    print(f"   - 平均攻击步数: {moe_results['average_steps_per_attack']:.1f}")
    print(f"   - 攻击成功率: {moe_results['attack_success_rate']:.3f}")
    print(f"   - 误报率: {moe_results['false_positive_rate']:.4f}")
    print(f"   - 漏报率: {moe_results['false_negative_rate']:.3f}")
    print(f"   - 早期检测率: {moe_results['early_detection_rate']:.3f}")
    print(f"   - 协同检测率: {moe_results['collaborative_detection_rate']:.3f}")
    print(f"   - 攻击规避率: {moe_results['evasion_rate']:.3f}")
    print(f"   - 精确率: {moe_results['precision']:.3f}")
    print(f"   - 召回率: {moe_results['recall']:.3f}")
    print(f"   - F1分数: {moe_results['f1_score']:.3f}")

    # 4. 运行基线对比
    print("\n4. 运行基线部署模拟...")
    baseline_simulator = AdvancedDynamicAttackSimulator(
        network_graph=network,
        honeypot_nodes=random_deployment,
        random_seed=42
    )

    baseline_results = baseline_simulator.run_batch_attacks(num_attacks=500)

    print("\n 基线部署结果:")
    print(f"   - 触碰概率: {baseline_results['touch_probability']:.3f}")
    print(f"   - 误报率: {baseline_results['false_positive_rate']:.4f}")
    print(f"   - 漏报率: {baseline_results['false_negative_rate']:.3f}")
    print(f"   - 精确率: {baseline_results['precision']:.3f}")
    print(f"   - 召回率: {baseline_results['recall']:.3f}")
    print(f"   - F1分数: {baseline_results['f1_score']:.3f}")

    # 5. 对比分析
    print("\n5. 对比分析:")
    improvement = {
        'touch_probability': moe_results['touch_probability'] - baseline_results['touch_probability'],
        'false_positive_rate': baseline_results['false_positive_rate'] - moe_results['false_positive_rate'],
        'false_negative_rate': baseline_results['false_negative_rate'] - moe_results['false_negative_rate'],
        'precision': moe_results['precision'] - baseline_results['precision'],
        'recall': moe_results['recall'] - baseline_results['recall'],
        'f1_score': moe_results['f1_score'] - baseline_results['f1_score'],
        'attack_success_rate': baseline_results['attack_success_rate'] - moe_results['attack_success_rate']
    }

    print(f"   - 触碰概率提升: {improvement['touch_probability']:+.3f}")
    print(f"   - 误报率降低: {improvement['false_positive_rate']:+.4f}")
    print(f"   - 漏报率降低: {improvement['false_negative_rate']:+.3f}")
    print(f"   - 精确率提升: {improvement['precision']:+.3f}")
    print(f"   - 召回率提升: {improvement['recall']:+.3f}")
    print(f"   - F1分数提升: {improvement['f1_score']:+.3f}")
    print(f"   - 攻击成功率降低: {improvement['attack_success_rate']:+.3f} (防御效果)")

    # 6. 攻击类型分析
    print("\n6. 攻击类型分析:")
    total_attacks = moe_results['total_attacks']
    for attack_type, count in sorted(moe_results['attack_type_distribution'].items()):
        percentage = count / total_attacks * 100 if total_attacks > 0 else 0
        print(f"   - {attack_type}: {count}次 ({percentage:.1f}%)")

    # 7. 攻击者类型分析
    print("\n7. 攻击者类型分析:")
    for attacker_type, count in sorted(moe_results['attacker_type_distribution'].items()):
        percentage = count / total_attacks * 100 if total_attacks > 0 else 0
        print(f"   - {attacker_type}: {count}次 ({percentage:.1f}%)")

    # 8. 专家性能详细分析
    print("\n8. 专家性能详细分析:")
    total_detections = moe_results['captured_attacks']

    # 按检测次数排序
    expert_perf_items = sorted(
        moe_results['expert_performance'].items(),
        key=lambda x: x[1]['detection_counts'],
        reverse=True
    )

    print("   Top 5 专家:")
    for i, (node_id, perf) in enumerate(expert_perf_items[:5]):
        if perf['detection_counts'] > 0:
            detection_rate = perf['detection_counts'] / total_detections if total_detections > 0 else 0

            print(f"   {i + 1}. 节点{node_id} ({perf['expert_type']}):")
            print(f"       检测次数: {perf['detection_counts']}, 占比: {detection_rate:.2f}")
            print(f"       精确率: {perf['true_positives'] / max(1, perf['true_positives'] + perf['false_positives']):.2f}")
            print(f"       TP/FP/FN: {perf['true_positives']}/{perf['false_positives']}/{perf['false_negatives']}")
            print(f"       平均置信度: {perf['avg_confidence']:.2f}")
            print(f"       上下文感知率: {perf['context_aware_rate']:.2f}")

            if perf['attack_type_detections']:
                print(f"       攻击类型检测分布: {dict(perf['attack_type_detections'])}")

    return {
        'network': network,
        'steiner_deployment': steiner_deployment,
        'random_deployment': random_deployment,
        'moe_results': moe_results,
        'baseline_results': baseline_results,
        'improvement': improvement
    }


def validate_advanced_system(results: Dict[str, Any]):
    """
    验证高级MoE SHD系统的有效性
    """
    print("\n" + "=" * 60)
    print("高级MoE SHD系统有效性验证")
    print("=" * 60)

    moe_results = results['moe_results']
    improvement = results['improvement']

    validation_results = {
        'touch_probability': False,
        'false_positive_rate': False,
        'false_negative_rate': False,
        'early_detection': False,
        'collaborative_detection': False,
        'expert_specialization': False,
        'overall_effectiveness': False
    }

    # 1. 触碰概率验证
    print("\n1. 蜜罐诱捕有效性验证:")
    if moe_results['touch_probability'] > 0.35:
        print(f"    通过 - MoE SHD触碰概率良好 ({moe_results['touch_probability']:.3f})")
        validation_results['touch_probability'] = True
    elif moe_results['touch_probability'] > 0.25:
        print(f"     警告 - 触碰概率一般 ({moe_results['touch_probability']:.3f})")
    else:
        print(f"    失败 - 触碰概率偏低 ({moe_results['touch_probability']:.3f})")

    if improvement['touch_probability'] > 0.15:
        print(f"    通过 - 比基线显著提升 (+{improvement['touch_probability']:.3f})")
        validation_results['touch_probability'] = True
    else:
        print(f"     警告 - 提升不明显 (+{improvement['touch_probability']:.3f})")

    # 2. 误报率验证
    print("\n2. 误报率优化验证:")
    if moe_results['false_positive_rate'] < 0.02:
        print(f"    优秀 - 极低误报率 ({moe_results['false_positive_rate']:.4f})")
        validation_results['false_positive_rate'] = True
    elif moe_results['false_positive_rate'] < 0.05:
        print(f"    通过 - 低误报率 ({moe_results['false_positive_rate']:.4f})")
        validation_results['false_positive_rate'] = True
    else:
        print(f"     警告 - 误报率偏高 ({moe_results['false_positive_rate']:.4f})")

    # 3. 漏报率验证
    print("\n3. 漏报率优化验证:")
    if moe_results['false_negative_rate'] < 0.15:
        print(f"    优秀 - 低漏报率 ({moe_results['false_negative_rate']:.3f})")
        validation_results['false_negative_rate'] = True
    elif moe_results['false_negative_rate'] < 0.25:
        print(f"    通过 - 合理漏报率 ({moe_results['false_negative_rate']:.3f})")
        validation_results['false_negative_rate'] = True
    else:
        print(f"    失败 - 漏报率偏高 ({moe_results['false_negative_rate']:.3f})")

    if improvement['false_negative_rate'] > 0:
        print(f"    通过 - 漏报率比基线降低 (+{improvement['false_negative_rate']:.3f})")
        validation_results['false_negative_rate'] = True

    # 4. 早期检测验证
    print("\n4. 早期检测能力验证:")
    if moe_results['early_detection_rate'] > 0.3:
        print(f"    优秀 - 早期检测能力强 ({moe_results['early_detection_rate']:.3f})")
        validation_results['early_detection'] = True
    elif moe_results['early_detection_rate'] > 0.15:
        print(f"    通过 - 具备早期检测能力 ({moe_results['early_detection_rate']:.3f})")
        validation_results['early_detection'] = True
    else:
        print(f"     警告 - 早期检测能力弱 ({moe_results['early_detection_rate']:.3f})")

    # 5. 协同检测验证
    print("\n5. 协同检测能力验证:")
    if moe_results['collaborative_detection_rate'] > 0.2:
        print(f"    优秀 - 协同检测效果好 ({moe_results['collaborative_detection_rate']:.3f})")
        validation_results['collaborative_detection'] = True
    elif moe_results['collaborative_detection_rate'] > 0.1:
        print(f"    通过 - 具备协同检测能力 ({moe_results['collaborative_detection_rate']:.3f})")
        validation_results['collaborative_detection'] = True
    else:
        print(f"     警告 - 协同检测能力弱 ({moe_results['collaborative_detection_rate']:.3f})")

    # 6. 专家专业化验证
    print("\n6. MoE专家专业化验证:")
    expert_specialization_score = 0
    total_experts = 0

    for node_id, perf in moe_results['expert_performance'].items():
        if perf['detection_counts'] > 0:
            total_experts += 1
            expert_type = perf['expert_type']
            attack_detections = perf['attack_type_detections']

            # 检查专家是否检测到其擅长领域的攻击
            if expert_type == 'scanning_expert' and 'scanning' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'lateral_expert' and 'lateral' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'privilege_expert' and 'priv' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'data_exfil_expert' and 'exfil' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'ddos_expert' and 'ddos' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'zero_day_expert' and 'zero_day' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'ransomware_expert' and 'ransomware' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'anomaly_expert' and ('zero_day' in attack_detections or 'ransomware' in attack_detections):
                expert_specialization_score += 1
            elif expert_type in ['hybrid_expert', 'general_expert'] and len(attack_detections) > 0:
                expert_specialization_score += 0.5  # 部分分数

    specialization_rate = expert_specialization_score / max(1, total_experts)

    if specialization_rate > 0.7:
        print(f"    优秀 - 专家专业化程度高 ({specialization_rate:.2f})")
        validation_results['expert_specialization'] = True
    elif specialization_rate > 0.5:
        print(f"    通过 - 专家专业化程度合理 ({specialization_rate:.2f})")
        validation_results['expert_specialization'] = True
    else:
        print(f"    失败 - 专家专业化程度低 ({specialization_rate:.2f})")

    # 7. 总体有效性评估
    print("\n7. 总体有效性评估:")
    passed_tests = sum(validation_results.values())
    total_tests = len(validation_results)

    if passed_tests >= total_tests - 1:  # 最多允许1项失败
        print(f"    MoE SHD系统总体优秀 ({passed_tests}/{total_tests} 项通过)")
        validation_results['overall_effectiveness'] = True
    elif passed_tests >= total_tests * 0.7:
        print(f"    MoE SHD系统总体有效 ({passed_tests}/{total_tests} 项通过)")
        validation_results['overall_effectiveness'] = True
    else:
        print(f"    MoE SHD系统效果不佳 ({passed_tests}/{total_tests} 项通过)")

    return validation_results


def generate_comprehensive_report(results: Dict[str, Any], validation: Dict[str, bool]):
    """生成综合报告"""
    print("\n" + "=" * 60)
    print("高级MoE SHD系统综合性能报告")
    print("=" * 60)

    moe_results = results['moe_results']
    baseline_results = results['baseline_results']
    improvement = results['improvement']

    # 性能指标汇总
    print("\n 性能指标汇总:")
    print("   Metric                    | MoE SHD     | Baseline    | Improvement")
    print("   --------------------------|-------------|-------------|-------------")

    metrics = [
        ("触碰概率", moe_results['touch_probability'], baseline_results['touch_probability'], improvement['touch_probability']),
        ("误报率", moe_results['false_positive_rate'], baseline_results['false_positive_rate'], improvement['false_positive_rate']),
        ("漏报率", moe_results['false_negative_rate'], baseline_results['false_negative_rate'], improvement['false_negative_rate']),
        ("精确率", moe_results['precision'], baseline_results['precision'], improvement['precision']),
        ("召回率", moe_results['recall'], baseline_results['recall'], improvement['recall']),
        ("F1分数", moe_results['f1_score'], baseline_results['f1_score'], improvement['f1_score']),
        ("攻击成功率", moe_results['attack_success_rate'], baseline_results['attack_success_rate'], improvement['attack_success_rate'])
    ]

    for name, moe_val, base_val, imp_val in metrics:
        if name == "攻击成功率":
            # 攻击成功率降低表示防御有效
            imp_display = f"{imp_val:+.3f} (防御效果)"
        else:
            imp_display = f"{imp_val:+.3f}"

        print(f"   {name:<25} | {moe_val:^11.3f} | {base_val:^11.3f} | {imp_display}")

    # 高级能力评估
    print("\n 高级能力评估:")
    advanced_metrics = [
        ("早期检测率", moe_results['early_detection_rate'], ">0.2"),
        ("协同检测率", moe_results['collaborative_detection_rate'], ">0.15"),
        ("攻击规避率", moe_results['evasion_rate'], "<0.3"),
        ("平均检测置信度", np.mean(list(moe_results['avg_confidence_scores'].values())) if moe_results['avg_confidence_scores'] else 0, ">0.7")
    ]

    for name, value, threshold in advanced_metrics:
        if isinstance(threshold, str):
            if threshold.startswith(">"):
                target = float(threshold[1:])
                status = "" if value > target else ""
            elif threshold.startswith("<"):
                target = float(threshold[1:])
                status = "" if value < target else ""
            else:
                target = float(threshold)
                status = "" if value >= target else ""
        else:
            status = "" if value >= threshold else ""

        print(f"   {status} {name}: {value:.3f} (目标: {threshold})")

    # 验证结果总结
    print("\n 验证结果总结:")
    passed = sum(validation.values())
    total = len(validation)

    print(f"   通过测试: {passed}/{total} ({passed / total * 100:.1f}%)")

    if validation['overall_effectiveness']:
        print("    总体评估: MoE SHD系统部署成功，显著优于基线方法")
    else:
        print("     总体评估: MoE SHD系统需要进一步优化")

    # 建议和改进方向
    print("\n 建议和改进方向:")

    if moe_results['false_negative_rate'] > 0.2:
        print("   - 考虑增加异常检测专家或混合专家的比例")

    if moe_results['early_detection_rate'] < 0.2:
        print("   - 在网络入口处部署更多扫描专家和异常检测专家")

    if moe_results['collaborative_detection_rate'] < 0.15:
        print("   - 加强蜜罐间的信息共享和协同检测机制")

    if improvement['touch_probability'] < 0.15:
        print("   - 优化蜜罐部署策略，考虑更精细的社区检测")

    print("   - 定期更新专家检测模型，适应新型攻击模式")
    print("   - 实施动态蜜罐迁移策略，应对攻击者的规避行为")


def save_results(results: Dict[str, Any], validation: Dict[str, bool]):
    """保存结果到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"advanced_moe_simulation_results_{timestamp}.json"

    # 准备保存的数据
    save_data = {
        'timestamp': timestamp,
        'moe_results': results['moe_results'],
        'baseline_results': results['baseline_results'],
        'improvement': results['improvement'],
        'validation': validation,
        'network_info': {
            'num_nodes': results['network'].number_of_nodes(),
            'num_edges': results['network'].number_of_edges(),
            'num_honeypots_moe': len(results['steiner_deployment']),
            'num_honeypots_baseline': len(results['random_deployment'])
        }
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"\n 结果已保存至: {filename}")

    return filename


if __name__ == "__main__":
    # 运行高级模拟
    print("开始高级版MoE SHD攻击模拟实验...\n")

    try:
        results = run_advanced_simulation()

        # 验证系统有效性
        validation = validate_advanced_system(results)

        # 生成综合报告
        generate_comprehensive_report(results, validation)

        # 保存结果
        filename = save_results(results, validation)

        print("\n" + "=" * 60)
        print(" 实验完成总结")
        print("=" * 60)

        print(f"\n 高级MoE SHD系统模拟实验成功完成")
        print(f" 主要成果:")
        print(f"   - MoE SHD触碰概率: {results['moe_results']['touch_probability']:.3f}")
        print(f"   - 比基线提升: {results['improvement']['touch_probability']:+.3f}")
        print(f"   - 误报率: {results['moe_results']['false_positive_rate']:.4f}")
        print(f"   - 漏报率: {results['moe_results']['false_negative_rate']:.3f}")
        print(f"   - F1分数: {results['moe_results']['f1_score']:.3f}")
        print(f"\n 系统优势:")
        print(f"   - 协同检测能力: {results['moe_results']['collaborative_detection_rate']:.3f}")
        print(f"   - 早期检测能力: {results['moe_results']['early_detection_rate']:.3f}")
        print(f"   - 上下文感知检测: 已实现")
        print(f"   - 自适应学习: 已实现")

        print(f"\n 详细结果已保存至: {filename}")

    except Exception as e:
        print(f"\n 实验执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()'''
import random
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set, Deque
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
from collections import defaultdict, deque
import warnings
import math
from heapq import heappush, heappop

# 安全导入虚假专家响应器
try:
    from .fake_expert_responder import FakeExpertResponder
except (ImportError, ModuleNotFoundError):
    # 如果相对导入失败，尝试绝对导入
    try:
        from fake_expert_responder import FakeExpertResponder
    except ImportError:
        # 若还是失败，提供模拟实现
        class FakeExpertResponder:
            def __init__(self, *args, **kwargs):
                self.tree = {}
                self.profiles = {}
            def respond(self, attack_context):
                return {'latency': 0.05, 'response': 'mock', 'gradient_mask': np.array([])}

warnings.filterwarnings('ignore')


class AttackType(Enum):
    """攻击类型枚举"""
    SCANNING = "scanning"
    LATERAL_MOVEMENT = "lateral"
    PRIVILEGE_ESCALATION = "priv"
    DATA_EXFILTRATION = "exfil"
    DDOS = "ddos"
    ZERO_DAY = "zero_day"
    RANSOMWARE = "ransomware"


class ExpertType(Enum):
    """MoE专家类型枚举"""
    SCANNING_EXPERT = "scanning_expert"
    LATERAL_EXPERT = "lateral_expert"
    PRIVILEGE_EXPERT = "privilege_expert"
    DATA_EXFIL_EXPERT = "data_exfil_expert"
    DDOS_EXPERT = "ddos_expert"
    ZERO_DAY_EXPERT = "zero_day_expert"
    RANSOMWARE_EXPERT = "ransomware_expert"
    HYBRID_EXPERT = "hybrid_expert"
    ANOMALY_EXPERT = "anomaly_expert"
    GENERAL_EXPERT = "general_expert"


@dataclass
class AttackContext:
    """攻击上下文信息"""
    attacker_id: str
    attack_path: List[str]
    attack_pattern: str
    attack_intensity: float
    time_of_day: float  # 0-24小时
    previous_actions: List[str]
    resources_accessed: Set[str]


@dataclass
class AttackAction:
    """攻击动作"""
    attack_id: str
    attack_type: AttackType
    source_node: str
    target_node: str
    timestamp: float
    success: bool
    context: Optional[AttackContext] = None
    detected_by: Optional[str] = None
    detection_latency: float = 0.0
    false_positive: bool = False
    false_negative: bool = False
    confidence_score: float = 0.0
    routed_expert: Optional[str] = None
    # 虚假响应字段
    fake_response_latency: float = 0.0
    fake_response_type: str = ""
    gradient_mask_applied: List[float] = field(default_factory=list)


@dataclass
class AttackPath:
    """攻击路径"""
    path_id: str
    attacker_id: str
    start_node: str
    target_node: str
    actions: List[AttackAction]
    total_steps: int
    captured: bool = False
    capture_step: int = -1
    expert_type_detected: Optional[str] = None
    detection_confidence: float = 0.0
    evasive_actions: int = 0


# ==================== MoE门控路由器 ====================
class MoERouter:
    """MoE门控路由器，根据攻击特征计算每个专家的路由概率"""
    def __init__(self, expert_types: List[ExpertType], feature_dim: int = 8):
        self.expert_types = expert_types
        self.num_experts = len(expert_types)
        self.feature_dim = feature_dim
        self.gate_weights = self._init_heuristic_weights()
        self.routing_history = deque(maxlen=200)

    def _init_heuristic_weights(self) -> Dict[ExpertType, np.ndarray]:
        weights = {}
        for expert in self.expert_types:
            w = np.zeros(self.feature_dim)
            if expert == ExpertType.SCANNING_EXPERT:
                w[0] = 0.8; w[2] = 0.2; w[5] = -0.1
            elif expert == ExpertType.LATERAL_EXPERT:
                w[0] = 0.7; w[2] = 0.3; w[3] = 0.2
            elif expert == ExpertType.PRIVILEGE_EXPERT:
                w[0] = 0.6; w[2] = 0.4; w[3] = 0.3
            elif expert == ExpertType.DATA_EXFIL_EXPERT:
                w[0] = 0.5; w[2] = 0.5; w[4] = 0.2
            elif expert == ExpertType.DDOS_EXPERT:
                w[0] = 0.4; w[2] = 0.6; w[1] = 0.3
            elif expert == ExpertType.ZERO_DAY_EXPERT:
                w[0] = 0.3; w[2] = 0.7; w[7] = 0.4
            elif expert == ExpertType.RANSOMWARE_EXPERT:
                w[0] = 0.2; w[2] = 0.8; w[3] = 0.2
            elif expert == ExpertType.HYBRID_EXPERT:
                w = np.ones(self.feature_dim) * 0.2
            elif expert == ExpertType.ANOMALY_EXPERT:
                w[1] = 0.3; w[2] = 0.5; w[7] = 0.3
            else:  # GENERAL_EXPERT
                w = np.ones(self.feature_dim) * 0.1
            weights[expert] = w
        return weights

    def extract_features(self, attack_type: AttackType, attack_intensity: float,
                         attack_pattern: str, node_importance: float,
                         is_honeypot: bool, visited_nodes_ratio: float,
                         time_of_day: float, attacker_skill: float) -> np.ndarray:
        attack_type_map = {
            AttackType.SCANNING: 0.8, AttackType.LATERAL_MOVEMENT: 0.7,
            AttackType.PRIVILEGE_ESCALATION: 0.6, AttackType.DATA_EXFILTRATION: 0.5,
            AttackType.DDOS: 0.4, AttackType.ZERO_DAY: 0.3, AttackType.RANSOMWARE: 0.2
        }
        attack_type_val = attack_type_map.get(attack_type, 0.5)
        pattern_map = {'random': 0.2, 'targeted': 0.5, 'stealthy': 0.7, 'aggressive': 0.9, 'evasive': 0.6}
        pattern_val = pattern_map.get(attack_pattern, 0.5)
        time_factor = 1.0 if 2 <= time_of_day <= 6 else 0.2
        features = np.array([
            attack_type_val, attack_intensity, pattern_val,
            node_importance, 1.0 if is_honeypot else 0.0,
            visited_nodes_ratio, time_factor, attacker_skill
        ])
        return features

    def route(self, attack_type: AttackType, attack_intensity: float,
              attack_pattern: str, node_importance: float,
              is_honeypot: bool, visited_nodes_ratio: float,
              time_of_day: float, attacker_skill: float) -> ExpertType:
        features = self.extract_features(
            attack_type, attack_intensity, attack_pattern,
            node_importance, is_honeypot, visited_nodes_ratio,
            time_of_day, attacker_skill
        )
        scores = [np.dot(self.gate_weights[expert], features) for expert in self.expert_types]
        exp_scores = np.exp(scores - np.max(scores))
        probs = exp_scores / exp_scores.sum()
        selected_idx = np.random.choice(len(self.expert_types), p=probs)
        selected_expert = self.expert_types[selected_idx]
        self.routing_history.append({
            'selected_expert': selected_expert,
            'probabilities': dict(zip(self.expert_types, probs)),
            'attack_type': attack_type,
            'timestamp': datetime.now().timestamp()
        })
        return selected_expert

    def update_weights(self, feedback: Dict[str, float]):
        pass


# ==================== 协同检测系统 ====================
class CollaborativeDetectionSystem:
    """协同检测系统"""
    def __init__(self):
        self.shared_knowledge = defaultdict(dict)
        self.attack_patterns = defaultdict(list)
        self.suspicious_nodes = set()
        self.threat_intelligence = {
            'recent_attacks': deque(maxlen=100),
            'attack_correlations': defaultdict(float),
            'node_risk_scores': defaultdict(float)
        }
        self.network = None

    def share_information(self, node_id: str, attack_type: AttackType,
                         timestamp: float, confidence: float):
        key = f"{node_id}_{attack_type.value}_{timestamp}"
        self.shared_knowledge[key] = {
            'node_id': node_id,
            'attack_type': attack_type,
            'timestamp': timestamp,
            'confidence': confidence
        }

    def get_relevant_threats(self, node_id: str, time_window: float = 300) -> List[Dict]:
        current_time = datetime.now().timestamp()
        relevant_threats = []
        for key, threat in self.shared_knowledge.items():
            if current_time - threat['timestamp'] <= time_window:
                distance = self.calculate_network_distance(node_id, threat['node_id'])
                if distance <= 3:
                    threat['distance'] = distance
                    relevant_threats.append(threat)
        return relevant_threats

    def calculate_network_distance(self, node1: str, node2: str) -> int:
        if self.network is None:
            return float('inf')
        try:
            return len(nx.shortest_path(self.network, node1, node2)) - 1
        except:
            return float('inf')

    def update_attack_patterns(self, attack_path: AttackPath):
        attack_types = [action.attack_type for action in attack_path.actions]
        pattern_key = "_".join([at.value for at in attack_types[:3]])
        self.attack_patterns[pattern_key].append(attack_path.attacker_id)

    def detect_pattern_anomaly(self, current_actions: List[AttackType]) -> float:
        pattern_key = "_".join([at.value for at in current_actions[:3]])
        if pattern_key in self.attack_patterns:
            frequency = len(self.attack_patterns[pattern_key])
            return 1.0 - math.exp(-frequency / 10.0)
        else:
            return 0.7


# ==================== 自适应MoE专家蜜罐 ====================
class AdaptiveMoEExpertHoneypot:
    """自适应MoE专家蜜罐"""
    def __init__(self, node_id: str, expert_type: ExpertType,
                 detection_threshold: float = 0.6, learning_rate: float = 0.05):
        self.node_id = node_id
        self.expert_type = expert_type
        self.base_threshold = detection_threshold
        self.detection_threshold = detection_threshold
        self.learning_rate = learning_rate
        self.detection_counts = 0
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.detection_history = deque(maxlen=100)
        self.attack_type_stats = defaultdict(lambda: {'detected': 0, 'total': 0})
        self.context_weights = {
            'time_of_day': 0.1, 'attack_pattern': 0.3, 'intensity': 0.2,
            'path_length': 0.1, 'node_importance': 0.2, 'threat_intelligence': 0.1
        }
        self.expert_capabilities = self._init_enhanced_capabilities()
        self.collaboration_system = None

    def set_collaboration_system(self, system: CollaborativeDetectionSystem):
        self.collaboration_system = system

    def _init_enhanced_capabilities(self) -> Dict[AttackType, float]:
        if self.expert_type == ExpertType.SCANNING_EXPERT:
            return {AttackType.SCANNING: 0.92, AttackType.LATERAL_MOVEMENT: 0.40,
                    AttackType.PRIVILEGE_ESCALATION: 0.25, AttackType.DATA_EXFILTRATION: 0.30,
                    AttackType.DDOS: 0.20, AttackType.ZERO_DAY: 0.15, AttackType.RANSOMWARE: 0.20}
        elif self.expert_type == ExpertType.LATERAL_EXPERT:
            return {AttackType.SCANNING: 0.45, AttackType.LATERAL_MOVEMENT: 0.88,
                    AttackType.PRIVILEGE_ESCALATION: 0.50, AttackType.DATA_EXFILTRATION: 0.40,
                    AttackType.DDOS: 0.30, AttackType.ZERO_DAY: 0.25, AttackType.RANSOMWARE: 0.35}
        elif self.expert_type == ExpertType.PRIVILEGE_EXPERT:
            return {AttackType.SCANNING: 0.30, AttackType.LATERAL_MOVEMENT: 0.50,
                    AttackType.PRIVILEGE_ESCALATION: 0.90, AttackType.DATA_EXFILTRATION: 0.40,
                    AttackType.DDOS: 0.25, AttackType.ZERO_DAY: 0.30, AttackType.RANSOMWARE: 0.40}
        elif self.expert_type == ExpertType.DATA_EXFIL_EXPERT:
            return {AttackType.SCANNING: 0.40, AttackType.LATERAL_MOVEMENT: 0.45,
                    AttackType.PRIVILEGE_ESCALATION: 0.50, AttackType.DATA_EXFILTRATION: 0.85,
                    AttackType.DDOS: 0.35, AttackType.ZERO_DAY: 0.35, AttackType.RANSOMWARE: 0.45}
        elif self.expert_type == ExpertType.DDOS_EXPERT:
            return {AttackType.SCANNING: 0.20, AttackType.LATERAL_MOVEMENT: 0.30,
                    AttackType.PRIVILEGE_ESCALATION: 0.20, AttackType.DATA_EXFILTRATION: 0.30,
                    AttackType.DDOS: 0.92, AttackType.ZERO_DAY: 0.25, AttackType.RANSOMWARE: 0.30}
        elif self.expert_type == ExpertType.ZERO_DAY_EXPERT:
            return {AttackType.SCANNING: 0.35, AttackType.LATERAL_MOVEMENT: 0.40,
                    AttackType.PRIVILEGE_ESCALATION: 0.45, AttackType.DATA_EXFILTRATION: 0.40,
                    AttackType.DDOS: 0.30, AttackType.ZERO_DAY: 0.85, AttackType.RANSOMWARE: 0.50}
        elif self.expert_type == ExpertType.RANSOMWARE_EXPERT:
            return {AttackType.SCANNING: 0.30, AttackType.LATERAL_MOVEMENT: 0.45,
                    AttackType.PRIVILEGE_ESCALATION: 0.55, AttackType.DATA_EXFILTRATION: 0.60,
                    AttackType.DDOS: 0.25, AttackType.ZERO_DAY: 0.40, AttackType.RANSOMWARE: 0.88}
        elif self.expert_type == ExpertType.HYBRID_EXPERT:
            return {AttackType.SCANNING: 0.70, AttackType.LATERAL_MOVEMENT: 0.75,
                    AttackType.PRIVILEGE_ESCALATION: 0.70, AttackType.DATA_EXFILTRATION: 0.70,
                    AttackType.DDOS: 0.65, AttackType.ZERO_DAY: 0.60, AttackType.RANSOMWARE: 0.65}
        elif self.expert_type == ExpertType.ANOMALY_EXPERT:
            return {AttackType.SCANNING: 0.65, AttackType.LATERAL_MOVEMENT: 0.70,
                    AttackType.PRIVILEGE_ESCALATION: 0.65, AttackType.DATA_EXFILTRATION: 0.70,
                    AttackType.DDOS: 0.60, AttackType.ZERO_DAY: 0.75, AttackType.RANSOMWARE: 0.75}
        else:
            return {AttackType.SCANNING: 0.65, AttackType.LATERAL_MOVEMENT: 0.70,
                    AttackType.PRIVILEGE_ESCALATION: 0.65, AttackType.DATA_EXFILTRATION: 0.65,
                    AttackType.DDOS: 0.60, AttackType.ZERO_DAY: 0.55, AttackType.RANSOMWARE: 0.60}

    def detect_attack_with_context(self, attack_type: AttackType,
                                 attack_intensity: float = 1.0,
                                 context: Optional[AttackContext] = None) -> Tuple[bool, bool, bool, float]:
        base_detection_rate = self.expert_capabilities.get(attack_type, 0.5)
        intensity_factor = min(attack_intensity, 1.5)
        adjusted_rate = base_detection_rate * intensity_factor
        expert_bias = self._calculate_expert_bias(attack_type)
        adjusted_rate *= expert_bias
        context_bonus = 0.0
        if context:
            context_bonus = self._analyze_context(context, attack_type)
        adjusted_rate += context_bonus
        collaboration_bonus = 0.0
        if self.collaboration_system:
            collaboration_bonus = self._get_collaboration_bonus(attack_type)
        adjusted_rate += collaboration_bonus
        self._adjust_threshold_based_on_history(attack_type)
        detection_prob = adjusted_rate + random.uniform(-0.05, 0.05)
        detection_prob = max(0.15, min(0.95, detection_prob))
        detected = detection_prob > self.detection_threshold
        self.attack_type_stats[attack_type]['total'] += 1
        false_positive = False
        false_negative = False
        confidence_score = detection_prob
        if detected:
            self.detection_counts += 1
            self.attack_type_stats[attack_type]['detected'] += 1
            fp_rate = self._calculate_fp_rate(attack_type, expert_bias)
            if random.random() < fp_rate:
                false_positive = True
                self.false_positives += 1
                confidence_score *= 0.7
            else:
                self.true_positives += 1
                confidence_score *= 1.1
        else:
            fn_rate = self._calculate_fn_rate(attack_type, expert_bias)
            if random.random() < fn_rate:
                false_negative = True
                self.false_negatives += 1
            if context_bonus > 0.15 and detection_prob > self.detection_threshold * 0.8:
                detected = True
                confidence_score = detection_prob * 0.8
        self.detection_history.append({
            'attack_type': attack_type, 'detected': detected, 'fp': false_positive,
            'fn': false_negative, 'confidence': confidence_score,
            'timestamp': datetime.now().timestamp()
        })
        return detected, false_positive, false_negative, confidence_score

    def _calculate_expert_bias(self, attack_type: AttackType) -> float:
        expert_specializations = {
            ExpertType.SCANNING_EXPERT: AttackType.SCANNING,
            ExpertType.LATERAL_EXPERT: AttackType.LATERAL_MOVEMENT,
            ExpertType.PRIVILEGE_EXPERT: AttackType.PRIVILEGE_ESCALATION,
            ExpertType.DATA_EXFIL_EXPERT: AttackType.DATA_EXFILTRATION,
            ExpertType.DDOS_EXPERT: AttackType.DDOS,
            ExpertType.ZERO_DAY_EXPERT: AttackType.ZERO_DAY,
            ExpertType.RANSOMWARE_EXPERT: AttackType.RANSOMWARE,
            ExpertType.ANOMALY_EXPERT: AttackType.ZERO_DAY
        }
        if self.expert_type in expert_specializations:
            if expert_specializations[self.expert_type] == attack_type:
                return 1.25
        if self.expert_type == ExpertType.HYBRID_EXPERT:
            return 1.15
        return 1.0

    def _analyze_context(self, context: AttackContext, attack_type: AttackType) -> float:
        context_score = 0.0
        if 2 <= context.time_of_day <= 6:
            context_score += 0.05
        if len(context.attack_path) > 5:
            context_score += 0.03
        if context.attack_pattern == "aggressive":
            context_score += 0.04
        elif context.attack_pattern == "stealthy":
            context_score += 0.02
        if len(context.resources_accessed) > 3:
            context_score += 0.03
        return context_score

    def _get_collaboration_bonus(self, attack_type: AttackType) -> float:
        if not self.collaboration_system:
            return 0.0
        relevant_threats = self.collaboration_system.get_relevant_threats(self.node_id)
        if relevant_threats:
            threat_count = len(relevant_threats)
            avg_confidence = sum(t['confidence'] for t in relevant_threats) / threat_count
            return min(0.15, threat_count * 0.02 + avg_confidence * 0.05)
        return 0.0

    def _adjust_threshold_based_on_history(self, attack_type: AttackType):
        if len(self.detection_history) < 10:
            return
        recent_detections = list(self.detection_history)[-10:]
        tp_count = sum(1 for d in recent_detections if d['detected'] and not d['fp'])
        fp_count = sum(1 for d in recent_detections if d['fp'])
        accuracy = tp_count / max(1, tp_count + fp_count)
        if accuracy < 0.8:
            self.detection_threshold *= (1 - self.learning_rate)
        elif accuracy > 0.95:
            self.detection_threshold *= (1 + self.learning_rate)
        self.detection_threshold = max(self.base_threshold * 0.7,
                                     min(self.detection_threshold, self.base_threshold * 1.3))

    def _calculate_fp_rate(self, attack_type: AttackType, expert_bias: float) -> float:
        base_fp_rate = 0.03
        if expert_bias > 1.2:
            base_fp_rate = 0.01
        if attack_type in [AttackType.ZERO_DAY, AttackType.RANSOMWARE]:
            base_fp_rate += 0.02
        total_detections = self.attack_type_stats[attack_type]['total']
        if total_detections > 0:
            detection_rate = self.attack_type_stats[attack_type]['detected'] / total_detections
            if detection_rate > 0.9:
                base_fp_rate *= 0.8
        return base_fp_rate

    def _calculate_fn_rate(self, attack_type: AttackType, expert_bias: float) -> float:
        base_fn_rate = 0.05
        if expert_bias > 1.2:
            base_fn_rate = 0.02
        if attack_type in [AttackType.ZERO_DAY, AttackType.RANSOMWARE]:
            base_fn_rate += 0.03
        return base_fn_rate


# ==================== 高级动态攻击模拟器 ====================
class AdvancedDynamicAttackSimulator:
    """高级动态攻击模拟器（集成MoE门控路由与虚假响应）"""

    def __init__(self,
                 network_graph: nx.Graph,
                 honeypot_nodes: Dict[str, ExpertType],
                 random_seed: Optional[int] = None,
                 use_gate_routing: bool = True,
                 steiner_tree: Optional[Dict] = None,
                 expert_profiles: Optional[Dict] = None):

        if not isinstance(network_graph, nx.Graph):
            raise TypeError("network_graph 必须是 networkx.Graph 实例")
        if not honeypot_nodes:
            raise ValueError("honeypot_nodes 不能为空")

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        self.network = network_graph
        self.use_gate_routing = use_gate_routing
        self.steiner_tree = steiner_tree or {}
        self.expert_profiles = expert_profiles or {}

        # 协同检测系统
        self.collaboration_system = CollaborativeDetectionSystem()
        self.collaboration_system.network = self.network

        # 初始化专家蜜罐
        self.expert_honeypots: Dict[str, AdaptiveMoEExpertHoneypot] = {}
        for node_id, expert_type in honeypot_nodes.items():
            if node_id in self.network.nodes():
                honeypot = AdaptiveMoEExpertHoneypot(node_id, expert_type)
                honeypot.set_collaboration_system(self.collaboration_system)
                self.expert_honeypots[node_id] = honeypot

        # 初始化虚假响应器（为每个蜜罐节点创建）
        self.fake_responders: Dict[str, FakeExpertResponder] = {}
        for node_id, expert_type in honeypot_nodes.items():
            self.fake_responders[node_id] = FakeExpertResponder(
                steiner_tree=self.steiner_tree,
                expert_profiles=self.expert_profiles,
                expert_type=expert_type.value,
                node_id=node_id
            )

        # 初始化MoE门控路由器
        all_expert_types = list(set(honeypot_nodes.values()))
        self.moe_router = MoERouter(all_expert_types) if use_gate_routing else None

        # 攻击参数、攻击者模型等
        self.attack_parameters = self._init_attack_parameters()
        self.attacker_models = self._init_attacker_models()
        self.attack_logs: List[AttackPath] = []
        self.metrics = self._initialize_metrics()
        self._analyze_network_structure()

        print(f" 高级版MoE动态攻击模拟器初始化完成")
        print(f"   网络节点数: {self.network.number_of_nodes()}")
        print(f"   专家蜜罐数: {len(self.expert_honeypots)}")
        print(f"   协同检测系统: 已启用")
        print(f"   MoE门控路由: {'启用' if use_gate_routing else '禁用'}")
        print(f"   虚假响应器: 已初始化 ({len(self.fake_responders)}个)")

    def _init_attack_parameters(self) -> Dict[AttackType, Dict]:
        return {
            AttackType.SCANNING: {
                'success_rate': 0.70, 'intensity': 0.7, 'max_steps': 30,
                'behavior': 'random', 'target_preference': 0.2,
                'honeypot_avoidance': 0.3, 'stealth_level': 0.4, 'resource_consumption': 0.2
            },
            AttackType.LATERAL_MOVEMENT: {
                'success_rate': 0.60, 'intensity': 0.8, 'max_steps': 40,
                'behavior': 'targeted', 'target_preference': 0.7,
                'honeypot_avoidance': 0.4, 'stealth_level': 0.6, 'resource_consumption': 0.3
            },
            AttackType.PRIVILEGE_ESCALATION: {
                'success_rate': 0.45, 'intensity': 0.9, 'max_steps': 25,
                'behavior': 'focused', 'target_preference': 0.6,
                'honeypot_avoidance': 0.5, 'stealth_level': 0.7, 'resource_consumption': 0.4
            },
            AttackType.DATA_EXFILTRATION: {
                'success_rate': 0.55, 'intensity': 0.85, 'max_steps': 35,
                'behavior': 'stealthy', 'target_preference': 0.5,
                'honeypot_avoidance': 0.4, 'stealth_level': 0.8, 'resource_consumption': 0.5
            },
            AttackType.DDOS: {
                'success_rate': 0.80, 'intensity': 0.95, 'max_steps': 20,
                'behavior': 'aggressive', 'target_preference': 0.4,
                'honeypot_avoidance': 0.2, 'stealth_level': 0.2, 'resource_consumption': 0.9
            },
            AttackType.ZERO_DAY: {
                'success_rate': 0.65, 'intensity': 0.9, 'max_steps': 30,
                'behavior': 'stealthy', 'target_preference': 0.8,
                'honeypot_avoidance': 0.6, 'stealth_level': 0.9, 'resource_consumption': 0.3
            },
            AttackType.RANSOMWARE: {
                'success_rate': 0.50, 'intensity': 0.85, 'max_steps': 25,
                'behavior': 'aggressive', 'target_preference': 0.7,
                'honeypot_avoidance': 0.3, 'stealth_level': 0.5, 'resource_consumption': 0.7
            }
        }

    def _init_attacker_models(self) -> Dict[str, Dict]:
        return {
            'script_kiddie': {
                'skill_level': 0.3, 'persistence': 0.2, 'adaptability': 0.1,
                'stealth': 0.2, 'target_selection': 'random', 'target_selection_weight': 0.5
            },
            'hacker': {
                'skill_level': 0.7, 'persistence': 0.5, 'adaptability': 0.6,
                'stealth': 0.7, 'target_selection': 'strategic', 'target_selection_weight': 1.0
            },
            'apt_group': {
                'skill_level': 0.9, 'persistence': 0.9, 'adaptability': 0.8,
                'stealth': 0.9, 'target_selection': 'focused', 'target_selection_weight': 1.2
            },
            'insider_threat': {
                'skill_level': 0.6, 'persistence': 0.4, 'adaptability': 0.5,
                'stealth': 0.8, 'target_selection': 'precise', 'target_selection_weight': 1.1
            }
        }

    def _initialize_metrics(self) -> Dict[str, Any]:
        metrics = {
            'total_attacks': 0, 'captured_attacks': 0, 'total_steps': 0,
            'capture_latency': [], 'attack_type_distribution': defaultdict(int),
            'expert_performance': {}, 'attacker_type_distribution': defaultdict(int),
            'true_positives': 0, 'false_positives': 0, 'false_negatives': 0,
            'touch_probability': 0.0, 'attack_success_rate': 0.0,
            'total_successful_actions': 0, 'total_action_steps': 0,
            'early_detection_rate': 0.0, 'collaborative_detections': 0, 'evasion_rate': 0.0,
            'gate_routing_stats': {
                'routing_calls': 0,
                'routing_expert_distribution': defaultdict(int),
                'routing_accuracy': 0.0
            }
        }
        for node_id in self.expert_honeypots.keys():
            metrics['expert_performance'][node_id] = {
                'detection_counts': 0, 'true_positives': 0, 'false_positives': 0,
                'false_negatives': 0, 'expert_type': self.expert_honeypots[node_id].expert_type.value,
                'attack_type_detections': defaultdict(int), 'confidence_scores': [],
                'context_aware_detections': 0
            }
        return metrics

    def _analyze_network_structure(self):
        self.node_importance = {}
        degree_centrality = nx.degree_centrality(self.network)
        try:
            betweenness = nx.betweenness_centrality(self.network, k=min(20, self.network.number_of_nodes()))
        except:
            betweenness = {node: 0.0 for node in self.network.nodes()}
        try:
            closeness = nx.closeness_centrality(self.network)
        except:
            closeness = {node: 0.0 for node in self.network.nodes()}
        for node in self.network.nodes():
            importance = (degree_centrality[node] * 0.3 +
                          betweenness[node] * 0.4 +
                          closeness[node] * 0.3)
            self.node_importance[node] = importance
        sorted_nodes = sorted(self.node_importance.items(), key=lambda x: x[1], reverse=True)
        cutoff = int(len(sorted_nodes) * 0.2)
        self.critical_nodes = {node for node, _ in sorted_nodes[:cutoff]}

    def simulate_attack(self,
                       start_node: str,
                       target_node: str,
                       attack_type: AttackType,
                       attacker_model: str = 'hacker') -> AttackPath:
        if start_node not in self.network.nodes():
            raise ValueError(f"起始节点 {start_node} 不存在")
        if target_node not in self.network.nodes():
            raise ValueError(f"目标节点 {target_node} 不存在")

        path_id = f"attack_{len(self.attack_logs)}_{datetime.now().strftime('%H%M%S')}"
        current_node = start_node

        context = AttackContext(
            attacker_id=f"attacker_{random.randint(1000, 9999)}",
            attack_path=[current_node],
            attack_pattern=self.attack_parameters[attack_type]['behavior'],
            attack_intensity=self.attack_parameters[attack_type]['intensity'],
            time_of_day=random.uniform(0, 24),
            previous_actions=[],
            resources_accessed=set()
        )

        path = AttackPath(
            path_id=path_id,
            attacker_id=context.attacker_id,
            start_node=start_node,
            target_node=target_node,
            actions=[],
            total_steps=0
        )

        attack_params = self.attack_parameters[attack_type]
        max_steps = attack_params['max_steps']
        attack_behavior = attack_params['behavior']
        attack_intensity = attack_params['intensity']
        target_preference = attack_params['target_preference']
        honeypot_avoidance = attack_params['honeypot_avoidance']
        stealth_level = attack_params['stealth_level']

        attacker_params = self.attacker_models[attacker_model]

        step = 0
        captured = False
        expert_detected = None
        successful_actions = 0
        evasive_actions = 0
        detection_confidence = 0.0
        visited_nodes = set([current_node])

        while step < max_steps and current_node != target_node:
            context.attack_path.append(current_node)

            next_node = self._intelligent_select_next_node(
                current_node, target_node, attack_type, attack_behavior,
                target_preference, honeypot_avoidance, visited_nodes,
                attacker_params, stealth_level
            )

            visited_nodes.add(next_node)

            action_success = self._execute_intelligent_attack(
                current_node, next_node, attack_type, attack_params['success_rate'],
                attacker_params['skill_level']
            )

            if action_success:
                successful_actions += 1
                if random.random() < 0.3:
                    context.resources_accessed.add(next_node)

            self._update_attacker_behavior(attacker_params, step, captured)

            detected_by = None
            detection_latency = 0.0
            false_positive = False
            false_negative = False
            confidence = 0.0
            routed_expert = None

            # ===== 生成虚假响应 =====
            fake_latency = 0.0
            fake_response_type = ""
            gradient_mask_list = []
            if next_node in self.fake_responders:
                attack_ctx_for_fake = {
                    'type': attack_type.value,
                    'stage': min(step // 5, 2),
                    'network_congestion': 0.0,
                    'source_ip': f"10.0.0.{random.randint(1,254)}",
                    'target_port': random.choice([22,80,443])
                }
                fake_resp = self.fake_responders[next_node].respond(attack_ctx_for_fake)
                fake_latency = fake_resp['latency']
                fake_response_type = fake_resp['response'][:100]
                gradient_mask = fake_resp.get('gradient_mask', np.array([]))
                if isinstance(gradient_mask, np.ndarray):
                    gradient_mask_list = gradient_mask.tolist()
                else:
                    gradient_mask_list = list(gradient_mask) if gradient_mask is not None else []
            # =========================

            # 门控路由决策
            if self.use_gate_routing and self.moe_router is not None:
                visited_ratio = len(visited_nodes) / max(1, self.network.number_of_nodes())
                node_importance = self.node_importance.get(next_node, 0.5)
                is_honeypot = next_node in self.expert_honeypots
                routed_expert = self.moe_router.route(
                    attack_type, attack_intensity, attack_behavior,
                    node_importance, is_honeypot, visited_ratio,
                    context.time_of_day, attacker_params['skill_level']
                )
                self.metrics['gate_routing_stats']['routing_calls'] += 1
                self.metrics['gate_routing_stats']['routing_expert_distribution'][routed_expert.value] += 1

            # 蜜罐检测
            if next_node in self.expert_honeypots:
                honeypot = self.expert_honeypots[next_node]
                detected, fp, fn, conf = honeypot.detect_attack_with_context(
                    attack_type, attack_intensity, context
                )
                confidence = conf

                if detected and not fp:
                    if step <= 5:
                        self.metrics['early_detection_rate'] += 1
                    if conf > 0.8 and self._is_collaborative_detection(next_node, attack_type):
                        self.metrics['collaborative_detections'] += 1

                    captured = True
                    detected_by = next_node
                    expert_detected = honeypot.expert_type.value
                    detection_latency = step + random.uniform(0.5, 3.0)
                    detection_confidence = conf

                    if detected_by in self.metrics['expert_performance']:
                        self.metrics['expert_performance'][detected_by]['detection_counts'] += 1
                        self.metrics['expert_performance'][detected_by]['true_positives'] += 1
                        self.metrics['expert_performance'][detected_by]['attack_type_detections'][attack_type.value] += 1
                        self.metrics['expert_performance'][detected_by]['confidence_scores'].append(conf)
                        if conf > 0.85:
                            self.metrics['expert_performance'][detected_by]['context_aware_detections'] += 1

                if fp:
                    self.metrics['false_positives'] += 1
                    if next_node in self.metrics['expert_performance']:
                        self.metrics['expert_performance'][next_node]['false_positives'] += 1
                if fn:
                    self.metrics['false_negatives'] += 1
                    if next_node in self.metrics['expert_performance']:
                        self.metrics['expert_performance'][next_node]['false_negatives'] += 1

                false_positive = fp
                false_negative = fn

            # 攻击规避
            if not captured and step > 3 and random.random() < attacker_params['adaptability'] * 0.3:
                evasive_actions += 1
                context.attack_pattern = "evasive"

            # 记录攻击动作（包含虚假响应字段）
            action = AttackAction(
                attack_id=f"{path_id}_step_{step}",
                attack_type=attack_type,
                source_node=current_node,
                target_node=next_node,
                timestamp=datetime.now().timestamp() + step,
                success=action_success,
                context=context,
                detected_by=detected_by,
                detection_latency=detection_latency,
                false_positive=false_positive,
                false_negative=false_negative,
                confidence_score=confidence,
                routed_expert=routed_expert.value if routed_expert else None,
                fake_response_latency=fake_latency,
                fake_response_type=fake_response_type,
                gradient_mask_applied=gradient_mask_list
            )

            path.actions.append(action)
            step += 1
            current_node = next_node

            if detected_by:
                self.collaboration_system.share_information(
                    detected_by, attack_type,
                    datetime.now().timestamp(), confidence
                )

            if captured:
                path.captured = True
                path.capture_step = step
                path.expert_type_detected = expert_detected
                path.detection_confidence = detection_confidence
                path.evasive_actions = evasive_actions
                break

        path.total_steps = step
        self.attack_logs.append(path)
        self.collaboration_system.update_attack_patterns(path)
        self._update_metrics(path, attack_type, captured, successful_actions, step, evasive_actions)
        self.metrics['attacker_type_distribution'][attacker_model] += 1

        return path

    def _intelligent_select_next_node(self,
                                    current_node: str,
                                    target_node: str,
                                    attack_type: AttackType,
                                    behavior: str,
                                    target_preference: float,
                                    honeypot_avoidance: float,
                                    visited_nodes: Set[str],
                                    attacker_params: Dict,
                                    stealth_level: float) -> str:
        try:
            neighbors = list(self.network.neighbors(current_node))
        except Exception:
            return current_node
        if not neighbors:
            return current_node

        neighbor_scores = []
        for neighbor in neighbors:
            score = 0.0
            if neighbor == target_node:
                score += 5.0 * attacker_params['skill_level']
            else:
                try:
                    distance = nx.shortest_path_length(self.network, neighbor, target_node)
                    if distance > 0:
                        distance_score = 2.0 / distance * target_preference
                        score += distance_score * attacker_params.get('target_selection_weight', 1.0)
                except:
                    pass

            if neighbor in self.expert_honeypots:
                honeypot = self.expert_honeypots[neighbor]
                honeypot_type = honeypot.expert_type
                avoidance_factor = honeypot_avoidance * attacker_params['stealth']
                if attack_type == AttackType.SCANNING and honeypot_type == ExpertType.SCANNING_EXPERT:
                    score -= 3.0 * avoidance_factor
                elif attack_type == AttackType.LATERAL_MOVEMENT and honeypot_type == ExpertType.LATERAL_EXPERT:
                    score -= 4.0 * avoidance_factor
                elif attack_type == AttackType.DATA_EXFILTRATION and honeypot_type == ExpertType.DATA_EXFIL_EXPERT:
                    score -= 5.0 * avoidance_factor
                elif attack_type == AttackType.PRIVILEGE_ESCALATION and honeypot_type == ExpertType.PRIVILEGE_EXPERT:
                    score -= 4.0 * avoidance_factor
                elif attack_type == AttackType.ZERO_DAY and honeypot_type in [ExpertType.ZERO_DAY_EXPERT, ExpertType.ANOMALY_EXPERT]:
                    score -= 4.5 * avoidance_factor
                else:
                    score -= 2.0 * avoidance_factor

            node_value = self.node_importance.get(neighbor, 0.5)
            if node_value > 0.7:
                attraction = node_value * 2.0
                defense_penalty = node_value * 0.5 if stealth_level < 0.7 else 0
                score += attraction - defense_penalty
            else:
                score += node_value

            if neighbor in visited_nodes:
                penalty = -1.5 if attack_type != AttackType.SCANNING else -0.5
                score += penalty

            neighbor_degree = self.network.degree(neighbor)
            if neighbor_degree >= 3:
                if attack_type in [AttackType.LATERAL_MOVEMENT, AttackType.DATA_EXFILTRATION]:
                    score += 0.5

            if attacker_params['target_selection'] == 'strategic':
                if neighbor in self.critical_nodes:
                    score += 1.0

            adaptability = attacker_params['adaptability']
            if attack_type == AttackType.SCANNING:
                randomness = random.uniform(-0.3, 0.5) * (1 - adaptability * 0.5)
            elif attack_type == AttackType.DDOS:
                randomness = random.uniform(-0.1, 0.3)
            else:
                randomness = random.uniform(-0.2, 0.3) * (1 - adaptability * 0.3)
            score += randomness

            neighbor_scores.append((neighbor, score))

        if not neighbor_scores:
            return current_node

        scores = np.array([score for _, score in neighbor_scores])
        temperature = 1.0 - attacker_params['skill_level'] * 0.5
        exp_scores = np.exp(scores / temperature - np.max(scores / temperature))
        probabilities = exp_scores / exp_scores.sum()
        if attacker_params['skill_level'] > 0.7:
            if random.random() < 0.8:
                selected_idx = np.argmax(probabilities)
            else:
                selected_idx = np.random.choice(len(neighbor_scores), p=probabilities)
        else:
            selected_idx = np.random.choice(len(neighbor_scores), p=probabilities)
        return neighbor_scores[selected_idx][0]

    def _execute_intelligent_attack(self,
                                  source: str,
                                  target: str,
                                  attack_type: AttackType,
                                  base_success_rate: float,
                                  skill_level: float) -> bool:
        reliability = 0.8
        security_level = 1
        if self.network.has_edge(source, target):
            edge_data = self.network[source][target]
            reliability = edge_data.get('reliability', 0.8)
            security_level = edge_data.get('security_level', 1)

        type_multiplier = 1.0
        if attack_type == AttackType.SCANNING:
            type_multiplier = 1.15
        elif attack_type == AttackType.DDOS:
            type_multiplier = 1.10
        elif attack_type == AttackType.PRIVILEGE_ESCALATION:
            type_multiplier = 0.85
        elif attack_type == AttackType.ZERO_DAY:
            type_multiplier = 1.25
        elif attack_type == AttackType.RANSOMWARE:
            type_multiplier = 0.90

        skill_multiplier = 0.8 + skill_level * 0.4
        security_factor = max(0.5, 1.0 / max(security_level, 0.5))
        success_rate = (base_success_rate * reliability * security_factor *
                       type_multiplier * skill_multiplier)

        target_importance = self.node_importance.get(target, 0.5)
        if target_importance > 0.7:
            success_rate *= (1 - target_importance * 0.3)

        success_rate += random.uniform(-0.08, 0.08)
        success_rate = max(0.2, min(0.9, success_rate))
        return random.random() < success_rate

    def _update_attacker_behavior(self, attacker_params: Dict, step: int, captured: bool):
        if captured and step > 5:
            attacker_params['stealth'] = min(1.0, attacker_params['stealth'] + 0.05)
            attacker_params['adaptability'] = min(1.0, attacker_params['adaptability'] + 0.03)

    def _is_collaborative_detection(self, node_id: str, attack_type: AttackType) -> bool:
        if not self.collaboration_system:
            return False
        relevant_threats = self.collaboration_system.get_relevant_threats(node_id)
        if len(relevant_threats) >= 2:
            same_type_count = sum(1 for t in relevant_threats if t['attack_type'] == attack_type)
            return same_type_count >= 1
        return False

    def _update_metrics(self, path: AttackPath, attack_type: AttackType,
                       captured: bool, successful_actions: int,
                       total_steps: int, evasive_actions: int):
        self.metrics['total_attacks'] += 1
        if captured:
            self.metrics['captured_attacks'] += 1
            self.metrics['capture_latency'].append(path.capture_step)
            self.metrics['true_positives'] += 1
        self.metrics['total_steps'] += total_steps
        self.metrics['attack_type_distribution'][attack_type.value] += 1
        self.metrics['touch_probability'] = \
            self.metrics['captured_attacks'] / max(1, self.metrics['total_attacks'])
        if total_steps > 0:
            self.metrics['total_successful_actions'] += successful_actions
            self.metrics['total_action_steps'] += total_steps
            self.metrics['attack_success_rate'] = \
                self.metrics['total_successful_actions'] / max(1, self.metrics['total_action_steps'])
        if evasive_actions > 0:
            self.metrics['evasion_rate'] = \
                sum(p.evasive_actions for p in self.attack_logs) / max(1, len(self.attack_logs))

    def run_batch_attacks(self, num_attacks: int = 500) -> Dict[str, Any]:
        attack_type_dist = {
            AttackType.SCANNING: 0.30, AttackType.LATERAL_MOVEMENT: 0.25,
            AttackType.PRIVILEGE_ESCALATION: 0.15, AttackType.DATA_EXFILTRATION: 0.10,
            AttackType.DDOS: 0.08, AttackType.ZERO_DAY: 0.07, AttackType.RANSOMWARE: 0.05
        }
        attacker_type_dist = {
            'script_kiddie': 0.30, 'hacker': 0.45,
            'apt_group': 0.15, 'insider_threat': 0.10
        }

        self.attack_logs = []
        self.metrics = self._initialize_metrics()
        all_nodes = list(self.network.nodes())

        for i in range(num_attacks):
            attack_type = self._select_by_distribution(attack_type_dist)
            attacker_type = self._select_by_distribution(attacker_type_dist)
            start_node = random.choice(all_nodes)
            target_node = random.choice(all_nodes)
            attempts = 0
            while (target_node == start_node or
                   self._calculate_node_distance(start_node, target_node) < 2) and attempts < 5:
                target_node = random.choice(all_nodes)
                attempts += 1
            try:
                self.simulate_attack(start_node, target_node, attack_type, attacker_type)
            except Exception as e:
                print(f"  攻击模拟失败: {e}")
                continue
            if (i + 1) % 100 == 0:
                print(f"   进度: {i + 1}/{num_attacks} 攻击完成")
        return self.get_metrics()

    def _select_by_distribution(self, distribution: Dict) -> Any:
        items = list(distribution.keys())
        probabilities = list(distribution.values())
        total = sum(probabilities)
        normalized_probs = [p / total for p in probabilities]
        return random.choices(items, weights=normalized_probs, k=1)[0]

    def _calculate_node_distance(self, node1: str, node2: str) -> int:
        try:
            return nx.shortest_path_length(self.network, node1, node2)
        except:
            return float('inf')

    def get_metrics(self) -> Dict[str, Any]:
        capture_latency = self.metrics['capture_latency']
        if capture_latency:
            capture_latency_mean = float(np.mean(capture_latency))
            capture_latency_std = float(np.std(capture_latency))
        else:
            capture_latency_mean = 0.0
            capture_latency_std = 0.0

        total_attacks = self.metrics['total_attacks']
        if total_attacks > 0:
            average_steps_per_attack = self.metrics['total_steps'] / total_attacks
        else:
            average_steps_per_attack = 0.0

        total_detections = self.metrics['true_positives'] + self.metrics['false_positives']
        false_positive_rate = 0.0
        if total_detections > 0:
            false_positive_rate = self.metrics['false_positives'] / total_detections

        false_negative_rate = 0.0
        total_attacks_without_detection = self.metrics['total_attacks'] - self.metrics['captured_attacks']
        if total_attacks_without_detection > 0:
            false_negative_rate = self.metrics['false_negatives'] / total_attacks_without_detection

        early_detection_rate = 0.0
        if self.metrics['captured_attacks'] > 0:
            early_detection_rate = self.metrics['early_detection_rate'] / self.metrics['captured_attacks']

        collaborative_detection_rate = 0.0
        if self.metrics['captured_attacks'] > 0:
            collaborative_detection_rate = self.metrics['collaborative_detections'] / self.metrics['captured_attacks']

        avg_confidence_scores = {}
        for node_id, perf in self.metrics['expert_performance'].items():
            if perf['confidence_scores']:
                avg_confidence_scores[node_id] = np.mean(perf['confidence_scores'])

        result = {
            'total_attacks': self.metrics['total_attacks'],
            'captured_attacks': self.metrics['captured_attacks'],
            'touch_probability': float(self.metrics['touch_probability']),
            'capture_latency_mean': capture_latency_mean,
            'capture_latency_std': capture_latency_std,
            'average_steps_per_attack': float(average_steps_per_attack),
            'attack_success_rate': float(self.metrics['attack_success_rate']),
            'false_positive_rate': float(false_positive_rate),
            'false_negative_rate': float(false_negative_rate),
            'early_detection_rate': float(early_detection_rate),
            'collaborative_detection_rate': float(collaborative_detection_rate),
            'evasion_rate': float(self.metrics['evasion_rate']),
            'precision': self.metrics['true_positives'] / max(1, self.metrics['true_positives'] + self.metrics['false_positives']),
            'recall': self.metrics['true_positives'] / max(1, self.metrics['true_positives'] + self.metrics['false_negatives']),
            'f1_score': 2 * (self.metrics['true_positives']) / max(1, 2 * self.metrics['true_positives'] + self.metrics['false_positives'] + self.metrics['false_negatives']),
            'attack_type_distribution': dict(self.metrics['attack_type_distribution']),
            'attacker_type_distribution': dict(self.metrics['attacker_type_distribution']),
            'expert_performance': {},
            'avg_confidence_scores': avg_confidence_scores,
            'gate_routing_stats': dict(self.metrics['gate_routing_stats'])
        }

        for node_id, perf in self.metrics['expert_performance'].items():
            result['expert_performance'][node_id] = {
                'detection_counts': perf['detection_counts'],
                'true_positives': perf['true_positives'],
                'false_positives': perf['false_positives'],
                'false_negatives': perf['false_negatives'],
                'expert_type': perf['expert_type'],
                'attack_type_detections': dict(perf['attack_type_detections']),
                'avg_confidence': np.mean(perf['confidence_scores']) if perf['confidence_scores'] else 0.0,
                'context_aware_detections': perf['context_aware_detections'],
                'context_aware_rate': perf['context_aware_detections'] / max(1, perf['detection_counts'])
            }
        return result

    def save_attack_logs(self, filename: str = "attack_logs.json") -> None:
        """保存攻击日志到JSON文件，包含虚假响应字段"""
        logs_to_save = []
        for path in self.attack_logs:
            for action in path.actions:
                log_entry = {
                    "timestamp": action.timestamp,
                    "attack_id": action.attack_id,
                    "attack_type": action.attack_type.value,
                    "source_node": action.source_node,
                    "target_node": action.target_node,
                    "success": action.success,
                    "detected_by": action.detected_by,
                    "detection_latency": action.detection_latency,
                    "false_positive": action.false_positive,
                    "false_negative": action.false_negative,
                    "confidence_score": action.confidence_score,
                    "routed_expert": action.routed_expert,
                    "fake_response_latency": action.fake_response_latency,
                    "fake_response_type": action.fake_response_type,
                    "gradient_mask_applied": action.gradient_mask_applied,
                    "attack_pattern": action.context.attack_pattern if action.context else None,
                    "attack_intensity": action.context.attack_intensity if action.context else None,
                    "time_of_day": action.context.time_of_day if action.context else None
                }
                logs_to_save.append(log_entry)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(logs_to_save, f, indent=2, ensure_ascii=False)
        print(f" 攻击日志已保存至: {filename}")


# ==================== 遗传算法优化蜜罐部署 ====================
class GeneticHoneypotOptimizer:
    """使用遗传算法优化蜜罐部署（节点选择和专家类型分配）"""
    def __init__(self, network: nx.Graph, num_honeypots: int, population_size: int = 50,
                 generations: int = 100, mutation_rate: float = 0.1, crossover_rate: float = 0.8,
                 random_seed: Optional[int] = None):
        self.network = network
        self.num_honeypots = num_honeypots
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.all_nodes = list(network.nodes())
        self.expert_types = list(ExpertType)

        # 节点重要性预计算
        self.node_importance = self._compute_node_importance()
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

    def _compute_node_importance(self) -> Dict[str, float]:
        """计算节点重要性作为启发式信息"""
        degree_cent = nx.degree_centrality(self.network)
        try:
            betweenness = nx.betweenness_centrality(self.network, k=min(20, self.network.number_of_nodes()))
        except:
            betweenness = {node: 0.0 for node in self.network.nodes()}
        try:
            closeness = nx.closeness_centrality(self.network)
        except:
            closeness = {node: 0.0 for node in self.network.nodes()}
        importance = {}
        for node in self.network.nodes():
            importance[node] = (degree_cent[node] * 0.3 + betweenness[node] * 0.4 + closeness[node] * 0.3)
        return importance

    def _encode(self, deployment: Dict[str, ExpertType]) -> Tuple[List[str], List[int]]:
        """将部署字典编码为个体（节点列表+专家索引列表）"""
        nodes = list(deployment.keys())
        expert_indices = [self.expert_types.index(et) for et in deployment.values()]
        return nodes, expert_indices

    def _decode(self, nodes: List[str], expert_indices: List[int]) -> Dict[str, ExpertType]:
        """解码为部署字典"""
        return {nodes[i]: self.expert_types[expert_indices[i]] for i in range(len(nodes))}

    def _create_individual(self) -> Tuple[List[str], List[int]]:
        """创建随机个体（节点+专家类型）"""
        # 按重要性加权选择节点
        weights = [1 + self.node_importance[node] for node in self.all_nodes]
        nodes = random.choices(self.all_nodes, weights=weights, k=self.num_honeypots)
        # 专家类型分布偏向专业专家（适当调整）
        type_weights = [0.12, 0.12, 0.12, 0.12, 0.12, 0.08, 0.08, 0.08, 0.08, 0.08]  # 共10种
        expert_indices = random.choices(range(len(self.expert_types)), weights=type_weights, k=self.num_honeypots)
        return nodes, expert_indices

    def _fitness(self, nodes: List[str], expert_indices: List[int]) -> float:
        """
        适应度函数：评估部署的预期检测性能
        使用启发式指标：节点覆盖度、专家匹配度、关键节点覆盖率
        """
        deployment = self._decode(nodes, expert_indices)
        # 1. 节点覆盖度（唯一节点比例）
        coverage = len(set(nodes)) / self.network.number_of_nodes()
        # 2. 专家匹配度：每个专家对其最擅长攻击类型的平均能力（按节点重要性加权）
        avg_capability = 0.0
        for node, et in deployment.items():
            importance = self.node_importance[node]
            # 专家最大能力（取对所有攻击类型的最大值）
            max_cap = max(self._expert_capability(et, at) for at in AttackType)
            avg_capability += importance * max_cap
        avg_capability /= len(deployment)
        # 3. 关键节点覆盖率（前20%重要节点中被覆盖的比例）
        critical_nodes = self._critical_nodes(0.2)
        critical_covered = sum(1 for node in nodes if node in critical_nodes)
        critical_coverage = critical_covered / len(critical_nodes) if critical_nodes else 0
        # 综合适应度（权重可调）
        fitness = 0.3 * coverage + 0.5 * avg_capability + 0.2 * critical_coverage
        return fitness

    def _expert_capability(self, expert_type: ExpertType, attack_type: AttackType) -> float:
        """专家对某攻击类型的能力（启发式）"""
        mapping = {
            ExpertType.SCANNING_EXPERT: {AttackType.SCANNING: 0.9, AttackType.LATERAL_MOVEMENT: 0.4, AttackType.PRIVILEGE_ESCALATION: 0.2,
                                         AttackType.DATA_EXFILTRATION: 0.3, AttackType.DDOS: 0.2, AttackType.ZERO_DAY: 0.1, AttackType.RANSOMWARE: 0.2},
            ExpertType.LATERAL_EXPERT: {AttackType.SCANNING: 0.4, AttackType.LATERAL_MOVEMENT: 0.9, AttackType.PRIVILEGE_ESCALATION: 0.5,
                                        AttackType.DATA_EXFILTRATION: 0.4, AttackType.DDOS: 0.3, AttackType.ZERO_DAY: 0.2, AttackType.RANSOMWARE: 0.3},
            ExpertType.PRIVILEGE_EXPERT: {AttackType.SCANNING: 0.3, AttackType.LATERAL_MOVEMENT: 0.5, AttackType.PRIVILEGE_ESCALATION: 0.9,
                                          AttackType.DATA_EXFILTRATION: 0.4, AttackType.DDOS: 0.2, AttackType.ZERO_DAY: 0.3, AttackType.RANSOMWARE: 0.4},
            ExpertType.DATA_EXFIL_EXPERT: {AttackType.SCANNING: 0.4, AttackType.LATERAL_MOVEMENT: 0.4, AttackType.PRIVILEGE_ESCALATION: 0.5,
                                           AttackType.DATA_EXFILTRATION: 0.9, AttackType.DDOS: 0.3, AttackType.ZERO_DAY: 0.3, AttackType.RANSOMWARE: 0.4},
            ExpertType.DDOS_EXPERT: {AttackType.SCANNING: 0.2, AttackType.LATERAL_MOVEMENT: 0.3, AttackType.PRIVILEGE_ESCALATION: 0.2,
                                     AttackType.DATA_EXFILTRATION: 0.3, AttackType.DDOS: 0.9, AttackType.ZERO_DAY: 0.2, AttackType.RANSOMWARE: 0.3},
            ExpertType.ZERO_DAY_EXPERT: {AttackType.SCANNING: 0.3, AttackType.LATERAL_MOVEMENT: 0.4, AttackType.PRIVILEGE_ESCALATION: 0.4,
                                         AttackType.DATA_EXFILTRATION: 0.4, AttackType.DDOS: 0.3, AttackType.ZERO_DAY: 0.9, AttackType.RANSOMWARE: 0.5},
            ExpertType.RANSOMWARE_EXPERT: {AttackType.SCANNING: 0.3, AttackType.LATERAL_MOVEMENT: 0.4, AttackType.PRIVILEGE_ESCALATION: 0.5,
                                           AttackType.DATA_EXFILTRATION: 0.6, AttackType.DDOS: 0.2, AttackType.ZERO_DAY: 0.4, AttackType.RANSOMWARE: 0.9},
            ExpertType.HYBRID_EXPERT: {at: 0.7 for at in AttackType},
            ExpertType.ANOMALY_EXPERT: {AttackType.ZERO_DAY: 0.8, AttackType.RANSOMWARE: 0.8, **{at: 0.6 for at in AttackType if at not in [AttackType.ZERO_DAY, AttackType.RANSOMWARE]}},
            ExpertType.GENERAL_EXPERT: {at: 0.6 for at in AttackType},
        }
        return mapping.get(expert_type, {}).get(attack_type, 0.5)

    def _critical_nodes(self, top_percent: float = 0.2) -> Set[str]:
        """识别关键节点（基于重要性）"""
        sorted_nodes = sorted(self.node_importance.items(), key=lambda x: x[1], reverse=True)
        cutoff = int(len(sorted_nodes) * top_percent)
        return {node for node, _ in sorted_nodes[:cutoff]}

    def _crossover(self, parent1_nodes, parent1_indices, parent2_nodes, parent2_indices):
        """两点交叉"""
        if random.random() > self.crossover_rate:
            return (parent1_nodes.copy(), parent1_indices.copy()), (parent2_nodes.copy(), parent2_indices.copy())
        # 选择交叉点
        cx_point1 = random.randint(1, self.num_honeypots - 1)
        cx_point2 = random.randint(cx_point1, self.num_honeypots - 1)
        child1_nodes = parent1_nodes[:cx_point1] + parent2_nodes[cx_point1:cx_point2] + parent1_nodes[cx_point2:]
        child2_nodes = parent2_nodes[:cx_point1] + parent1_nodes[cx_point1:cx_point2] + parent2_nodes[cx_point2:]
        child1_indices = parent1_indices[:cx_point1] + parent2_indices[cx_point1:cx_point2] + parent1_indices[cx_point2:]
        child2_indices = parent2_indices[:cx_point1] + parent1_indices[cx_point1:cx_point2] + parent2_indices[cx_point2:]
        # 确保节点不重复
        child1_nodes = self._ensure_unique_nodes(child1_nodes)
        child2_nodes = self._ensure_unique_nodes(child2_nodes)
        return (child1_nodes, child1_indices), (child2_nodes, child2_indices)

    def _ensure_unique_nodes(self, nodes: List[str]) -> List[str]:
        """确保节点列表无重复，若重复则替换为未选中的节点"""
        seen = set()
        unique_nodes = []
        for node in nodes:
            if node not in seen:
                seen.add(node)
                unique_nodes.append(node)
            else:
                available = [n for n in self.all_nodes if n not in seen]
                if available:
                    new_node = random.choice(available)
                    seen.add(new_node)
                    unique_nodes.append(new_node)
                else:
                    unique_nodes.append(node)  # 极端情况
        while len(unique_nodes) < self.num_honeypots:
            new_node = random.choice([n for n in self.all_nodes if n not in seen])
            seen.add(new_node)
            unique_nodes.append(new_node)
        return unique_nodes

    def _mutate(self, nodes: List[str], indices: List[int]) -> Tuple[List[str], List[int]]:
        """变异操作：随机替换节点或专家类型"""
        for i in range(self.num_honeypots):
            if random.random() < self.mutation_rate:
                if random.random() < 0.5:
                    # 替换节点
                    available = [n for n in self.all_nodes if n not in nodes]
                    if available:
                        new_node = random.choice(available)
                        nodes[i] = new_node
                else:
                    # 替换专家类型
                    new_type = random.choice(range(len(self.expert_types)))
                    indices[i] = new_type
        # 再次确保节点唯一性
        nodes = self._ensure_unique_nodes(nodes)
        return nodes, indices

    def optimize(self, verbose: bool = True) -> Dict[str, ExpertType]:
        """执行遗传算法优化"""
        # 初始化种群
        population = [self._create_individual() for _ in range(self.population_size)]
        best_fitness = -np.inf
        best_individual = None
        for gen in range(self.generations):
            # 评估适应度
            fitness_scores = [self._fitness(ind[0], ind[1]) for ind in population]
            # 记录最佳
            max_idx = np.argmax(fitness_scores)
            if fitness_scores[max_idx] > best_fitness:
                best_fitness = fitness_scores[max_idx]
                best_individual = (population[max_idx][0].copy(), population[max_idx][1].copy())
            if verbose and (gen % 20 == 0 or gen == self.generations - 1):
                print(f"  第 {gen} 代: 最佳适应度 = {best_fitness:.4f}")
            # 选择（锦标赛）
            new_population = []
            for _ in range(self.population_size):
                idx1 = random.randint(0, self.population_size - 1)
                idx2 = random.randint(0, self.population_size - 1)
                if fitness_scores[idx1] > fitness_scores[idx2]:
                    parent1 = (population[idx1][0].copy(), population[idx1][1].copy())
                else:
                    parent1 = (population[idx2][0].copy(), population[idx2][1].copy())
                idx1 = random.randint(0, self.population_size - 1)
                idx2 = random.randint(0, self.population_size - 1)
                if fitness_scores[idx1] > fitness_scores[idx2]:
                    parent2 = (population[idx1][0].copy(), population[idx1][1].copy())
                else:
                    parent2 = (population[idx2][0].copy(), population[idx2][1].copy())
                # 交叉
                child1, child2 = self._crossover(parent1[0], parent1[1], parent2[0], parent2[1])
                # 变异
                child1 = self._mutate(child1[0], child1[1])
                child2 = self._mutate(child2[0], child2[1])
                new_population.extend([child1, child2])
            # 截断至种群大小
            population = new_population[:self.population_size]
        # 最终解码
        best_deployment = self._decode(best_individual[0], best_individual[1])
        if verbose:
            print(f"遗传算法优化完成，最佳适应度: {best_fitness:.4f}")
        return best_deployment


# ==================== 蜜罐部署策略函数 ====================
def create_advanced_steiner_honeypots(network: nx.Graph, num_honeypots: int = 15) -> Dict[str, ExpertType]:
    """高级斯坦纳树蜜罐部署策略"""
    honeypot_deployment = {}
    try:
        communities = list(nx.community.greedy_modularity_communities(network))
    except:
        communities = [set(network.nodes())]
    print(f"   检测到 {len(communities)} 个网络社区")
    degree_centrality = nx.degree_centrality(network)
    betweenness_centrality = nx.betweenness_centrality(network, k=min(20, network.number_of_nodes()))
    node_scores = {}
    for node in network.nodes():
        score = (degree_centrality[node] * 0.4 + betweenness_centrality[node] * 0.6)
        node_scores[node] = score
    expert_assignments = []
    for i, community in enumerate(communities):
        community_nodes = list(community)
        if len(community_nodes) < 3:
            continue
        community_scores = {node: node_scores[node] for node in community_nodes}
        top_community_nodes = sorted(community_scores.items(), key=lambda x: x[1], reverse=True)
        boundary_nodes = []
        for node in community_nodes:
            neighbors = list(network.neighbors(node))
            external_neighbors = [n for n in neighbors if n not in community]
            if len(external_neighbors) > 0:
                boundary_nodes.append(node)
        if i == 0:
            for node, _ in top_community_nodes[:2]:
                if len(expert_assignments) < num_honeypots:
                    expert_assignments.append((node, ExpertType.PRIVILEGE_EXPERT))
            for node in boundary_nodes[:1]:
                if len(expert_assignments) < num_honeypots:
                    expert_assignments.append((node, ExpertType.LATERAL_EXPERT))
        elif i == 1:
            for node, _ in top_community_nodes[:2]:
                if len(expert_assignments) < num_honeypots:
                    if network.degree(node) > 3:
                        expert_assignments.append((node, ExpertType.SCANNING_EXPERT))
                    else:
                        expert_assignments.append((node, ExpertType.DDOS_EXPERT))
        else:
            for node, _ in top_community_nodes[:1]:
                if len(expert_assignments) < num_honeypots:
                    expert_assignments.append((node, ExpertType.DATA_EXFIL_EXPERT))
            for node in boundary_nodes[:1]:
                if len(expert_assignments) < num_honeypots:
                    expert_assignments.append((node, ExpertType.ANOMALY_EXPERT))
    global_top_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
    for node, _ in global_top_nodes:
        if node not in [n for n, _ in expert_assignments] and len(expert_assignments) < num_honeypots:
            if network.degree(node) >= 4 and betweenness_centrality[node] > 0.1:
                expert_assignments.append((node, ExpertType.ZERO_DAY_EXPERT))
                break
    for node, _ in global_top_nodes:
        if node not in [n for n, _ in expert_assignments] and len(expert_assignments) < num_honeypots:
            if 3 <= network.degree(node) <= 6 and node_scores[node] > 0.3:
                expert_assignments.append((node, ExpertType.RANSOMWARE_EXPERT))
                break
    remaining_nodes = []
    for node, score in global_top_nodes:
        if node not in [n for n, _ in expert_assignments]:
            remaining_nodes.append((node, score))
    for node, _ in remaining_nodes:
        if len(expert_assignments) < num_honeypots:
            expert_assignments.append((node, ExpertType.HYBRID_EXPERT))
        else:
            break
    honeypot_deployment = dict(expert_assignments)
    print(f"   蜜罐部署完成: {len(honeypot_deployment)} 个蜜罐")
    expert_count = defaultdict(int)
    for _, expert in honeypot_deployment.items():
        expert_count[expert.value] += 1
    print("   专家分布:")
    for expert_type, count in sorted(expert_count.items()):
        print(f"     - {expert_type}: {count}个")
    return honeypot_deployment


def create_advanced_random_honeypots(network: nx.Graph, num_honeypots: int = 15) -> Dict[str, ExpertType]:
    """高级随机蜜罐部署（基线方法）"""
    all_nodes = list(network.nodes())
    degree_centrality = nx.degree_centrality(network)
    weights = [1 + degree_centrality[node] * 2 for node in all_nodes]
    selected_nodes = random.choices(all_nodes, weights=weights, k=num_honeypots)
    honeypot_deployment = {}
    expert_types = list(ExpertType)
    type_weights = [0.08, 0.08, 0.08, 0.08, 0.08, 0.05, 0.05, 0.10, 0.10, 0.30]
    for node in selected_nodes:
        expert_type = random.choices(expert_types, weights=type_weights, k=1)[0]
        honeypot_deployment[node] = expert_type
    return honeypot_deployment


def create_genetic_honeypots(network: nx.Graph, num_honeypots: int = 15,
                             population_size: int = 50, generations: int = 100,
                             random_seed: int = 42) -> Dict[str, ExpertType]:
    """使用遗传算法优化的蜜罐部署"""
    optimizer = GeneticHoneypotOptimizer(network, num_honeypots, population_size, generations,
                                         mutation_rate=0.1, crossover_rate=0.8, random_seed=random_seed)
    deployment = optimizer.optimize(verbose=True)
    print(f"   遗传算法蜜罐部署完成: {len(deployment)} 个蜜罐")
    expert_count = defaultdict(int)
    for _, expert in deployment.items():
        expert_count[expert.value] += 1
    print("   专家分布:")
    for expert_type, count in sorted(expert_count.items()):
        print(f"     - {expert_type}: {count}个")
    return deployment


# ==================== 主实验函数 ====================
def run_advanced_simulation(use_gate_routing: bool = True, use_genetic: bool = False):
    """运行高级攻击模拟实验"""
    print("=" * 60)
    print("高级版MoE SHD动态攻击模拟实验")
    print("=" * 60)

    print("\n1. 创建网络拓扑...")
    network = nx.Graph()
    for i in range(50):
        network.add_node(i,
                        type='core' if i < 5 else 'aggregation' if i < 15 else 'access',
                        security_level=random.randint(1, 5))
    for i in range(5):
        for j in range(i+1, 5):
            network.add_edge(i, j, reliability=random.uniform(0.95, 0.99), security_level=5, bandwidth=1000)
    for i in range(5, 15):
        core_connections = random.sample(range(5), 2)
        for core in core_connections:
            network.add_edge(i, core, reliability=random.uniform(0.90, 0.95), security_level=4, bandwidth=500)
        if i < 14 and random.random() < 0.5:
            network.add_edge(i, i+1, reliability=random.uniform(0.85, 0.90), security_level=3, bandwidth=100)
    for i in range(15, 50):
        agg_connections = random.sample(range(5, 15), random.randint(1, 2))
        for agg in agg_connections:
            network.add_edge(i, agg, reliability=random.uniform(0.80, 0.90), security_level=2, bandwidth=100)
        if random.random() < 0.3:
            potential_peers = range(15, 50)
            peer = random.choice(potential_peers)
            if peer != i and not network.has_edge(i, peer):
                network.add_edge(i, peer, reliability=random.uniform(0.75, 0.85), security_level=1, bandwidth=10)

    print(f"   网络类型: 层次化网络（核心-汇聚-接入）")
    print(f"   节点数: {network.number_of_nodes()}")
    print(f"   边数: {network.number_of_edges()}")
    print(f"   核心节点: 5个")
    print(f"   汇聚节点: 10个")
    print(f"   接入节点: 35个")

    print("\n2. 创建蜜罐部署...")
    if use_genetic:
        steiner_deployment = create_genetic_honeypots(network, 15, population_size=30, generations=50, random_seed=42)
    else:
        steiner_deployment = create_advanced_steiner_honeypots(network, 15)
    random_deployment = create_advanced_random_honeypots(network, 15)

    # 构建斯坦纳树信息（用于虚假响应器）
    steiner_tree = {}
    for node_id, expert_type in steiner_deployment.items():
        steiner_tree[node_id] = {'expert_type': expert_type.value, 'distance_to_real_expert': 0}
    for node_id in network.nodes():
        if node_id not in steiner_tree:
            steiner_tree[node_id] = {'expert_type': 'general', 'distance_to_real_expert': 0}

    expert_profiles = {}  # 实际可从文件加载

    print("\n3. 运行MoE SHD部署模拟（门控路由: {}）...".format("启用" if use_gate_routing else "禁用"))
    moe_simulator = AdvancedDynamicAttackSimulator(
        network_graph=network,
        honeypot_nodes=steiner_deployment,
        random_seed=42,
        use_gate_routing=use_gate_routing,
        steiner_tree=steiner_tree,
        expert_profiles=expert_profiles
    )

    moe_results = moe_simulator.run_batch_attacks(num_attacks=1000)

    # 保存攻击日志（包含虚假响应字段）
    moe_simulator.save_attack_logs("attack_logs.json")

    print("\n MoE SHD部署结果:")
    print(f"   - 总攻击次数: {moe_results['total_attacks']}")
    print(f"   - 捕获攻击次数: {moe_results['captured_attacks']}")
    print(f"   - 触碰概率: {moe_results['touch_probability']:.3f}")
    print(f"   - 平均捕获步数: {moe_results['capture_latency_mean']:.1f}")
    print(f"   - 平均攻击步数: {moe_results['average_steps_per_attack']:.1f}")
    print(f"   - 攻击成功率: {moe_results['attack_success_rate']:.3f}")
    print(f"   - 误报率: {moe_results['false_positive_rate']:.4f}")
    print(f"   - 漏报率: {moe_results['false_negative_rate']:.3f}")
    print(f"   - 早期检测率: {moe_results['early_detection_rate']:.3f}")
    print(f"   - 协同检测率: {moe_results['collaborative_detection_rate']:.3f}")
    print(f"   - 攻击规避率: {moe_results['evasion_rate']:.3f}")
    print(f"   - 精确率: {moe_results['precision']:.3f}")
    print(f"   - 召回率: {moe_results['recall']:.3f}")
    print(f"   - F1分数: {moe_results['f1_score']:.3f}")
    if use_gate_routing:
        print(f"   - 门控路由调用次数: {moe_results['gate_routing_stats']['routing_calls']}")
        print(f"   - 路由专家分布: {dict(moe_results['gate_routing_stats']['routing_expert_distribution'])}")

    print("\n4. 运行基线部署模拟...")
    baseline_simulator = AdvancedDynamicAttackSimulator(
        network_graph=network,
        honeypot_nodes=random_deployment,
        random_seed=42,
        use_gate_routing=False,
        steiner_tree={},
        expert_profiles={}
    )
    baseline_results = baseline_simulator.run_batch_attacks(num_attacks=500)

    print("\n 基线部署结果:")
    print(f"   - 触碰概率: {baseline_results['touch_probability']:.3f}")
    print(f"   - 误报率: {baseline_results['false_positive_rate']:.4f}")
    print(f"   - 漏报率: {baseline_results['false_negative_rate']:.3f}")
    print(f"   - 精确率: {baseline_results['precision']:.3f}")
    print(f"   - 召回率: {baseline_results['recall']:.3f}")
    print(f"   - F1分数: {baseline_results['f1_score']:.3f}")

    print("\n5. 对比分析:")
    improvement = {
        'touch_probability': moe_results['touch_probability'] - baseline_results['touch_probability'],
        'false_positive_rate': baseline_results['false_positive_rate'] - moe_results['false_positive_rate'],
        'false_negative_rate': baseline_results['false_negative_rate'] - moe_results['false_negative_rate'],
        'precision': moe_results['precision'] - baseline_results['precision'],
        'recall': moe_results['recall'] - baseline_results['recall'],
        'f1_score': moe_results['f1_score'] - baseline_results['f1_score'],
        'attack_success_rate': baseline_results['attack_success_rate'] - moe_results['attack_success_rate']
    }
    print(f"   - 触碰概率提升: {improvement['touch_probability']:+.3f}")
    print(f"   - 误报率降低: {improvement['false_positive_rate']:+.4f}")
    print(f"   - 漏报率降低: {improvement['false_negative_rate']:+.3f}")
    print(f"   - 精确率提升: {improvement['precision']:+.3f}")
    print(f"   - 召回率提升: {improvement['recall']:+.3f}")
    print(f"   - F1分数提升: {improvement['f1_score']:+.3f}")
    print(f"   - 攻击成功率降低: {improvement['attack_success_rate']:+.3f} (防御效果)")

    print("\n6. 攻击类型分析:")
    total_attacks = moe_results['total_attacks']
    for attack_type, count in sorted(moe_results['attack_type_distribution'].items()):
        percentage = count / total_attacks * 100 if total_attacks > 0 else 0
        print(f"   - {attack_type}: {count}次 ({percentage:.1f}%)")

    print("\n7. 攻击者类型分析:")
    for attacker_type, count in sorted(moe_results['attacker_type_distribution'].items()):
        percentage = count / total_attacks * 100 if total_attacks > 0 else 0
        print(f"   - {attacker_type}: {count}次 ({percentage:.1f}%)")

    print("\n8. 专家性能详细分析:")
    total_detections = moe_results['captured_attacks']
    expert_perf_items = sorted(
        moe_results['expert_performance'].items(),
        key=lambda x: x[1]['detection_counts'],
        reverse=True
    )
    print("   Top 5 专家:")
    for i, (node_id, perf) in enumerate(expert_perf_items[:5]):
        if perf['detection_counts'] > 0:
            detection_rate = perf['detection_counts'] / total_detections if total_detections > 0 else 0
            print(f"   {i+1}. 节点{node_id} ({perf['expert_type']}):")
            print(f"       检测次数: {perf['detection_counts']}, 占比: {detection_rate:.2f}")
            print(f"       精确率: {perf['true_positives'] / max(1, perf['true_positives'] + perf['false_positives']):.2f}")
            print(f"       TP/FP/FN: {perf['true_positives']}/{perf['false_positives']}/{perf['false_negatives']}")
            print(f"       平均置信度: {perf['avg_confidence']:.2f}")
            print(f"       上下文感知率: {perf['context_aware_rate']:.2f}")
            if perf['attack_type_detections']:
                print(f"       攻击类型检测分布: {dict(perf['attack_type_detections'])}")

    return {
        'network': network,
        'steiner_deployment': steiner_deployment,
        'random_deployment': random_deployment,
        'moe_results': moe_results,
        'baseline_results': baseline_results,
        'improvement': improvement
    }


def validate_advanced_system(results: Dict[str, Any]):
    """验证高级MoE SHD系统的有效性"""
    print("\n" + "=" * 60)
    print("高级MoE SHD系统有效性验证")
    print("=" * 60)

    moe_results = results['moe_results']
    improvement = results['improvement']

    validation_results = {
        'touch_probability': False,
        'false_positive_rate': False,
        'false_negative_rate': False,
        'early_detection': False,
        'collaborative_detection': False,
        'expert_specialization': False,
        'overall_effectiveness': False,
        'gate_routing': False
    }

    print("\n1. 蜜罐诱捕有效性验证:")
    if moe_results['touch_probability'] > 0.35:
        print(f"    通过 - MoE SHD触碰概率良好 ({moe_results['touch_probability']:.3f})")
        validation_results['touch_probability'] = True
    elif moe_results['touch_probability'] > 0.25:
        print(f"     警告 - 触碰概率一般 ({moe_results['touch_probability']:.3f})")
    else:
        print(f"    失败 - 触碰概率偏低 ({moe_results['touch_probability']:.3f})")
    if improvement['touch_probability'] > 0.15:
        print(f"    通过 - 比基线显著提升 (+{improvement['touch_probability']:.3f})")
        validation_results['touch_probability'] = True
    else:
        print(f"     警告 - 提升不明显 (+{improvement['touch_probability']:.3f})")

    print("\n2. 误报率优化验证:")
    if moe_results['false_positive_rate'] < 0.02:
        print(f"    优秀 - 极低误报率 ({moe_results['false_positive_rate']:.4f})")
        validation_results['false_positive_rate'] = True
    elif moe_results['false_positive_rate'] < 0.05:
        print(f"    通过 - 低误报率 ({moe_results['false_positive_rate']:.4f})")
        validation_results['false_positive_rate'] = True
    else:
        print(f"     警告 - 误报率偏高 ({moe_results['false_positive_rate']:.4f})")

    print("\n3. 漏报率优化验证:")
    if moe_results['false_negative_rate'] < 0.15:
        print(f"    优秀 - 低漏报率 ({moe_results['false_negative_rate']:.3f})")
        validation_results['false_negative_rate'] = True
    elif moe_results['false_negative_rate'] < 0.25:
        print(f"    通过 - 合理漏报率 ({moe_results['false_negative_rate']:.3f})")
        validation_results['false_negative_rate'] = True
    else:
        print(f"    失败 - 漏报率偏高 ({moe_results['false_negative_rate']:.3f})")
    if improvement['false_negative_rate'] > 0:
        print(f"    通过 - 漏报率比基线降低 (+{improvement['false_negative_rate']:.3f})")
        validation_results['false_negative_rate'] = True

    print("\n4. 早期检测能力验证:")
    if moe_results['early_detection_rate'] > 0.3:
        print(f"    优秀 - 早期检测能力强 ({moe_results['early_detection_rate']:.3f})")
        validation_results['early_detection'] = True
    elif moe_results['early_detection_rate'] > 0.15:
        print(f"    通过 - 具备早期检测能力 ({moe_results['early_detection_rate']:.3f})")
        validation_results['early_detection'] = True
    else:
        print(f"     警告 - 早期检测能力弱 ({moe_results['early_detection_rate']:.3f})")

    print("\n5. 协同检测能力验证:")
    if moe_results['collaborative_detection_rate'] > 0.2:
        print(f"    优秀 - 协同检测效果好 ({moe_results['collaborative_detection_rate']:.3f})")
        validation_results['collaborative_detection'] = True
    elif moe_results['collaborative_detection_rate'] > 0.1:
        print(f"    通过 - 具备协同检测能力 ({moe_results['collaborative_detection_rate']:.3f})")
        validation_results['collaborative_detection'] = True
    else:
        print(f"     警告 - 协同检测能力弱 ({moe_results['collaborative_detection_rate']:.3f})")

    print("\n6. MoE专家专业化验证:")
    expert_specialization_score = 0
    total_experts = 0
    for node_id, perf in moe_results['expert_performance'].items():
        if perf['detection_counts'] > 0:
            total_experts += 1
            expert_type = perf['expert_type']
            attack_detections = perf['attack_type_detections']
            if expert_type == 'scanning_expert' and 'scanning' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'lateral_expert' and 'lateral' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'privilege_expert' and 'priv' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'data_exfil_expert' and 'exfil' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'ddos_expert' and 'ddos' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'zero_day_expert' and 'zero_day' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'ransomware_expert' and 'ransomware' in attack_detections:
                expert_specialization_score += 1
            elif expert_type == 'anomaly_expert' and ('zero_day' in attack_detections or 'ransomware' in attack_detections):
                expert_specialization_score += 1
            elif expert_type in ['hybrid_expert', 'general_expert'] and len(attack_detections) > 0:
                expert_specialization_score += 0.5
    specialization_rate = expert_specialization_score / max(1, total_experts)
    if specialization_rate > 0.7:
        print(f"    优秀 - 专家专业化程度高 ({specialization_rate:.2f})")
        validation_results['expert_specialization'] = True
    elif specialization_rate > 0.5:
        print(f"    通过 - 专家专业化程度合理 ({specialization_rate:.2f})")
        validation_results['expert_specialization'] = True
    else:
        print(f"    失败 - 专家专业化程度低 ({specialization_rate:.2f})")

    print("\n7. MoE门控路由验证:")
    gate_stats = moe_results.get('gate_routing_stats', {})
    if gate_stats.get('routing_calls', 0) > 0:
        print(f"    门控路由已启用，共进行 {gate_stats['routing_calls']} 次路由决策")
        unique_experts = len(gate_stats.get('routing_expert_distribution', {}))
        if unique_experts > 1:
            print(f"    路由专家分布多样（{unique_experts} 种类型）")
            validation_results['gate_routing'] = True
        else:
            print(f"     路由专家分布单一，可能未充分利用专家多样性")
            validation_results['gate_routing'] = False
    else:
        print(f"     门控路由未启用或无路由记录")
        validation_results['gate_routing'] = False

    print("\n8. 总体有效性评估:")
    passed_tests = sum(validation_results.values())
    total_tests = len(validation_results)
    if passed_tests >= total_tests - 1:
        print(f"    MoE SHD系统总体优秀 ({passed_tests}/{total_tests} 项通过)")
        validation_results['overall_effectiveness'] = True
    elif passed_tests >= total_tests * 0.7:
        print(f"    MoE SHD系统总体有效 ({passed_tests}/{total_tests} 项通过)")
        validation_results['overall_effectiveness'] = True
    else:
        print(f"    MoE SHD系统效果不佳 ({passed_tests}/{total_tests} 项通过)")

    return validation_results


def generate_comprehensive_report(results: Dict[str, Any], validation: Dict[str, bool]):
    """生成综合报告"""
    print("\n" + "=" * 60)
    print("高级MoE SHD系统综合性能报告")
    print("=" * 60)

    moe_results = results['moe_results']
    baseline_results = results['baseline_results']
    improvement = results['improvement']

    print("\n 性能指标汇总:")
    print("   Metric                    | MoE SHD     | Baseline    | Improvement")
    print("   --------------------------|-------------|-------------|-------------")
    metrics = [
        ("触碰概率", moe_results['touch_probability'], baseline_results['touch_probability'], improvement['touch_probability']),
        ("误报率", moe_results['false_positive_rate'], baseline_results['false_positive_rate'], improvement['false_positive_rate']),
        ("漏报率", moe_results['false_negative_rate'], baseline_results['false_negative_rate'], improvement['false_negative_rate']),
        ("精确率", moe_results['precision'], baseline_results['precision'], improvement['precision']),
        ("召回率", moe_results['recall'], baseline_results['recall'], improvement['recall']),
        ("F1分数", moe_results['f1_score'], baseline_results['f1_score'], improvement['f1_score']),
        ("攻击成功率", moe_results['attack_success_rate'], baseline_results['attack_success_rate'], improvement['attack_success_rate'])
    ]
    for name, moe_val, base_val, imp_val in metrics:
        if name == "攻击成功率":
            imp_display = f"{imp_val:+.3f} (防御效果)"
        else:
            imp_display = f"{imp_val:+.3f}"
        print(f"   {name:<25} | {moe_val:^11.3f} | {base_val:^11.3f} | {imp_display}")

    print("\n 高级能力评估:")
    advanced_metrics = [
        ("早期检测率", moe_results['early_detection_rate'], ">0.2"),
        ("协同检测率", moe_results['collaborative_detection_rate'], ">0.15"),
        ("攻击规避率", moe_results['evasion_rate'], "<0.3"),
        ("平均检测置信度", np.mean(list(moe_results['avg_confidence_scores'].values())) if moe_results['avg_confidence_scores'] else 0, ">0.7"),
        ("门控路由调用次数", moe_results['gate_routing_stats'].get('routing_calls', 0), ">0")
    ]
    for name, value, threshold in advanced_metrics:
        if isinstance(threshold, str):
            if threshold.startswith(">"):
                target = float(threshold[1:])
                status = "" if value > target else ""
            elif threshold.startswith("<"):
                target = float(threshold[1:])
                status = "" if value < target else ""
            else:
                target = float(threshold)
                status = "" if value >= target else ""
        else:
            status = "" if value >= threshold else ""
        print(f"   {status} {name}: {value:.3f} (目标: {threshold})")

    print("\n 验证结果总结:")
    passed = sum(validation.values())
    total = len(validation)
    print(f"   通过测试: {passed}/{total} ({passed / total * 100:.1f}%)")
    if validation['overall_effectiveness']:
        print("    总体评估: MoE SHD系统部署成功，显著优于基线方法")
    else:
        print("     总体评估: MoE SHD系统需要进一步优化")

    print("\n 建议和改进方向:")
    if moe_results['false_negative_rate'] > 0.2:
        print("   - 考虑增加异常检测专家或混合专家的比例")
    if moe_results['early_detection_rate'] < 0.2:
        print("   - 在网络入口处部署更多扫描专家和异常检测专家")
    if moe_results['collaborative_detection_rate'] < 0.15:
        print("   - 加强蜜罐间的信息共享和协同检测机制")
    if improvement['touch_probability'] < 0.15:
        print("   - 优化蜜罐部署策略，考虑更精细的社区检测")
    if moe_results['gate_routing_stats'].get('routing_calls', 0) == 0:
        print("   - 门控路由未启用，建议启用以提升专家利用率")
    print("   - 定期更新专家检测模型，适应新型攻击模式")
    print("   - 实施动态蜜罐迁移策略，应对攻击者的规避行为")


def save_results(results: Dict[str, Any], validation: Dict[str, bool]):
    """保存结果到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"advanced_moe_simulation_results_{timestamp}.json"
    save_data = {
        'timestamp': timestamp,
        'moe_results': results['moe_results'],
        'baseline_results': results['baseline_results'],
        'improvement': results['improvement'],
        'validation': validation,
        'network_info': {
            'num_nodes': results['network'].number_of_nodes(),
            'num_edges': results['network'].number_of_edges(),
            'num_honeypots_moe': len(results['steiner_deployment']),
            'num_honeypots_baseline': len(results['random_deployment'])
        }
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    print(f"\n 结果已保存至: {filename}")
    return filename


if __name__ == "__main__":
    print("开始高级版MoE SHD攻击模拟实验...\n")
    try:
        # 可选：启用门控路由和遗传算法优化
        results = run_advanced_simulation(use_gate_routing=True, use_genetic=False)
        validation = validate_advanced_system(results)
        generate_comprehensive_report(results, validation)
        filename = save_results(results, validation)
        print("\n" + "=" * 60)
        print(" 实验完成总结")
        print("=" * 60)
        print(f"\n 高级MoE SHD系统模拟实验成功完成")
        print(f" 主要成果:")
        print(f"   - MoE SHD触碰概率: {results['moe_results']['touch_probability']:.3f}")
        print(f"   - 比基线提升: {results['improvement']['touch_probability']:+.3f}")
        print(f"   - 误报率: {results['moe_results']['false_positive_rate']:.4f}")
        print(f"   - 漏报率: {results['moe_results']['false_negative_rate']:.3f}")
        print(f"   - F1分数: {results['moe_results']['f1_score']:.3f}")
        print(f"\n 系统优势:")
        print(f"   - 协同检测能力: {results['moe_results']['collaborative_detection_rate']:.3f}")
        print(f"   - 早期检测能力: {results['moe_results']['early_detection_rate']:.3f}")
        print(f"   - 上下文感知检测: 已实现")
        print(f"   - 自适应学习: 已实现")
        if results['moe_results']['gate_routing_stats'].get('routing_calls', 0) > 0:
            print(f"   - MoE门控路由: 已启用（{results['moe_results']['gate_routing_stats']['routing_calls']}次路由）")
        else:
            print(f"   - MoE门控路由: 未启用")
        print(f"\n 详细结果已保存至: {filename}")
    except Exception as e:
        print(f"\n 实验执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()