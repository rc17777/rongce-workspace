import sys
sys.stdout.reconfigure(encoding='utf-8')
src = open(r'C:\Users\scrccpa\.openclaw\workspace\temp\build_algorithm_lib_v5.py', 'rb').read()
idx = src.find(b'LINES = [')
chunk = src[idx:idx+6000].decode('utf-8', errors='replace')
for line in chunk.split('\n'):
    if '财会' in line or '税务' in line or '大数据审计' in line:
        print(line.strip())
