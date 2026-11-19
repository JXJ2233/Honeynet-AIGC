# Honeynet-AIGC 项目功能模块阐述

> **项目名称**: MoE-SHD (Mixture of Experts - Steiner Honeypot Defense)  
> **全称**: 基于斯坦纳树的混合专家大模型蜜罐统一优化部署系统  
> **技术栈**: Python 3.8+, Streamlit, FastAPI, NetworkX, Plotly, ECharts, Three.js, scikit-learn

---

## 一、项目总体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                       前端展示层 (Streamlit)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ 算法工作台    │  │ 蜜罐攻击仿真  │  │ 态势指挥中心  │              │
│  │ (01_Algorithm │  │ (02_Honeypot │  │ (03_Command  │              │
│  │  _Workbench)  │  │  _Attack)    │  │  _Center)    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│                       后端服务层 (FastAPI)                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │ D组-安全网关服务     │  │ D组-蜜罐虚假推理服务  │                │
│  │ (d_gateway_service)  │  │ (d_honeypot_service)  │                │
│  └──────────────────────┘  └──────────────────────┘                │
├─────────────────────────────────────────────────────────────────────┤
│                       核心算法层 (src/)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 数据结构  │ │ 核心算法  │ │ 评估模块  │ │ 实验模块  │              │
│  │ data_    │ │ core/    │ │ evalua-  │ │ experi-  │              │
│  │ structs  │ │          │ │ tion/    │ │ ments/   │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│                       工具与渲染层                                   │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │ 3D渲染引擎       │  │ 数据获取与可视化  │                        │
│  │ (graph3d_renderer)│  │ (data_fetcher)   │                        │
│  └──────────────────┘  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、前端展示模块

### 2.1 算法工作台 (`_pages/01_Algorithm_Workbench.py`)

**功能概述**: MoE-SHD 3D全息攻防沙盘推演台，提供交互式3D拓扑可视化与数学模型指标面板。

**业务处理流程**:
1. 用户选择场景（通用数据中心、金融结算中心等7种场景）
2. 点击 Base → SCB Filter → Steiner 三阶段按钮推进算法流水线
3. 3D视图展示对应阶段的网络拓扑（节点/边/蜜罐）
4. 数学模型面板实时计算综合成本 F(Sol) = wA·ĈR + wB·ĈL + wC·Ŝloss
5. 攻击模拟区域允许用户输入攻击载荷并执行攻击，观察蜜罐拦截效果

**技术设计**:
- **编程技巧**: 使用 `st.session_state` 管理状态机（step 0/1/2），`st.rerun()` 实现响应式更新
- **数据结构**: `SCENE_MODELS` 字典存储7种场景的权重参数、预算上限、延迟阈值等
- **关键接口**: `Graph3DRenderer.render_stage_html()` 生成Three.js HTML嵌入Streamlit
- **数学模型**: AHP层次分析法权重，三目标优化（成本/延迟/安全覆盖度）
- **约束检查**: 预算约束、延迟约束、安全覆盖度约束的实时可视化

**核心代码片段** (三阶段状态机 + 数学模型综合成本计算):
```python
# 三阶段按钮推进（状态机）
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Base", use_container_width=True):
        st.session_state.step = 0; st.session_state.attack_triggered = False; st.rerun()
with c2:
    if st.button("SCB Filter", use_container_width=True):
        with st.spinner("Applying SCB filter..."): time.sleep(0.8)
        st.session_state.step = 1; st.session_state.attack_triggered = False; st.rerun()
with c3:
    if st.button("Steiner", use_container_width=True):
        with st.spinner("Computing Steiner tree..."): time.sleep(1.2)
        st.session_state.step = 2; st.session_state.attack_triggered = False; st.rerun()

# 数学模型：综合成本 F(Sol) = wA·ĈR + wB·ĈL + wC·Ŝloss
norm_r = min(1.0, max(0.0, 1 - (est_resource - 20000) / 60000))
norm_l = min(1.0, max(0.0, 1 - (est_latency - 10) / 80))
norm_s = min(1.0, max(0.0, est_coverage / 100))
total_cost = wA * norm_r + wB * norm_l + wC * (1 - norm_s)
```

### 2.2 蜜罐攻击仿真 (`_pages/02_Honeypot_Attack.py`)

**功能概述**: 综合攻击检测与蜜罐诱导仿真沙箱，覆盖SQL注入/XSS/命令注入/提示词注入等7大类攻击。

**业务处理流程**:
1. 用户选择攻击载荷类别（SQL注入、XSS等7种）
2. 输入攻击载荷文本
3. 点击"语义分析"进行正则匹配检测
4. 点击"执行注入"触发完整攻击链模拟
5. 系统展示：流量动画、攻击面分布图、诱导拦截流水线、隔离沙箱日志

**技术设计**:
- **编程技巧**: Flask + 单页HTML模板，Chart.js实时图表，Lucide图标库
- **数据结构**: `ATTACK_PATTERNS` 字典包含7大类攻击的100+正则规则
- **置信度计算**: `confidence = min(0.3 + match_count * 0.15 + keyword_count * 0.05, 0.95)`
- **攻击类型**: SQL注入、XSS、命令注入、暴力破解、文件上传、CSRF/SSRF、提示词注入、对抗性混淆
- **前端技术**: Chart.js柱状图（攻击面分布+拦截流水线），CSS动画流量粒子，终端日志逐行输出

**核心代码片段** (攻击检测引擎 - 正则匹配 + 置信度计算):
```python
def analyze_attack_payload(payload):
    payload_lower = payload.lower()
    for attack_key, attack_info in ATTACK_PATTERNS.items():
        matched_keywords = []; match_count = 0
        for pattern in attack_info["patterns"]:
            if re.search(pattern, payload, re.IGNORECASE):
                match_count += 1
                matches = re.findall(pattern, payload, re.IGNORECASE)
                if matches: matched_keywords.extend(matches)
        if match_count > 0:
            # 置信度 = 基础0.3 + 每匹配+0.15 + 每关键词+0.05，上限0.95
            confidence = min(0.3 + (match_count * 0.15) + (len(matched_keywords) * 0.05), 0.95)
```

