#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR and archive audit case PDFs from Desktop/6册.

The source PDFs are scanned images. This script keeps them read-only, writes
intermediate OCR artifacts under the workspace, then publishes Markdown notes
to the local knowledge base and Obsidian vault.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import fitz
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
SOURCE_DIR = Path(r"C:\Users\scrccpa\Desktop\6册")
RUN_DIR = WORKSPACE / "outputs" / "audit_case_6册_ocr"
TEXT_DIR = RUN_DIR / "texts"
MD_DIR = RUN_DIR / "markdown"
IMG_DIR = RUN_DIR / "page_images"
INDEX_PATH = RUN_DIR / "index.json"

KNOWLEDGE_ROOT = WORKSPACE / "knowledge" / "审计案例库-OCR" / "6册"
VAULT_ROOT = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault") / "审计案例库-OCR" / "6册"
VAULT_INDEX = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault") / "审计资料清单.json"

SCENE_KEYWORDS = {
    "经济责任审计": ["经济责任", "领导干部", "离任", "任中", "权力运行", "履职", "决策"],
    "预算执行审计": ["预算执行", "预算", "决算", "财政收支", "财政资金", "支出", "债务"],
    "专项资金审计": ["专项资金", "专项", "补助", "补贴", "转移支付", "资金管理", "套取", "挤占", "挪用"],
    "工程审计": ["工程", "建设项目", "招标", "投标", "造价", "施工", "项目管理", "竣工", "结算"],
    "国企审计": ["国企", "国有企业", "央企", "国资", "国有资本", "企业", "主责主业"],
    "金融审计": ["金融", "银行", "债券", "债务", "保证金", "融资", "基金", "私募", "保险", "证券"],
    "资源环境审计": ["资源", "环境", "生态", "污染", "绿色", "能源", "水环境", "土壤", "矿", "碳"],
    "信息系统审计": ["信息系统", "数据", "数字", "大数据", "SQL", "Excel", "算法", "模型", "人工智能", "网络安全"],
    "绩效审计": ["绩效", "效益", "效率", "效果", "绩效评价", "效能"],
    "政策落实审计": ["政策落实", "政策", "重大决策", "落实", "改革", "监督", "治理"],
    "社保民生审计": ["社保", "民生", "医疗", "医院", "医保", "养老", "教育", "学校", "就业", "残疾人"],
    "农业农村审计": ["农业", "农村", "乡村", "涉农", "粮食", "耕地", "农民", "农田"],
    "内部审计": ["内部审计", "内审", "内控", "风险管理", "公司治理"],
}

LOGIC_PATTERNS = [
    ("审计切入点", ["聚焦", "围绕", "针对", "发现", "线索", "切入", "突破口", "疑点"]),
    ("数据和资料", ["数据", "台账", "清单", "凭证", "报表", "系统", "资料", "合同", "票据", "银行"]),
    ("分析方法", ["比对", "关联", "穿透", "核查", "抽查", "筛查", "模型", "分析", "延伸", "追踪"]),
    ("问题链条", ["违规", "虚报", "套取", "挤占", "挪用", "闲置", "损失", "风险", "漏洞", "不规范"]),
    ("取证路径", ["现场", "访谈", "函证", "取证", "核实", "延伸", "查看", "调查", "走访"]),
    ("治理建议", ["建议", "整改", "完善", "健全", "规范", "推动", "提升", "堵塞", "机制"]),
]


def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
    return name or "untitled"


def run_tesseract(image_path: Path) -> str:
    cmd = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        str(image_path),
        "stdout",
        "-l",
        "chi_sim+eng",
        "--psm",
        "6",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"tesseract failed: {image_path}")
    return result.stdout.strip()


def render_page(page: fitz.Page, out_path: Path, zoom: float = 2.8) -> Path:
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(str(out_path))
    img = Image.open(out_path).convert("L")
    img.save(out_path)
    return out_path


