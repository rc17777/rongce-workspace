#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Production cloud OCR pipeline for scanned audit PDFs.

Features:
- PDF -> page images with PyMuPDF
- Baidu OCR per page, with checkpoint/skip-existing
- configurable engine: accurate_basic (verified), accurate, general_basic, doc_parse
- output raw JSON, page text, combined text, and Markdown notes
- optional publishing to local knowledge base and Obsidian vault
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import re
import shutil
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
sys.path.insert(0, str(WORKSPACE / "scripts"))

from baidu_doc_parse_client import (  # noqa: E402
    call_doc_parse_image,
    call_ocr_image,
    extract_text,
    get_access_token,
    load_env,
    summarize_payload,
)

DEFAULT_OUT = WORKSPACE / "outputs" / "cloud_ocr"
DEFAULT_KNOWLEDGE_ROOT = WORKSPACE / "knowledge" / "审计案例库-OCR-Cloud"
DEFAULT_VAULT_ROOT = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault") / "审计案例库-OCR-Cloud"
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
    ("审计切入点", ["聚焦", "围绕", "针对", "发现", "线索", "切入", "突破口", "疑点", "异常"]),
    ("数据和资料", ["数据", "台账", "清单", "凭证", "报表", "系统", "资料", "合同", "票据", "银行"]),
    ("分析方法", ["比对", "关联", "穿透", "核查", "抽查", "筛查", "模型", "分析", "延伸", "追踪"]),
    ("问题链条", ["违规", "虚报", "套取", "挤占", "挪用", "闲置", "损失", "风险", "漏洞", "不规范"]),
    ("取证路径", ["现场", "访谈", "函证", "取证", "核实", "延伸", "查看", "调查", "走访"]),
    ("治理建议", ["建议", "整改", "完善", "健全", "规范", "推动", "提升", "堵塞", "机制"]),
]


def safe_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip() or "untitled"


def render_pdf_pages(pdf: Path, image_dir: Path, dpi_scale: float = 2.8, force: bool = False) -> list[Path]:
    image_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf))
    images: list[Path] = []
    for idx, page in enumerate(doc, start=1):
        out = image_dir / f"page_{idx:03d}.png"
        if not out.exists() or force:
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi_scale, dpi_scale), alpha=False)
            pix.save(str(out))
            Image.open(out).convert("L").save(out)
        images.append(out)
    doc.close()
    return images


