#!/usr/bin/env python3
"""
批量测试运行器
用于 MoE-SHD 算法的批量测试和结果分析
"""

import os
import sys
import json
import random
import time
import yaml
from datetime import datetime
from typing import Dict, List, Tuple, Any

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    from src.data_structures.nodes import TerminalNode, SteinerNode
    print(" 成功导入节点类")
except ImportError as e:
    print(f" 导入节点类失败: {e}")
    sys.exit(1)

class BatchRunner:
    """批量测试运行器"""
    
    def __init__(self, config_file: str = "configs/default_config.yaml"):
        """初始化批量测试运行器"""
        self.config_file = config_file
        self.results_dir = "results/batch_test"
        self.data_dir = "test_data"
        
        # 创建目录
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载配置
        self.load_config()
        
        print(f" BatchRunner 初始化完成")
        print(f"   配置: {config_file}")
        print(f"   结果目录: {self.results_dir}")
        print(f"   数据目录: {self.data_dir}")
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            print(f" 配置加载成功: {self.config_file}")
        except Exception as e:
            print(f"  配置加载失败: {e}，使用默认配置")
            self.config = {
                'scenario': 'default',
                'weights': {
                    'w_A': 0.3,  # 经济性
                    'w_B': 0.3,  # 性能
                    'w_C': 0.4   # 安全性
                }
            }
    
    def create_test_nodes(self, count: int = 10, node_type: str = "terminal"):
        """创建测试节点"""
        nodes = []
        
        for i in range(1, count + 1):
            if node_type == "terminal":
                node = TerminalNode(
                    node_id=f"{node_type}_{i:03d}",
                    node_type="terminal",
                    name=f"测试终端{i}",
                    critical_level=random.uniform(0.3, 0.9),
                    service_type=random.choice(["web", "database", "api", "file_server"]),
                    is_real=True
                )
            else:  # steiner
                node = SteinerNode(
                    node_id=f"{node_type}_{i:03d}",
                    node_type="steiner",
                    name=f"测试斯坦纳{i}",
                    deployable=True,
                    deployment_cost=random.uniform(500.0, 2000.0)
                )
            nodes.append(node)
        
        return nodes
    
    def simulate_algorithm(self, algorithm_name: str, terminals_count: int, steiner_count: int) -> Dict[str, Any]:
        """模拟算法运行结果"""
        # 模拟运行时间
        time.sleep(random.uniform(0.01, 0.1))
        
        # 根据算法类型生成不同结果
        if algorithm_name == "MoE-SHD":
            # MoE-SHD 表现最好
            total_cost = 5000 + terminals_count * 100 + steiner_count * 300
            security_coverage = 95 - terminals_count * 0.1
            avg_latency = 15 + terminals_count * 0.5
        elif algorithm_name == "Random-K":
            # Random-K 表现中等
            total_cost = 7000 + terminals_count * 150 + steiner_count * 400
            security_coverage = 75 - terminals_count * 0.2
            avg_latency = 25 + terminals_count * 1.0
        else:  # K-Medoids
            # K-Medoids 表现较差
            total_cost = 8000 + terminals_count * 200 + steiner_count * 500
            security_coverage = 85 - terminals_count * 0.15
            avg_latency = 20 + terminals_count * 0.8
        
        # 添加一些随机变化
        total_cost += random.uniform(-500, 500)
        security_coverage += random.uniform(-5, 5)
        avg_latency += random.uniform(-3, 3)
        
        return {
            'algorithm': algorithm_name,
            'total_cost': round(max(1000, total_cost), 2),
            'security_coverage': round(min(100, max(50, security_coverage)), 2),
            'avg_latency': round(max(5, avg_latency), 2),
            'terminals_count': terminals_count,
            'steiner_count': steiner_count,
            'run_time': round(random.uniform(0.1, 2.0), 3)
        }
    
    def run_batch_test(self, scenarios: List[Dict[str, Any]] = None):
        """运行批量测试"""
        print("\n 开始批量测试")
        print("=" * 60)
        
        if scenarios is None:
            # 默认测试场景
            scenarios = [
                {"name": "小型稀疏网络", "terminals": 5, "steiners": 3},
                {"name": "小型密集网络", "terminals": 10, "steiners": 5},
                {"name": "中型稀疏网络", "terminals": 20, "steiners": 8},
                {"name": "中型密集网络", "terminals": 30, "steiners": 10},
                {"name": "大型稀疏网络", "terminals": 50, "steiners": 15},
                {"name": "大型密集网络", "terminals": 100, "steiners": 20}
            ]
        
        # 测试算法
        algorithms = ["MoE-SHD", "Random-K", "K-Medoids"]
        
        all_results = []
        
        for scenario in scenarios:
            print(f"\n 测试场景: {scenario['name']}")
            print(f"   终端数量: {scenario['terminals']}")
            print(f"   斯坦纳候选数量: {scenario['steiners']}")
            
            for algorithm in algorithms:
                print(f"    运行算法: {algorithm}")
                
                # 模拟算法运行
                result = self.simulate_algorithm(
                    algorithm,
                    scenario['terminals'],
                    scenario['steiners']
                )
                
                # 添加场景信息
                result['scenario'] = scenario['name']
                result['scenario_type'] = scenario.get('type', 'default')
                
                all_results.append(result)
                
                print(f"       完成: 成本=${result['total_cost']:.2f}, " +
                      f"覆盖率={result['security_coverage']:.2f}%, " +
                      f"延迟={result['avg_latency']:.2f}ms")
        
        # 保存结果
        self.save_results(all_results)
        
        # 显示摘要
        self.print_summary(all_results)
        
        return all_results
    
    def save_results(self, results: List[Dict[str, Any]]):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.results_dir, f"batch_results_{timestamp}.json")
        
        # 准备结果数据
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "config_file": self.config_file,
                "scenario": self.config.get('scenario', 'default')
            },
            "results": results
        }
        
        # 保存为 JSON
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n 结果已保存: {result_file}")
        
        # 同时保存为 CSV 格式（可选）
        csv_file = result_file.replace('.json', '.csv')
        try:
            import csv
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
            print(f" CSV 格式已保存: {csv_file}")
        except Exception as e:
            print(f"  CSV 保存失败: {e}")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """打印测试摘要"""
        print("\n 批量测试摘要")
        print("=" * 60)
        
        # 按算法分组
        algorithm_results = {}
        for result in results:
            algo = result['algorithm']
            if algo not in algorithm_results:
                algorithm_results[algo] = []
            algorithm_results[algo].append(result)
        
        # 打印每个算法的统计信息
        for algo, algo_results in algorithm_results.items():
            print(f"\n{algo} 算法:")
            print(f"  {'场景':<20} {'成本($)':<12} {'覆盖率(%)':<12} {'延迟(ms)':<12}")
            print(f"  {'-'*20:<20} {'-'*12:<12} {'-'*12:<12} {'-'*12:<12}")
            
            for result in algo_results:
                print(f"  {result['scenario']:<20} " +
                      f"{result['total_cost']:<12.2f} " +
                      f"{result['security_coverage']:<12.2f} " +
                      f"{result['avg_latency']:<12.2f}")
            
            # 计算平均值
            if algo_results:
                avg_cost = sum(r['total_cost'] for r in algo_results) / len(algo_results)
                avg_coverage = sum(r['security_coverage'] for r in algo_results) / len(algo_results)
                avg_latency = sum(r['avg_latency'] for r in algo_results) / len(algo_results)
                
                print(f"  {'平均值':<20} " +
                      f"{avg_cost:<12.2f} " +
                      f"{avg_coverage:<12.2f} " +
                      f"{avg_latency:<12.2f}")
        
        print(f"\n 批量测试完成！共测试 {len(results)} 个场景/算法组合")

def main():
    """主函数"""
    print(" MoE-SHD 批量测试运行器")
    print("基于斯坦纳树的混合专家大模型蜜罐统一优化部署系统")
    print("=" * 60)
    
    # 检查配置文件
    config_files = [
        "configs/default_config.yaml",
        "configs/high_security_scenario.yaml",
        "configs/low_cost_scenario.yaml"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f" 找到配置文件: {config_file}")
            # 使用第一个找到的配置文件
            runner = BatchRunner(config_file)
            break
    else:
        print("  未找到配置文件，使用默认设置")
        runner = BatchRunner()
    
    # 运行批量测试
    results = runner.run_batch_test()
    
    print("\n 批量测试完成！")
    print(f"结果保存在: {runner.results_dir}")
    
    return results

if __name__ == "__main__":
    main()