"""新维度深挖：WPS签名同源比对 + JPEG量化表指纹 + 页面结构模式 + 文件系统时间线"""
import fitz, os, struct, re, hashlib, json
from collections import Counter
from datetime import datetime

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目"

files = {
    '招标文件': os.path.join(BASE, '招标采购文件-ZHH-F〔2025〕85号磋商文件-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目.pdf'),
    '胤皓': os.path.join(BASE, '供应商投标文件', '四川胤皓文化传媒有限公司.pdf'),
    '太格': os.path.join(BASE, '供应商投标文件', '太格电子文档.pdf'),
}

# ==========================================
# 维度A: WPS同源签名比对（胤皓 vs 招标文件）
# ==========================================
print("=" * 60)
print("维度A: WPS签名同源比对")
print("=" * 60)

def extract_wps_signatures(filepath):
    """Extract all WPS-related byte sequences and their contexts"""
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    sigs = []
    # Find WPS signatures with surrounding context
    for pattern, label in [(b'WPS', b'WPS'), (b'wps', b'wps'), (b'Kingsoft', b'Kingsoft')]:
        pos = 0
        while True:
            idx = raw.find(pattern, pos)
            if idx == -1:
                break
            # Get 100 bytes of context
            start = max(0, idx - 30)
            end = min(len(raw), idx + 70)
            ctx = raw[start:end]
            # Extract readable ASCII parts
            readable = ''
            for b in ctx:
                if 32 <= b < 127:
                    readable += chr(b)
                else:
                    readable += '.'
            sigs.append({
                'pattern': label.decode(),
                'offset': idx,
                'context': readable
            })
            pos = idx + 1
    
    return sigs

for name in ['招标文件', '胤皓']:
    path = files[name]
    sigs = extract_wps_signatures(path)
    
    print(f"\n[{name}] WPS相关签名: {len(sigs)}处")
    for s in sigs:
        print(f"  offset={s['offset']:,} [{s['pattern']}]: {s['context']}")

# ==========================================
# 维度B: JPEG量化表指纹比对
# ==========================================
print("\n" + "=" * 60)
print("维度B: JPEG量化表指纹比对")
print("=" * 60)

