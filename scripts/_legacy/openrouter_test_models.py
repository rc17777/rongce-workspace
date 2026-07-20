#!/usr/bin/env python3
"""
OpenRouter 免费模型连通性测试
遍历所有免费模型，逐一发送 "Hello, reply with just 'OK'." 测试可用性
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests

TZ = timezone(timedelta(hours=8))
SNAPSHOT_PATH = Path(__file__).parent.parent / "config" / "openrouter_free_models.json"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# 要测试的提示词
TEST_PROMPT = "Hello, reply with just 'OK'."

def load_api_key() -> str:
    """从环境变量或配置文件读取 API Key"""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    
    # 尝试从 OpenClaw 配置环境变量读取
    config_path = Path(os.environ.get("OPENCLAW_CONFIG_PATH", 
                     Path.home() / ".openclaw" / "openclaw.json"))
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            key = cfg.get("env", {}).get("vars", {}).get("OPENROUTER_API_KEY", "")
            if key and key != "__OPENCLAW_REDACTED__":
                return key
        except Exception:
            pass
    
    # 尝试从 .env 文件读取
    env_files = [
        Path(__file__).parent.parent / ".env",
        Path.cwd() / ".env",
    ]
    for envf in env_files:
        if envf.exists():
            for line in envf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    
    return ""

def load_free_models() -> list[dict]:
    """加载免费模型快照"""
    if SNAPSHOT_PATH.exists():
        snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        return list(snap.get("models", {}).values())
    print("❌ 快照文件不存在，请先运行 openrouter_monitor.py")
    sys.exit(1)

def test_model(model: dict, api_key: str, timeout: int = 30) -> dict:
    """测试单个模型"""
    model_id = model["id"]
    
    # 跳过特殊路由
    if model_id == "openrouter/free":
        return {"id": model_id, "status": "skipped", "reason": "路由模型，非实际模型"}

    # 跳过音频生成模型（没法在 chat 里测试）
    modality = model.get("modality", "")
    if "audio" in modality and "audio" in modality.split("->")[1] if "->" in modality else False:
        return {"id": model_id, "status": "skipped", "reason": "音频输出模型，chat接口不适用"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openclaw.ai",
        "X-Title": "OpenClaw Free Model Tester",
    }
    
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "max_tokens": 10,
        "temperature": 0,
    }
    
    start = time.time()
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
        elapsed = round((time.time() - start) * 1000)
        
        if resp.status_code == 200:
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            reply = msg.get("content") or ""
            if isinstance(reply, str):
                reply = reply.strip()
            else:
                reply = str(reply)
            # 检查是否是拒绝响应（内容为空或拒绝消息）
            refusal = msg.get("refusal", "")
            usage = data.get("usage", {})
            finish = choice.get("finish_reason", "")
            if refusal:
                return {"id": model_id, "status": "refused", "error": f"模型拒绝: {refusal[:100]}", "latency_ms": elapsed}
            if not reply and finish != "stop":
                return {"id": model_id, "status": "empty", "error": f"空响应 (finish={finish})", "latency_ms": elapsed}
            return {
                "id": model_id,
                "name": model.get("name", model_id),
                "status": "ok",
                "latency_ms": elapsed,
                "reply": reply[:100],
                "tokens": usage.get("total_tokens", 0),
                "model_used": data.get("model", model_id),
            }
        elif resp.status_code == 402:
            return {"id": model_id, "status": "error", "error": "402 需要付款/额度不足", "latency_ms": elapsed}
        elif resp.status_code == 429:
            return {"id": model_id, "status": "rate_limited", "error": "429 限流", "latency_ms": elapsed}
        else:
            errmsg = ""
            try:
                errmsg = resp.json().get("error", {}).get("message", resp.text[:200])
            except Exception:
                errmsg = resp.text[:200]
            return {"id": model_id, "status": "error", "error": f"{resp.status_code} {errmsg}", "latency_ms": elapsed}
    except requests.Timeout:
        return {"id": model_id, "status": "timeout", "error": f"超时({timeout}s)", "latency_ms": timeout * 1000}
    except Exception as e:
        return {"id": model_id, "status": "error", "error": str(e)[:200], "latency_ms": round((time.time() - start) * 1000)}

def main():
    api_key = load_api_key()
    if not api_key:
        print("❌ 未找到 OpenRouter API Key！")
        print()
        print("获取方式：")
        print("  1. 访问 https://openrouter.ai 注册账号")
        print("  2. Settings → Keys → Create Key")
        print("  3. 设置环境变量: set OPENROUTER_API_KEY=sk-or-v1-xxxxx")
        print("     或在 openclaw.json 的 env.vars 中添加: \"OPENROUTER_API_KEY\": \"sk-or-v1-xxxxx\"")
        print("     或在工作区根目录创建 .env 文件: OPENROUTER_API_KEY=sk-or-v1-xxxxx")
        sys.exit(1)
    
    models = load_free_models()
    print(f"🔑 API Key: {api_key[:15]}...{api_key[-4:]}")
    print(f"📋 共 {len(models)} 个免费模型待测试")
    print(f"{'='*80}")
    print()
    
    results = []
    ok_count = 0
    error_count = 0
    skip_count = 0
    
    # 逐个串行测试（避免限流）
    for i, model in enumerate(models, 1):
        mid = model["id"]
        print(f"[{i:2d}/{len(models)}] 测试 {mid:<55} ", end="", flush=True)
        
        time.sleep(0.3)  # 轻微间隔避免触发限流
        result = test_model(model, api_key)
        results.append(result)
        
        status = result["status"]
        if status == "ok":
            ok_count += 1
            print(f"✅ {result['latency_ms']}ms | {result.get('reply', '')[:60]}")
        elif status == "skipped":
            skip_count += 1
            print(f"⏭️ {result['reason']}")
        elif status == "rate_limited":
            error_count += 1
            print(f"⏳ 限流，等5秒...")
            time.sleep(5)
        else:
            error_count += 1
            print(f"❌ {result.get('error', 'unknown')[:80]}")
    
    # 汇总报告
    print()
    print(f"{'='*80}")
    print(f"📊 测试结果汇总")
    print(f"{'='*80}")
    print(f"  总计: {len(models)} | ✅ 可用: {ok_count} | ❌ 失败: {error_count} | ⏭️ 跳过: {skip_count}")
    print()
    
    # 分类展示
    print("--- ✅ 可用模型 ---")
    for r in results:
        if r["status"] == "ok":
            print(f"  {r['id']:<55} {r['latency_ms']:>5}ms  reply={r.get('reply', '')[:50]}")
    
    print()
    print("--- ❌ 不可用模型 ---")
    for r in results:
        if r["status"] in ("error", "timeout", "rate_limited"):
            print(f"  {r['id']:<55} [{r['status']}] {r.get('error', '')[:80]}")
    
    print()
    print("--- ⏭️ 跳过模型 ---")
    for r in results:
        if r["status"] == "skipped":
            print(f"  {r['id']:<55} {r['reason']}")
    
    # 保存详细报告
    report_path = Path(__file__).parent.parent / "output" / "openrouter_model_test.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": datetime.now(TZ).isoformat(),
        "summary": {"total": len(models), "ok": ok_count, "error": error_count, "skipped": skip_count},
        "results": results,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📁 详细报告已保存: {report_path}")

if __name__ == "__main__":
    main()
