import sys
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.data_fetcher import (
    fetch_kpi_metrics, fetch_attack_logs, 
    fetch_intent_distribution, fetch_expert_load, fetch_cost_comparison
)

# ------------------------------------------------------------------
# 页面全局配置：彻底隐藏侧边栏
# ------------------------------------------------------------------
st.set_page_config(page_title="态势指挥中心 | MoE-SHD", layout="wide", initial_sidebar_state="collapsed")

# 强制隐藏侧边栏
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        overflow: hidden !important;
        padding: 0 !important;
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 注入黑色调 CSS（与界面二完全统一）
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    /* ===== 全局纯黑背景 ===== */
    html, body, [class*="css"], .stApp, .stApp > header, .main > div {
        background-color: #000000 !important; 
        color: #EDEDED !important;
    }
    .stApp {
        background: #000000 !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
        max-width: 96% !important; 
        background-color: #000000 !important;
    }

    /* ===== 卡片表面 ===== */
    div[data-testid="stContainer"] {
        background-color: #0A0A0A !important;
        border: 1px solid #1F1F22 !important;
        padding: 24px !important;
        border-radius: 8px !important;
    }

    /* ===== Metric 卡片 ===== */
    div[data-testid="metric-container"] {
        background-color: #0A0A0A !important;
        border: 1px solid #1F1F22 !important;
        padding: 16px 24px !important;
        border-radius: 8px !important;
        border-left: 3px solid #EDEDED !important; 
    }
    [data-testid="stMetricValue"] { 
        font-weight: 300 !important; 
        font-size: 2.2rem !important; 
        color: #EDEDED !important; 
    }
    [data-testid="stMetricLabel"] { 
        font-weight: 500 !important; 
        color: #888888 !important; 
        font-size: 0.75rem !important; 
        text-transform: uppercase !important; 
        letter-spacing: 0.5px !important;
    }
    [data-testid="stMetricDelta"] div { 
        color: #10B981 !important; 
        font-weight: 500 !important; 
    }

    /* ===== 按钮 ===== */
    .stButton > button, .stDownloadButton > button {
        background-color: transparent !important;
        border: 1px solid #1F1F22 !important;
        color: #888888 !important;
        font-size: 0.7rem !important;
        letter-spacing: 1px !important;
        transition: all 0.2s ease;
        border-radius: 6px !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { 
        border-color: #EDEDED !important; 
        color: #EDEDED !important; 
    }

    /* ===== 标题 ===== */
    h1 { 
        font-weight: 500 !important; 
        letter-spacing: -0.02em; 
        color: #EDEDED !important; 
        font-size: 1.25rem !important; 
        margin-bottom: 0rem !important;
    }
    h4 { 
        font-weight: 500 !important; 
        color: #888888 !important; 
        font-size: 0.75rem !important; 
        text-transform: uppercase !important; 
        letter-spacing: 1px !important; 
        margin-top: 0rem !important; 
        margin-bottom: 1rem !important;
    }
    
    div[data-testid="stHorizontalBlock"] { gap: 8px !important; }

    /* ===== 日志流 ===== */
    .log-stream-box {
        background-color: #0A0A0A !important;
        border: 1px solid #1F1F22 !important;
        border-radius: 8px !important;
        padding: 20px 32px !important;
        margin-top: 20px !important;
    }
    .log-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        padding: 8px 0;
        border-bottom: 1px solid #1F1F22;
        font-family: monospace;
    }
    .log-row:last-child { border-bottom: none; }
    .status-lamp { color: #10B981; margin-right: 8px; }

    /* ===== 弹窗 ===== */
    div[data-testid="stModal"] {
        width: 65vw !important; max-width: 1100px !important;        
        background-color: rgba(10, 10, 10, 0.85) !important; 
        backdrop-filter: blur(16px) !important;              
        border: 1px solid #1F1F22 !important; padding: 40px !important; border-radius: 8px !important;
    }

    /* ===== Selectbox ===== */
    div[data-testid="stSelectbox"] label {
        color: #888888 !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #000000 !important;
        border: 1px solid #1F1F22 !important;
        border-radius: 6px !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
        color: #EDEDED !important;
    }

    /* ===== 彻底消除任何蓝色调残留 ===== */
    .stApp [data-testid="stAppViewContainer"] {
        background-color: #000000 !important;
    }
    .stApp [data-testid="stAppViewBlockContainer"] {
        background-color: #000000 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
    }
    .st-emotion-cache-1wrcr25, .st-emotion-cache-12fmjuu, .st-emotion-cache-1r4qj8v {
        background-color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# 交互弹窗定义
# ------------------------------------------------------------------
@st.dialog("深度分析：安全态势数据透视矩阵", width="large")
def threat_modal(df, title_text):
    sort_col = "调度频次" if "调度频次" in df.columns else ("频次" if "频次" in df.columns else df.columns[0])
    st.markdown(f"<p style='color: #888888; font-size: 0.9rem; margin-bottom: 16px;'>{title_text} // 基于优化拓扑的实时统计。</p>", unsafe_allow_html=True)
    st.dataframe(df.sort_values(by=sort_col, ascending=False), hide_index=True, use_container_width=True)
    if st.button("CLOSE MATRIX"): st.rerun()

# ------------------------------------------------------------------
# 数据抓取
# ------------------------------------------------------------------
kpi_data = fetch_kpi_metrics()
intent_df = fetch_intent_distribution()
load_df = fetch_expert_load()
cost_df = fetch_cost_comparison()
logs_df = fetch_attack_logs()

# ------------------------------------------------------------------
# 页面布局（原样保留，仅加侧边栏隐藏）
# ------------------------------------------------------------------
header_left, header_right = st.columns([0.7, 0.3])
with header_left:
    st.markdown("<h1>MoE-SHD 态势感知与调度中心</h1>", unsafe_allow_html=True)
with header_right:
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.download_button(label="EXPORT STRATEGY (CSV)", data=cost_df.to_csv(index=False), file_name="moe_shd_report.csv", use_container_width=True)
    with btn_col2:
        if st.button("FORCE REFRESH", use_container_width=True): st.rerun()

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1: st.metric(label="有效诱导数 (THREATS ISOLATED)", value=f"{kpi_data.get('total_blocked', 0):,}", delta="+132/min")
with kpi_col2: st.metric(label="专家决策准确率 (EXPERT ACCURACY)", value=f"{kpi_data.get('accuracy', 0)}%", delta="+2.1%")
with kpi_col3: st.metric(label="算力节省率 (COST REDUCTION)", value=f"{kpi_data.get('cost_saved', 0)}%", delta="最高达 72%")
with kpi_col4: st.metric(label="拓扑收敛时间 (CONVERGENCE)", value=f"{kpi_data.get('converge_time', 0)} s", delta="-0.12s", delta_color="inverse")

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

chart_col1, chart_col2, chart_col3 = st.columns(3)

common_layout = dict(
    template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=25, b=0, l=5, r=5), height=340, 
    font=dict(family="Inter", color="#888888", size=11),
    xaxis=dict(showgrid=False, zeroline=False, showline=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, showline=False, visible=False)
)

with chart_col1:
    with st.container():
        ctrl_l, ctrl_r = st.columns([0.6, 0.4])
        with ctrl_l: st.markdown("<h4>威胁类型分布</h4>", unsafe_allow_html=True)
        with ctrl_r: st.selectbox("WINDOW", ["1H", "6H", "24H"], label_visibility="collapsed", key="sel1")
            
        colors_pie = ['#0EA5E9', '#38BDF8', '#7DD3FC', '#334155', '#1E293B'] 
        fig1 = px.pie(intent_df, values='频次', names='意图分类', hole=0.75)
        total_threats = intent_df['频次'].sum()
        fig1.add_annotation(text=f"{total_threats}", x=0.5, y=0.5, font=dict(size=22, color="#FFFFFF", weight=300), showarrow=False)
        fig1.add_annotation(text="总诱导数", x=0.5, y=0.38, font=dict(size=11, color="#475569"), showarrow=False)
        fig1.update_traces(marker=dict(colors=colors_pie, line=dict(color='#0A0A0A', width=2)), textinfo='none')
        fig1.update_layout(**common_layout, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5))
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        
        if st.button("ANALYSIS DATA", key="btn1", use_container_width=True): threat_modal(intent_df, "威胁攻击分类及风险热图趋势")

