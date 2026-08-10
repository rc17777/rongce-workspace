import os, json, time
d = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\稽查文件3'
mds = [f for f in os.listdir(d) if f.endswith('.md')]
print(f'Total .md files: {len(mds)}')
recent = sorted(mds, key=lambda x: os.path.getmtime(os.path.join(d, x)), reverse=True)[:5]
for f in recent:
    mt = os.path.getmtime(os.path.join(d, f))
    ts = time.strftime('%H:%M:%S', time.localtime(mt))
    sz = os.path.getsize(os.path.join(d, f))
    print(f'  {f}  {ts}  {sz}b')
pf = os.path.join(d, '_progress.json')
pd = json.load(open(pf, encoding='utf-8'))
print(f'Progress: {len(pd["done"])}/{pd["total"]}')
