#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E05 — 投标文件元数据同源检测
═══════════════════════════════
核查逻辑：多家投标人的投标文件创建/修改时间接近、最后保存者相同 → 同一台电脑制作 → 围标

数据源：投标文件电子版（.docx/.pdf）

输出：
  同源分组列表 + 时间线比对

难度：⭐ | 方法：python-docx提取core.xml

前提：pip install python-docx (如处理.docx)
     .pdf元数据通过PyPDF2提取（可选）
"""

import sys
import os
import csv
import hashlib
from datetime import datetime
from collections import defaultdict

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 尝试导入可选依赖
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    print("⚠️ python-docx 未安装，将跳过.docx元数据提取。安装: pip install python-docx")

try:
    from PyPDF2 import PdfReader
    HAS_PDF = True
except ImportError:
    from pypdf import PdfReader
    HAS_PDF = True


def extract_docx_metadata(filepath):
    """提取.docx文件的元数据"""
    meta = {
        'filename': os.path.basename(filepath),
        'path': filepath,
        'format': 'docx',
        'created': None,
        'modified': None,
        'last_modified_by': None,
        'revision': None,
        'author': None,
        'title': None,
        'company': None,
        'error': None,
        'md5': None,
    }
    try:
        # 计算文件哈希
        with open(filepath, 'rb') as f:
            meta['md5'] = hashlib.md5(f.read()).hexdigest()[:12]

        doc = Document(filepath)
        core = doc.core_properties
        meta['created'] = str(core.created) if core.created else None
        meta['modified'] = str(core.modified) if core.modified else None
        meta['last_modified_by'] = core.last_modified_by or None
        meta['revision'] = str(core.revision) if core.revision else None
        meta['author'] = core.author or None
        meta['title'] = core.title or None
        meta['company'] = core.last_modified_by or None  # 有时company存在此字段
    except Exception as e:
        meta['error'] = str(e)[:100]

    return meta


def extract_pdf_metadata(filepath):
    """提取.pdf文件的元数据"""
    meta = {
        'filename': os.path.basename(filepath),
        'path': filepath,
        'format': 'pdf',
        'created': None,
        'modified': None,
        'last_modified_by': None,
        'author': None,
        'title': None,
        'producer': None,
        'creator': None,
        'error': None,
        'md5': None,
    }
    try:
        with open(filepath, 'rb') as f:
            meta['md5'] = hashlib.md5(f.read()).hexdigest()[:12]

        reader = PdfReader(filepath)
        info = reader.metadata or {}
        meta['author'] = str(info.get('/Author', '')) if info.get('/Author') else None
        meta['title'] = str(info.get('/Title', '')) if info.get('/Title') else None
        meta['producer'] = str(info.get('/Producer', '')) if info.get('/Producer') else None
        meta['creator'] = str(info.get('/Creator', '')) if info.get('/Creator') else None
        meta['created'] = str(info.get('/CreationDate', '')) if info.get('/CreationDate') else None
        meta['modified'] = str(info.get('/ModDate', '')) if info.get('/ModDate') else None
        meta['last_modified_by'] = meta['creator'] or None
    except Exception as e:
        meta['error'] = str(e)[:100]

    return meta


def extract_metadata(filepath):
    """自动识别格式并提取元数据"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.docx':
        if not HAS_DOCX:
            return None  # 跳过，不提取
        return extract_docx_metadata(filepath)
    elif ext == '.pdf':
        return extract_pdf_metadata(filepath)
    return None


def is_same_origin(m1, m2):
    """判断两份文件是否可能来自同一来源"""
    score = 0
    reasons = []

    # 1. 最后保存者相同
    if m1.get('last_modified_by') and m2.get('last_modified_by'):
        if m1['last_modified_by'] == m2['last_modified_by']:
            score += 3
            reasons.append(f"最后保存者相同: {m1['last_modified_by']}")

    # 2. 创建者/作者相同
    if m1.get('author') and m2.get('author'):
        if m1['author'] == m2['author']:
            score += 2
            reasons.append(f"作者相同: {m1['author']}")

    # 3. 修改时间接近（5分钟以内）
    if m1.get('modified') and m2.get('modified'):
        try:
            t1 = datetime.fromisoformat(m1['modified'].replace('Z', '+00:00').split('+')[0])
            t2 = datetime.fromisoformat(m2['modified'].replace('Z', '+00:00').split('+')[0])
            diff_sec = abs((t1 - t2).total_seconds())
            if diff_sec < 300:
                score += 2
                reasons.append(f"修改时间差 {diff_sec:.0f} 秒")
            elif diff_sec < 3600:
                score += 1
                reasons.append(f"修改时间差 {diff_sec/60:.0f} 分钟")
        except (ValueError, TypeError):
            pass

    # 4. PDF Producer相同（同一扫描仪/软件）
    if m1.get('producer') and m2.get('producer'):
        if m1['producer'] == m2['producer']:
            score += 2
            reasons.append(f"Producer相同: {m1['producer']}")

    # 5. 创建时间在2小时内
    if m1.get('created') and m2.get('created'):
        try:
            t1 = datetime.fromisoformat(m1['created'].replace('Z', '+00:00').split('+')[0])
            t2 = datetime.fromisoformat(m2['created'].replace('Z', '+00:00').split('+')[0])
            diff_sec = abs((t1 - t2).total_seconds())
            if diff_sec < 7200:
                score += 1
                reasons.append(f"创建时间差 {diff_sec/60:.0f} 分钟")
        except (ValueError, TypeError):
            pass

    # 6. MD5完全相同
    if m1.get('md5') and m2.get('md5'):
        if m1['md5'] == m2['md5']:
            score += 5
            reasons.append("⚠️ 文件MD5完全相同（标书内容一致）")

    return score >= 2, score, reasons