with chart_col2:
    with st.container():
        ctrl_l, ctrl_r = st.columns([0.6, 0.4])
        with ctrl_l: st.markdown("<h4>专家节点负载状况</h4>", unsafe_allow_html=True)
        with ctrl_r: st.selectbox("METRIC", ["FREQUENCY", "CPU", "MEM"], label_visibility="collapsed", key="sel2")
            
        max_val = load_df['调度频次'].max()
        colors_bar2 = ['#0EA5E9' if val == max_val else '#222222' for val in load_df['调度频次']]
        fig2 = px.bar(load_df, x='专家模型', y='调度频次', text='调度频次')
        fig2.update_traces(marker_color=colors_bar2, width=0.35, textposition='outside', textfont=dict(color="#FFFFFF"), cliponaxis=False) 
        fig2.update_layout(**common_layout)
        fig2.update_yaxes(range=[0, max_val * 1.25], visible=False)
        fig2.update_xaxes(visible=True, showline=True, linecolor='#1F1F22', tickcolor='#888888')
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        
        if st.button("LOAD MATRIX", key="btn2", use_container_width=True): threat_modal(load_df, "全网动态调度分布式资源利用率")

with chart_col3:
    with st.container():
        ctrl_l, ctrl_r = st.columns([0.6, 0.4])
        with ctrl_l: st.markdown("<h4>部署算力成本对比</h4>", unsafe_allow_html=True)
        with ctrl_r: st.selectbox("CURRENCY", ["CNY (￥)", "USD ($)"], label_visibility="collapsed", key="sel3")
            
        colors_bar3 = ['#1A1A1A', '#262626', '#FFFFFF'] 
        max_cost = cost_df['算力开销(元)'].max()
        fig3 = go.Figure(data=[go.Bar(x=cost_df['部署策略'], y=cost_df['算力开销(元)'], marker_color=colors_bar3, text=cost_df['算力开销(元)'], textposition='outside', textfont=dict(color="#FFFFFF", size=11))])
        fig3.update_traces(width=0.35, cliponaxis=False)
        fig3.update_layout(**common_layout)
        fig3.update_yaxes(range=[0, max_cost * 1.25], visible=False)
        fig3.update_xaxes(visible=True, showline=True, linecolor='#1F1F22', tickcolor='#888888')
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        
        if st.button("COST REPORTS", key="btn3", use_container_width=True): threat_modal(cost_df, "多阶段多策略算力链路开销边际评估")

st.markdown("<div class='log-stream-box'>", unsafe_allow_html=True)
st.markdown("<h4 style='margin-bottom: 12px;'>实时隔离与诱导执行流水线 (Execution Pipeline Telemetry)</h4>", unsafe_allow_html=True)

for _, row in logs_df.head(3).iterrows():
    st.markdown(f"""
    <div class='log-row'>
        <div><span class='status-lamp'>●</span>[{row['时间']}] SRC_IP: <span style='color: #888888;'>{row['攻击源 IP']}</span> // ROUTE: <span style='color: #555555;'>{row['诱导路径']}</span></div>
        <div>ACTIVE_EXPERT: <span style='color: #EDEDED;'>{row['命中专家模型']}</span> // STATUS: <span style='color: #10B981;'>{row['防御状态']}</span></div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"<div style='text-align: right; color: #555555; font-size: 11px; margin-top: 16px; font-weight:400; letter-spacing:1px;'>SYSTEM STATUS: SECURE // REFRESH_RATE: 4.0S // ENGINE: ACTIVE</div>", unsafe_allow_html=True)

time.sleep(4)
st.rerun()