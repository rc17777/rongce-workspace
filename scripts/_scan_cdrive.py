import os, sys
sys.stdout.reconfigure(encoding='utf-8')

ws = r'C:\Users\scrccpa\.openclaw\workspace'

def dir_size(path):
    total = 0
    for r, d, fs in os.walk(path):
        total += sum(os.path.getsize(os.path.join(r, f)) for f in fs)
    return total

# Scan top-level items
items = []
for item in os.listdir(ws):
    ip = os.path.join(ws, item)
    if item.startswith('.') or item.startswith('_'):
        continue
    if os.path.isdir(ip):
        sz = dir_size(ip)
        md_cnt = sum(1 for r,d,fs in os.walk(ip) for f in fs if f.endswith('.md'))
        items.append((item, sz, md_cnt, True))
    else:
        sz = os.path.getsize(ip)
        items.append((item, sz, 1 if item.endswith('.md') else 0, False))

items.sort(key=lambda x: -x[1])

print(f'{"项目":<40} {"大小":>10} {"文件数":>8} 类型')
print('-' * 70)
total = 0
for name, sz, cnt, is_dir in items[:40]:
    total += sz
    icon = '📁' if is_dir else '📄'
    if sz > 1024*1024*1024:
        sizestr = f'{sz/1024/1024/1024:.1f}GB'
    elif sz > 1024*1024:
        sizestr = f'{sz/1024/1024:.0f}MB'
    else:
        sizestr = f'{sz/1024:.0f}KB'
    print(f'{icon} {name:<38} {sizestr:>10} {cnt:>8}')

print('-' * 70)
print(f'合计: {total/1024/1024/1024:.1f}GB')

# Also check for temp/cache dirs
extra_checks = [
    r'C:\Users\scrccpa\.openclaw\skills',
    r'C:\Users\scrccpa\.openclaw\extensions',
    r'C:\Users\scrccpa\AppData\Local\Temp\openclaw*',
]
for path in extra_checks:
    if '*' in path:
        import glob
        for match in glob.glob(path):
            sz = dir_size(match) if os.path.isdir(match) else os.path.getsize(match)
            if sz > 10*1024*1024:
                print(f'\n📁 {match}: {sz/1024/1024:.0f}MB')
    elif os.path.exists(path):
        sz = dir_size(path)
        print(f'\n📁 {path}: {sz/1024/1024:.0f}MB')
