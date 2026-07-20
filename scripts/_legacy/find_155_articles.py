import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

base = r'C:\Users\scrccpa\Documents\Obsidian Vault'
keywords = ['十五五', '国资', '聚焦', '穿透', '四川审计']

found = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.md'):
            full = os.path.join(root, f)
            score = sum(1 for kw in keywords if kw in f)
            if score >= 2:
                found.append((score, full))

found.sort(key=lambda x: x[0], reverse=True)
for score, path in found[:20]:
    rel = os.path.relpath(path, base)
    print(f"[{score}] {rel}")
print(f"\nTotal matches: {len(found)}")
