#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR and archive selected China Audit issue 6 PDFs."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SOURCE_DIR = Path(r"C:\Users\scrccpa\Desktop\中国审计第6期")
VAULT = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault")
ARCHIVE_ROOT = VAULT / "审计案例库-OCR" / "中国审计第6期"
INDEX_PATH = VAULT / "中国审计第6期-OCR归档索引.json"

SCENE_KEYWORDS = {
    "经济责任审计": ["经济责任", "领导干部", "离任", "任中", "权力运行", "政绩观"],
    "预算执行审计": ["预算执行", "预算", "决算", "财政收支", "财政资金", "支出", "地方政府债务"],
    "专项资金审计": ["专项资金", "专项", "补助", "补贴", "转移支付", "资金管理"],
    "工程审计": ["工程", "建设项目", "招标", "投标", "造价", "施工", "项目管理", "竣工", "结算"],
    "国企审计": ["国企", "国有企业", "央企", "国资", "国有资本", "主责主业", "企业"],
    "金融审计": ["金融", "银行", "债券", "债务", "保证金", "融资", "AMC", "保险", "证券"],
    "资源环境审计": ["资源", "环境", "生态", "污染", "绿色", "能源", "碳", "气候"],
    "信息系统审计": ["信息系统", "数据", "数字", "大数据", "SQL", "Excel", "算法", "模型", "人工智能", "网络安全"],
    "绩效审计": ["绩效", "效益", "效率", "效果", "绩效评价", "效能"],
    "政策落实审计": ["政策落实", "政策", "重大决策", "十五五", "协同发展", "现代化"],
    "社保民生审计": ["社保", "民生", "医疗", "医院", "医保", "养老", "教育", "营养餐"],
    "农业农村审计": ["农业", "农村", "乡村", "涉农", "粮食", "耕地"],
    "内部审计": ["内部审计", "内审", "内控", "风险管理", "公司治理", "协同审计"],
}

LOGIC_PATTERNS = [
    ("审计目标", ["目标", "目的", "围绕", "聚焦", "立足"]),
    ("审计对象", ["对象", "范围", "领域", "项目", "资金", "单位"]),
    ("数据资料", ["数据", "资料", "台账", "凭证", "报表", "系统", "清单", "SQL", "Excel"]),
    ("分析方法", ["分析", "比对", "穿透", "关联", "模型", "算法", "核查", "抽查", "访谈"]),
    ("疑点线索", ["疑点", "线索", "异常", "风险", "问题", "漏洞", "违规"]),
    ("核实取证", ["延伸", "核实", "取证", "现场", "访谈", "函证", "勘察"]),
    ("整改建议", ["建议", "整改", "完善", "健全", "规范", "推动", "提升"]),
]


def slug_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).replace(".pdf", ".md")


def init_ocr():
    from paddleocr import PaddleOCR
    try:
        return PaddleOCR(lang="ch")
    except Exception:
        return PaddleOCR(use_angle_cls=True, lang="ch")


def pdf_to_images(pdf_path: Path, temp_dir: Path) -> list[Path]:
    import fitz
    doc = fitz.open(str(pdf_path))
    images: list[Path] = []
    for idx, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        out = temp_dir / f"{pdf_path.stem}_{idx:03d}.png"
        pix.save(str(out))
        images.append(out)
    doc.close()
    return images


def extract_ocr_text(ocr, image: Path) -> str:
    result = ocr.ocr(str(image), cls=True)
    lines: list[str] = []
    if not result:
        return ""
    for block in result:
        if not block:
            continue
        for item in block:
            try:
                text, conf = item[1]
            except Exception:
                continue
            if text and float(conf) >= 0.55:
                lines.append(text.strip())
    return "\n".join(lines)


def split_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", text)
    parts = re.split(r"(?<=[。！？；])", compact)
    return [p for p in parts if 18 <= len(p) <= 180]


