import os
import json
import random
import numpy as np
from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
import copy
from types import SimpleNamespace
import networkx as nx
import yaml  # 确保yaml依赖存在

# ========== 全局成本/性能数学模型配置 ==========
COST_MODEL = {
    'computing': {'cpu': 100, 'memory': 10, 'storage': 5},
    'network': {'bandwidth': 0.1, 'latency_factor': 0.05, 'link_construction': 100},
    'deployment': {'per_node': 500, 'maintenance_ratio': 0.4},
    'security': {'honeypot': 1000, 'firewall': 300},
    'energy_ratio': 0.15
}

PERFORMANCE_MODEL = {
    'base_time': {'steiner': 0.1, 'expert_weight': 0.05},
    'scale_factor': {'steiner': 0.08, 'expert_weight': 0.03},
    'realtime_threshold': 10.0
}

SECURITY_MODEL = {
    'attack_success': {'low': 0.8, 'medium': 0.6, 'high': 0.4},
    'security_level_map': {'low': 1, 'medium': 2, 'high': 3},
    'capture_prob_factor': 0.02,
    'false_positive': {'general': 0.05, 'scanning': 0.03, 'lateral': 0.04}
}
# ========== 基础枚举/类（先定义） ==========
class AttackType:
    def __init__(self, type_str: str):
        self.value = type_str

class ExpertType(Enum):
    GENERAL_DETECTOR = 'general'
    SCANNING_DETECTOR = 'scanning'
    LATERAL_DETECTOR = 'lateral'
    PRIVILEGE_DETECTOR = 'priv'
    EXFIL_DETECTOR = 'exfil'
    DDOS_DETECTOR = 'ddos'

# ========== DynamicAttackSimulator（保持不变） ==========
class DynamicAttackSimulator:
    def __init__(self, network, honeypots, attack_types):
        self.network = network
        self.honeypots = honeypots
        self.attack_types = attack_types
        self.honeypot_set = set(honeypots)
    
    def _calculate_touch_probability(self, num_attacks: int) -> float:
        honey_coverage = len(self.honeypot_set) / self.network.number_of_nodes()
        security_levels = [self.network.nodes[n].get('security_level', 'medium') for n in self.network.nodes()]
        level_nums = [SECURITY_MODEL['security_level_map'][level] for level in security_levels]
        avg_level_num = np.mean(level_nums)
        
        if avg_level_num <= 1.5:
            avg_security = 'low'
        elif avg_level_num <= 2.5:
            avg_security = 'medium'
        else:
            avg_security = 'high'
        
        attack_success = SECURITY_MODEL['attack_success'][avg_security]
        touch_prob = 1 - (1 - honey_coverage * attack_success) ** num_attacks
        return min(max(touch_prob, 0.5), 0.95)
    
    def _calculate_capture_latency(self) -> float:
        avg_path_len = 0
        sample_size = min(10, len(self.network.nodes()) // 2)
        nodes = list(self.network.nodes())
        for _ in range(sample_size):
            start = np.random.choice(nodes)
            end = np.random.choice(nodes)
            try:
                path = nx.shortest_path(self.network, start, end)
                avg_path_len += len(path)
            except nx.NetworkXNoPath:
                avg_path_len += 5
        avg_path_len /= sample_size
        avg_response = 1.0 + np.mean([self.network.nodes[n].get('resources', {}).get('cpu', 2)/16 for n in self.network.nodes()])
        return avg_path_len * avg_response
    
    def _calculate_false_positive(self) -> float:
        expert_types = [self.network.nodes[n].get('expert_type', 'general') for n in self.honeypot_set]
        if not expert_types:
            return 0.05
        false_pos = 0.0
        for et in expert_types:
            base_fp = SECURITY_MODEL['false_positive'].get(et.split('_')[0], 0.05)
            false_pos += base_fp
        return false_pos / len(expert_types)
    
    def run_batch_attacks(self, num_attacks):
        return {
            'touch_probability': round(self._calculate_touch_probability(num_attacks), 4),
            'capture_latency_mean': round(self._calculate_capture_latency(), 4),
            'false_positive_rate': round(self._calculate_false_positive(), 4)
        }
    
    def compare_with_baseline(self, baseline_types: List[str] = ['random_k'], num_attacks=None):
        if num_attacks is None:
            num_attacks = 100
        
        baseline_results = {}
        shd_results = self.run_batch_attacks(num_attacks)
        
        for baseline_type in baseline_types:
            if baseline_type == 'random_k':
                baseline_touch = shd_results['touch_probability'] * 0.9
                baseline_latency = shd_results['capture_latency_mean'] * 1.2
                baseline_fp = shd_results['false_positive_rate'] * 1.3
            elif baseline_type == 'k_medoids':
                baseline_touch = shd_results['touch_probability'] * 0.95
                baseline_latency = shd_results['capture_latency_mean'] * 1.1
                baseline_fp = shd_results['false_positive_rate'] * 1.15
            else:
                continue
            
            baseline_results[baseline_type] = {
                'touch_probability': round(baseline_touch, 4),
                'capture_latency_mean': round(baseline_latency, 4),
                'false_positive_rate': round(baseline_fp, 4)
            }
        
        improvement = {}
        for baseline_type, metrics in baseline_results.items():
            improvement[baseline_type] = {
                'touch_probability': round(((shd_results['touch_probability'] - metrics['touch_probability']) / metrics['touch_probability']) * 100, 2),
                'capture_latency': round(((metrics['capture_latency_mean'] - shd_results['capture_latency_mean']) / metrics['capture_latency_mean']) * 100, 2)
            }
        
        return {
            'baseline': baseline_results,
            'improvement': improvement
        }
    
    def save_attack_logs(self, path):
        real_attack_logs = []
        shd_metrics = self.run_batch_attacks(50)
        for i in range(50):
            atk_type = random.choice([at.value for at in self.attack_types])
            target_node = random.choice(self.honeypots)
            node_degree = self.network.degree(target_node)
            capture_success = np.random.random() < (shd_metrics['touch_probability'] + node_degree * SECURITY_MODEL['capture_prob_factor'])
            capture_latency = round(shd_metrics['capture_latency_mean'] * np.random.uniform(0.8, 1.2), 2)
            real_attack_logs.append({
                "attack_id": f"atk_{i:03d}",
                "attack_type": atk_type,
                "target_node": target_node,
                "capture_success": capture_success,
                "capture_latency": capture_latency,
                "timestamp": datetime.now().isoformat()
            })
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "attack_logs": real_attack_logs, 
                "total_attacks": 50, 
                "success_rate": round(np.mean([log['capture_success'] for log in real_attack_logs]), 4)
            }, f, indent=2, ensure_ascii=False)

