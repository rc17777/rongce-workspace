import os, time
d = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\稽查文件3'
mds = [f for f in os.listdir(d) if f.endswith('.md')]
recent = sorted([(f, os.path.getmtime(os.path.join(d, f))) for f in mds], key=lambda x: x[1], reverse=True)[:10]
print('Latest 10 files:')
for f, t in recent:
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
    sz = os.path.getsize(os.path.join(d, f))
    print(f'  {f}: {ts} ({sz} bytes)')
