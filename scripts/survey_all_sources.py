# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

def survey(path, label):
    total = 0
    total_size = 0
    by_dir = {}
    by_business = {}
    
    bus_lines = ['经责','收支','预算','专项','往来款','招投标','国企','成本','能源','工程','绩效','补贴',
                 '审计报告','审计方法','审计案例','法规','政策','AI审计','内部控制','财务造假','审计逻辑']
    
    for root, dirs, files in os.walk(path):
        if '.git' in root:
            continue
        for f in files:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            total += 1
            size = os.path.getsize(fp)
            total_size += size
            
            # by top dir
            rel = os.path.relpath(root, path)
            top = rel.split('\\')[0] if '\\' in rel else 'root'
            by_dir[top] = by_dir.get(top, 0) + 1
            
            # by business line (from filename)
            for bl in bus_lines:
                if bl in f or bl in rel:
                    by_business[bl] = by_business.get(bl, 0) + 1
                    break
    
    print(f'\n{"="*60}')
    print(f'  {label}: {total} files, {total_size/1024/1024:.1f}MB')
    print(f'{"="*60}')
    print('  按目录:')
    for k, v in sorted(by_dir.items(), key=lambda x: -x[1]):
        print(f'    {k}: {v}')
    
    if by_business:
        print('  按业务线（文件名匹配）:')
        for k, v in sorted(by_business.items(), key=lambda x: -x[1]):
            print(f'    {k}: {v}')
    
    return total, total_size

# survey knowledge/
t1, s1 = survey(r'C:\Users\scrccpa\.openclaw\workspace\knowledge', 'knowledge/')

# survey obsidian-vault/
t2, s2 = survey(r'C:\Users\scrccpa\.openclaw\workspace\obsidian-vault', 'obsidian-vault/')

# check LLM-WIKI skill
llm_wiki = r'C:\Users\scrccpa\.openclaw\skills\llm-wiki'
if os.path.exists(llm_wiki):
    t3, s3 = survey(llm_wiki, 'llm-wiki skill')
else:
    print(f'\n  llm-wiki skill: NOT FOUND at {llm_wiki}')
    t3, s3 = 0, 0

print(f'\n{"="*60}')
print(f'  总计: {t1+t2+t3} files, {(s1+s2+s3)/1024/1024:.1f}MB')
