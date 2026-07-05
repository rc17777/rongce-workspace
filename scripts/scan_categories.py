import os, re
from collections import Counter

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault\杂志资料'
out_path = r'D:\openclaw-workspace\temp\cat_output.txt'
categories = Counter()
total = 0
errors = 0

for root, dirs, files in os.walk(vault):
    for filename in files:
        if not filename.endswith('.md'):
            continue
        total += 1
        path = os.path.join(root, filename)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read(2000)
            m = re.search(r'category:\s*"(.+?)"', content)
            if m:
                categories[m.group(1)] += 1
        except:
            errors += 1

with open(out_path, 'w', encoding='utf-8') as outf:
    outf.write(f'Total MD: {total}, Errors: {errors}\n\n')
    outf.write('=== Categories ===\n')
    for cat, count in categories.most_common():
        outf.write(f'  {count:>4}  {cat}\n')

print('Done')
