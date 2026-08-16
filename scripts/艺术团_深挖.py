"""深挖维度：内部结构指纹 + XMP残留 + 扫描EXIF + 图像特征"""
import fitz, os, hashlib, json, struct, re
from PIL import Image
from collections import Counter

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目"
OUT = r"D:\openclaw-workspace\output\艺术团采购"

files = {
    '招标文件': os.path.join(BASE, '招标采购文件-ZHH-F〔2025〕85号磋商文件-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目.pdf'),
    '胤皓': os.path.join(BASE, '供应商投标文件', '四川胤皓文化传媒有限公司.pdf'),
    '太格': os.path.join(BASE, '供应商投标文件', '太格电子文档.pdf'),
}

# ================================
# 维度1: PDF内部对象结构指纹
# ================================
print("=" * 60)
print("维度1: PDF内部对象结构指纹")
print("=" * 60)

for name, path in files.items():
    doc = fitz.open(path)
    
    # Get document-level stats
    xref_len = doc.xref_length()
    
    # Count object types
    obj_types = Counter()
    for xref in range(1, xref_len):
        try:
            obj_type = doc.xref_object(xref)
            if 'stream' in obj_type.lower():
                obj_types['Stream'] += 1
            elif 'dictionary' in obj_type.lower() or '<<' in obj_type:
                obj_types['Dict'] += 1
            else:
                obj_types['Other'] += 1
        except:
            obj_types['Error'] += 1
    
    # Check for WPS signatures in raw PDF
    doc2 = doc  # keep for later
    doc.close()
    
    # Read raw PDF bytes for string patterns
    with open(path, 'rb') as f:
        raw = f.read(4096)  # First 4KB has most metadata
    
    # WPS signatures
    wps_sigs = []
    for sig in [b'WPS', b'wps', b'Kingsoft', b'kingsoft', b'KSO', b'kso']:
        if sig in raw:
            wps_sigs.append(sig.decode('latin-1'))
    
    # Check for XMP metadata stream
    has_xmp = b'xmp' in raw.lower() or b'XMP' in raw
    has_metadata_stream = b'/Metadata' in raw
    
    # Check PDF version
    version_match = re.search(rb'%PDF-(\d+\.\d+)', raw)
    pdf_version = version_match.group(1).decode() if version_match else '?'
    
    # Look for document ID (unique identifier)
    doc_id_match = re.search(rb'/ID\s*\[<([^>]+)><([^>]+)>\]', raw, re.DOTALL)
    doc_id = doc_id_match.group(1).decode()[:32] if doc_id_match else 'N/A'
    
    print(f"\n[{name}]")
    print(f"  PDF版本: {pdf_version}")
    print(f"  对象数: {xref_len}")
    print(f"  对象类型: {dict(obj_types)}")
    print(f"  文档ID: {doc_id}")
    print(f"  WPS签名: {wps_sigs if wps_sigs else '无'}")
    print(f"  XMP流: {'有' if has_xmp else '无'}")
    print(f"  /Metadata引用: {'有' if has_metadata_stream else '无'}")

# ================================
# 维度2: 页面图像特征对比
# ================================
print("\n" + "=" * 60)
print("维度2: 页面图像特征对比")
print("=" * 60)

