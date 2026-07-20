"""Check printer/scanner models from embedded images and scanned PDFs"""
import os, glob, zipfile, struct
from PIL import Image
from PIL.ExifTags import TAGS

def extract_exif_from_image(img_data, label):
    """Try to extract EXIF from image bytes"""
    try:
        from io import BytesIO
        img = Image.open(BytesIO(img_data))
        exif = img._getexif()
        if exif:
            results = {}
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                # Only report interesting tags
                interesting = ['Make', 'Model', 'Software', 'DateTime', 'DateTimeOriginal',
                               'DateTimeDigitized', 'Artist', 'ImageDescription']
                if tag_name in interesting:
                    results[tag_name] = str(value)
            if results:
                print(f'  [{label}] EXIF:')
                for k, v in sorted(results.items()):
                    print(f'    {k}: {v}')
                return results
    except:
        pass
    return None

def check_image_metadata(img_data):
    """Check various image metadata"""
    info = {}
    try:
        from io import BytesIO
        img = Image.open(BytesIO(img_data))
        info['format'] = img.format
        info['mode'] = img.mode
        info['size'] = f'{img.width}x{img.height}'
        # Check for DPI info
        if hasattr(img, 'info'):
            dpi = img.info.get('dpi', None)
            if dpi:
                info['dpi'] = str(dpi)
    except:
        pass
    return info

# ═══════════════════════════════════════
# Part 1: EXIF from .docx embedded images
# ═══════════════════════════════════════
print('='*60)
print('Part 1: Scanner/Device EXIF from .docx Embedded Images')
print('='*60)

exif_findings = {}
for base_dir in [r'C:\Users\scrccpa\Desktop\校服2']:
    for docx_path in glob.glob(os.path.join(base_dir, '**', '*.docx'), recursive=True):
        fsize = os.path.getsize(docx_path)
        if fsize > 200*1024*1024:
            continue
        # Get company label
        parts = docx_path.replace('\\', '/').split('/')
        company = 'unknown'
        for p in parts:
            if '乐吉' in p or '吉玛' in p: company = '乐吉玛帝诺'
            elif '牧森' in p: company = '牧森'
            elif '苏美达' in p or '伊顿' in p: company = '苏美达'
            elif '顺华' in p: company = '顺华'
            elif '博士' in p: company = '弘博士'
        
        bid_type = '资格标' if '资格' in docx_path else '商务标'
        label = f'{company}-{bid_type}'
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                media_files = [f for f in zf.namelist() if f.startswith('word/media/')]
                found_exif = 0
                for mf in media_files[:50]:  # Sample first 50 images
                    data = zf.read(mf)
                    if len(data) < 100:
                        continue
                    r = extract_exif_from_image(data, f'{label}|{os.path.basename(mf)}')
                    if r:
                        found_exif += 1
                        key = company
                        if key not in exif_findings:
                            exif_findings[key] = []
                        exif_findings[key].append({**r, 'file': mf, 'source': docx_path})
                    if found_exif >= 5:  # Enough samples
                        break
        except Exception as e:
            print(f'  Error with {label}: {e}')

print(f'\nEXIF summary by company:')
for company, entries in sorted(exif_findings.items()):
    models = set()
    makes = set()
    softwares = set()
    for e in entries:
        if 'Model' in e: models.add(e['Model'])
        if 'Make' in e: makes.add(e['Make'])
        if 'Software' in e: softwares.add(e['Software'])
    if models:
        print(f'  {company}:')
        print(f'    Camera/Scanner Models: {models}')
        print(f'    Makes: {makes}')
        print(f'    Software: {softwares}')

# ═══════════════════════════════════════
# Part 2: PDF metadata from scanned copies
# ═══════════════════════════════════════
print(f'\n{"="*60}')
print('Part 2: PDF Metadata (Scanned Copies)')
print('='*60)

try:
    import pikepdf
    has_pikepdf = True
except:
    has_pikepdf = False
    print('  pikepdf not available, using PyPDF2 fallback')

for base_dir in [r'C:\Users\scrccpa\Desktop\校服2']:
    for pdf_path in sorted(glob.glob(os.path.join(base_dir, '**', '*.pdf'), recursive=True)):
        fsize = os.path.getsize(pdf_path)
        parts = pdf_path.replace('\\', '/').split('/')
        company = 'unknown'
        for p in parts:
            if '乐吉' in p or '吉玛' in p: company = '乐吉玛帝诺'
            elif '牧森' in p: company = '牧森'
            elif '苏美达' in p or '伊顿' in p: company = '苏美达'
            elif '顺华' in p: company = '顺华'
            elif '博士' in p: company = '弘博士'
        
        fname = os.path.basename(pdf_path)
        bid_type = '资格标' if '资格' in fname else ('商务标' if '商务' in fname else '招标文件')
        label = f'{company}-{bid_type}'
        
        print(f'\n  [{label}] {fname} ({fsize/1024/1024:.1f}MB)')
        
        if has_pikepdf:
            try:
                pdf = pikepdf.open(pdf_path)
                info = pdf.docinfo
                for key in sorted(info.keys()):
                    print(f'    {key}: {info[key]}')
                # Check XMP metadata
                try:
                    xmp = pdf.open_metadata()
                    if xmp:
                        for key in sorted(xmp.keys()):
                            print(f'    XMP {key}: {xmp[key]}')
                except:
                    pass
                pdf.close()
            except Exception as e:
                print(f'    pikepdf error: {e}')
        else:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                meta = reader.metadata
                if meta:
                    for key in sorted(meta.keys()):
                        val = meta[key]
                        if val:
                            print(f'    {key}: {val}')
            except Exception as e:
                print(f'    PyPDF2 error: {e}')

# ═══════════════════════════════════════
# Part 3: Check PNG chunks (textual metadata)
# ═══════════════════════════════════════
print(f'\n{"="*60}')
print('Part 3: PNG Metadata Chunks (iTXt/tEXt/zTXt)')
print('='*60)

def read_png_chunks(data):
    """Read PNG chunk metadata"""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    chunks = {}
    pos = 8
    while pos < len(data) - 12:
        length = struct.unpack_from('>I', data, pos)[0]
        chunk_type = data[pos+4:pos+8].decode('ascii', errors='replace')
        chunk_data = data[pos+8:pos+8+length]
        if chunk_type in ('tEXt', 'zTXt', 'iTXt'):
            try:
                text = chunk_data.decode('latin-1')
                chunks[chunk_type] = text
            except:
                pass
        pos += 12 + length
    return chunks if chunks else None

for base_dir in [r'C:\Users\scrccpa\Desktop\校服2']:
    for docx_path in glob.glob(os.path.join(base_dir, '**', '*.docx'), recursive=True):
        if os.path.getsize(docx_path) > 200*1024*1024: continue
        parts = docx_path.replace('\\', '/').split('/')
        company = 'unknown'
        for p in parts:
            if '乐吉' in p or '吉玛' in p: company = '乐吉玛帝诺'
            elif '牧森' in p: company = '牧森'
            elif '苏美达' in p or '伊顿' in p: company = '苏美达'
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                for mf in zf.namelist():
                    if mf.startswith('word/media/') and mf.lower().endswith('.png'):
                        data = zf.read(mf)
                        chunks = read_png_chunks(data)
                        if chunks:
                            print(f'\n  [{company}] {mf}:')
                            for ctype, text in chunks.items():
                                # Truncate long text
                                display = text[:200] + '...' if len(text) > 200 else text
                                print(f'    {ctype}: {display}')
        except:
            pass

print('\nDone.')
