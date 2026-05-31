#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探索校服目录完整结构"""
import os
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\scrccpa\Desktop\校服"

def show_tree(path, indent=0, max_depth=4):
    if indent > max_depth * 2:
        return
    try:
        items = sorted(path.iterdir())
        for item in items:
            prefix = "  " * indent
            if item.is_dir():
                print(f"{prefix}[DIR] {item.name}")
                show_tree(item, indent + 1, max_depth)
            else:
                size = item.stat().st_size
                print(f"{prefix}{item.name}  ({size/1024/1024:.1f} MB)")
    except PermissionError:
        print(f"{'  ' * indent}[DENIED]")

print("=" * 60)
print("校服采购项目 - 完整目录结构")
print("=" * 60)
show_tree(Path(BASE), max_depth=6)

# Find all docx, doc, pdf
print("\n" + "=" * 60)
print("所有文件统计")
print("=" * 60)
all_docx = list(Path(BASE).rglob("*.docx"))
all_doc = list(Path(BASE).rglob("*.doc"))
all_pdf = list(Path(BASE).rglob("*.pdf"))

print(f".docx: {len(all_docx)} files, total {sum(d.stat().st_size for d in all_docx)/1024/1024:.0f} MB")
for d in all_docx:
    print(f"  {d.relative_to(BASE)}")

print(f"\n.doc: {len(all_doc)} files, total {sum(d.stat().st_size for d in all_doc)/1024/1024:.0f} MB")
for d in all_doc:
    print(f"  {d.relative_to(BASE)}")

print(f"\n.pdf: {len(all_pdf)} files")
for d in all_pdf:
    print(f"  {d.relative_to(BASE)}")
