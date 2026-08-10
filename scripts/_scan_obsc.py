import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

# Step 2: Scan Obsidian-C
obsc = r'C:\Users\scrccpa\Documents\Obsidian Vault'

# Audit/business keywords
audit_kw = ['审计', 'audit', '经责', '预算', '绩效', '招投标', '采购', '工程', '国企', '财政', '财务',
            '补贴', '能源', '资源', '环境', '数据化', '数字化', '大数据', 'AI', '人工智能',
            'RAG', '知识库', '政策', '法规', '案例', '底稿', '报告', '整改', '监督', '检查',
            '评价', '评估', '咨询', '造价', '结算', '决算', '内控', '风险', '合规']

files = []
for root, dirs, fnames in os.walk(obsc):
    # Skip hidden/system dirs
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['.obsidian', 'node_modules', '.trash']]
    for f in fnames:
        if f.endswith('.md'):
            fp = os.path.join(root, f)
            files.append((fp, f))

print(f'Obsidian-C: {len(files)} 个.md文件')

# Categorize by relevance
relevant = []
irrelevant = []

for fp, f in files:
    # Check filename
    fname_lower = f.lower()
    if any(kw in fname_lower for kw in audit_kw):
        relevant.append((fp, f, 'filename'))
        continue
    
    # Check first 500 chars of content
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read(500).lower()
        if any(kw in content for kw in audit_kw):
            relevant.append((fp, f, 'content'))
        else:
            irrelevant.append((fp, f))
    except:
        irrelevant.append((fp, f))

print(f'\n相关: {len(relevant)} 篇')
fname_match = sum(1 for _,_,m in relevant if m == 'filename')
content_match = sum(1 for _,_,m in relevant if m == 'content')
print(f'  - 文件名匹配: {fname_match}')
print(f'  - 内容匹配: {content_match}')
print(f'\n无关: {len(irrelevant)} 篇')

# Show sample of irrelevant
print('\n无关文件样本（前20）:')
for fp, f in irrelevant[:20]:
    rel = os.path.relpath(fp, obsc)
    print(f'  {rel}')
