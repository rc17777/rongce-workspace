#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理审计案例库与OCR版的重复文件"""
import sys, os, shutil
sys.stdout.reconfigure(encoding='utf-8')

VAULT = r'C:\Users\scrccpa\Documents\Obsidian Vault'
OLD = os.path.join(VAULT, '审计案例库')
OCR = os.path.join(VAULT, '审计案例库-OCR')
BACKUP = os.path.join(VAULT, '_已清理重复')

# 收集OCR版文件名（去重）
ocr_files = set()
for root, dirs, files in os.walk(OCR):
    for f in files:
        if f.endswith('.md') and not f.startswith('00-') and f != '00-索引.md':
            ocr_files.add(f)

# 收集旧案例库文件名
old_files = set()
old_by_dir = {}
for root, dirs, files in os.walk(OLD):
    for f in files:
        if f.endswith('.md') and not f.startswith('00-') and f != '00-索引.md':
            old_files.add(f)
            rel = os.path.relpath(root, OLD)
            old_by_dir.setdefault(rel, []).append(f)

# 找出重复文件
duplicates = old_files & ocr_files
only_in_old = old_files - ocr_files

print(f'OCR版: {len(ocr_files)}个文件')
print(f'旧案例库: {len(old_files)}个文件')
print(f'重复文件: {len(duplicates)}个（将在旧案例库中删除）')
print(f'仅在旧案例库中的文件: {len(only_in_old)}个（保留）')
print()

# 显示重复文件分布
if duplicates:
    dup_by_dir = {}
    for d, files in old_by_dir.items():
        for f in files:
            if f in duplicates:
                dup_by_dir.setdefault(d, []).append(f)
    print('重复文件分布（旧案例库中各场景的重复数）:')
    for d in sorted(dup_by_dir.keys()):
        print(f'  {d}/{len(dup_by_dir[d])}篇重复')
    print()

# 确认清理
# 先把重复文件移到备份目录
if duplicates:
    for f in sorted(duplicates):
        # 找到文件在旧案例库中的位置（可能在子目录里）
        found = False
        for root, dirs, files in os.walk(OLD):
            if f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(root, OLD)
                # 构建备份路径
                dst_dir = os.path.join(BACKUP, '审计案例库', rel)
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, f)
                shutil.move(src, dst)
                found = True
                break
        if found:
            print(f'  已移动: {f}')
    
    # 删除空目录
    for root, dirs, files in os.walk(OLD, topdown=False):
        if root == OLD:
            continue
        if not os.listdir(root):
            os.rmdir(root)
            print(f'  已删除空目录: {os.path.relpath(root, OLD)}')
    
    print(f'\n清理完成！')
    print(f'  从旧案例库移除了 {len(duplicates)} 个重复文件到 _已清理重复/')
    print(f'  旧案例库保留 {len(only_in_old)} 个独立文件（OCR版没有的）')
else:
    print('没有找到重复文件')
