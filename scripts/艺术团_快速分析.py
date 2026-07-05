import fitz, os, hashlib
from collections import Counter

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目"
OUT = r"D:\openclaw-workspace\output\艺术团采购"
os.makedirs(OUT, exist_ok=True)

files = {
    '招标文件': os.path.join(BASE, '招标采购文件-ZHH-F〔2025〕85号磋商文件-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目.pdf'),
    '归档资料': os.path.join(BASE, '备案资料-ZHH-F〔2025〕85号--四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目.pdf'),
    '胤皓': os.path.join(BASE, '供应商投标文件', '四川胤皓文化传媒有限公司.pdf'),
    '太格': os.path.join(BASE, '供应商投标文件', '太格电子文档.pdf'),
    '立美': os.path.join(BASE, '供应商投标文件', '立美响应文件.pdf'),
}

# L5: Metadata
print('=== L5: METADATA ===')
for name, path in files.items():
    if not os.path.exists(path): continue
    try:
        doc = fitz.open(path)
        meta = doc.metadata
        print('[%s] Producer=%s | Creator=%s | Author=%s | Created=%s | Pages=%d' % (
            name, 
            meta.get('producer', '?'), 
            meta.get('creator', '?'),
            meta.get('author', '?'),
            meta.get('creationDate', '?'),
            len(doc)))
        doc.close()
    except Exception as e:
        print('[%s] ERROR: %s' % (name, str(e)[:80]))

# L4: Image Hash
print('\n=== L4: IMAGE HASH ===')
all_hashes = {}
for name, path in files.items():
    if name in ['招标文件','归档资料']: continue
    if not os.path.exists(path): continue
    doc = fitz.open(path)
    count = 0
    for pg in range(len(doc)):
        for img_info in doc[pg].get_images(full=True):
            try:
                img_data = doc.extract_image(img_info[0])
                h = hashlib.sha256(img_data['image']).hexdigest()
                all_hashes.setdefault(h, []).append(name)
                count += 1
            except: pass
    doc.close()
    print('  %s: %d images' % (name, count))

cross = [(h,b) for h,b in all_hashes.items() if len(set(b))>1]
print('  Cross-bidder matches: %d' % len(cross))
for h,b in cross:
    print('    %s... by %s' % (h[:16], b))

# L6: Fonts
print('\n=== L6: FONTS ===')
fonts_per = {}
for name, path in files.items():
    if name in ['招标文件','归档资料']: continue
    if not os.path.exists(path): continue
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
    fonts_per[name] = fonts
    top3 = ' | '.join(['%s(%d)' % (f,c) for f,c in fonts.most_common(3)])
    print('  %s: %d spans, %d fonts | Top: %s' % (name, sum(fonts.values()), len(fonts), top3))

for a,b in [('胤皓','太格'),('胤皓','立美'),('太格','立美')]:
    if a in fonts_per and b in fonts_per:
        sa = set(fonts_per[a].keys()); sb = set(fonts_per[b].keys())
        print('  %s vs %s: %d shared, %d/%d unique' % (a,b, len(sa&sb), len(sa-sb), len(sb-sa)))

# Text extraction (fast PyMuPDF)
print('\n=== TEXT EXTRACTION ===')
for name in ['招标文件','胤皓','太格','立美']:
    path = files.get(name)
    if not path or not os.path.exists(path): continue
    doc = fitz.open(path)
    text = ''
    for pg in range(len(doc)):
        text += doc[pg].get_text()
    doc.close()
    out_path = os.path.join(OUT, '%s.txt' % name)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    # Extract prices
    import re
    prices = re.findall(r'(\d[\d,.]{3,})\s*元', text)
    print('  %s: %d chars, %d pages | Top prices: %s' % (
        name, len(text), len(text.split('\n')), 
        str([int(p.replace(',','').replace('.','')) for p in prices[:5] if len(p)>3])
    ))

print('\nDone!')
