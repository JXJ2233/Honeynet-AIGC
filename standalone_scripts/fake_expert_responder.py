'''# src/security/fake_expert_responder.py

import numpy as np
import random
from typing import Dict, Any, List

class FakeExpertResponder:
    """
    虚假专家响应器，用于在蜜罐节点被门控网络路由时生成逼真的响应。
    通过模拟真实专家的响应时延分布、梯度掩码等特征，增强欺骗性。
    """

    def __init__(self, steiner_tree: Dict, expert_profiles: Dict[str, Any]):
        """
        初始化虚假专家响应器。
        :param steiner_tree: 斯坦纳树结构，包含节点角色和拓扑关系
        :param expert_profiles: 从历史数据中提取的真实专家行为档案
        """
        self.tree = steiner_tree
        self.profiles = expert_profiles

    def generate_fake_response(self, request_type: str, target_node_id: str,
                               network_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成虚假响应。
        :param request_type: 攻击类型，如 'scanning', 'lateral' 等
        :param target_node_id: 当前蜜罐节点ID
        :param network_state: 当前网络态势（时延、负载等）
        :return: 伪造的响应数据包
        """
        # 1. 获取节点在斯坦纳树中的角色（专家类型）
        role = self.tree.get(target_node_id, {}).get('expert_type', 'general')
        # 2. 从档案中获取对应角色的行为模式
        pattern = self.profiles.get(role, self._default_pattern())
        # 3. 根据请求类型和网络状态微调响应
        pattern = self._adapt_pattern(pattern, request_type, network_state)

        fake_resp = {
            "response_time": self._simulate_response_time(pattern),
            "gradient_mask": self._simulate_gradient_mask(pattern),
            "status": 200,
            "payload": self._generate_payload(request_type, role)
        }
        return fake_resp

    def _simulate_response_time(self, pattern: Dict) -> float:
        """模拟响应时延，使用真实专家的时延分布（正态分布）"""
        mean = pattern.get('mean_latency', 0.05)      # 默认50ms
        std = pattern.get('latency_std', 0.01)         # 默认10ms
        return max(0.01, random.gauss(mean, std))

    def _simulate_gradient_mask(self, pattern: Dict) -> np.ndarray:
        """模拟梯度掩码，生成与真实专家激活模式相似的稀疏张量"""
        mask_shape = pattern.get('mask_shape', (100,))
        sparsity = pattern.get('sparsity', 0.9)
        mask = np.random.rand(*mask_shape)
        mask[mask < sparsity] = 0
        return mask

    def _generate_payload(self, request_type: str, role: str) -> str:
        """生成看起来合理的响应内容"""
        if request_type == 'scanning':
            return "Open ports: 22, 80, 443 (simulated)"
        elif request_type == 'lateral':
            return "SMB share accessible (simulated)"
        else:
            return f"{role} response: ok"

    def _adapt_pattern(self, pattern: Dict, request_type: str,
                       network_state: Dict) -> Dict:
        """根据当前网络状态动态调整模式，使响应更真实"""
        # 示例：如果网络拥塞，增加响应时延
        if network_state.get('congestion_level', 0) > 0.7:
            pattern['mean_latency'] *= 1.5
        return pattern

    def _default_pattern(self) -> Dict:
        """默认模式，用于未定义的专家类型"""
        return {
            'mean_latency': 0.05,
            'latency_std': 0.01,
            'mask_shape': (100,),
            'sparsity': 0.9
        }'''# src/security/fake_expert_responder.py

# src/security/fake_expert_responder.py

import numpy as np
import random
from typing import Dict, Any, List, Optional
from src.security.fake_expert_responder import FakeExpertResponder

