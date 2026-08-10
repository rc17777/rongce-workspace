import os, json
out = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\医保局稽查文件3'
items = os.listdir(out)
mds = [f for f in items if f.endswith('.md')]
old_fmt = [f for f in mds if f.startswith('p') and f[1].isdigit()]
new_fmt = [f for f in mds if f.startswith('chunk')]
print(f'Old (pNNNN): {len(old_fmt)}')
print(f'New (chunk_p): {len(new_fmt)}')
print(f'Total .md: {len(mds)}')
# check progress files
for f in sorted(items):
    if f.startswith('_progress_'):
        fp = os.path.join(out, f)
        d = json.load(open(fp, encoding='utf-8'))
        print(f'  {f}: {len(d.get("done",[]))}/{d.get("total","?")}')
# check chunk manifest
manifest = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\split_chunks\_chunk_progress.json'
if os.path.exists(manifest):
    md = json.load(open(manifest, encoding='utf-8'))
    print(f'Chunks done: {md.get("done",[])}')