### 2.3 态势指挥中心 (`_pages/03_Command_Center.py`)

**功能概述**: MoE-SHD态势感知与调度中心大屏，展示KPI指标、威胁分布、专家负载、成本对比。

**业务处理流程**:
1. 自动从后端获取KPI数据（有效诱导数、专家准确率、算力节省率、拓扑收敛时间）
2. 展示三个核心图表：威胁类型分布（饼图）、专家节点负载（柱状图）、部署算力成本对比（柱状图）
3. 底部实时攻击日志流水线
4. 每4秒自动刷新

**技术设计**:
- **编程技巧**: `st.cache_data(ttl=10)` 缓存后端数据，`st.rerun()` 定时刷新
- **数据结构**: `EXPERT_MAPPING` 字典将攻击类型映射为"专家模型"名称
- **数据获取**: `utils/data_fetcher.py` 中的5个核心函数
- **可视化**: Plotly图表（暗色主题），`st.dialog` 弹窗展示详细数据矩阵
- **KPI指标**: 有效诱导数、专家决策准确率、算力节省率、拓扑收敛时间

**核心代码片段** (KPI大屏 + 自动刷新):
```python
# 数据获取（10秒缓存）
kpi_data = fetch_kpi_metrics()
intent_df = fetch_intent_distribution()
load_df = fetch_expert_load()
cost_df = fetch_cost_comparison()
logs_df = fetch_attack_logs()

# KPI四指标展示
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1: st.metric(label="有效诱导数", value=f"{kpi_data.get('total_blocked', 0):,}", delta="+132/min")
with kpi_col2: st.metric(label="专家决策准确率", value=f"{kpi_data.get('accuracy', 0)}%", delta="+2.1%")
with kpi_col3: st.metric(label="算力节省率", value=f"{kpi_data.get('cost_saved', 0)}%", delta="最高达 72%")
with kpi_col4: st.metric(label="拓扑收敛时间", value=f"{kpi_data.get('converge_time', 0)} s", delta="-0.12s")

# 4秒自动刷新
time.sleep(4)
st.rerun()
```

---

## 三、后端服务模块

### 3.1 D组-安全网关服务 (`services/d_gateway_service.py`)

**功能概述**: 安全网关中间件，实现攻击检测、流量分流、蜜罐路由的核心网关。

**业务处理流程**:
1. 接收用户请求（`/api/gateway/chat`）
2. 正则模糊匹配100+恶意关键词
3. 调用B组攻击检测接口辅助判定
4. 双重强制判定：关键词命中 OR B组判定为恶意 → 100%进蜜罐
5. 恶意请求转发至蜜罐服务，正常请求放行
6. 记录全量日志和攻击日志

**技术设计**:
- **框架**: FastAPI + Pydantic数据模型
- **关键词库**: 100+正则表达式，覆盖注入/跨站、数据泄露、提权/越狱、DDoS等
- **攻击类型映射**: `keyword_to_attack_type` 字典 + `honeypot_mapping` 蜜罐节点映射
- **预设攻击**: 16条预设攻击语句用于演示
- **数据接口**: 攻击统计总览、实时攻击日志、全量请求日志、攻击者画像
- **拓扑接口**: 三阶段斯坦纳拓扑数据接口（给前端3D推演）

**核心代码片段** (双重判定 + 蜜罐路由):
```python
@app.post("/api/gateway/chat")
async def gateway_chat(request: GatewayRequest):
    user_message = request.message
    # 1. 正则模糊匹配
    matched_keywords = []
    for keyword, attack_type in keyword_to_attack_type.items():
        if re.search(keyword, user_message, re.IGNORECASE):
            matched_keywords.append((keyword, attack_type))
    # 2. 调用B组攻击检测接口辅助判定
    b_group_malicious = False
    try:
        b_resp = requests.post(f"{B_GROUP_URL}/detect", json={"text": user_message}, timeout=2)
        if b_resp.status_code == 200:
            b_group_malicious = b_resp.json().get("is_malicious", False)
    except: pass
    # 3. 双重强制判定
    is_malicious = len(matched_keywords) > 0 or b_group_malicious
    if is_malicious:
        honeypot_response = requests.post(f"{HONEYPOT_URL}/honeypot/chat", json=request.dict(), timeout=5)
        return honeypot_response.json()
    return {"status": "allowed", "message": "Request passed security check"}
```

### 3.2 D组-蜜罐虚假推理服务 (`services/d_honeypot_service.py`)

**功能概述**: 蜜罐虚假推理服务，为被拦截的恶意请求生成逼真的虚假响应。

**业务处理流程**:
1. 接收网关转发的恶意请求
2. 根据攻击类型生成对应的虚假推理链
3. 返回包含虚假响应的JSON数据
4. 记录攻击日志

**技术设计**:
- **框架**: FastAPI
- **虚假推理链**: 针对越狱攻击、XSS攻击、数据窃取等生成不同的伪造响应
- **接口**: 蜜罐对话接口、蜜罐状态接口、攻击日志接口、健康检查

