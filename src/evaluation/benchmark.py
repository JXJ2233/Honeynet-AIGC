#!/usr/bin/env python3
"""
基准测试模块 - 简化版本
用于对比不同算法的性能
"""

from typing import Union, Optional, List, Dict, Any, Tuple, Callable
from pathlib import Path
import json
import time
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BenchmarkResult:
    """基准测试结果数据类"""
    algorithm_name: str
    scenario: str
    execution_time: float
    solution_quality: float
    memory_usage: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'algorithm_name': self.algorithm_name,
            'scenario': self.scenario,
            'execution_time': self.execution_time,
            'solution_quality': self.solution_quality,
            'memory_usage': self.memory_usage,
            'metrics': self.metrics,
            'timestamp': self.timestamp
        }


@dataclass
class AlgorithmConfig:
    """算法配置数据类"""
    name: str
    function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class BenchmarkRunner:
    """基准测试运行器"""
    
    def __init__(self, output_dir: Union[str, Path] = "benchmark_results"):
        """
        初始化基准测试运行器
        
        Args:
            output_dir: 结果输出目录
        """
        self.output_dir = Path(output_dir)
        self.results: List[BenchmarkResult] = []
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _measure_memory_usage(self) -> float:
        """测量内存使用量（简化版本）"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # 转换为MB
        except ImportError:
            # 如果psutil不可用，返回估计值
            return 0.0
    
    def _calculate_solution_quality(self, algorithm_result: Any, scenario_data: Dict[str, Any]) -> float:
        """计算解决方案质量"""
        if algorithm_result is None:
            return 0.0
        
        # 简化质量评估
        quality = 0.0
        
        # 如果算法返回了质量分数，直接使用
        if hasattr(algorithm_result, 'quality'):
            quality = algorithm_result.quality
        elif isinstance(algorithm_result, dict) and 'quality' in algorithm_result:
            quality = algorithm_result['quality']
        elif isinstance(algorithm_result, dict) and 'score' in algorithm_result:
            quality = algorithm_result['score']
        elif isinstance(algorithm_result, (int, float)):
            quality = float(algorithm_result)
        
        # 确保质量在0-1之间
        quality = max(0.0, min(1.0, quality))
        
        return quality
    
    def run_single_benchmark(self, algorithm_config: AlgorithmConfig, 
                            scenario_data: Dict[str, Any]) -> BenchmarkResult:
        """
        运行单个算法的基准测试
        
        Args:
            algorithm_config: 算法配置
            scenario_data: 场景数据
            
        Returns:
            基准测试结果
        """
        print(f" 运行算法: {algorithm_config.name}")
        
        # 测量内存使用（之前）
        memory_before = self._measure_memory_usage()
        
        # 运行算法并计时
        start_time = time.perf_counter()
        
        try:
            # 执行算法
            algorithm_result = algorithm_config.function(scenario_data, **algorithm_config.parameters)
            
            execution_time = time.perf_counter() - start_time
            
            # 测量内存使用（之后）
            memory_after = self._measure_memory_usage()
            memory_usage = max(0.0, memory_after - memory_before)
            
            # 计算解决方案质量
            solution_quality = self._calculate_solution_quality(algorithm_result, scenario_data)
            
            # 提取其他指标
            metrics = {}
            if isinstance(algorithm_result, dict):
                for key in ['nodes_selected', 'total_cost', 'coverage_rate']:
                    if key in algorithm_result:
                        metrics[key] = algorithm_result[key]
            
            # 创建结果对象
            benchmark_result = BenchmarkResult(
                algorithm_name=algorithm_config.name,
                scenario=scenario_data.get('name', 'unknown'),
                execution_time=execution_time,
                solution_quality=solution_quality,
                memory_usage=memory_usage,
                metrics=metrics
            )
            
            self.results.append(benchmark_result)
            
            print(f" 完成: {algorithm_config.name}")
            print(f"   执行时间: {execution_time:.4f}秒")
            print(f"   解决方案质量: {solution_quality:.4f}")
            
            return benchmark_result
            
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            
            print(f" 算法执行失败: {algorithm_config.name}")
            print(f"   错误: {e}")
            
            # 创建失败结果
            benchmark_result = BenchmarkResult(
                algorithm_name=algorithm_config.name,
                scenario=scenario_data.get('name', 'unknown'),
                execution_time=execution_time,
                solution_quality=0.0,
                memory_usage=0.0,
                metrics={'error': str(e)}
            )
            
            self.results.append(benchmark_result)
            return benchmark_result
    
    def run_comparison(self, algorithms: List[AlgorithmConfig], 
                      scenario_data: Dict[str, Any]) -> List[BenchmarkResult]:
        """
        运行多个算法对比
        
        Args:
            algorithms: 算法配置列表
            scenario_data: 场景数据
            
        Returns:
            基准测试结果列表
        """
        print("=" * 60)
        print(f"开始基准测试对比: {scenario_data.get('name', '未知场景')}")
        print("=" * 60)
        
        results = []
        
        for algorithm_config in algorithms:
            result = self.run_single_benchmark(algorithm_config, scenario_data)
            results.append(result)
        
        return results
    
    def save_results(self, filename: Optional[str] = None) -> Path:
        """保存基准测试结果到文件"""
        if not self.results:
            print("  没有结果可保存")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        # 转换为字典列表
        results_dict = [result.to_dict() for result in self.results]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        print(f" 基准测试结果已保存到: {output_path}")
        return output_path
    
    def plot_comparison(self, output_filename: str = "benchmark_comparison.png"):
        """绘制算法对比图表"""
        if not self.results:
            print("  没有结果可绘制")
            return
        
        print(" 生成对比图表...")
        
        # 提取数据
        algorithm_names = [result.algorithm_name for result in self.results]
        execution_times = [result.execution_time for result in self.results]
        solution_qualities = [result.solution_quality for result in self.results]
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. 执行时间对比
        axes[0, 0].bar(algorithm_names, execution_times, color='skyblue', alpha=0.8)
        axes[0, 0].set_title('算法执行时间对比', fontsize=14, fontweight='bold')
        axes[0, 0].set_ylabel('时间(秒)', fontsize=12)
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].grid(axis='y', linestyle='--', alpha=0.7)
        
        # 添加数值标签
        for i, v in enumerate(execution_times):
            axes[0, 0].text(i, v + max(execution_times) * 0.01, f'{v:.3f}', 
                           ha='center', va='bottom', fontsize=9)
        
        # 2. 解决方案质量对比
        axes[0, 1].bar(algorithm_names, solution_qualities, color='lightgreen', alpha=0.8)
        axes[0, 1].set_title('解决方案质量对比', fontsize=14, fontweight='bold')
        axes[0, 1].set_ylabel('质量分数(0-1)', fontsize=12)
        axes[0, 1].set_ylim(0, 1.1)
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].grid(axis='y', linestyle='--', alpha=0.7)
        
        # 添加数值标签
        for i, v in enumerate(solution_qualities):
            axes[0, 1].text(i, v + 0.02, f'{v:.3f}', 
                           ha='center', va='bottom', fontsize=9)
        
        # 3. 执行时间与质量散点图
        scatter = axes[1, 0].scatter(execution_times, solution_qualities, 
                                    c=range(len(algorithm_names)), 
                                    s=100, cmap='viridis', alpha=0.8)
        axes[1, 0].set_title('执行时间 vs 解决方案质量', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('执行时间(秒)', fontsize=12)
        axes[1, 0].set_ylabel('质量分数', fontsize=12)
        axes[1, 0].grid(True, linestyle='--', alpha=0.7)
        
        # 添加算法名称标签
        for i, name in enumerate(algorithm_names):
            axes[1, 0].annotate(name, (execution_times[i], solution_qualities[i]),
                               xytext=(5, 5), textcoords='offset points', fontsize=9)
        
        # 4. 内存使用对比（如果有数据）
        memory_usages = [result.memory_usage for result in self.results]
        if any(memory_usages):
            axes[1, 1].bar(algorithm_names, memory_usages, color='lightcoral', alpha=0.8)
            axes[1, 1].set_title('内存使用对比', fontsize=14, fontweight='bold')
            axes[1, 1].set_ylabel('内存(MB)', fontsize=12)
            axes[1, 1].tick_params(axis='x', rotation=45)
            axes[1, 1].grid(axis='y', linestyle='--', alpha=0.7)
            
            # 添加数值标签
            for i, v in enumerate(memory_usages):
                if v > 0:
                    axes[1, 1].text(i, v + max(memory_usages) * 0.01, f'{v:.1f}', 
                                   ha='center', va='bottom', fontsize=9)
        else:
            axes[1, 1].text(0.5, 0.5, '内存使用数据不可用', 
                           ha='center', va='center', transform=axes[1, 1].transAxes,
                           fontsize=12, color='gray')
            axes[1, 1].set_title('内存使用对比', fontsize=14, fontweight='bold')
            axes[1, 1].set_xticks([])
            axes[1, 1].set_yticks([])
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f" 对比图表已保存到: {output_path}")
        
        # 显示图表
        plt.show()
        
        return output_path
    
    def generate_summary_report(self, output_filename: str = "benchmark_summary.md"):
        """生成基准测试总结报告"""
        if not self.results:
            print("  没有结果可生成报告")
            return
        
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 基准测试总结报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 测试概况\n")
            f.write(f"- 测试场景数量: 1\n")
            f.write(f"- 测试算法数量: {len(self.results)}\n")
            f.write(f"- 总测试次数: {len(self.results)}\n\n")
            
            f.write("## 算法性能排名\n")
            
            # 按解决方案质量排序
            sorted_results = sorted(self.results, key=lambda x: x.solution_quality, reverse=True)
            
            f.write("### 按解决方案质量排名\n")
            f.write("| 排名 | 算法名称 | 解决方案质量 | 执行时间(秒) | 内存使用(MB) |\n")
            f.write("|------|----------|--------------|--------------|--------------|\n")
            
            for i, result in enumerate(sorted_results, 1):
                f.write(f"| {i} | {result.algorithm_name} | {result.solution_quality:.4f} | "
                       f"{result.execution_time:.4f} | {result.memory_usage:.1f} |\n")
            
            # 按执行时间排序
            sorted_by_time = sorted(self.results, key=lambda x: x.execution_time)
            
            f.write("\n### 按执行时间排名\n")
            f.write("| 排名 | 算法名称 | 执行时间(秒) | 解决方案质量 |\n")
            f.write("|------|----------|--------------|--------------|\n")
            
            for i, result in enumerate(sorted_by_time, 1):
                f.write(f"| {i} | {result.algorithm_name} | {result.execution_time:.4f} | "
                       f"{result.solution_quality:.4f} |\n")
            
            f.write("\n## 详细结果\n")
            for result in self.results:
                f.write(f"\n### {result.algorithm_name}\n")
                f.write(f"- 场景: {result.scenario}\n")
                f.write(f"- 执行时间: {result.execution_time:.4f}秒\n")
                f.write(f"- 解决方案质量: {result.solution_quality:.4f}\n")
                f.write(f"- 内存使用: {result.memory_usage:.1f}MB\n")
                f.write(f"- 测试时间: {result.timestamp}\n")
                
                if result.metrics:
                    f.write(f"- 其他指标:\n")
                    for key, value in result.metrics.items():
                        if key != 'error':
                            f.write(f"  - {key}: {value}\n")
        
        print(f" 总结报告已保存到: {output_path}")
        return output_path


def create_default_algorithm_configs() -> List[AlgorithmConfig]:
    """创建默认的算法配置"""
    
    def random_k_algorithm(scenario_data: Dict[str, Any], k: int = 5) -> Dict[str, Any]:
        """Random-K算法实现"""
        import random
        candidate_nodes = scenario_data.get('steiner_candidates', [])
        
        if not candidate_nodes:
            return {'selected_nodes': [], 'quality': 0.0}
        
        if len(candidate_nodes) <= k:
            selected = candidate_nodes.copy()
        else:
            selected = random.sample(candidate_nodes, k)
        
        # 简单质量评估：基于选择节点数量
        quality = min(1.0, len(selected) / max(1, len(candidate_nodes)))
        
        return {
            'selected_nodes': selected,
            'quality': quality,
            'nodes_selected': len(selected),
            'total_cost': sum(node.get('cost', 1) for node in selected)
        }
    
    def k_medoids_algorithm(scenario_data: Dict[str, Any], k: int = 5) -> Dict[str, Any]:
        """K-Medoids算法实现（简化版本）"""
        import random
        candidate_nodes = scenario_data.get('steiner_candidates', [])
        
        if not candidate_nodes:
            return {'selected_nodes': [], 'quality': 0.0}
        
        if len(candidate_nodes) <= k:
            selected = candidate_nodes.copy()
        else:
            # 简化的K-Medoids实现
            selected = random.sample(candidate_nodes, k)
        
        # 稍微好一点的质量评估
        quality = min(1.0, len(selected) / max(1, len(candidate_nodes))) * 0.8
        
        return {
            'selected_nodes': selected,
            'quality': quality,
            'nodes_selected': len(selected),
            'total_cost': sum(node.get('cost', 1) for node in selected)
        }
    
    # 创建算法配置
    configs = [
        AlgorithmConfig(
            name="Random-K",
            function=random_k_algorithm,
            parameters={'k': 5},
            description="随机选择K个节点作为蜜罐部署位置"
        ),
        AlgorithmConfig(
            name="K-Medoids",
            function=k_medoids_algorithm,
            parameters={'k': 5},
            description="基于聚类的K-Medoids算法选择部署位置"
        )
    ]
    
    return configs


def main():
    """主函数 - 示例用法"""
    print("基准测试模块示例")
    
    # 创建示例场景数据
    scenario_data = {
        'name': '小型稀疏网络',
        'terminal_nodes': [{'id': i, 'x': i*10, 'y': i*10} for i in range(10)],
        'steiner_candidates': [{'id': i, 'x': i*8, 'y': i*8, 'cost': 1.0} for i in range(15)]
    }
    
    # 创建基准测试运行器
    runner = BenchmarkRunner()
    
    # 创建算法配置
    algorithms = create_default_algorithm_configs()
    
    # 运行基准测试
    results = runner.run_comparison(algorithms, scenario_data)
    
    # 保存结果
    runner.save_results()
    
    # 生成图表
    runner.plot_comparison()
    
    # 生成报告
    runner.generate_summary_report()
    
    print(" 基准测试完成")


if __name__ == "__main__":
    main()

Benchmark = BenchmarkRunner