def normalize_text(text: str) -> str:
    text = re.sub(r"(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def ocr_one_page(task: dict[str, Any]) -> dict[str, Any]:
    image = Path(task["image"])
    json_path = Path(task["json_path"])
    txt_path = Path(task["txt_path"])
    engine = task["engine"]
    endpoint = task["endpoint"]
    skip_existing = task["skip_existing"]
    token = task["token"]
    env = task["env"]

    if skip_existing and json_path.exists() and txt_path.exists():
        return {"image": str(image), "skipped": True, "summary": None}

    for attempt in range(1, task["retries"] + 2):
        try:
            if engine == "doc_parse":
                payload = call_doc_parse_image(image, token, env)
            else:
                payload = call_ocr_image(image, token, endpoint_name=endpoint)
            text = normalize_text(extract_text(payload))
            json_path.parent.mkdir(parents=True, exist_ok=True)
            txt_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            txt_path.write_text(text, encoding="utf-8")
            return {"image": str(image), "skipped": False, "summary": summarize_payload(payload)}
        except Exception as exc:
            if attempt > task["retries"]:
                return {"image": str(image), "error": str(exc)}
            time.sleep(min(2 * attempt, 8))
    return {"image": str(image), "error": "unreachable"}


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
    haystack = f"{title}\n{text[:7000]}"
    scores = {}
    for scene, keywords in SCENE_KEYWORDS.items():
        scores[scene] = sum(haystack.count(kw) * (4 if kw in title else 1) for kw in keywords)
    best, score = max(scores.items(), key=lambda item: item[1])
    return (best if score > 0 else "其他审计"), scores


def extract_keywords(title: str, text: str, scene: str) -> list[str]:
    fixed = [kw for kw in SCENE_KEYWORDS.get(scene, []) if kw in title or kw in text[:7000]]
    words = re.findall(r"[\u4e00-\u9fa5]{2,8}", title + text[:4000])
    banned = {"中国审计", "审计署", "一个", "进行", "通过", "相关", "工作", "问题", "情况", "发现", "单位"}
    common = [w for w, _ in Counter(words).most_common(30) if w not in fixed and w not in banned]
    return (fixed + common + ["审计案例", "云OCR"])[:14]


def yaml_list(items: list[str]) -> str:
    return "[" + ", ".join(json.dumps(i, ensure_ascii=False) for i in items) + "]"


def make_markdown(pdf: Path, text: str, scene: str, scores: dict[str, int], engine: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    keywords = extract_keywords(pdf.stem, text, scene)
    abstract = "".join(split_sentences(text)[:5])[:900]
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
tags:
  - 审计案例
  - 云OCR
  - {scene}
keywords: {yaml_list(keywords)}
findings: {yaml_list(findings)}
recommendations: {yaml_list(recommendations)}
ocr_engine: Baidu {engine}
---

# {pdf.stem}

## 基本信息

- 来源: {pdf}
- 应用场景: {scene}
- 分类依据: {scene_scores}
- OCR时间: {now}
- OCR文本长度: {len(text)} 字符
- OCR引擎: Baidu {engine}

## 内容摘要

{abstract or "（未能自动生成摘要）"}

## 审计逻辑提炼

{chr(10).join(logic_sections)}

## 可迁移审计发现

{findings_md}

## 可迁移治理建议

{rec_md}

## OCR完整文本

<details>
<summary>展开 OCR 文本</summary>

```text
{text}
```

</details>
"""


def discover_pdfs(input_path: Path) -> list[Path]:
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    return sorted(input_path.rglob("*.pdf"), key=lambda p: p.name)


def publish(md_path: Path, scene: str, knowledge_root: Path, vault_root: Path) -> tuple[Path, Path]:
    k_dir = knowledge_root / scene
    v_dir = vault_root / scene
    k_dir.mkdir(parents=True, exist_ok=True)
    v_dir.mkdir(parents=True, exist_ok=True)
    k_path = k_dir / md_path.name
    v_path = v_dir / md_path.name
    shutil.copy2(md_path, k_path)
    shutil.copy2(md_path, v_path)
    return k_path, v_path


def rebuild_vault_index(vault_root: Path, source_folder: str) -> None:
    if not vault_root.exists():
        return
    rows = []
    for fp in sorted(vault_root.rglob("*.md")):
        content = fp.read_text(encoding="utf-8", errors="replace")[:2500]
        head = ""
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                head = content[3:end]
        scene = re.search(r"scene:\s*([^\n]+)", head)
        title = re.search(r"title:\s*(.+)", head)
        rows.append({
            "path": str(fp.relative_to(vault_root.parent)),
            "filename": fp.name,
            "scene": scene.group(1).strip() if scene else "",
            "title": title.group(1).strip().strip('"') if title else fp.stem,
            "source_folder": source_folder,
            "has_keywords": "keywords:" in head,
            "has_findings": "findings:" in head,
        })
    existing = []
    if VAULT_INDEX.exists():
        try:
            existing = json.loads(VAULT_INDEX.read_text(encoding="utf-8-sig"))
        except Exception:
            existing = []
    existing = [x for x in existing if x.get("source_folder") != source_folder]
    VAULT_INDEX.write_text(json.dumps(existing + rows, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="PDF file or directory")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--engine", choices=["accurate_basic", "accurate", "general_basic", "doc_parse"], default="accurate_basic")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force-render", action="store_true")
    parser.add_argument("--force-ocr", action="store_true")
    parser.add_argument("--publish", action="store_true", help="Publish Markdown to knowledge and Obsidian")
    parser.add_argument("--knowledge-root", type=Path, default=DEFAULT_KNOWLEDGE_ROOT)
    parser.add_argument("--vault-root", type=Path, default=DEFAULT_VAULT_ROOT)
    parser.add_argument("--source-folder", default="cloud-ocr")
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    pdfs = discover_pdfs(args.input)
    if args.limit:
        pdfs = pdfs[: args.limit]
    if not pdfs:
        print(f"No PDFs found: {args.input}")
        return 1

    env = load_env()
    token = get_access_token(env)["access_token"]
    run_index = []
    print(f"PDF count: {len(pdfs)} | engine={args.engine} | workers={args.workers}")

    for pdf_idx, pdf in enumerate(pdfs, start=1):
        pdf_stem = safe_name(pdf.stem)
        pdf_dir = args.out / pdf_stem
        img_dir = pdf_dir / "images"
        json_dir = pdf_dir / "json"
        page_txt_dir = pdf_dir / "page_text"
        combined_txt = pdf_dir / f"{pdf_stem}.txt"
        md_path = pdf_dir / f"{pdf_stem}.md"
        pdf_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[{pdf_idx}/{len(pdfs)}] render {pdf.name}")
        images = render_pdf_pages(pdf, img_dir, force=args.force_render)
        tasks = []
        for image in images:
            stem = image.stem
            tasks.append({
                "image": str(image),
                "json_path": str(json_dir / f"{stem}.json"),
                "txt_path": str(page_txt_dir / f"{stem}.txt"),
                "engine": "doc_parse" if args.engine == "doc_parse" else "ocr",
                "endpoint": args.engine,
                "skip_existing": not args.force_ocr,
                "token": token,
                "env": env,
                "retries": args.retries,
            })

        print(f"[{pdf_idx}/{len(pdfs)}] OCR pages={len(tasks)}")
        results = []
        with futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for result in pool.map(ocr_one_page, tasks):
                results.append(result)
                status = "skip" if result.get("skipped") else "ok" if not result.get("error") else "ERR"
                print(f"  {status} {Path(result['image']).name}")

        errors = [r for r in results if r.get("error")]
        if errors:
            print(json.dumps(errors, ensure_ascii=False, indent=2))
            raise RuntimeError(f"OCR failed for {len(errors)} pages in {pdf}")

        texts = []
        for idx in range(1, len(images) + 1):
            page_txt = page_txt_dir / f"page_{idx:03d}.txt"
            texts.append(f"\n\n--- 第 {idx} 页 ---\n\n{page_txt.read_text(encoding='utf-8', errors='replace')}")
        text = normalize_text("".join(texts))
        combined_txt.write_text(text, encoding="utf-8")

        scene, scores = classify_scene(pdf.stem, text)
        md = make_markdown(pdf, text, scene, scores, args.engine)
        md_path.write_text(md, encoding="utf-8")
        item = {
            "source": str(pdf),
            "engine": args.engine,
            "pages": len(images),
            "text_chars": len(text),
            "scene": scene,
            "out_dir": str(pdf_dir),
            "text": str(combined_txt),
            "markdown": str(md_path),
        }
        if args.publish:
            k_path, v_path = publish(md_path, scene, args.knowledge_root, args.vault_root)
            item["knowledge_path"] = str(k_path)
            item["vault_path"] = str(v_path)
        run_index.append(item)
        print(f"[OK] {scene} | {len(text)} chars | {md_path}")

    index_path = args.out / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(run_index, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.publish:
        rebuild_vault_index(args.vault_root, args.source_folder)
    print(f"\nIndex written: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
