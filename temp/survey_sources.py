import os, sys
sys.stdout.reconfigure(encoding='utf-8')

print('=== 杂志资料目录结构 ===')
mag = r'D:\杂志资料'
if os.path.exists(mag):
    for root, dirs, files in os.walk(mag):
        level = root.replace(mag, '').count(os.sep)
        indent = '  ' * level
        md = sum(1 for f in files if f.endswith('.md'))
        pdf = sum(1 for f in files if f.endswith('.pdf'))
        docx = sum(1 for f in files if f.endswith('.docx'))
        name = os.path.basename(root) or '杂志资料'
        parts = []
        if md: parts.append(f'{md}md')
        if pdf: parts.append(f'{pdf}pdf')
        if docx: parts.append(f'{docx}docx')
        if parts:
            print(f'{indent}{name}: {", ".join(parts)}')
        if level >= 3:  # don't go too deep
            dirs.clear()
else:
    print('杂志资料目录不存在')

print('\n=== My eBooks ===')
ebooks = r'C:\Users\scrccpa\Documents\My eBooks\My Bookcase'
if os.path.exists(ebooks):
    for f in sorted(os.listdir(ebooks))[:10]:
        print(f'  {f}')
    total = len(os.listdir(ebooks))
    print(f'  ... {total} files total')
else:
    print('My eBooks 目录不存在')

print('\n=== 政策法规库 ===')
laws_path = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\laws'
if os.path.exists(laws_path):
    for d in os.listdir(laws_path):
        dp = os.path.join(laws_path, d)
        if os.path.isdir(dp):
            n = len(os.listdir(dp))
            print(f'  {d}: {n} files')
else:
    print('laws目录不存在')
