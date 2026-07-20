import os, glob

OUT = r'C:\Users\scrccpa\.openclaw\workspace\temp\policy_files.md'

kb = r'C:\Users\scrccpa\.openclaw\workspace\knowledge'
obsidian = r'C:\Users\scrccpa\Documents\Obsidian Vault'

lines = []

# 1. List all policy files in knowledge/policies/
lines.append('# 医保政策文件清单\n')

lines.append('## knowledge/policies/ 目录\n')
lines.append('| 序号 | 文件名 | 文件大小 |\n')
lines.append('|:---:|:------|:------:|\n')
for i, f in enumerate(sorted(glob.glob(kb+'/policies/**/*.md', recursive=True)), 1):
    sz = os.path.getsize(f)
    bn = os.path.basename(f)
    lines.append(f'| {i} | {bn} | {sz/1024:.1f}KB |\n')

lines.append('\n## knowledge/references/ 医保相关\n')
lines.append('| 序号 | 文件名 | 文件大小 |\n')
lines.append('|:---:|:------|:------:|\n')
for i, f in enumerate(sorted(glob.glob(kb+'/references/**/*.md', recursive=True)), 1):
    bn = os.path.basename(f)
    sz = os.path.getsize(f)
    lines.append(f'| {i} | {bn} | {sz/1024:.1f}KB |\n')

lines.append('\n## Obsidian Vault 核心医保政策文件\n')
lines.append('| 序号 | 文件名 | 文件大小 |\n')
lines.append('|:---:|:------|:------:|\n')
count = 0
for root, dirs, files in os.walk(obsidian):
    for f in files:
        if not f.endswith('.md'):
            continue
        path = os.path.join(root, f)
        # Check if file is about 医保 or 医疗保障
        # We can't rely on the filename (garbled), so let's read the first 100 chars
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                head = fh.read(200)
            if any(kw in head for kw in ['医保', '医疗保障', '社会保险', '医疗机构', '定点零售', 'DRG', 'DIP', '基金监管', '药品目录', '采购', '国办发', '医保发']):
                count += 1
                rel = os.path.relpath(path, obsidian)
                lines.append(f'| {count} | {rel} | {os.path.getsize(path)/1024:.1f}KB |\n')
                if count >= 30:
                    lines.append(f'| ... | (共{count}+文件，限于篇幅仅显示前30个) | ... |\n')
                    break
        except:
            pass

with open(OUT, 'w', encoding='utf-8') as out:
    out.writelines(lines)

print('Done. Written to', OUT)