class FakeExpertResponder:
    """
    虚假专家响应器，用于蜜罐节点被攻击时模拟真实专家行为。
    兼容原有接口，同时新增基于攻击上下文的响应生成。
    """

    # 原有接口保留
    def __init__(self, steiner_tree: Dict, expert_profiles: Dict[str, Any],
                 expert_type: str = None,
                 baseline_latency_mean: float = None,
                 baseline_latency_std: float = None,
                 gradient_profile: List[float] = None,
                 node_id: str = None):
        """
        初始化虚假专家响应器。
        兼容旧调用方式：只传 steiner_tree, expert_profiles。
        新调用方式可额外传入专家专属参数。

        :param steiner_tree: 斯坦纳树结构，包含节点角色和拓扑关系
        :param expert_profiles: 从历史数据中提取的真实专家行为档案
        :param expert_type: 当前节点专家类型（可选，若不提供则从树中获取）
        :param baseline_latency_mean: 基础时延均值（可选，若不提供则从档案中获取）
        :param baseline_latency_std: 基础时延标准差（可选）
        :param gradient_profile: 梯度掩码稀疏度列表（可选）
        :param node_id: 当前蜜罐节点ID（可选）
        """
        # 原有属性
        self.tree = steiner_tree
        self.profiles = expert_profiles

        # 新属性，从参数或档案中推导
        self.expert_type = expert_type
        self.node_id = node_id

        # 如果未提供专家类型，且 node_id 存在，则从树中获取
        if self.expert_type is None and self.node_id is not None:
            self.expert_type = self.tree.get(self.node_id, {}).get('expert_type', 'general')

        # 获取档案中的模式（用于回退）
        pattern = self.profiles.get(self.expert_type or 'general', self._default_pattern())

        # 设置基线时延
        if baseline_latency_mean is None:
            self.baseline_latency_mean = pattern.get('mean_latency', 0.05)
        else:
            self.baseline_latency_mean = baseline_latency_mean

        if baseline_latency_std is None:
            self.baseline_latency_std = pattern.get('latency_std', 0.01)
        else:
            self.baseline_latency_std = baseline_latency_std

        # 设置梯度档案
        if gradient_profile is None:
            self.gradient_profile = pattern.get('gradient_profile', [0.9, 0.7, 0.5])
        else:
            self.gradient_profile = gradient_profile

        # 响应模板库（可扩展）
        self.response_templates = {
            'scanning_detector': {
                'scanning': "Open ports: 22 (ssh), 80 (http), 443 (https) - simulated",
                'default': "Port scan detected. System information: Linux 5.4, kernel hardened."
            },
            'lateral_detector': {
                'lateral': "SMB share \\\\192.168.1.100\\shared accessible (simulated)",
                'default': "NetBIOS session established. Share enumeration completed."
            },
            'general_detector': {
                'default': "Service response: ok"
            },
            'general': {
                'default': "Service response: ok"
            }
        }

    # ==================== 原有方法（完全保留） ====================

    def generate_fake_response(self, request_type: str, target_node_id: str,
                               network_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        原有接口：生成虚假响应（基于请求类型和网络状态）。
        :param request_type: 攻击类型，如 'scanning', 'lateral' 等
        :param target_node_id: 当前蜜罐节点ID
        :param network_state: 当前网络态势（时延、负载等）
        :return: 伪造的响应数据包
        """
        # 1. 获取节点在斯坦纳树中的角色（专家类型）
        role = self.tree.get(target_node_id, {}).get('expert_type', 'general')
        # 2. 从档案中获取对应角色的行为模式
        pattern = self.profiles.get(role, self._default_pattern())
        # 3. 根据请求类型和网络状态微调响应
        pattern = self._adapt_pattern(pattern, request_type, network_state)

        fake_resp = {
            "response_time": self._simulate_response_time(pattern),
            "gradient_mask": self._simulate_gradient_mask(pattern),
            "status": 200,
            "payload": self._generate_payload(request_type, role)
        }
        return fake_resp

    def _simulate_response_time(self, pattern: Dict) -> float:
        """模拟响应时延，使用真实专家的时延分布（正态分布）"""
        mean = pattern.get('mean_latency', 0.05)
        std = pattern.get('latency_std', 0.01)
        return max(0.01, random.gauss(mean, std))

    def _simulate_gradient_mask(self, pattern: Dict) -> np.ndarray:
        """模拟梯度掩码，生成与真实专家激活模式相似的稀疏张量"""
        mask_shape = pattern.get('mask_shape', (100,))
        sparsity = pattern.get('sparsity', 0.9)
        mask = np.random.rand(*mask_shape)
        mask[mask < sparsity] = 0
        return mask

    def _generate_payload(self, request_type: str, role: str) -> str:
        """生成看起来合理的响应内容"""
        if request_type == 'scanning':
            return "Open ports: 22, 80, 443 (simulated)"
        elif request_type == 'lateral':
            return "SMB share accessible (simulated)"
        else:
            return f"{role} response: ok"

    def _adapt_pattern(self, pattern: Dict, request_type: str,
                       network_state: Dict) -> Dict:
        """根据当前网络状态动态调整模式，使响应更真实"""
        if network_state.get('congestion_level', 0) > 0.7:
            pattern['mean_latency'] *= 1.5
        return pattern

    def _default_pattern(self) -> Dict:
        """默认模式，用于未定义的专家类型"""
        return {
            'mean_latency': 0.05,
            'latency_std': 0.01,
            'mask_shape': (100,),
            'sparsity': 0.9,
            'gradient_profile': [0.9, 0.7, 0.5]
        }

    # ==================== 新增方法（基于攻击上下文） ====================

    def respond(self, attack_context: Dict[str, Any], expert_type: Optional[str] = None) -> Dict[str, Any]:
        """
        新接口：根据攻击上下文和门控路由选择的专家类型生成虚假响应。
        :param attack_context: 包含攻击信息的字典，如：
            {
                'type': 'scanning',           # 攻击类型
                'stage': 0,                   # 攻击阶段索引 (0~2)
                'source_ip': '10.0.0.1',
                'target_port': 80,
                'network_congestion': 0.2
            }
        :param expert_type: 门控路由选择的专家类型（若为 None 则使用实例默认专家类型）
        :return: 包含时延、响应内容和梯度掩码的字典
        """
        # 确定本次响应使用的专家类型
        used_expert_type = expert_type if expert_type is not None else self.expert_type

        # 1. 计算时延（可能根据到真实专家的距离进行调整）
        latency = self._compute_latency(attack_context)

        # 2. 根据攻击类型和专家类型生成响应内容
        response = self._generate_response(attack_context, used_expert_type)

        # 3. 根据攻击阶段生成梯度掩码
        gradient_mask = self._generate_gradient_mask(attack_context)

        return {
            'latency': latency,
            'response': response,
            'gradient_mask': gradient_mask
        }

    def _compute_latency(self, attack_context: Dict) -> float:
        """计算响应时延：基础分布 + 拓扑距离调整 + 网络拥塞影响"""
        # 基础时延：正态分布
        latency = random.gauss(self.baseline_latency_mean, self.baseline_latency_std)
        latency = max(0.005, latency)  # 最小5ms

        # 如果提供了节点ID和树结构，根据到真实专家的跳数增加时延
        if self.node_id and self.tree:
            distance = self._distance_to_real_expert()
            # 每跳增加 5ms 时延
            latency += distance * 0.005

        # 攻击上下文可能携带网络拥塞信息
        congestion = attack_context.get('network_congestion', 0.0)
        latency *= (1 + congestion)

        return round(latency, 6)

    def _distance_to_real_expert(self) -> int:
        """计算当前蜜罐节点到最近真实专家的最短路径跳数（基于斯坦纳树）"""
        node_info = self.tree.get(self.node_id, {})
        return node_info.get('distance_to_real_expert', 0)

    def _generate_response(self, attack_context: Dict, expert_type: str) -> str:
        """根据攻击类型和专家类型生成文本响应"""
        attack_type = attack_context.get('type', 'default')
        templates = self.response_templates.get(expert_type, self.response_templates['general_detector'])
        return templates.get(attack_type, templates.get('default', 'Response ok'))

    def _generate_gradient_mask(self, attack_context: Dict) -> np.ndarray:
        """
        生成模拟梯度掩码。根据攻击阶段从 gradient_profile 中选择稀疏度，
        构造稀疏张量以迷惑攻击者。
        """
        stage = attack_context.get('stage', 0)
        # 确保 stage 在合法范围
        stage = min(max(stage, 0), len(self.gradient_profile) - 1)
        sparsity = self.gradient_profile[stage]

        # 模拟梯度形状（可配置，这里固定为100维向量）
        mask_shape = (100,)
        mask = np.random.rand(*mask_shape)
        mask[mask < sparsity] = 0.0
        # 非零部分模拟梯度幅值（正态分布）
        mask[mask > 0] = np.random.normal(0.0, 0.1, size=np.sum(mask > 0))

        return mask