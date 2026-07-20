from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz
from PIL import Image

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
sys.path.insert(0, str(WORKSPACE / "scripts" / "ocr"))

from baidu_doc_parse_client import call_ocr_image, extract_text, get_access_token, load_env, summarize_payload

PDF_PATH = Path(r"C:\Users\scrccpa\Desktop\数据化改革\四川融策.pdf")
OUT_DIR = WORKSPACE / "work" / "sichuan_rongce_brochure" / "baidu_ocr"


def render_pages() -> list[Path]:
    img_dir = OUT_DIR / "pages"
    img_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(PDF_PATH))
    paths = []
    for idx, page in enumerate(doc, start=1):
        out = img_dir / f"page_{idx:02d}.png"
        if not out.exists():
            pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
            pix.save(str(out))
            Image.open(out).convert("RGB").save(out)
        paths.append(out)
    doc.close()
    return paths


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    env = load_env()
    token = get_access_token(env)["access_token"]
    page_images = render_pages()
    summary = []
    for idx, image in enumerate(page_images, start=1):
        json_path = OUT_DIR / f"page_{idx:02d}.json"
        txt_path = OUT_DIR / f"page_{idx:02d}.txt"
        if json_path.exists() and txt_path.exists():
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        else:
            payload = call_ocr_image(image, token, endpoint_name="accurate")
            json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            txt_path.write_text(extract_text(payload), encoding="utf-8")
        summary.append({"page": idx, **summarize_payload(payload)})
        print(json.dumps(summary[-1], ensure_ascii=False))
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
