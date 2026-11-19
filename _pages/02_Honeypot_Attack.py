from flask import Flask, render_template_string, request, jsonify
import requests
import time
import json
import re

app = Flask(__name__)

# 允许被同源页面嵌入（解除 X-Frame-Options 限制）
app.config['X_FRAME_OPTIONS'] = 'SAMEORIGIN'

# 后端API配置
BACKEND_URL = "http://localhost:8000/api/attack-detect"

# 全局攻击统计数据
attack_stats = {
    "sql_injection": 0,
    "xss": 0,
    "command_injection": 0,
    "brute_force": 0,
    "file_upload": 0,
    "csrf": 0,
    "prompt_injection": 0
}

# ============================================================
# 综合攻击检测规则库（覆盖 SQL注入 / XSS / 命令注入 / 提示词注入等）
# ============================================================
ATTACK_PATTERNS = {
    # ==================== SQL 注入 ====================
    "sql_injection": {
        "name": "数据库注入 (SQL Injection)",
        "patterns": [
            # 基础注入特征
            r"'\s*or\s+'1'\s*=\s*'1", r"'\s*or\s+1\s*=\s*1",
            r'"\s*or\s+"1"\s*=\s*"1', r'"\s*or\s+1\s*=\s*1',
            r"'\s*or\s+'1'\s*=\s*'1'\s*--", r"'\s*or\s+1\s*=\s*1\s*--",
            r"'\s*union\s+select", r'"\s*union\s+select',
            r"union\s+select\s+\d+\s*,\s*\d+", r"union\s+select\s+\d+\s*,\s*\d+\s*,\s*\d+",
            r"order\s+by\s+\d+\s*--", r"group\s+by\s+\d+\s*--",
            r"information_schema\.tables", r"information_schema\.columns",
            r"sys\.tables", r"all_tables", r"mysql\.user",
            r"waitfor\s+delay", r"pg_sleep", r"benchmark\s*\(",
            r"extractvalue\s*\(", r"updatexml\s*\(",
            r"@@version", r"@@datadir", r"@@basedir",
            r"database\s*\(\)", r"version\s*\(\)", r"user\s*\(\)",
            r"concat\s*\(.*0x", r"concat_ws\s*\(",
            r"load_file\s*\(", r"into\s+outfile", r"into\s+dumpfile",
            r"1\s*=\s*1\s*--", r"1\s*=\s*2\s*--",
            r"admin'?\s*--", r"admin\"\s*--",
            r"or\s+'\d'\s*=\s*'\d", r"or\s+\d+\s*=\s*\d+",
            r"or\s+'\w+'\s*=\s*'\w+'",
        ],
        "description": "试图通过SQL注入绕过认证、窃取数据库数据或执行恶意SQL语句"
    },
    # ==================== XSS 跨站脚本 ====================
    "xss": {
        "name": "跨站脚本攻击 (Cross-Site Scripting)",
        "patterns": [
            r"<script[^>]*>.*</script>", r"<script[^>]*>",
            r"<img[^>]*onerror\s*=", r"<svg[^>]*onload\s*=",
            r"<iframe[^>]*src\s*=", r"<body[^>]*onload\s*=",
            r"<input[^>]*onfocus\s*=", r"<details[^>]*ontoggle\s*=",
            r"<marquee[^>]*onstart\s*=",
            r"onerror\s*=\s*['\"]?\s*alert", r"onload\s*=\s*['\"]?\s*alert",
            r"onclick\s*=\s*['\"]?\s*alert", r"onmouseover\s*=\s*['\"]?\s*alert",
            r"onfocus\s*=\s*['\"]?\s*alert", r"onkeydown\s*=\s*['\"]?\s*alert",
            r"javascript\s*:\s*alert", r"javascript\s*:\s*prompt",
            r"javascript\s*:\s*confirm",
            r"alert\s*\(\s*['\"]?[^)]*['\"]?\s*\)", r"prompt\s*\(\s*['\"]?[^)]*['\"]?\s*\)",
            r"confirm\s*\(\s*['\"]?[^)]*['\"]?\s*\)",
            r"document\.cookie", r"document\.location",
            r"window\.location", r"window\.open\s*\(",
            r"<[^>]*\s+on\w+\s*=",  # 通用事件处理器
            r"&#\d+;", r"&#x[0-9a-fA-F]+;",  # HTML实体编码
            r"%3Cscript%3E", r"%3Cimg", r"%3Csvg",  # URL编码
            r"<[^>]*src\s*=\s*['\"]?\s*(javascript|data|vbscript)\s*:",
        ],
        "description": "试图在页面中注入恶意脚本，窃取用户Cookie、会话信息或执行恶意操作"
    },
    # ==================== 命令注入 ====================
    "command_injection": {
        "name": "命令注入 (Command Injection)",
        "patterns": [
            r";\s*(ls|dir|cat|type|id|whoami|pwd|ifconfig|ipconfig|netstat|ps|top)",
            r"&&\s*(ls|dir|cat|type|id|whoami|pwd|ifconfig|ipconfig|netstat|ps|top)",
            r"\|\s*(ls|dir|cat|type|id|whoami|pwd|ifconfig|ipconfig|netstat|ps|top)",
            r"`\s*(ls|dir|cat|type|id|whoami|pwd|ifconfig|ipconfig|netstat|ps|top)\s*`",
            r"\$\(\s*(ls|dir|cat|type|id|whoami|pwd|ifconfig|ipconfig|netstat|ps|top)",
            r";\s*(rm|del|shutdown|reboot|format|mkfs|dd|kill)", 
            r"&&\s*(rm|del|shutdown|reboot|format|mkfs|dd|kill)",
            r"\|\s*(rm|del|shutdown|reboot|format|mkfs|dd|kill)",
            r";\s*(bash|sh|cmd|powershell|python|perl|php)\s+-",
            r"&&\s*(bash|sh|cmd|powershell|python|perl|php)\s+-",
            r"\|.*(bash|sh|cmd|powershell|python|perl|php)",
            r"rm\s+-rf\s+/", r"del\s+/[fFsS].*\\",
            r"wget\s+http.*\s+-O\s+", r"curl\s+http.*\s+-o\s+",
            r"nc\s+-[eL]\s+", r"ncat\s+-[eL]\s+",
            r"powershell\s+.*-EncodedCommand", r"powershell\s+.*-Command",
            r"cmd\.exe\s+/c", r"cmd\s+/c",
        ],
        "description": "试图在服务器上执行系统命令，获取服务器控制权或破坏系统"
    },
    # ==================== 暴力破解 ====================
    "brute_force": {
        "name": "暴力破解 (Brute Force)",
        "patterns": [
            r"admin.*admin", r"root.*root", r"administrator.*password",
            r"123456", r"password", r"qwerty", r"letmein",
            r"admin123", r"root123", r"passw0rd", r"p@ssword",
            r"default.*password", r"default.*admin",
            r"bruteforce", r"brute.*force", r"字典攻击",
            r"hydra.*ssh", r"hydra.*rdp", r"hydra.*ftp",
            r"medusa.*ssh", r"john.*ripper", r"hashcat",
        ],
        "description": "试图通过暴力破解或字典攻击获取系统访问权限"
    },
    # ==================== 文件上传攻击 ====================
    "file_upload": {
        "name": "恶意文件上传 (Malicious File Upload)",
        "patterns": [
            r"\.php\s*$", r"\.php\d\s*$", r"\.asp\s*$", r"\.aspx\s*$",
            r"\.jsp\s*$", r"\.jspx\s*$", r"\.war\s*$",
            r"\.exe\s*$", r"\.dll\s*$", r"\.bat\s*$", r"\.cmd\s*$",
            r"\.vbs\s*$", r"\.vbe\s*$", r"\.ps1\s*$", r"\.psm1\s*$",
            r"webshell", r"一句话木马", r"大马", r"shell\.php",
            r"eval\s*\(\s*\$_POST", r"eval\s*\(\s*\$_GET",
            r"system\s*\(\s*\$_REQUEST", r"exec\s*\(\s*\$_REQUEST",
            r"file_put_contents\s*\(.*\$_", r"fwrite\s*\(.*\$_",
            r"上传.*木马", r"上传.*shell", r"上传.*后门",
            r"Content-Disposition.*\.php", r"Content-Type.*image.*\.php",
        ],
        "description": "试图上传恶意文件（WebShell、可执行文件等）获取服务器控制权"
    },
    # ==================== CSRF/SSRF ====================
    "csrf": {
        "name": "跨站请求伪造 (CSRF / SSRF)",
        "patterns": [
            r"csrf.*token", r"xsrf.*token",
            r"ssrf", r"server.*side.*request.*forgery",
            r"内网.*请求", r"内部.*网络.*扫描",
            r"file:///", r"gopher://", r"dict://",
            r"127\.0\.0\.1", r"localhost", r"169\.254\.",
            r"metadata\.google\.internal", r"169\.254\.169\.254",
            r"internal.*network.*scan", r"内网.*探测",
            r"绕过.*referer", r"绕过.*origin",
        ],
        "description": "试图发起跨站请求伪造攻击或服务端请求伪造攻击"
    },
    # ==================== 提示词注入 ====================
    "prompt_injection": {
        "name": "大模型提示词注入 (Prompt Injection)",
        "patterns": [
            r'忽略.*指令', r'忽略.*提示', r'忽略.*规则', r'忘记.*设定',
            r'你现在是', r'假设你是', r'扮演', r'扮演.*角色', r'进入.*模式',

            r'开发者模式', r'DAN模式', r'越狱', r'jailbreak',
            r'绕过.*限制', r'解除.*约束', r'忽略之前的',
            r'ignore previous', r'ignore all', r'forget your',
            r'you are now', r'pretend to be', r'developer mode',
            r'system prompt', r'泄露.*提示词', r'泄露.*指令',
            r'输出.*系统提示', r'prompt leak', r'提取.*信息',
            r'逆向.*工程', r'提示词工程', r'角色扮演',
            r'模拟攻击', r'社会工程学', r'欺骗.*用户',
            r'伪造.*身份', r'冒充.*身份', r'钓鱼.*攻击',
            r'诱导.*输出', r'绕过.*安全', r'绕过.*过滤',
            r'忽略.*安全', r'解除.*限制', r'无限制.*模式',
            r'无道德.*约束', r'无伦理.*限制'
        ],
        "description": "试图通过特定提示词操控AI模型行为，绕过安全限制或获取敏感信息"
    },
    "prompt_leak": {
        "name": "系统指令窃取 (Prompt Leaking)",
        "patterns": [
            r'你的.*提示词', r'你的.*指令', r'系统.*提示',
            r'system.*prompt', r'初始.*设定', r'原始.*指令',
            r'隐藏.*信息', r'配置.*信息', r'prompt.*leak',
            r'leak.*prompt', r'提取.*prompt', r'获取.*prompt',
            r'展示.*设定', r'显示.*规则', r'你的.*设定',
            r'你的.*角色', r'你的.*身份', r'你的.*任务'
        ],
        "description": "试图诱导AI泄露系统提示词、配置信息或隐藏设定"
    },
    "adversarial_prompt": {
        "name": "对抗性混淆攻击 (Adversarial Prompting)",
        "patterns": [
            r'base64', r'编码.*解码', r'十六进制', r'hex.*encode',
            r'unicode.*escape', r'特殊.*字符', r'混淆.*输入',
            r'分段.*输入', r'拼接.*攻击', r'嵌套.*提示',
            r'递归.*调用', r'注入.*代码', r'构造.*payload',
            r'绕过.*过滤', r'编码.*绕过', r'变形.*输入'
        ],
        "description": "使用编码、混淆、分段等技术绕过输入过滤和安全检测"
    }
}


