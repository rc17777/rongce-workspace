# -*- coding: utf-8 -*-
"""扫描杂志资料目录，了解文件结构、内容质量和类型"""
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

BASE = r"E:\2026\审计方法&政策文件\杂志资料"

def scan():
    # 1. 目录结构
    mags = sorted(os.listdir(BASE))
    print(f"=== 杂志资料总览 ===\n")
    
    for mag in mags:
        mag_path = os.path.join(BASE, mag)
        if not os.path.isdir(mag_path):
            continue
        
        all_files = []
        for root, dirs, files in os.walk(mag_path):
            for f in files:
                fp = os.path.join(root, f)
                all_files.append(fp)
        
        docx_count = sum(1 for f in all_files if f.endswith('.docx'))
        pdf_count = sum(1 for f in all_files if f.endswith('.pdf'))
        total_size = sum(os.path.getsize(f) for f in all_files) / 1e6
        
        print(f"\n【{mag}】{len(all_files)}篇, docx:{docx_count} pdf:{pdf_count}, {total_size:.0f} MB")
        
        # 列出子目录（期次）
        subs = sorted([d for d in os.listdir(mag_path) if os.path.isdir(os.path.join(mag_path, d))])
        for s in subs:
            sp = os.path.join(mag_path, s)
            cnt = len([f for f in os.listdir(sp) if os.path.isfile(os.path.join(sp, f))])
            print(f"  ├ {s} → {cnt}篇")
        
        # 根目录下的文件
        root_files = [f for f in os.listdir(mag_path) if os.path.isfile(os.path.join(mag_path, f))]
        for rf in sorted(root_files):
            sz = os.path.getsize(os.path.join(mag_path, rf)) / 1e6
            print(f"  ├ {rf} [{sz:.1f}MB]")
    
    # 2. 抽样检查docx内容
    print("\n\n=== docx内容抽样 ===")
    sample_docx = None
    for root, dirs, files in os.walk(BASE):
        for f in sorted(files):
            if f.endswith('.docx'):
                sample_docx = os.path.join(root, f)
                break
        if sample_docx:
            break
    
    if sample_docx:
        try:
            import zipfile, re
            z = zipfile.ZipFile(sample_docx)
            xml = z.read('word/document.xml').decode('utf-8')
            text = re.sub(r'<[^>]+>', '', xml)
            text = re.sub(r'\s+', ' ', text).strip()
            print(f"抽样: {os.path.relpath(sample_docx, BASE)}")
            print(f"字数: {len(text)}")
            print(f"前200字: {text[:200]}")
        except Exception as e:
            print(f"docx读取失败: {e}")
    
    # 3. 抽样检查PDF
    print("\n\n=== PDF抽样检查 ===")
    for root, dirs, files in os.walk(BASE):
        for f in sorted(files):
            if f.endswith('.pdf'):
                pdf_path = os.path.join(root, f)
                from pdfminer.high_level import extract_text
                text = extract_text(pdf_path, maxpages=2)
                if text.strip():
                    print(f"【可提取文本】{os.path.relpath(pdf_path, BASE)}")
                    print(f"  文字长度: {len(text.strip())}")
                    print(f"  前200字: {text.strip()[:200]}")
                else:
                    print(f"【需OCR】{os.path.relpath(pdf_path, BASE)}")
                break

if __name__ == '__main__':
    scan()
