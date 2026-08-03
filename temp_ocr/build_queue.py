# -*- coding: utf-8 -*-
"""扫描全部源PDF，建立完整OCR队列——小文件优先"""
import os, sys, json, glob
sys.stdout.reconfigure(encoding='utf-8')

SRC = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）'
OUT = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'

# 收集所有源PDF
all_pdfs = []
for root, dirs, files in os.walk(SRC):
    for f in files:
        if f.lower().endswith('.pdf'):
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            all_pdfs.append((sz, f, fp))

all_pdfs.sort()  # 按大小排序，小的先跑

# 检查哪些已经OCR过(有output目录且progress>=100%)
done_labels = set()
for d in os.listdir(OUT):
    dp = os.path.join(OUT, d)
    if not os.path.isdir(dp): continue
    pf = os.path.join(dp, '_progress.json')
    if os.path.exists(pf):
        p = json.load(open(pf, encoding='utf-8'))
        if len(p.get('done',[])) >= p.get('total',0):
            done_labels.add(d)

print(f'源PDF总数: {len(all_pdfs)}')
print(f'已100%完成: {len(done_labels)} 本')
print()

queue = []
for sz, name, path in all_pdfs:
    label = os.path.splitext(name)[0][:50]
    rel = os.path.relpath(path, SRC)
    if label in done_labels:
        continue
    # 估算页数(基于文件大小)
    est_pages = max(1, int(sz / 1024 / 1024 * 1.5))
    if sz > 100*1024*1024:
        est_pages = max(1, int(sz / 1024 / 1024 * 1.5))
    queue.append((sz, label, rel))

print(f'待OCR队列: {len(queue)} 本')
print()
print('--- 前20本（最小的）---')
for sz, name, rel in queue[:20]:
    print(f'  {sz/1024/1024:8.1f}MB  {name[:45]}')
if len(queue) > 20:
    print(f'  ... 还有 {len(queue)-20} 本')

# 输出队列JSON供OCR脚本使用
with open(os.path.join(os.path.dirname(OUT), 'full_queue.json'), 'w', encoding='utf-8') as f:
    json.dump([{'label': name, 'rel_path': rel, 'size_mb': round(sz/1024/1024,1)} for sz, name, rel in queue], f, ensure_ascii=False, indent=2)

print(f'\n队列已写入: full_queue.json')
# 估算总时间
total_mb = sum(sz/1024/1024 for sz,_,_ in queue)
print(f'待处理总大小: {total_mb:.0f}MB, 预估 ~{total_mb*0.5/60:.0f} 小时')
