# -*- coding: utf-8 -*-
"""查找归类为"其他"的文章，需要用户确认归类"""
import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')

KB = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\magazines'
other_articles = []

for root, dirs, files in os.walk(KB):
    for f in files:
        if f.endswith('.md'):
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read(2000)
            if '"其他"' in content:
                title_m = re.search(r'title: "(.+?)"', content)
                title = title_m.group(1) if title_m else f
                summary_m = re.search(r'summary: "(.+?)"', content)
                summary = summary_m.group(1)[:100] if summary_m else ''
                other_articles.append({
                    'file': os.path.relpath(fp, KB),
                    'title': title,
                    'summary': summary
                })

print(f"=== 需确认归类的文章 ({len(other_articles)}篇) ===\n")
for i, a in enumerate(other_articles, 1):
    print(f"{i}. 【{a['title']}】")
    print(f"   来源: {a['file']}")
    print(f"   摘要: {a['summary']}...")
    print()

# 输出JSON供后续处理
with open(os.path.join(os.path.dirname(__file__), 'other_articles.json'), 'w', encoding='utf-8') as f:
    json.dump(other_articles, f, ensure_ascii=False, indent=2)
