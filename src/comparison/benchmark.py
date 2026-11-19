#!/usr/bin/env python3
"""
算法基准测试框架 - 用于对比不同蜜罐部署算法的性能
"""

import time
import json
import numpy as np
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

try:
    from src.core.module_b_ose import OSEOptimizer
    print(" OSEOptimizer 导入成功")
except ImportError as e:
    print(f" 导入 OSEOptimizer 失败: {e}")
    OSEOptimizer = None


@dataclass
class BenchmarkResult:
    """基准测试结果数据类"""
    algorithm_name: str
    scenario: str
    execution_time: float
    memory_usage: float  # MB
    solution_quality: float
    constraints_violated: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass 
class AlgorithmConfig:
    """算法配置数据类"""
    name: str
    parameters: Dict[str, Any]
    description: str = ""


class AlgorithmBenchmark:
    """算法基准测试主类"""
    
    def __init__(self, 
                 output_dir: str = "benchmark_results",
                 save_results: bool = True,
                 verbose: bool = True):
        """
        初始化基准测试
        
        Args:
            output_dir: 结果输出目录
            save_results: 是否保存结果到文件
            verbose: 是否显示详细输出
        """
        self.output_dir = Path(output_dir)
        self.save_results = save_results
        self.verbose = verbose
        self.results: List[BenchmarkResult] = []
        
        # 创建输出目录
        if save_results:
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _measure_memory_usage(self) -> float:
        """测量内存使用量（简化版本）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # 转换为MB
        except ImportError:
            # 如果psutil不可用，返回估计值
            return 0.0
    
    def _calculate_solution_quality(self, 
                                  selected_nodes: List[Dict],
                                  scenario_data: Dict[str, Any]) -> float:
        """计算解决方案质量"""
        if not selected_nodes:
            return 0.0
        
        # 基本质量指标：选择节点数量与场景需求的匹配度
        required_nodes = scenario_data.get('required_nodes', 0)
        if required_nodes > 0:
            node_match = 1.0 - abs(len(selected_nodes) - required_nodes) / required_nodes
        else:
            node_match = 1.0
        
        # 节点分布质量（如果有位置信息）
        if all('x' in node and 'y' in node for node in selected_nodes):
            # 计算节点间的平均距离
            positions = [(node['x'], node['y']) for node in selected_nodes]
            distances = []
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    dx = positions[i][0] - positions[j][0]
                    dy = positions[i][1] - positions[j][1]
                    distances.append(np.sqrt(dx**2 + dy**2))
            
            if distances:
                avg_distance = np.mean(distances)
                # 理想距离（假设均匀分布在100x100区域内）
                ideal_distance = 100 / (len(selected_nodes) ** 0.5)
                distance_quality = 1.0 - abs(avg_distance - ideal_distance) / ideal_distance
                node_match = (node_match + distance_quality) / 2
        
        return max(0.0, min(1.0, node_match))
    
    def _check_constraints(self, 
                          selected_nodes: List[Dict],
                          scenario_data: Dict[str, Any]) -> List[str]:
        """检查约束条件"""
        violated_constraints = []
        
        # 预算约束
        budget_limit = scenario_data.get('budget_limit', float('inf'))
        total_cost = sum(node.get('cost', 0) for node in selected_nodes)
        if total_cost > budget_limit:
            violated_constraints.append(f"预算超限: {total_cost:.2f} > {budget_limit}")
        
        # 节点数量约束
        max_nodes = scenario_data.get('max_nodes', float('inf'))
        if len(selected_nodes) > max_nodes:
            violated_constraints.append(f"节点数量超限: {len(selected_nodes)} > {max_nodes}")
        
        # 最小节点数量约束
        min_nodes = scenario_data.get('min_nodes', 0)
        if len(selected_nodes) < min_nodes:
            violated_constraints.append(f"节点数量不足: {len(selected_nodes)} < {min_nodes}")
        
        return violated_constraints
    
    def run_algorithm(self, 
                     algorithm_func: Callable,
                     algorithm_name: str,
                     scenario_data: Dict[str, Any],
                     algorithm_params: Dict[str, Any] = None) -> BenchmarkResult:
        """
        运行单个算法并收集性能指标
        
        Args:
            algorithm_func: 算法函数
            algorithm_name: 算法名称
            scenario_data: 场景数据
            algorithm_params: 算法参数
            
        Returns:
            基准测试结果
        """
        if algorithm_params is None:
            algorithm_params = {}
        
        if self.verbose:
            print(f" 运行算法: {algorithm_name}")
            print(f"   参数: {algorithm_params}")
        
        # 测量内存使用（之前）
        memory_before = self._measure_memory_usage()
        
        # 运行算法并计时
        start_time = time.perf_counter()
        
        try:
            # 执行算法
            result = algorithm_func(scenario_data, **algorithm_params)
            selected_nodes = result.get('selected_nodes', [])
            
            execution_time = time.perf_counter() - start_time
            
            # 测量内存使用（之后）
            memory_after = self._measure_memory_usage()
            memory_usage = memory_after - memory_before
            
            # 计算解决方案质量
            solution_quality = self._calculate_solution_quality(selected_nodes, scenario_data)
            
            # 检查约束条件
            violated_constraints = self._check_constraints(selected_nodes, scenario_data)
            
            # 收集其他指标
            metrics = {
                'nodes_selected': len(selected_nodes),
                'total_cost': sum(node.get('cost', 0) for node in selected_nodes),
                'avg_node_cost': np.mean([node.get('cost', 0) for node in selected_nodes]) if selected_nodes else 0,
                'std_node_cost': np.std([node.get('cost', 0) for node in selected_nodes]) if len(selected_nodes) > 1 else 0
            }
            
            # 创建结果对象
            benchmark_result = BenchmarkResult(
                algorithm_name=algorithm_name,
                scenario=scenario_data.get('name', 'unknown'),
                execution_time=execution_time,
                memory_usage=memory_usage,
                solution_quality=solution_quality,
                constraints_violated=violated_constraints,
                metrics=metrics
            )
            
            self.results.append(benchmark_result)
            
            if self.verbose:
                print(f" 完成: {algorithm_name}")
                print(f"   执行时间: {execution_time:.4f}秒")
                print(f"   内存使用: {memory_usage:.2f}MB")
                print(f"   解决方案质量: {solution_quality:.4f}")
                print(f"   选择节点数: {len(selected_nodes)}")
                if violated_constraints:
                    print(f"   违反约束: {len(violated_constraints)}个")
            
            return benchmark_result
            
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            
            if self.verbose:
                print(f" 算法执行失败: {algorithm_name}")
                print(f"   错误: {e}")
            
            # 创建失败结果
            benchmark_result = BenchmarkResult(
                algorithm_name=algorithm_name,
                scenario=scenario_data.get('name', 'unknown'),
                execution_time=execution_time,
                memory_usage=0.0,
                solution_quality=0.0,
                constraints_violated=[f"执行失败: {str(e)}"],
                metrics={'error': str(e)}
            )
            
            self.results.append(benchmark_result)
            return benchmark_result
    
    def run_comparison(self, 
                      algorithms: List[AlgorithmConfig],
                      scenario_data: Dict[str, Any]) -> List[BenchmarkResult]:
        """
        运行多个算法对比
        
        Args:
            algorithms: 算法配置列表
            scenario_data: 场景数据
            
        Returns:
            基准测试结果列表
        """
        results = []
        
        for algorithm_config in algorithms:
            # 这里需要根据算法名称选择实际的算法函数
            algorithm_func = self._get_algorithm_function(algorithm_config.name)
            
            if algorithm_func:
                result = self.run_algorithm(
                    algorithm_func=algorithm_func,
                    algorithm_name=algorithm_config.name,
                    scenario_data=scenario_data,
                    algorithm_params=algorithm_config.parameters
                )
                results.append(result)
            else:
                print(f"  警告: 找不到算法函数: {algorithm_config.name}")
        
        return results
    
    def _get_algorithm_function(self, algorithm_name: str) -> Optional[Callable]:
        """根据算法名称获取对应的算法函数"""
        # 这里应该根据实际的算法模块进行导入
        if algorithm_name == "random_k":
            try:
                from .random_k import RandomKAlgorithm
                def random_k_func(scenario_data, **kwargs):
                    k = kwargs.get('k', 5)
                    algorithm = RandomKAlgorithm(k=k)
                    candidate_nodes = scenario_data.get('steiner_candidates', [])
                    selected_nodes = algorithm.select_nodes(candidate_nodes)
                    return {'selected_nodes': selected_nodes}
                return random_k_func
            except ImportError:
                pass
        
        elif algorithm_name == "k_medoids":
            try:
                from .k_medoids import KMedoidsAlgorithm
                def k_medoids_func(scenario_data, **kwargs):
                    k = kwargs.get('k', 5)
                    algorithm = KMedoidsAlgorithm(k=k)
                    candidate_nodes = scenario_data.get('steiner_candidates', [])
                    terminal_nodes = scenario_data.get('terminal_nodes', [])
                    selected_nodes = algorithm.select_nodes(candidate_nodes, terminal_nodes)
                    return {'selected_nodes': selected_nodes}
                return k_medoids_func
            except ImportError:
                pass
        
        elif algorithm_name == "ose_optimizer" and OSEOptimizer is not None:
            def ose_optimizer_func(scenario_data, **kwargs):
                config_manager = kwargs.get('config_manager')
                algorithm = OSEOptimizer(config_manager=config_manager)
                candidate_nodes = scenario_data.get('steiner_candidates', [])
                terminal_nodes = scenario_data.get('terminal_nodes', [])
                edges = scenario_data.get('edges', [])
                attack_vectors = scenario_data.get('attack_vectors', [])
                solution, evaluation, history = algorithm.optimize(
                    candidate_nodes, terminal_nodes, edges, attack_vectors
                )
                return {
                    'selected_nodes': solution,
                    'evaluation': evaluation,
                    'history': history
                }
            return ose_optimizer_func
        
        return None
    
    def save_results_to_file(self, filename: Optional[str] = None) -> str:
        """保存基准测试结果到文件"""
        if not self.save_results:
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # 将结果转换为字典列表
        results_dict = []
        for result in self.results:
            result_dict = {
                'algorithm_name': result.algorithm_name,
                'scenario': result.scenario,
                'execution_time': result.execution_time,
                'memory_usage': result.memory_usage,
                'solution_quality': result.solution_quality,
                'constraints_violated': result.constraints_violated,
                'metrics': result.metrics,
                'timestamp': result.timestamp
            }
            results_dict.append(result_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def plot_results(self, output_filename: str = "benchmark_comparison.png"):
        """绘制基准测试结果对比图"""
        if not self.results:
            print("  没有结果数据可绘制")
            return
        
        # 按算法名称分组
        algorithms = {}
        for result in self.results:
            if result.algorithm_name not in algorithms:
                algorithms[result.algorithm_name] = []
            algorithms[result.algorithm_name].append(result)
        
        # 创建图形
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 提取数据
        algo_names = list(algorithms.keys())
        
        # 1. 执行时间对比
        exec_times = []
        for algo in algo_names:
            times = [r.execution_time for r in algorithms[algo]]
            exec_times.append(np.mean(times))
        
        axes[0, 0].bar(algo_names, exec_times, color='skyblue')
        axes[0, 0].set_title('平均执行时间对比')
        axes[0, 0].set_ylabel('时间(秒)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 解决方案质量对比
        qualities = []
        for algo in algo_names:
            quals = [r.solution_quality for r in algorithms[algo]]
            qualities.append(np.mean(quals))
        
        axes[0, 1].bar(algo_names, qualities, color='lightgreen')
        axes[0, 1].set_title('平均解决方案质量对比')
        axes[0, 1].set_ylabel('质量分数(0-1)')
        axes[0, 1].set_ylim(0, 1)
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. 内存使用对比
        memories = []
        for algo in algo_names:
            mems = [r.memory_usage for r in algorithms[algo]]
            memories.append(np.mean(mems))
        
        axes[1, 0].bar(algo_names, memories, color='lightcoral')
        axes[1, 0].set_title('平均内存使用对比')
        axes[1, 0].set_ylabel('内存(MB)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 4. 约束违反次数对比
        violations = []
        for algo in algo_names:
            viols = [len(r.constraints_violated) for r in algorithms[algo]]
            violations.append(np.mean(viols))
        
        axes[1, 1].bar(algo_names, violations, color='gold')
        axes[1, 1].set_title('平均约束违反次数对比')
        axes[1, 1].set_ylabel('违反次数')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图像
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f" 基准测试对比图已保存: {output_path}")
        
        # 显示图像
        plt.show()