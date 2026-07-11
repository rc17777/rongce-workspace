#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位报告问题到章节位置"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

import docx

path = r'C:\Users\scrccpa\Desktop\四川食在攒劲餐饮服务有限公司2024年7月—2025年12月财务收支专项审计报告\四川食在攒劲餐饮服务有限公司2024年7月—2025年12月财务收支专项审计报告-（6月1日）.docx'
doc = docx.Document(path)

# 提取所有非空段落，标注章节
current_section = ""
current_sub = ""
chapter_map = {}

for i, p in enumerate(doc.paragraphs):
    text = p.text.strip()
    if not text:
        continue
    
    # 判断是否为章节标题
    if text.startswith('一、') or text.startswith('二、') or text.startswith('三、') or text.startswith('四、') or text.startswith('五、') or text.startswith('六、'):
        current_section = text
        current_sub = ""
    elif text.startswith('（一）') or text.startswith('（二）') or text.startswith('（三）') or text.startswith('（四）') or text.startswith('（五）'):
        current_sub = text
    
    chapter_map[i] = (current_section, current_sub, text[:60])

# 需要定位的问题点
targets = {
    'P145': 145,
    'P66': 66,
    'P86': 86,
    'P87': 87,
    'P65': 65,
    'P189': 189,
    'P200': 200,
    'P203': 203,
    'P209': 209,
    'P211': 211,
    'P216': 216,
    'P225': 225,
    'P240': 240,
    'P150': 150,
    'P168': 168,
    'P47': 47,
    'P49': 49,
    'P56': 56,
    'P129': 129,
}

print('===== 问题位置对照表 =====')
print()
for label, pid in targets.items():
    if pid in chapter_map:
        sec, sub, preview = chapter_map[pid]
        # 也显示前后内容方便确认
        prev_text = ""
        next_text = ""
        if pid-1 in chapter_map:
            prev_text = chapter_map[pid-1][2]
        if pid+1 in chapter_map:
            next_text = chapter_map[pid+1][2]
        
        print(f'{label} (P{pid}):')
        print(f'  章节: {sec}')
        if sub:
            print(f'  子节: {sub}')
        print(f'  原文: {preview}')
        print()
