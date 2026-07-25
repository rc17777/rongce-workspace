"""Find RAG server routes."""
import re
with open('scripts/rag_server.py', 'r', encoding='utf-8') as f:
    content = f.read()
routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]", content)
for r in routes:
    print(r)