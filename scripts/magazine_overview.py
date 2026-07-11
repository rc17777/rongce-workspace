"""
Phase 1.5: 全量标题扫描 - 聚类分析
读取所有文章标题和标签，做词频+共现分析，
快速识别跨期刊的核心主题集群
"""
import os, re, json
from collections import Counter

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault\杂志资料'

# Collect all titles and tags
all_titles = []
tag_counter = Counter()
type_counter = Counter()
cat_counter = Counter()

for root, dirs, files in os.walk(vault):
    for filename in files:
        if not filename.endswith('.md'):
            continue
        path = os.path.join(root, filename)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read(3000)
            
            m_title = re.search(r'title:\s*"(.+?)"', content)
            m_cat = re.search(r'category:\s*"(.+?)"', content)
            m_type = re.search(r'type:\s*"(.+?)"', content)
            m_tags = re.search(r'tags:\s*\[(.*?)\]', content)
            
            if m_title:
                all_titles.append(m_title.group(1))
            if m_cat:
                cat_counter[m_cat.group(1)] += 1
            if m_type:
                type_counter[m_type.group(1)] += 1
            if m_tags:
                for t in m_tags.group(1).split(','):
                    tag = t.strip().strip('"')
                    if tag:
                        tag_counter[tag] += 1
        except:
            pass

# Save results
out = {
    'total_articles': len(all_titles),
    'categories': dict(cat_counter.most_common()),
    'article_types': dict(type_counter.most_common(20)),
    'top_tags': dict(tag_counter.most_common(50)),
    'sample_titles': all_titles[:30]
}

out_path = r'D:\openclaw-workspace\temp\magazine_overview.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f'{len(all_titles)} articles indexed')
print(f'{len(cat_counter)} categories')
print(f'{len(tag_counter)} unique tags')
print(f'Saved to {out_path}')
