# -*- coding: utf-8 -*-
"""
PDF电子件适配器 — pdfplumber
适用: 从系统直接导出的可编辑PDF（有文本层）
流程: 文本层探测 → 表格定位抽取 → 结构化
      无文本层 → 提示转扫描件适配器 (pdf_scanned)

用法: python pdf_electronic.py --source "report.pdf" --out sdf.json
"""
import sys, os, json, argparse
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import build_sdf, save_sdf, print_sdf_summary, sha256_file, now_iso

TEXT_LAYER_THRESHOLD = 0.1  # 文本页占比 <10% 视为扫描件


def probe_text_layer(path):
    """探测文本层: 返回 (有文本页数, 总页数, 总字符数)"""
    import pdfplumber
    text_pages = 0
    total_chars = 0
    with pdfplumber.open(path) as pdf:
        total = len(pdf.pages)
        for page in pdf.pages:
            t = page.extract_text() or ''
            if t.strip():
                text_pages += 1
                total_chars += len(t.strip())
    return text_pages, total, total_chars


def normalize_table(table):
    """归一化 pdfplumber 表格: 空行剔除、行列填充"""
    if not table:
        return []
    max_cols = max(len(r) for r in table)
    rows = []
    for r in table:
        row = [c if c is not None else '' for c in r]
        row += [''] * (max_cols - len(row))
        if any(str(c).strip() for c in row):
            rows.append(row)
    return rows


def extract_tables(path, min_rows=2):
    """抽取全部表格 → [{header, rows, page}]"""
    import pdfplumber
    results = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
            except Exception:
                continue
            for t in tables:
                t = normalize_table(t)
                if len(t) < min_rows:
                    continue
                header = [str(c).strip() if c else f'列{i+1}' for i, c in enumerate(t[0])]
                data = t[1:]
                results.append({'header': header, 'rows': data, 'page': pno + 1})
    return results


def extract_text_records(path):
    """纯文本模式: 每行一条记录 {page, line, text}"""
    import pdfplumber
    records = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages):
            t = page.extract_text() or ''
            for ln, line in enumerate(t.split('\n')):
                if line.strip():
                    records.append({'page': pno + 1, 'line': ln + 1, 'text': line.strip()})
    return records


def convert(path, out_path=None, min_rows=2):
    """
    主入口: 返回 (sdf, 是否电子件)
    """
    text_pages, total, total_chars = probe_text_layer(path)

    if total == 0:
        raise ValueError('PDF 无页面')

    is_electronic = (text_pages / total) >= TEXT_LAYER_THRESHOLD
    if not is_electronic:
        # 无文本层 → 提示转扫描件
        sdf = build_sdf(
            'pdf_scanned_suggested', os.path.basename(path), [],
            checksum=sha256_file(path),
            extra_source={'text_pages': text_pages, 'total_pages': total, 'note': '无文本层，疑似扫描件，请用 pdf_scanned 适配器 OCR'}
        )
        sdf['profile']['encoding'] = 'none'
        if out_path:
            save_sdf(sdf, out_path)
        return sdf, False

    tables = extract_tables(path, min_rows=min_rows)
    checksum = sha256_file(path)

    if tables:
        # 表格模式: 跨页合并同构表格
        rows = []
        columns = None
        for t in tables:
            hdr = [h for h in t['header']]
            if columns is None:
                columns = [{'name': h, 'type': 'string'} for h in hdr]
            if len(hdr) == len(columns) and hdr == [c['name'] for c in columns]:
                for r in t['rows']:
                    rows.append({hdr[i]: (r[i] if i < len(r) else None) for i in range(len(hdr))})
            else:
                # 异构表格: 每行加 table_index 列
                for r in t['rows']:
                    rec = {'_table': t['page'], '_row': r[0] if r else ''}
                    for i, h in enumerate(hdr):
                        rec[h] = r[i] if i < len(r) else None
                    rows.append(rec)
        sdf = build_sdf('pdf_electronic', os.path.basename(path), rows, columns=columns,
                        checksum=checksum,
                        extra_source={'total_pages': total, 'text_pages': text_pages, 'tables_found': len(tables)})
    else:
        # 文本模式: 无表格 → 行记录
        records = extract_text_records(path)
        sdf = build_sdf('pdf_electronic_text', os.path.basename(path), records,
                        checksum=checksum,
                        extra_source={'total_pages': total, 'text_pages': text_pages, 'mode': 'text'})

    if out_path:
        save_sdf(sdf, out_path)
    return sdf, True


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='PDF电子件适配器 (pdfplumber)')
    p.add_argument('--source', required=True, help='PDF文件路径')
    p.add_argument('--out', help='SDF输出路径')
    p.add_argument('--min-rows', type=int, default=2, help='表格最少数据行数(过滤噪声)')
    args = p.parse_args()

    sdf, is_elec = convert(args.source, args.out, args.min_rows)
    if not is_elec:
        print(f'⚠️  疑似扫描件: 文本页 {sdf["source"].get("text_pages")}/{sdf["source"].get("total_pages")}')
        print(f'   建议: 使用 pdf_scanned 适配器 (PaddleOCR)')
    else:
        print_sdf_summary(sdf)