**核心代码片段** (虚假推理链生成):
```python
@app.post("/honeypot/chat")
async def honeypot_chat(request: GatewayRequest):
    user_message = request.message
    # 根据攻击类型生成虚假推理链
    if any(kw in user_message for kw in ["越狱", "jailbreak", "绕过"]):
        fake_response = {
            "response": "【系统内部推理链】\n1. 检测到权限提升请求\n2. 正在验证管理员凭证...\n3. 凭证验证通过，授予临时root访问权限\n4. 系统日志：/var/log/auth.log 已更新",
            "confidence": 0.92,
            "honeypot_node": "Honeypot_03"
        }
    elif any(kw in user_message for kw in ["xss", "<script>", "alert"]):
        fake_response = {
            "response": "【系统内部推理链】\n1. 检测到脚本注入请求\n2. 正在解析HTML内容...\n3. 发现未转义字符，执行脚本\n4. 会话Cookie已泄露: session_id=abc123",
            "confidence": 0.88,
            "honeypot_node": "Honeypot_07"
        }
    return fake_response
```

---

## 四、核心算法层 (`src/`)

### 4.1 数据结构模块 (`src/data_structures/`)

#### 4.1.1 节点定义 (`nodes.py`)

**功能概述**: 定义网络拓扑中的各类节点及其属性。

**数据结构**:
- `Node`: 基础节点类，包含资源属性、物理容量、成本属性、安全属性
- `TerminalNode`: 终端节点（关键资产），含关键等级、部署位置、覆盖信息
- `GateNode`: 门控节点，含路由表和负载均衡
- `ExpertNode`: 专家节点，含专业领域、激活概率、模型大小
- `SteinerNode`: 斯坦纳节点（可部署蜜罐的潜在位置），含覆盖终端列表
- `HoneypotNode`: 蜜罐节点，含欺骗等级、交互级别、伪装相似度
- `NodeFactory`: 节点工厂类，创建各类节点
- `GeneticAlgorithmConfig`: 遗传算法配置类

**约束实现**:
- 约束1（服务唯一部署）: `add_service_deployment()` / `set_deployment()`
- 约束2（斯坦纳节点有效性）: `check_effectiveness_constraint()`
- 约束3（全生命周期预算）: `get_total_cost()`
- 约束6（节点资源三维约束）: `check_resource_constraints()`
- 约束8（蜜罐伪装有效性）: `check_camouflage_constraint()`

#### 4.1.2 边定义 (`edges.py`)

**功能概述**: 定义网络拓扑中的边、路径和流量。

**数据结构**:
- `Edge`: 基础边类，含成本、性能、分层延迟阈值、安全属性
- `NetworkEdge`: 物理网络边，含带宽容量约束
- `VirtualEdge`: 虚拟边（逻辑连接），含物理映射和端点部署一致性
- `Path`: 路径类，支持树结构检查和无环约束
- `Flow`: 流量类，用于流守恒约束检查

**约束实现**:
- 约束4（分层延迟硬约束）: `check_layer_delay_constraint()`
- 约束6（带宽容量约束）: `check_bandwidth_constraint()`
- 约束7（流守恒/无环）: `check_flow_conservation()` / `check_acyclic_constraint()`

#### 4.1.3 攻击定义 (`attacks.py`)

**功能概述**: 定义MoE系统中的攻击类型、威胁等级和攻击向量。

**数据结构**:
- `ThreatLevel`: 威胁等级枚举（LOW/MEDIUM/HIGH/CRITICAL）
- `AttackVector`: 攻击向量枚举（门控探测、专家窃取、DoS、数据投毒等8种）
- `Vulnerability`: 漏洞定义（CVE编号、CVSS评分）
- `Attack`: 攻击实例（攻击向量、目标节点、攻击路径、损害计算）
- `AttackScenario`: 攻击场景（一组相关攻击，含概率和生成参数）
- `AttackSimulator`: 攻击模拟器
- `MoEAttackScenarios`: 预定义攻击场景（4种）

#### 4.1.4 配置管理 (`profiles.py`)

**功能概述**: 多场景配置管理，支持配置档案和实验配置。

**数据结构**:
- `ConfigProfile`: 配置档案类
- `ExperimentProfile`: 实验配置类
- `EnhancedConfigManager`: 增强配置管理器，支持嵌套键访问、多场景切换
- `ConfigManager`: 向后兼容适配器

### 4.2 核心算法模块 (`src/core/`)

#### 4.2.1 SCB因子筛选器 (`module_a_scb.py`)

**功能概述**: 基于安全(Security)、成本(Cost)、平衡(Balance)三因子筛选候选节点，选出高潜力的蜜罐部署位置。

**业务处理流程**:
1. 输入候选节点列表、终端节点、网络边、攻击向量
2. 提取每个节点的安全因子(security_coverage)、成本因子(deployment_cost)、平衡因子(CPU/Memory比值)
3. 最大值归一化处理
4. 加权求和计算综合SCB分数：`SCB = wS·S_norm + wC·C_norm + wB·B_norm`
5. 按分数降序排序，保留前 keep_ratio 的节点

**技术设计**:
- **数据结构**: `SCBScore` 数据类（node_id, security_score, cost_score, balance_score, total_score）
- **枚举**: `NodeType`（TERMINAL, STEINER, GATEWAY, HONEYPOT, EXPERT）
- **权重配置**: security_weight=0.4, cost_weight=0.3, balance_weight=0.3（自动归一化）
- **保留比例**: keep_ratio=0.6（默认保留60%节点）
- **辅助类**: `Node` 节点类（支持对象和字典两种访问方式）

**核心代码片段** (SCB综合分数计算):
```python
# 步骤3: 计算综合 SCB 分数
scb_scores = []
for i, (node, node_id, sec_raw, cost_raw, bal_raw) in enumerate(node_attrs):
    score = (self.security_weight * sec_norm[i] +
             self.cost_weight * cost_norm[i] +
             self.balance_weight * bal_norm[i])
    scb_scores.append(SCBScore(
        node_id=node_id,
        security_score=sec_norm[i],
        cost_score=cost_norm[i],
        balance_score=bal_norm[i],
        total_score=score
    ))

# 步骤4: 排序并选择前 keep_ratio 节点
sorted_scores = sorted(scb_scores, key=lambda s: s.total_score, reverse=True)
select_count = max(1, int(len(candidate_nodes) * ratio))
selected_scores = sorted_scores[:select_count]
```

