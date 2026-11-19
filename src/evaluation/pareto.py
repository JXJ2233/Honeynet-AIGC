#!/usr/bin/env python3
"""
帕累托前沿分析模块
用于多目标优化中的帕累托前沿分析和可视化
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class ParetoSolution:
    """帕累托解决方案数据类"""
    solution_id: str
    objectives: Dict[str, float]  # 目标函数值
    variables: Dict[str, Any]  # 决策变量
    is_dominated: bool = False
    rank: int = 0
    crowding_distance: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        obj_str = ", ".join([f"{k}: {v:.4f}" for k, v in self.objectives.items()])
        return f"ParetoSolution(id={self.solution_id}, objectives={{{obj_str}}}, rank={self.rank})"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'solution_id': self.solution_id,
            'objectives': self.objectives,
            'variables': self.variables,
            'is_dominated': self.is_dominated,
            'rank': self.rank,
            'crowding_distance': self.crowding_distance,
            'metadata': self.metadata
        }


class ParetoAnalyzer:
    """
    帕累托前沿分析器
    用于识别和可视化多目标优化中的帕累托前沿
    """
    
    def __init__(self, objectives: List[str], minimize: bool = True):
        """
        初始化帕累托分析器
        
        Args:
            objectives: 目标函数名称列表
            minimize: 是否为最小化问题，False表示最大化
        """
        self.objectives = objectives
        self.minimize = minimize
        self.solutions: List[ParetoSolution] = []
        self.pareto_front: List[ParetoSolution] = []
        
    def add_solution(self, solution: ParetoSolution) -> None:
        """添加解决方案"""
        self.solutions.append(solution)
    
    def add_solutions(self, solutions: List[ParetoSolution]) -> None:
        """批量添加解决方案"""
        self.solutions.extend(solutions)
    
    def _dominates(self, sol1: ParetoSolution, sol2: ParetoSolution) -> bool:
        """
        判断sol1是否支配sol2
        
        对于最小化问题：sol1支配sol2当且仅当sol1在所有目标上都不差于sol2，
        且至少在一个目标上严格更好。
        """
        if self.minimize:
            # 检查sol1是否在所有目标上都不差于sol2
            not_worse = all(sol1.objectives[obj] <= sol2.objectives[obj] 
                           for obj in self.objectives)
            # 检查sol1是否至少在一个目标上严格更好
            strictly_better = any(sol1.objectives[obj] < sol2.objectives[obj]
                                 for obj in self.objectives)
            return not_worse and strictly_better
        else:
            # 最大化问题：符号相反
            not_worse = all(sol1.objectives[obj] >= sol2.objectives[obj]
                           for obj in self.objectives)
            strictly_better = any(sol1.objectives[obj] > sol2.objectives[obj]
                                 for obj in self.objectives)
            return not_worse and strictly_better
    
    def compute_pareto_front(self) -> List[ParetoSolution]:
        """计算帕累托前沿"""
        if not self.solutions:
            return []
        
        # 重置支配状态
        for solution in self.solutions:
            solution.is_dominated = False
        
        pareto_front = []
        
        for i, sol_i in enumerate(self.solutions):
            dominated = False
            
            for j, sol_j in enumerate(self.solutions):
                if i == j:
                    continue
                
                if self._dominates(sol_j, sol_i):
                    dominated = True
                    break
            
            if not dominated:
                sol_i.is_dominated = False
                pareto_front.append(sol_i)
            else:
                sol_i.is_dominated = True
        
        self.pareto_front = pareto_front
        return pareto_front
    
    def fast_non_dominated_sort(self) -> List[List[ParetoSolution]]:
        """
        快速非支配排序
        返回按支配层级分组的解决方案列表
        """
        if not self.solutions:
            return []
        
        # 初始化数据结构
        S: Dict[int, List[int]] = {}  # 被i支配的解决方案索引
        n: Dict[int, int] = {}  # 支配i的解决方案数量
        F: List[List[int]] = [[]]  # 前沿层级
        
        # 初始化
        for i in range(len(self.solutions)):
            S[i] = []
            n[i] = 0
        
        # 计算支配关系
        for i in range(len(self.solutions)):
            for j in range(len(self.solutions)):
                if i == j:
                    continue
                
                if self._dominates(self.solutions[i], self.solutions[j]):
                    S[i].append(j)
                elif self._dominates(self.solutions[j], self.solutions[i]):
                    n[i] += 1
            
            if n[i] == 0:
                self.solutions[i].rank = 0
                F[0].append(i)
        
        # 构建后续前沿
        i = 0
        while F[i]:
            Q = []
            for p in F[i]:
                for q in S[p]:
                    n[q] -= 1
                    if n[q] == 0:
                        self.solutions[q].rank = i + 1
                        Q.append(q)
            i += 1
            if Q:
                F.append(Q)
        
        # 按前沿层级分组返回
        fronts = []
        for front_indices in F:
            if front_indices:
                front = [self.solutions[idx] for idx in front_indices]
                fronts.append(front)
        
        # 第一前沿即为帕累托前沿
        if fronts:
            self.pareto_front = fronts[0]
        
        return fronts
    
    def compute_crowding_distance(self, front: List[ParetoSolution]) -> None:
        """
        计算拥挤距离
        用于在NSGA-II等算法中保持多样性
        """
        if not front:
            return
        
        # 初始化拥挤距离
        for solution in front:
            solution.crowding_distance = 0.0
        
        # 对每个目标计算拥挤距离
        for obj in self.objectives:
            # 按当前目标值排序
            front_sorted = sorted(front, key=lambda x: x.objectives[obj])
            
            # 边界个体的拥挤距离设为无穷大
            front_sorted[0].crowding_distance = float('inf')
            front_sorted[-1].crowding_distance = float('inf')
            
            # 计算中间个体的拥挤距离
            obj_min = front_sorted[0].objectives[obj]
            obj_max = front_sorted[-1].objectives[obj]
            
            if abs(obj_max - obj_min) < 1e-10:
                continue  # 避免除以零
            
            for i in range(1, len(front_sorted) - 1):
                prev_obj = front_sorted[i-1].objectives[obj]
                next_obj = front_sorted[i+1].objectives[obj]
                
                distance = (next_obj - prev_obj) / (obj_max - obj_min)
                front_sorted[i].crowding_distance += distance
    
    def get_pareto_front_metrics(self) -> Dict[str, Any]:
        """获取帕累托前沿的统计指标"""
        if not self.pareto_front:
            return {}
        
        metrics = {
            'num_solutions': len(self.pareto_front),
            'num_total_solutions': len(self.solutions),
            'pareto_ratio': len(self.pareto_front) / len(self.solutions) if self.solutions else 0,
            'objective_ranges': {},
            'objective_means': {},
            'objective_stds': {}
        }
        
        # 计算每个目标的统计信息
        for obj in self.objectives:
            values = [sol.objectives[obj] for sol in self.pareto_front]
            metrics['objective_ranges'][obj] = {
                'min': min(values),
                'max': max(values),
                'range': max(values) - min(values)
            }
            metrics['objective_means'][obj] = np.mean(values)
            metrics['objective_stds'][obj] = np.std(values)
        
        return metrics
    
    def plot_pareto_front(self, 
                         obj_x: str, 
                         obj_y: str, 
                         title: str = "帕累托前沿",
                         save_path: Optional[str] = None,
                         show_plot: bool = True) -> None:
        """
        绘制二维帕累托前沿
        
        Args:
            obj_x: X轴目标名称
            obj_y: Y轴目标名称
            title: 图表标题
            save_path: 保存路径，如果为None则不保存
            show_plot: 是否显示图表
        """
        if not self.solutions:
            print("  没有解决方案可绘制")
            return
        
        if obj_x not in self.objectives or obj_y not in self.objectives:
            print(f"  目标名称无效，可用目标: {self.objectives}")
            return
        
        # 计算帕累托前沿（如果尚未计算）
        if not self.pareto_front:
            self.compute_pareto_front()
        
        # 提取数据
        x_all = [sol.objectives[obj_x] for sol in self.solutions]
        y_all = [sol.objectives[obj_y] for sol in self.solutions]
        
        x_pareto = [sol.objectives[obj_x] for sol in self.pareto_front]
        y_pareto = [sol.objectives[obj_y] for sol in self.pareto_front]
        
        # 按X轴排序帕累托前沿点，便于绘制连线
        pareto_sorted = sorted(zip(x_pareto, y_pareto), key=lambda p: p[0])
        x_pareto_sorted = [p[0] for p in pareto_sorted]
        y_pareto_sorted = [p[1] for p in pareto_sorted]
        
        # 创建图表
        plt.figure(figsize=(10, 8))
        
        # 绘制所有解决方案
        plt.scatter(x_all, y_all, 
                   alpha=0.6, 
                   s=50, 
                   c='gray', 
                   label='所有解决方案',
                   edgecolors='black',
                   linewidth=0.5)
        
        # 绘制帕累托前沿
        plt.scatter(x_pareto, y_pareto,
                   alpha=0.9,
                   s=100,
                   c='red',
                   label='帕累托前沿',
                   edgecolors='darkred',
                   linewidth=1.5,
                   zorder=5)
        
        # 连接帕累托前沿点
        plt.plot(x_pareto_sorted, y_pareto_sorted,
                'r--',
                alpha=0.7,
                linewidth=2,
                label='帕累托边界')
        
        # 设置图表属性
        plt.xlabel(obj_x, fontsize=14)
        plt.ylabel(obj_y, fontsize=14)
        plt.title(title, fontsize=16, fontweight='bold')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(fontsize=12)
        
        # 如果是最大化问题，反转轴的方向
        if not self.minimize:
            plt.gca().invert_xaxis()
            plt.gca().invert_yaxis()
        
        # 添加统计信息文本
        metrics = self.get_pareto_front_metrics()
        if metrics:
            info_text = (f"帕累托前沿解决方案: {metrics['num_solutions']}\n"
                        f"总解决方案数: {metrics['num_total_solutions']}\n"
                        f"帕累托比例: {metrics['pareto_ratio']:.2%}")
            
            plt.text(0.02, 0.98, info_text,
                    transform=plt.gca().transAxes,
                    verticalalignment='top',
                    horizontalalignment='left',
                    fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f" 帕累托前沿图已保存到: {save_path}")
        
        # 显示图表
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_3d_pareto_front(self,
                            obj_x: str,
                            obj_y: str,
                            obj_z: str,
                            title: str = "三维帕累托前沿",
                            save_path: Optional[str] = None,
                            show_plot: bool = True) -> None:
        """
        绘制三维帕累托前沿
        
        Args:
            obj_x: X轴目标名称
            obj_y: Y轴目标名称
            obj_z: Z轴目标名称
            title: 图表标题
            save_path: 保存路径
            show_plot: 是否显示图表
        """
        if not self.solutions:
            print("  没有解决方案可绘制")
            return
        
        # 检查目标名称
        for obj in [obj_x, obj_y, obj_z]:
            if obj not in self.objectives:
                print(f"  目标名称无效: {obj}，可用目标: {self.objectives}")
                return
        
        # 计算帕累托前沿
        if not self.pareto_front:
            self.compute_pareto_front()
        
        try:
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            print("  需要安装 mpl_toolkits.mplot3d 以绘制3D图表")
            return
        
        # 提取数据
        x_all = [sol.objectives[obj_x] for sol in self.solutions]
        y_all = [sol.objectives[obj_y] for sol in self.solutions]
        z_all = [sol.objectives[obj_z] for sol in self.solutions]
        
        x_pareto = [sol.objectives[obj_x] for sol in self.pareto_front]
        y_pareto = [sol.objectives[obj_y] for sol in self.pareto_front]
        z_pareto = [sol.objectives[obj_z] for sol in self.pareto_front]
        
        # 创建3D图表
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # 绘制所有解决方案
        ax.scatter(x_all, y_all, z_all,
                  alpha=0.4,
                  s=30,
                  c='gray',
                  label='所有解决方案',
                  depthshade=True)
        
        # 绘制帕累托前沿
        ax.scatter(x_pareto, y_pareto, z_pareto,
                  alpha=0.9,
                  s=80,
                  c='red',
                  label='帕累托前沿',
                  depthshade=True)
        
        # 设置图表属性
        ax.set_xlabel(obj_x, fontsize=12)
        ax.set_ylabel(obj_y, fontsize=12)
        ax.set_zlabel(obj_z, fontsize=12)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend(fontsize=11)
        
        # 添加视角控制
        ax.view_init(elev=20, azim=45)
        
        plt.tight_layout()
        
        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f" 三维帕累托前沿图已保存到: {save_path}")
        
        # 显示图表
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def save_pareto_front(self, filepath: str) -> None:
        """保存帕累托前沿到文件"""
        if not self.pareto_front:
            print("  没有帕累托前沿可保存")
            return
        
        data = {
            'objectives': self.objectives,
            'minimize': self.minimize,
            'solutions': [sol.to_dict() for sol in self.pareto_front],
            'metrics': self.get_pareto_front_metrics()
        }
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f" 帕累托前沿已保存到: {filepath}")
    
    @classmethod
    def load_pareto_front(cls, filepath: str) -> 'ParetoAnalyzer':
        """从文件加载帕累托前沿"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analyzer = cls(data['objectives'], data['minimize'])
        
        for sol_dict in data['solutions']:
            solution = ParetoSolution(
                solution_id=sol_dict['solution_id'],
                objectives=sol_dict['objectives'],
                variables=sol_dict['variables'],
                is_dominated=sol_dict.get('is_dominated', False),
                rank=sol_dict.get('rank', 0),
                crowding_distance=sol_dict.get('crowding_distance', 0.0),
                metadata=sol_dict.get('metadata', {})
            )
            analyzer.add_solution(solution)
        
        analyzer.compute_pareto_front()
        return analyzer


