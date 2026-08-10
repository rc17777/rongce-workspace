import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open(r'C:\Users\scrccpa\.openclaw\workspace\temp\batch_algorithms_batch1.json', 'r', encoding='utf-8'))
algos = d['algorithms']
total = d['total_algorithms']
print(f'Total: {total}')
l2 = sum(1 for a in algos if a.get('complexity') == 'L2')
l3 = sum(1 for a in algos if a.get('complexity') == 'L3')
print(f'L2 rules: {l2}, L3 algorithms: {l3}')
print()
for a in algos:
    c = a.get('complexity', '?')
    sn = a.get('sn', '?')
    name = a.get('name', '?')[:55]
    print(f'{sn:22s} [{c}] {name}')
