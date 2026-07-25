"""Test RAG query with correct endpoint."""
import requests, json

# Test via /api/ask
r = requests.post('http://127.0.0.1:5001/api/ask',
                  json={'query': '常态化帮扶资金审计要点 联农带农不能简单入股分红'},
                  timeout=15)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])
else:
    print(r.text[:1000])