# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

# 先确认文件实际路径
base = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\magazines'
target_dirs = []

for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.md'):
            fp = os.path.join(root, f)
            # 招投标/采购相关
            keywords = ['采购', '招标', '投标', '串标', '围标', 'tender', 'bid', '异常低价', '虚构采购']
            if any(k in f for k in keywords):
                target_dirs.append(fp)

print(f'找到 {len(target_dirs)} 篇招投标/采购相关文章:\n')
for i, fp in enumerate(target_dirs, 1):
    size = os.path.getsize(fp)
    kb = size / 1024
    print(f'{i}. [{kb:.1f}KB] {fp}')

# 保存路径到文件，方便后续脚本读取
out = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\datasets\bidding-audit\_sources.txt'
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(target_dirs))
print(f'\n路径清单已保存到: {out}')
