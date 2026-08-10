# -*- coding: utf-8 -*-
"""
模型可用性诊断工具 - 找出404根本原因
"""
import json
import urllib.request
import urllib.error

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# 读取配置
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 测试矩阵：成功的 vs 失败的
TEST_CASES = [
    # 已验证成功的
    {"name": "claude-sonnet-5 (✅成功)", "provider": "custom-cbwyy-claude", "model": "claude-sonnet-5", "type": "anthropic"},
    # 失败的
    {"name": "deepseek-v4-pro (❌失败)", "provider": "custom-cbwyy-top-v1", "model": "deepseek-v4-pro", "type": "openai"},
    {"name": "qwen3.7-plus (❌失败)", "provider": "custom-cbwyy-qwen", "model": "qwen3.7-plus", "type": "openai"},
    {"name": "gpt-5.5 (❌失败)", "provider": "custom-cbwyy-gpt55", "model": "gpt-5.5", "type": "openai"},
    {"name": "gemini (❌失败)", "provider": "custom-cbwyy-gemini", "model": "gemini-3.1-pro-preview", "type": "openai"}
]

print("🔍 模型可用性深度诊断")
print("=" * 80)

for case in TEST_CASES:
    provider_cfg = config['models']['providers'][case['provider']]
    api_key = provider_cfg['apiKey']
    base_url = provider_cfg['baseUrl']
    
    print(f"\n【{case['name']}】")
    print(f"  Provider: {case['provider']}")
    print(f"  BaseURL: {base_url}")
    print(f"  API Key: {api_key[:10]}...{api_key[-6:]}")
    print(f"  Type: {case['type']}")
    
    # 构造请求
    if case['type'] == 'anthropic':
        url = f"{base_url}/v1/messages"
        payload = {
            "model": case['model'],
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "test"}]
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    else:
        url = f"{base_url}/chat/completions"
        payload = {
            "model": case['model'],
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    print(f"  完整URL: {url}")
    print(f"  Model参数: {case['model']}")
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers
    )
    
    try:
        with opener.open(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"  ✅ 成功")
            print(f"     响应前100字符: {str(result)[:100]}")
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code}: {e.reason}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"     完整错误: {error_body}")
        except:
            pass
    except Exception as e:
        print(f"  ❌ 异常: {e}")

print("\n" + "=" * 80)
print("诊断完成")
