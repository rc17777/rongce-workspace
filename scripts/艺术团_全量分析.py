"""艺术团采购项目 — 全量分析脚本"""
import fitz, os, hashlib, pdfplumber, re
from collections import Counter

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目"
OUT = r"D:\openclaw-workspace\output\艺术团采购"
os.makedirs(OUT, exist_ok=True)

# ============ 1. 文本提取 ============
print("=" * 60)
print("1. TEXT EXTRACTION")
print("=" * 60)

files = {
    '招标文件': os.path.join(BASE, '招标采购文件-ZHH-F〔2025〕85号磋商文件-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目.pdf'),
    '归档资料': os.path.join(BASE, '备案资料-ZHH-F〔2025〕85号--四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目.pdf'),
    '胤皓': os.path.join(BASE, '供应商投标文件', '四川胤皓文化传媒有限公司.pdf'),
    '太格': os.path.join(BASE, '供应商投标文件', '太格电子文档.pdf'),
    '立美': os.path.join(BASE, '供应商投标文件', '立美响应文件.pdf'),
}

texts = {}
for name, path in files.items():
    if not os.path.exists(path):
        print(f"  SKIP {name}: not found")
        continue
    try:
        with pdfplumber.open(path) as pdf:
            text = ""
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                if t:
                    text += t + "\n"
        # Save
        out_path = os.path.join(OUT, f'{name}.txt')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)
        texts[name] = text
        print(f"  {name}: {len(text):,} chars, {len(pdf.pages)} pages → saved")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

# ============ 2. L5 元数据提取 ============
print("\n" + "=" * 60)
print("2. L5: PDF METADATA")
print("=" * 60)

for name, path in files.items():
    if not os.path.exists(path):
        continue
    doc = fitz.open(path)
    meta = doc.metadata
    print(f"\n  [{name}]")
    print(f"    Producer:   {meta.get('producer', 'N/A')}")
    print(f"    Creator:    {meta.get('creator', 'N/A')}")
    print(f"    Author:     {meta.get('author', 'N/A')}")
    print(f"    CreationDate: {meta.get('creationDate', 'N/A')}")
    print(f"    ModDate:    {meta.get('modDate', 'N/A')}")
    print(f"    Subject:    {meta.get('subject', 'N/A')}")
    print(f"    Pages:      {len(doc)}")
    doc.close()

# ============ 3. L4 图片哈希 ============
print("\n" + "=" * 60)
print("3. L4: IMAGE HASH EXTRACTION")
print("=" * 60)

all_hashes = {}
bidder_counts = {}

for name, path in files.items():
    if name in ['招标文件', '归档资料']:
        continue
    if not os.path.exists(path):
        continue
    doc = fitz.open(path)
    count = 0
    for pg in range(len(doc)):
        for img_info in doc[pg].get_images(full=True):
            try:
                img_data = doc.extract_image(img_info[0])
                h = hashlib.sha256(img_data['image']).hexdigest()
                all_hashes.setdefault(h, []).append(name)
                count += 1
            except:
                pass
    doc.close()
    bidder_counts[name] = count
    print(f"  {name}: {count} images")

# Cross-bidder matches
cross = [(h, bidders) for h, bidders in all_hashes.items() if len(set(bidders)) > 1]
print(f"\n  Cross-bidder image matches: {len(cross)}")
for h, bidders in cross:
    print(f"    SHA256: {h[:16]}... by {bidders}")

# ============ 4. L6 字体分析 ============
print("\n" + "=" * 60)
print("4. L6: FONT ANALYSIS")
print("=" * 60)

fonts_per_bidder = {}
for name, path in files.items():
    if name in ['招标文件', '归档资料']:
        continue
    if not os.path.exists(path):
        continue
    doc = fitz.open(path)
    fonts = Counter()
    for pg in range(len(doc)):
        blocks = doc[pg].get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        fonts[span["font"]] += 1
    doc.close()
    fonts_per_bidder[name] = fonts
    print(f"\n  [{name}] {sum(fonts.values())} font usages, {len(fonts)} unique")
    for font, count in fonts.most_common(10):
        print(f"    {font}: {count}")

# Cross-bidder font overlap
print("\n  Font overlap:")
for a, b in [('胤皓','太格'),('胤皓','立美'),('太格','立美')]:
    if a in fonts_per_bidder and b in fonts_per_bidder:
        sa = set(fonts_per_bidder[a].keys())
        sb = set(fonts_per_bidder[b].keys())
        common = sa & sb
        print(f"    {a} vs {b}: {len(common)} shared / {len(sa)} vs {len(sb)}")

# ============ 5. 价格提取 ============
print("\n" + "=" * 60)
print("5. PRICE EXTRACTION")
print("=" * 60)

for name in ['胤皓', '太格', '立美']:
    text = texts.get(name, '')
    if not text:
        print(f"  {name}: no text")
        continue
    # Look for price patterns
    price_patterns = [
        (r'总价[：:]\s*(\d[\d,.]*)', '总价'),
        (r'报价[：:]\s*(\d[\d,.]*)', '报价'),
        (r'金额[：:]\s*(\d[\d,.]*)', '金额'),
        (r'大写[：:].*?([\d,]{4,})', '大写后数字'),
        (r'最终报价.*?(\d[\d,.]{3,})', '最终报价'),
        (r'响应报价.*?(\d[\d,.]{3,})', '响应报价'),
        (r'(\d[\d,.]{3,})\s*元', 'XX元'),
    ]
    for pattern, label in price_patterns:
        matches = re.findall(pattern, text)
        if matches:
            for m in matches[:5]:
                val = m
                try:
                    val = int(val.replace(',', '').replace('.', '').strip())
                    print(f"  {name} [{label}]: {val:,}")
                except:
                    pass
            break

print("\nDone!")