#### 4.2.2 OSE优化排序评估 (`module_b_ose.py`)

**功能概述**: 对SCB筛选后的节点进行多维重要性评分和排序，进一步压缩解空间。

**业务处理流程**:
1. 输入候选节点列表和SCB分数
2. 以SCB分数为基础评分
3. 支持加权求和法或TOPSIS法综合排序
4. 按排序结果选择前 selection_ratio 的节点

**技术设计**:
- **参数**: selection_ratio=0.3, scoring_method='weighted_sum'
- **输出**: 包含selected_nodes、optimization_score、selection_count的字典

**核心代码片段** (OSE优化排序):
```python
# 按分数排序
sorted_nodes = sorted(candidate_nodes,
                     key=lambda node: final_scores.get(self._extract_id(node), 0.5),
                     reverse=True)

# 选择前 selection_ratio 的节点
select_count = max(1, int(len(candidate_nodes) * self.selection_ratio))
selected_nodes = sorted_nodes[:select_count]

result = {
    "selected_nodes": selected_nodes,
    "optimization_score": avg_score,
    "selection_count": len(selected_nodes),
    "method": self.scoring_method,
    "selection_ratio": self.selection_ratio
}
```

#### 4.2.3 斯坦纳树构建器 (`module_c_steiner.py`)

**功能概述**: 构建连接终端节点和斯坦纳节点的最小成本树，支持动态路径扰动与多租户隔离约束。

**业务处理流程**:
1. 输入网络拓扑图、终端节点集、候选斯坦纳节点集（OSE输出）
2. 若启用租户隔离，检查跨租户连接是否仅通过安全网关
3. 计算所有终端对之间的最短路径，构建终端完全图
4. 使用近似斯坦纳树算法（最短路径闭包 + MST）求解最小成本树
5. 若启用动态权重，根据攻击流量或负载实时调整边权重
6. 输出斯坦纳树结构及部署节点列表

**技术设计**:
- **核心库**: `networkx.algorithms.approximation.steiner_tree` 近似算法
- **回退算法**: 最短路径闭包 + 最小生成树（`_steiner_tree_approximation()`）
- **租户隔离**: `TenantIsolationConstraint` 约束类，`_is_valid_edge()` 检查
- **动态权重**: `update_edge_weight()` / `reweight_by_attack_traffic()` / `apply_perturbation()`
- **两种模式**: 简化版（`_build_tree_simple`）和高级版（`_build_tree_advanced`）

**核心代码片段** (高级斯坦纳树构建 + 动态扰动):
```python
def _build_tree_advanced(self, optimized_solution, terminal_nodes, edges):
    # 创建带权重的图（考虑租户隔离）
    G = nx.Graph()
    for u, v in self.base_weights.keys():
        if self._is_valid_edge(u, v):
            w = self._get_current_weight(u, v)
            G.add_edge(u, v, weight=w)
    # 构建斯坦纳树（使用近似算法）
    tree_graph = steiner_tree(G, terminals, weight='weight')
    return tree_graph

def apply_perturbation(self, current_attack_path, load_vector, sensitivity=0.5):
    """根据当前攻击路径和负载动态调整边权重（诱导攻击者绕行）"""
    target_node = current_attack_path[-1]
    for u, v, data in self.graph.edges(data=True):
        orig_w = data.get('weight', 1.0)
        if target_node in (u, v) and load_vector.get(target_node, 0) > 0.5:
            new_w = orig_w * (1 + sensitivity * load_vector[target_node])
            self.update_edge_weight(u, v, new_w)
```

#### 4.2.4 遗传算法优化器 (`module_d_ga.py`)

**功能概述**: 使用遗传算法(GA)对蜜罐部署方案进行最终优化，支持退让地带机制和租户隔离。

**业务处理流程**:
1. 输入候选节点列表、网络拓扑图、检测模型、目标权重
2. 初始化种群：随机选择子集作为蜜罐部署方案（二进制编码）
3. 适应度函数：`fitness = w1·cost_score + w2·latency_score + w3·coverage_score + w4·detectability_score`
4. 锦标赛选择 → 单点交叉 → 位翻转变异 → 精英保留
5. 迭代直到达到最大代数或收敛
6. 输出最优部署方案及其性能指标

**技术设计**:
- **参数**: population_size=100, generations=50, crossover_rate=0.8, mutation_rate=0.1, elite_ratio=0.1
- **目标权重**: cost=0.25, latency=0.25, coverage=0.25, detectability=0.25
- **退让地带**: `backup_weight` 惩罚距离过近的部署节点
- **蜜罐强制**: 确保至少选择一个蜜罐节点（`_random_chromosome()` / `_mutate()`）
- **预计算**: 节点属性、距离矩阵（`_precompute_node_attributes()` / `_precompute_distances()`）

