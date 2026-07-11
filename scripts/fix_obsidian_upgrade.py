# -*- coding: utf-8 -*-
from pathlib import Path
root=Path(r'D:\openclaw-workspace\obsidian-vault')
for p in (root/'_templates').glob('*.md'):
    s=p.read_text(encoding='utf8')
    s=s.replace('创建时间: {{date}}','创建时间: "{{date}}"').replace('updated: {{date}}','updated: "{{date}}"')
    p.write_text(s,encoding='utf8')
scenes=['预算编制','财政评审','工程结算','全过程工程咨询','营养餐审计']
for n in scenes:
    base=f'工程咨询/{n}/_index' if n!='营养餐审计' else '02-主题数据库/营养餐审计/_index'
    text=f'''---
type: 场景
场景名: "{n}"
business_line: "{n}"
updated: 2026-07-11
---
# 🎯 {n}｜场景入口

- [[{base}|进入业务驾驶舱]]

## 项目列表
```dataview
TABLE status AS 状态, due_date AS 交付日
FROM "01-项目对象库"
WHERE business_line = "{n}"
```
'''
    (root/'场景'/f'场景-{n}.md').write_text(text,encoding='utf8')
print('fixed templates and scenes')
