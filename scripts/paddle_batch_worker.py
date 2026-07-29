# encoding: utf-8
"""
PaddleOCR 批量处理器 — 由 hybrid_ocr_pipeline.py 调用
=====================================================
用途: 加载一次PaddleOCR，对PDF所有页做OCR，返回JSON结果
用法: paddle_python.exe paddle_batch_worker.py <pdf_path> <output_json_path>
"""
import sys, os, json, time, tempfile

sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 2:
    print('Usage: paddle_batch_worker.py <config_json_path>')
    sys.exit(1)

# 从JSON配置文件读取路径（绕过命令行编码问题）
with open(sys.argv[1], encoding='utf-8') as f:
    config = json.load(f)
pdf_path = config['pdf_path']
output_json = config['output_json']
DPI = 200

print(f'[PaddleWorker] 加载 PaddleOCR...', flush=True)
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False)

print(f'[PaddleWorker] 加载 PyMuPDF...', flush=True)
import fitz

print(f'[PaddleWorker] 打开 PDF: {os.path.basename(pdf_path)}', flush=True)
doc = fitz.open(pdf_path)
total_pages = len(doc)

results = []
t_start = time.time()

for page_num in range(total_pages):
    t_page = time.time()

    try:
        # 渲染页面为PNG
        page = doc[page_num]
        mat = fitz.Matrix(DPI / 72, DPI / 72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes('png')

        # 写临时文件（PaddleOCR需要文件路径）
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.write(img_bytes)
        tmp.close()

        # OCR识别
        ocr_result = ocr.ocr(tmp.name, cls=True)

        # 清理临时文件
        try:
            os.unlink(tmp.name)
        except:
            pass

        # 提取文本和置信度
        lines = []
        confs = []
        if ocr_result and ocr_result[0]:
            for line in ocr_result[0]:
                lines.append(line[1][0])
                confs.append(line[1][1])

        text = '\n'.join(lines)
        avg_conf = round(sum(confs) / len(confs), 4) if confs else 0.0

        results.append({
            'page': page_num,
            'text': text,
            'confidence': avg_conf,
            'chars': len(text),
            'time': round(time.time() - t_page, 2),
        })

    except Exception as e:
        results.append({
            'page': page_num,
            'text': '',
            'confidence': 0.0,
            'chars': 0,
            'error': str(e),
            'time': round(time.time() - t_page, 2),
        })

    # 进度报告
    elapsed = time.time() - t_start
    if (page_num + 1) % 10 == 0 or page_num == 0:
        rate = (page_num + 1) / elapsed if elapsed > 0 else 0
        eta = (total_pages - page_num - 1) / rate if rate > 0 else 0
        print(f'[PaddleWorker] 进度: {page_num+1}/{total_pages} '
              f'({rate:.1f}页/秒, ETA {eta:.0f}s)', flush=True)

doc.close()

total_time = time.time() - t_start
avg_conf = sum(r['confidence'] for r in results) / len(results) if results else 0
total_chars = sum(r['chars'] for r in results)
errors = sum(1 for r in results if 'error' in r)

output = {
    'pdf': pdf_path,
    'total_pages': total_pages,
    'total_chars': total_chars,
    'avg_confidence': round(avg_conf, 4),
    'errors': errors,
    'total_time': round(total_time, 1),
    'dpi': DPI,
    'results': results,
}

os.makedirs(os.path.dirname(output_json), exist_ok=True)
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

print(f'[PaddleWorker] ✅ 完成: {total_pages}页 {total_chars}字 '
      f'置信度{avg_conf:.2%} 耗时{total_time:.0f}s 错误{errors}',
      flush=True)