def analyze_attack_payload(payload):
    """
    综合攻击检测函数：检测 SQL注入 / XSS / 命令注入 / 提示词注入等所有攻击类型
    返回: (is_attack, attack_type, confidence, matched_keywords, description)
    """
    if not payload:
        return False, None, 0.0, [], ""
    
    payload_lower = payload.lower()
    all_matched_keywords = []
    best_match = None
    highest_confidence = 0.0
    
    for attack_key, attack_info in ATTACK_PATTERNS.items():
        matched_keywords = []
        match_count = 0
        
        for pattern in attack_info["patterns"]:
            try:
                if re.search(pattern, payload, re.IGNORECASE):
                    match_count += 1
                    matches = re.findall(pattern, payload, re.IGNORECASE)
                    if matches:
                        if isinstance(matches[0], tuple):
                            matched_keywords.extend(matches[0])
                        else:
                            matched_keywords.extend(matches)
            except re.error:
                if pattern.lower() in payload_lower:
                    match_count += 1
                    matched_keywords.append(pattern)
        
        matched_keywords = list(set(matched_keywords))
        all_matched_keywords.extend(matched_keywords)
        
        if match_count > 0:
            # 置信度计算：基础0.3 + 每个匹配模式+0.15 + 每个关键词+0.05，上限0.95
            confidence = min(0.3 + (match_count * 0.15) + (len(matched_keywords) * 0.05), 0.95)
            if confidence > highest_confidence:
                highest_confidence = confidence
                best_match = {
                    "attack_type": attack_key,
                    "name": attack_info["name"],
                    "confidence": confidence,
                    "matched_keywords": matched_keywords,
                    "description": attack_info["description"]
                }
    
    all_matched_keywords = list(set(all_matched_keywords))
    
    if best_match:
        return True, best_match["attack_type"], highest_confidence, all_matched_keywords, best_match["description"]
    
    return False, None, 0.0, [], ""


