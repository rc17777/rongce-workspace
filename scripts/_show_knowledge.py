import os, sys
sys.stdout.reconfigure(encoding='utf-8')

kb = r'C:\Users\scrccpa\.openclaw\workspace\knowledge'

def show_dir(path, name, max_show=12):
    """Show directory contents"""
    md_files = []
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if os.path.isfile(fp) and f.endswith('.md'):
            sz = os.path.getsize(fp)
            md_files.append((f.replace('.md',''), sz))
        elif os.path.isdir(fp):
            sub_md = sum(1 for r,d,fs in os.walk(fp) for fn in fs if fn.endswith('.md'))
            if sub_md > 0:
                md_files.append((f'📁 {f}/ ({sub_md}篇)', 0))
    md_files.sort(key=lambda x: -x[1])
    
    total = len([x for x in md_files if not x[0].startswith('📁')])
    print(f'\n{"─"*60}')
    print(f'  {name}  ({total}个文件)')
    print(f'{"─"*60}')
    for i, (fn, sz) in enumerate(md_files[:max_show]):
        if sz > 0:
            kbsz = sz/1024
            if kbsz > 100:
                sizestr = f'{kbsz:.0f}KB'
            else:
                sizestr = f'{kbsz:.1f}KB'
            print(f'  {fn}  [{sizestr}]')
        else:
            print(f'  {fn}')
    if len(md_files) > max_show:
        print(f'  ... 还有 {len(md_files)-max_show} 个未显示')

# Show all top-level dirs and files
print('='*60)
print('  knowledge/ 目录明细')
print('='*60)

# Top level files
top_files = [f for f in os.listdir(kb) if os.path.isfile(os.path.join(kb, f)) and f.endswith('.md')]
if top_files:
    print(f'\n📄 根目录文件 ({len(top_files)}个):')
    for f in sorted(top_files)[:10]:
        print(f'  {f}')

# Subdirectories sorted by content size
subdirs = []
for item in sorted(os.listdir(kb)):
    ip = os.path.join(kb, item)
    if os.path.isdir(ip) and not item.startswith('.') and not item.startswith('_'):
        cnt = sum(1 for r,d,fs in os.walk(ip) for f in fs if f.endswith('.md'))
        if cnt > 0:
            subdirs.append((item, cnt, ip))

subdirs.sort(key=lambda x: -x[1])

for name, cnt, path in subdirs[:20]:
    show_dir(path, f'{name}/ ({cnt}篇)')
