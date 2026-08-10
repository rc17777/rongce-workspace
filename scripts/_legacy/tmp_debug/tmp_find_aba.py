# -*- coding: utf-8 -*-
import os, datetime, sys
sys.stdout.reconfigure(encoding='utf-8')
desktop = os.path.expanduser(r'~\Desktop')
for f in os.listdir(desktop):
    if '阿坝' not in f:
        continue
    fp = os.path.join(desktop, f)
    if not os.path.isfile(fp):
        continue
    s = os.path.getsize(fp)
    m = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    print(f'{m.strftime("%m-%d %H:%M")} | {s:>12,}B | {f}')
