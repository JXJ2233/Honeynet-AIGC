import json
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib import cm
from collections import defaultdict
import os
from datetime import datetime
import pandas as pd
class GateMapper:
    """
    门控偏好映射器：根据攻击特征选择专家模板
    """
    def __init__(self, templates: Dict[str, dict]):
        self.templates = templates
        # 可以训练一个分类器或使用规则
        self.attack_to_template = {
            'scanning': 'scanning',
            'lateral': 'lateral',
            'priv': 'privilege',
            'exfil': 'exfil',
            'ddos': 'ddos',
        }

    def get_template(self, attack_type: str, attack_features: dict) -> str:
        """
        根据攻击类型和特征选择模板名称
        """
        base = self.attack_to_template.get(attack_type, 'default')
        # 可以根据特征微调，例如攻击速率高时切换到更激进的模板
        if attack_features.get('rate', 0) > 10:
            base = base + '_aggressive'
        return self.templates.get(base, self.templates['default'])
class AttackVisualization:
    """攻击模拟结果可视化系统（纯matplotlib版）"""
    
    def __init__(self, results_file="realistic_algorithm_results.json"):
        self.results_file = results_file
        self.comparison_data = None
        self.algorithm_logs = {}
        
    def load_data(self):
        """加载数据"""
        print(" 加载数据...")
        
        # 加载对比结果
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r', encoding='utf-8') as f:
                self.comparison_data = json.load(f)
            print(f" 已加载对比结果: {self.results_file}")
        else:
            print(f" 对比结果文件不存在: {self.results_file}")
        
        # 加载各算法的攻击日志
        algorithms = ['random-k', 'k-medoids', 'moe-shd']
        for algo in algorithms:
            log_file = f"attack_logs_{algo}.json"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    self.algorithm_logs[algo] = json.load(f)
                print(f" 已加载 {algo} 日志: {log_file}")
            else:
                print(f"  日志文件不存在: {log_file}")
    
    def create_comparison_dashboard(self):
        """创建算法对比仪表盘"""
        if not self.comparison_data:
            print(" 没有对比数据可显示")
            return
        
        results = self.comparison_data.get('algorithm_results', {})
        summary = self.comparison_data.get('comparison_summary', {})
        
        if not results:
            print(" 对比结果数据为空")
            return
        
        # 创建仪表盘（2行3列）
        fig = plt.figure(figsize=(18, 12))
        fig.suptitle('网络安全攻防模拟 - 算法对比分析', fontsize=20, fontweight='bold')
        
        # 1. 触碰概率对比
        ax1 = plt.subplot(2, 3, 1)
        self._plot_touch_probability_comparison(ax1, results, summary)
        
        # 2. 捕获延迟对比
        ax2 = plt.subplot(2, 3, 2)
        self._plot_capture_latency_comparison(ax2, results)
        
        # 3. 斯坦纳树性能
        ax3 = plt.subplot(2, 3, 3)
        self._plot_steiner_performance(ax3, results)
        
        # 4. MoE专家系统性能
        ax4 = plt.subplot(2, 3, 4)
        self._plot_moe_performance(ax4, results)
        
        # 5. 攻击类型分布
        ax5 = plt.subplot(2, 3, 5)
        self._plot_attack_type_distribution(ax5, results)
        
        # 6. 蜜罐触发热力图
        ax6 = plt.subplot(2, 3, 6)
        self._plot_honeypot_heatmap(ax6, results)
        
        plt.tight_layout()
        plt.savefig('algorithm_comparison_dashboard.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(" 对比仪表盘已保存: algorithm_comparison_dashboard.png")
    
    def _plot_touch_probability_comparison(self, ax, results, summary):
        """绘制触碰概率对比图"""
        algorithms = ['random-k', 'k-medoids', 'moe-shd']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        overall_tp = []
        scanning_tp = []
        lateral_tp = []
        
        for algo in algorithms:
            if algo in results:
                metrics = results[algo]
                overall_tp.append(metrics.get('touch_probability', 0) * 100)
                
                # 获取按攻击类型的触碰概率
                tp_by_type = metrics.get('touch_probability_by_type', {})
                scanning_tp.append(tp_by_type.get('scanning', 0) * 100)
                lateral_tp.append(tp_by_type.get('lateral_movement', 0) * 100)
        
        x = np.arange(len(algorithms))
        width = 0.25
        
        ax.bar(x - width, overall_tp, width, label='整体触碰率', color=colors[0], alpha=0.8)
        ax.bar(x, scanning_tp, width, label='扫描攻击触碰率', color=colors[1], alpha=0.8)
        ax.bar(x + width, lateral_tp, width, label='横向移动触碰率', color=colors[2], alpha=0.8)
        
        ax.set_xlabel('部署算法')
        ax.set_ylabel('触碰概率 (%)')
        ax.set_title('蜜罐触碰概率对比')
        ax.set_xticks(x)
        ax.set_xticklabels(['Random-K', 'K-Medoids', 'MoE-SHD'])
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, v in enumerate(overall_tp):
            ax.text(i - width, v + 1, f'{v:.1f}%', ha='center', fontsize=9)
        
        # 添加改进百分比
        if 'key_findings' in summary:
            for finding in summary['key_findings']:
                if '提升' in finding:
                    ax.text(0.02, 0.95, finding, transform=ax.transAxes, 
                           fontsize=8, verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_capture_latency_comparison(self, ax, results):
        """绘制捕获延迟对比图"""
        algorithms = ['random-k', 'k-medoids', 'moe-shd']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        mean_latency = []
        std_latency = []
        
        for algo in algorithms:
            if algo in results:
                metrics = results[algo]
                mean_latency.append(metrics.get('capture_latency_mean', 0))
                std_latency.append(metrics.get('capture_latency_std', 0))
        
        x = np.arange(len(algorithms))
        
        # 柱状图显示均值，误差线显示标准差
        bars = ax.bar(x, mean_latency, color=colors, alpha=0.7, yerr=std_latency, 
                      capsize=5, error_kw={'elinewidth': 2, 'capthick': 2})
        
        ax.set_xlabel('部署算法')
        ax.set_ylabel('捕获延迟 (攻击步数)')
        ax.set_title('平均捕获延迟对比')
        ax.set_xticks(x)
        ax.set_xticklabels(['Random-K', 'K-Medoids', 'MoE-SHD'])
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, mean, std in zip(bars, mean_latency, std_latency):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{mean:.1f}±{std:.1f}', ha='center', va='bottom', fontsize=9)
    
    def _plot_steiner_performance(self, ax, results):
        """绘制斯坦纳树性能图"""
        if 'moe-shd' not in results:
            ax.text(0.5, 0.5, 'MoE-SHD 数据不可用', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('斯坦纳树性能')
            return
        
        moe_metrics = results['moe-shd']
        
        # 提取斯坦纳相关指标
        steiner_latency_steps = moe_metrics.get('steiner_capture_latency_mean_steps', 0)
        steiner_latency_time = moe_metrics.get('steiner_capture_latency_mean_time', 0)
        
        # 计算斯坦纳节点效率
        steiner_nodes = []
        steiner_rates = []
        
        honeypot_effectiveness = moe_metrics.get('honeypot_effectiveness', {})
        for node, data in honeypot_effectiveness.items():
            if data.get('is_steiner', False):
                steiner_nodes.append(node)
                steiner_rates.append(data.get('trigger_rate', 0) * 100)
        
        if not steiner_nodes:
            ax.text(0.5, 0.5, '无斯坦纳节点数据', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('斯坦纳树性能')
            return
        
        # 创建子图
        ax1 = ax
        
        # 绘制斯坦纳节点触发率
        x_pos = np.arange(len(steiner_nodes))
        colors = cm.viridis(np.linspace(0.3, 0.9, len(steiner_nodes)))
        
        bars = ax1.bar(x_pos, steiner_rates, color=colors, alpha=0.8)
        ax1.set_xlabel('斯坦纳节点')
        ax1.set_ylabel('触发率 (%)')
        ax1.set_title('斯坦纳节点触发效率')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels([f'ST-{i}' for i in range(len(steiner_nodes))], rotation=45)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 添加延迟信息
        info_text = f'平均捕获延迟:\n{steiner_latency_steps:.1f} 步\n{steiner_latency_time:.1f} 秒'
        ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # 添加数值标签
        for bar, rate in zip(bars, steiner_rates):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontsize=8)
    
    def _plot_moe_performance(self, ax, results):
        """绘制MoE专家系统性能图"""
        if 'moe-shd' not in results:
            ax.text(0.5, 0.5, 'MoE-SHD 数据不可用', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('MoE专家系统性能')
            return
        
        moe_metrics = results['moe-shd'].get('moe_metrics', {})
        
        if not moe_metrics:
            ax.text(0.5, 0.5, 'MoE指标数据为空', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('MoE专家系统性能')
            return
        
        # 提取MoE指标
        fp_rate = moe_metrics.get('false_positive_rate', 0) * 100
        fn_rate = moe_metrics.get('false_negative_rate', 0) * 100
        accuracy = 100 - fp_rate - fn_rate
        
        # 专家性能数据
        expert_performance = moe_metrics.get('expert_performance', {})
        
        if expert_performance:
            # 创建子图
            ax1 = ax
            
            # 绘制误报/漏报率
            error_rates = [fp_rate, fn_rate]
            error_labels = ['误报率', '漏报率']
            colors = ['#FF9999', '#99CCFF']
            
            bars1 = ax1.bar([0, 1], error_rates, color=colors, alpha=0.8)
            ax1.set_xlabel('错误类型')
            ax1.set_ylabel('错误率 (%)')
            ax1.set_title('MoE专家系统错误率')
            ax1.set_xticks([0, 1])
            ax1.set_xticklabels(error_labels)
            ax1.grid(True, alpha=0.3, axis='y')
            
            # 添加准确率信息
            info_text = f'整体准确率: {accuracy:.1f}%'
            ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes,
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
            
            # 添加数值标签
            for bar, rate in zip(bars1, error_rates):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
    
    def _plot_attack_type_distribution(self, ax, results):
        """绘制攻击类型分布图"""
        if 'moe-shd' not in results:
            ax.text(0.5, 0.5, 'MoE-SHD 数据不可用', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('攻击类型分布')
            return
        
        moe_metrics = results['moe-shd']
        attack_dist = moe_metrics.get('attack_type_distribution', {})
        
        if not attack_dist:
            ax.text(0.5, 0.5, '攻击类型数据为空', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('攻击类型分布')
            return
        
        # 处理攻击类型名称
        attack_types = []
        counts = []
        
        for atk_type, count in attack_dist.items():
            # 转换类型名称
            type_names = {
                'scanning': '扫描',
                'lateral_movement': '横向移动',
                'privilege_escalation': '权限提升',
                'data_exfiltration': '数据窃取',
                'ddos': 'DDoS'
            }
            display_name = type_names.get(atk_type, atk_type)
            attack_types.append(display_name)
            counts.append(count)
        
        # 计算百分比
        total = sum(counts)
        percentages = [count/total*100 for count in counts]
        
        # 颜色
        colors = cm.Set3(np.linspace(0, 1, len(attack_types)))
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(percentages, labels=attack_types, 
                                         autopct='%1.1f%%', startangle=90,
                                         colors=colors, explode=[0.05]*len(attack_types))
        
        ax.set_title('攻击类型分布')
        
        # 美化文本
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)
        
        # 添加总数信息
        ax.text(0, -1.2, f'总攻击次数: {total}', ha='center', va='center', fontsize=10)
    
    def _plot_honeypot_heatmap(self, ax, results):
        """绘制蜜罐触发热力图"""
        if 'moe-shd' not in results:
            ax.text(0.5, 0.5, 'MoE-SHD 数据不可用', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('蜜罐触发热力图')
            return
        
        honeypot_effectiveness = results['moe-shd'].get('honeypot_effectiveness', {})
        
        if not honeypot_effectiveness:
            ax.text(0.5, 0.5, '蜜罐数据为空', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('蜜罐触发热力图')
            return
        
        # 提取数据
        nodes = []
        trigger_rates = []
        is_steiner = []
        
        for node, data in honeypot_effectiveness.items():
            nodes.append(node)
            trigger_rates.append(data.get('trigger_rate', 0) * 100)
            is_steiner.append(data.get('is_steiner', False))
        
        # 按触发率排序
        sorted_indices = np.argsort(trigger_rates)[::-1]  # 降序
        nodes = [nodes[i] for i in sorted_indices[:10]]  # 取前10
        trigger_rates = [trigger_rates[i] for i in sorted_indices[:10]]
        is_steiner = [is_steiner[i] for i in sorted_indices[:10]]
        
        # 创建热力图
        x = np.arange(len(nodes))
        colors = ['#FF6B6B' if st else '#4ECDC4' for st in is_steiner]  # 红色=斯坦纳，青色=普通
        
        bars = ax.barh(x, trigger_rates, color=colors, alpha=0.8)
        
        ax.set_xlabel('触发率 (%)')
        ax.set_title('Top 10 蜜罐触发率')
        ax.set_yticks(x)
        ax.set_yticklabels([f'HP-{i+1}' for i in range(len(nodes))])
        ax.invert_yaxis()  # 最高的在最上面
        ax.grid(True, alpha=0.3, axis='x')
        
        # 添加数值标签
        for bar, rate, st in zip(bars, trigger_rates, is_steiner):
            width = bar.get_width()
            label = f'{rate:.1f}%'
            if st:
                label += ' (S)'
            ax.text(width + 1, bar.get_y() + bar.get_height()/2., 
                   label, va='center', fontsize=9)
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#FF6B6B', label='斯坦纳节点'),
            Patch(facecolor='#4ECDC4', label='普通节点')
        ]
        ax.legend(handles=legend_elements, loc='lower right')
    
    def create_attack_network_visualization(self, algorithm='moe-shd'):
        """创建攻击网络可视化"""
        if algorithm not in self.algorithm_logs:
            print(f" {algorithm} 算法的日志数据不存在")
            return
        
        log_data = self.algorithm_logs[algorithm]
        
        # 提取网络信息
        network_nodes = log_data.get('network_nodes', [])
        honeypot_nodes = log_data.get('current_honeypots', [])
        steiner_nodes = log_data.get('steiner_nodes', [])
        attack_paths = log_data.get('attack_paths', [])
        
        if not attack_paths:
            print(f" {algorithm} 算法没有攻击路径数据")
            return
        
        # 创建网络图
        G = nx.Graph()
        
        # 添加节点
        for node in network_nodes:
            node_type = 'normal'
            if node in honeypot_nodes:
                node_type = 'honeypot'
            if node in steiner_nodes:
                node_type = 'steiner'
            
            G.add_node(node, node_type=node_type)
        
        # 从攻击路径中提取边（仅展示部分路径）
        edge_weights = defaultdict(int)
        
        # 选择前5条攻击路径进行可视化
        for path in attack_paths[:5]:
            actions = path.get('actions', [])
            for i in range(len(actions) - 1):
                source = actions[i]['source_node']
                target = actions[i]['target_node']
                edge_weights[(source, target)] += 1
        
        # 添加边
        for (source, target), weight in edge_weights.items():
            if G.has_node(source) and G.has_node(target):
                G.add_edge(source, target, weight=weight)
        
        # 绘制网络图
        plt.figure(figsize=(14, 10))
        
        # 节点布局
        pos = nx.spring_layout(G, seed=42, k=2)
        
        # 分离不同类型节点
        normal_nodes = [n for n, d in G.nodes(data=True) if d['node_type'] == 'normal']
        honeypot_nodes_g = [n for n, d in G.nodes(data=True) if d['node_type'] == 'honeypot']
        steiner_nodes_g = [n for n, d in G.nodes(data=True) if d['node_type'] == 'steiner']
        
        # 绘制节点
        nx.draw_networkx_nodes(G, pos, nodelist=normal_nodes, 
                               node_color='lightblue', node_size=300, alpha=0.7)
        nx.draw_networkx_nodes(G, pos, nodelist=honeypot_nodes_g, 
                               node_color='red', node_size=500, alpha=0.8)
        nx.draw_networkx_nodes(G, pos, nodelist=steiner_nodes_g, 
                               node_color='orange', node_size=700, alpha=0.9, 
                               node_shape='s')  # 方形表示斯坦纳节点
        
        # 绘制边（宽度表示攻击频率）
        edges = G.edges()
        weights = [G[u][v]['weight'] for u, v in edges]
        edge_widths = [w * 0.5 for w in weights]  # 缩放宽度
        
        nx.draw_networkx_edges(G, pos, width=edge_widths, 
                               alpha=0.5, edge_color='gray')
        
        # 绘制标签（只显示蜜罐和斯坦纳节点）
        labels = {}
        for node in honeypot_nodes_g + steiner_nodes_g:
            labels[node] = node
        
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold')
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='lightblue', alpha=0.7, label='普通节点'),
            Patch(facecolor='red', alpha=0.8, label='蜜罐节点'),
            Patch(facecolor='orange', alpha=0.9, label='斯坦纳节点'),
            Patch(facecolor='gray', alpha=0.5, label='攻击路径')
        ]
        plt.legend(handles=legend_elements, loc='upper left')
        
        plt.title(f'{algorithm.upper()} 部署 - 攻击网络可视化\n(边宽度表示攻击频率)', fontsize=16)
        plt.axis('off')
        
        # 保存图片
        filename = f'network_visualization_{algorithm}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f" 网络可视化已保存: {filename}")
    
    def create_detailed_analysis_report(self):
        """创建详细分析报告"""
        if not self.comparison_data:
            print(" 没有对比数据可生成报告")
            return
        
        results = self.comparison_data.get('algorithm_results', {})
        summary = self.comparison_data.get('comparison_summary', {})
        
        # 提取关键指标
        key_metrics = {}
        for algo in ['random-k', 'k-medoids', 'moe-shd']:
            if algo in results:
                metrics = results[algo]
                key_metrics[algo] = {
                    'touch_probability': metrics.get('touch_probability', 0) * 100,
                    'capture_latency': metrics.get('capture_latency_mean', 0),
                    'average_steps': metrics.get('average_steps_per_attack', 0)
                }
        
        # 计算改进百分比
        improvements = {}
        if 'random-k' in key_metrics and 'moe-shd' in key_metrics:
            random_metrics = key_metrics['random-k']
            moe_metrics = key_metrics['moe-shd']
            
            improvements['touch_probability'] = (
                (moe_metrics['touch_probability'] - random_metrics['touch_probability']) / 
                random_metrics['touch_probability'] * 100
            )
            
            improvements['capture_latency'] = (
                (random_metrics['capture_latency'] - moe_metrics['capture_latency']) / 
                random_metrics['capture_latency'] * 100
            )
        
        # 生成报告
        report = f"""
{'='*80}
网络安全攻防模拟 - 详细分析报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

一、实验配置
{'─'*40}
实验配置: {self.comparison_data.get('experiment_config', {})}

二、算法性能对比
{'─'*40}
"""
        
        # 算法性能表格
        report += "部署算法 | 触碰概率 | 平均捕获延迟 | 平均攻击步数\n"
        report += "---------|----------|--------------|-------------\n"
        
        for algo, metrics in key_metrics.items():
            report += f"{algo:<10} | {metrics['touch_probability']:.2f}% | "
            report += f"{metrics['capture_latency']:.2f}步 | {metrics['average_steps']:.2f}\n"
        
        # 改进分析
        if improvements:
            report += f"""
三、MoE-SHD 相对 Random-K 的改进
{'─'*40}
• 触碰概率提升: {improvements.get('touch_probability', 0):.2f}%
• 捕获延迟降低: {improvements.get('capture_latency', 0):.2f}%
"""
        
        # MoE专家系统分析
        if 'moe-shd' in results:
            moe_metrics = results['moe-shd'].get('moe_metrics', {})
            if moe_metrics:
                report += f"""
四、MoE专家系统性能
{'─'*40}
• 误报率: {moe_metrics.get('false_positive_rate', 0)*100:.2f}%
• 漏报率: {moe_metrics.get('false_negative_rate', 0)*100:.2f}%
• 整体准确率: {(1 - moe_metrics.get('false_positive_rate', 0) - 
                  moe_metrics.get('false_negative_rate', 0))*100:.2f}%
"""
        
        # 关键发现
        if 'key_findings' in summary:
            report += f"""
五、关键发现
{'─'*40}
"""
            for finding in summary['key_findings']:
                report += f"• {finding}\n"
        
        # 建议
        report += f"""
六、安全建议
{'─'*40}
1. 推荐使用 MoE-SHD 算法进行蜜罐部署，其在斯坦纳树节点上表现出色
2. 重点关注横向移动攻击的检测，这是攻击链中的关键环节
3. 定期评估蜜罐相似度和伪装效果，保持高检测率
4. 结合 MoE 专家系统和传统检测方法，降低误报率

{'='*80}
报告结束
{'='*80}
"""
        
        # 保存报告
        with open('security_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(" 详细分析报告已保存: security_analysis_report.txt")
        
        # 在控制台显示关键结论
        print("\n 关键结论摘要:")
        print("-" * 40)
        for algo, metrics in key_metrics.items():
            print(f"{algo.upper():<10}: 触碰率={metrics['touch_probability']:.2f}%, "
                  f"延迟={metrics['capture_latency']:.2f}步")
        
        return report
    
    def create_attack_timeline_analysis(self, algorithm='moe-shd', num_paths=5):
        """创建攻击时间线分析"""
        if algorithm not in self.algorithm_logs:
            print(f" {algorithm} 算法的日志数据不存在")
            return
        
        log_data = self.algorithm_logs[algorithm]
        attack_paths = log_data.get('attack_paths', [])
        
        if not attack_paths:
            print(f" {algorithm} 算法没有攻击路径数据")
            return
        
        # 选择前几条攻击路径进行分析
        selected_paths = attack_paths[:num_paths]
        
        fig, axes = plt.subplots(num_paths, 1, figsize=(14, 3*num_paths))
        if num_paths == 1:
            axes = [axes]
        
        fig.suptitle(f'{algorithm.upper()} 部署 - 攻击时间线分析', fontsize=16, fontweight='bold')
        
        for idx, path in enumerate(selected_paths):
            ax = axes[idx]
            actions = path.get('actions', [])
            
            if not actions:
                continue
            
            # 提取时间线数据
            steps = list(range(len(actions)))
            success_rates = []
            detection_points = []
            steiner_points = []
            
            for i, action in enumerate(actions):
                success_rates.append(1 if action['success'] else 0)
                
                if action['detected_by']:
                    detection_points.append(i)
                
                if action.get('is_steiner_target', False):
                    steiner_points.append(i)
            
            # 绘制成功/失败时间线
            ax.plot(steps, success_rates, 'b-', alpha=0.3, label='攻击成功')
            ax.fill_between(steps, 0, success_rates, alpha=0.2, color='blue')
            
            # 标记检测点
            for point in detection_points:
                ax.axvline(x=point, color='red', alpha=0.7, linestyle='--', linewidth=1)
                ax.text(point, 0.5, '检测', rotation=90, 
                       ha='right', va='center', color='red', fontsize=8)
            
            # 标记斯坦纳节点
            for point in steiner_points:
                ax.plot(point, 0.5, 's', color='orange', markersize=8, 
                       label='斯坦纳节点' if idx == 0 else "")
            
            ax.set_xlabel('攻击步数')
            ax.set_ylabel('状态')
            ax.set_title(f'攻击路径 {path["path_id"][-6:]} - 捕获: {path["captured"]}')
            ax.set_yticks([0, 1])
            ax.set_yticklabels(['失败', '成功'])
            ax.set_xlim(0, len(actions)-1)
            ax.grid(True, alpha=0.3)
            
            if idx == 0:
                ax.legend(loc='upper right')
        
        plt.tight_layout()
        filename = f'attack_timeline_{algorithm}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f" 攻击时间线分析已保存: {filename}")
    
    def run_all_visualizations(self):
        """运行所有可视化"""
        print(" 开始生成所有可视化图表...")
        
        # 1. 加载数据
        self.load_data()
        
        # 2. 创建对比仪表盘
        print("\n 生成算法对比仪表盘...")
        self.create_comparison_dashboard()
        
        # 3. 创建网络可视化
        print("\n 生成网络可视化...")
        for algo in ['random-k', 'moe-shd']:
            self.create_attack_network_visualization(algorithm=algo)
        
        # 4. 创建攻击时间线分析
        print("\n 生成攻击时间线分析...")
        self.create_attack_timeline_analysis(algorithm='moe-shd', num_paths=3)
        
        # 5. 生成详细报告
        print("\n 生成详细分析报告...")
        self.create_detailed_analysis_report()
        
        print("\n" + "="*60)
        print(" 所有可视化已完成！")
        print("="*60)
        print(" 生成的文件：")
        print("  - algorithm_comparison_dashboard.png  # 对比仪表盘")
        print("  - network_visualization_*.png         # 网络可视化")
        print("  - attack_timeline_*.png              # 时间线分析")
        print("  - security_analysis_report.txt       # 详细报告")
        print("="*60)

# ===================== 使用示例 =====================
if __name__ == "__main__":
    # 创建可视化实例
    visualizer = AttackVisualization(
        results_file="realistic_algorithm_results.json"
    )
    
    # 运行所有可视化
    visualizer.run_all_visualizations()
    
    # 或者单独运行某个功能：
    # visualizer.load_data()
    # visualizer.create_comparison_dashboard()
    # visualizer.create_attack_network_visualization(algorithm='moe-shd')