def main(input_dir, output_path=None):
    """
    Args:
        input_dir: 投标文件存放目录（含多家投标人的.docx/.pdf文件）
        output_path: 输出CSV路径
    """
    print(f"E05 投标文件元数据同源检测")
    print(f"═" * 50)
    print(f"扫描目录: {input_dir}")

    # 扫描文件
    files = []
    for f in sorted(os.listdir(input_dir)):
        fp = os.path.join(input_dir, f)
        if os.path.isfile(fp) and f.lower().endswith(('.docx', '.pdf')):
            files.append(fp)

    if not files:
        print("❌ 未找到.docx或.pdf文件")
        return []

    print(f"[1/2] 找到 {len(files)} 个文件，提取元数据...")

    # 提取元数据
    metadata_list = []
    for fp in files:
        meta = extract_metadata(fp)
        if meta:
            metadata_list.append(meta)
            err = f" ⚠️ {meta['error']}" if meta.get('error') else ''
            print(f"  {meta['filename']} | 作者:{meta.get('author','?')} | 修改:{meta.get('modified','?')} | 保存者:{meta.get('last_modified_by','?')}{err}")
        else:
            print(f"  {os.path.basename(fp)} | 跳过（不支持或缺少依赖）")

    # 交叉比对
    print(f"\n[2/2] 交叉比对同源信号...")
    anomalies = []
    n = len(metadata_list)
    groups = {}  # pair key → score

    for i in range(n):
        for j in range(i + 1, n):
            m1, m2 = metadata_list[i], metadata_list[j]
            same, score, reasons = is_same_origin(m1, m2)
            if same:
                pair_key = f"{m1['filename']} ↔ {m2['filename']}"
                groups[pair_key] = (score, reasons)
                print(f"  🔴 {pair_key} (得分:{score}) {'; '.join(reasons[:3])}")
                anomalies.append({
                    '投标人A': m1['filename'],
                    '投标人B': m2['filename'],
                    '同源得分': score,
                    '判断依据': '; '.join(reasons),
                    'A_作者': m1.get('author', ''),
                    'A_最后保存者': m1.get('last_modified_by', ''),
                    'A_修改时间': m1.get('modified', ''),
                    'B_作者': m2.get('author', ''),
                    'B_最后保存者': m2.get('last_modified_by', ''),
                    'B_修改时间': m2.get('modified', ''),
                    '建议动作': '围标嫌疑：建议调取投标电子文件原始设备信息（IP/MAC/CPU/硬盘SN）做L18级检测' if score >= 5 else '同源信号：建议进一步核实投标人是否独立编制投标文件'
                })

    # 输出
    if not output_path:
        output_path = 'anomalies_e05.csv'

    if anomalies:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=anomalies[0].keys())
            writer.writeheader()
            writer.writerows(anomalies)
    else:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write('未发现元数据同源信号\n')

    # 汇总
    print(f"\n═" * 50)
    print(f"检测完成:")
    print(f"  扫描文件: {len(files)}")
    print(f"  成功提取元数据: {len(metadata_list)}")
    print(f"  发现同源信号: {len(anomalies)} 对")
    print(f"  结果保存至: {output_path}")

    # 输出元数据明细表
    detail_path = output_path.replace('.csv', '_detail.csv')
    if metadata_list:
        fieldnames = ['filename', 'format', 'author', 'last_modified_by', 'created', 'modified', 'producer', 'creator', 'md5', 'error']
        with open(detail_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(metadata_list)
        print(f"  元数据明细: {detail_path}")

    return anomalies


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='E05 投标文件元数据同源检测')
    parser.add_argument('dir', help='投标文件存放目录')
    parser.add_argument('-o', '--output', default='anomalies_e05.csv', help='输出文件路径')
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"❌ 目录不存在: {args.dir}")
        print(f"用法: python e05_bid_metadata_homology.py 投标文件目录/")
        sys.exit(1)

    main(args.dir, args.output)