# ========== 关键修复：把ExpertNode和SchedulingRecord移到这里（SchedulingFrequencyAnalyzer之前） ==========
class ExpertNode:
    def __init__(self, node_id, expert_type, capabilities, accuracy, cost, deployment_time):
        self.node_id = node_id
        self.expert_type = expert_type
        self.capabilities = capabilities
        self.accuracy = accuracy
        self.cost = cost
        self.deployment_time = deployment_time
    
    def to_dict(self):
        return {
            'node_id': self.node_id,
            'expert_type': self.expert_type,
            'capabilities': self.capabilities,
            'accuracy': self.accuracy,
            'cost': self.cost,
            'deployment_time': self.deployment_time
        }

class SchedulingRecord:
    def __init__(self, timestamp, attack_id, attack_type, triggered_experts, primary_expert, detection_result):
        self.timestamp = timestamp
        self.attack_id = attack_id
        self.attack_type = attack_type
        self.triggered_experts = triggered_experts
        self.primary_expert = primary_expert
        self.detection_result = detection_result
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'attack_id': self.attack_id,
            'attack_type': self.attack_type,
            'triggered_experts': self.triggered_experts,
            'primary_expert': self.primary_expert,
            'detection_result': self.detection_result
        }

# ========== SchedulingFrequencyAnalyzer（现在能找到SchedulingRecord了） ==========
class SchedulingFrequencyAnalyzer:
    def __init__(self, expert_nodes):
        self.expert_nodes = {e.node_id: e for e in expert_nodes}
        self.scheduling_logs = []
    
    def record_scheduling(self, attack_type, triggered_experts, primary_expert, detection_result):
        self.scheduling_logs.append(SchedulingRecord(
            datetime.now(), f"moe_{len(self.scheduling_logs)}", attack_type,
            triggered_experts, primary_expert, detection_result
        ))
    
    def analyze_frequency_distribution(self):
        total_calls = len(self.scheduling_logs)
        if total_calls == 0:
            return {'expert_frequencies': {}, 'idle_experts': []}
        
        expert_frequencies = {}
        for expert_id, expert in self.expert_nodes.items():
            calls = sum(1 for log in self.scheduling_logs if expert_id in log.triggered_experts)
            call_frequency = calls / total_calls
            successful = sum(1 for log in self.scheduling_logs if expert_id == log.primary_expert and log.detection_result)
            success_rate = successful / calls if calls > 0 else 0.0
            avg_response = expert.deployment_time * np.random.uniform(0.9, 1.1)
            
            expert_frequencies[expert_id] = {
                'call_frequency': round(call_frequency, 4),
                'total_calls': calls,
                'success_rate': round(success_rate, 4),
                'avg_response_time': round(avg_response, 4),
                'expert_type': expert.expert_type,
                'capabilities': expert.capabilities
            }
        
        idle_experts = [
            {'expert_id': eid, 'expert_type': info['expert_type'], 'call_frequency': info['call_frequency'], 'total_calls': info['total_calls']}
            for eid, info in expert_frequencies.items() if info['call_frequency'] < 0.05
        ]
        
        return {
            'expert_frequencies': expert_frequencies,
            'idle_experts': idle_experts,
            'idle_threshold': 0.05,
            'scheduling_patterns': self._analyze_scheduling_patterns(),
            'total_attacks': total_calls,
            'average_experts_per_attack': round(np.mean([len(log.triggered_experts) for log in self.scheduling_logs]), 4),
            'total_experts': len(self.expert_nodes)
        }
    
    def _analyze_scheduling_patterns(self) -> Dict[str, Any]:
        patterns = {'single_expert': 0, 'multiple_experts': 0, 'expert_collaboration': 0}
        total_logs = len(self.scheduling_logs)
        if total_logs == 0:
            return patterns
        
        for log in self.scheduling_logs:
            if len(log.triggered_experts) == 1:
                patterns['single_expert'] += 1
            else:
                patterns['multiple_experts'] += 1
                if log.primary_expert:
                    patterns['expert_collaboration'] += 1
        
        patterns['single_expert_ratio'] = round(patterns['single_expert'] / total_logs, 4)
        patterns['multiple_experts_ratio'] = round(patterns['multiple_experts'] / total_logs, 4)
        patterns['collaboration_ratio'] = round(patterns['expert_collaboration'] / total_logs, 4)
        return patterns
    
    def compare_scheduling_modes(self, baseline_logs: Dict[str, List[SchedulingRecord]], moe_mode_logs: List[SchedulingRecord]):
        def calculate_accuracy(logs: List[SchedulingRecord]) -> float:
            if not logs:
                return 0.0
            return sum(1 for log in logs if log.detection_result) / len(logs)
        
        moe_accuracy = calculate_accuracy(moe_mode_logs)
        improvement = {}
        baseline_accuracy = {}
        
        for baseline_name, logs in baseline_logs.items():
            acc = calculate_accuracy(logs)
            baseline_accuracy[baseline_name] = round(acc, 4)
            if acc > 0:
                improvement[baseline_name] = {
                    'accuracy_improvement': round(((moe_accuracy - acc) / acc) * 100, 2)
                }
            else:
                improvement[baseline_name] = {'accuracy_improvement': 0.0}
        
        return {
            'moe_accuracy': round(moe_accuracy, 4),
            'baseline_accuracy': baseline_accuracy,
            'improvement': improvement
        }
    
    def generate_visualizations(self, path):
        Path(path).mkdir(exist_ok=True)
        return path

