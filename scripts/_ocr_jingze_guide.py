# -*- coding: utf-8 -*-
"""OCR处理：第3204号内部审计实务指南——经济责任审计"""
import sys, os, time, tempfile, json
sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = r"C:\Users\scrccpa\Desktop\审计方案以及案例\第3204 号内部审计实务指南——经济责任审计.pdf"
OUT_PATH = r"C:\Users\scrccpa\.openclaw\workspace\output\ocr\第3204号内部审计实务指南——经济责任审计.md"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

from paddleocr import PaddleOCR
import fitz

ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False)
doc = fitz.open(PDF_PATH)
total = len(doc)
print(f"PDF: {os.path.basename(PDF_PATH)}")
print(f"总页数: {total}")
print(f"开始OCR...")

pages_text = []
t_start = time.time()

for i in range(total):
    page = doc[i]
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(img_bytes)
        tmp = f.name
    
    try:
        result = ocr.ocr(tmp, cls=True)
        lines = []
        if result and result[0]:
            for line in result[0]:
                lines.append(line[1][0])
        pages_text.append("\n".join(lines))
    except Exception as e:
        pages_text.append(f"[OCR错误 第{i+1}页: {e}]")
    finally:
        os.unlink(tmp)
    
    elapsed = time.time() - t_start
    avg = elapsed / (i + 1)
    remaining = avg * (total - i - 1)
    if (i + 1) % 10 == 0 or i == total - 1:
        print(f"  进度: {i+1}/{total} ({elapsed:.0f}s, 预计剩余{remaining:.0f}s)", flush=True)

doc.close()

full_text = "\n\n---\n\n".join(pages_text)

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write("---\n")
    f.write(f'title: "第3204号内部审计实务指南——经济责任审计"\n')
    f.write(f'type: "法规指引"\n')
    f.write(f'source: "中国内部审计协会"\n')
    f.write(f'biz_lines: ["经济责任审计"]\n')
    f.write(f'pages: {total}\n')
    f.write(f'ocr_date: "{time.strftime("%Y-%m-%d")}"\n')
    f.write(f'ocr_engine: "PaddleOCR"\n')
    f.write('tags: ["内部审计", "经济责任审计", "实务指南", "第3204号"]\n')
    f.write('---\n\n')
    f.write(f'# 第3204号内部审计实务指南——经济责任审计\n\n')
    f.write(f'*中国内部审计协会发布 | {total}页 | OCR识别时间: {time.strftime("%Y-%m-%d %H:%M")}*\n\n')
    f.write(full_text)

total_time = time.time() - t_start
char_count = sum(len(t) for t in pages_text)
print(f"\n✅ OCR完成!")
print(f"输出: {OUT_PATH}")
print(f"总页数: {total}")
print(f"总字符: {char_count}")
print(f"耗时: {total_time:.0f}s ({total_time/60:.1f}min)")
print(f"平均: {total_time/total:.1f}s/页")
print(f"OCR_DONE:{OUT_PATH}")
