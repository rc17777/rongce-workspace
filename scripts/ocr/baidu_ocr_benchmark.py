#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small benchmark for Baidu OCR against existing local OCR artifacts."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
sys.path.insert(0, str(WORKSPACE / "scripts"))

from baidu_ocr_client import call_accurate_basic, get_access_token, load_env  # noqa: E402

OUT_DIR = WORKSPACE / "outputs" / "baidu_ocr_benchmark"


def words_to_text(payload: dict) -> str:
    return "\n".join(item.get("words", "") for item in payload.get("words_result", []))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted((WORKSPACE / "outputs").glob("audit_case_*_ocr/page_images/*/page_001.png"))[:3]
    if not images:
        print("No sample images found")
        return 1
    token = get_access_token(load_env())["access_token"]
    rows = []
    for image in images:
        print(f"[Baidu OCR] {image}")
        payload = call_accurate_basic(image, token)
        text = words_to_text(payload)
        sample_name = image.parent.name
        out_json = OUT_DIR / f"{sample_name}_page001_baidu.json"
        out_txt = OUT_DIR / f"{sample_name}_page001_baidu.txt"
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out_txt.write_text(text, encoding="utf-8")
        probs = [x.get("probability", {}).get("average") for x in payload.get("words_result", [])]
        probs = [p for p in probs if isinstance(p, (int, float))]
        rows.append({
            "image": str(image),
            "words_result_num": payload.get("words_result_num", len(payload.get("words_result", []))),
            "chars": len(text),
            "avg_probability": round(sum(probs) / len(probs), 6) if probs else None,
            "txt": str(out_txt),
            "json": str(out_json),
        })
    summary = {
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "engine": "baidu accurate_basic",
        "samples": rows,
    }
    summary_path = OUT_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