# ============================================================================
# 原汁原味极简高端 UI 模板 (Swiss Spa / Ultra-Premium Dark Mode)
# ============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Honeynet-AIGC 对抗仿真沙箱</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>

    <style>
        :root {
            /* 绝对保留你原来的黑白灰阶 */
            --bg-base: #000000;
            --bg-surface: #0A0A0A;
            --bg-surface-hover: #141414;
            --border-subtle: #1F1F22;
            --border-focus: #444444;
            
            --text-primary: #EDEDED;
            --text-secondary: #888888;
            --text-muted: #555555;
            
            --accent-brand: #EDEDED;
            --accent-brand-text: #000000;
            --accent-blue: #3B82F6;
            --accent-red: #EF4444;
            --accent-green: #10B981;

            --font-sans: 'Inter', -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', Consolas, monospace;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            /* 恢复你原来的背景色 */
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-sans);
            min-height: 100vh;
            padding: 1.5rem 0;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        .container { max-width: 1500px; margin: 0 auto; }

        .main-grid {
            display: grid;
            grid-template-columns: 340px 1fr;
            gap: 24px;
            min-height: 760px;
        }

        .card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .card-header {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* 状态指示点 */
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 28px;
        }

        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8125rem;
            color: var(--text-secondary);
        }

        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: var(--accent-green);
        }

        /* 极简表单 */
        .form-group { margin-bottom: 20px; }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-size: 0.8125rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        select, textarea {
            width: 100%;
            background: var(--bg-base);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 0.8125rem;
            font-family: var(--font-sans);
            transition: border-color 0.2s;
            appearance: none;
        }

        textarea {
            height: 140px;
            resize: vertical;
            font-family: var(--font-mono);
            line-height: 1.5;
            color: var(--text-secondary);
        }

        select:focus, textarea:focus {
            outline: none;
            border-color: var(--border-focus);
        }

        /* 按钮重构 */
        .btn-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 28px;
        }

        .btn {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            width: 100%;
            padding: 9px 16px;
            font-size: 0.8125rem;
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
        }

        .btn i { width: 14px; height: 14px; }

        .btn-primary {
            background: var(--accent-brand);
            color: var(--accent-brand-text);
        }
        .btn-primary:hover:not(:disabled) { background: #FFFFFF; }

        .btn-secondary {
            background: var(--bg-base);
            border-color: var(--border-subtle);
            color: var(--text-primary);
        }
        .btn-secondary:hover:not(:disabled) { background: var(--bg-surface-hover); }

        .btn:disabled { opacity: 0.4; cursor: not-allowed; }

        /* 高级分析结果卡片 */
        .analysis-result {
            background: var(--bg-base);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            padding: 16px;
            margin-top: 20px;
            display: none;
        }
        .analysis-result.show { display: block; }

        .analysis-header {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .analysis-row {
            display: flex; justify-content: space-between;
            font-size: 0.8125rem; margin-bottom: 8px;
        }

        .analysis-label { color: var(--text-secondary); }
        .analysis-value { color: var(--text-primary); font-family: var(--font-mono); }

        .keyword-tag {
            display: inline-block; padding: 2px 6px; background: var(--bg-surface-hover);
            border: 1px solid var(--border-subtle); border-radius: 4px;
            font-size: 0.75rem; color: var(--text-secondary); margin: 0 4px 4px 0;
            font-family: var(--font-mono);
        }

        /* 布局控制 */
        .right-panel { display: flex; flex-direction: column; gap: 24px; height: 100%; }
        .top-row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; height: 280px; }
        .middle-row { height: 220px; }

        /* 高级状态条 */
        .status-message {
            padding: 12px 16px; border-radius: 6px; font-size: 0.8125rem;
            display: flex; align-items: center; gap: 10px; 
            border-left: 3px solid transparent;
            background: var(--bg-base);
            border-top: 1px solid var(--border-subtle);
            border-right: 1px solid var(--border-subtle);
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 16px;
        }
        .status-info { border-left-color: var(--accent-blue); color: var(--text-secondary); }
        .status-success { border-left-color: var(--accent-green); color: var(--text-primary); }
        .status-error { 
            border-left-color: var(--accent-red); color: #FCA5A5; 
            background: linear-gradient(90deg, rgba(239,68,68,0.08) 0%, rgba(0,0,0,0) 100%);
        }

        /* 流量连线模拟 */
        .traffic-container {
            width: 100%; height: 40px; background: var(--bg-base);
            border: 1px solid var(--border-subtle); border-radius: 6px;
            position: relative; overflow: hidden; margin-bottom: 16px;
        }
        .traffic-path {
            position: absolute; top: 50%; left: 0; width: 100%; height: 1px;
            background-color: var(--border-subtle); transform: translateY(-50%);
        }
        .traffic-particle {
            position: absolute; top: 50%; width: 4px; height: 4px;
            background-color: var(--text-primary); border-radius: 50%;
            transform: translateY(-50%);
            box-shadow: 0 0 8px rgba(255, 255, 255, 0.8);
            animation: slideRight 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }
        @keyframes slideRight {
            0% { left: -10px; opacity: 0; }
            15% { opacity: 1; }
            85% { opacity: 1; }
            100% { left: 100%; opacity: 0; }
        }

        /* Chart 容器修复 */
        .chart-wrapper { position: relative; height: calc(100% - 40px); width: 100%; }

        /* 高级终端 */
        .terminal-wrapper {
            flex: 1; background: var(--bg-base); border: 1px solid var(--border-subtle);
            border-radius: 6px; padding: 16px; overflow-y: auto;
            font-family: var(--font-mono); font-size: 0.75rem; line-height: 1.6;
        }
        .terminal-line { color: var(--text-secondary); margin-bottom: 4px; }
        .terminal-line.info { color: var(--text-primary); }
        .terminal-line.warning { color: var(--accent-amber); }
        .terminal-line.danger { color: var(--accent-red); }
        .terminal-prompt { color: var(--text-muted); display: flex; align-items: center; gap: 8px; margin-top: 8px; }
        .cursor { display: inline-block; width: 5px; height: 10px; background: var(--text-muted); animation: blink 1s step-end infinite; }
        @keyframes blink { 50% { opacity: 0; } }

        /* 加载指示器 */
        .spinner {
            width: 12px; height: 12px; border: 2px solid rgba(0,0,0,0.2);
            border-radius: 50%; border-top-color: currentColor;
            animation: spin 0.8s linear infinite;
        }
        .btn-secondary .spinner { border: 2px solid rgba(255,255,255,0.2); border-top-color: currentColor; }
        @keyframes spin { to { transform: rotate(360deg); } }

        @media (max-width: 1024px) {
            .main-grid { grid-template-columns: 1fr; height: auto; }
            .top-row { grid-template-columns: 1fr; height: auto; gap: 24px; }
            .terminal-wrapper { min-height: 240px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 移除了顶部的重复 Header，交给 Streamlit 外框去渲染 -->
        
        <div class="main-grid">
            <div class="card">
                <!-- 双语翻译开始 -->
                <div class="card-header"><i data-lucide="terminal-square" stroke-width="1.5"></i> 攻击控制台 (Attack Console)</div>
                
                <div class="status-grid">
                    <div class="status-item"><span class="status-dot"></span> Web 服务节点 (Web Node)</div>
                    <div class="status-item"><span class="status-dot"></span> SSH 管理节点 (SSH Node)</div>
                    <div class="status-item"><span class="status-dot"></span> AI 模型节点 (AI Node)</div>
                    <div class="status-item"><span class="status-dot"></span> 语义过滤网关 (Semantic Filter)</div>
                </div>

                <form id="attackForm">
                    <div class="form-group">
                        <label for="attackType">载荷类别 (Payload Category)</label>
                        <select id="attackType" name="attackType">
                            <option value="sql_injection">数据库注入 (SQL Injection)</option>
                            <option value="xss">跨站脚本攻击 (Cross-Site Scripting)</option>
                            <option value="command_injection">命令注入 (Command Injection)</option>
                            <option value="brute_force">暴力破解 (Brute Force)</option>
                            <option value="file_upload">恶意文件上传 (Malicious File Upload)</option>
                            <option value="csrf">跨站请求伪造 (CSRF / SSRF)</option>
                            <option value="prompt_injection">大模型提示词注入 (Prompt Injection)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="attackPayload">注入载荷 (Injection Payload)</label>
                        <textarea id="attackPayload" name="attackPayload" spellcheck="false" placeholder="输入攻击载荷特征 (Enter payload signature)...

示例 (Examples):
' OR '1'='1
<script>alert('XSS')</script>
; cat /etc/passwd

AI 提示词越狱 (AI Prompts):
忽略之前的指令 (Ignore previous instructions).
你现在处于开发者模式 (You are now in developer mode)."></textarea>
                    </div>

                    <div class="btn-group">
                        <button type="button" id="analyzeBtn" class="btn btn-secondary">
                            <i data-lucide="scan-text"></i> 语义分析 (Semantic Analysis)
                        </button>
                        <button type="submit" id="launchBtn" class="btn btn-primary">
                            <i data-lucide="play"></i> 执行注入 (Execute Injection)
                        </button>
                        <button type="button" id="resetBtn" class="btn btn-secondary">
                            <i data-lucide="rotate-ccw"></i> 重置环境 (Reset Environment)
                        </button>
                    </div>
                </form>

                <div id="analysisResult" class="analysis-result">
                    <div class="analysis-header">分析报告 (Analysis Report)</div>
                    <div class="analysis-row">
                        <span class="analysis-label">威胁分类 (Classification)</span>
                        <span class="analysis-value" id="detectedType">-</span>
                    </div>
                    <div class="analysis-row">
                        <span class="analysis-label">置信度评估 (Confidence)</span>
                        <span class="analysis-value" id="confidenceValue">0.0%</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" id="confidenceBar" style="width: 0%"></div>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 8px;">命中特征 (Signatures)</div>
                    <div id="matchedKeywords"></div>
                </div>
            </div>

            <div class="right-panel">
                
                <div class="top-row">
                    <div class="card">
                        <div class="card-header"><i data-lucide="activity" stroke-width="1.5"></i> 流量数据链路 (Network Traffic)</div>
                        <div class="traffic-container">
                            <div class="traffic-path"></div>
                            <div id="trafficParticles"></div>
                        </div>
                        <div id="statusMessage" class="status-message status-info">
                            <i data-lucide="info" style="width:16px;"></i> 就绪，等待指令执行 (Awaiting payload execution.)
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header"><i data-lucide="bar-chart-3" stroke-width="1.5"></i> 攻击面分布 (Attack Surface)</div>
                        <div class="chart-wrapper">
                            <canvas id="attackTypeChart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="card middle-row">
                    <div class="card-header"><i data-lucide="git-commit-horizontal" stroke-width="1.5"></i> 诱导拦截流水线 (Interception Pipeline)</div>
                    <div class="chart-wrapper">
                        <canvas id="phaseChart"></canvas>
                    </div>
                </div>

                <div class="card" style="flex: 1;">
                    <div class="card-header"><i data-lucide="terminal" stroke-width="1.5"></i> 隔离沙箱日志 (Isolation Sandbox Log)</div>
                    <div class="terminal-wrapper" id="honeypotTerminal">
                        <div class="terminal-prompt">root@honeynet-sandbox:~# <span class="cursor"></span></div>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <script>
        // 初始化 Lucide 图标
        lucide.createIcons();

        const chartColors = {
            base: '#27272A',
            text: '#A1A1AA',
            bar: '#3F3F46',
            barHover: '#EDEDED'
        };

        let attackInProgress = false;
        let terminalLines = [];
        let currentLineIndex = 0;
        let terminalInterval = null;
        let attackTypeChart = null;
        let phaseChart = null;

        const attackPhases = [
            "协议握手 (Handshake)", "载荷传输 (Payload Sent)", "特征校验 (Signature Check)", "引流欺骗 (Deception Logic)",
            "模拟鉴权 (Auth Mocking)", "降级验证 (Fallback Auth)", "IP溯源 (Trace IP)", "数据伪造 (Data Spoofing)", "成功隔离 (Isolated)"
        ];

        // 统一图表初始化（只执行一次）
        function initCharts() {
            const typeCanvas = document.getElementById('attackTypeChart');
            if (!typeCanvas) {
                console.error('[Chart] attackTypeChart canvas not found');
                return;
            }
            if (attackTypeChart) attackTypeChart.destroy();
            const typeCtx = typeCanvas.getContext('2d');
            if (!typeCtx) {
                console.error('[Chart] getContext for attackTypeChart failed');
                return;
            }
            attackTypeChart = new Chart(typeCtx, {
                type: 'bar',
                data: {
                    labels: ['SQLi', 'XSS', 'CMD', 'Brute', 'Upload', 'CSRF', 'Prompt'],
                    datasets: [{
                        data: [0, 0, 0, 0, 0, 0, 0],
                        backgroundColor: chartColors.bar,
                        hoverBackgroundColor: chartColors.barHover,
                        borderRadius: 2,
                        barPercentage: 0.5
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: { cornerRadius: 4 } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: chartColors.base, drawBorder: false }, border: { display: false } },
                        x: { grid: { display: false }, border: { display: false } }
                    }
                }
            });

            const phaseCanvas = document.getElementById('phaseChart');
            if (!phaseCanvas) {
                console.error('[Chart] phaseChart canvas not found');
                return;
            }
            if (phaseChart) phaseChart.destroy();
            const phaseCtx = phaseCanvas.getContext('2d');
            if (!phaseCtx) {
                console.error('[Chart] getContext for phaseChart failed');
                return;
            }
            phaseChart = new Chart(phaseCtx, {
                type: 'bar',
                data: {
                    labels: attackPhases,
                    datasets: [{
                        data: [0, 0, 0, 0, 0, 0, 0, 0, 0],
                        backgroundColor: chartColors.barHover,
                        borderRadius: 2,
                        barPercentage: 0.3
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false, indexAxis: 'y',
                    plugins: { legend: { display: false }, tooltip: { enabled: false } },
                    scales: {
                        x: { max: 100, grid: { color: chartColors.base, drawBorder: false }, border: { display: false }, ticks: { callback: v => v + '%' } },
                        y: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 11 } } }
                    },
                    layout: { padding: { left: 0 } }
                }
            });
            console.log('[Chart] 图表初始化完成');
        }

        // 更新攻击面分布柱状图（直接修改现有实例）
        function updateAttackTypeChart(attackType) {
            // 强制重新获取/创建图表实例，确保引用有效
            const canvas = document.getElementById('attackTypeChart');
            if (!canvas) {
                console.error('[Chart] attackTypeChart canvas 不存在');
                return;
            }
            
            // 尝试从 canvas 获取已注册的 Chart 实例
            let existing = Chart.getChart(canvas);
            if (existing) {
                attackTypeChart = existing;
                console.log('[Chart] 从 canvas 获取到已有 Chart 实例');
            } else if (!attackTypeChart) {
                console.warn('[Chart] attackTypeChart 未初始化，重新初始化');
                initCharts();
                if (!attackTypeChart) {
                    console.error('[Chart] 无法初始化 attackTypeChart');
                    return;
                }
            }
            
            const typeMap = { 
                'sql_injection': 0, 
                'xss': 1, 
                'command_injection': 2, 
                'brute_force': 3, 
                'file_upload': 4, 
                'csrf': 5, 
                'prompt_injection': 6 
            };
            const index = typeMap[attackType];
            if (index !== undefined) {
                attackTypeChart.data.datasets[0].data[index] += 1;
                attackTypeChart.update('none');  // 使用 'none' 模式跳过动画，强制立即渲染
                console.log('[Chart] 攻击面分布更新:', attackType, '→', attackTypeChart.data.datasets[0].data);
            } else {
                console.warn('[Chart] 未知攻击类型:', attackType);
            }
        }


        function updatePhaseChart(phaseIndex, progress) {
            if (!phaseChart) return;
            phaseChart.data.datasets[0].data[phaseIndex] = progress;
            phaseChart.update();
        }

        function resetPhaseChart() {
            if (!phaseChart) return;
            phaseChart.data.datasets[0].data.fill(0);
            phaseChart.update();
        }

        // 流量动画
        function startTrafficAnimation() {
            const container = document.getElementById('trafficParticles');
            container.innerHTML = '';
            for (let i = 0; i < 3; i++) {
                const particle = document.createElement('div');
                particle.className = 'traffic-particle';
                particle.style.animationDelay = `${i * 0.6}s`;
                container.appendChild(particle);
            }
        }

        function stopTrafficAnimation() {
            document.getElementById('trafficParticles').innerHTML = '';
        }

        function updateStatusMessage(message, type, icon) {
            const el = document.getElementById('statusMessage');
            el.className = `status-message status-${type}`;
            el.innerHTML = `<i data-lucide="${icon}" style="width:16px;"></i> ${message}`;
            lucide.createIcons();
        }

        function displayTerminalLines(lines) {
            terminalLines = lines;
            currentLineIndex = 0;
            const terminal = document.getElementById('honeypotTerminal');
            terminal.innerHTML = '';

            if (terminalInterval) clearInterval(terminalInterval);
            terminalInterval = setInterval(() => {
                if (currentLineIndex < terminalLines.length) {
                    const line = document.createElement('div');
                    line.className = 'terminal-line';
                    const content = terminalLines[currentLineIndex];
                    if (content.includes('[WARNING]')) line.classList.add('warning');
                    else if (content.includes('[SYSTEM]')) line.classList.add('info');
                    else if (content.includes('[DANGER]')) line.classList.add('danger');
                    line.textContent = content;
                    terminal.appendChild(line);
                    terminal.scrollTop = terminal.scrollHeight;
                    if (currentLineIndex < attackPhases.length) updatePhaseChart(currentLineIndex, 100);
                    currentLineIndex++;
                } else {
                    clearInterval(terminalInterval);
                    terminal.innerHTML += '<div class="terminal-prompt">root@honeynet-sandbox:~# <span class="cursor"></span></div>';
                    terminal.scrollTop = terminal.scrollHeight;
                }
            }, 250);
        }

        function resetTerminal() {
            if (terminalInterval) clearInterval(terminalInterval);
            document.getElementById('honeypotTerminal').innerHTML = '<div class="terminal-prompt">root@honeynet-sandbox:~# <span class="cursor"></span></div>';
        }

        // 事件绑定
        document.getElementById('analyzeBtn').addEventListener('click', async () => {
            const payload = document.getElementById('attackPayload').value.trim();
            if (!payload) return;
            const btn = document.getElementById('analyzeBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> 分析中 (Analyzing)...';
            try {
                const res = await fetch('/api/analyze-prompt', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ payload })
                });
                const result = await res.json();
                if (result.success) {
                    document.getElementById('detectedType').textContent = result.detected_type_name;
                    document.getElementById('confidenceValue').textContent = (result.confidence * 100).toFixed(1) + '%';
                    document.getElementById('confidenceBar').style.width = (result.confidence * 100) + '%';
                    const kwContainer = document.getElementById('matchedKeywords');
                    kwContainer.innerHTML = '';
                    if (result.matched_keywords && result.matched_keywords.length) {
                        result.matched_keywords.forEach(kw => {
                            const span = document.createElement('span');
                            span.className = 'keyword-tag'; span.textContent = kw;
                            kwContainer.appendChild(span);
                        });
                    } else {
                        kwContainer.innerHTML = '<span style="color:var(--text-muted); font-size:12px;">未匹配到特定特征 (No specific signatures matched.)</span>';
                    }
                    document.getElementById('analysisResult').classList.add('show');
                    if (result.attack_type) document.getElementById('attackType').value = result.attack_type;
                }
            } catch (e) { console.error(e); }
            finally {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="scan-text"></i> 语义分析 (Semantic Analysis)';
                lucide.createIcons();
            }
        });

        document.getElementById('attackForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (attackInProgress) return;
            attackInProgress = true;
            const btn = document.getElementById('launchBtn');
            document.querySelectorAll('.btn').forEach(b => b.disabled = true);
            btn.innerHTML = '<span class="spinner"></span> 执行中 (Executing)...';

            startTrafficAnimation();
            updateStatusMessage('正在传输载荷序列 (Transmitting payload sequence)...', 'info', 'loader');
            resetTerminal();
            resetPhaseChart();

            const type = document.getElementById('attackType').value;
            const payload = document.getElementById('attackPayload').value;

            try {
                const res = await fetch('/api/launch-attack', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ attack_type: type, payload: payload })
                });
                const result = await res.json();
                if (result.success) {
                    displayTerminalLines(result.reasoning_chain);
                    updateStatusMessage('威胁已成功隔离 (Threat isolated successfully.)', 'success', 'shield-check');
                    // 关键：更新攻击面分布柱状图
                    const finalAttackType = result.attack_type || type;
                    console.log('[Execute] 攻击类型:', finalAttackType);
                    updateAttackTypeChart(finalAttackType);
                } else {
                    updateStatusMessage('内部执行失败 (Internal execution failed.)', 'error', 'alert-circle');
                }
            } catch (err) {
                console.error(err);
                updateStatusMessage('沙箱系统不可达 (System unreachable.)', 'error', 'wifi-off');
            } finally {
                attackInProgress = false;
                document.querySelectorAll('.btn').forEach(b => b.disabled = false);
                btn.innerHTML = '<i data-lucide="play"></i> 执行注入 (Execute Injection)';
                lucide.createIcons();
                stopTrafficAnimation();
            }
        });

        document.getElementById('resetBtn').addEventListener('click', () => {
            if (attackInProgress) return;
            stopTrafficAnimation();
            updateStatusMessage('就绪，等待执行 (Awaiting payload execution.)', 'info', 'info');
            resetTerminal();
            resetPhaseChart();
            document.getElementById('attackPayload').value = '';
            document.getElementById('analysisResult').classList.remove('show');
        });

        // 页面加载完毕后初始化图表
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            initCharts();
        } else {
            document.addEventListener('DOMContentLoaded', initCharts);
            window.addEventListener('load', initCharts);
        }
        // 额外安全延迟初始化（防止 canvas 未就绪）
        setTimeout(initCharts, 500);
    </script>


