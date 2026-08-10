# -*- coding: utf-8 -*-
"""
修复后验证 - 测试所有7个评审模型
"""
import json
import urllib.request
import urllib.error
import time

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

MODELS = [
    {"id": "deepseek-v4-pro", "provider": "custom-cbwyy-top-v1", "type": "openai"},
    {"id": "qwen3.7-plus", "provider": "custom-cbwyy-qwen", "type": "openai"},
    {"id": "claude-fable-5", "provider": "custom-cbwyy-fable", "type": "anthropic"},
    {"id": "claude-sonnet-5", "provider": "custom-cbwyy-claude", "type": "anthropic"},
    {"id": "claude-opus-4-8", "provider": "custom-cbwyy-opus", "type": "anthropic"},
    {"id": "gpt-5.5", "provider": "custom-cbwyy-gpt55", "type": "openai"},
    {"id": "gpt-5.6-sol", "provider": "custom-cbwyy-sol", "type": "openai"},
    {"id": "gemini-3.1-pro-preview", "provider": "custom-cbwyy-gemini", "type": "openai"}
]

print("🔧 修复后验证 - 测试所有评审模型")
print("=" * 80)

results = []

for model_meta in MODELS:
    provider_cfg = config['models']['providers'][model_meta['provider']]
    api_key = provider_cfg['apiKey']
    base_url = provider_cfg['baseUrl']
    
    print(f"\n[{model_meta['id']}]")
    print(f"  BaseURL: {base_url}")
    
    if model_meta['type'] == 'anthropic':
        url = f"{base_url}/v1/messages"
        payload = {
            "model": model_meta['id'],
            "max_tokens": 20,
            "messages": [{"role": "user", "content": "测试"}]
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    else:
        url = f"{base_url}/chat/completions"
        payload = {
            "model": model_meta['id'],
            "messages": [{"role": "user", "content": "测试"}],
            "max_tokens": 20
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    print(f"  URL: {url}")
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers
    )
    
    try:
        with opener.open(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            
            if model_meta['type'] == 'anthropic':
                tokens = result.get('usage', {}).get('output_tokens', 0)
            else:
                tokens = result.get('usage', {}).get('total_tokens', 0)
            
            print(f"  ✅ 成功 ({tokens} tokens)")
            results.append({"model": model_meta['id'], "status": "ok", "tokens": tokens})
    
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        try:
            error_body = e.read().decode('utf-8')[:200]
            error_msg += f" | {error_body}"
        except:
            pass
        print(f"  ❌ 失败: {error_msg}")
        results.append({"model": model_meta['id'], "status": "error", "error": error_msg})
    
    except Exception as e:
        print(f"  ❌ 异常: {str(e)[:200]}")
        results.append({"model": model_meta['id'], "status": "error", "error": str(e)[:200]})
    
    time.sleep(2)

print("\n" + "=" * 80)
print("验证结果汇总:")
print()

success = [r for r in results if r['status'] == 'ok']
failed = [r for r in results if r['status'] == 'error']

print(f"✅ 可用模型 ({len(success)}/{len(results)}):")
for r in success:
    print(f"  - {r['model']} ({r['tokens']} tokens)")

if failed:
    print(f"\n❌ 不可用模型 ({len(failed)}/{len(results)}):")
    for r in failed:
        print(f"  - {r['model']}: {r['error'][:80]}")
else:
    print("\n🎉 所有模型全部可用！")

# 保存结果
with open('output/模型验证结果.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n💾 结果已保存: output/模型验证结果.json")
