#!/usr/bin/env python3
"""Update TECHNICAL-FOUNDATION.md to v3.2"""
path = r'D:\openclaw-workspace\skills\procurement-audit-models\TECHNICAL-FOUNDATION.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# v3.1 -> v3.2
content = content.replace(
    '# 招投标串标围标检测 — 技术底座 v3.1',
    '# 招投标串标围标检测 — 技术底座 v3.2'
)
content = content.replace(
    '> v3.1 更新: 新增L11(跨项目伴随投标) + L12(历史投标异常关联)',
    '> v3.2 更新: 新增L13(节资率分析+支持度/置信度) + L14(最优围标人数规则)'
)

# Add L13/L14 to core table
old_l12 = '| **L12** | **历史投标异常关联** | **历史IP/MAC/关联标记数据库** |'
new_l12 = '| **L12** | **历史投标异常关联** | **历史IP/MAC/关联标记数据库** | **需建立历史异常标记库** |\n| **L13** | **节资率分析+支持度/置信度** | **招标台账(控制价+中标价+投标人)** | **需历史招标台账数据** |\n| **L14** | **最优围标人数** | **投标单位数=3~4** | **投标人数统计即可** |'
content = content.replace(old_l12, new_l12)

# Add D6/D7 to 纵深 table
old_d5 = '| D5 | 文件系统时间线 | stat(ctime/mtime/atime) + PDF内部时间戳 | 还原文件制作时序 |'
new_d5 = old_d5 + '\n| **D6** | **节资率箱线图** | **IQR异常检测+节资率低疑点表** | **竞争不足的围标信号** |\n| **D7** | **支持度/置信度矩阵** | **投标人共现网络** | **长期联手围标集团** |'
content = content.replace(old_d5, new_d5)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated to v3.2')
