import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'D:\openclaw-workspace\memory\references\数据化审计-数字化专辑85篇目录.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    for n in range(47, 55):
        if f'#{n}' in line or f'#0{n}' in line:
            print(f"L{i}: {line.rstrip()[:150]}")
            break
