import os, sys
sys.stdout.reconfigure(encoding='utf-8')
root = r'C:\Users\scrccpa\.openclaw\workspace'

# 55本书搜索
for search_dir, label in [
    (r'C:\Users\scrccpa\Desktop', 'Desktop'),
    (r'C:\Users\scrccpa\Documents', 'Documents'),
    (r'D:\openclaw-workspace', 'D-workspace'),
    (root, 'workspace'),
]:
    try:
        for item in os.listdir(search_dir):
            if '书' in item or 'book' in item.lower() or '55' in item or '电子书' in item:
                print(f'{label}: {item}')
    except Exception as e:
        print(f'{label}: skip ({e})')

# knowledge/literature
lp = os.path.join(root, 'knowledge', 'literature')
items = sorted(os.listdir(lp))[:30]
print(f'\nknowledge/literature/ ({len(os.listdir(lp))} items):')
for i in items:
    print(f'  {i}')

# knowledge/references 
rp = os.path.join(root, 'knowledge', 'references')
print(f'\nknowledge/references/:')
for f in sorted(os.listdir(rp)):
    print(f'  {f}')

# Obsidian 审计案例库结构
ob = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'
if os.path.exists(ob):
    subdirs = [d for d in os.listdir(ob) if os.path.isdir(os.path.join(ob, d))]
    print(f'\nObsidian 审计案例库-OCR/ 子目录: {subdirs[:15]}')
    for sd in subdirs[:8]:
        sdp = os.path.join(ob, sd)
        fcount = len(os.listdir(sdp))
        print(f'  {sd}/: {fcount} items')

# llm-wiki 内容
llm = r'C:\Users\scrccpa\.openclaw\skills\llm-wiki\platforms'
print(f'\nllm-wiki/platforms/:')
for f in sorted(os.listdir(llm)):
    print(f'  {f}')
