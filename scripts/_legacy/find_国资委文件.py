#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜索国资委相关文件"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

# 搜索knowledge目录
base = r'D:\openclaw-workspace\knowledge'
if os.path.isdir(base):
    print(f"📂 knowledge/ 目录搜索:")
    for root, dirs, files in os.walk(base):
        for f in files:
            if any(kw in f for kw in ['国资委','1号','2号','15号','46号']):
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                rel = os.path.relpath(fp, base)
                print(f"  {rel} ({sz//1000}KB)")

# 搜索obsidian
vault = r'D:\openclaw-workspace\obsidian-vault'
if os.path.isdir(vault):
    print(f"\n📂 obsidian-vault/ 目录搜索:")
    for root, dirs, files in os.walk(vault):
        for f in files:
            if any(kw in f for kw in ['国资委','1号','2号','15号','46号','穿透式','数智化','内控']):
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                rel = os.path.relpath(fp, vault)
                print(f"  {rel} ({sz//1000}KB)")

# 读15号文解读
print(f"\n{'='*60}")
fp15 = r'D:\openclaw-workspace\knowledge\政策法规\国资委2026-15号文-容诚解读-中国注册会计师俱乐部20260327.md'
if os.path.exists(fp15):
    with open(fp15, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"📄 15号文解读 ({len(content)}字符):")
    print(content[:3000])
    if len(content) > 3000:
        print(f"\n... (剩余{len(content)-3000}字符)")
else:
    # 搜索
    for root, dirs, files in os.walk(base):
        for f in files:
            if '15号' in f:
                print(f"✅ 找到: {os.path.join(root, f)}")