def normalize_ocr_text(text: str) -> str:
    text = text.replace("丨", "|")
    text = re.sub(r"(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def ocr_page_columns(image_path: Path) -> str:
    img = Image.open(image_path)
    width, height = img.size
    margin_x = int(width * 0.035)
    margin_y = int(height * 0.035)
    mid = width // 2
    overlap = int(width * 0.015)
    boxes = [
        (margin_x, margin_y, mid + overlap, height - margin_y),
        (mid - overlap, margin_y, width - margin_x, height - margin_y),
    ]
    parts = []
    for col_idx, box in enumerate(boxes, start=1):
        crop_path = image_path.with_name(f"{image_path.stem}_col{col_idx}.png")
        img.crop(box).save(crop_path)
        parts.append(run_tesseract(crop_path))
    return normalize_ocr_text("\n".join(parts))


def ocr_pdf(pdf_path: Path, force: bool = False) -> tuple[str, int]:
    stem = safe_filename(pdf_path.stem)
    text_path = TEXT_DIR / f"{stem}.txt"
    if text_path.exists() and not force:
        return text_path.read_text(encoding="utf-8", errors="replace"), 0

    doc = fitz.open(str(pdf_path))
    page_texts: list[str] = []
    pdf_img_dir = IMG_DIR / stem
    pdf_img_dir.mkdir(parents=True, exist_ok=True)
    for idx, page in enumerate(doc, start=1):
        image_path = pdf_img_dir / f"page_{idx:03d}.png"
        render_page(page, image_path)
        text = ocr_page_columns(image_path)
        page_texts.append(f"\n\n--- 第 {idx} 页 ---\n\n{text}")
        print(f"[OCR] {pdf_path.name} page {idx}/{doc.page_count}: {len(text)} chars")
    doc.close()
    full_text = "".join(page_texts).strip()
    text_path.write_text(full_text, encoding="utf-8")
    return full_text, len(page_texts)


def split_sentences(text: str) -> list[str]:
    compact = re.sub(r"[ \t\r\f\v]+", "", text)
    compact = re.sub(r"\n+", "", compact)
    parts = re.split(r"(?<=[。！？；])", compact)
    return [p for p in parts if 18 <= len(p) <= 220]


def top_sentences(text: str, keywords: list[str], limit: int = 5) -> list[str]:
    scored = []
    for sent in split_sentences(text):
        score = sum(2 for kw in keywords if kw in sent)
        score += min(len(sent) // 45, 3)
        if score:
            scored.append((score, sent))
    picked: list[str] = []
    seen: set[str] = set()
    for _, sent in sorted(scored, key=lambda x: x[0], reverse=True):
        key = sent[:34]
        if key in seen:
            continue
        seen.add(key)
        picked.append(sent)
        if len(picked) >= limit:
            break
    return picked


def classify_scene(title: str, text: str) -> tuple[str, dict[str, int]]:
    haystack = f"{title}\n{text[:5000]}"
    scores = {}
    for scene, keywords in SCENE_KEYWORDS.items():
        scores[scene] = sum(haystack.count(kw) * (4 if kw in title else 1) for kw in keywords)
    best, score = max(scores.items(), key=lambda item: item[1])
    return (best if score > 0 else "其他审计"), scores


def extract_keywords(title: str, text: str, scene: str) -> list[str]:
    fixed = [kw for kw in SCENE_KEYWORDS.get(scene, []) if kw in title or kw in text[:6000]]
    words = re.findall(r"[\u4e00-\u9fa5]{2,8}", title + text[:3500])
    banned = {"中国审计", "审计署", "一个", "进行", "通过", "相关", "工作", "问题", "情况", "发现", "单位"}
    common = [w for w, _ in Counter(words).most_common(30) if w not in fixed and w not in banned]
    return (fixed + common + ["审计案例", "OCR"])[:14]


def yaml_list(items: list[str]) -> str:
    return "[" + ", ".join(json.dumps(i, ensure_ascii=False) for i in items) + "]"


def build_markdown(pdf: Path, text: str, scene: str, scores: dict[str, int]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    keywords = extract_keywords(pdf.stem, text, scene)
    abstract = "".join(split_sentences(text)[:5])[:800]
    findings = top_sentences(text, ["问题", "风险", "违规", "不足", "异常", "漏洞", "套取", "挪用"], 7)
    recommendations = top_sentences(text, ["建议", "整改", "完善", "健全", "规范", "提升", "机制", "监督"], 7)

    logic_sections = []
    for label, kws in LOGIC_PATTERNS:
        items = top_sentences(text, kws, 4)
        body = "\n".join(f"- {item}" for item in items) if items else "- （未自动提取到明确表述，建议人工复核补充）"
        logic_sections.append(f"### {label}\n{body}")

    scene_scores = ", ".join(f"{k}:{v}" for k, v in sorted(scores.items(), key=lambda x: -x[1])[:5])
    findings_md = "\n".join(f"{idx}. {item}" for idx, item in enumerate(findings, 1)) or "（未自动提取到典型问题句）"
    rec_md = "\n".join(f"{idx}. {item}" for idx, item in enumerate(recommendations, 1)) or "（未自动提取到建议句）"

    return f"""---
title: {json.dumps(pdf.stem, ensure_ascii=False)}
created: {now}
scene: {scene}
source: {json.dumps(str(pdf), ensure_ascii=False)}
folder: 6册
tags:
  - 审计案例
  - OCR
  - {scene}
keywords: {yaml_list(keywords)}
findings: {yaml_list(findings)}
recommendations: {yaml_list(recommendations)}
ocr_engine: Tesseract chi_sim+eng
---

# {pdf.stem}

## 基本信息

- 来源: {pdf}
- 应用场景: {scene}
- 分类依据: {scene_scores}
- OCR时间: {now}
- OCR文本长度: {len(text)} 字符

## 内容摘要

{abstract or "（未能自动生成摘要）"}

## 审计逻辑提炼

{chr(10).join(logic_sections)}

## 可迁移审计发现

{findings_md}

## 可迁移治理建议

{rec_md}

## 应用提示

- 可作为 `{scene}` 的案例素材，用于审计方案设计、疑点模型构建、访谈提纲和底稿问题表述参考。
- OCR文本已自动提取，引用到正式报告前应回看原 PDF 校核关键金额、主体名称和法规表述。

## OCR完整文本

<details>
<summary>展开 OCR 文本</summary>

```text
{text}
```

</details>
"""


def publish_note(md_path: Path, scene: str) -> tuple[Path, Path]:
    knowledge_scene = KNOWLEDGE_ROOT / scene
    vault_scene = VAULT_ROOT / scene
    knowledge_scene.mkdir(parents=True, exist_ok=True)
    vault_scene.mkdir(parents=True, exist_ok=True)
    k_path = knowledge_scene / md_path.name
    v_path = vault_scene / md_path.name
    shutil.copy2(md_path, k_path)
    shutil.copy2(md_path, v_path)
    return k_path, v_path


def rebuild_vault_index() -> None:
    if not VAULT_ROOT.exists():
        return
    rows = []
    for fp in sorted(VAULT_ROOT.rglob("*.md")):
        content = fp.read_text(encoding="utf-8", errors="replace")[:2500]
        head = ""
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                head = content[3:end]
        scene = re.search(r"scene:\s*([^\n]+)", head)
        title = re.search(r"title:\s*(.+)", head)
        rows.append({
            "path": str(fp.relative_to(VAULT_ROOT.parent)),
            "filename": fp.name,
            "scene": scene.group(1).strip() if scene else "",
            "title": title.group(1).strip().strip('"') if title else fp.stem,
            "source_folder": "6册",
            "has_keywords": "keywords:" in head,
            "has_findings": "findings:" in head,
        })
    existing = []
    if VAULT_INDEX.exists():
        try:
            existing = json.loads(VAULT_INDEX.read_text(encoding="utf-8-sig"))
        except Exception:
            existing = []
    existing = [x for x in existing if x.get("source_folder") != "6册" and "审计案例库-OCR\\6册" not in x.get("path", "")]
    VAULT_INDEX.write_text(json.dumps(existing + rows, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Only process first N PDFs")
    parser.add_argument("--force", action="store_true", help="Re-run OCR even if text exists")
    args = parser.parse_args()

    if not SOURCE_DIR.exists():
        print(f"Source not found: {SOURCE_DIR}")
        return 1
    for path in [RUN_DIR, TEXT_DIR, MD_DIR, IMG_DIR, KNOWLEDGE_ROOT, VAULT_ROOT]:
        path.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(SOURCE_DIR.glob("*.pdf"), key=lambda p: p.name)
    if args.limit:
        pdfs = pdfs[: args.limit]
    print(f"PDF count: {len(pdfs)}")

    index = []
    for idx, pdf in enumerate(pdfs, start=1):
        print(f"\n[{idx}/{len(pdfs)}] {pdf.name}")
        text, pages_ocrd = ocr_pdf(pdf, force=args.force)
        scene, scores = classify_scene(pdf.stem, text)
        md = build_markdown(pdf, text, scene, scores)
        md_path = MD_DIR / f"{safe_filename(pdf.stem)}.md"
        md_path.write_text(md, encoding="utf-8")
        knowledge_path, vault_path = publish_note(md_path, scene)
        index.append({
            "source": str(pdf),
            "pages_ocrd": pages_ocrd,
            "text_chars": len(text),
            "scene": scene,
            "markdown": str(md_path),
            "knowledge_path": str(knowledge_path),
            "vault_path": str(vault_path),
        })
        print(f"[OK] {scene} | {len(text)} chars | {vault_path}")

    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    rebuild_vault_index()
    print(f"\nIndex written: {INDEX_PATH}")
    print(f"Knowledge root: {KNOWLEDGE_ROOT}")
    print(f"Vault root: {VAULT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
