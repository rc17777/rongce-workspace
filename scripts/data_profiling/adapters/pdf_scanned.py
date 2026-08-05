# -*- coding: utf-8 -*-
"""
PDF扫描件适配器 — PaddleOCR + PDF拆分
适用: 发票/合同/银行回单/会议纪要等扫描件
流程: 大PDF拆分(chunk) → 子进程调用paddleocr环境worker → 页级JSON收集
      → 表格行重建 → SDF + OCR质量分层(4.3)

依赖: base环境(pymupdf) + paddleocr conda环境
用法: python pdf_scanned.py --source "scan.pdf" --out sdf.json [--chunk-pages 25] [--dpi 200] [--keep-chunks]

PADDLEOCR_PYTHON 环境变量可指定paddleocr解释器路径
"""
import sys, os, json, argparse, subprocess, shutil, time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import build_sdf, save_sdf, print_sdf_summary, sha256_file, quality_layer

WORKER = HERE / 'pdf_ocr_worker.py'

PADDLEOCR_PYTHON_CANDIDATES = [
    os.environ.get('PADDLEOCR_PYTHON', ''),
    r'C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe',
    str(Path.home() / 'miniconda3/envs/paddleocr/python.exe'),
    str(Path.home() / 'anaconda3/envs/paddleocr/python.exe'),
    sys.executable,  # 兜底: 当前解释器(若恰好是paddleocr环境)
]


def find_paddleocr_python():
    import importlib.util
    for cand in PADDLEOCR_PYTHON_CANDIDATES:
        if not cand:
            continue
        if not os.path.exists(cand):
            continue
        # 验证该解释器可导入 paddleocr
        try:
            r = subprocess.run([cand, '-c', 'import paddleocr; print(paddleocr.__version__)'],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and r.stdout.strip():
                print(f'  🔧 PaddleOCR 环境: {cand} (v{r.stdout.strip()})')
                return cand
        except Exception:
            continue
    raise RuntimeError('未找到可用的 PaddleOCR 环境。请安装或设置 PADDLEOCR_PYTHON 环境变量。')


def split_pdf(source, out_dir, chunk_pages):
    """用 pymupdf 拆分大PDF → chunk_000.pdf, chunk_001.pdf ..."""
    import fitz
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(source)
    total = doc.page_count
    chunks = []
    for start in range(0, total, chunk_pages):
        end = min(start + chunk_pages, total)
        chunk_path = out_dir / f'chunk_{start//chunk_pages:03d}_p{start+1}-{end}.pdf'
        if chunk_path.exists():
            chunks.append(chunk_path)
            continue
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end - 1)
        new_doc.save(chunk_path)
        new_doc.close()
        chunks.append(chunk_path)
    doc.close()
    print(f'  ✂️  拆分: {total} 页 → {len(chunks)} 个 chunk (每chunk≤{chunk_pages}页)')
    return chunks


def run_ocr_chunks(chunks, work_dir, paddle_python, dpi, lang):
    """逐chunk调用paddleocr worker，返回页级JSON文件列表"""
    page_files = []
    for i, chunk in enumerate(chunks):
        chunk_out = work_dir / f'ocr_{i:03d}'
        chunk_out.mkdir(parents=True, exist_ok=True)
        cmd = [paddle_python, str(WORKER), '--pdf', str(chunk), '--out', str(chunk_out),
               '--dpi', str(dpi), '--lang', lang]
        print(f'  🔍 OCR chunk {i+1}/{len(chunks)}: {chunk.name}')
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.stdout:
            print('    ' + '\n    '.join(r.stdout.strip().split('\n')))
        if r.returncode != 0:
            raise RuntimeError(f'OCR chunk 失败: {chunk.name}\n{r.stderr[-2000:]}')
        for pf in sorted(chunk_out.glob('p*.json')):
            page_files.append(pf)
    return page_files


