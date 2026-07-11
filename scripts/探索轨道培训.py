#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探索轨道培训目录的原始文件"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

d = r'C:\Users\scrccpa\Desktop\轨道培训'
for f in os.listdir(d):
    fp = os.path.join(d, f)
    sz = os.path.getsize(fp)
    ext = os.path.splitext(f)[1]
    name = f  # OS shows correct Chinese names
    print(f"{name:60s} {sz:>8,}B {ext}")
    
# 读那本PDF
pdf_path = r'C:\Users\scrccpa\Desktop\轨道培训\SW-2026-1196 关于印发成都市市属国有企业违规经营投资责任追究实施办法的通知.pdf'
if os.path.exists(pdf_path):
    print(f"\n✅ 找到PDF: {os.path.basename(pdf_path)}")
    import shutil
    # copy to workspace
    dst = r'D:\openclaw-workspace\轨道培训\SW-2026-1196_成都市违规经营投资责任追究实施办法.pdf'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(pdf_path, dst)
    print(f"已复制到: {dst}")
else:
    # 找所有PDF
    print("\n搜索所有PDF:")
    for f in os.listdir(d):
        if f.endswith('.pdf'):
            fp = os.path.join(d, f)
            print(f"  {f} ({os.path.getsize(fp)//1000}KB)")

# 找46号令相关内容
print(f"\n搜索含'46号'的文件:")
for f in os.listdir(d):
    if '46' in f or '追责' in f or '追究' in f:
        fp = os.path.join(d, f)
        print(f"  {f} ({os.path.getsize(fp)//1000}KB)")

# 看看有没有1号文2号文的原文
print(f"\n搜索其他原文文件:")
for f in os.listdir(d):
    if '1号' in f or '2号' in f or '15号' in f or '财务数智' in f or '穿透' in f:
        fp = os.path.join(d, f)
        print(f"  {f} ({os.path.getsize(fp)//1000}KB)")

# 再看其他桌面目录
print(f"\n搜索桌面其他目录:")
desktop = r'C:\Users\scrccpa\Desktop'
for item in os.listdir(desktop):
    fp = os.path.join(desktop, item)
    if os.path.isdir(fp) and item not in ['轨道培训']:
        # 只看深度2
        for f2 in os.listdir(fp):
            if any(kw in f2 for kw in ['国资委','1号文','2号文','15号','46号','穿透']):
                print(f"  {item}/{f2}")
