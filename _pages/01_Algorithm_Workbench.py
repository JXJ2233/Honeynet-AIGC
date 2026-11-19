"""
MoE-SHD 3D 全息攻防沙盘 · Pro 版推演台
- 完全兼容球形 Three.js 渲染器
- 扩展数学模型场景与指标面板
"""

import json
import sys
import time
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html as components_html

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.graph3d_renderer import Graph3DRenderer


st.set_page_config(
    page_title="MoE-SHD 3D Sandbox",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 隐藏侧边栏
st.markdown("""
<style>
    section[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 全局样式（延续您的 Pro 风格）
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #030407; color: #E2E8F0; }
.stApp { background: #030407; }
.block-container { padding: 2rem 3rem; max-width: 1800px; }
.premium-title { font-size: 26px; font-weight: 500; letter-spacing: -0.8px; color: #FFFFFF; margin-bottom: 4px; }
.premium-subtitle { font-size: 13px; font-weight: 400; color: #8B949E; margin-bottom: 36px; }
.section-header { font-size: 12px; font-weight: 600; color: #F8FAFC; margin-bottom: 16px; letter-spacing: 0.8px; text-transform: uppercase; }
.soft-card { background: #0B0E14; border: 1px solid #1C212B; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; }
.small-muted { color: #8B949E; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px; display: block; }
.data-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; color: #8B949E; }
.data-value { font-weight: 500; color: #E2E8F0; font-family: monospace; }
.metric-container { display: flex; justify-content: space-between; background: #0B0E14; border: 1px solid #1C212B; border-radius: 8px; padding: 16px 24px; margin-bottom: 16px; }
.metric-divider { border-left: 1px solid #1C212B; height: 32px; }
.metric-value { font-size: 20px; font-weight: 500; color: #FFFFFF; }
.stButton > button { border-radius: 6px; border: 1px solid #232A38; background: #0B0E14; color: #E2E8F0; width: 100%; padding: 12px; }
.stButton > button:hover { border-color: #3B82F6; background: #141A26; }
.stTextArea textarea { background: #0B0E14 !important; color: #E2E8F0 !important; border: 1px solid #1C212B !important; border-radius: 6px !important; }
.status-indicator { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 8px; }
.status-red { background: #EF4444; }
.status-yellow { background: #F59E0B; }
.status-green { background: #10B981; }
.math-card { background: #0D1117; border-left: 3px solid #3B82F6; padding: 12px 16px; border-radius: 6px; margin: 12px 0; font-family: monospace; font-size: 13px; }
</style>
""", unsafe_allow_html=True)


# ================================================================
# 数学模型场景参数库（与您的渲染器场景名对应）
# ================================================================
SCENE_MODELS = {
    "通用数据中心": {
        "name": "通用数据中心",
        "weights": (0.35, 0.30, 0.35),
        "budget_max": 45000,
        "delay_limits": {"core_agg": 20, "agg_edge": 30, "cross": 50},
        "security_target": 0.75,
        "desc": "标准企业级数据中心，成本、性能、安全均衡配置。",
        "ws": 0.35, "wl": 0.30, "wc": 0.35,
        "cpu": 18, "mem": 14, "bw": 28, "cov": 78, "gain": "+35.2%"
    },
    "金融结算中心": {
        "name": "金融结算中心",
        "weights": (0.20, 0.10, 0.70),
        "budget_max": 60000,
        "delay_limits": {"core_agg": 18, "agg_edge": 25, "cross": 45},
        "security_target": 0.90,
        "desc": "极高安全敏感度。AHP 权重侧重安全损耗 (Ws)。优先防范参数窃取与链路劫持。",
        "ws": 0.65, "wl": 0.20, "wc": 0.15,
        "cpu": 22, "mem": 18, "bw": 30, "cov": 94, "gain": "+42.5%"
    },
    "政务数据专网": {
        "name": "政务数据专网",
        "weights": (0.20, 0.10, 0.70),
        "budget_max": 55000,
        "delay_limits": {"core_agg": 18, "agg_edge": 25, "cross": 40},
        "security_target": 0.95,
        "desc": "合规与隐私导向。约束5 (加权安全覆盖) 要求极高，防御拓扑需实现全域包裹。",
        "ws": 0.75, "wl": 0.10, "wc": 0.15,
        "cpu": 25, "mem": 15, "bw": 25, "cov": 98, "gain": "+48.2%"
    },
    "工业控制系统": {
        "name": "工业控制系统",
        "weights": (0.25, 0.55, 0.20),
        "budget_max": 40000,
        "delay_limits": {"core_agg": 10, "agg_edge": 15, "cross": 25},
        "security_target": 0.80,
        "desc": "SCADA 毫秒级控制。AHP 权重侧重延迟 (Wl)。触发约束2 (最大路由延迟预警)。",
        "ws": 0.35, "wl": 0.55, "wc": 0.10,
        "cpu": 12, "mem": 10, "bw": 15, "cov": 82, "gain": "+55.0%"
    },
    "医疗物联网": {
        "name": "医疗物联网",
        "weights": (0.25, 0.35, 0.40),
        "budget_max": 50000,
        "delay_limits": {"core_agg": 15, "agg_edge": 20, "cross": 35},
        "security_target": 0.85,
        "desc": "生命通道保障。延迟与安全双重敏感，对蜜罐节点的注入跳数进行严格惩罚。",
        "ws": 0.40, "wl": 0.40, "wc": 0.20,
        "cpu": 15, "mem": 12, "bw": 20, "cov": 85, "gain": "+38.7%"
    },
    "教育科研云": {
        "name": "教育科研云",
        "weights": (0.55, 0.20, 0.25),
        "budget_max": 30000,
        "delay_limits": {"core_agg": 30, "agg_edge": 40, "cross": 70},
        "security_target": 0.65,
        "desc": "成本驱动型场景，适合预算有限的教育机构。",
        "ws": 0.30, "wl": 0.25, "wc": 0.45,
        "cpu": 16, "mem": 12, "bw": 22, "cov": 70, "gain": "+32.8%"
    },
    "边缘算力网络": {
        "name": "边缘算力网络",
        "weights": (0.40, 0.45, 0.15),
        "budget_max": 35000,
        "delay_limits": {"core_agg": 12, "agg_edge": 18, "cross": 30},
        "security_target": 0.70,
        "desc": "MEC 终端资源受限。AHP 权重侧重成本 (Wc)。逼近约束6 (CPU<30%, MEM<20%) 极限。",
        "ws": 0.20, "wl": 0.20, "wc": 0.60,
        "cpu": 29, "mem": 19, "bw": 38, "cov": 72, "gain": "+62.4%"
    }
}


def init_state():
    if "scene_key" not in st.session_state:
        st.session_state.scene_key = "通用数据中心"
    if "renderer" not in st.session_state:
        st.session_state.renderer = Graph3DRenderer(
            backend_url="http://127.0.0.1:8000",
            seed=42,
            node_count=232,
            prefer_backend=False,
        )
        st.session_state.renderer.scene = st.session_state.scene_key
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "attack_triggered" not in st.session_state:
        st.session_state.attack_triggered = False
    if "attack_target" not in st.session_state:
        st.session_state.attack_target = None
    if "attack_path" not in st.session_state:
        st.session_state.attack_path = []
    if "attack_message" not in st.session_state:
        st.session_state.attack_message = ""
    if "attack_log" not in st.session_state:
        st.session_state.attack_log = []


def format_percent(v): return f"{v:.1f}%"


def status_block(stage):
    if stage == 0: return "Vulnerable", "status-red"
    if stage == 1: return "SCB Processing", "status-yellow"
    return "Steiner Secured", "status-green"


def render_graph(stage: int, height: int = 760, attack_path: list = None):
    renderer = st.session_state.renderer
    # 您的 render_stage_html 支持 attack_path 参数
    html = renderer.render_stage_html(stage=stage, attack_path=attack_path, height=height)
    components_html(html, height=height, scrolling=False)


def main():
    init_state()
    renderer = st.session_state.renderer

    st.markdown('<div class="premium-title">MoE-SHD Holographic Sandbox</div>', unsafe_allow_html=True)
    st.markdown('<div class="premium-subtitle">Steiner-Tree Optimized Active Defense · Mathematical Model Integration</div>', unsafe_allow_html=True)

    try:
        payload = renderer.build_payload()
        total_nodes = len(payload.stage1_nodes)
        total_edges = len(payload.stage1_edges)
    except Exception as e:
        st.error(f"Failed to load: {e}")
        st.stop()

    col_ctrl, col_view, col_scene = st.columns([1.0, 2.35, 0.85], gap="large")

    # ========== 左侧控制台 ==========
    with col_ctrl:
        st.markdown('<div class="section-header">Algorithm Pipeline</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Base", use_container_width=True):
                st.session_state.step = 0
                st.session_state.attack_triggered = False
                st.rerun()
        with c2:
            if st.button("SCB Filter", use_container_width=True):
                with st.spinner("Applying SCB filter..."):
                    time.sleep(0.8)          # 模拟计算
                st.session_state.step = 1
                st.session_state.attack_triggered = False
                st.rerun()
        with c3:
            if st.button("Steiner", use_container_width=True):
                with st.spinner("Computing Steiner tree..."):
                    time.sleep(1.2)          # 斯坦纳计算稍重
                st.session_state.step = 2
                st.session_state.attack_triggered = False
                st.rerun()

        stats = renderer.get_stage_stats(st.session_state.step)
        status_text, status_dot = status_block(st.session_state.step)

        st.markdown(f"""
        <div class="soft-card">
            <span class="small-muted">Security State</span>
            <div style="display:flex; align-items:center; margin:8px 0 12px 0;">
                <span class="status-indicator {status_dot}"></span><span style="font-weight:500;">{status_text}</span>
            </div>
            <div style="font-size:13px; color:#8B949E;">{stats['status']}</div>
        </div>
        """, unsafe_allow_html=True)

        # ========== 数学模型指标面板（仅 Steiner 阶段） ==========
        scene_model = SCENE_MODELS[st.session_state.scene_key]
        wA, wB, wC = scene_model["weights"]

        if st.session_state.step == 2:
            st.markdown('<div class="section-header" style="margin-top:16px;">Mathematical Model</div>', unsafe_allow_html=True)

            # 基于当前拓扑估算指标（与您的渲染器实际数据无关，仅用于演示数学模型应用）
            node_count = stats['node_count']
            edge_count = stats['edge_count']
            honey_count = stats.get('active_honeypots', 0)

            est_resource = 5000 + node_count * 120 + honey_count * 800
            est_latency = 5 + edge_count * 0.15 + honey_count * 2
            est_coverage = min(100, 40 + honey_count * 3 + (node_count / 232) * 20)

            norm_r = min(1.0, max(0.0, 1 - (est_resource - 20000) / 60000))
            norm_l = min(1.0, max(0.0, 1 - (est_latency - 10) / 80))
            norm_s = min(1.0, max(0.0, est_coverage / 100))
            total_cost = wA * norm_r + wB * norm_l + wC * (1 - norm_s)

            st.markdown(f"""
            <div class="math-card">
                <strong>F(Sol)</strong> = {wA:.2f}·Ĉ<sub>R</sub> + {wB:.2f}·Ĉ<sub>L</sub> + {wC:.2f}·Ŝ<sub>loss</sub><br>
                Ĉ<sub>R</sub> = {norm_r:.3f} &nbsp; | &nbsp; Ĉ<sub>L</sub> = {norm_l:.3f} &nbsp; | &nbsp; Ŝ<sub>loss</sub> = {(1-norm_s):.3f}<br>
                <span style="color:#3B82F6;">▶ 综合成本 = {total_cost:.3f}</span>
            </div>
            """, unsafe_allow_html=True)

            # 约束满足状态
            col_b, col_d, col_sec = st.columns(3)
            budget_ok = est_resource <= scene_model["budget_max"]
            delay_ok = est_latency <= scene_model["delay_limits"]["cross"]
            sec_ok = est_coverage / 100 >= scene_model["security_target"]

            col_b.metric("Budget", f"${est_resource:.0f}", f"≤ ${scene_model['budget_max']:.0f}", delta_color="normal" if budget_ok else "off")
            col_d.metric("Latency", f"{est_latency:.1f}ms", f"≤ {scene_model['delay_limits']['cross']}ms", delta_color="normal" if delay_ok else "off")
            col_sec.metric("Coverage", f"{est_coverage:.0f}%", f"≥ {scene_model['security_target']*100:.0f}%", delta_color="normal" if sec_ok else "off")

        # ========== 攻击模拟区域 ==========
        st.markdown('<div class="section-header" style="margin-top:20px;">Threat Simulation</div>', unsafe_allow_html=True)
        st.session_state.attack_query = st.text_area("Payload", value="Requesting unprivileged access...", height=80, label_visibility="collapsed")

        if st.button("Execute Attack", use_container_width=True):
            if st.session_state.step != 2:
                st.warning("Please advance to Stage 2 (Steiner) first.")
            else:
                target = renderer.get_attack_target()
                path = renderer.build_attack_path(target)
                if path:
                    st.session_state.attack_target = target
                    st.session_state.attack_path = path
                    st.session_state.attack_triggered = True

                    # 记录攻击收益（数学模型演示）
                    st.session_state.attack_log.insert(0, {
                        "time": time.strftime("%H:%M:%S"),
                        "target": target,
                        "cost_saved": f"{(est_resource * 0.15):.0f}" if 'est_resource' in dir() else "N/A",
                        "delay_saved": f"{(est_latency * 0.08):.1f}" if 'est_latency' in dir() else "N/A",
                    })
                    st.session_state.attack_message = f"Attack intercepted by honeypot: {target}"
                st.rerun()

        if st.session_state.attack_message:
            st.success(st.session_state.attack_message)

        if st.session_state.attack_log:
            st.markdown('<div class="small-muted" style="margin-top:16px;">Incident Log</div>', unsafe_allow_html=True)
            for log in st.session_state.attack_log[:3]:
                st.markdown(f"""
                <div style="background:#0B0E14; border-left:2px solid #EF4444; padding:8px 12px; margin-bottom:8px; border-radius:4px; font-size:12px;">
                    [{log['time']}] → {log['target']}<br>
                    <span style="color:#8B949E;"> Saved {log['cost_saved']} |  Latency -{log['delay_saved']}ms</span>
                </div>
                """, unsafe_allow_html=True)

    # ========== 中间 3D 视图 ==========
    with col_view:
        st.markdown('<div class="section-header">3D Topology View</div>', unsafe_allow_html=True)
        if st.session_state.attack_triggered and st.session_state.attack_path:
            render_graph(stage=st.session_state.step, height=720, attack_path=st.session_state.attack_path)
        else:
            render_graph(stage=st.session_state.step, height=720)

    # ==========================================
    # 右侧：场景控制台 & 可视化指标 (无冗余文字)
    # ==========================================
    with col_scene:
        st.markdown('<div class="section-header">Environment Profile</div>', unsafe_allow_html=True)

        # 场景参数库（数值已内置）
        SCENE_DATA = {
            "通用数据中心": {"ws":0.35, "wl":0.30, "wc":0.35, "cpu":18, "mem":14, "bw":28, "gain":"+35.2%"},
            "金融结算中心": {"ws":0.65, "wl":0.20, "wc":0.15, "cpu":22, "mem":18, "bw":30, "gain":"+42.5%"},
            "政务数据专网": {"ws":0.75, "wl":0.10, "wc":0.15, "cpu":25, "mem":15, "bw":25, "gain":"+48.2%"},
            "工业控制系统": {"ws":0.35, "wl":0.55, "wc":0.10, "cpu":12, "mem":10, "bw":15, "gain":"+55.0%"},
            "医疗物联网":   {"ws":0.40, "wl":0.40, "wc":0.20, "cpu":15, "mem":12, "bw":20, "gain":"+38.7%"},
            "边缘算力网络": {"ws":0.20, "wl":0.20, "wc":0.60, "cpu":29, "mem":19, "bw":38, "gain":"+62.4%"}
        }

        scene_list = list(SCENE_DATA.keys())
        current = st.session_state.scene_key
        selected = st.radio("", scene_list, index=scene_list.index(current), label_visibility="collapsed")

        if selected != current:
            st.session_state.scene_key = selected
            st.session_state.step = 0
            st.session_state.attack_triggered = False
            renderer.scene = selected
            renderer.refresh()
            st.rerun()

        data = SCENE_DATA[selected]

        st.markdown("<div style='height:1px; background:#1C212B; margin:20px 0;'></div>", unsafe_allow_html=True)

        # ---- AHP 权重（三色进度条） ----
        st.markdown("**AHP Weights**")
        for label, key, color in [("Security", "ws", "#EF4444"), ("Latency", "wl", "#3B82F6"), ("Cost", "wc", "#10B981")]:
            val = data[key]
            st.markdown(f"""
            <div style="margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;">
                    <span>{label}</span> <span>{val:.2f}</span>
                </div>
                <div style="width:100%; height:4px; background:#1C212B; border-radius:4px; overflow:hidden;">
                    <div style="width:{val*100}%; height:100%; background:{color}; border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:1px; background:#1C212B; margin:20px 0;'></div>", unsafe_allow_html=True)

        # ---- 约束遥测（进度条+阈值） ----
        st.markdown("**Constraints**")
        constraints = [
            ("CPU", data["cpu"], 30),
            ("MEM", data["mem"], 20),
            ("BW",  data["bw"],  40)
        ]
        for name, curr, maxv in constraints:
            ratio = min(1.0, curr / maxv)
            color = "#F59E0B" if ratio > 0.8 else "#3B82F6"
            st.markdown(f"""
            <div style="margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;">
                    <span>{name}</span> <span>{curr}% / {maxv}%</span>
                </div>
                <div style="width:100%; height:4px; background:#1C212B; border-radius:4px; overflow:hidden;">
                    <div style="width:{ratio*100}%; height:100%; background:{color}; border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:1px; background:#1C212B; margin:20px 0;'></div>", unsafe_allow_html=True)

        # ---- 算法优势（大数字卡片） ----
        st.markdown(f"""
        <div style="background:#0B0E14; padding:12px; border-radius:8px; text-align:center; border:1px solid #1C212B;">
            <div style="font-size:10px; color:#8B949E; letter-spacing:0.5px; margin-bottom:4px;">ALGORITHMIC EDGE</div>
            <div style="font-size:28px; font-weight:600; color:#3B82F6;">{data['gain']}</div>
            <div style="font-size:10px; color:#8B949E;">vs Random-K baseline</div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()