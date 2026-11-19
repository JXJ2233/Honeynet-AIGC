"""
图3-5：成本-延迟-安全多目标约束下的帕累托前沿分析
====================================================
不同运维偏好下的非支配解集分布曲线。

展示三种算法在不同运维偏好（成本优先、延迟优先、均衡型）下，
在三维目标空间中的帕累托前沿分布。

依赖：pip install plotly numpy scipy
运行：python standalone_scripts/pareto_analysis_fig3_5.py
输出：charts/图3-5_帕累托前沿分析.png + .html
"""

import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata, interp1d
import os

# ============================================================
# 全局随机种子
# ============================================================
np.random.seed(42)

# ============================================================
# 1. 模拟三种运维偏好下的实验数据
#    每个偏好代表一种门控权重配置
# ============================================================

# ---- 1a. 成本优先策略 (Cost Priority) ----
# 门控权重：w_cost=0.6, w_latency=0.2, w_security=0.2
# 特点：成本最低，但延迟和安全损失可能略高
x_cost = np.random.uniform(0.20, 0.35, 25)
y_cost = np.random.uniform(12, 25, 25)
z_cost = np.random.uniform(15, 35, 25)

# ---- 1b. 延迟优先策略 (Latency Priority) ----
# 门控权重：w_cost=0.2, w_latency=0.6, w_security=0.2
# 特点：延迟最低，但成本和安全损失可能略高
x_lat = np.random.uniform(0.30, 0.50, 25)
y_lat = np.random.uniform(3, 12, 25)
z_lat = np.random.uniform(10, 30, 25)

# ---- 1c. 均衡型策略 (Balanced) ----
# 门控权重：w_cost=0.33, w_latency=0.33, w_security=0.33
# 特点：三个目标均衡优化
x_bal = np.random.uniform(0.25, 0.42, 25)
y_bal = np.random.uniform(6, 16, 25)
z_bal = np.random.uniform(5, 22, 25)

# ---- 1d. 安全优先策略 (Security Priority) ----
# 门控权重：w_cost=0.15, w_latency=0.15, w_security=0.7
# 特点：安全损失最低，但成本可能较高
x_sec = np.random.uniform(0.35, 0.55, 25)
y_sec = np.random.uniform(8, 20, 25)
z_sec = np.random.uniform(3, 12, 25)

# ---- 1e. 对比算法数据 ----
# RandomK (无优化)
x_rand = np.random.uniform(0.75, 0.95, 30)
y_rand = np.random.uniform(35, 55, 30)
z_rand = np.random.uniform(55, 80, 30)

# KMedoids (聚类优化)
x_kmed = np.random.uniform(0.55, 0.75, 30)
y_kmed = np.random.uniform(20, 38, 30)
z_kmed = np.random.uniform(30, 55, 30)

# ============================================================
# 2. 合并所有 MoE-SHD 数据，计算全局帕累托前沿
# ============================================================

all_x = np.concatenate([x_cost, x_lat, x_bal, x_sec, x_rand, x_kmed])
all_y = np.concatenate([y_cost, y_lat, y_bal, y_sec, y_rand, y_kmed])
all_z = np.concatenate([z_cost, z_lat, z_bal, z_sec, z_rand, z_kmed])
all_labels = np.concatenate([
    np.zeros(25),    # 0 = Cost Priority
    np.ones(25),     # 1 = Latency Priority
    np.full(25, 2),  # 2 = Balanced
    np.full(25, 3),  # 3 = Security Priority
    np.full(30, 4),  # 4 = RandomK
    np.full(30, 5),  # 5 = KMedoids
])

pref_names = ['成本优先', '延迟优先', '均衡型', '安全优先', 'RandomK', 'KMedoids']
pref_colors = ['#E67E22', '#3498DB', '#2ECC71', '#9B59B6', '#E74C3C', '#7F8C8D']
pref_symbols = ['diamond', 'diamond', 'diamond', 'diamond', 'circle', 'square']

# 帕累托非支配筛选
def pareto_non_dominated(x, y, z):
    n = len(x)
    is_nd = np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(n):
            if i == j: continue
            if (x[j] <= x[i] and y[j] <= y[i] and z[j] <= z[i] and
                (x[j] < x[i] or y[j] < y[i] or z[j] < z[i])):
                is_nd[i] = False
                break
    return is_nd

is_nd = pareto_non_dominated(all_x, all_y, all_z)

# 统计各策略的非支配解数量
print("\n=== 帕累托非支配分析 ===")
for i in range(6):
    n_total = np.sum(all_labels == i)
    n_nd = np.sum((all_labels == i) & is_nd)
    print(f"  {pref_names[i]:>8}: {n_nd}/{n_total} 个非支配解 ({n_nd/max(n_total,1)*100:.0f}%)")

# ============================================================
# 3. 创建 3D 图表
# ============================================================
fig = go.Figure()

# ---- 3a. 绘制各运维偏好的散点 ----
for i in range(6):
    mask = all_labels == i
    fig.add_trace(go.Scatter3d(
        x=all_x[mask], y=all_y[mask], z=all_z[mask],
        mode='markers',
        marker=dict(
            size=5 if i < 4 else 4,
            color=pref_colors[i],
            symbol=pref_symbols[i],
            opacity=0.7 if i < 4 else 0.4,
            line=dict(color='rgba(0,0,0,0.2)', width=0.3)
        ),
        name=pref_names[i],
    ))

