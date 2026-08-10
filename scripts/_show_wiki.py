import os, sys
sys.stdout.reconfigure(encoding='utf-8')

wiki = r'C:\Users\scrccpa\.openclaw\workspace\obsidian-vault\wiki'

# Count by subdirectory
dirs = {}
files_at_root = 0
for item in sorted(os.listdir(wiki)):
    ip = os.path.join(wiki, item)
    if os.path.isdir(ip):
        cnt = sum(1 for r, d, fs in os.walk(ip) for f in fs if f.endswith('.md'))
        if cnt > 0:
            dirs[item] = cnt
    elif item.endswith('.md'):
        files_at_root += 1

print(f'=== obsidian-vault/wiki/ ({files_at_root + sum(dirs.values())}篇) ===')
print(f'根目录文件: {files_at_root}')
print(f'子目录: {len(dirs)}')
print()

# Show dirs by count
for name, cnt in sorted(dirs.items(), key=lambda x: -x[1]):
    print(f'  wiki/{name}/  ({cnt}篇)')

# Show some root files
if files_at_root > 0:
    print(f'\n根目录文件样例:')
    for f in sorted([f for f in os.listdir(wiki) if f.endswith('.md')])[:20]:
        print(f'  {f[:80]}')
