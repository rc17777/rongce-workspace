#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型健康检查 (v3)
检查所有 cbwxy.top 代理上模型的 API 连通性。

特性：
- 自动解析 env:// 引用的 API Key
- 覆盖全部 11 个 provider
- 退出码: 0=全部正常, 1=配置未找到, 2=有异常需告警

用法:
  python scripts/deepseek_model_check.py
"""
import json, sys, os, io, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WORKSPACE = Path(__file__).parent.parent
TZ = timezone(timedelta(hours=8))

# 完整 provider 清单（名称 → 期望模型 + 接口风格）
CHECK_PROVIDERS = {
    "custom-cbwyy-top-v1": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["deepseek-v4-flash", "deepseek-v4-pro"],
        "role": "🔧 免费执行 / 🧠 中代价分析",
    },
    "custom-cbwyy-gpt55": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["gpt-5.5"],
        "role": "🎯 高代价表达审查",
    },
    "custom-cbwyy-claude": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["claude-sonnet-5"],
        "role": "🎯 高代价逻辑审查",
    },
    "custom-cbwyy-opus": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["claude-opus-4-8"],
        "role": "🔬 致命代价终审",
    },
    "custom-cbwyy-fable": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["claude-fable-5"],
        "role": "🟡 咨询层独立顾问",
    },
    "custom-cbwyy-doubao": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["doubao-seed-2.0-lite"],
        "role": "📎 合规备选",
    },
    "custom-cbwyy-image": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["gpt-image-2"],
        "role": "🎨 生图专用",
    },
    "custom-cbwyy-qwen": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["qwen3.7-plus"],
        "role": "🔧 低代价中文·图片",
    },
    "custom-cbwyy-luna": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["gpt-5.6-luna"],
        "role": "🎯 高代价审查",
    },
    "custom-cbwyy-sol": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["gpt-5.6-sol"],
        "role": "🎯 高代价审查",
    },
    "custom-cbwyy-terra": {
        "url": "https://cbwyy.top/v1/models",
        "expected_models": ["gpt-5.6-terra"],
        "role": "🎯 高代价审查",
    },
}


def resolve_api_key(raw_key: str) -> str:
    """解析 env://VAR_NAME 引用，返回实际 API Key"""
    if not raw_key:
        return ""
    m = re.match(r'^env://(.+)$', raw_key.strip())
    if m:
        return os.environ.get(m.group(1), "")
    return raw_key


def load_providers_config():
    """从 openclaw.json 读取 providers 配置"""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("models", {}).get("providers", {})
    return None


def check_provider(provider_id: str, providers: dict, expected: list) -> dict:
    """检查单个 provider"""
    prov = providers.get(provider_id, {})
    if not prov:
        return {"status": "NOT_FOUND", "models_found": [], "expected": expected,
                "error": "provider not found in config"}

    raw_key = prov.get("apiKey", "")
    api_key = resolve_api_key(raw_key)
    
    if not api_key:
        hint = f"env var not set" if raw_key.startswith("env://") else "missing apiKey"
        return {"status": "NO_KEY", "models_found": [], "expected": expected, "error": hint}

    url = CHECK_PROVIDERS.get(provider_id, {}).get("url",
                                                    f"{prov.get('baseUrl', '').rstrip('/')}/models")

    try:
        import urllib.request, ssl
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
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
        error_msg = str(e)
        return {"status": "ERROR", "models_found": [], "expected": expected, "error": error_msg}


def main():
    providers = load_providers_config()
    if not providers:
        print("ERROR: Providers config not found in openclaw.json")
        sys.exit(1)

    print(f"模型健康检查  {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}")
    print(f"Provider 总数: {len(CHECK_PROVIDERS)} | 配置文件: {Path.home() / '.openclaw' / 'openclaw.json'}")
    print()

    # 表头
    print(f"{'Provider':<28} {'状态':<8} {'期望模型':<22} {'角色'}")
    print("-" * 95)

    ok_count = 0
    issues = []

    for pid, check_cfg in CHECK_PROVIDERS.items():
        result = check_provider(pid, providers, check_cfg["expected_models"])
        role = check_cfg.get("role", "")

        if result["status"] == "OK":
            icon = "✅"
            ok_count += 1
        elif result["status"] == "PARTIAL":
            icon = "⚠️"
            issues.append((pid, result))
        else:
            icon = "❌"
            issues.append((pid, result))

        expected_str = ", ".join(result["expected"])[:21]
        print(f"{icon} {pid:<26} {result['status']:<8} {expected_str:<22} {role}")

        if result["status"] != "OK":
            print(f"   ↳ {result.get('error', 'unknown')}")

    print("-" * 95)
    print(f"结果: {ok_count}/{len(CHECK_PROVIDERS)} 正常")

    if issues:
        print()
        print("异常明细:")
        for pid, result in issues:
            print(f"  [{result['status']}] {pid}")
            if result.get("error"):
                print(f"      错误: {result['error']}")
            if result.get("missing"):
                print(f"      缺失模型: {', '.join(result['missing'])}")
        print()
        print("建议行动:")
        for pid, result in issues:
            prov = providers.get(pid, {})
            raw_key = prov.get("apiKey", "")
            if result["status"] == "ERROR" and "401" in result.get("error", ""):
                env_var = ""
                m = re.match(r'^env://(.+)$', raw_key.strip())
                if m:
                    env_var = m.group(1)
                print(f"  🔑 {pid}: API Key 失效(401) — 需更新环境变量 {env_var}")
            elif result["status"] == "NO_KEY":
                print(f"  🔑 {pid}: API Key 未设置 — 检查环境变量或配置文件")
            elif result["status"] == "PARTIAL":
                print(f"  🔍 {pid}: 模型列表不完整 — 联系 cbwxy.top 管理员")
            else:
                print(f"  ⚡ {pid}: {result.get('error', '未知错误')}")

        print()
        print("WARNING: issues detected!")
        sys.exit(2)
    else:
        print("✅ 全部正常")
        sys.exit(0)


if __name__ == "__main__":
    main()
