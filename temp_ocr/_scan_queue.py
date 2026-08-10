import os, json, glob, time
out = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
src = r'D:\2026\审计项目\若尔盖县城乡居民基本医疗保险及人员意外伤害保险、大病保险报销资料专项审计调查'

# Get all PDFs sorted by size (small first)
pdfs = []
for root, dirs, files in os.walk(src):
    for f in files:
        if f.lower().endswith('.pdf'):
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            pdfs.append((sz, f, fp))

pdfs.sort()

# Check which are already done
done_names = set()
for d in os.listdir(out):
    dp = os.path.join(out, d)
    if not os.path.isdir(dp): continue
    pf = os.path.join(dp, '_progress.json')
    if not os.path.exists(pf): continue
    p = json.load(open(pf, encoding='utf-8'))
    if len(p.get('done', [])) >= p.get('total', 0) and p.get('total', 0) > 0:
        done_names.add(d)

pending = []
for sz, name, fp in pdfs:
    base = os.path.splitext(name)[0]
    if base not in done_names:
        pending.append((sz, name, fp))

print(f'已完成: {len(done_names)}')
print(f'剩余: {len(pending)}')
print()

for i, (sz, name, fp) in enumerate(pending[:15]):
    mb = sz / 1024 / 1024
    print(f'  {i+1}. {name[:60]:<62} {mb:.1f}MB')
    print(f'     {fp[:120]}')
if len(pending) > 15:
    mb_total = sum(s[0] for s in pending) / 1024 / 1024
    print(f'  ... 还有 {len(pending)-15} 本，共 {mb_total:.0f}MB')
