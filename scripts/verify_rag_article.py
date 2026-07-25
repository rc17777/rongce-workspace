"""Verify new procurement audit article in RAG."""
import requests, json

r = requests.post('http://127.0.0.1:5001/api/ask',
                  json={'query': 'AI采购审计 四码筛查 MAC地址 IP地址 知识图谱'},
                  timeout=15)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    # Check if new article is in sources
    for s in data.get('sources', []):
        if 'AI审计' in s.get('file', ''):
            print(f'✅ FOUND: {s["file"]} (score={s["score"]})')
            print(f'   Preview: {s["preview"][:100]}')
    if not any('AI审计' in s.get('file', '') for s in data.get('sources', [])):
        print('Checking all sources:')
        for s in data.get('sources', [])[:5]:
            print(f'  {s["file"]} (score={s["score"]})')
else:
    print(r.text[:500])