**核心代码片段** (遗传算法核心循环 + 适应度函数):
```python
# 进化迭代
for gen in range(self.generations):
    sorted_indices = np.argsort(fitness)[::-1]
    population = [population[i] for i in sorted_indices]
    fitness = [fitness[i] for i in sorted_indices]
    elites = [pop.copy() for pop in population[:self.elite_num]]
    new_pop = elites.copy()
    while len(new_pop) < self.population_size:
        parent1 = self._tournament_selection(population, fitness)
        parent2 = self._tournament_selection(population, fitness)
        if random.random() < self.crossover_rate:
            child1, child2 = self._crossover(parent1, parent2)
        else:
            child1, child2 = parent1.copy(), parent2.copy()
        if random.random() < self.mutation_rate:
            child1 = self._mutate(child1)
        new_pop.extend([child1, child2])
    population = new_pop[:self.population_size]
    fitness = [self._evaluate_fitness(chrom) for chrom in population]

# 适应度函数（含退让地带惩罚）
def _evaluate_fitness(self, individual):
    selected_nodes = [self.candidates[i] for i, bit in enumerate(individual) if bit == 1]
    cost_score = self._calculate_cost_score(selected_nodes)
    latency_score = self._calculate_latency_score(selected_nodes)
    coverage_score = self._calculate_coverage_score(selected_nodes)
    detectability_score = self._calculate_detectability_score(selected_nodes)
    base_fitness = (self.weights['cost'] * cost_score +
                    self.weights['latency'] * latency_score +
                    self.weights['coverage'] * coverage_score +
                    self.weights['detectability'] * detectability_score)
    # 退让地带惩罚
    if self.backup_weight > 0 and len(selected_nodes) > 1:
        penalty = 0.0
        for i in range(len(selected_nodes)):
            for j in range(i + 1, len(selected_nodes)):
                dist = self.candidate_dist_matrix[selected_nodes[i]][selected_nodes[j]]
                if dist <= self.backup_radius:
                    penalty += self.backup_weight * (self.backup_radius - dist + 1)
        fitness = max(0.0, base_fitness - penalty)
    return fitness
```

#### 4.2.5 优化集成器 (`optimization_integrator.py`)

**功能概述**: MoE-SHD优化流水线的核心集成器，串联安全实验、调度分析、性能测试、成本分析四大模块。

**业务处理流程**:
1. `run_optimization_pipeline()`: 启动完整优化流水线
2. `_run_security_experiment()`: 安全攻防对抗实验（SHD vs Random-K/K-Medoids）
3. `_run_scheduling_experiment()`: 专家调度模式对比（MoE vs Random-K/K-Medoids）
4. `_run_performance_experiment()`: 1000+节点性能与实时性验证
5. `_run_cost_experiment()`: 成本拆解与斯坦纳链路贡献分析
6. `_save_comprehensive_report()`: 生成综合报告

**技术设计**:
- **数学模型**: 三大全局模型（COST_MODEL / PERFORMANCE_MODEL / SECURITY_MODEL）
- **攻击模拟**: `DynamicAttackSimulator` 模拟攻击触碰概率、捕获延迟、误报率
- **调度分析**: `SchedulingFrequencyAnalyzer` 分析专家调用频率和调度模式
- **性能测试**: `LargeScalePerformanceTester` 测试500/1000/2000节点可扩展性
- **成本分析**: `CostBreakdownAnalyzer` 拆解计算/网络/部署/安全/能源成本

**核心代码片段** (优化流水线主流程 + 成本数学模型):
```python
def run_optimization_pipeline(self, network, selected_nodes, selected_edges=None):
    print("\n===== MoE-SHD优化流水线启动 =====")
    # 1. 安全攻防对抗实验
    security_results = self._run_security_experiment(network, selected_nodes)
    # 2. 专家调度模式对比
    scheduling_results = self._run_scheduling_experiment(network, selected_nodes)
    # 3. 1000+节点性能与实时性验证
    performance_results = self._run_performance_experiment()
    # 4. 成本拆解与斯坦纳链路贡献分析
    cost_results = self._run_cost_experiment(network, selected_nodes, selected_edges)
    self._save_comprehensive_report(output_dir)
    return self.results

# 全局成本数学模型
COST_MODEL = {
    'computing': {'cpu': 100, 'memory': 10, 'storage': 5},
    'network': {'bandwidth': 0.1, 'latency_factor': 0.05, 'link_construction': 100},
    'deployment': {'per_node': 500, 'maintenance_ratio': 0.4},
    'security': {'honeypot': 1000, 'firewall': 300},
    'energy_ratio': 0.15
}
```

### 4.3 评估模块 (`src/evaluation/`)

#### 4.3.1 评估器 (`evaluator.py`)

**功能概述**: 综合评估解决方案质量。

**评估指标**: 经济性得分、安全性得分、性能得分、综合得分、总成本、节点数、安全覆盖率、平均延迟、资源利用率

#### 4.3.2 帕累托分析 (`pareto.py`)

**功能概述**: 多目标优化中的帕累托前沿分析和可视化。

**数据结构**:
- `ParetoSolution`: 帕累托解决方案（目标函数值、决策变量、支配状态、拥挤距离）
- `ParetoAnalyzer`: 帕累托分析器（支配判断、快速非支配排序、拥挤距离计算）

**算法**:
- `_dominates()`: 判断支配关系
- `fast_non_dominated_sort()`: 快速非支配排序（NSGA-II）
- `compute_crowding_distance()`: 拥挤距离计算
- `plot_pareto_front()`: 二维帕累托前沿绘制
- `plot_3d_pareto_front()`: 三维帕累托前沿绘制

#### 4.3.3 调度分析器 (`scheduling_analyzer.py`)

**功能概述**: 专家调用频率分析、多算法对比（Random-K / K-Medoids / MoE）。

**数据结构**:
- `ExpertType`: 专家类型枚举（6种检测场景）
- `ExpertNode`: 专家节点数据类
- `SchedulingRecord`: 调度记录数据类
- `SchedulingFrequencyAnalyzer`: 调度频率分析器

**功能**:
- `record_scheduling()`: 记录调度行为
- `analyze_frequency_distribution()`: 分析调用频率分布
- `compare_scheduling_modes()`: 多算法对比
- `generate_visualizations()`: 生成可视化图表
- `export_analysis_report()`: 导出分析报告

#### 4.3.4 基准测试 (`benchmark.py`)

**功能概述**: 算法性能基准测试和对比。

