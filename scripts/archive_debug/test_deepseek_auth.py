import requests
import json

# DeepSeek API Key
api_key = "sk-4253399e4b624bee87b2b248d80731f7"
base_url = "https://api.deepseek.com"

# 测试 API Key 有效性
print("=== 测试 DeepSeek API Key 有效性 ===")

# 构造 OpenAI 格式的请求
payload = {
    "model": "deepseek-v4-pro",
    "messages": [
        {
            "role": "user",
            "content": "测试"
        }
    ],
    "max_tokens": 10
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

try:
    print(f"请求URL: {base_url}/v1/chat/completions")
    print(f"请求头: {headers}")
    print(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
    
    response = requests.post(
        f"{base_url}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("✅ API Key 有效！")
        print(f"响应内容: {response.text[:200]}...")
    else:
        print(f"❌ API Key 无效！")
        print(f"错误响应: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
except Exception as e:
    print(f"其他错误: {e}")