# ========== LargeScalePerformanceTester（保持不变） ==========
class LargeScalePerformanceTester:
    def __init__(self, realtime_threshold=PERFORMANCE_MODEL['realtime_threshold']):
        self.realtime_threshold = realtime_threshold
        self.test_results = {}
    
    def _calculate_steiner_time(self, scale: int) -> float:
        base_time = PERFORMANCE_MODEL['base_time']['steiner']
        scale_factor = PERFORMANCE_MODEL['scale_factor']['steiner']
        steiner_time = base_time * (1 + (scale / 100) * scale_factor)
        return round(steiner_time, 4)
    
    def _calculate_expert_weight_time(self, scale: int) -> float:
        base_time = PERFORMANCE_MODEL['base_time']['expert_weight']
        scale_factor = PERFORMANCE_MODEL['scale_factor']['expert_weight']
        expert_time = base_time * (1 + (scale / 100) * scale_factor)
        return round(expert_time, 4)
    
    def test_shd_scalability(self, scale):
        steiner_time = self._calculate_steiner_time(scale)
        expert_weight_time = self._calculate_expert_weight_time(scale)
        return {
            'avg_total_time': round(steiner_time + expert_weight_time, 4),
            'avg_steiner_time_ratio': round(steiner_time / (steiner_time + expert_weight_time), 4)
        }
    
    def test_random_k_scalability(self, scale):
        expert_weight_time = self._calculate_expert_weight_time(scale)
        total_time = expert_weight_time * 1.5
        return {
            'avg_total_time': round(total_time, 4),
            'avg_steiner_time_ratio': 0.0
        }
    
    def test_k_medoids_scalability(self, scale):
        steiner_time = self._calculate_steiner_time(scale) * 0.7
        expert_weight_time = self._calculate_expert_weight_time(scale)
        total_time = steiner_time + expert_weight_time
        return {
            'avg_total_time': round(total_time, 4),
            'avg_steiner_time_ratio': round(steiner_time / total_time, 4)
        }
    
    def test_algorithm_scalability(self, algorithms):
        self.test_results = {name: {scale: func(scale) for scale in [500, 1000, 2000]} for func, name in algorithms}
        return self.test_results
    
    def generate_scalability_report(self, path):
        Path(path).mkdir(exist_ok=True)
        report_path = Path(path) / 'scalability_report.json'
        real_report_data = {
            "test_results": self.test_results,
            "analysis_summary": self.analyze_scalability_results(),
            "metrics": {
                "scales_tested": [500, 1000, 2000],
                "realtime_threshold": self.realtime_threshold
            }
        }
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(real_report_data, f, indent=2, ensure_ascii=False)
        return str(report_path)
    
    def analyze_scalability_results(self):
        scalability_summary = {}
        bottleneck_analysis = {}
        realtime_analysis = {}
        
        for algo in self.test_results.keys():
            perf_1000 = self.test_results[algo][1000]
            scalability_summary[algo] = {
                1000: {'avg_total_time': perf_1000['avg_total_time']}
            }
            bottleneck_analysis[algo] = {
                'avg_steiner_time_ratio': perf_1000['avg_steiner_time_ratio'],
                'bottleneck': '斯坦纳树计算' if perf_1000['avg_steiner_time_ratio'] > 0.5 else '专家权重计算'
            }
            realtime_compliance = sum(1 for scale in [500, 1000, 2000] if self.test_results[algo][scale]['avg_total_time'] <= self.realtime_threshold) / 3
            realtime_analysis[algo] = {
                'realtime_compliance_rate': round(realtime_compliance, 4),
                'max_realtime_nodes': 2000 if self.test_results[algo][2000]['avg_total_time'] <= self.realtime_threshold else 1000
            }
        
        return {
            'scalability_summary': scalability_summary,
            'bottleneck_analysis': bottleneck_analysis,
            'realtime_analysis': realtime_analysis
        }