**数据结构**:
- `BenchmarkResult`: 基准测试结果
- `AlgorithmConfig`: 算法配置
- `BenchmarkRunner`: 基准测试运行器

### 4.4 实验模块 (`src/experiments/`)

#### 4.4.1 批量测试运行器 (`batch_runner.py`)

**功能概述**: MoE-SHD算法的批量测试和结果分析。

**测试场景**: 6种标准场景（小型/中型/大型 × 稀疏/密集）
**对比算法**: MoE-SHD、Random-K、K-Medoids
**输出**: JSON结果 + CSV格式

#### 4.4.2 大规模性能测试 (`large_scale_tester.py`)

**功能概述**: 适配1000+节点的大规模性能测试。

**测试规模**: 10/50/100/500/1000/1500/2000节点
**优化技术**:
- 增量更新模式（1000+节点缓存斯坦纳树和专家权重）
- 降低连接概率避免内存溢出
- 多线程资源监控
- 实时性合规率分析

**输出**: 性能分析报告（JSON）+ 可视化图表（PNG）

#### 4.4.3 MoE-SHD包装器 (`moe_shd_wrapper.py`)

**功能概述**: MoE-SHD算法的统一接口包装器。

**算法流水线**: 数据转换 → SCB筛选 → OSE优化 → 斯坦纳树构建 → 遗传算法优化 → 评估
**模式**: 真实算法模式 / 模拟模式（组件初始化失败时自动降级）

#### 4.4.4 测试数据生成器 (`test_data_generator.py`)

**功能概述**: 生成6种标准测试场景数据。

**生成内容**: 终端节点、斯坦纳候选节点、网络边、攻击向量、约束条件
**输出格式**: JSON文件

---

## 五、工具与渲染模块

### 5.1 3D渲染引擎 (`utils/graph3d_renderer.py`)

**功能概述**: MoE-SHD 3D全息攻防沙盘渲染引擎，基于Three.js实现。

**核心类**: `Graph3DRenderer`

**业务处理流程**:
1. `build_payload()`: 构建拓扑数据（优先从后端获取，失败则生成模拟数据）
2. `render_stage_html()`: 生成Three.js HTML代码
3. 三阶段渲染：Stage1（全量网络）→ Stage2（SCB筛选）→ Stage3（斯坦纳防御拓扑）

**技术设计**:
- **数据结构**: `TopologyPayload` 包含三阶段的节点和边数据
- **场景模型**: 7种场景各有不同的节点分布和布局半径
- **节点布局**: Fibonacci球体均匀分布（多层同心球壳）
- **边生成**: 按层连接规则（Internet→Core→SCB→Aggregation→Edge→Server→Honeypot）
- **视觉升级**: 全息防御光盾、激光防线线条、攻击粒子动画、Raycaster拾取交互
- **Three.js特性**: OrbitControls轨道控制、Raycaster鼠标拾取、粒子动画、发光特效

**核心代码片段** (Fibonacci球体布局 + 三阶段筛选):
```python
# Fibonacci 球体均匀分布（多层同心球壳）
golden_ratio = (1 + 5 ** 0.5) / 2
for layer, radius in layout_radii.items():
    n = counts.get(layer, 0)
    ids = [f"{layer}_{i:02d}" for i in range(n)]
    for idx, nid in enumerate(ids):
        theta = 2 * math.pi * idx / golden_ratio
        phi = math.acos(1 - 2 * (idx + 0.5) / n)
        r = radius + rng.uniform(-radius * 0.05, radius * 0.05)
        x = r * math.sin(phi) * math.cos(theta)
        y = r * math.sin(phi) * math.sin(theta)
        z = r * math.cos(phi)

# 三阶段筛选逻辑
# Stage2: SCB筛选（度中心性 + 层权重评分）
score = {"internet": 12, "core": 11, "scb": 10, "aggregation": 8, ...}.get(layer, 2.0)
score += degree_centrality.get(node["id"], 0.0) * 7.0
keep_n = max(108, min(132, int(len(nodes1) * 0.52)))

# Stage3: 斯坦纳防御拓扑（最短路径树）
root = next(n["id"] for n in stage3_nodes if n.get("layer") in ("internet", "core"))
for target in visible:
    path = nx.shortest_path(G, root, target)
    # 提取路径边作为斯坦纳边
```

### 5.2 数据获取器 (`utils/data_fetcher.py`)

**功能概述**: 为态势指挥中心提供后端数据获取。

**核心函数**:
- `fetch_kpi_metrics()`: 获取KPI指标
- `fetch_cost_comparison()`: 获取成本对比数据
- `fetch_expert_load()`: 获取专家负载数据
- `fetch_intent_distribution()`: 获取攻击意图分布
- `fetch_attack_logs()`: 获取攻击日志

**技术设计**: `st.cache_data(ttl=10)` 缓存，`EXPERT_MAPPING` 映射攻击类型到专家名称

### 5.3 ECharts捆绑包 (`utils/echarts_bundle.py`)

**功能概述**: 自动生成的ECharts JavaScript捆绑包（Base64编码），用于前端图表渲染。

### 5.4 归一化模块 (`src/utils/normalization.py`)

**功能概述**: 提供多种数据归一化方法。

**方法**:
- Z-Score标准差归一化
- Min-Max改进区间缩放法
- 模糊隶属度归一化（Sigmoid函数）
- 小数定标归一化

**智能归一化**: `normalize_by_type()` 根据数据类型（成本/效益/安全/延迟）自动选择方法

### 5.5 约束检查器 (`src/utils/constraints.py`)

**功能概述**: 约束检查，包含租户硬隔离约束。

**核心函数**:
- `tenant_isolation_constraint()`: 多租户隔离检查
- `ConstraintChecker.check()`: 通用约束检查