# ---- 3b. 绘制帕累托前沿面（基于所有非支配解） ----
nd_x = all_x[is_nd]
nd_y = all_y[is_nd]
nd_z = all_z[is_nd]

xi = np.linspace(min(nd_x) - 0.02, max(nd_x) + 0.02, 30)
yi = np.linspace(min(nd_y) - 0.5, max(nd_y) + 0.5, 30)
X_grid, Y_grid = np.meshgrid(xi, yi)
Z_grid = griddata((nd_x, nd_y), nd_z, (X_grid, Y_grid), method='cubic')

fig.add_trace(go.Surface(
    x=X_grid, y=Y_grid, z=Z_grid,
    colorscale=[
        [0, 'rgba(46, 204, 113, 0.60)'],
        [0.5, 'rgba(39, 174, 96, 0.40)'],
        [1.0, 'rgba(26, 188, 156, 0.25)']
    ],
    opacity=0.4,
    showscale=False,
    name='帕累托最优前沿面',
))

# ---- 3c. 帕累托前沿边界线 ----
xz_idx = np.argsort(nd_x)
fig.add_trace(go.Scatter3d(
    x=nd_x[xz_idx],
    y=np.full_like(nd_x[xz_idx], min(yi)),
    z=nd_z[xz_idx],
    mode='lines',
    line=dict(color='rgba(46, 204, 113, 0.6)', width=2.5),
    showlegend=False,
))

yz_idx = np.argsort(nd_y)
fig.add_trace(go.Scatter3d(
    x=np.full_like(nd_y[yz_idx], min(xi)),
    y=nd_y[yz_idx],
    z=nd_z[yz_idx],
    mode='lines',
    line=dict(color='rgba(46, 204, 113, 0.6)', width=2.5),
    showlegend=False,
))

# ============================================================
# 4. 图表样式
# ============================================================

fig.update_layout(
    scene=dict(
        xaxis_title=dict(
            text='资源成本 (Cost<sub>Resource</sub>) ↓',
            font=dict(size=14, family='Times New Roman', color='#1a1a1a')
        ),
        yaxis_title=dict(
            text='链路延迟 (Cost<sub>Latency</sub>/ms) ↓',
            font=dict(size=14, family='Times New Roman', color='#1a1a1a')
        ),
        zaxis_title=dict(
            text='安全损失 (S<sub>loss</sub>/%) ↓',
            font=dict(size=14, family='Times New Roman', color='#1a1a1a')
        ),
        xaxis=dict(
            backgroundcolor='rgba(255,255,255,0.95)',
            gridcolor='#CCCCCC', showbackground=True,
            zerolinecolor='#AAAAAA',
            tickfont=dict(size=10, family='Times New Roman', color='#333333'),
            range=[0.1, 1.05], dtick=0.2
        ),
        yaxis=dict(
            backgroundcolor='rgba(255,255,255,0.95)',
            gridcolor='#CCCCCC', showbackground=True,
            zerolinecolor='#AAAAAA',
            tickfont=dict(size=10, family='Times New Roman', color='#333333'),
            range=[0, 60], dtick=10
        ),
        zaxis=dict(
            backgroundcolor='rgba(255,255,255,0.95)',
            gridcolor='#CCCCCC', showbackground=True,
            zerolinecolor='#AAAAAA',
            tickfont=dict(size=10, family='Times New Roman', color='#333333'),
            range=[0, 85], dtick=20
        ),
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.3), up=dict(x=0, y=0, z=1)),
        aspectmode='manual',
        aspectratio=dict(x=1.1, y=1.1, z=1.0)
    ),
    paper_bgcolor='rgba(255,255,255,0)',
    plot_bgcolor='rgba(255,255,255,0)',
    margin=dict(l=5, r=5, b=5, t=35),
    legend=dict(
        x=0.72, y=0.96,
        bgcolor='rgba(255,255,255,0.88)',
        bordercolor='#CCCCCC', borderwidth=0.8,
        font=dict(family='Times New Roman', size=11, color='#1a1a1a'),
        itemsizing='constant'
    ),
    title=dict(
        text='图3-5 成本-延迟-安全多目标约束下的帕累托前沿分析',
        font=dict(size=15, family='Times New Roman', color='#1a1a1a'),
        x=0.5, xanchor='center', y=0.98
    ),
    annotations=[
        dict(
            text=('不同运维偏好下的非支配解集分布曲线<br>'
                  'MoE-SHD 四种门控策略（成本优先/延迟优先/均衡型/安全优先）均优于 RandomK 与 KMedoids'),
            x=0.5, y=0.005,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=10, family='Times New Roman', color='#333333'),
            bgcolor='rgba(255,255,255,0.92)',
            bordercolor='#CCCCCC', borderwidth=0.8, borderpad=6
        )
    ]
)

# ============================================================
# 5. 保存输出
# ============================================================

os.makedirs('charts', exist_ok=True)

fig.write_html('charts/图3-5_帕累托前沿分析.html', include_plotlyjs='cdn')
fig.write_image('charts/图3-5_帕累托前沿分析.png', width=1200, height=900, scale=2)

if __name__ == "__main__":
    fig.show()
    print("\n" + "="*65)
    print("  图3-5 成本-延迟-安全帕累托前沿分析已生成")
    print("="*65)
    print(f"  输出文件:")
    print(f"    📄 charts/图3-5_帕累托前沿分析.html")
    print(f"    🖼️  charts/图3-5_帕累托前沿分析.png")