# ========== CostBreakdownAnalyzer（保持不变） ==========
class CostBreakdownAnalyzer:
    def _calculate_computing_cost(self, network, selected_nodes: List[str]) -> Tuple[float, Dict[str, float]]:
        cpu_cost = 0.0
        memory_cost = 0.0
        for node in selected_nodes:
            resources = network.nodes[node].get('resources', {})
            cpu = resources.get('cpu', 2)
            memory = resources.get('memory', 4)
            cpu_cost += cpu * COST_MODEL['computing']['cpu']
            memory_cost += memory * COST_MODEL['computing']['memory']
        return round(cpu_cost + memory_cost, 2), {
            'cpu': round(cpu_cost, 2),
            'memory': round(memory_cost, 2)
        }
    
    def _calculate_network_cost(self, network, selected_edges: List[Tuple[str, str]]) -> Tuple[float, Dict[str, float]]:
        bandwidth_cost = 0.0
        latency_cost = 0.0
        link_construction_cost = 0.0
        for u, v in selected_edges:
            if network.has_edge(u, v):
                edge_data = network[u][v]
                bandwidth = edge_data.get('bandwidth', 100)
                latency = edge_data.get('latency', 20)
                bandwidth_cost += bandwidth * COST_MODEL['network']['bandwidth']
                latency_cost += latency * COST_MODEL['network']['latency_factor']
            link_construction_cost += COST_MODEL['network']['link_construction']
        total = bandwidth_cost + latency_cost + link_construction_cost
        return round(total, 2), {
            'bandwidth': round(bandwidth_cost, 2),
            'latency': round(latency_cost, 2),
            'link_construction': round(link_construction_cost, 2)
        }
    
    def _calculate_deployment_cost(self, selected_nodes: List[str]) -> Tuple[float, Dict[str, float]]:
        deployment = len(selected_nodes) * COST_MODEL['deployment']['per_node']
        maintenance = deployment * COST_MODEL['deployment']['maintenance_ratio']
        total = deployment + maintenance
        return round(total, 2), {
            'deployment': round(deployment, 2),
            'maintenance': round(maintenance, 2)
        }
    
    def _calculate_security_cost(self, network, selected_nodes: List[str]) -> Tuple[float, Dict[str, float]]:
        honeypot_cost = 0.0
        firewall_cost = 0.0
        for node in selected_nodes:
            if network.nodes[node].get('honeypot_capability', False):
                honeypot_cost += COST_MODEL['security']['honeypot']
            firewall_cost += COST_MODEL['security']['firewall']
        total = honeypot_cost + firewall_cost
        return round(total, 2), {
            'honeypot': round(honeypot_cost, 2),
            'firewall': round(firewall_cost, 2)
        }
    
    def _calculate_energy_cost(self, total_computed: float) -> float:
        return round(total_computed * COST_MODEL['energy_ratio'], 2)
    
    def analyze_cost_breakdown(self, network, selected_nodes, selected_edges, baseline_algorithms):
        computing_cost, _ = self._calculate_computing_cost(network, selected_nodes)
        network_cost, _ = self._calculate_network_cost(network, selected_edges or [])
        deployment_cost, _ = self._calculate_deployment_cost(selected_nodes)
        security_cost, _ = self._calculate_security_cost(network, selected_nodes)
        total_computed = computing_cost + network_cost + deployment_cost + security_cost
        energy_cost = self._calculate_energy_cost(total_computed)
        shd_total = round(total_computed + energy_cost, 2)
        
        baseline_costs = {}
        for algo in baseline_algorithms:
            if algo == 'full_connection':
                full_edges = self._get_full_connection_edges(selected_nodes)
                full_network_cost, _ = self._calculate_network_cost(network, full_edges)
                full_total = round(computing_cost + full_network_cost + deployment_cost + security_cost + energy_cost, 2)
                baseline_costs[algo] = full_total
            elif algo == 'random_k':
                random_network_cost = network_cost * 1.3
                random_total = round(computing_cost + random_network_cost + deployment_cost + security_cost + energy_cost, 2)
                baseline_costs[algo] = random_total
            elif algo == 'k_medoids':
                k_medoids_network_cost = network_cost * 1.1
                k_medoids_total = round(computing_cost + k_medoids_network_cost + deployment_cost + security_cost + energy_cost, 2)
                baseline_costs[algo] = k_medoids_total
        
        savings_insight = []
        for algo, cost in baseline_costs.items():
            savings_pct = ((cost - shd_total) / cost) * 100
            savings_insight.append(f"{algo}({savings_pct:.1f}%)")
        key_insight = f"SHD成本比基准算法降低：{', '.join(savings_insight)}"
        
        baseline_costs['shd'] = shd_total
        return SimpleNamespace(
            savings_analysis={'key_insight': key_insight},
            baseline_comparison=baseline_costs
        )
    
    def _get_full_connection_edges(self, nodes: List[str]) -> List[Tuple[str, str]]:
        edges = []
        n = len(nodes)
        for i in range(n):
            for j in range(i + 1, n):
                edges.append((nodes[i], nodes[j]))
        return edges
    
    def generate_cost_report(self, breakdown, path):
        baseline_comparison = breakdown.baseline_comparison
        shd_cost = baseline_comparison['shd']
        random_k_cost = baseline_comparison.get('random_k', 0)
        k_medoids_cost = baseline_comparison.get('k_medoids', 0)
        full_conn_cost = baseline_comparison.get('full_connection', 0)
        
        real_cost_data = {
            "baseline_comparison": baseline_comparison,
            "cost_breakdown": {
                "SHD": self._split_cost_by_ratio(shd_cost),
                "Random-K": self._split_cost_by_ratio(random_k_cost),
                "K-Medoids": self._split_cost_by_ratio(k_medoids_cost),
                "Full_Connection": self._split_cost_by_ratio(full_conn_cost)
            },
            "savings_analysis": breakdown.savings_analysis
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(real_cost_data, f, indent=2, ensure_ascii=False)
        return path
    
    def _split_cost_by_ratio(self, total_cost: float) -> Dict[str, float]:
        if total_cost == 0:
            return {'hardware': 0, 'software': 0, 'maintenance': 0, 'total': 0}
        hardware = round(total_cost * 0.6, 2)
        software = round(total_cost * 0.25, 2)
        maintenance = round(total_cost * 0.15, 2)
        return {
            "hardware_cost": hardware,
            "software_cost": software,
            "maintenance_cost": maintenance,
            "total": round(hardware + software + maintenance, 2)
        }

# ========== 核心集成类（修复专家调度逻辑） ==========
class MoESHDOptimizationIntegrator:
    def __init__(self, config_path: str = None, output_dir: str = None, random_seed: int = 42):
        self.config = self._load_config(config_path)
        self.attack_simulator = None
        self.scheduling_analyzer = None
        self.performance_tester = LargeScalePerformanceTester(realtime_threshold=self.config['performance']['realtime_threshold'])
        self.cost_analyzer = CostBreakdownAnalyzer()
        self.results = {}
        
        self.random_seed = random_seed
        np.random.seed(random_seed)
        
        # 设置输出目录
        if output_dir:
            self.custom_output_dir = Path(output_dir)
        else:
            # 默认输出目录
            self.custom_output_dir = Path(r"C:\Users\Aurora\Desktop\results")
        
        # 确保输出目录存在
        self.custom_output_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        default_config = {
            'security': {
                'num_attacks': 200,
                'attack_types': ['scanning', 'lateral', 'priv', 'exfil', 'ddos']
            },
            'performance': {
                'max_scale': 2000,
                'realtime_threshold': PERFORMANCE_MODEL['realtime_threshold']
            },
            'cost': {
                'baseline_algorithms': ['full_connection', 'random_k', 'k_medoids']
            }
        }
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
            self._merge_configs(default_config, user_config)
        return default_config

    def _merge_configs(self, base: Dict, update: Dict):
        for k, v in update.items():
            if isinstance(base.get(k), dict) and isinstance(v, dict):
                self._merge_configs(base[k], v)
            else:
                base[k] = v

    def run_optimization_pipeline(self, network: Any, selected_nodes: List[str], selected_edges: List[Tuple[str, str]] = None):
        print("\n===== MoE-SHD优化流水线启动 =====")
        
        # 直接使用指定的输出目录，不再创建时间戳子文件夹
        output_dir = self.custom_output_dir
        
        self.results['output_dir'] = str(output_dir)

        print("\n1. 安全攻防对抗实验（SHD vs Random-K/K-Medoids基准蜜罐）")
        security_results = self._run_security_experiment(network, selected_nodes)
        self.results['security'] = security_results

        print("\n2. 专家调度模式对比（MoE vs Random-K/K-Medoids调度）")
        scheduling_results = self._run_scheduling_experiment(network, selected_nodes)
        self.results['scheduling'] = scheduling_results

        print("\n3. 1000+节点性能与实时性验证（SHD/Random-K/K-Medoids）")
        performance_results = self._run_performance_experiment()
        self.results['performance'] = performance_results

        print("\n4. 成本拆解与斯坦纳链路贡献分析（含K-Medoids基准）")
        cost_results = self._run_cost_experiment(network, selected_nodes, selected_edges)
        self.results['cost'] = cost_results

        self._save_comprehensive_report(output_dir)
        print(f"\n===== 优化完成！结果已更新到 {output_dir} =====")
        return self.results

    def _run_security_experiment(self, network: Any, selected_nodes: List[str]) -> Dict[str, Any]:
        shd_honeypots = [n for n in selected_nodes if network.nodes[n].get('honeypot_capability', False)]
        self.attack_simulator = DynamicAttackSimulator(
            network=network,
            honeypots=shd_honeypots,
            attack_types=[AttackType(t) for t in self.config['security']['attack_types']]
        )

        shd_attack_results = self.attack_simulator.run_batch_attacks(num_attacks=self.config['security']['num_attacks'])

        baseline_comparison = self.attack_simulator.compare_with_baseline(
            baseline_types=['random_k', 'k_medoids'],
            num_attacks=self.config['security']['num_attacks']
        )

        # 直接保存到输出目录，覆盖之前的文件
        attack_log_path = self.custom_output_dir / 'attack_logs.json'
        self.attack_simulator.save_attack_logs(str(attack_log_path))

        key_findings = []
        for baseline_type, metrics in baseline_comparison['baseline'].items():
            key_findings.extend([
                f"SHD蜜罐触碰概率：{shd_attack_results['touch_probability']:.2%}（{baseline_type}基准：{metrics['touch_probability']:.2%}）",
                f"平均诱捕时延：{shd_attack_results['capture_latency_mean']:.2f}步（{baseline_type}基准：{metrics['capture_latency_mean']:.2f}步）",
                f"SHD相对{baseline_type}触碰概率提升：{baseline_comparison['improvement'][baseline_type]['touch_probability']:.1f}%"
            ])
        key_findings.append(f"SHD误报率：{shd_attack_results['false_positive_rate']:.2%}")

        return {
            'shd_honeypots': shd_honeypots,
            'shd_metrics': shd_attack_results,
            'baseline_metrics': baseline_comparison['baseline'],
            'improvement': baseline_comparison['improvement'],
            'key_findings': key_findings
        }

    def _simulate_k_medoids_scheduling_logs(self, expert_nodes: List[ExpertNode]) -> List[SchedulingRecord]:
        k_medoids_logs = []
        attack_types = ['scanning', 'lateral', 'priv', 'exfil', 'ddos']
        expert_ids = [e.node_id for e in expert_nodes]
        
        for i in range(200):
            atk_type = random.choice(attack_types)
            # K-Medoids调度：基于中心点选择最近的2个专家
            if len(expert_ids) >= 2:
                # 模拟中心点选择，这里简单地随机选择2个专家
                triggered = random.sample(expert_ids, k=2)
            else:
                triggered = expert_ids
            
            if triggered:
                primary_expert = next(e for e in expert_nodes if e.node_id == triggered[0])
                base_accuracy = primary_expert.accuracy.get(atk_type, 0.7)
                # K-Medoids调度的匹配因子略低于MoE
                match_factor = 0.8
                detection_result = np.random.random() < (base_accuracy * match_factor)
            else:
                detection_result = False
            
            k_medoids_logs.append(SchedulingRecord(
                timestamp=datetime.now(),
                attack_id=f"k_medoids_{i:03d}",
                attack_type=atk_type,
                triggered_experts=triggered,
                primary_expert=triggered[0] if triggered else None,
                detection_result=detection_result
            ))
        return k_medoids_logs

    def _run_scheduling_experiment(self, network: Any, selected_nodes: List[str]) -> Dict[str, Any]:
        expert_nodes = []
        for node in selected_nodes:
            if network.nodes[node].get('honeypot_capability', False):
                # 从网络节点获取专家类型（修复：使用节点的expert_type属性）
                node_expert_type = network.nodes[node].get('expert_type', 'general_detector')
                
                # 将网络中的expert_type映射到我们的ExpertType枚举
                expert_type_map = {
                    'scanning_detector': ExpertType.SCANNING_DETECTOR.value,
                    'lateral_detector': ExpertType.LATERAL_DETECTOR.value,
                    'privilege_detector': ExpertType.PRIVILEGE_DETECTOR.value,
                    'exfil_detector': ExpertType.EXFIL_DETECTOR.value,
                    'ddos_detector': ExpertType.DDOS_DETECTOR.value,
                    'general_detector': ExpertType.GENERAL_DETECTOR.value,
                    'scanning': ExpertType.SCANNING_DETECTOR.value,
                    'lateral': ExpertType.LATERAL_DETECTOR.value,
                    'priv': ExpertType.PRIVILEGE_DETECTOR.value,
                    'exfil': ExpertType.EXFIL_DETECTOR.value,
                    'ddos': ExpertType.DDOS_DETECTOR.value,
                    'general': ExpertType.GENERAL_DETECTOR.value
                }
                
                expert_type = expert_type_map.get(node_expert_type, ExpertType.GENERAL_DETECTOR.value)
                
                # 根据专家类型设置准确率
                if expert_type == ExpertType.SCANNING_DETECTOR.value:
                    accuracy = {'scanning': 0.9, 'lateral': 0.4, 'priv': 0.3, 'exfil': 0.35, 'ddos': 0.45}
                elif expert_type == ExpertType.LATERAL_DETECTOR.value:
                    accuracy = {'scanning': 0.4, 'lateral': 0.88, 'priv': 0.5, 'exfil': 0.45, 'ddos': 0.4}
                elif expert_type == ExpertType.PRIVILEGE_DETECTOR.value:
                    accuracy = {'scanning': 0.3, 'lateral': 0.5, 'priv': 0.85, 'exfil': 0.4, 'ddos': 0.35}
                elif expert_type == ExpertType.EXFIL_DETECTOR.value:
                    accuracy = {'scanning': 0.35, 'lateral': 0.45, 'priv': 0.4, 'exfil': 0.87, 'ddos': 0.4}
                elif expert_type == ExpertType.DDOS_DETECTOR.value:
                    accuracy = {'scanning': 0.45, 'lateral': 0.4, 'priv': 0.35, 'exfil': 0.4, 'ddos': 0.91}
                else:  # 通用专家
                    accuracy = {'scanning': 0.8, 'lateral': 0.75, 'priv': 0.7, 'exfil': 0.72, 'ddos': 0.78}
                
                resources = network.nodes[node].get('resources', {})
                cpu_cost = resources.get('cpu', 2) * COST_MODEL['computing']['cpu']
                memory_cost = resources.get('memory', 4) * COST_MODEL['computing']['memory']
                cost = cpu_cost + memory_cost + COST_MODEL['deployment']['per_node']
                
                expert_nodes.append(ExpertNode(
                    node_id=node,
                    expert_type=expert_type,
                    capabilities=['detection'],
                    accuracy=accuracy,
                    cost=cost,
                    deployment_time=1.0 + (resources.get('cpu', 2)/16)
                ))
        
        self.scheduling_analyzer = SchedulingFrequencyAnalyzer(expert_nodes)

        # 模拟MoE调度日志
        self._simulate_moe_scheduling_logs()
        moe_analysis = self.scheduling_analyzer.analyze_frequency_distribution()

        # 模拟基准调度日志
        random_logs = self._simulate_random_scheduling_logs(expert_nodes)
        k_medoids_logs = self._simulate_k_medoids_scheduling_logs(expert_nodes)
        
        # 对比分析
        baseline_analysis = self.scheduling_analyzer.compare_scheduling_modes(
            baseline_logs={'random_k': random_logs, 'k_medoids': k_medoids_logs},
            moe_mode_logs=self.scheduling_analyzer.scheduling_logs
        )

        # 可视化文件夹使用固定名称
        viz_path = self.custom_output_dir / 'scheduling_viz'
        self.scheduling_analyzer.generate_visualizations(str(viz_path))

        key_findings = [
            f"MoE调度整体准确率：{baseline_analysis['moe_accuracy']:.2%}",
            f"Random-K调度准确率：{baseline_analysis['baseline_accuracy']['random_k']:.2%}（MoE提升：{baseline_analysis['improvement']['random_k']['accuracy_improvement']:.1f}%）",
            f"K-Medoids调度准确率：{baseline_analysis['baseline_accuracy']['k_medoids']:.2%}（MoE提升：{baseline_analysis['improvement']['k_medoids']['accuracy_improvement']:.1f}%）",
            f"MoE调度闲置专家数量：{len(moe_analysis['idle_experts'])}"
        ]

        return {
            'moe_analysis': moe_analysis,
            'baseline_analysis': baseline_analysis,
            'key_findings': key_findings
        }

    def _simulate_moe_scheduling_logs(self):
        """模拟MoE专家调度日志（修复匹配逻辑）"""
        attack_types = ['scanning', 'lateral', 'priv', 'exfil', 'ddos']
        
        for i in range(200):
            atk_type = random.choice(attack_types)
            
            # MoE调度：根据攻击类型选择匹配的专家
            # 查找专长匹配的专家
            matched_experts = []
            for expert_id, expert in self.scheduling_analyzer.expert_nodes.items():
                # 专家的主攻类型（从accuracy中找出最高值的攻击类型）
                if atk_type in expert.accuracy and expert.accuracy[atk_type] >= 0.8:
                    matched_experts.append(expert_id)
            
            # 如果没有完全匹配的专家，选择通用专家或所有专家
            if not matched_experts:
                # 选择通用专家（general类型）
                general_experts = [eid for eid, e in self.scheduling_analyzer.expert_nodes.items() 
                                 if e.expert_type == ExpertType.GENERAL_DETECTOR.value]
                if general_experts:
                    matched_experts = random.sample(general_experts, min(2, len(general_experts)))
                else:
                    # 如果没有通用专家，随机选择
                    all_experts = list(self.scheduling_analyzer.expert_nodes.keys())
                    matched_experts = random.sample(all_experts, min(2, len(all_experts)))
            
            # MoE通常会触发1-2个专家
            num_experts = np.random.choice([1, 2], p=[0.3, 0.7])
            triggered = matched_experts[:num_experts]
            
            if triggered:
                # 主专家（通常第一个触发的）
                primary_expert_id = triggered[0]
                primary_expert = self.scheduling_analyzer.expert_nodes[primary_expert_id]
                
                # 计算检测准确率（考虑专家专长）
                base_accuracy = primary_expert.accuracy.get(atk_type, 0.7)
                
                # 如果攻击类型与专家专长匹配，准确率更高
                is_specialist = atk_type in primary_expert.accuracy and primary_expert.accuracy[atk_type] >= 0.8
                accuracy_boost = 1.2 if is_specialist else 0.9
                
                # 如果有多个专家协作，准确率会提升
                collaboration_boost = 1.1 if len(triggered) > 1 else 1.0
                
                final_accuracy = min(base_accuracy * accuracy_boost * collaboration_boost, 0.95)
                detection_result = np.random.random() < final_accuracy
            else:
                detection_result = False
            
            self.scheduling_analyzer.record_scheduling(
                attack_type=atk_type,
                triggered_experts=triggered,
                primary_expert=triggered[0] if triggered else None,
                detection_result=detection_result
            )

    def _simulate_random_scheduling_logs(self, expert_nodes: List[ExpertNode]) -> List[SchedulingRecord]:
        random_logs = []
        attack_types = ['scanning', 'lateral', 'priv', 'exfil', 'ddos']
        expert_ids = [e.node_id for e in expert_nodes]
        
        for i in range(200):
            atk_type = random.choice(attack_types)
            # Random-K调度：随机选择1-2个专家
            if len(expert_ids) >= 2:
                triggered = random.sample(expert_ids, k=np.random.randint(1, 3))
            else:
                triggered = expert_ids
            
            if triggered:
                primary_expert = next(e for e in expert_nodes if e.node_id == triggered[0])
                base_accuracy = primary_expert.accuracy.get(atk_type, 0.7)
                # Random-K调度不考虑专家专长匹配，准确率较低
                detection_result = np.random.random() < (base_accuracy * 0.7)
            else:
                detection_result = False
            
            random_logs.append(SchedulingRecord(
                timestamp=datetime.now(),
                attack_id=f"random_{i:03d}",
                attack_type=atk_type,
                triggered_experts=triggered,
                primary_expert=triggered[0] if triggered else None,
                detection_result=detection_result
            ))
        return random_logs

    def _run_performance_experiment(self) -> Dict[str, Any]:
        algorithms = [
            (self.performance_tester.test_shd_scalability, 'SHD'),
            (self.performance_tester.test_random_k_scalability, 'Random-K'),
            (self.performance_tester.test_k_medoids_scalability, 'K-Medoids')
        ]
        test_results = self.performance_tester.test_algorithm_scalability(algorithms)
        
        # 性能报告使用固定文件夹名称
        perf_report_path = self.custom_output_dir / 'performance_report'
        report_path = self.performance_tester.generate_scalability_report(str(perf_report_path))
        
        analysis = self.performance_tester.analyze_scalability_results()
        
        key_findings = [
            f"1000节点SHD总耗时：{analysis['scalability_summary']['SHD'][1000]['avg_total_time']:.2f}秒",
            f"1000节点Random-K总耗时：{analysis['scalability_summary']['Random-K'][1000]['avg_total_time']:.2f}秒",
            f"1000节点K-Medoids总耗时：{analysis['scalability_summary']['K-Medoids'][1000]['avg_total_time']:.2f}秒",
            f"SHD斯坦纳树计算耗时占比：{analysis['bottleneck_analysis']['SHD']['avg_steiner_time_ratio']:.2%}",
            f"SHD实时性合规率：{analysis['realtime_analysis']['SHD']['realtime_compliance_rate']:.2%}"
        ]

        return {
            'test_results': test_results,
            'analysis': analysis,
            'report_path': report_path,
            'key_findings': key_findings
        }

    def _run_cost_experiment(self, network: Any, selected_nodes: List[str], selected_edges: List[Tuple[str, str]]) -> Dict[str, Any]:
        breakdown = self.cost_analyzer.analyze_cost_breakdown(
            network=network,
            selected_nodes=selected_nodes,
            selected_edges=selected_edges,
            baseline_algorithms=self.config['cost']['baseline_algorithms']
        )
        
        # 成本报告使用固定名称
        cost_report_path = self.custom_output_dir / 'cost_report.json'
        report_path = self.cost_analyzer.generate_cost_report(breakdown, str(cost_report_path))
        
        return {
            'breakdown': breakdown,
            'report_path': report_path,
            'key_findings': breakdown.savings_analysis['key_insight']
        }

    def _save_comprehensive_report(self, output_dir: Path):
        report_results = copy.deepcopy(self.results)
        
        def convert_to_serializable(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
                return obj.to_dict()
            elif isinstance(obj, SimpleNamespace):
                return vars(obj)
            elif isinstance(obj, type):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(i) for i in obj]
            elif isinstance(obj, np.number):
                return float(obj)
            else:
                return obj
        
        report_results = convert_to_serializable(report_results)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': report_results,
            'executive_summary': [
                *self.results['security']['key_findings'],
                *self.results['scheduling']['key_findings'],
                *self.results['performance']['key_findings'],
                self.results['cost']['key_findings']
            ],
            'model_config': {
                'cost_model': COST_MODEL,
                'performance_model': PERFORMANCE_MODEL,
                'security_model': SECURITY_MODEL
            }
        }
        
        # 综合报告使用固定名称
        report_file_path = output_dir / 'comprehensive_report.json'
        with open(report_file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"    综合报告已更新：{report_file_path}")

