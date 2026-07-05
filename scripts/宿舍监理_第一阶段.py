"""宿舍监理项目 — 第一阶段：关键文档文本提取 + 全量L5元数据 + 评标报告"""
import fitz, os, re, hashlib
from collections import Counter

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\5号6号学生宿舍建设项目监理"
OUT = r"D:\openclaw-workspace\output\宿舍监理"
os.makedirs(OUT, exist_ok=True)

# ====== Part 1: Extract text from key documents ======
print("=" * 60)
print("PART 1: 关键文档文本提取")
print("=" * 60)

key_files = {
    '招标文件': os.path.join(BASE, '监理招标文件定稿.pdf'),
    '书面报告': os.path.join(BASE, '监理定稿', '1.书面报告.pdf'),
    '评标报告': os.path.join(BASE, '监理定稿', '7.监理评标报告.pdf'),
    '中标公示': os.path.join(BASE, '监理定稿', '8.监理公示用章后.pdf'),
    '中标通知书': os.path.join(BASE, '监理定稿', '9.中标通知书签字盖章.pdf'),
}

for name, path in key_files.items():
    if not os.path.exists(path):
        print(f'  {name}: 文件不存在')
        continue
    try:
        doc = fitz.open(path)
        text = ''
        for pg in range(len(doc)):
            text += doc[pg].get_text()
        
        out_path = os.path.join(OUT, f'{name}.txt')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        meta = doc.metadata
        print(f'  {name}: {len(text):,} chars, {len(doc)} pages')
        print(f'    元数据: Producer={meta.get("producer","?")} Creator={meta.get("creator","?")} Author={meta.get("author","?")}')
        doc.close()
    except Exception as e:
        print(f'  {name}: ERROR - {str(e)[:80]}')

# ====== Part 2: L5元数据全量扫描（22家投标人）======  
print("\n" + "=" * 60)
print("PART 2: L5 元数据全量扫描")
print("=" * 60)

bid_dir = os.path.join(BASE, '监理投标文件(PDF)')
bid_files = sorted([f for f in os.listdir(bid_dir) if f.endswith('.pdf')])

meta_results = []
for fname in bid_files:
    path = os.path.join(bid_dir, fname)
    name = fname.replace('.pdf', '')
    try:
        doc = fitz.open(path)
        meta = doc.metadata
        pages = len(doc)
        
        # Check if has text layer (sample pages 0, mid, last)
        has_text = False
        for pg in [0, pages//2, pages-1] if pages > 0 else []:
            t = doc[pg].get_text()
            if t.strip() and len(t.strip()) > 50:
                has_text = True
                break
        
        meta_results.append({
            'name': name,
            'pages': pages,
            'has_text': has_text,
            'producer': meta.get('producer', '') or '',
            'creator': meta.get('creator', '') or '',
            'author': meta.get('author', '') or '',
            'created': meta.get('creationDate', '') or '',
            'mod_date': meta.get('modDate', '') or '',
        })
        
        producer_short = (meta.get('producer') or '?')[:50]
        creator_short = (meta.get('creator') or '?')[:30]
        author_short = (meta.get('author') or '?')[:30]
        
        print(f'  [{name[:20]:20s}] pgs={pages:3d} txt={has_text} | Producer={producer_short} | Creator={creator_short} | Author={author_short} | Created={meta.get("creationDate","?")}')
        doc.close()
        
    except Exception as e:
        print(f'  [{name[:20]:20s}] ERROR: {str(e)[:60]}')
        meta_results.append({'name': name, 'pages': 0, 'has_text': False, 'producer': '', 'creator': '', 'author': '', 'created': '', 'mod_date': ''})

# ====== Part 3: 分析元数据交叉 ======
print("\n" + "=" * 60)
print("PART 3: 元数据交叉分析")
print("=" * 60)

# Group by Producer
producer_groups = Counter([r['producer'] for r in meta_results])
print("\n按Producer分组:")
for p, count in producer_groups.most_common():
    names = [r['name'][:20] for r in meta_results if r['producer'] == p]
    print(f'  [{p[:60] if p else "(空白)"}]: {count}家')
    for n in names:
        print(f'    - {n}')

# Group by Creator
creator_groups = Counter([r['creator'] for r in meta_results])
print("\n按Creator分组:")
for c, count in creator_groups.most_common():
    names = [r['name'][:20] for r in meta_results if r['creator'] == c]
    print(f'  [{c[:40] if c else "(空白)"}]: {count}家')
    for n in names:
        print(f'    - {n}')

# Group by Author
author_groups = Counter([r['author'] for r in meta_results])
print("\n按Author分组:")
for a, count in author_groups.most_common():
    names = [r['name'][:20] for r in meta_results if r['author'] == a]
    print(f'  [{a[:30] if a else "(空白)"}]: {count}家')
    for n in names:
        print(f'    - {n}')

# Check for exact same Producer+Creator+Author combinations
combo_groups = Counter([(r['producer'], r['creator'], r['author']) for r in meta_results])
print("\n按Producer+Creator+Author组合分组:")
for combo, count in combo_groups.most_common():
    if count > 1:
        names = [r['name'][:20] for r in meta_results if (r['producer'],r['creator'],r['author'])==combo]
        p,c,a = combo
        print(f'  Producer=[{p[:50]}] Creator=[{c[:30]}] Author=[{a[:30]}]: {count}家')
        for n in names:
            print(f'    - {n}')

# Check for exact creation date matches
print("\nCreationDate完全匹配:")
date_groups = Counter([r['created'] for r in meta_results])
for d, count in date_groups.most_common():
    if count > 1 and d:
        names = [r['name'][:20] for r in meta_results if r['created'] == d]
        print(f'  {d}: {count}家')
        for n in names:
            print(f'    - {n}')

print(f"\n总投标人数: {len(meta_results)}")
print(f"有文字层: {sum(1 for r in meta_results if r['has_text'])}")
print(f"纯扫描件: {sum(1 for r in meta_results if not r['has_text'])}")
print(f"文件损坏: {sum(1 for r in meta_results if r['pages'] == 0)}")
