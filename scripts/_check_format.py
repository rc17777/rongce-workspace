# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 检查索引文件格式
fp = r'D:\openclaw-workspace\.rag_index\rag_index.json'
with open(fp, 'rb') as f:
    magic = f.read(10)

print(f'前10字节: {magic.hex()}')
print(f'是否为pickle: {magic[:2] in (b"\x80\x04", b"\x80\x05")}')
print(f'是否为json: {magic[0:1] in (b"[", b"{")}')
print(f'完整前200字节:')
with open(fp, 'rb') as f:
    head = f.read(200)
print(repr(head[:200]))