def create_example_pareto_solutions() -> List[ParetoSolution]:
    """创建示例帕累托解决方案（用于测试）"""
    solutions = []
    
    # 创建一系列解决方案，模拟两个目标（成本和安全）的权衡
    for i in range(50):
        # 生成在两个目标上权衡的解决方案
        cost = 10 + np.random.rand() * 90  # 成本：10-100
        security = 0.1 + np.random.rand() * 0.9  # 安全性：0.1-1.0
        
        # 添加一些随机噪声
        cost += np.random.randn() * 5
        security += np.random.randn() * 0.05
        
        # 确保值在合理范围内
        cost = max(5, min(110, cost))
        security = max(0.05, min(1.0, security))
        
        solution = ParetoSolution(
            solution_id=f"sol_{i:03d}",
            objectives={
                'cost': cost,
                'security': security
            },
            variables={
                'nodes_selected': np.random.randint(3, 10),
                'total_budget': cost * 1000
            },
            metadata={
                'algorithm': np.random.choice(['GA', 'PSO', 'Random']),
                'iteration': i
            }
        )
        
        solutions.append(solution)
    
    return solutions


def main():
    """主函数 - 示例用法"""
    print("帕累托前沿分析模块示例")
    
    # 创建帕累托分析器
    analyzer = ParetoAnalyzer(objectives=['cost', 'security'], minimize=True)
    
    # 添加示例解决方案
    solutions = create_example_pareto_solutions()
    analyzer.add_solutions(solutions)
    
    # 计算帕累托前沿
    pareto_front = analyzer.compute_pareto_front()
    print(f" 找到 {len(pareto_front)} 个帕累托前沿解决方案")
    
    # 执行快速非支配排序
    fronts = analyzer.fast_non_dominated_sort()
    print(f" 非支配排序得到 {len(fronts)} 个前沿")
    
    # 计算拥挤距离
    analyzer.compute_crowding_distance(pareto_front)
    
    # 获取统计指标
    metrics = analyzer.get_pareto_front_metrics()
    print(f"帕累托比例: {metrics['pareto_ratio']:.2%}")
    
    # 绘制二维帕累托前沿
    analyzer.plot_pareto_front(
        obj_x='cost',
        obj_y='security',
        title='成本 vs 安全性 - 帕累托前沿',
        save_path='pareto_front_2d.png',
        show_plot=True
    )
    
    # 尝试绘制三维帕累托前沿（如果需要第三个目标）
    # 注意：这里我们只有两个目标，所以跳过3D绘图
    
    # 保存帕累托前沿
    analyzer.save_pareto_front('pareto_front.json')
    
    print(" 帕累托前沿分析完成")


if __name__ == "__main__":
    main()