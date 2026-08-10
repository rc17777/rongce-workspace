# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'
targets = [
    ('国企审计', '影子'),
    ('金融审计', '空壳'),
    ('农业农村审计', '农产品保单'),
    ('农业农村审计', '整体分析'),
    ('工程审计', '先种后铲'),
    ('教科文卫审计', '围标串标'),
    ('资源环境审计', 'ArcGIS'),
    ('预算执行审计', '60条'),
]
for sub, kw in targets:
    p = os.path.join(base, sub)
    for f in os.listdir(p):
        if kw in f:
            full = os.path.join(p, f)
            print(f'### [{sub}] {f}  ({os.path.getsize(full)} bytes)')
