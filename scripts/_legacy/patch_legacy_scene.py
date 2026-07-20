#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补全审计案例库(非OCR)的scene字段"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'
base = os.path.join(vault, '审计案例库')

cnt = 0
for root, dirs, files in os.walk(base):
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8', errors='replace') as ff:
            content = ff.read()
        
        if not content.startswith('---'):
            continue
        end = content.find('---', 3)
        if end < 0:
            continue
        head = content[3:end]
        body = content[end+3:]
        
        # 如果已有scene就跳过
        if re.search(r'^scene:', head, re.MULTILINE):
            continue
        
        # 从tags提取场景
        m = re.search(r'tags:\s*\n([\s\S]*?)(?=\n\S)', head)
        if not m:
            # 也可能是单行格式 tags: [xxx, yyy]
            m = re.search(r'tags:\s*\[(.*?)\]', head)
            if m:
                tag_list = [t.strip().strip('"').strip("'") for t in m.group(1).split(',')]
            else:
                continue
        else:
            tag_block = m.group(1)
            tag_list = [t.strip().strip('- "').strip("'") for t in tag_block.split('\n') if t.strip()]
        
        # 找场景标签（排除"审计案例"、"扫描件"、[审计案例], [扫描件]）
        scene = ''
        for t in tag_list:
            t = t.strip('[]')
            if t not in ('审计案例', '扫描件', '审计案例-OCR', ''):
                scene = t
                break
        
        if not scene:
            continue
        
        # 插入scene字段（紧跟tags后面或单独插入）
        if 'tags:' in head:
            # 在tags行后插入
            new_head = re.sub(r'^(tags:.*?)$', f'\\1\nscene: "{scene}"', head, flags=re.MULTILINE)
        else:
            new_head = head.rstrip() + f'\nscene: "{scene}"\n'
        
        new_content = '---' + new_head + '---\n' + body.lstrip()
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(new_content)
        cnt += 1

print(f'补全完成: {cnt}篇')