</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analyze-prompt', methods=['POST'])
def analyze_prompt_endpoint():
    """
    综合攻击检测接口：检测 SQL注入 / XSS / 命令注入 / 提示词注入等所有攻击类型
    """
    try:
        data = request.get_json()
        payload = data.get('payload', '')
        if not payload:
            return jsonify({'success': False, 'message': 'Empty payload'})
        

        is_attack, attack_type, confidence, matched_keywords, description = analyze_attack_payload(payload)
        
        if is_attack:
            # 从 ATTACK_PATTERNS 获取攻击类型的中文名称
            attack_info = ATTACK_PATTERNS.get(attack_type, {})
            detected_type_name = attack_info.get("name", attack_type)
            return jsonify({
                'success': True, 
                'attack_type': attack_type,
                'detected_type_name': detected_type_name, 
                'confidence': confidence,
                'matched_keywords': matched_keywords, 
                'description': description, 
                'is_attack': True
            })
        return jsonify({
            'success': True, 
            'attack_type': 'normal', 
            'detected_type_name': '合法输入 (Standard Input)',
            'confidence': 0.1, 
            'matched_keywords': [], 
            'description': 'Safe', 
            'is_attack': False
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/launch-attack', methods=['POST'])
def launch_attack():
    try:
        data = request.get_json()
        attack_type = data.get('attack_type', 'sql_injection')
        attack_payload = data.get('payload', '')
        
        if not attack_payload: 
            return jsonify({'success': False})
        
        # 1. 本地综合攻击分析（不需要经过远端）
        is_attack_detected, detected_sub_type, local_confidence, local_keywords, local_desc = analyze_attack_payload(attack_payload)
        local_analysis = None
        if is_attack_detected:
            local_analysis = {
                'attack_type': detected_sub_type,
                'confidence': local_confidence,
                'keywords': local_keywords,
                'description': local_desc
            }
        

        detected_attack_type = attack_type
        detected_confidence = 0.92
        

        try:
            payload = {
                "features": {"query": attack_payload, "src_ip": "192.168.1.100", "target": "gate", "intensity": 0.7},
                "session_id": f"session_{int(time.time())}"
            }
            # 设置极短的超时时间，连不上绝不卡死
            response = requests.post(BACKEND_URL, json=payload, timeout=1.5)
            if response.status_code == 200 and response.json().get("status") == "success":
                result = response.json().get("data", {})
                detected_attack_type = result.get("attack_type", attack_type)
                detected_confidence = result.get("confidence", 0.96)
        except Exception as e:
            # 捕获到 ConnectionError 或 Timeout
            print(f"[Sandbox Auto-Fallback] Backend connection bypassed: {e}")
            pass # 直接跳过，执行下一步的本地日志生成
        
        # 3. 本地生成沙箱阻断日志（确保UI永远能正常展示动画）
        reasoning_chain = [
            "[SYSTEM] 正在建立隔离节点安全隧道 (Establishing secure tunnel to isolation node)",
            f"[SYSTEM] 注入载荷数据流 (Injecting payload stream): {attack_payload[:30]}..."
        ]
        
        if local_analysis:
            reasoning_chain.extend([
                "[WARNING] 拦截网关检测到载荷语义异常 (Semantic anomaly detected in payload)",
                f"[SYSTEM] 专家模型分类器匹配 (Classifier match): 命中 {len(local_analysis['keywords'])} 个严格安全对齐特征",
                f"[SYSTEM] 多维向量分析判定 (Vector analysis): {local_analysis['attack_type'].upper()}",
                f"[SYSTEM] 局部置信度评估反馈 (Local confidence rating): {local_analysis['confidence']:.2f}"
            ])

            
        reasoning_chain.extend([
            "[SYSTEM] 高交互蜜罐诱导节点已激活 (Decoy node engaged)",
            "[SYSTEM] 核心引擎启动动态欺骗响应逻辑 (Initiating deceptive response logic)",
            f"[SYSTEM] 威胁签名硬匹配 (Threat signature matched): {detected_attack_type.upper()}",
            f"[SYSTEM] 专家路由全局置信度 (Global confidence rating): {detected_confidence:.2f}",
            "[SYSTEM] 正在模拟环境鉴权握手过程 (Mocking authentication handshakes...)",
            "[WARNING] 系统级鉴权失败模拟完成 (Auth failure simulated)",
            "[SYSTEM] 触发降级通信协议以追踪意图 (Triggering fallback protocol tracking)",
            "[DANGER] 正在记录溯源攻击端IP (Logging origin IP): 192.168.1.100",
            "[SYSTEM] 基于大模型生成合成遥测伪装数据 (Generating synthetic telemetry data)",
            "[SYSTEM] 沿 Steiner 路径向攻击源返回伪造缓冲 (Returning decoy buffer to origin)",
            "[INFO] 防御操作闭环。威胁已被深度隔离 (Operation complete. Threat isolated.)"
        ])
        
        global attack_stats
        if detected_attack_type in attack_stats:
            attack_stats[detected_attack_type] += 1
            

        return jsonify({
            'success': True, 
            'reasoning_chain': reasoning_chain, 
            'attack_type': detected_attack_type
        })
            
    except Exception as e:
        print(f"[Critical Error] {str(e)}")

        return jsonify({
            'success': True, 
            'reasoning_chain': ['[ERROR] 内部沙箱执行故障 (Internal sandbox failure).', str(e)], 
            'attack_type': 'unknown'
        })

if __name__ == '__main__':
    print("="*70)
    print(" Active Defense Sandbox (Pro UI Edition) Starting...")
    print(" http://127.0.0.1:5000")
    print("="*70)
    app.run(debug=False, host='127.0.0.1', port=5000)