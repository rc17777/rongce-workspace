import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\audit-models\医保资金'
v2dir = os.path.join(base, 'v2')

models = {}
for f in os.listdir(base):
    if f.endswith('.md'):
        models[f] = os.path.join(base, f)
for f in os.listdir(v2dir):
    if f.endswith('.md') and f != 'INDEX-v2.0升级说明.md':
        models[f] = os.path.join(v2dir, f)

required = ['法规依据', '审计问题', '核心逻辑', '数据需求', '检测逻辑', '阈值', '典型发现', '局限性']
print(f'共 {len(models)} 个模型\n')

results = []
for name in sorted(models.keys()):
    path = models[name]
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    rule_count = len(re.findall(r'规则\d+:', content))
    data_tables = content.count('| 字段 |')
    has_refs = 'policy_refs' in content or '条>' in content
    
    found = []
    missing = []
    for s in required:
        if s in content:
            found.append(s)
        else:
            missing.append(s)
    
    status = 'OK' if len(missing) <= 2 else 'GAP'
    results.append((status, name, rule_count, data_tables, has_refs, missing))
    
    print(f'[{status}] {name}')
    print(f'  规则: {rule_count}条 | 数据表: {data_tables}个 | 法规引用: {"Y" if has_refs else "N"}')
    if missing:
        print(f'  缺失: {", ".join(missing)}')
    print()

# Summary
total_rules = sum(r[2] for r in results)
total_tables = sum(r[3] for r in results)
ok = sum(1 for r in results if r[0] == 'OK')
gap = sum(1 for r in results if r[0] == 'GAP')
print(f'=== 汇总 ===')
print(f'模型总数: {len(models)} (OK:{ok} GAP:{gap})')
print(f'规则总数: {total_rules}条')
print(f'数据表需求: {total_tables}个')
print(f'全部有法规引用: {all(r[4] for r in results)}')
print(f'平均每模型规则: {total_rules/len(models):.1f}条')
