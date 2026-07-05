#!/usr/bin/env python3
"""
<<<<<<< HEAD
DeepSeek 模型健康检查 (v2)
==========================
现在DeepSeek直连key已失效，改为检测 cbwxy.top 代理上的模型。
也检测 DashScope (qwen-vl-max) 等其他provider的健康状态。

用法:
  python scripts/deepseek_model_check.py
  退出码: 0=正常, 1=配置未找到, 2=API异常(需告警)
"""
import json, sys, os, io
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WORKSPACE = Path(__file__).parent.parent
TZ = timezone(timedelta(hours=8))

# 要检查的 provider 清单（key已知有效）
CHECK_PROVIDERS = {
    "custom-cbwyy-top-v1": {
        "url": "https://cbwxy.top/v1/models",
        "expected_models": ["deepseek-v4-flash", "deepseek-v4-pro"],
    },
    "dashscope": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
        "expected_models": ["qwen-vl-max"],
    },
}

def load_models_config():
    """从工作区 models.json 读取所有 provider 及其 apiKey"""
    paths = [
        WORKSPACE / "models.json",
    ]
    for p in paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("providers", {})
    return None

def check_provider(provider_id: str, config: dict, expected: list) -> dict:
    """检查单个 provider 的 API 连通性和模型列表"""
    prov = config.get(provider_id, {})
    if not prov:
        return {"status": "NOT_FOUND", "models_found": [], "expected": expected, "error": "provider 配置不存在"}

    api_key = prov.get("apiKey", "")
    if not api_key:
        return {"status": "NO_KEY", "models_found": [], "expected": expected, "error": "未配置 apiKey"}

    base_url = prov.get("baseUrl", "").rstrip("/")
    url = CHECK_PROVIDERS.get(provider_id, {}).get("url", f"{base_url}/models")

    try:
        import urllib.request, ssl
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        models_from_api = [m["id"] for m in data.get("data", [])]
        found = [m for m in expected if m in models_from_api]
        missing = [m for m in expected if m not in models_from_api]

        return {
            "status": "OK" if not missing else "PARTIAL",
            "models_found": models_from_api,
            "expected": expected,
            "found": found,
            "missing": missing,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "models_found": [],
            "expected": expected,
            "error": str(e),
        }

def main():
    providers = load_models_config()
    if not providers:
        print("❌ 未找到工作区 models.json")
        sys.exit(1)

    print(f"🧪 {datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')} 模型健康检查\n")
    print(f"{'Provider':<25} {'Status':<10} {'发现':<30} {'缺失':<15}")
    print("-" * 80)

    has_issue = False
    for pid, check_cfg in CHECK_PROVIDERS.items():
        result = check_provider(pid, providers, check_cfg["expected_models"])
        status_icon = "✅" if result["status"] == "OK" else "⚠️" if result["status"] == "PARTIAL" else "❌"
        found_str = ",".join(result.get("found", result.get("models_found", [])))[:28]
        missing_str = ",".join(result.get("missing", []))[:13]
        print(f"{status_icon} {pid:<23} {result['status']:<10} {found_str:<30} {missing_str:<15}")
        if result["status"] in ("ERROR", "NOT_FOUND", "NO_KEY", "PARTIAL"):
            has_issue = True
            print(f"   ├ 错误: {result.get('error', '部分模型缺失')}")

    print("-" * 80)
    providers_ok = sum(1 for pid in CHECK_PROVIDERS
                       if check_provider(pid, providers, CHECK_PROVIDERS[pid]["expected_models"]).get("status") == "OK")
    print(f"\n总计: {len(CHECK_PROVIDERS)} 个 provider, {providers_ok} 个正常")

    if has_issue:
        print("⚠️ 存在异常，请关注！")
        sys.exit(2)
    else:
        print("✅ 全部正常")
        sys.exit(0)
=======
DeepSeek 模型健康检查
每周对比 DeepSeek API 可用模型列表 vs openclaw.json 配置，发现变化时告警。
"""
import json
import re
import sys
import io
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Windows GBK 编码兼容
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
TZ = timezone(timedelta(hours=8))

# ── 从 config 中提取 deepseek 模型 ID ──────────────────────────
def get_configured_models():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    prov = config.get("models", {}).get("providers", {}).get("deepseek", {})
    models = prov.get("models", [])
    return [m["id"] for m in models], config

# ── 从 API 获取可用模型列表 ─────────────────────────────────────
def get_api_models(api_key: str):
    import urllib.request, ssl
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return [m["id"] for m in data.get("data", [])]

# ── 对比并生成报告 ──────────────────────────────────────────────
def check(config_models: list, api_models: list):
    added = set(api_models) - set(config_models)      # 新增模型
    removed = set(config_models) - set(api_models)    # 已下线模型
    prim_id = None
    fall_ids = []

    # 从 config 提取 primary/fallback
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    am = config.get("agents", {}).get("defaults", {}).get("model", {})
    prim_raw = am.get("primary", "")
    # 提取 provider/model-id → 只取 model-id
    match = re.search(r"deepseek/(\S+)", prim_raw)
    if match:
        prim_id = match.group(1)
    for fb in am.get("fallbacks", []):
        m = re.search(r"deepseek/(\S+)", fb)
        if m:
            fall_ids.append(m.group(1))

    issues = []
    if prim_id and prim_id not in api_models:
        issues.append(f"🔴 主力模型 '{prim_id}' 在 API 中不存在！")
    for fid in fall_ids:
        if fid not in api_models:
            issues.append(f"🟡 备用模型 '{fid}' 在 API 中不存在！")

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    lines = [f"## DeepSeek 模型健康检查 — {now}", ""]

    if issues or added or removed:
        lines.append("⚠️ 发现问题，需要关注：")
        lines.append("")
        for i in issues:
            lines.append(f"- {i}")
        if added:
            lines.append(f"- 🟢 API 新增模型（未配置）: {', '.join(added)}")
        if removed:
            lines.append(f"- 🔴 API 已下线模型（仍在配置中）: {', '.join(removed)}")
        return True, "\n".join(lines)

    lines.append("✅ 所有 DeepSeek 模型正常，配置与 API 一致。")
    lines.append("")
    lines.append(f"配置模型: {', '.join(config_models)}")
    lines.append(f"API 模型:  {', '.join(api_models)}")
    lines.append(f"主力: {prim_id} | 备胎: {', '.join(fall_ids)}")
    return False, "\n".join(lines)

# ── main ────────────────────────────────────────────────────────
def main():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 无法读取配置文件: {e}")
        sys.exit(1)

    api_key = (
        config.get("models", {})
        .get("providers", {})
        .get("deepseek", {})
        .get("apiKey", "")
    )
    if not api_key:
        print("❌ 配置中未找到 DeepSeek API Key")
        sys.exit(1)

    config_models, _ = get_configured_models()
    api_models = get_api_models(api_key)
    has_issues, report = check(config_models, api_models)

    # 输出报告
    print(report)

    # 退出码：有问题=2 正常=0
    sys.exit(2 if has_issues else 0)
>>>>>>> c3097c346e456e55f12e02c4d4e7b612d0fc2140

if __name__ == "__main__":
    main()
