# -*- coding: utf-8 -*-
"""
重新生成 _ocr_output 的准确 manifest。
- 扫描 E:\2026\审计方法&政策文件\_ocr_output 下所有 .md
- 书籍类：解析 YAML frontmatter（total_pages / business_line / ocr_avg_confidence 等）
- 杂志文章类：解析 "> 来源: ... | 页数: N | OCR引擎: ..." 头部 + "## 第N页" 标记
- 输出 _manifest.json（stats / results / coverage / timestamp）
用法: python scripts/regenerate_ocr_manifest.py [--output-dir 路径]
"""
import json
import re
import sys
import glob
import os
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR = r"E:\2026\审计方法&政策文件\_ocr_output"
SOURCE_DIR = r"E:\2026\审计方法&政策文件\审计相关书籍"

FM_PATTERNS = {
    "title": re.compile(r'^title:\s*["\']?(.*?)["\']?\s*$', re.M),
    "source": re.compile(r'^source:\s*["\']?(.*?)["\']?\s*$', re.M),
    "business_line": re.compile(r'^business_line:\s*["\']?(.*?)["\']?\s*$', re.M),
    "total_pages": re.compile(r'^total_pages:\s*(\d+)\s*$', re.M),
    "ocr_date": re.compile(r'^ocr_date:\s*["\']?(.*?)["\']?\s*$', re.M),
    "ocr_pages_paddle": re.compile(r'^ocr_pages_paddle:\s*(\d+)\s*$', re.M),
    "ocr_pages_qwen": re.compile(r'^ocr_pages_qwen:\s*(\d+)\s*$', re.M),
    "ocr_avg_confidence": re.compile(r'^ocr_avg_confidence:\s*([\d.]+)\s*$', re.M),
    "ocr_engine": re.compile(r'^ocr_engine:\s*["\']?(.*?)["\']?\s*$', re.M),
}
ARTICLE_HEADER = re.compile(r">\s*来源:\s*(.*?)\s*\|\s*页数:\s*(\d+)\s*\|\s*OCR引擎:\s*(.*?)\s*$", re.M)
PAGE_MARK = re.compile(r"^##\s*第(\d+)页\s*$", re.M)


def strip_frontmatter(text):
    """返回 (frontmatter_dict, body_text)"""
    fm = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            head = text[3:end]
            for key, pat in FM_PATTERNS.items():
                m = pat.search(head)
                if m:
                    val = m.group(1)
                    if key in ("total_pages", "ocr_pages_paddle", "ocr_pages_qwen"):
                        val = int(val)
                    elif key == "ocr_avg_confidence":
                        val = float(val)
                    fm[key] = val
            body = text[end + 4 :]
            return fm, body
    return fm, text


def count_chars(body):
    """正文有效字符：去空白、去 markdown 标记后的字符数（含中文/数字/字母）"""
    # 去掉代码块外的 md 符号影响不大，直接去掉空白统计可读字符
    return len(re.sub(r"\s", "", body))