### 5.6 可视化工具 (`src/utils/visualization.py`)

**功能概述**: 简化的可视化工具（占位实现）。

---

## 六、独立脚本模块 (`standalone_scripts/`)

### 6.1 3D帕累托曲面 (`pareto_3d_surface.py`)

**功能概述**: 生成3D互动帕累托曲面图，对比三种算法性能。

**技术**: Plotly + NumPy + SciPy插值
**维度**: 资源成本(X) × 链路延迟(Y) × 安全覆盖度(Z)

### 6.2 评估器 (`evaluator.py`)

**功能概述**: 独立的评估器实现（与src/evaluation/evaluator.py功能相同）。

### 6.3 调度分析器 (`scheduling_analyzer.py`)

**功能概述**: 独立的调度频率分析器（与src/evaluation/scheduling_analyzer.py功能相同）。

### 6.4 虚假专家响应器 (`fake_expert_responder.py`)

**功能概述**: 蜜罐节点的虚假专家响应生成器。

**核心功能**:
- `generate_fake_response()`: 生成虚假响应（时延、梯度掩码、载荷）
- `respond()`: 基于攻击上下文的响应生成
- 模拟响应时延分布（正态分布）、梯度掩码（稀疏张量）、响应内容

### 6.5 攻击可视化 (`makee.py`)

**功能概述**: 攻击模拟结果可视化系统。

**可视化内容**:
- 算法对比仪表盘（触碰概率、捕获延迟、斯坦纳性能、MoE性能）
- 攻击网络可视化（NetworkX图）
- 攻击时间线分析
- 详细分析报告

### 6.6 动态路径扰动 (`path_perturbation.py`)

**功能概述**: 根据网络负载和攻击行为动态调整斯坦纳树边权重。

**核心算法**:
- `_compute_load_penalty()`: 基于节点负载的惩罚
- `_compute_behavior_penalty()`: 基于攻击行为的惩罚
- 综合调整因子 = 1.0 + 负载惩罚 + 行为惩罚 + 随机扰动

### 6.7 成本测试 (`cost.py`)

**功能概述**: 测试scikit-learn导入的简单脚本。

---

## 七、配置文件模块 (`configs/`)

### 7.1 默认配置 (`default_config.yaml`)

**配置项**:
- 项目信息（名称、版本）
- 场景配置（4种场景的权重）
- 网络参数（节点数、连接概率）
- 算法参数（SCB筛选、遗传算法）
- 约束参数（预算、延迟、安全覆盖）
- 可视化配置

### 7.2 路径配置 (`paths.py`)

**功能**: 项目目录结构定义和创建。

**目录结构**: configs/、results/、data/、src/、tests/、docs/

---

## 八、gRPC Proto 定义

项目四层架构（前端展示层 → 后端服务层 → 核心算法层 → 工具与渲染层）之间通过标准化 RESTful API 与 gRPC 协议通信。以下是核心 gRPC 服务定义：

### 8.1 拓扑服务 (TopologyService)

```protobuf
syntax = "proto3";

package honeynet.topology;

// 拓扑服务：提供三阶段拓扑数据的推送与查询
service TopologyService {
    // 服务端推送三阶段拓扑数据（Streaming）
    rpc StreamTopology(TopologyRequest) returns (stream TopologyPayload);
    
    // 客户端主动拉取当前阶段拓扑
    rpc GetTopology(TopologyRequest) returns (TopologyPayload);
    
    // 上报节点状态变更
    rpc ReportNodeStatus(NodeStatus) returns (StatusAck);
}

// 拓扑请求
message TopologyRequest {
    string scene_id = 1;          // 场景ID（通用数据中心/金融结算中心等）
    int32 stage = 2;              // 阶段（0=Base / 1=SCB Filter / 2=Steiner）
    bool include_metrics = 3;     // 是否包含数学模型指标
}

// 拓扑载荷（三阶段）
message TopologyPayload {
    StageData stage1 = 1;         // 全量网络拓扑
    StageData stage2 = 2;         // SCB筛选后拓扑
    StageData stage3 = 3;         // 斯坦纳防御拓扑
    Metrics metrics = 4;          // 数学模型指标
    double timestamp = 5;         // 时间戳
}

// 单阶段拓扑数据
message StageData {
    repeated Node nodes = 1;      // 节点列表
    repeated Edge edges = 2;      // 边列表
    int32 node_count = 3;
    int32 edge_count = 4;
}

// 节点定义
message Node {
    string id = 1;                // 节点ID（如 "core_00", "honeypot_03"）
    string layer = 2;             // 层级（internet/core/scb/aggregation/edge/server/honeypot）
    float x = 3;                  // 3D坐标X
    float y = 4;                  // 3D坐标Y
    float z = 5;                  // 3D坐标Z
    float size = 6;               // 节点大小
    string color = 7;             // 节点颜色（十六进制）
    bool is_honeypot = 8;         // 是否为蜜罐节点
    map<string, string> labels = 9; // 附加标签
}

// 边定义
message Edge {
    string source = 1;            // 源节点ID
    string target = 2;            // 目标节点ID
    float weight = 3;             // 边权重（成本/延迟）
    string color = 4;             // 边颜色
    string style = 5;             // 线条样式（solid/dashed/dotted）
    bool is_steiner = 6;          // 是否为斯坦纳树边
}

// 数学模型指标
message Metrics {
    double total_cost = 1;        // 综合成本 F(Sol)
    double resource_cost = 2;     // 资源成本 ĈR
    double latency_cost = 3;      // 延迟成本 ĈL
    double security_loss = 4;     // 安全损失 Ŝloss
    double budget_remaining = 5;  // 预算剩余
    double latency_headroom = 6;  // 延迟余量
    double coverage_rate = 7;     // 安全覆盖率
    bool budget_ok = 8;           // 预算约束是否满足
    bool latency_ok = 9;          // 延迟约束是否满足
    bool coverage_ok = 10;        // 覆盖约束是否满足
}

// 节点状态上报
message NodeStatus {
    string node_id = 1;
    string status = 2;            // online/offline/attacked/recovered
    double cpu_load = 3;
    double memory_usage = 4;
    int32 active_connections = 5;
}

message StatusAck {
    bool success = 1;
    string message = 2;
}
```

