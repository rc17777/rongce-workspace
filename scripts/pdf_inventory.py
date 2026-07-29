# -*- coding: utf-8 -*-
"""列出所有待OCR的PDF文件"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"E:\2026\审计方法&政策文件\杂志资料"
pdfs_by_mag = {}

for root, dirs, files in os.walk(BASE):
    for f in sorted(files):
        if f.endswith('.pdf') and not f.startswith('~$'):
            fp = os.path.join(root, f)
            rel = os.path.relpath(root, BASE)
            mag = rel.split(os.sep)[0] if os.sep in rel else rel
            if mag not in pdfs_by_mag:
                pdfs_by_mag[mag] = []
            pdfs_by_mag[mag].append({
                'file': f,
                'path': fp,
                'size_mb': os.path.getsize(fp) / 1e6,
                'issue': os.path.basename(root) if root != os.path.join(BASE, mag) else '整期'
            })

print("=== 待OCR的PDF清单 (共52篇) ===\n")
total_mb = 0
for mag, files in sorted(pdfs_by_mag.items()):
    mag_mb = sum(f['size_mb'] for f in files)
    total_mb += mag_mb
    print(f"【{mag}】{len(files)}篇 ({mag_mb:.0f} MB)")
    
    # 按期次分组
    by_issue = {}
    for f in files:
        iss = f['issue']
        if iss not in by_issue:
            by_issue[iss] = []
        by_issue[iss].append(f)
    
    for iss, fs in sorted(by_issue.items()):
        if iss == '整期':
            for f in fs:
                print(f"  ├ {f['file']} ({f['size_mb']:.0f}MB)")
        else:
            print(f"  ├ {iss}/ ({len(fs)}篇)")
            for f in fs:
                print(f"     └ {f['file']} ({f['size_mb']:.0f}MB)")
    print()

print(f"总计: {sum(len(v) for v in pdfs_by_mag.values())}篇 PDF, 约 {total_mb:.0f} MB")
print("\n说明: 这些是扫描件PDF(整期杂志)，需PaddleOCR识别后按文章切分再归类入库")
