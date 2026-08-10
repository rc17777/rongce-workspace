import os
import datetime

root = r'D:\openclaw-workspace\knowledge'
cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
exclude = {'dashboards', 'templates', 'inbox', '.obsidian'}
files = []

for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d not in exclude]
    for f in filenames:
        if f.endswith('.md'):
            fp = os.path.join(dirpath, f)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
            if mtime > cutoff:
                files.append((fp, mtime, os.path.getsize(fp)))

files.sort(key=lambda x: x[1], reverse=True)
for fp, mt, sz in files:
    print(fp)
    print(f"  modified: {mt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  size: {sz}")
