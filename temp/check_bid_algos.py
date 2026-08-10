import json, sys
sys.stdout.reconfigure(encoding='utf-8')
r = json.load(open(r'C:\Users\scrccpa\.openclaw\workspace\audit-blackboard\algorithm_registry.json','r',encoding='utf-8'))
al = r['algorithms']
bids = ['BID-PATTERN-005','BID-DARKMARK-001','BID-ROTATE-001','PROC-CONCEN-001','PROC-RELATED-001','INVEST-001','INVEST2-001','PROC2-001','PROC2-004']
for sn in bids:
    if sn not in al: continue
    a = al[sn]
    print(f'### {sn}: {a.get("name","")}')
    print(f'场景: {a.get("scene","")}')
    print(f'信号: {str(a.get("signals",""))[:200]}')
    print(f'公式: {str(a.get("calc_logic",""))[:200]}')
    print(f'阈值: {str(a.get("threshold",""))[:100]}')
    print(f'证据: {str(a.get("evidence",""))[:150]}')
    print()