def extract_jpeg_quant_tables(filepath, max_pages=5):
    """Extract JPEG quantization tables from PDF embedded images"""
    doc = fitz.open(filepath)
    quant_tables = []
    
    pages_to_check = list(range(0, min(3, len(doc)))) + list(range(len(doc)//2, min(len(doc)//2 + 2, len(doc))))
    
    for pg_idx in pages_to_check:
        page = doc[pg_idx]
        for img_info in page.get_images(full=True):
            try:
                img_data = doc.extract_image(img_info[0])
                if img_data.get('ext') != 'jpeg':
                    continue
                img_bytes = img_data['image']
                
                # Parse JPEG markers to find DQT (Define Quantization Table)
                # DQT marker = 0xFF 0xDB
                pos = 0
                tables = []
                while pos < len(img_bytes) - 1:
                    if img_bytes[pos] == 0xFF and img_bytes[pos+1] == 0xDB:
                        # DQT segment
                        seg_len = struct.unpack('>H', img_bytes[pos+2:pos+4])[0]
                        table_id = img_bytes[pos+4] >> 4
                        precision = img_bytes[pos+4] & 0x0F
                        table_data = img_bytes[pos+5:pos+2+seg_len]
                        table_hash = hashlib.md5(table_data).hexdigest()[:12]
                        tables.append({
                            'table_id': table_id,
                            'precision': precision,
                            'hash': table_hash,
                            'first_8': [int(b) for b in table_data[1:9]]
                        })
                        pos += seg_len + 2
                    else:
                        pos += 1
                
                quant_tables.append({
                    'page': pg_idx + 1,
                    'tables': tables,
                    'img_size': len(img_bytes)
                })
                break  # one image per page
            except:
                pass
    doc.close()
    return quant_tables

for name in ['胤皓', '太格']:
    path = files[name]
    print(f"\n[{name}] JPEG量化表:")
    tables = extract_jpeg_quant_tables(path)
    
    # Summarize unique quant table hashes
    all_hashes = set()
    for t in tables:
        for tbl in t['tables']:
            all_hashes.add(tbl['hash'])
    
    print(f"  检查了{len(tables)}页，唯一量化表哈希数: {len(all_hashes)}")
    for t in tables[:3]:
        for tbl in t['tables']:
            print(f"  Page{t['page']} Tbl{tbl['table_id']} precision={tbl['precision']} hash={tbl['hash']} first8={tbl['first_8']}")

# ==========================================
# 维度C: 页面结构模式分析
# ==========================================
print("\n" + "=" * 60)
print("维度C: 页面结构模式")
print("=" * 60)

for name in ['胤皓', '太格']:
    path = files[name]
    doc = fitz.open(path)
    
    # Analyze objects per page, image count per page, content stream size
    page_stats = []
    # Check pages 1-20 and every 20th page
    check_pages = list(range(0, min(20, len(doc)))) + list(range(20, len(doc), 20))
    
    for pg_idx in check_pages:
        page = doc[pg_idx]
        rect = page.rect
        img_count = len(page.get_images())
        # Get content stream size
        contents = page.read_contents()
        if isinstance(contents, int):
            stream_size = contents
        elif isinstance(contents, list):
            stream_size = sum(len(c) for c in contents) if contents else 0
        else:
            stream_size = len(contents) if contents else 0
        
        page_stats.append({
            'page': pg_idx + 1,
            'size': (round(rect.width, 1), round(rect.height, 1)),
            'images': img_count,
            'stream_bytes': stream_size
        })
    
    # Stats
    sizes = [tuple(p['size']) for p in page_stats]
    img_counts = [p['images'] for p in page_stats]
    stream_sizes = [p['stream_bytes'] for p in page_stats]
    
    size_unique = len(set(sizes))
    img_avg = sum(img_counts) / len(img_counts) if img_counts else 0
    stream_avg = sum(stream_sizes) / len(stream_sizes) if stream_sizes else 0
    
    print(f"\n[{name}] 采样{len(page_stats)}页:")
    print(f"  唯一页面尺寸数: {size_unique}")
    print(f"  平均图片数/页: {img_avg:.1f}")
    print(f"  平均内容流大小: {stream_avg:,.0f} bytes")
    print(f"  内容流波动: {min(stream_sizes):,} ~ {max(stream_sizes):,}")
    
    doc.close()

# ==========================================
# 维度D: 文件系统时间线
# ==========================================
print("\n" + "=" * 60)
print("维度D: 文件系统时间线")
print("=" * 60)

for name, path in files.items():
    stat = os.stat(path)
    ctime = datetime.fromtimestamp(stat.st_ctime)
    mtime = datetime.fromtimestamp(stat.st_mtime)
    atime = datetime.fromtimestamp(stat.st_atime)
    size_mb = stat.st_size / (1024*1024)
    
    print(f"\n[{name}] {size_mb:.1f}MB")
    print(f"  创建时间: {ctime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  访问时间: {atime.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# 维度E: 胤皓PDF中WPS签名与招标文件的相似性
# ==========================================
print("\n" + "=" * 60)
print("维度E: 胤皓 vs 招标文件 WPS签名相似度")
print("=" * 60)

# Compare the actual WPS signature byte sequences
sigs_yh = extract_wps_signatures(files['胤皓'])
sigs_zb = extract_wps_signatures(files['招标文件'])

# Extract unique WPS-related strings
def get_wps_strings(sigs):
    strings = set()
    for s in sigs:
        ctx = s['context']
        # Extract continuous alphanumeric strings around WPS
        import re
        found = re.findall(r'[A-Za-z0-9_/.-]{6,}', ctx)
        strings.update(found)
    return strings

yh_strs = get_wps_strings(sigs_yh)
zb_strs = get_wps_strings(sigs_zb)

print(f"  胤皓WPS相关字符串: {len(yh_strs)}")
print(f"  招标文件WPS相关字符串: {len(zb_strs)}")
common = yh_strs & zb_strs
print(f"  共同字符串: {len(common)}")
if common:
    print(f"  共同内容: {list(common)[:10]}")

print("\nDone!")
