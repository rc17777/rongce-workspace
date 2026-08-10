# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

def read_any(path):
    raw = open(path, 'rb').read()
    for enc in ['utf-16', 'utf-8-sig', 'utf-8', 'gbk']:
        try:
            t = raw.decode(enc)
            return t.replace('\u0a0d', '\n')
        except Exception:
            continue
    return raw.decode('utf-8', errors='replace')

base = r'D:\杂志资料\按类型'
files = [
    '08-金融审计\\金融审计-被“熨平”的收益曲线.md',
    '08-金融审计\\金融审计-构建数据分析模型揭示银行违规问题的审计思路和方法.md',
    '07-企业审计\\企业审计-不翼而飞的应收账款.md',
    '07-企业审计\\企业审计-昂贵的“数字摆设”.md',
    '07-企业审计\\企业审计-高息融资现形记.md',
    '06-资源环境审计\\资源环境审计-利用ArcGIS与奥维地图双平台穿透私挖乱采“迷雾”.md',
    '06-资源环境审计\\资源环境审计-雾里寻踪揭开补充耕地项目的层层面纱.md',
    '04-投资审计\\投资审计-巧用大数据技术让围标串标问题无所遁形.md',
    '02-农业农村审计\\农业农村审计-整体分析由表及里 深挖骗取农业保险补贴行为.md',
]
for f in files:
    p = os.path.join(base, f)
    t = read_any(p)
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    print('=' * 70)
    print(os.path.basename(f), '| non-empty lines:', len(lines))
    for l in lines[:46]:
        print('  ', l[:135])
