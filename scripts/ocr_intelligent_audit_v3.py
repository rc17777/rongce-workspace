#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量OCR处理PDF文件 - 智能化审计文章 (使用Tesseract + PyMuPDF)
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# 确保输出编码正确
sys.stdout.reconfigure(encoding='utf-8')

# 导入库
try:
    import pytesseract
    import fitz  # PyMuPDF
    from PIL import Image
    print("✓ Tesseract 和 PyMuPDF 导入成功")
except ImportError as e:
    print(f"错误: 无法导入所需库: {e}")
    sys.exit(1)

# 配置Tesseract中文支持
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 配置
INPUT_DIR = r"E:\2026\审计方法\智能化"
OUTPUT_DIR = r"E:\2026\审计方法\智能化\ocr_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def pdf_page_to_image(doc, page_num, zoom=2):
    """将PDF页面转换为PIL Image"""
    page = doc[page_num]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

def extract_text_from_pdf(pdf_path, output_md_path):
    """从PDF提取文本并保存为Markdown"""
    print(f"\n处理: {os.path.basename(pdf_path)}")
    
    try:
        # 打开PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"  → 共 {total_pages} 页")
        
        # OCR识别
        full_text = []
        base_name = os.path.basename(pdf_path).replace('.pdf', '')
        full_text.append(f"# {base_name}\n")
        full_text.append(f"*OCR提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        full_text.append("---\n")
        
        for i in range(total_pages):
            print(f"  → 识别第 {i+1}/{total_pages} 页...")
            
            # 将页面转为图片
            img = pdf_page_to_image(doc, i, zoom=2)
            
            # OCR识别 (中文+英文)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            
            # 添加分页标记
            full_text.append(f"\n## 第 {i+1} 页\n")
            full_text.append(text)
            full_text.append("\n")
        
        # 关闭PDF
        doc.close()
        
        # 保存Markdown
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(full_text))
        
        print(f"  ✓ 已保存: {output_md_path}")
        return True
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("批量OCR处理 - 智能化审计文章 (Tesseract + PyMuPDF)")
    print("=" * 60)
    print(f"输入目录: {INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    # 获取所有PDF文件
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.pdf')]
    pdf_files.sort()
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    print("-" * 60)
    
    # 处理统计
    stats = {
        'total': len(pdf_files),
        'success': 0,
        'failed': 0,
        'start_time': time.time()
    }
    
    # 处理每个PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        
        # 生成输出文件名
        base_name = pdf_file.replace('.pdf', '')
        safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            safe_name = f"article_{i:02d}"
        
        output_md = os.path.join(OUTPUT_DIR, f"{safe_name}.md")
        
        print(f"\n[{i}/{len(pdf_files)}] ")
        
        if extract_text_from_pdf(pdf_path, output_md):
            stats['success'] += 1
        else:
            stats['failed'] += 1
        
        # 进度报告
        elapsed = time.time() - stats['start_time']
        avg_time = elapsed / i if i > 0 else 0
        remaining = avg_time * (len(pdf_files) - i)
        
        print(f"\n进度: {i}/{len(pdf_files)} | "
              f"成功: {stats['success']} | "
              f"失败: {stats['failed']} | "
              f"预计剩余: {remaining/60:.1f}分钟")
        print("-" * 60)
    
    # 最终报告
    total_time = time.time() - stats['start_time']
    print("\n" + "=" * 60)
    print("OCR处理完成!")
    print("=" * 60)
    print(f"总计: {stats['total']} 个文件")
    print(f"成功: {stats['success']} 个")
    print(f"失败: {stats['failed']} 个")
    print(f"总用时: {total_time/60:.1f} 分钟")
    print("=" * 60)
    
    # 保存处理报告
    report_path = os.path.join(OUTPUT_DIR, "ocr_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': stats,
            'files': pdf_files,
            'output_dir': OUTPUT_DIR,
            'completed_at': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_path}")
    print(f"OCR结果目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
