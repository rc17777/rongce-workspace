import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
output_dir = r'D:\openclaw-workspace\output'
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, '审计方法详解手册.xlsx')

# Re-run the original generation logic
exec(open(r'D:\openclaw-workspace\scripts\gen_audit_methods.py', encoding='utf-8').read())

print(f'Done: {output_path}')
print(f'Size: {os.path.getsize(output_path):,} bytes')
