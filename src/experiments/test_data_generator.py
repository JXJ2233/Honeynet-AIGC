# src/experiments/test_data_generator.py
"""
测试数据生成器 - 生成MoE-SHD测试场景
生成6种标准测试场景用于算法评估
"""

import json
import os
import random
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime


class TestDataGenerator:
    """生成MoE-SHD测试数据的类"""
    
    def __init__(self, seed: int = 42):
        """初始化测试数据生成器
        
        Args:
            seed: 随机种子
        """
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        print(f" TestDataGenerator 初始化完成，种子: {seed}")
        
    def generate_scenario(self, scenario_name: str) -> Dict:
        """生成指定场景的测试数据
        
        Args:
            scenario_name: 场景名称
            
        Returns:
            包含测试数据的字典
        """
        scenarios = {
            "小型稀疏网络": {
                "terminal_nodes": 10,
                "steiner_candidates": 15,
                "avg_degree": 1.5,
                "density": "低",
                "attack_vectors": 5,
                "budget": 5000
            },
            "小型密集网络": {
                "terminal_nodes": 10,
                "steiner_candidates": 15,
                "avg_degree": 3.5,
                "density": "高",
                "attack_vectors": 8,
                "budget": 6000
            },
            "中型稀疏网络": {
                "terminal_nodes": 30,
                "steiner_candidates": 45,
                "avg_degree": 2.0,
                "density": "中",
                "attack_vectors": 12,
                "budget": 15000
            },
            "中型密集网络": {
                "terminal_nodes": 30,
                "steiner_candidates": 45,
                "avg_degree": 4.0,
                "density": "高",
                "attack_vectors": 15,
                "budget": 18000
            },
            "大型稀疏网络": {
                "terminal_nodes": 50,
                "steiner_candidates": 75,
                "avg_degree": 2.5,
                "density": "中",
                "attack_vectors": 20,
                "budget": 25000
            },
            "大型密集网络": {
                "terminal_nodes": 50,
                "steiner_candidates": 75,
                "avg_degree": 5.0,
                "density": "很高",
                "attack_vectors": 25,
                "budget": 30000
            }
        }
        
        if scenario_name not in scenarios:
            raise ValueError(f"未知场景: {scenario_name}")
        
        config = scenarios[scenario_name]
        
        print(f"生成测试场景: {scenario_name}")
        print(f"  终端节点: {config['terminal_nodes']}, 斯坦纳候选: {config['steiner_candidates']}")
        print(f"  平均度数: {config['avg_degree']}, 密度: {config['density']}, 预算: ${config['budget']}")
        
        # 生成测试数据
        data = {
            "scenario_name": scenario_name,
            "config": config,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "seed": self.seed,
                "version": "1.0"
            },
            "terminal_nodes": self._generate_terminal_nodes(config),
            "steiner_candidates": self._generate_steiner_candidates(config),
            "network_edges": self._generate_network_edges(config),
            "attack_vectors": self._generate_attack_vectors(config),
            "constraints": self._generate_constraints(config)
        }
        
        return data
    
    def _generate_terminal_nodes(self, config: Dict) -> List[Dict]:
        """生成终端节点数据"""
        nodes = []
        
        for i in range(config["terminal_nodes"]):
            # 随机分配重要性级别
            importance = random.choice([0.3, 0.5, 0.7, 0.9])
            
            # 根据重要性分配资源
            cpu_base = 0.2 if importance < 0.5 else 0.5 if importance < 0.8 else 0.8
            memory_base = 0.3 if importance < 0.5 else 0.6 if importance < 0.8 else 0.9
            
            nodes.append({
                "id": f"T{i:03d}",
                "type": "terminal",
                "name": f"终端节点_{i+1}",
                "importance": importance,
                "cpu_capacity": cpu_base + random.uniform(-0.1, 0.1),
                "memory_capacity": memory_base + random.uniform(-0.1, 0.1),
                "bandwidth_capacity": random.uniform(1.0, 3.0),
                "coordinates": {
                    "x": random.uniform(0, 100),
                    "y": random.uniform(0, 100)
                },
                "attacked_probability": random.uniform(0.1, 0.9),
                "security_level": random.choice(["低", "中", "高"])
            })
        
        return nodes
    
    def _generate_steiner_candidates(self, config: Dict) -> List[Dict]:
        """生成斯坦纳候选节点数据"""
        candidates = []
        
        for i in range(config["steiner_candidates"]):
            # 随机生成节点类型
            node_type = random.choice(["server", "router", "switch", "firewall"])
            
            # 根据类型分配成本和资源
            if node_type == "server":
                cpu = random.uniform(2.0, 8.0)
                memory = random.uniform(4.0, 16.0)
                cost = random.uniform(800, 2000)
                security_coverage = random.uniform(0.7, 0.95)
            elif node_type == "router":
                cpu = random.uniform(1.0, 4.0)
                memory = random.uniform(2.0, 8.0)
                cost = random.uniform(500, 1200)
                security_coverage = random.uniform(0.5, 0.8)
            elif node_type == "switch":
                cpu = random.uniform(0.5, 2.0)
                memory = random.uniform(1.0, 4.0)
                cost = random.uniform(300, 800)
                security_coverage = random.uniform(0.3, 0.6)
            else:  # firewall
                cpu = random.uniform(1.5, 6.0)
                memory = random.uniform(3.0, 12.0)
                cost = random.uniform(600, 1500)
                security_coverage = random.uniform(0.8, 0.99)
            
            candidates.append({
                "id": f"S{i:03d}",
                "type": "steiner_candidate",
                "node_type": node_type,
                "name": f"{node_type}_{i+1}",
                "cpu_capacity": cpu,
                "memory_capacity": memory,
                "bandwidth_capacity": random.uniform(5.0, 20.0),
                "deployment_cost": cost,
                "maintenance_cost": cost * 0.1,  # 维护成本是部署成本的10%
                "security_coverage": security_coverage,
                "honeypot_capability": random.choice([True, False]),
                "coordinates": {
                    "x": random.uniform(0, 100),
                    "y": random.uniform(0, 100)
                },
                "availability": random.uniform(0.95, 0.999)
            })
        
        return candidates
    
    def _generate_network_edges(self, config: Dict) -> List[Dict]:
        """生成网络边数据"""
        edges = []
        
        # 合并所有节点
        all_nodes = []
        terminal_count = config["terminal_nodes"]
        steiner_count = config["steiner_candidates"]
        
        # 创建节点ID列表
        terminal_ids = [f"T{i:03d}" for i in range(terminal_count)]
        steiner_ids = [f"S{i:03d}" for i in range(steiner_count)]
        all_node_ids = terminal_ids + steiner_ids
        
        # 计算需要的边数（根据平均度数）
        total_edges_needed = int(len(all_node_ids) * config["avg_degree"] / 2)
        
        # 确保每个终端节点至少有一条边
        for i in range(terminal_count):
            source = terminal_ids[i]
            # 连接到随机斯坦纳节点或另一个终端
            if steiner_ids:
                target = random.choice(steiner_ids)
            else:
                target = terminal_ids[(i + 1) % terminal_count]
            
            edges.append(self._create_edge(source, target, "必须连接"))
        
        # 生成剩余边
        while len(edges) < total_edges_needed:
            source = random.choice(all_node_ids)
            target = random.choice(all_node_ids)
            
            if source != target:
                # 检查边是否已存在
                edge_exists = any(
                    (e["source"] == source and e["target"] == target) or 
                    (e["source"] == target and e["target"] == source)
                    for e in edges
                )
                
                if not edge_exists:
                    edges.append(self._create_edge(source, target))
        
        return edges
    
    def _create_edge(self, source: str, target: str, edge_type: str = "普通") -> Dict:
        """创建一条边"""
        # 根据端点类型确定延迟和带宽
        is_terminal_source = source.startswith("T")
        is_terminal_target = target.startswith("T")
        
        if is_terminal_source and is_terminal_target:
            # 终端-终端连接
            delay = random.uniform(5.0, 20.0)
            bandwidth = random.uniform(1.0, 5.0)
            cost = random.uniform(50, 200)
        elif (is_terminal_source and not is_terminal_target) or (not is_terminal_source and is_terminal_target):
            # 终端-斯坦纳连接
            delay = random.uniform(2.0, 10.0)
            bandwidth = random.uniform(5.0, 15.0)
            cost = random.uniform(100, 400)
        else:
            # 斯坦纳-斯坦纳连接
            delay = random.uniform(1.0, 5.0)
            bandwidth = random.uniform(10.0, 30.0)
            cost = random.uniform(200, 800)
        
        return {
            "id": f"E{len(self._edge_counter):03d}",
            "source": source,
            "target": target,
            "edge_type": edge_type,
            "bandwidth_capacity": bandwidth,
            "current_bandwidth": random.uniform(0.1, 0.5) * bandwidth,
            "delay": delay,
            "cost_per_unit": cost,
            "reliability": random.uniform(0.98, 0.999),
            "security_level": random.choice(["低", "中", "高"])
        }
    
    # 用于生成边ID的计数器
    _edge_counter = 0
    
    def _generate_attack_vectors(self, config: Dict) -> List[Dict]:
        """生成攻击向量数据"""
        attacks = []
        attack_types = [
            {"name": "DDoS", "cvss_base": 7.5, "difficulty": "中等"},
            {"name": "SQL注入", "cvss_base": 8.5, "difficulty": "高"},
            {"name": "XSS", "cvss_base": 6.5, "difficulty": "中等"},
            {"name": "CSRF", "cvss_base": 8.0, "difficulty": "高"},
            {"name": "中间人攻击", "cvss_base": 8.5, "difficulty": "高"},
            {"name": "零日攻击", "cvss_base": 9.5, "difficulty": "非常高"},
            {"name": "暴力破解", "cvss_base": 5.5, "difficulty": "低"},
            {"name": "社会工程学", "cvss_base": 7.0, "difficulty": "中等"},
            {"name": "恶意软件", "cvss_base": 8.0, "difficulty": "高"},
            {"name": "APT攻击", "cvss_base": 9.0, "difficulty": "非常高"}
        ]
        
        for i in range(config["attack_vectors"]):
            attack_type = random.choice(attack_types)
            cvss_score = attack_type["cvss_base"] + random.uniform(-1.0, 1.0)
            cvss_score = max(0.0, min(10.0, cvss_score))
            
            # 确定严重性等级
            if cvss_score >= 9.0:
                severity = "CRITICAL"
                detection_difficulty = 0.1  # 最难检测
            elif cvss_score >= 7.0:
                severity = "HIGH"
                detection_difficulty = 0.3
            elif cvss_score >= 4.0:
                severity = "MEDIUM"
                detection_difficulty = 0.5
            else:
                severity = "LOW"
                detection_difficulty = 0.7
            
            attacks.append({
                "id": f"A{i:03d}",
                "name": f"{attack_type['name']}_{i+1}",
                "type": attack_type["name"],
                "severity": severity,
                "cvss_score": round(cvss_score, 1),
                "detection_difficulty": detection_difficulty,
                "potential_targets": random.sample(
                    [f"T{j:03d}" for j in range(config["terminal_nodes"])],
                    k=random.randint(1, min(5, config["terminal_nodes"]))
                ),
                "description": f"这是{attack_type['name']}攻击的变种{i+1}",
                "countermeasures": ["防火墙规则", "入侵检测", "流量监控"],
                "success_probability": random.uniform(0.1, 0.8)
            })
        
        return attacks
    
    def _generate_constraints(self, config: Dict) -> Dict:
        """生成约束条件"""
        return {
            "budget_constraint": {
                "total_budget": config["budget"],
                "hardware_budget_ratio": 0.6,
                "deployment_budget_ratio": 0.3,
                "maintenance_budget_ratio": 0.1
            },
            "delay_constraints": {
                "core_to_aggregation_max_ms": 20,
                "aggregation_to_access_max_ms": 30,
                "cross_layer_max_ms": 50
            },
            "security_constraints": {
                "min_coverage_rate": 0.7,
                "min_honeypot_similarity": 0.8,
                "critical_attack_coverage": 1.0  # 必须覆盖所有关键攻击
            },
            "resource_constraints": {
                "max_cpu_usage": 0.3,
                "max_memory_usage": 0.2,
                "max_bandwidth_usage": 0.4
            },
            "topology_constraints": {
                "tree_structure": True,
                "max_steiner_nodes": int(config["steiner_candidates"] * 0.4),  # 最多使用40%的候选节点
                "min_terminal_coverage": 1.0  # 必须覆盖所有终端节点
            }
        }
    
    def save_to_file(self, data: Dict, filename: str):
        """保存数据到文件"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  已保存: {filename}")
    
    def generate_all_scenarios(self, output_dir: str = "test_data"):
        """生成所有测试场景"""
        scenarios = [
            "小型稀疏网络", "小型密集网络",
            "中型稀疏网络", "中型密集网络",
            "大型稀疏网络", "大型密集网络"
        ]
        
        print(f"\n生成MoE-SHD测试数据")
        print(f"输出目录: {output_dir}")
        print(f"随机种子: {self.seed}")
        print("=" * 50)
        
        for scenario in scenarios:
            print(f"\n生成: {scenario}...")
            data = self.generate_scenario(scenario)
            
            # 保存数据
            filename = os.path.join(output_dir, f"{scenario}.json")
            self.save_to_file(data, filename)
            
            print(f"  终端节点: {len(data['terminal_nodes'])}, "
                  f"斯坦纳候选: {len(data['steiner_candidates'])}, "
                  f"平均度数: {data['config']['avg_degree']}")
        
        # 保存配置文件
        config_file = os.path.join(output_dir, "test_config.json")
        config = {
            "scenarios": scenarios,
            "output_dir": output_dir,
            "generated_at": datetime.now().isoformat(),
            "seed": self.seed,
            "version": "1.0"
        }
        self.save_to_file(config, config_file)
        
        print(f"\n{'='*50}")
        print(f" 测试数据生成完成！共 {len(scenarios)} 个场景")
        print(f" 配置文件: {config_file}")
        print(f" 数据目录: {output_dir}/")
        
        return scenarios


def main():
    """主函数：生成所有测试数据"""
    print(" MoE-SHD 测试数据生成器")
    print("基于斯坦纳树的混合专家大模型蜜罐统一优化部署系统")
    print("=" * 60)
    
    generator = TestDataGenerator(seed=42)
    generator.generate_all_scenarios()


if __name__ == "__main__":
    main()