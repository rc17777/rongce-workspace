# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.error

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# 测试 deepseek-v4-flash
url = "https://cbwyy.top/v1/chat/completions"
api_key = "sk-Bq4EalSwLmehZ3xXa55b7TzRX4HIlbTppgdKQ0ElOab09AZa"

payload = {
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "测试"}],
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

try:
    with opener.open(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print("✅ 成功:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.reason}")
    try:
        error_body = e.read().decode('utf-8')
        print("错误详情:")
        print(error_body)
    except:
        pass
except Exception as e:
    print(f"❌ 异常: {e}")