def top_sentences(text: str, keywords: list[str], limit: int = 5) -> list[str]:
    sentences = split_sentences(text)
    scored = []
    for s in sentences:
        score = sum(2 for k in keywords if k in s)
        score += min(len(s) // 40, 3)
        if score:
            scored.append((score, s))
    seen = set()
    picked = []
    for _, sent in sorted(scored, key=lambda x: x[0], reverse=True):
        key = sent[:28]
        if key in seen:
            continue
        seen.add(key)
        picked.append(sent)
        if len(picked) >= limit:
            break
    return picked


def classify_scene(title: str, text: str) -> tuple[str, dict[str, int]]:
    haystack = f"{title}\n{text[:3000]}"
    scores = {}
    for scene, kws in SCENE_KEYWORDS.items():
        scores[scene] = sum(haystack.count(k) * (3 if k in title else 1) for k in kws)
    best, score = max(scores.items(), key=lambda kv: kv[1])
    return (best if score > 0 else "其他审计"), scores


def extract_keywords(title: str, text: str, scene: str) -> list[str]:
    candidates = SCENE_KEYWORDS.get(scene, []) + ["审计", "风险", "问题", "建议", "整改", "监督", "治理"]
    found = [k for k in candidates if k in title or k in text[:5000]]
    cn_terms = re.findall(r"[\u4e00-\u9fa5]{2,8}", title + text[:2000])
    banned = {"中国审计", "审计署", "工作", "进行", "通过", "我国", "相关", "实现"}
    common = [w for w, _ in Counter(cn_terms).most_common(20) if w not in found and w not in banned]
    return (found + common)[:10]


def build_audit_logic(text: str) -> dict[str, list[str]]:
    return {label: top_sentences(text, kws, limit=3) for label, kws in LOGIC_PATTERNS}


def yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(json.dumps(i, ensure_ascii=False) for i in items) + "]"


def make_markdown(pdf: Path, text: str, scene: str, keywords: list[str], logic: dict[str, list[str]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    findings = top_sentences(text, ["问题", "风险", "违规", "不足", "异常", "漏洞"], limit=6)
    recommendations = top_sentences(text, ["建议", "整改", "完善", "健全", "规范", "提升"], limit=6)
    abstract = "".join(split_sentences(text)[:5])[:700]
    logic_md = ""
    for label, items in logic.items():
        logic_md += f"### {label}\n"
        logic_md += "\n".join(f"- {item}" for item in items) if items else "- （OCR文本中未自动提取到明确表述）"
        logic_md += "\n\n"
    findings_md = "\n".join(f"{i + 1}. {x}" for i, x in enumerate(findings)) if findings else "（未能自动提取关键发现，请复核原文补充）"
    recommendations_md = "\n".join(f"{i + 1}. {x}" for i, x in enumerate(recommendations)) if recommendations else "（未能自动提取建议，请复核原文补充）"
    return f'''---
title: {json.dumps(pdf.stem, ensure_ascii=False)}
created: {now}
scene: {scene}
source: {json.dumps(str(pdf), ensure_ascii=False)}
folder: 中国审计第6期
tags:
  - 审计案例
  - OCR
  - {scene}
keywords: {yaml_list(keywords)}
findings: {yaml_list(findings)}
recommendations: {yaml_list(recommendations)}
ocr_engine: PaddleOCR
---

# {pdf.stem}

## 基本信息

- 来源: {pdf}
- 场景分类: {scene}
- OCR时间: {now}
- 文本长度: {len(text)} 字符

## 内容摘要

{abstract or '（未能生成摘要）'}

## 审计逻辑

{logic_md}## 审计发现线索

{findings_md}

## 审计建议

{recommendations_md}

## OCR完整文本

<details>
<summary>点击展开完整文本</summary>

```text
{text}
```

</details>
'''


def main() -> int:
    if not SOURCE_DIR.exists():
        print(f"源目录不存在: {SOURCE_DIR}")
        return 1
    pdfs = sorted(SOURCE_DIR.glob("*.pdf"), key=lambda p: p.name)
    print(f"找到PDF: {len(pdfs)}")
    if not pdfs:
        return 1

    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    ocr = init_ocr()
    index = []
    with tempfile.TemporaryDirectory(prefix="china_audit_issue6_") as tmp:
        temp_dir = Path(tmp)
        for n, pdf in enumerate(pdfs, 1):
            print(f"[{n}/{len(pdfs)}] OCR: {pdf.name}")
            images = pdf_to_images(pdf, temp_dir)
            page_texts = []
            for image in images:
                page_texts.append(extract_ocr_text(ocr, image))
                image.unlink(missing_ok=True)
            text = "\n\n".join(t for t in page_texts if t.strip())
            scene, scores = classify_scene(pdf.stem, text)
            keywords = extract_keywords(pdf.stem, text, scene)
            logic = build_audit_logic(text)
            out_dir = ARCHIVE_ROOT / scene
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / slug_name(pdf.name)
            out_path.write_text(make_markdown(pdf, text, scene, keywords, logic), encoding="utf-8")
            index.append({
                "title": pdf.stem,
                "source": str(pdf),
                "archive_path": str(out_path),
                "scene": scene,
                "keywords": keywords,
                "text_length": len(text),
                "scene_scores": scores,
            })
            print(f"    -> {scene} | {len(text)}字 | {out_path}")

    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"索引写入: {INDEX_PATH}")
    by_scene = Counter(item["scene"] for item in index)
    print("场景统计:")
    for scene, count in by_scene.most_common():
        print(f"  {scene}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
