# -*- coding: utf-8 -*-
"""
审盾数据接入统一入口 — 六入口归一化 → SDF (审盾数据帧)

用法:
  # 自动识别类型 (excel/csv/pdf电子/PDF扫描/sql/api)
  python ingest.py --source "序时账.xlsx" --project pidou_2026 --label 序时账

  # 指定类型
  python ingest.py --source "扫描发票.pdf" --type pdf_scanned --project xx --label 发票
  python ingest.py --source "dump.sql" --type sql_dump --project xx --label 台账 --table 明细表
  python ingest.py --source "https://api.example.com" --type api --api-config cfg.json --project xx --label 数据

  # 全部输出到 profiles/<project>/sdf/
  默认输出: scripts/data_profiling/profiles/<project>/sdf/<label>_sdf.json

说明:
  - PDF电子件: 自动探测文本层, 无文本层自动提示转扫描件
  - PDF扫描件: 自动调用 PaddleOCR 环境 (需安装, 或设 PADDLEOCR_PYTHON)
  - API: 需要 --api-config 配置文件 (见 api_adapter.py 文档)
"""
import sys, os, json, argparse
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from adapters.router import detect_type, dispatch


def main():
    p = argparse.ArgumentParser(description='审盾数据接入统一入口 v1.0 (六入口→SDF)')
    p.add_argument('--source', required=True, help='数据源: 文件路径或API URL')
    p.add_argument('--type', default='auto', help='入口类型: auto|excel|csv|pdf_electronic|pdf_scanned|sql_dump|api')
    p.add_argument('--project', required=True, help='项目标识 (如 pidou_2026)')
    p.add_argument('--label', required=True, help='数据集标签 (如 运行经费/发票台账)')
    p.add_argument('--out', help='输出目录 (默认 profiles/<project>/sdf)')
    p.add_argument('--api-config', help='API配置JSON (api类型必填)')
    p.add_argument('--sheet', help='Excel Sheet名 (excel类型)')
    p.add_argument('--table', help='只处理指定表 (sql_dump类型)')
    p.add_argument('--chunk-pages', type=int, default=25, help='PDF扫描件每chunk页数')
    p.add_argument('--dpi', type=int, default=200, help='PDF扫描件OCR DPI')
    p.add_argument('--keep-chunks', action='store_true', help='PDF扫描件保留chunk')
    p.add_argument('--dry-run', action='store_true', help='只识别类型不分派')
    args = p.parse_args()

    # ─── 类型识别 ────────────────────────────
    print('=' * 60)
    print(f'  🚪 审盾数据接入 — 入口识别')
    print('=' * 60)
    entry_type = detect_type(args.source, args.type)
    print(f'  ✅ 识别入口: {entry_type}')
    if args.dry_run:
        print('  (dry-run, 未执行)')
        return

    # ─── 输出目录 ────────────────────────────
    if args.out:
        out_dir = Path(args.out)
    else:
        out_dir = HERE / 'profiles' / args.project / 'sdf'
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f'  📂 输出目录: {out_dir}')

    # ─── 分派 ────────────────────────────────
    print('=' * 60)
    print(f'  🔄 执行 {entry_type} 适配器...')
    print('=' * 60)
    results = dispatch(
        entry_type, args.source, str(out_dir), args.label,
        sheet=args.sheet, table=args.table,
        chunk_pages=args.chunk_pages, dpi=args.dpi,
        keep_chunks=args.keep_chunks, api_config=args.api_config,
    )

    # ─── 汇总 ────────────────────────────────
    print('=' * 60)
    print('  ✅ 接入完成')
    print('=' * 60)
    for name, path, sdf in results:
        src = sdf['source']
        prof = sdf['profile']
        print(f'  📦 [{name}] {src["type"]} | {src["original_file"]}')
        print(f'     行: {prof["row_count"]} | 列: {prof["col_count"]} | 空值率: {prof["null_rate"]*100:.1f}%')
        if path:
            print(f'     → {path}')
        if src.get('ocr_quality'):
            print(f'     OCR质量: {src["ocr_quality"]} ({src.get("ocr_mean_conf")})')
        if src.get('note'):
            print(f'     注: {src["note"]}')


if __name__ == '__main__':
    main()
