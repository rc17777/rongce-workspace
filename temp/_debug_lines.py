import sys, re
sys.stdout.reconfigure(encoding='utf-8')
src = open(r'C:\Users\scrccpa\.openclaw\workspace\temp\build_algorithm_lib_v5.py', encoding='utf-8').read()
idx = src.find('LINES = [')
end = src.find('BIZ_FALLBACK')
section = src[idx:end]
names = re.findall(r"'([^']*)'", section)
# Filter to line name tuples
line_names = [n for n in names if '审计' in n or '延伸' in n or '检查' in n]
for i, n in enumerate(line_names):
    print(f'{i}: {n}')
