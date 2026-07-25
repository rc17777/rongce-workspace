"""Test GLM-5.2 API connection."""
import requests, json

r = requests.post(
    'https://cbwyy.top/v1/chat/completions',
    headers={
        'Authorization': 'Bearer sk-KthgLLlTBL0g0aYT7gEa33l6wdN88JYY91Wcmpc7P4D54UoD',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'glm-5.2',
        'messages': [{'role': 'user', 'content': '回复"OK"即可'}],
        'max_tokens': 10
    },
    timeout=15
)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
else:
    print(r.text[:500])