def merge_pages(page_files):
    """收集页级JSON → (lines记录, 表格行, 质量指标)"""
    records = []   # 文本行记录: {page, line, text}
    rows = []      # 表格行记录
    confs = []
    total_chars = 0
    for pf in sorted(page_files, key=lambda x: int(x.stem[1:])):
        with open(pf, encoding='utf-8') as f:
            pj = json.load(f)
        page = pj.get('page', int(pf.stem[1:]) + 1)
        confs.append(pj.get('mean_conf', 0))
        total_chars += pj.get('char_count', 0)
        for ln, line in enumerate(pj.get('lines', [])):
            records.append({'page': page, 'line': ln + 1, 'text': line['text']})
        for r in pj.get('rows', []):
            row = {'page': page}
            for i, cell in enumerate(r):
                row[f'col{i+1}'] = cell
            rows.append(row)
    mean_conf = round(sum(confs) / max(len(confs), 1), 4)
    return records, rows, mean_conf, total_chars


def convert(source, out_path=None, chunk_pages=25, dpi=200, lang='ch', keep_chunks=False, work_root=None):
    """
    主入口: 返回 (sdf, 质量层)
    """
    import fitz
    # 快速检查页数
    doc = fitz.open(source)
    total = doc.page_count
    doc.close()

    checksum = sha256_file(source)
    work_root = Path(work_root or (Path(out_path).parent if out_path else Path.cwd()))
    work_dir = work_root / f'_pdfscan_{Path(source).stem}'
    chunks_dir = work_dir / 'chunks'
    chunks_dir.mkdir(parents=True, exist_ok=True)

    paddle_python = find_paddleocr_python()
    chunks = split_pdf(source, chunks_dir, chunk_pages)
    page_files = run_ocr_chunks(chunks, work_dir, paddle_python, dpi, lang)

    records, rows, mean_conf, total_chars = merge_pages(page_files)
    layer = quality_layer(mean_conf)

    if rows:
        sdf = build_sdf('pdf_scanned', os.path.basename(source), rows,
                        checksum=checksum,
                        extra_source={'total_pages': total, 'ocr_mean_conf': mean_conf,
                                      'ocr_quality': layer, 'mode': 'table'})
    else:
        sdf = build_sdf('pdf_scanned', os.path.basename(source), records,
                        checksum=checksum,
                        extra_source={'total_pages': total, 'ocr_mean_conf': mean_conf,
                                      'ocr_quality': layer, 'mode': 'text',
                                      'char_count': total_chars})

    # 质量分层提示 (设计文档 4.3)
    if layer == 'high':
        sdf['source']['note'] = 'OCR高质量(≥95%)，自动入库'
    elif layer == 'medium':
        sdf['source']['note'] = 'OCR中质量(85-95%)，建议人工抽检'
    else:
        sdf['source']['note'] = 'OCR低质量(<85%)，暂停入库，需审计师确认'

    if out_path:
        save_sdf(sdf, out_path)

    if not keep_chunks:
        shutil.rmtree(work_dir, ignore_errors=True)
        print(f'  🧹 临时chunk已清理 (--keep-chunks 可保留)')

    return sdf, layer


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='PDF扫描件适配器 (PaddleOCR)')
    p.add_argument('--source', required=True, help='扫描PDF路径')
    p.add_argument('--out', help='SDF输出路径')
    p.add_argument('--chunk-pages', type=int, default=25, help='每chunk页数(内存控制)')
    p.add_argument('--dpi', type=int, default=200)
    p.add_argument('--lang', default='ch')
    p.add_argument('--keep-chunks', action='store_true', help='保留拆分chunk(便于断点续跑)')
    args = p.parse_args()

    sdf, layer = convert(args.source, args.out, args.chunk_pages, args.dpi, args.lang, args.keep_chunks)
    print_sdf_summary(sdf)
    print(f'  🎯 OCR质量: {layer} ({sdf["source"].get("ocr_mean_conf")}) | 模式: {sdf["source"].get("mode")}')
