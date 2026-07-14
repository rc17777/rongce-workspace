#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投标文件元数据分析 + 深度解析"""
import sys, os, time, struct, zipfile, re, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

CST = timezone(timedelta(hours=8))

BASE = Path(r"C:\Users\scrccpa\Desktop\校服\2025年校服采购\校服\2025年\投标文件\投标文件")

def get_file_metadata(filepath):
    """Extract comprehensive file metadata"""
    stat = filepath.stat()
    info = {
        'path': str(filepath.relative_to(BASE)),
        'size_mb': stat.st_size / 1024 / 1024,
        'created': datetime.fromtimestamp(stat.st_ctime, CST).strftime('%Y-%m-%d %H:%M:%S'),
        'modified': datetime.fromtimestamp(stat.st_mtime, CST).strftime('%Y-%m-%d %H:%M:%S'),
        'accessed': datetime.fromtimestamp(stat.st_atime, CST).strftime('%Y-%m-%d %H:%M:%S'),
        'md5': None,
        'doc_author': None,
        'doc_created': None,
        'doc_modified': None,
        'doc_last_author': None,
        'doc_revision': None,
        'doc_company': None,
        'doc_title': None,
        'doc_app': None,
    }
    
    # MD5
    with open(filepath, 'rb') as f:
        info['md5'] = hashlib.md5(f.read(1024*1024)).hexdigest()[:16]  # First 1MB
    
    # DOCX metadata (ZIP-based, including .doc pretending to be docx)
    if filepath.suffix.lower() in ['.docx', '.doc']:
        try:
            if filepath.read_bytes()[:2] == b'PK':  # ZIP magic
                with zipfile.ZipFile(filepath, 'r') as z:
                    # Core properties
                    if 'docProps/core.xml' in z.namelist():
                        xml = z.read('docProps/core.xml').decode('utf-8', errors='ignore')
                        for tag, key in [
                            (r'<dc:creator>(.*?)</dc:creator>', 'doc_author'),
                            (r'<dc:title>(.*?)</dc:title>', 'doc_title'),
                            (r'<dcterms:created[^>]*>(.*?)</dcterms:created>', 'doc_created'),
                            (r'<dcterms:modified[^>]*>(.*?)</dcterms:modified>', 'doc_modified'),
                            (r'<cp:lastModifiedBy>(.*?)</cp:lastModifiedBy>', 'doc_last_author'),
                            (r'<cp:revision>(.*?)</cp:revision>', 'doc_revision'),
                        ]:
                            m = re.search(tag, xml)
                            if m:
                                info[key] = m.group(1)
                    
                    # App properties
                    if 'docProps/app.xml' in z.namelist():
                        xml = z.read('docProps/app.xml').decode('utf-8', errors='ignore')
                        for tag, key in [
                            (r'<Application>(.*?)</Application>', 'doc_app'),
                            (r'<Company>(.*?)</Company>', 'doc_company'),
                        ]:
                            m = re.search(tag, xml)
                            if m:
                                info[key] = m.group(1)
        except:
            pass
    
    return info

# Collect all bid files
all_files = list(BASE.rglob("*.*"))
metas = []
for f in all_files:
    if f.is_file() and f.suffix.lower() in ['.docx', '.doc', '.pdf']:
        metas.append(get_file_metadata(f))

# Group by company
companies = {}
for m in metas:
    parts = Path(m['path']).parts
    company = parts[0] if parts else 'unknown'
    if company not in companies:
        companies[company] = []
    companies[company].append(m)

print("=" * 90)
print("一、投标文件元数据分析")
print("=" * 90)

for company in sorted(companies.keys()):
    files = companies[company]
    print(f"\n{'─'*80}")
    print(f"📁 {company}")
    print(f"{'─'*80}")
    for f in sorted(files, key=lambda x: x['size_mb'], reverse=True):
        print(f"\n  文件: {Path(f['path']).name}")
        print(f"  大小: {f['size_mb']:.1f} MB")
        print(f"  文件系统创建时间: {f['created']}")
        print(f"  文件系统修改时间: {f['modified']}")
        
        if f['doc_author']:
            print(f"  📝 文档作者: {f['doc_author']}")
        if f['doc_last_author']:
            print(f"  📝 最后修改者: {f['doc_last_author']}")
        if f['doc_created']:
            print(f"  📅 文档创建时间: {f['doc_created']}")
        if f['doc_modified']:
            print(f"  📅 文档修改时间: {f['doc_modified']}")
        if f['doc_revision']:
            print(f"  🔢 修订版本号: {f['doc_revision']}")
        if f['doc_company']:
            print(f"  🏢 文档公司: {f['doc_company']}")
        if f['doc_title']:
            print(f"  📋 文档标题: {f['doc_title']}")
        if f['doc_app']:
            print(f"  💻 创建应用: {f['doc_app']}")

# Cross-company metadata analysis
print(f"\n\n{'='*90}")
print("二、跨公司元数据交叉比对")
print("="*90)

# Check for same author across companies
all_authors = {}
for m in metas:
    if m['doc_author']:
        if m['doc_author'] not in all_authors:
            all_authors[m['doc_author']] = []
        all_authors[m['doc_author']].append(m['path'])

print(f"\n文档作者汇总:")
for author, paths in all_authors.items():
    companies_set = set(Path(p).parts[0] for p in paths)
    print(f"  作者 [{author}]: 出现在 {len(companies_set)} 家公司 - {companies_set}")
    if len(companies_set) > 1:
        print(f"    ⚠️ 同一作者出现在多家公司！")

# Check for same application
all_apps = {}
for m in metas:
    if m['doc_app']:
        if m['doc_app'] not in all_apps:
            all_apps[m['doc_app']] = []
        all_apps[m['doc_app']].append(Path(m['path']).parts[0])

print(f"\n创建应用汇总:")
for app, comps in all_apps.items():
    unique_comps = set(comps)
    print(f"  {app}: {unique_comps}")

# Check creation date clustering
print(f"\n文件创建时间线:")
timeline = []
for m in metas:
    if m['doc_created']:
        timeline.append((m['doc_created'], Path(m['path']).parts[0], Path(m['path']).name))
    timeline.append((m['modified'], Path(m['path']).parts[0], Path(m['path']).name + ' [FS修改]'))

timeline.sort()
for dt, company, fname in timeline:
    print(f"  {dt} | {company} | {fname[:60]}")

# Check for OLE2 .doc files
print(f"\n\n{'='*90}")
print("三、.doc 文件格式验证（弘博士、顺华）")
print("="*90)

doc_files = list(BASE.rglob("*.doc"))
for d in doc_files:
    magic = d.read_bytes()[:8]
    is_docx = magic[:2] == b'PK'
    is_ole = magic[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    fmt = "DOCX(ZIP伪装)" if is_docx else "OLE2真.doc" if is_ole else "未知"
    print(f"  {d.relative_to(BASE)}")
    print(f"    格式: {fmt} | 大小: {d.stat().st_size/1024/1024:.1f}MB")
    if is_ole:
        print(f"    ⚠️ 真.doc格式无法程序化提取元数据")

print("\nDone!")
