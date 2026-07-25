"""Test RAG query for the new article."""
import requests

r = requests.post('http://127.0.0.1:5001/api/query', 
                  json={'query': '常态化帮扶资金审计要点 联农带农', 'top_k': 3}, 
                  timeout=10)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    for i, doc in enumerate(data.get('results', [])):
        title = doc.get('title', '')
        score = doc.get('score', 0)
        content = doc.get('content', '')[:120]
        print(f'[{i+1}] {title} | score={score:.3f}')
        print(f'    {content}')
        print()
else:
    print(r.text[:500])