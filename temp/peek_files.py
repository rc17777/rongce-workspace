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
    '05-经济责任审计\\经济责任审计-巧用数据分析叫停“车轮腐败”.md',
    '03-民生审计\\民生审计-从一张迟迟未结算的消费券核销商户清单揭开一起重大违纪案件背后的“隐情”.md',
    '03-民生审计\\民生审计-工伤保险业务背后的基金安全风险.md',
    '03-民生审计\\民生审计-大数据锁定公立医院院长与供应商的利益勾连.md',
    '04-投资审计\\投资审计-被识破的基建造价“泡沫”.md',
    '06-资源环境审计\\资源环境审计-从200万元到3亿元的反常溢价.md',
    '06-资源环境审计\\资源环境审计-虚假合同背后的猫腻.md',
]
for f in files:
    p = os.path.join(base, f)
    t = read_any(p)
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    print('=' * 70)
    print(os.path.basename(f), '| non-empty lines:', len(lines))
    for l in lines[:36]:
        print('  ', l[:130])
