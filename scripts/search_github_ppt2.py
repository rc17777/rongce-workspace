#!/usr/bin/env python3
import subprocess, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Search for AI presentation generators
queries = [
    'AI+presentation+generator+stars:>500',
    'slides+generator+AI',
    'ppt-generator+AI+agent+skill',
    'presentation+generator+GPT+slides',
]

for q in queries:
    print(f'=== {q} ===')
    result = subprocess.run(
        ['curl.exe', '-s', f'https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=5'],
        capture_output=True, timeout=30
    )
    data = json.loads(result.stdout.decode('utf-8', errors='replace'))
    for r in data.get('items', []):
        print(f"  ⭐ {r['stargazers_count']:>6} | {r['full_name']:<45}")
        print(f"    {(r['description'] or '-')[:100]}")
        print(f"    {r['html_url']}")
    print()