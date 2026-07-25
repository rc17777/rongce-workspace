import os, sys
sys.stdout.reconfigure(encoding='utf-8')

skills_dir = os.path.expanduser('~/.openclaw/skills')
workspace = os.path.expanduser('~/.openclaw/workspace')

all_skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir,d))]

lines = [
    (1, '经济责任审计', 'jt', 'audit-jingze'),
    (2, '收支审计', 'sz', None),
    (3, '预算执行审计', 'ys', 'budget-audit'),
    (4, '专项资金审计', 'zx', 'special-fund-audit'),
    (5, '往来款清理', 'wl', None),
    (6, '招投标审计', 'zb', 'procurement-audit-models'),
    (7, '国企审计', 'gq', None),
    (8, '成本效益审计', 'cb', None),
    (9, '能源审计', 'ny', 'energy-audit'),
    (10, '工程竣工决算财务审计', 'gc', 'engineering-audit'),
    (11, '预算绩效管理', 'jx', 'perf-audit-checklist'),
    (12, '政府补贴审计', 'bt', 'subsidy-audit'),
]

# Map skills to business lines
skill_map = {
    'audit-jingze': 1,
    'audit-report-review': [1,2,3,4,6,7,10,11,12],
    'perf-audit-checklist': 11,
    'procurement-audit-models': 6,
    'financial-fraud-detection': [1,2,3,4,7,8],
    'budget-audit': 3,
    'special-fund-audit': 4,
    'subsidy-audit': 12,
    'energy-audit': 9,
    'engineering-audit': 10,
    'bim-engineering-audit': 10,
    'fiscal-supervision-model': [1,2,3,4],
    'special-bond-audit': 4,
    'gov-audit-methodology': [1,2,3,4,7,11],
    'gov-subsidy-penetration-audit': 12,
    'spatial-audit-analysis': [6,9,10],
    'digital-audit-methodology': [1,2,3,4,6,7,8,9,10,11,12],
    'unstructured-audit-data': [1,2,3,4,6,7],
    'apriori-audit': [1,4,6,7],
    'audit-knowledge-graph': [1,2,3,4,6,7,11],
    'data-analyst-cn': [1,2,3,4,5,6,7,8,9,10,11,12],
    'deepseek-charting': [1,2,3,4,6,7,8,9,10,11,12],
    'drawio': [1,2,3,4,6,7,10,11],
    'audit-data-analysis-methods': [1,2,3,4,6,7,8,9,10,11,12],
    'bid-document': [6,10,11],
    'gov-doc-formatting': [1,2,3,4,6,7,10,11,12],
}

print('=' * 70)
print('融策12大业务线 - 现有资产覆盖度评估')
print('=' * 70)

for num, name, short, skill_hint in lines:
    has_dedicated = skill_hint and skill_hint in all_skills
    
    # Count supporting skills
    supporting = []
    for sk, targets in skill_map.items():
        if isinstance(targets, list):
            if num in targets and sk != skill_hint:
                supporting.append(sk)
        elif targets == num and sk != skill_hint:
            supporting.append(sk)
    
    # Check knowledge base
    kb_count = 0
    kb_path = os.path.join(workspace, 'knowledge')
    for root, dirs, files in os.walk(kb_path):
        for f in files:
            if f.endswith('.md'):
                fname = f.lower()
                if short in fname:
                    kb_count += 1
    
    # Check RAG index
    rag_file = os.path.join(workspace, 'knowledge', '审计资料清单.json')
    rag_count = 0
    if os.path.exists(rag_file):
        import json
        with open(rag_file, 'r', encoding='utf-8') as fh:
            catalog = json.load(fh)
        # Count items with relevant keywords
        keywords_map = {
            1: ['经责', '经济责任', '离任', '任中'],
            2: ['收支'],
            3: ['预算执行', '部门预算'],
            4: ['专项', '专项资金', '社保', '营养餐'],
            5: ['往来', '资金清理'],
            6: ['招投标', '采购', '围标', '串标'],
            7: ['国企', '国有企业'],
            8: ['成本', '效益'],
            9: ['能源', '碳中和'],
            10: ['工程', '竣工', '决算'],
            11: ['绩效', '绩效评价'],
            12: ['补贴', '补助', '政府补贴'],
        }
        if isinstance(catalog, list):
            for item in catalog:
                kw_list = keywords_map.get(num, [])
                title = str(item.get('title', '') or '') + str(item.get('filename', '') or '')
                for kw in kw_list:
                    if kw in title:
                        rag_count += 1
                        break
        elif isinstance(catalog, dict):
            for k, v in catalog.items():
                kw_list = keywords_map.get(num, [])
                title = str(v.get('title','') or '') + str(v.get('filename','') or '') + str(k)
                for kw in kw_list:
                    if kw in title:
                        rag_count += 1
                        break
    
    score = 0
    if has_dedicated:
        score += 3
    score += min(len(supporting), 5) 
    if rag_count >= 5:
        score += 2
    elif rag_count >= 1:
        score += 1
    
    level = '★★★' if score >= 8 else ('★★☆' if score >= 5 else ('★☆☆' if score >= 2 else '☆☆☆'))
    
    print(f'\n{num:2d}. {name}  {level} (score={score})')
    print(f'    专属技能: {"YES" if has_dedicated else "NO"} | 辅助技能: {len(supporting)}个 | 知识库: ~{rag_count}条')
    if supporting:
        print(f'    辅助: {supporting[:3]}...' if len(supporting)>3 else f'    辅助: {supporting}')

print('\n' + '=' * 70)
print('梯队建议（基于标准化成熟度）:')
print('第一梯队(score>=5): 已有方法论基础,可立即启动指引编写')
print('第二梯队(score 2-4): 有部分积累,需补充后再写')
print('第三梯队(score<=1): 需从头建设')
