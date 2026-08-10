import os, sys, json
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\audit-articles'
files = sorted([f for f in os.listdir(base) if f.endswith('.md')])
print(f'知识库文章总数: {len(files)}')

bl_counter = Counter()
for f in files:
    with open(os.path.join(base, f), 'r', encoding='utf-8') as fh:
        content = fh.read()
        in_front = False
        for line in content.split('\n'):
            if line.strip() == '---':
                if not in_front:
                    in_front = True
                else:
                    break
                continue
            if in_front and line.startswith('business_line:'):
                bl = line.split(':', 1)[1].strip()
                for b in bl.split(','):
                    b = b.strip().strip('"').strip()
                    if b:
                        bl_counter[b] += 1

print('\n===== 业务线分布 =====')
for bl, cnt in bl_counter.most_common():
    print(f'  {bl}: {cnt}篇')

# Source distribution
src_counter = Counter()
for f in files:
    with open(os.path.join(base, f), 'r', encoding='utf-8') as fh:
        content = fh.read()
        for line in content.split('\n'):
            if line.startswith('source:'):
                src = line.split(':', 1)[1].strip().strip('"')
                src_counter[src] += 1
                break

print('\n===== 来源分布 =====')
for src, cnt in src_counter.most_common():
    print(f'  {src}: {cnt}篇')

obs = r'C:\Users\scrccpa\.openclaw\workspace\obsidian-vault\audit-articles'
ofiles = len([f for f in os.listdir(obs) if f.endswith('.md')])
print(f'\nObsidian同步: {ofiles}篇')
print(f'知识库: {len(files)}篇')
