import os, sys
sys.stdout.reconfigure(encoding='utf-8')

lit = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\literature'

# Get all year-month dirs and count files
months = []
for item in sorted(os.listdir(lit)):
    ip = os.path.join(lit, item)
    if os.path.isdir(ip) and not item.startswith('.'):
        md_files = [f for f in os.listdir(ip) if f.endswith('.md')]
        total_size = sum(os.path.getsize(os.path.join(ip, f)) for f in md_files)
        months.append((item, len(md_files), total_size, ip, md_files))

# Yearly summary
from collections import defaultdict
yearly = defaultdict(lambda: {'count': 0, 'size': 0})
for m, cnt, sz, _, _ in months:
    year = m.split('-')[0]
    yearly[year]['count'] += cnt
    yearly[year]['size'] += sz

print('='*65)
print('  literature/ 学术文献 — 年度汇总')
print('='*65)
total_cnt = 0
total_sz = 0
for year in sorted(yearly.keys()):
    y = yearly[year]
    total_cnt += y['count']
    total_sz += y['size']
    print(f'  {year}年: {y["count"]:>4}篇  {y["size"]/1024/1024:.1f}MB')
print(f'  {"─"*30}')
print(f'  合计: {total_cnt}篇  {total_sz/1024/1024:.1f}MB')

# Monthly breakdown with samples
print(f'\n{"="*65}')
print(f'  月度明细（含样例文章）')
print(f'{"="*65}')

for m, cnt, sz, path, files in months:
    kb = sz/1024
    print(f'\n  ── {m}  ({cnt}篇, {kb:.0f}KB) ──')
    # Show up to 4 samples
    samples = sorted(files, key=lambda f: os.path.getsize(os.path.join(path, f)), reverse=True)[:4]
    for f in samples:
        fname = f.replace('.md', '')
        if len(fname) > 75:
            fname = fname[:72] + '...'
        fsz = os.path.getsize(os.path.join(path, f)) / 1024
        print(f'    • {fname}  [{fsz:.0f}KB]')
