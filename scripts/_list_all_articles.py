import os, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\audit-articles'
files = sorted([f for f in os.listdir(base) if f.endswith('.md')])

articles = []
for f in files:
    fp = os.path.join(base, f)
    with open(fp, 'r', encoding='utf-8') as fh:
        content = fh.read()
    # Parse frontmatter
    bl = '?'
    src = '?'
    summary = ''
    for line in content.split('\n'):
        if line.startswith('business_line:'):
            bl = line.split(':', 1)[1].strip().strip('"')
        if line.startswith('source:'):
            src = line.split(':', 1)[1].strip().strip('"')
        if line.startswith('summary:'):
            summary = line.split(':', 1)[1].strip().strip('"')
    articles.append({
        'name': f.replace('.md', ''),
        'bl': bl,
        'src': src,
        'summary': summary
    })

# Group by source
for src_name in ['中国审计 2026年第7期', '经济责任审计 2026年第6期']:
    group = [a for a in articles if a['src'] == src_name]
    print(f'\n{"="*70}')
    print(f'  {src_name}  ({len(group)}篇)')
    print(f'{"="*70}')
    for i, a in enumerate(group, 1):
        print(f'\n  [{i:02d}] [{a["bl"]}] {a["name"]}')
        if a['summary']:
            print(f'      📌 {a["summary"][:80]}')

print(f'\n{"="*70}')
print(f'  总计: {len(articles)}篇')
