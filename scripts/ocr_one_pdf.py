# -*- coding: utf-8 -*-
"""
单个PDF的OCR处理脚本（由pdf_ocr_pipeline.py调用）
用法: paddleocr_python.exe ocr_one_pdf.py <pdf_path> <magazine_name> <output_dir>
"""
import sys, os, json, tempfile, time
sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 4:
    print("Usage: python ocr_one_pdf.py <pdf_path> <magazine> <output_dir>")
    sys.exit(1)

pdf_path = sys.argv[1]
magazine = sys.argv[2]
output_dir = sys.argv[3]
pdf_name = os.path.basename(pdf_path)

# 杂志→业务场景映射
MAG_SCENES = {
    "财政监督": ["财政监督", "绩效评价", "政策法规"],
    "四川注册会计师": ["事务所管理", "政策法规"],
    "中国内部审计": ["内部控制", "经济责任审计"],
    "中国审计": ["财政监督", "政策法规"],
}

scenes = MAG_SCENES.get(magazine, ["其他"])

from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False)

import fitz
doc = fitz.open(pdf_path)
pages_text = []
total_pages = len(doc)
print(f"总页数: {total_pages}")

for page_num in range(total_pages):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp.write(img_bytes)
        tmp_path = tmp.name
    
    try:
        result = ocr.ocr(tmp_path, cls=True)
        page_text = []
        if result and result[0]:
            confs = []
            for line in result[0]:
                page_text.append(line[1][0])
                confs.append(line[1][1])
        pages_text.append("\n".join(page_text))
    except Exception as e:
        pages_text.append(f"[OCR ERROR: {e}]")
    finally:
        os.unlink(tmp_path)
    
    if (page_num + 1) % 5 == 0:
        print(f"  进度: {page_num+1}/{total_pages}", flush=True)

doc.close()

full_text = "\n\n--- 分页分隔线 ---\n\n".join(pages_text)

# 保存结果
safe_name = pdf_name.replace('.pdf', '.md')
outfile = os.path.join(output_dir, magazine, safe_name)
os.makedirs(os.path.dirname(outfile), exist_ok=True)

with open(outfile, 'w', encoding='utf-8') as f:
    f.write("---\n")
    f.write(f'title: "{pdf_name}"\n')
    f.write(f'source: "{magazine}/{pdf_name}"\n')
    f.write(f'source_type: "杂志(扫描件)"\n')
    f.write(f'business_scenes: {json.dumps(scenes, ensure_ascii=False)}\n')
    f.write(f'pages: {total_pages}\n')
    f.write(f'ocr_date: "{time.strftime("%Y-%m-%d")}"\n')
    f.write('---\n\n')
    f.write(f'# {pdf_name}\n\n')
    f.write(full_text)

print(f"\nOCR完成: {outfile}")
print(f"字数: {len(full_text)}")
print(f"OCR_RESULT:{outfile}")
