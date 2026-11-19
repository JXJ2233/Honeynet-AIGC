import streamlit as st
import base64

# ---------- 读取背景图片并转为 base64 ----------
try:
    with open("login_bg.jpg", "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    BG_IMAGE = f"url('data:image/jpeg;base64,{img_base64}')"
except FileNotFoundError:
    BG_IMAGE = "none"
    # st.warning("未找到 login_bg.jpg，背景将使用默认黑色") # 可选：在正式环境中注释掉警告

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="Honeynet-AIGC | 主动诱导防御系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Session 初始化 ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "users" not in st.session_state:
    st.session_state.users = {"testuser": {"password": "testpass"}, "admin": {"password": "admin123"}}
if "current_page" not in st.session_state:
    st.session_state.current_page = "系统控制大厅"
if "login_mode" not in st.session_state:
    st.session_state.login_mode = "login"

# ---------- 辅助函数 ----------
def do_login(username, password):
    if username in st.session_state.users and st.session_state.users[username]["password"] == password:
        st.session_state.authenticated = True
        st.session_state.current_user = username
        return True
    return False

def do_register(username, password, confirm_password):
    if not username or not password:
        return False, "用户名/密码不能为空"
    if password != confirm_password:
        return False, "两次输入的密码不一致"
    if username in st.session_state.users:
        return False, "用户名已存在"
    st.session_state.users[username] = {"password": password}
    st.session_state.authenticated = True
    st.session_state.current_user = username
    return True, ""

# ==================== 未登录：登录/注册页面 ====================
if not st.session_state.authenticated:
    # 背景图
    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            background: {BG_IMAGE} no-repeat center center fixed !important;
            background-size: cover !important;
        }}
        .main .block-container {{
            background: transparent !important;
        }}
        section[data-testid="stSidebar"] {{
            display: none !important;
        }}
        /* 去掉右侧卡片的透明黑框 */
        .login-card {{
            background: transparent !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border: none !important;
            box-shadow: none !important;
            padding: 2rem 1.8rem !important;
            margin-top: 15vh;
        }}
        /* 调整输入框样式，确保在亮色背景图上可读 */
        .stTextInput > div > div > input {{
            background-color: rgba(0,0,0,0.6);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
        }}
        .stButton > button {{
            background-color: rgba(0,0,0,0.6);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    col_left, col_right = st.columns([2, 1.2])
    with col_right:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        # 切换登录/注册按钮
        mode_col1, mode_col2 = st.columns(2)
        with mode_col1:
            if st.button("登录", use_container_width=True, key="go_login"):
                st.session_state.login_mode = "login"
                st.rerun()
        with mode_col2:
            if st.button("注册", use_container_width=True, key="go_register"):
                st.session_state.login_mode = "register"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.login_mode == "login":
            with st.form("login_form"):
                username = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                submitted = st.form_submit_button("登录", use_container_width=True)
                if submitted:
                    if do_login(username, password):
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
            if st.button("使用测试账号登录", use_container_width=True):
                if do_login("admin", "admin123"):
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error("测试账号异常")
        else:
            with st.form("register_form"):
                new_user = st.text_input("用户名", placeholder="请设置用户名")
                new_pass = st.text_input("密码", type="password", placeholder="请设置密码")
                confirm_pass = st.text_input("确认密码", type="password", placeholder="再次输入密码")
                submitted = st.form_submit_button("注册并自动登录", use_container_width=True)
                if submitted:
                    ok, msg = do_register(new_user, new_pass, confirm_pass)
                    if ok:
                        st.success("注册成功，已自动登录！")
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==================== 已登录：Honeynet-AIGC 核心大厅 ====================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

    /* ==========================================
       1. 抹除登录页背景，切换为顶级深曜石底色
       ========================================== */
    html, body, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #030406 !important; 
        background-image: none !important; /* 核心：清除登录背景图 */
        color: #EDEDED !important;
    }

    header, footer, [data-testid="stSidebarNav"] { display: none !important; } 

    /* 显示侧边栏 */
    section[data-testid="stSidebar"] {
        display: block !important;
        background-color: rgba(0, 0, 0, 0.15) !important; 
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: inset -1px 0 0 rgba(0,0,0,0.5) !important;
    }
    section[data-testid="stSidebar"] .block-container { padding: 3rem 1.5rem !important; }

    /* ==========================================
       2. 侧边栏导航：白字 + 发光红点
       ========================================== */
    [data-testid="stRadio"] { gap: 8px; }
    
    [data-testid="stRadio"] label > div:first-of-type,
    [data-testid="stRadio"] label svg,
    [data-testid="stRadio"] label input {
        display: none !important; width: 0 !important; height: 0 !important; opacity: 0 !important; margin: 0 !important;
    }
    [data-testid="stRadio"] label > div:last-child { margin-left: 0 !important; width: 100%; }
    
    [data-testid="stRadio"] label {
        padding: 12px 16px !important; border-radius: 8px !important; background: transparent !important;
        margin-bottom: 4px !important; transition: all 0.3s ease !important; cursor: pointer !important;
        display: flex !important; align-items: center !important; border: 1px solid transparent !important; 
    }
    [data-testid="stRadio"] label:hover { background: rgba(255,255,255,0.03) !important; }
    [data-testid="stRadio"] label[data-checked="true"] {
        background: rgba(255, 255, 255, 0.06) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: inset 0 1px 1px rgba(255,255,255,0.05), 0 4px 10px rgba(0,0,0,0.2) !important;
    }
    
    [data-testid="stRadio"] label p {
        font-size: 15px !important; font-weight: 500 !important; color: rgba(255, 255, 255, 0.6) !important; 
        letter-spacing: 0.03em !important; margin: 0 !important; display: flex !important; align-items: center !important;
    }
    [data-testid="stRadio"] label[data-checked="true"] p { color: #FFFFFF !important; font-weight: 600 !important; }

    [data-testid="stRadio"] label p::before {
        content: ''; display: inline-block; width: 8px; height: 8px; border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.2); margin-right: 14px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.5); transition: all 0.3s ease;
    }
    [data-testid="stRadio"] label[data-checked="true"] p::before {
        background-color: #EF4444 !important; 
        box-shadow: 0 0 12px rgba(239, 68, 68, 0.9), inset 0 1px 2px rgba(255,255,255,0.4) !important;
    }

    /* ==========================================
       3. 主内容区与 Baby蓝 英雄卡片
       ========================================== */
    .main .block-container { max-width: 100%; padding: 2.5rem 3.5rem !important; }

    .top-header { 
        margin-bottom: 2.5rem; padding: 24px 32px; 
        border: 2px solid rgba(137, 207, 240, 0.6); 
        border-radius: 16px; background: rgba(137, 207, 240, 0.03); 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 0 20px rgba(137, 207, 240, 0.05); 
    }
    .top-title { font-size: 1.75rem; font-weight: 600; color: #89CFF0; margin-bottom: 12px; text-shadow: 0 0 15px rgba(137, 207, 240, 0.3); }
    .top-desc { font-size: 0.95rem; color: rgba(255,255,255,0.75); line-height: 1.6; max-width: 900px; }

    .iframe-container { 
        border-radius: 0; overflow: hidden; border: none; background: transparent; 
        height: 820px; width: 100%; max-width: 100%; 
        margin-left: 0; margin-right: 0;
    }
    .iframe-container iframe {
        width: 100% !important; 
        min-width: 100% !important;
        max-width: 100% !important;
    }

    .glass-card {
        background: rgba(0, 0, 0, 0.25); 
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08); border-top: 1px solid rgba(255, 255, 255, 0.15); 
        border-radius: 16px; padding: 24px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 10px 30px rgba(0,0,0,0.5);
        transition: transform 0.3s ease, border-color 0.3s ease; display: flex; flex-direction: column;
    }
    .glass-card:hover { transform: translateY(-4px); border-color: rgba(137, 207, 240, 0.3); }

    /* ==========================================
       4. 动态架构拓扑图 CSS
       ========================================== */
    .architecture-diagram {
        display: flex; justify-content: space-between; align-items: center;
        padding: 20px; background: rgba(0,0,0,0.4); border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.05); margin-top: 12px; position: relative;
    }
    .diagram-column { display: flex; flex-direction: column; align-items: center; gap: 16px; z-index: 2; width: 28%; }
    .diag-node {
        padding: 12px 20px; border-radius: 8px; font-size: 13px; font-weight: 600; text-align: center;
        width: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.4); border: 1px solid transparent; letter-spacing: 0.05em;
    }
    .node-threat { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.4); color: #EF4444; }
    .node-steiner { background: rgba(137, 207, 240, 0.15); border-color: rgba(137, 207, 240, 0.4); color: #89CFF0; }
    .node-scb { background: transparent; border: 1px dashed rgba(255,255,255,0.2); color: rgba(255,255,255,0.5); }
    .node-moe-gate { background: rgba(167, 139, 250, 0.15); border-color: rgba(167, 139, 250, 0.4); color: #A78BFA; }
    .node-expert { background: rgba(255, 255, 255, 0.05); border-color: rgba(255, 255, 255, 0.1); color: #EDEDED; font-size: 11px; padding: 8px; }

    .flow-path {
        position: relative; flex: 1; height: 2px; background: rgba(255,255,255,0.1);
        margin: 0 10px; display: flex; align-items: center; z-index: 1;
    }
    @keyframes particle-flow { 0% { left: 0; opacity: 0; } 20% { opacity: 1; } 80% { opacity: 1; } 100% { left: 100%; opacity: 0; } }
    .particle {
        position: absolute; width: 6px; height: 6px; border-radius: 50%; background: #89CFF0; box-shadow: 0 0 10px #89CFF0;
        animation: particle-flow 2s infinite linear;
    }
    .particle-red { background: #EF4444; box-shadow: 0 0 10px #EF4444; animation-duration: 1.5s; }
    
    .expert-group {
        display: flex; flex-direction: column; gap: 8px; width: 100%;
        padding-left: 20px; border-left: 1px solid rgba(167, 139, 250, 0.3); margin-top: 8px;
    }
    .expert-item { position: relative; width: 100%; }
    .expert-item::before {
        content: ''; position: absolute; left: -20px; top: 50%; width: 20px; height: 1px; background: rgba(167, 139, 250, 0.3);
    }
    
    /* 呼吸脉冲与日志样式 */
    @keyframes pulse-blue { 0% { box-shadow: 0 0 0 0 rgba(137, 207, 240, 0.7); } 70% { box-shadow: 0 0 0 8px rgba(137, 207, 240, 0); } 100% { box-shadow: 0 0 0 0 rgba(137, 207, 240, 0); } }
    .live-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #89CFF0; margin-right: 8px; animation: pulse-blue 2s infinite; }
    .feed-row { display: grid; grid-template-columns: 80px 120px 1fr 140px; gap: 16px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: 'JetBrains Mono', monospace; font-size: 13px; color: rgba(255,255,255,0.6); align-items: center; }
    .feed-row:last-child { border-bottom: none; }
    .feed-tag { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-align: center; }
    .tag-red { background: rgba(239,68,68,0.15); color: #EF4444; border: 1px solid rgba(239,68,68,0.3); }
    .tag-blue { background: rgba(137,207,240,0.1); color: #89CFF0; border: 1px solid rgba(137,207,240,0.3); }
    .tag-amber { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
    .progress-track { width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden; margin-top: 8px; }
    .progress-fill { height: 100%; border-radius: 8px; background: linear-gradient(90deg, #3B82F6, #89CFF0); box-shadow: 0 0 10px rgba(137, 207, 240, 0.5); }
</style>
""", unsafe_allow_html=True)

FEATURES = {
    "系统控制大厅": "Honeynet-AIGC 核心枢纽。提供环境网关的权限管控与算力概览，展示全网资产暴露面与高交互蜜罐 (Honeypot) 的全局部署状态，构建防御态势的基座。",
    "拓扑策略引擎": "算法推演台。执行子模最大化 (SCB) 剔除边缘节点，求解多目标斯坦纳树 (Steiner Tree)。实现核心资产隐匿与蜜罐的最优拓扑编排，大幅降低算力开销。",
    "对抗仿真平台": "实兵演练沙箱。基于混合专家模型拦截网络攻击。精准捕获 SQLi、XSS、命令注入及大模型提示词越狱 (Prompt Injection)，实时输出隔离溯源日志。",
    "全域态势感知": "安全遥测指挥中心。汇聚多节点状态，提供攻击意图分布环形图、专家负载热图，对比展现 SHD 算法在安全调度与算力分配上的边际效益优势。"
}

with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 36px 8px; display: flex; align-items: center; gap: 12px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#89CFF0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 8px rgba(137, 207, 240, 0.4));"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
        <span style="font-weight: 700; font-size: 1.25rem; letter-spacing: 0.05em; color: #89CFF0; text-shadow: 0 0 10px rgba(137, 207, 240, 0.3);">Honeynet-AIGC</span>
    </div>
    """, unsafe_allow_html=True)

    menu_options = list(FEATURES.keys())
    st.session_state.current_page = st.radio("导航", menu_options, label_visibility="collapsed", index=menu_options.index(st.session_state.current_page))
    
    # === 退出登录按钮 ===
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
    if st.button(" 断开安全连接 (Logout)", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = ""
        st.rerun()

st.markdown(f"""
    <div class="top-header">
        <div class="top-title">{st.session_state.current_page}</div>
        <div class="top-desc">{FEATURES[st.session_state.current_page]}</div>
    </div>
""", unsafe_allow_html=True)

def render_iframe(url: str):
    st.markdown(f'<div class="iframe-container"><iframe src="{url}" width="100%" height="100%" style="border:none;" scrolling="yes"></iframe></div>', unsafe_allow_html=True)



if st.session_state.current_page == "系统控制大厅":
    
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 24px;">
        <div class="glass-card" style="padding: 24px;">
            <div style="color: rgba(255,255,255,0.5); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">全局蜜罐池规模</div>
            <div style="color: #FFF; font-size: 40px; font-weight: 600; font-family: 'JetBrains Mono', Consolas, monospace; line-height: 1;">256 <span style="font-size: 14px; color: rgba(255,255,255,0.3);">Nodes</span></div>
        </div>
        <div class="glass-card" style="padding: 24px;">
            <div style="color: rgba(255,255,255,0.5); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">系统已截获威胁</div>
            <div style="color: #89CFF0; font-size: 40px; font-weight: 600; font-family: 'JetBrains Mono', Consolas, monospace; line-height: 1; text-shadow: 0 0 15px rgba(137, 207, 240, 0.4);">1,283 <span style="font-size: 14px; color: rgba(255,255,255,0.3); text-shadow: none;">Isolated</span></div>
        </div>
        <div class="glass-card" style="padding: 24px;">
            <div style="color: rgba(255,255,255,0.5); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">欺骗网络吞吐带宽</div>
            <div style="color: #FFF; font-size: 40px; font-weight: 600; font-family: 'JetBrains Mono', Consolas, monospace; line-height: 1;">2.4 <span style="font-size: 14px; color: rgba(255,255,255,0.3);">Mbps</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="glass-card" style="margin-bottom: 24px;">
        <div style="color: #89CFF0; font-size: 14px; font-weight: 600; letter-spacing: 0.05em; display: flex; align-items: center; gap: 8px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            Honeynet-AIGC 核心架构拓扑流 (Live Architecture)
        </div>
        
        <div class="architecture-diagram">
            <div class="diagram-column">
                <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-bottom: 8px;">[ 外网威胁源 ]</div>
                <div class="diag-node node-threat">恶意流量集群 / 0-Day攻击</div>
            </div>
            
            <div class="flow-path"><div class="particle particle-red"></div></div>

            <div class="diagram-column" style="width: 35%;">
                <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-bottom: 8px;">[ SHD 主动防御层 ]</div>
                <div class="diag-node node-scb" style="margin-bottom: 8px;">SCB 子模过滤网关</div>
                <div class="diag-node node-steiner">Steiner Tree 最优诱导网络</div>
                <div style="font-size: 11px; color: #89CFF0; margin-top: 8px; text-align: center;">▲ 拓扑级协同欺骗</div>
            </div>

            <div class="flow-path"><div class="particle"></div></div>

            <div class="diagram-column">
                <div style="font-size: 11px; color: rgba(255,255,255,0.5); margin-bottom: 8px;">[ AI 研判集群 ]</div>
                <div class="diag-node node-moe-gate">MoE 门控分流 (Gating)</div>
                <div class="expert-group">
                    <div class="expert-item"><div class="diag-node node-expert">SQLi 分析专家</div></div>
                    <div class="expert-item"><div class="diag-node node-expert">Prompt 越狱专家</div></div>
                    <div class="expert-item"><div class="diag-node node-expert">XSS / 恶意文件专家</div></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px;">
        <div class="glass-card">
            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div style="color: #FFFFFF; font-size: 14px; font-weight: 600; letter-spacing: 0.05em; display: flex; align-items: center;">
                    <span class="live-dot"></span> 全域实时拦截流 (LIVE FEED)
                </div>
                <div style="color: rgba(255,255,255,0.4); font-size: 12px;">自动刷新激活</div>
            </div>
            <div style="display: flex; flex-direction: column;">
                <div class="feed-row"><div>14:23:01</div><div style="color:#FFF;">192.168.45.22</div><div><span class="feed-tag tag-red">SQLi INJECTION</span></div><div style="text-align:right;">Node-HNY-01</div></div>
                <div class="feed-row"><div>14:22:45</div><div style="color:#FFF;">45.133.22.19</div><div><span class="feed-tag tag-amber">PROMPT ESCAPE</span></div><div style="text-align:right;">Node-LLM-04</div></div>
                <div class="feed-row"><div>14:21:12</div><div style="color:#FFF;">10.0.5.101</div><div><span class="feed-tag tag-blue">PORT SCANNING</span></div><div style="text-align:right;">Node-HNY-02</div></div>
                <div class="feed-row"><div>14:18:55</div><div style="color:#FFF;">203.0.113.44</div><div><span class="feed-tag tag-amber">DATA EXFILTRATION</span></div><div style="text-align:right;">Node-LLM-01</div></div>
            </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 24px;">
            <div class="glass-card">
                <div style="color: #FFFFFF; font-size: 14px; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 24px;">MoE 专家集群健康度</div>
                <div style="margin-bottom: 16px;">
                    <div style="display:flex; justify-content:space-between; font-size:12px; color:rgba(255,255,255,0.6); margin-bottom:4px;"><span>Steiner 拓扑引擎 (SCB)</span> <span style="color:#89CFF0;">78%</span></div>
                    <div class="progress-track"><div class="progress-fill" style="width: 78%;"></div></div>
                </div>
                <div style="margin-bottom: 16px;">
                    <div style="display:flex; justify-content:space-between; font-size:12px; color:rgba(255,255,255,0.6); margin-bottom:4px;"><span>LLM 防御专家节点 (EXP-1)</span> <span style="color:#89CFF0;">45%</span></div>
                    <div class="progress-track"><div class="progress-fill" style="width: 45%;"></div></div>
                </div>
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; color:rgba(255,255,255,0.6); margin-bottom:4px;"><span>流量路由分配器 (Gate)</span> <span style="color:#89CFF0;">92%</span></div>
                    <div class="progress-track"><div class="progress-fill" style="width: 92%; background: linear-gradient(90deg, #F59E0B, #EF4444); box-shadow: 0 0 10px rgba(239,68,68,0.5);"></div></div>
                </div>
            </div>
            <div class="glass-card" style="padding: 20px 24px;">
                <div style="color: #FFFFFF; font-size: 14px; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 12px;">战术调度网关</div>
                <div style="display: flex; gap: 12px;">
                    <div style="flex:1; padding: 10px 12px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: rgba(255,255,255,0.5); font-size: 12px; display: flex; align-items: center; justify-content: space-between;">
                        <span>Current Operator</span>
                        <span style="color: #89CFF0;">{st.session_state.current_user.upper()}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.current_page == "拓扑策略引擎":
    render_iframe("http://localhost:8501")
elif st.session_state.current_page == "对抗仿真平台":
    render_iframe("http://localhost:5000")
elif st.session_state.current_page == "全域态势感知":
    render_iframe("http://localhost:8502")