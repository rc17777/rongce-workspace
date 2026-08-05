# -*- coding: utf-8 -*-
"""
PDF扫描件OCR工作器 — 在 paddleocr conda 环境中运行
用法: paddleocr_python pdf_ocr_worker.py --pdf chunk.pdf --out outdir [--dpi 200] [--lang ch]
输出: outdir/p0001.json ... (每页一个JSON, 支持断点续跑)

每页JSON结构:
{
  "page": 1,
  "lines": [{"text": "...", "conf": 0.98, "box": [[x,y]x4]}],
  "rows": [["单元格", ...]],        # y聚类表格重建结果(仅多列行)
  "mean_conf": 0.95,
  "char_count": 123
}
"""
import sys, os, json, argparse, time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')


def cluster_rows(lines, y_tol_factor=0.6):
    """
    基于y中心聚类重建表格行:
    1. 按y中心排序
    2. y差 < 中位行高*y_tol_factor 的行归为同一行
    3. 行内按x排序 → 单元格
    返回: [ [cell_text, ...], ... ]
    """
    if not lines:
        return []
    items = []
    for ln in lines:
        box = ln.get('box') or []
        if len(box) < 4:
            continue
        ys = [pt[1] for pt in box]
        xs = [pt[0] for pt in box]
        items.append({
            'text': ln.get('text', ''),
            'conf': ln.get('conf', 0),
            'y_center': sum(ys) / len(ys),
            'y_min': min(ys), 'y_max': max(ys),
            'x_min': min(xs), 'x_max': max(xs),
            'height': max(ys) - min(ys),
        })
    if not items:
        return []
    items.sort(key=lambda i: i['y_center'])
    heights = [i['height'] for i in items if i['height'] > 0]
    median_h = sorted(heights)[len(heights) // 2] if heights else 10
    tol = max(median_h * y_tol_factor, 4)

    # 贪心聚类: 当前行
    groups = []
    cur = [items[0]]
    for it in items[1:]:
        if abs(it['y_center'] - cur[-1]['y_center']) <= tol:
            cur.append(it)
        else:
            groups.append(cur)
            cur = [it]
    groups.append(cur)

    rows = []
    for g in groups:
        g.sort(key=lambda i: i['x_min'])
        texts = [i['text'] for i in g if i['text'].strip()]
        if len(texts) >= 2:
            rows.append(texts)
    return rows


def process_pdf(pdf_path, out_dir, dpi=200, lang='ch', skip_existing=True):
    import fitz
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    total = doc.page_count
    done = 0

    for pg in range(total):
        out_file = out_dir / f'p{pg:04d}.json'
        if skip_existing and out_file.exists():
            done += 1
            continue

        page = doc[pg]
        pix = page.get_pixmap(dpi=dpi)
        img_path = out_dir / f'_tmp_p{pg:04d}.png'
        pix.save(img_path)

        try:
            # paddleocr 2.7: ocr.ocr(img, cls=True) → [page_results]
            result = ocr.ocr(str(img_path), cls=True)
            page_items = result[0] if result else []
            lines = []
            for item in page_items or []:
                box = item[0]
                text, conf = item[1]
                lines.append({'text': text, 'conf': round(float(conf), 4), 'box': box})
            mean_conf = round(sum(l['conf'] for l in lines) / max(len(lines), 1), 4)
            rows = cluster_rows(lines)
            page_json = {
                'page': pg + 1,
                'lines': lines,
                'rows': rows,
                'mean_conf': mean_conf,
                'char_count': sum(len(l['text']) for l in lines),
            }
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(page_json, f, ensure_ascii=False)
            done += 1
            if done % 5 == 0 or done == total:
                print(f'  [{pdf_path}] {done}/{total} 页 (conf={mean_conf})', flush=True)
        finally:
            try:
                os.remove(img_path)
            except OSError:
                pass

    doc.close()
    print(f'DONE {pdf_path}: {done}/{total} 页', flush=True)
    return done


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='PDF扫描件OCR工作器 (PaddleOCR)')
    p.add_argument('--pdf', required=True, help='PDF路径(可为拆分chunk)')
    p.add_argument('--out', required=True, help='输出目录(每页JSON)')
    p.add_argument('--dpi', type=int, default=200)
    p.add_argument('--lang', default='ch')
    p.add_argument('--no-skip', action='store_true', help='不跳过已有页面')
    args = p.parse_args()
    process_pdf(args.pdf, args.out, args.dpi, args.lang, skip_existing=not args.no_skip)
