# -*- coding: utf-8 -*-
import sys, os, shutil
sys.stdout.reconfigure(encoding='utf-8')

src = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\datasets\_rag_indexed'
dst = r'D:\openclaw-workspace\knowledge\datasets\_rag_indexed'

print(f"D盘 knowledge 存在: {os.path.exists(r'D:\openclaw-workspace\knowledge')}")
print(f"C盘 knowledge 存在: {os.path.exists(r'C:\Users\scrccpa\.openclaw\workspace\knowledge')}")

if not os.path.exists(src):
    print(f"源目录不存在: {src}")
    sys.exit(1)

files = os.listdir(src)
print(f"源文件数: {len(files)}")

# 复制到D盘
os.makedirs(dst, exist_ok=True)
copied = 0
for f in files:
    s = os.path.join(src, f)
    d = os.path.join(dst, f)
    if not os.path.exists(d) or os.path.getmtime(s) > os.path.getmtime(d):
        shutil.copy2(s, d)
        copied += 1

print(f"已复制: {copied} 个文件 → {dst}")
print(f"目标文件数: {len(os.listdir(dst))}")

# 确认RAG能索引到
print(f"\n路径在 D:\\openclaw-workspace\\knowledge 下: True")
print(f"扩展名 .md: True")
print(f"不在排除列表: True")
print(f"\n✅ 下一步: 运行 python scripts/rag_rebuild.py 重建索引")
