import os, re

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault\杂志资料'
query_keywords = ['预算执行', '专项债券', '专项债', '预算', '国债']
results = []

for root, dirs, files in os.walk(vault):
    for filename in files:
        if not filename.endswith('.md'):
            continue
        path = os.path.join(root, filename)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read(5000)
        except:
            continue
        m_title = re.search(r'title:\s*"(.+?)"', content)
        title = m_title.group(1) if m_title else filename
        if any(kw in title for kw in query_keywords):
            m_issue = re.search(r'issue:\s*"(.+?)"', content)
            issue = m_issue.group(1) if m_issue else ''
            m_cat = re.search(r'category:\s*"(.+?)"', content)
            cat = m_cat.group(1) if m_cat else ''
            results.append({'title': title, 'issue': issue, 'category': cat, 'path': path})
        if len(results) >= 15:
            break
    if len(results) >= 15:
        break

print(f'Found {len(results)} matching articles:\n')
for r in results:
    print(f'  [{r["category"]}] {r["title"]}  ({r["issue"]})')
