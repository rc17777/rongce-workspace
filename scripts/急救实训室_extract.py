"""提取急救实训室项目所有PDF文本"""
import pdfplumber, os

base = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-37-2024年多功能急救实训室建设项目"
out_dir = r"D:\openclaw-workspace\output\急救实训室_extracted"
os.makedirs(out_dir, exist_ok=True)

def extract_pdf(path, out_name):
    print(f"Extracting: {os.path.basename(path)}")
    with pdfplumber.open(path) as pdf:
        pages_text = []
        for i, page in enumerate(pdf.pages):
            t = page.extract_text()
            if t:
                pages_text.append(f"=== PAGE {i+1} ===\n{t}")
            else:
                pages_text.append(f"=== PAGE {i+1} ===\n[NO TEXT EXTRACTED]")
        full = "\n\n".join(pages_text)
    out_path = os.path.join(out_dir, out_name)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(full)
    print(f"  -> {out_path} ({len(full)} chars, {len(pages_text)} pages)")
    return full

# 1. 招标文件
zhaobiao = extract_pdf(
    os.path.join(base, "2024年多功能急救实训室建设项目招标文件（N510001202500062820250425001）.pdf"),
    "招标文件.txt"
)

# 2. 归档资料
guidang = extract_pdf(
    os.path.join(base, "归档资料-2024年多功能急救实训室建设项目（N5100012025000628）.pdf"),
    "归档资料.txt"
)

# 3. 投标文件 - 逐个投标人的逐个PDF
bid_base = os.path.join(base, "2024年多功能急救实训室建设项目投标文件(1)", "投标文件", "采购包1")
bidders = [d for d in os.listdir(bid_base) if os.path.isdir(os.path.join(bid_base, d))]
for bidder in sorted(bidders):
    bidder_dir = os.path.join(bid_base, bidder)
    bidder_short = bidder.replace("(包1)", "").strip()
    pdfs = [f for f in os.listdir(bidder_dir) if f.lower().endswith('.pdf')]
    all_text = []
    for pf in sorted(pdfs):
        pf_path = os.path.join(bidder_dir, pf)
        try:
            with pdfplumber.open(pf_path) as pdf:
                pages = []
                for j, page in enumerate(pdf.pages):
                    t = page.extract_text()
                    if t:
                        pages.append(f"--- FILE: {pf} PAGE {j+1} ---\n{t}")
                if pages:
                    all_text.append("\n\n".join(pages))
            print(f"  {bidder_short}/{pf}: {len(pages)} pages extracted")
        except Exception as e:
            print(f"  {bidder_short}/{pf}: ERROR - {e}")
    combined = "\n\n==========\n\n".join(all_text)
    out_path = os.path.join(out_dir, f"投标_{bidder_short}.txt")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(combined)
    print(f"  -> {out_path} ({len(combined)} chars)")

print("\n=== DONE ===")
