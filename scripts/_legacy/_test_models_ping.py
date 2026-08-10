# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.error
import time

# 从 openclaw.json 读取配置
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 测试所有模型
TEST_MODELS = {
    "deepseek-v4-flash": {"provider": "custom-cbwyy-top-v1", "type": "openai"},
    "deepseek-v4-pro": {"provider": "custom-cbwyy-top-v1", "type": "openai"},
    "qwen3.7-plus": {"provider": "custom-cbwyy-qwen", "type": "openai"},
    "claude-fable-5": {"provider": "custom-cbwyy-fable", "type": "anthropic"},
    "claude-sonnet-5": {"provider": "custom-cbwyy-claude", "type": "anthropic"},
    "claude-opus-4-8": {"provider": "custom-cbwyy-opus", "type": "anthropic"},
    "gpt-5.5": {"provider": "custom-cbwyy-gpt55", "type": "openai"},
    "gpt-5.6-luna": {"provider": "custom-cbwyy-luna", "type": "openai"},
    "gpt-5.6-sol": {"provider": "custom-cbwyy-sol", "type": "openai"},
    "gpt-5.6-terra": {"provider": "custom-cbwyy-terra", "type": "openai"},
    "gemini-3.1-pro-preview": {"provider": "custom-cbwyy-gemini", "type": "openai"},
    "doubao-seed-2.0-lite": {"provider": "custom-cbwyy-doubao", "type": "openai"}
}

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def ping_model(model_id, meta):
    """用最简单的prompt测试模型可用性"""
    provider_id = meta['provider']
    provider_cfg = config['models']['providers'][provider_id]
    api_key = provider_cfg['apiKey']
    base_url = provider_cfg['baseUrl']
    
    test_prompt = "请回复'OK'"
    
    try:
        if meta['type'] == 'anthropic':
            url = f"{base_url}/v1/messages"
            payload = {
                "model": model_id,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": test_prompt}]
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
        else:
            url = f"{base_url}/v1/chat/completions"
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": test_prompt}],
                "max_tokens": 10
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers
        )
        
        with opener.open(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return {"status": "ok", "response": str(result)[:100]}
    
    except urllib.error.HTTPError as e:
        return {"status": "error", "code": e.code, "msg": e.reason}
    except Exception as e:
        return {"status": "error", "msg": str(e)[:100]}

# 主流程
print("🏥 模型可用性快速测试...")
print("=" * 80)

available = []
unavailable = []

for model_id, meta in TEST_MODELS.items():
    print(f"[{model_id}]...", end=" ", flush=True)
    result = ping_model(model_id, meta)
    
    if result['status'] == 'ok':
        print(f"✅ 可用")
        available.append(model_id)
    else:
        error_info = result.get('msg', '') or f"{result.get('code', '')} {result.get('msg', '')}"
        print(f"❌ {error_info}")
        unavailable.append((model_id, error_info))
    
    time.sleep(2)

print("=" * 80)
print(f"\n✅ 可用模型 ({len(available)}):")
for m in available:
    print(f"  - {m}")

print(f"\n❌ 不可用模型 ({len(unavailable)}):")
for m, err in unavailable:
    print(f"  - {m}: {err}")

# 保存结果
with open('output/models_availability.json', 'w', encoding='utf-8') as f:
    json.dump({
        "available": available,
        "unavailable": [{"model": m, "error": e} for m, e in unavailable],
        "timestamp": "2026-07-15 23:32"
    }, f, ensure_ascii=False, indent=2)

print("\n💾 结果已保存至: output/models_availability.json")
