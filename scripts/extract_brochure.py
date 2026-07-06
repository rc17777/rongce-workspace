from __future__ import annotations

import json
from pathlib import Path

import fitz


PDF_PATH = Path(r"C:\Users\scrccpa\Desktop\数据化改革\四川融策.pdf")
OUT_DIR = Path("work/sichuan_rongce_brochure")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF_PATH)
    texts = []
    for index, page in enumerate(doc):
        text = page.get_text("text")
        texts.append({"page": index + 1, "chars": len(text), "text": text})
        pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8), alpha=False)
        pix.save(str(OUT_DIR / f"page_{index + 1:02d}.png"))

    (OUT_DIR / "extracted_text.json").write_text(
        json.dumps(texts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "extracted_text.txt").write_text(
        "\n\n".join(f"===== Page {item['page']} =====\n{item['text']}" for item in texts),
        encoding="utf-8",
    )

    print(f"pages: {doc.page_count}")
    for item in texts:
        print(f"p{item['page']}: {item['chars']} chars")
    print((OUT_DIR / "extracted_text.txt").resolve())


if __name__ == "__main__":
    main()
