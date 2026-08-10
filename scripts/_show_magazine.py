import os, sys
sys.stdout.reconfigure(encoding='utf-8')

mgzl = r'D:\openclaw-workspace\knowledge\杂志资料'

for top_dir in sorted(os.listdir(mgzl)):
    ip = os.path.join(mgzl, top_dir)
    if not os.path.isdir(ip):
        continue
    
    subs = {}
    root_mds = []
    for item in sorted(os.listdir(ip)):
        sip = os.path.join(ip, item)
        if os.path.isdir(sip):
            cnt = sum(1 for r, d, fs in os.walk(sip) for f in fs if f.endswith('.md'))
            if cnt > 0:
                subs[item] = cnt
        elif item.endswith('.md'):
            root_mds.append(item)
    
    total = sum(subs.values()) + len(root_mds)
    print()
    print('=' * 60)
    print(f'  {top_dir}/  ({total}篇)')
    print('=' * 60)
    
    if subs:
        for sn, sc in sorted(subs.items(), key=lambda x: -x[1])[:15]:
            print(f'  {sn}/ ({sc}篇)')
            sip2 = os.path.join(ip, sn)
            samples = sorted([f for f in os.listdir(sip2) if f.endswith('.md')])[:2]
            for s in samples:
                print(f'      . {s[:80]}')
    
    if root_mds:
        print(f'  根目录 ({len(root_mds)}篇):')
        for f in sorted(root_mds)[:6]:
            print(f'      . {f[:80]}')

print()
total_all = sum(1 for r, d, fs in os.walk(mgzl) for f in fs if f.endswith('.md'))
print(f'总计: {total_all}篇')