def analyze_md(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    fm, body = strip_frontmatter(raw)
    category = os.path.basename(os.path.dirname(path))
    fname = os.path.basename(path)

    if fm.get("total_pages") is not None:
        # 书籍类（含 frontmatter）
        pages = fm["total_pages"]
        engine = fm.get("ocr_engine") or (
            "PaddleOCR" if fm.get("ocr_pages_qwen", 0) == 0 else "Qwen-API"
        )
        info = {
            "filename": os.path.splitext(fname)[0].replace(".pdf", ""),
            "pages": pages,
            "chars": count_chars(body),
            "path": path,
            "category": category,
            "source": fm.get("source", ""),
            "ocr_date": fm.get("ocr_date", ""),
            "ocr_engine": engine,
            "confidence": fm.get("ocr_avg_confidence"),
            "qwen_pages": fm.get("ocr_pages_qwen", 0),
            "paddle_pages": fm.get("ocr_pages_paddle", 0),
        }
    else:
        # 杂志文章类
        m = ARTICLE_HEADER.search(body)
        if m:
            pages = int(m.group(2))
            engine = m.group(3)
        else:
            marks = PAGE_MARK.findall(body)
            pages = max([int(p) for p in marks], default=0) or (1 if body.strip() else 0)
            engine = "PaddleOCR"
        info = {
            "filename": os.path.splitext(fname)[0],
            "pages": pages,
            "chars": count_chars(body),
            "path": path,
            "category": category,
            "source": "",
            "ocr_date": "",
            "ocr_engine": engine,
            "confidence": None,
            "qwen_pages": 0,
            "paddle_pages": pages,
        }
    return info


def source_coverage():
    """对比源目录 55 本 PDF 与输出，找出未 OCR 的书"""
    missing = []
    done = set()
    if not os.path.isdir(SOURCE_DIR):
        return None, None
    src_pdfs = []
    for root, _, files in os.walk(SOURCE_DIR):
        for f in files:
            if f.lower().endswith(".pdf"):
                src_pdfs.append(os.path.join(root, f))
    # 输出文件去掉 .md / .pdf.md 后缀后的名字集合
    out_mds = glob.glob(os.path.join(OUTPUT_DIR, "**", "*.md"), recursive=True)
    out_names = set()
    for m in out_mds:
        base = os.path.basename(m)
        base = base.replace(".pdf.md", "").replace(".md", "")
        out_names.add(base)
    for p in src_pdfs:
        base = os.path.splitext(os.path.basename(p))[0]
        if base not in out_names:
            missing.append(p)
    return len(src_pdfs), missing


def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_DIR
    md_files = sorted(glob.glob(os.path.join(output_dir, "**", "*.md"), recursive=True))
    md_files = [f for f in md_files if not f.endswith("_manifest.json")]

    results = {}
    total_pages = total_chars = failed = 0
    for path in md_files:
        category = os.path.basename(os.path.dirname(path))
        try:
            info = analyze_md(path)
        except Exception as e:
            failed += 1
            print(f"  !! 解析失败: {path}: {e}", file=sys.stderr)
            continue
        results.setdefault(category, []).append(info)
        total_pages += info["pages"]
        total_chars += info["chars"]

    # 按类别排序，条目加 label（保持旧格式：类别[i/N]）
    ordered = {}
    for cat in sorted(results):
        items = sorted(results[cat], key=lambda x: x["filename"])
        n = len(items)
        for i, it in enumerate(items, 1):
            it["label"] = f"{cat}[{i}/{n}]"
        ordered[cat] = items

    src_count, missing = source_coverage()
    manifest = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generator": "scripts/regenerate_ocr_manifest.py",
        "stats": {
            "total_files": len(md_files),
            "total_pages": total_pages,
            "total_chars": total_chars,
            "failed": failed,
            "categories": len(ordered),
        },
        "results": ordered,
    }
    if src_count is not None:
        manifest["coverage"] = {
            "source_pdfs": src_count,
            "not_ocr_yet": [os.path.basename(p) for p in (missing or [])],
            "note": "源目录 PDF 与输出文件名匹配不上的书籍（可能未处理或命名不一致）",
        }

    out_path = os.path.join(output_dir, "_manifest.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print("=" * 60)
    print(f"✅ manifest 已重新生成: {out_path}")
    print(json.dumps(manifest["stats"], ensure_ascii=False, indent=1))
    for cat, items in ordered.items():
        print(f"  {cat}: {len(items)} 个文件 / {sum(i['pages'] for i in items)} 页 / {sum(i['chars'] for i in items)} 字")
    if src_count is not None:
        print(f"\n📊 源目录 PDF: {src_count} 本，未匹配输出: {len(missing or [])} 本")
        for p in (missing or []):
            print(f"   ⚠️  {os.path.basename(p)}")


if __name__ == "__main__":
    main()