for name, path in files.items():
    if name == '招标文件':
        continue
    doc = fitz.open(path)
    
    # Sample first, middle, last pages
    pages_sample = [0, len(doc)//2, len(doc)-1] if len(doc) > 2 else [0]
    
    page_sizes = []
    img_formats = Counter()
    
    for pg_idx in pages_sample:
        page = doc[pg_idx]
        rect = page.rect
        page_sizes.append((rect.width, rect.height))
        
        # Check image formats on this page
        for img_info in page.get_images(full=True):
            try:
                img_data = doc.extract_image(img_info[0])
                fmt = img_data.get('ext', '?')
                img_formats[fmt] += 1
            except:
                pass
    
    # Analyze image properties on first page
    page0 = doc[0]
    pix = page0.get_pixmap(dpi=72)
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    
    # Image statistics
    import numpy as np
    arr = np.array(img)
    mean_val = arr.mean()
    std_val = arr.std()
    
    # Check color mode
    img_mode = img.mode
    
    print(f"\n[{name}]")
    print(f"  页面尺寸: {page_sizes}")
    print(f"  图片格式: {dict(img_formats)}")
    print(f"  首页尺寸: {pix.width}x{pix.height}")
    print(f"  首页模式: {img_mode}, 均值={mean_val:.1f}, 标准差={std_val:.1f}")
    
    doc.close()

# ================================
# 维度3: 太格扫描仪EXIF信息
# ================================
print("\n" + "=" * 60)
print("维度3: 太格 RICOH扫描仪详细分析")
print("=" * 60)

import pdfplumber
path_tg = files['太格']
try:
    doc = fitz.open(path_tg)
    # Extract image from first page with full metadata
    for pg in [0, 25, 50]:
        page = doc[pg]
        for img_info in page.get_images(full=True):
            try:
                img_raw = doc.extract_image(img_info[0])
                ext = img_raw.get('ext', '?')
                w = img_raw.get('width', 0)
                h = img_raw.get('height', 0)
                colorspace = img_raw.get('colorspace', 0)
                cs_name = img_raw.get('cs-name', '?')
                xres = img_raw.get('xres', 0)
                yres = img_raw.get('yres', 0)
                
                # Try to extract EXIF from JPEG data
                img_bytes = img_raw['image']
                has_exif = b'Exif' in img_bytes[:100]
                has_jfif = b'JFIF' in img_bytes[:10]
                
                # JPEG quality estimation
                if ext == 'jpeg':
                    size_bytes = len(img_bytes)
                    px_count = w * h
                    bpp = (size_bytes * 8) / px_count if px_count > 0 else 0
                else:
                    bpp = 0
                
                print(f"  Page{pg+1}: {ext} {w}x{h} cs={cs_name}({colorspace}) dpi={xres}x{yres} bpp={bpp:.2f} EXIF={'Y' if has_exif else 'N'} JFIF={'Y' if has_jfif else 'N'} size={size_bytes}bytes")
                
                # Try parse JFIF data
                if has_jfif:
                    jfif_start = img_bytes.find(b'JFIF')
                    jfif_seg = img_bytes[jfif_start:jfif_start+50]
                    # JFIF version is at offset 5-6
                    if len(jfif_seg) > 7:
                        jfif_ver = f'{jfif_seg[5]}.{jfif_seg[6]:02d}'
                        print(f"    JFIF version: {jfif_ver}")
                        # Density units and values
                        if len(jfif_seg) > 13:
                            units = jfif_seg[7]
                            xd = int.from_bytes(jfif_seg[8:10], 'big')
                            yd = int.from_bytes(jfif_seg[10:12], 'big')
                            units_name = {0:'无单位', 1:'dpi', 2:'dpcm'}.get(units, f'未知({units})')
                            print(f"    Density: {xd}x{yd} {units_name}")
                
                break  # Only first image per page
            except Exception as e:
                print(f"  Page{pg+1}: Error - {e}")
    doc.close()
except Exception as e:
    print(f"  Error: {e}")

# ================================
# 维度4: 胤皓PDF深层结构 — 找WPS残留
# ================================
print("\n" + "=" * 60)
print("维度4: 胤皓PDF深层结构 — WPS残留检测")
print("=" * 60)

path_yh = files['胤皓']
with open(path_yh, 'rb') as f:
    full_raw = f.read()

# Search for WPS traces throughout the file (not just first 4KB)
wps_traces = []
for sig, label in [
    (b'WPS', 'WPS Office'),
    (b'Kingsoft', 'Kingsoft'),
    (b'wps', 'wps lowercase'),
    (b'WPSOffice', 'WPSOffice'),
    (b'KSOFFICE', 'KSOFFICE'),
    (b'writerperfect', 'WriterPerfect'),
    (b'LibreOffice', 'LibreOffice'),
    (b'Microsoft', 'Microsoft Word'),
    (b'Word.Document', 'Word Document OLE'),
    (b'/Producer', 'Producer entry'),
    (b'/Creator', 'Creator entry'),
    (b'pdfmake', 'pdfmake'),
    (b'iText', 'iText'),
    (b'PyPDF', 'PyPDF'),
    (b'ReportLab', 'ReportLab'),
    (b'Ghostscript', 'Ghostscript'),
    (b'Adobe', 'Adobe'),
    (b'/Author', 'Author entry raw'),
    (b'/CreationDate', 'CreationDate raw'),
]:
    count = full_raw.count(sig)
    if count > 0:
        wps_traces.append(f'{label}: {count} occurrences')

print(f'  文件大小: {len(full_raw):,} bytes')
print(f'  签名检测:')
for t in wps_traces[:20]:
    print(f'    {t}')

# Check for PDF linearization
is_linearized = full_raw[:20].startswith(b'%PDF-') and b'/Linearized' in full_raw[:500]
print(f'  线性化(Web优化): {"是" if is_linearized else "否"}')

# Check PDF trailer for incremental updates
trailer_count = full_raw.count(b'startxref')
print(f'  startxref出现次数: {trailer_count} (多次=增量保存)')

# Check if PDF contains text streams despite appearing as scanned
text_stream_count = full_raw.count(b'/Subtype /Text')
print(f'  文本流/Subtype /Text: {text_stream_count}')

# Look for BT...ET text blocks (text blocks in content streams)
bt_blocks = len(re.findall(rb'BT\s.*?ET', full_raw, re.DOTALL))
print(f'  BT...ET文本块: {bt_blocks}')

# ================================
# 维度5: 同章节内容OCR对照
# ================================
print("\n" + "=" * 60)
print("维度5: 胤皓 vs 太格 同章节内容OCR对照")
print("=" * 60)

import pytesseract

def ocr_quick(doc, pg_idx):
    page = doc[pg_idx]
    pix = page.get_pixmap(dpi=100)
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img, lang='chi_sim', config='--psm 6').strip()
    return text

