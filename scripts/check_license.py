#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查ABBYY许可证文件"""
import os

abbyy_dir = r"C:\Program Files (x86)\ABBYY FineReader 15"
lic_files = []
for f in os.listdir(abbyy_dir):
    if f.endswith('.licp') or f.endswith('.lic'):
        lic_files.append(f)

print("许可证文件:")
for lf in lic_files:
    fp = os.path.join(abbyy_dir, lf)
    size = os.path.getsize(fp)
    print(f"  {lf} ({size} bytes)")
