import fitz, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from collections import Counter

base = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-37-2024年多功能急救实训室建设项目\2024年多功能急救实训室建设项目投标文件(1)\投标文件\采购包1"

bidders = {
    '好医助': '四川省好医助医疗器械有限公司(包1)',
    '易可天地': '成都易可天地科技有限公司(包1)',
    '江西正好': '江西正好医疗器械有限公司(包1)',
}

print('='*70)
print('L5: PDF METADATA')
print('='*70)

for name in bidders:
    bidder_dir = os.path.join(base, bidders[name])
    for f in sorted(os.listdir(bidder_dir)):
        if not f.lower().endswith('.pdf'):
            continue
        fpath = os.path.join(bidder_dir, f)
        doc = fitz.open(fpath)
        meta = doc.metadata
        producer = meta.get('producer', 'N/A')
        creator = meta.get('creator', 'N/A')
        author = meta.get('author', 'N/A')
        created = meta.get('creationDate', 'N/A')
        modified = meta.get('modDate', 'N/A')
        
        print('\n[%s] %s' % (name, f))
        print('  Producer:   %s' % producer)
        print('  Creator:    %s' % creator)
        print('  Author:     %s' % author.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
        print('  CreationDate: %s' % created)
        print('  ModDate:       %s' % modified)
        
        # Detect software
        for sw in ['WPS', 'Microsoft', 'Adobe', 'LibreOffice', 'iText', 'Foxit', 'Solid']:
            if sw.lower() in producer.lower():
                print('  -> Software detected: %s' % sw)
                break
        doc.close()

print('\n' + '='*70)
print('L6: FONT ANALYSIS')
print('='*70)

all_fonts_per_bidder = {}
for name in bidders:
    bidder_dir = os.path.join(base, bidders[name])
    fonts = Counter()
    for f in sorted(os.listdir(bidder_dir)):
        if not f.lower().endswith('.pdf'):
            continue
        fpath = os.path.join(bidder_dir, f)
        doc = fitz.open(fpath)
        for pg in range(len(doc)):
            blocks = doc[pg].get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            fonts[span["font"]] += 1
        doc.close()
    all_fonts_per_bidder[name] = fonts
    print('\n[%s] %d font usages, %d unique fonts' % (name, sum(fonts.values()), len(fonts)))
    for font, count in fonts.most_common(12):
        print('  %s: %d' % (font, count))

print('\n--- Cross-bidder font overlap ---')
for a, b in [('好医助','易可天地'),('好医助','江西正好'),('易可天地','江西正好')]:
    set_a = set(all_fonts_per_bidder[a].keys())
    set_b = set(all_fonts_per_bidder[b].keys())
    common = set_a & set_b
    only_a = set_a - set_b
    print('%s vs %s: %d shared fonts, %d unique to %s' % (a, b, len(common), len(only_a), a))

print('\nDone!')