doc_yh = fitz.open(files['胤皓'])
doc_tg = fitz.open(files['太格'])

# We know the structure: 胤皓 pg1=cover, pg2=TOC, pg3=似有项目经验列表, pg4=磋商承诺函
# 太格 pages need similar discovery

# Check parallel sections:
# 胤皓 pg4 = 磋商承诺函, find parallel in 太格
print("\n[胤皓 pg4: 磋商承诺函]")
yh_p4 = ocr_quick(doc_yh, 3)
print(yh_p4[:400])

print("\n--- Looking for 承诺函 in 太格 ---")
for pg in range(len(doc_tg)):
    text = ocr_quick(doc_tg, pg)
    if '承诺函' in text or '承诺' in text[:100]:
        print(f"\n[太格 pg{pg+1}: 含'承诺'关键字]")
        print(text[:400])
        break

# Check project experience sections
print("\n[胤皓 pg3: 项目经验列表]")
yh_p3 = ocr_quick(doc_yh, 2)
print(yh_p3[:400])

print("\n--- Looking for project experience in 太格 ---")
for pg in range(min(10, len(doc_tg))):
    text = ocr_quick(doc_tg, pg)
    if any(kw in text for kw in ['项目','合同','业绩','案例','2022','2023','2024','2025']):
        print(f"\n[太格 pg{pg+1}: 项目/业绩相关]")
        print(text[:400])
        break

doc_yh.close()
doc_tg.close()

print("\n" + "=" * 60)
print("维度6: 最终判断")
print("=" * 60)
print("""
分析总结:
1. 主动清除元数据=行为证据：正常投标人不会清除元数据，此行为本身就是可疑信号
2. 胤皓全图PDF vs 太格物理扫描 vs 立美损坏：三种规避方式互补，形成检测盲区
3. WPS识别: 如胤皓PDF内部有WPS签名残留但元数据被清空，则证明人为干预
4. 关键行动: 调取原始.docx文件可终结性证明文件同源性
""")
