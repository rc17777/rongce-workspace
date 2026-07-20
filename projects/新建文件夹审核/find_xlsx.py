import os, sys
sys.stdout.reconfigure(encoding='utf-8')
d = r'C:\Users\scrccpa\Desktop'
for f in os.listdir(d):
    if '复核' in f or '马尔康' in f or '三级' in f:
        print(repr(f))
