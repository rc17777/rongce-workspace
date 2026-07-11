import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import fitz
from collections import Counter

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\5号6号学生宿舍建设项目监理"
bid_dir = os.path.join(BASE, '监理投标文件(PDF)')

meta_results = []
for fname in sorted(os.listdir(bid_dir)):
    if not fname.endswith('.pdf'): continue
    path = os.path.join(bid_dir, fname)
    name = fname.replace('.pdf', '')
    try:
        doc = fitz.open(path)
        meta = doc.metadata
        meta_results.append({
            'name': name, 'pages': len(doc),
            'producer': meta.get('producer','') or '',
            'creator': meta.get('creator','') or '',
            'author': meta.get('author','') or '',
            'created': meta.get('creationDate','') or '',
        })
        doc.close()
    except Exception as e:
        meta_results.append({'name':name,'pages':0,'producer':f'ERR:{e}','creator':'','author':'','created':''})

# Producer
print('=== Producer ===')
pg = Counter([r['producer'][:80] for r in meta_results])
for p,c in pg.most_common():
    names = [r['name'][:25] for r in meta_results if r['producer'][:80]==p]
    print(f'{p}\n  {c}家: {", ".join(names)}')

# Author
print('\n=== Author ===')
ag = Counter([r['author'] for r in meta_results])
for a,c in ag.most_common():
    names = [r['name'][:25] for r in meta_results if r['author']==a]
    print(f'[{a}]: {c}家 = {", ".join(names)}')

# CreationDate
print('\n=== CreationDate ===')
dg = Counter([r['created'] for r in meta_results])
for d,c in dg.most_common():
    names = [r['name'][:25] for r in meta_results if r['created']==d]
    print(f'{d}: {c}家 = {", ".join(names)}')

# Check if ALL match
all_same = all(
    r['producer'] == meta_results[0]['producer'] and
    r['creator'] == meta_results[0]['creator'] and
    r['author'] == meta_results[0]['author'] and
    r['created'] == meta_results[0]['created']
    for r in meta_results
)

print(f'\n===== 全部22家元数据完全一致: {"是" if all_same else "否"} =====')
print(f'Producer: {meta_results[0]["producer"][:120]}')
print(f'Creator:  {meta_results[0]["creator"]}')
print(f'Author:   {meta_results[0]["author"]}')
print(f'Created:  {meta_results[0]["created"]}')
