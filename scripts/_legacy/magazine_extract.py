"""
杂志资料智能归纳流水线 Phase 1: 批量提取摘要
读取所有 MD 文件，按 category 分组，输出结构化摘要。
"""
import os, re, json
from collections import defaultdict

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault\杂志资料'
output_dir = r'D:\openclaw-workspace\temp\magazine_extract'
os.makedirs(output_dir, exist_ok=True)

# Category mapping
CAT_MAP = {
    '01-财政审计': '财政审计',
    '02-农业农村审计': '农业农村审计',
    '03-民生审计': '民生审计',
    '04-投资审计': '投资审计',
    '05-经济责任审计': '经济责任审计',
    '06-资源环境审计': '资源环境审计',
    '07-企业审计': '企业审计',
    '08-金融审计': '金融审计',
    '09-大数据与内部审计': '大数据内审',
}

category_data = defaultdict(list)
total = 0
errors = 0
no_cat = 0

for root, dirs, files in os.walk(vault):
    for filename in files:
        if not filename.endswith('.md'):
            continue
        total += 1
        path = os.path.join(root, filename)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            
            # Extract frontmatter
            m_title = re.search(r'title:\s*"(.+?)"', content)
            m_issue = re.search(r'issue:\s*"(.+?)"', content)
            m_cat = re.search(r'category:\s*"(.+?)"', content)
            m_type = re.search(r'type:\s*"(.+?)"', content)
            m_tags = re.search(r'tags:\s*\[(.*?)\]', content)
            
            title = m_title.group(1) if m_title else filename.replace('.md', '')
            issue = m_issue.group(1) if m_issue else ''
            cat = m_cat.group(1) if m_cat else ''
            atype = m_type.group(1) if m_type else ''
            tags = [t.strip().strip('"') for t in m_tags.group(1).split(',')] if m_tags else []
            
            # Extract body (after second ---)
            parts = content.split('---', 2)
            body = parts[2].strip() if len(parts) > 2 else content
            
            # Create summary (first 500 chars of body)
            summary = body[:500].replace('\n', ' ').strip()
            
            entry = {
                'title': title,
                'issue': issue,
                'type': atype,
                'tags': tags,
                'summary': summary,
                'char_count': len(body),
                'source': os.path.basename(root)
            }
            
            if cat in CAT_MAP:
                category_data[cat].append(entry)
            else:
                no_cat += 1
            
        except Exception as e:
            errors += 1

# Write per-category JSON
cat_counts = {}
for cat, entries in category_data.items():
    cat_name = CAT_MAP[cat]
    safe_name = cat.replace('/', '-')
    out_file = os.path.join(output_dir, f'{safe_name}.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    cat_counts[cat_name] = len(entries)

# Summary
summary = {
    'total_md': total,
    'errors': errors,
    'no_category': no_cat,
    'categories': cat_counts,
    'total_categorized': sum(cat_counts.values())
}

with open(os.path.join(output_dir, '_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print('=== Extraction Complete ===')
print(f'Total MD files: {total}')
print(f'Categorized: {summary["total_categorized"]}')
print(f'No category: {no_cat}')
print(f'Errors: {errors}')
print()
for cat_name, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
    print(f'  {count:>4}  {cat_name}')