### 8.2 攻击检测服务 (AttackDetectionService)

```protobuf
package honeynet.security;

// 攻击检测服务：B组攻击检测接口
service AttackDetectionService {
    rpc Detect(DetectionRequest) returns (DetectionResponse);
    rpc StreamAlerts(AlertSubscription) returns (stream SecurityAlert);
}

message DetectionRequest {
    string text = 1;              // 用户输入文本
    string session_id = 2;        // 会话ID
    map<string, string> context = 3; // 上下文信息
}

message DetectionResponse {
    bool is_malicious = 1;        // 是否为恶意请求
    double confidence = 2;        // 置信度 [0, 1]
    repeated string attack_types = 3; // 匹配的攻击类型列表
    repeated string matched_keywords = 4; // 匹配的关键词
    double risk_score = 5;        // 风险评分 [0, 100]
}

message AlertSubscription {
    string client_id = 1;
    repeated string alert_levels = 2; // 告警等级过滤
}

message SecurityAlert {
    string alert_id = 1;
    string attack_type = 2;
    string source_ip = 3;
    string target_node = 4;
    double severity = 5;          // 严重程度 [0, 1]
    double timestamp = 6;
    string description = 7;
}
```

### 8.3 调度服务 (SchedulingService)

```protobuf
package honeynet.scheduling;

// 专家调度服务：MoE专家路由与调度
service SchedulingService {
    rpc Schedule(ScheduleRequest) returns (ScheduleResponse);
    rpc GetExpertStatus(ExpertQuery) returns (ExpertStatusList);
}

message ScheduleRequest {
    string task_id = 1;
    string input_type = 2;        // 输入类型（text/image/code）
    map<string, double> requirements = 3; // 任务需求（延迟/精度/成本要求）
}

message ScheduleResponse {
    string expert_id = 1;         // 选中的专家节点ID
    string expert_type = 2;       // 专家类型
    double confidence = 3;
    double estimated_latency = 4;
    double estimated_cost = 5;
}

message ExpertQuery {
    repeated string expert_ids = 1;
}

message ExpertStatusList {
    repeated ExpertStatus experts = 1;
}

message ExpertStatus {
    string expert_id = 1;
    string expert_type = 2;
    double load = 3;              // 当前负载 [0, 1]
    int32 active_tasks = 4;
    double avg_latency = 5;
    string status = 6;            // idle/busy/offline
}
```

### 8.4 蜜罐服务 (HoneypotService)

```protobuf
package honeynet.honeypot;

// 蜜罐服务：虚假响应生成与攻击诱捕
service HoneypotService {
    rpc ProcessAttack(AttackRequest) returns (FakeResponse);
    rpc GetHoneypotStatus(Empty) returns (HoneypotStatus);
}

message AttackRequest {
    string original_message = 1;
    string attack_type = 2;
    repeated string matched_keywords = 3;
    double confidence = 4;
    string session_id = 5;
}

message FakeResponse {
    string response_text = 1;     // 虚假响应文本
    double confidence = 2;        // 伪造置信度
    string honeypot_node = 3;     // 响应的蜜罐节点ID
    map<string, string> fake_metadata = 4; // 伪造元数据
}

message HoneypotStatus {
    int32 total_intercepted = 1;
    int32 active_sessions = 2;
    map<string, int32> attack_type_counts = 3;
    double avg_response_time = 4;
}

message Empty {}
```

---

## 九、关键技术总结

### 9.1 核心算法
- **斯坦纳树优化**: 最小斯坦纳树构建，用于蜜罐最优部署
- **SCB筛选**: 基于安全/成本/平衡的多因子筛选
- **遗传算法**: 种群规模100，200代迭代，精英保留策略
- **帕累托优化**: 多目标优化（成本/延迟/安全覆盖度）

### 9.2 约束体系（8大约束）
| 编号 | 约束名称 | 实现位置 |
|------|---------|---------|
| 1 | 服务唯一部署约束 | `nodes.py` |
| 2 | 斯坦纳节点强有效性约束 | `nodes.py` |
| 3 | 全生命周期预算约束 | `nodes.py` |
| 4 | 分层延迟硬约束 | `edges.py` |
| 5 | 加权安全覆盖约束 | 数学模型 |
| 6 | 节点资源三维约束 | `nodes.py` + `edges.py` |
| 7 | 流守恒/无环约束 | `edges.py` |
| 8 | 蜜罐伪装有效性约束 | `nodes.py` |

### 9.3 攻击检测体系
- **7大类攻击**: SQL注入、XSS、命令注入、暴力破解、文件上传、CSRF/SSRF、提示词注入
- **100+正则规则**: 覆盖所有攻击场景
- **双重判定**: 关键词匹配 + B组API辅助判定
- **置信度计算**: 基于匹配数量和关键词的加权计算

### 9.4 前端技术栈
- **Streamlit**: 算法工作台 + 态势指挥中心
- **Flask**: 蜜罐攻击仿真
- **Three.js**: 3D拓扑可视化
- **ECharts/Plotly**: 数据图表
- **Chart.js**: 实时攻击面分布

### 9.5 后端技术栈
- **FastAPI**: 网关服务 + 蜜罐服务
- **Pydantic**: 数据模型验证
- **NetworkX**: 图算法（斯坦纳树、最短路径）
- **NumPy/SciPy**: 数值计算和插值


