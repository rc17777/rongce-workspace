"""
批量OCR 41个PDF → Markdown
用法: python batch_ocr_41pdfs.py
依赖: conda env paddleocr (Python 3.11, pymupdf, paddleocr)
"""
import sys, os, io, json, time, re
sys.stdout.reconfigure(encoding='utf-8')

import fitz  # pymupdf
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np

# 配置
SOURCE_DIRS = [
    (r'E:\2026\审计方法&政策文件\1中国审计\7期', '1中国审计_7期'),
    (r'E:\2026\审计方法&政策文件\2经济责任审计\6期', '2经济责任审计_6期'),
]
OUTPUT_BASE = r'E:\2026\审计方法&政策文件\_ocr_output'
MANIFEST_PATH = os.path.join(OUTPUT_BASE, '_manifest.json')

# 初始化 PaddleOCR
print("初始化 PaddleOCR...")
ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

def ocr_page(img_bytes):
    """OCR单页图片，返回文本"""
    img = Image.open(io.BytesIO(img_bytes))
    img_array = np.array(img)
    result = ocr.ocr(img_array, cls=True)
    if not result or not result[0]:
        return ""
    lines = []
    for line in result[0]:
        text = line[1][0]
        confidence = line[1][1]
        if confidence > 0.5:  # 过滤低置信度
            lines.append(text)
    return "\n".join(lines)

def process_pdf(pdf_path, output_dir, label):
    """处理单个PDF → Markdown"""
    doc = fitz.open(pdf_path)
    pages = doc.page_count
    
    md_lines = []
    total_imgs = 0
    
    for page_num in range(pages):
        page = doc[page_num]
        # 渲染为图片 (300 DPI 保证质量)
        mat = fitz.Matrix(300/72, 300/72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        
        # OCR
        text = ocr_page(img_bytes)
        if text.strip():
            md_lines.append(f"\n## 第{page_num+1}页\n\n{text}")
        else:
            md_lines.append(f"\n## 第{page_num+1}页\n\n*(OCR未识别到文字)*")
        
        total_imgs += 1
        if (page_num + 1) % 3 == 0:
            print(f"  [{label}] 进度: {page_num+1}/{pages}")
    
    doc.close()
    
    # 生成Markdown
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    md_content = f"# {filename}\n\n> 来源: {label} | 页数: {pages} | OCR引擎: PaddleOCR\n\n" + "\n".join(md_lines)
    
    out_path = os.path.join(output_dir, f"{filename}.md")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return {
        'filename': filename,
        'pages': pages,
        'chars': len(md_content),
        'path': out_path,
        'label': label
    }

def main():
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    
    all_results = {}
    stats = {'total_pdfs': 0, 'total_pages': 0, 'total_chars': 0, 'failed': 0}
    
    for src_dir, label in SOURCE_DIRS:
        out_dir = os.path.join(OUTPUT_BASE, label)
        os.makedirs(out_dir, exist_ok=True)
        
        pdfs = sorted([f for f in os.listdir(src_dir) if f.lower().endswith('.pdf')])
        print(f"\n{'='*60}")
        print(f"[{label}] 共 {len(pdfs)} 个PDF")
        print(f"{'='*60}")
        
        results = []
        for i, pdf_name in enumerate(pdfs, 1):
            pdf_path = os.path.join(src_dir, pdf_name)
            item_label = f"{label}[{i}/{len(pdfs)}]"
            print(f"\n处理: {item_label} - {pdf_name}")
            
            try:
                t0 = time.time()
                result = process_pdf(pdf_path, out_dir, item_label)
                elapsed = time.time() - t0
                stats['total_pdfs'] += 1
                stats['total_pages'] += result['pages']
                stats['total_chars'] += result['chars']
                results.append(result)
                print(f"  ✅ {result['pages']}页 {result['chars']}字 | 耗时 {elapsed:.0f}s")
            except Exception as e:
                print(f"  ❌ 失败: {e}")
                stats['failed'] += 1
                results.append({
                    'filename': pdf_name,
                    'pages': 0,
                    'chars': 0,
                    'error': str(e),
                    'label': item_label
                })
        
        all_results[label] = results
    
    # 保存清单
    manifest = {
        'stats': stats,
        'results': all_results,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"完成! 总计: {stats['total_pdfs']}PDF {stats['total_pages']}页 {stats['total_chars']}字 失败{stats['failed']}")
    print(f"输出: {OUTPUT_BASE}")
    print(f"清单: {MANIFEST_PATH}")

if __name__ == '__main__':
    main()