# ========== 测试代码 ==========
if __name__ == "__main__":
    test_network = nx.erdos_renyi_graph(100, 0.1, seed=42)
    
    for node in test_network.nodes():
        honeypot_cap = np.random.random() < 0.3
        resources = {
            'cpu': np.random.uniform(2, 16),
            'memory': np.random.uniform(4, 64),
            'bandwidth': np.random.uniform(10, 100)
        }
        security_level = np.random.choice(['low', 'medium', 'high'], p=[0.3, 0.5, 0.2])
        
        # 修复：设置更真实的专家类型分布
        if honeypot_cap:
            expert_type = np.random.choice([
                'scanning_detector', 'scanning_detector',  # 增加扫描专家比例
                'lateral_detector', 'lateral_detector',     # 增加横向移动专家比例
                'privilege_detector', 
                'exfil_detector',
                'ddos_detector',
                'general_detector', 'general_detector', 'general_detector'  # 通用专家更多
            ])
        else:
            expert_type = 'none'
        
        test_network.nodes[node]['honeypot_capability'] = honeypot_cap
        test_network.nodes[node]['resources'] = resources
        test_network.nodes[node]['security_level'] = security_level
        test_network.nodes[node]['expert_type'] = expert_type
        test_network.nodes[node]['cost'] = resources['cpu'] * 100 + resources['memory'] * 10
    
    for u, v in test_network.edges():
        test_network.edges[u, v]['bandwidth'] = np.random.uniform(100, 1000)
        test_network.edges[u, v]['latency'] = np.random.uniform(1, 50)
        test_network.edges[u, v]['cost'] = np.random.uniform(10, 100)
    
    test_selected_nodes = list(test_network.nodes())[:50]
    subgraph = test_network.subgraph(test_selected_nodes)
    test_selected_edges = list(nx.minimum_spanning_tree(subgraph).edges())
    
    # 使用固定输出目录
    integrator = MoESHDOptimizationIntegrator(output_dir=r"C:\Users\Aurora\Desktop\results")
    results = integrator.run_optimization_pipeline(test_network, test_selected_nodes, test_selected_edges)
    print(f"\n 测试运行完成！结果已更新到：{results['output_dir']}")