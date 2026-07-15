#!/usr/bin/env python3
import subprocess, json, sys
sys.stdout.reconfigure(encoding='utf-8')

result = subprocess.run(
    ['curl.exe', '-s', 'https://api.github.com/search/repositories?q=ppt+slides+presentation+generator&sort=stars&order=desc&per_page=15'],
    capture_output=True, timeout=30
)
data = json.loads(result.stdout.decode('utf-8', errors='replace'))
print(f'总结果: {data.get("total_count", 0)}')
print()
for r in data.get('items', []):
    print(f"⭐ {r['stargazers_count']:>6} | {r['full_name']:<45}")
    desc = (r['description'] or '-')[:80]
    print(f"    {desc}")
    print(f"    {r['html_url']}")
    print()