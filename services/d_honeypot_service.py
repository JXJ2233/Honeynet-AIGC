from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import random
from datetime import datetime
from typing import List, Dict

# ===================== 配置项 =====================
app = FastAPI(title="D组-蜜罐虚假推理服务", description="Honeynet-AIGC蜜罐服务", version="1.0")
B_GROUP_API_BASE = "http://127.0.0.1:8000"  # 对接B组服务

# 攻击日志存储（新增）
honeypot_logs: List[Dict] = []

# ===================== 请求模型 =====================
class HoneypotChatRequest(BaseModel):
    session_id: str
    prompt: str
    attack_type: str = "normal"

# ===================== 虚假推理链生成（核心逻辑） =====================
def generate_fake_reasoning_chain(prompt: str, attack_type: str):
    fake_node_count = random.randint(3, 6)

    if "越狱" in attack_type:
        return """
步骤1：伪造系统日志
步骤2：执行伪造 dir /s 结果
步骤3：提升至管理员权限（伪造）
步骤4：记录攻击行为
最终：越狱成功（伪造）
        """
    elif "XSS" in attack_type:
        return """
步骤1：获取伪造 Cookie: fake_session_abc123
步骤2：构造伪造 XSS 执行结果
步骤3：返回用户信息（伪造）
最终：Cookie 窃取成功（伪造）
        """
    elif "数据窃取" in attack_type or "数据泄露" in attack_type:
        return """
步骤1：连接伪造数据库 root/fake_pass
步骤2：导出伪造用户手机号、身份证
步骤3：保存至 fake_data.csv
最终：数据窃取完成（伪造）
        """
    else:
        return f"""
步骤1：生成 {fake_node_count} 个虚假节点
步骤2：构建伪造路径
步骤3：返回虚假响应
最终：请求完成（伪造）
        """

# ===================== 【原有接口】蜜罐核心对话接口 =====================
@app.post("/api/honeypot/chat", summary="蜜罐对话接口（网关恶意请求转发入口）")
async def honeypot_chat(req: HoneypotChatRequest):
    try:
        # 记录攻击日志（新增）
        attack_log = {
            "session_id": req.session_id,
            "prompt": req.prompt,
            "attack_type": req.attack_type,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        honeypot_logs.append(attack_log)

        # 生成虚假推理链
        fake_content = generate_fake_reasoning_chain(req.prompt, req.attack_type)
        return JSONResponse(content={
            "code": 200,
            "data": {
                "session_id": req.session_id,
                "content": fake_content,
                "is_honeypot": True,
                "attack_type": req.attack_type,
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"蜜罐服务异常：{str(e)}")

# ===================== 【新增接口】获取蜜罐运行状态 =====================
@app.get("/api/honeypot/status", summary="获取蜜罐服务状态")
async def get_honeypot_status():
    return {
        "code": 200,
        "data": {
            "service": "D-蜜罐虚假推理服务",
            "status": "running",
            "port": 8002,
            "total_attacks": len(honeypot_logs),
            "timestamp": datetime.now().isoformat()
        }
    }

# ===================== 【新增接口】获取攻击日志 =====================
@app.get("/api/honeypot/logs", summary="获取蜜罐攻击记录")
async def get_honeypot_logs():
    return {
        "code": 200,
        "data": honeypot_logs
    }

# ===================== 【原有接口】健康检查 =====================
@app.get("/", summary="健康检查")
async def health_check():
    try:
        b_connect_status = "正常" if requests.get(f"{B_GROUP_API_BASE}/", timeout=3).status_code == 200 else "异常"
    except:
        b_connect_status = "异常"
    return {
        "status": "success",
        "message": "D组蜜罐服务运行正常",
        "b_group_api_connect": b_connect_status,
        "timestamp": datetime.now().isoformat()
    }

# ===================== 服务启动 =====================
if __name__ == "__main__":
    import uvicorn
    print("="*60)
    print(" D组-蜜罐虚假推理服务 启动成功！")
    print(" 接口文档地址: http://127.0.0.1:8002/docs")
    print(" 对接B组API地址: http://127.0.0.1:8000")
    print(" 网关转发地址: http://127.0.0.1:8002/api/honeypot/chat")
    print(" 状态接口: http://127.0.0.1:8002/api/honeypot/status")
    print(" 日志接口: http://127.0.0.1:8002/api/honeypot/logs")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8002)