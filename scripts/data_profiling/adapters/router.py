# -*- coding: utf-8 -*-
"""
入口路由器 — 六入口类型识别与分派
识别: 扩展名 + 内容探测(PDf文本层) → 分派到对应适配器
统一输出: SDF (审盾数据帧)

类型: excel | csv | pdf_electronic | pdf_scanned | sql_dump | api
"""
import sys, os, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

EXT_MAP = {
    '.xlsx': 'excel', '.xlsm': 'excel', '.xls': 'excel',
    '.csv': 'csv', '.tsv': 'csv',
    '.sql': 'sql_dump',
    '.pdf': 'pdf',  # 需进一步探测文本层
}


def detect_type(source, hint=None):
    """识别入口类型。hint优先，否则扩展名+内容探测"""
    if hint and hint != 'auto':
        return hint
    if source.startswith('http://') or source.startswith('https://'):
        return 'api'
    ext = Path(source).suffix.lower()
    t = EXT_MAP.get(ext)
    if t == 'pdf':
        return detect_pdf(source)
    if t is None:
        raise ValueError(f'无法识别文件类型: {source} (扩展名 {ext or "无"})')
    return t


def detect_pdf(source):
    """PDF文本层探测: 文本页占比>=10% → 电子件, 否则扫描件"""
    try:
        import pdfplumber
        text_pages = 0
        with pdfplumber.open(source) as pdf:
            total = len(pdf.pages)
            for page in pdf.pages:
                if (page.extract_text() or '').strip():
                    text_pages += 1
        if total == 0:
            return 'pdf_scanned'
        return 'pdf_electronic' if text_pages / total >= 0.1 else 'pdf_scanned'
    except Exception as e:
        raise RuntimeError(f'PDF探测失败: {e}')


def dispatch(entry_type, source, out_dir=None, label='data', **kwargs):
    """
    分派到适配器，输出SDF
    out_dir: 输出目录 (None → 仅内存返回)
    返回: [ (名称, sdf或sdf路径, sdf对象), ... ]
    """
    out_dir = Path(out_dir) if out_dir else None
    results = []

    if entry_type in ('excel', 'csv'):
        from csv_excel_adapter import convert as conv
        out_path = out_dir / f'{label}_sdf.json' if out_dir else None
        sdf = conv(source, out_path, kwargs.get('sheet'))
        results.append((label, out_path, sdf))

    elif entry_type == 'pdf_electronic':
        from pdf_electronic import convert as conv
        out_path = out_dir / f'{label}_sdf.json' if out_dir else None
        sdf, is_elec = conv(source, out_path, kwargs.get('min_rows', 2))
        if not is_elec:
            print(f'  ⚠️ 提示: {source} 疑似扫描件，建议改用 pdf_scanned 入口')
        results.append((label, out_path, sdf))

    elif entry_type == 'pdf_scanned':
        from pdf_scanned import convert as conv
        out_path = out_dir / f'{label}_sdf.json' if out_dir else None
        sdf, layer = conv(source, out_path,
                          chunk_pages=kwargs.get('chunk_pages', 25),
                          dpi=kwargs.get('dpi', 200),
                          lang=kwargs.get('lang', 'ch'),
                          keep_chunks=kwargs.get('keep_chunks', False))
        results.append((label, out_path, sdf))

    elif entry_type == 'sql_dump':
        from sql_dump import convert as conv
        table_filter = kwargs.get('table')
        res = conv(source, out_dir, table_filter, label)
        results.extend([(f'{label}_{t}', p, s) for t, p, s in res])

    elif entry_type == 'api':
        from api_adapter import convert as conv
        cfg = kwargs.get('api_config')
        if not cfg:
            raise ValueError('API入口需要 --api-config 配置JSON')
        out_path = out_dir / f'{label}_sdf.json' if out_dir else None
        sdf = conv(cfg, out_path, label)
        results.append((label, out_path, sdf))

    else:
        raise ValueError(f'未知入口类型: {entry_type}')

    return results
