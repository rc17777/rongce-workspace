"""补全 L4/L5/L6 分析：从PDF中提取图片哈希 + 元数据 + 字体/结构"""
import fitz  # PyMuPDF
import hashlib
import os
import re
from collections import Counter

base = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-37-2024年多功能急救实训室建设项目\2024年多功能急救实训室建设项目投标文件(1)\投标文件\采购包1"

bidders = {
    '好医助': '四川省好医助医疗器械有限公司(包1)',
    '易可天地': '成都易可天地科技有限公司(包1)',
    '江西正好': '江西正好医疗器械有限公司(包1)',
}

pdf_files_all = {}
for name, folder in bidders.items():
    bidder_dir = os.path.join(base, folder)
    if not os.path.exists(bidder_dir):
        continue
    for f in os.listdir(bidder_dir):
        if f.lower().endswith('.pdf'):
            fpath = os.path.join(bidder_dir, f)
            pdf_files_all.setdefault(name, []).append(fpath)
    print(f'{name}: {len(pdf_files_all.get(name, []))} PDF files')
    for f in pdf_files_all.get(name, []):
        print(f'  {os.path.basename(f)}')

# ============ L4: 图片提取+哈希 ============
print('\n' + '='*60)
print('L4: PDF嵌入图片哈希比对')
print('='*60)

image_hashes = {}  # hash -> [(bidder, pdf, img_index)]

for name in bidders:
    for fpath in pdf_files_all.get(name, []):
        try:
            doc = fitz.open(fpath)
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Get all images on the page
                images = page.get_images(full=True)
                for img_idx, img_info in enumerate(images):
                    xref = img_info[0]
                    try:
                        base_image = doc.extract_image(xref)
                        img_bytes = base_image["image"]
                        img_hash = hashlib.sha256(img_bytes).hexdigest()
                        img_ext = base_image["ext"]
                        img_size = len(img_bytes)
                        image_hashes.setdefault(img_hash, []).append(
                            (name, os.path.basename(fpath), page_num+1, img_idx, img_ext, img_size)
                        )
                    except:
                        pass
            doc.close()
        except Exception as e:
            print(f'  Error reading {fpath}: {e}')

# Count images per bidder
bidder_img_counts = {}
for h, entries in image_hashes.items():
    for entry in entries:
        bidder = entry[0]
        bidder_img_counts[bidder] = bidder_img_counts.get(bidder, 0) + 1

for bidder in bidders:
    print(f'  {bidder}: {bidder_img_counts.get(bidder, 0)} 张嵌入图片')

# Find cross-bidder matches
cross_matches = []
for h, entries in image_hashes.items():
    bidders_set = set(e[0] for e in entries)
    if len(bidders_set) > 1:
        cross_matches.append((h, entries))

if cross_matches:
    print(f'\n  🔴 跨公司图片重复: {len(cross_matches)} 张!')
    for h, entries in cross_matches[:10]:
        print(f'    Hash: {h[:16]}...')
        for e in entries:
            print(f'      {e[0]} | {e[1]} | Page {e[2]} | img#{e[3]} | {e[4]} | {e[5]} bytes')
else:
    print(f'\n  🟢 0张跨公司重复图片')
    for name in bidders:
        if bidder_img_counts.get(name, 0) > 0:
            print(f'    {name}: {bidder_img_counts.get(name, 0)}张独立图片')

# ============ L5: PDF元数据 ============
print('\n' + '='*60)
print('L5: PDF元数据提取')
print('='*60)

for name in bidders:
    for fpath in pdf_files_all.get(name, []):
        try:
            doc = fitz.open(fpath)
            meta = doc.metadata
            fname = os.path.basename(fpath)
            print(f'\n  [{name}] {fname}')
            print(f'    Title:      {meta.get("title", "N/A")}')
            print(f'    Author:     {meta.get("author", "N/A")}')
            print(f'    Subject:    {meta.get("subject", "N/A")}')
            print(f'    Creator:    {meta.get("creator", "N/A")}')
            print(f'    Producer:   {meta.get("producer", "N/A")}')
            print(f'    Created:    {meta.get("creationDate", "N/A")}')
            print(f'    Modified:   {meta.get("modDate", "N/A")}')
            print(f'    Format:     {meta.get("format", "N/A")}')
            print(f'    Encryption: {meta.get("encryption", "N/A")}')
            doc.close()
        except Exception as e:
            print(f'  Error: {e}')

# ============ L6: 字体/页面结构 ============
print('\n' + '='*60)
print('L6: PDF字体使用和页面结构分析')
print('='*60)

for name in bidders:
    all_fonts = Counter()
    pdf_count = 0
    for fpath in pdf_files_all.get(name, []):
        try:
            doc = fitz.open(fpath)
            pdf_count += 1
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                all_fonts[span["font"]] += 1
            doc.close()
        except:
            pass
    
    print(f'\n  [{name}] ({pdf_count}个PDF，共{sum(all_fonts.values())}个文本span)')
    if all_fonts:
        print(f'  字体使用频次 (Top 10):')
        for font, count in all_fonts.most_common(10):
            print(f'    {font}: {count}次')

# Cross-bidder font comparison
print('\n  字体交集分析:')
all_fonts_per_bidder = {}
for name in bidders:
    fonts = set()
    for fpath in pdf_files_all.get(name, []):
        try:
            doc = fitz.open(fpath)
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                fonts.add(span["font"])
            doc.close()
        except:
            pass
    all_fonts_per_bidder[name] = fonts
    print(f'  {name}: {len(fonts)}种字体')

pairs = [('好医助','易可天地'), ('好医助','江西正好'), ('易可天地','江西正好')]
for a, b in pairs:
    common = all_fonts_per_bidder.get(a, set()) & all_fonts_per_bidder.get(b, set())
    print(f'  {a} ∩ {b}: {len(common)}种共用字体')
    if common:
        print(f'    共用: {list(common)[:5]}')

print('\nDone!')
