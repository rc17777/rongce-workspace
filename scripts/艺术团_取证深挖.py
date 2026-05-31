"""数字取证级深挖：文件雕刻 + EXIF深度 + 像素分布 + 重压缩检测 + 文件系统残留"""
import fitz, os, struct, json, hashlib
import numpy as np
from PIL import Image, ExifTags
from collections import Counter
from datetime import datetime

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-55-四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务采购项目"
OUT = r"D:\openclaw-workspace\output\艺术团采购"

files = {
    '胤皓': os.path.join(BASE, '供应商投标文件', '四川胤皓文化传媒有限公司.pdf'),
    '太格': os.path.join(BASE, '供应商投标文件', '太格电子文档.pdf'),
}

# ==========================================
# 1. JPEG文件雕刻 — 验证完整性和APP标记
# ==========================================
print("=" * 60)
print("1. JPEG文件雕刻 — 完整性验证 + APP标记分析")
print("=" * 60)

def analyze_jpeg_bytes(img_bytes):
    """Deep JPEG structure analysis"""
    result = {
        'header_ok': False, 'trailer_ok': False,
        'app_markers': [], 'comments': [],
        'has_exif': False, 'has_xmp': False,
        'has_thumbnail': False, 'dqt_count': 0,
        'sof_info': None, 'size_bytes': len(img_bytes)
    }
    
    # Check SOI (FFD8)
    if img_bytes[:2] == b'\xff\xd8':
        result['header_ok'] = True
    
    # Check EOI (FFD9) - last 2 bytes
    if img_bytes[-2:] == b'\xff\xd9':
        result['trailer_ok'] = True
    
    # Parse markers
    pos = 2
    while pos < len(img_bytes) - 1:
        if img_bytes[pos] != 0xFF:
            pos += 1
            continue
        
        marker = img_bytes[pos + 1]
        if marker == 0xD8:  # SOI (shouldn't appear again)
            pos += 2
            continue
        if marker == 0xD9:  # EOI
            break
        if marker == 0x00:  # Stuffed byte
            pos += 2
            continue
        if marker in [0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7]:  # RST markers
            pos += 2
            continue
        if marker == 0x01:  # TEM
            pos += 2
            continue
        
        # Get segment length
        if pos + 4 > len(img_bytes):
            break
        seg_len = struct.unpack('>H', img_bytes[pos+2:pos+4])[0]
        
        marker_name = f'0xFF{marker:02X}'
        
        if marker == 0xE0:  # APP0 (JFIF)
            result['app_markers'].append('JFIF')
            # Check JFIF version
            if pos + 12 <= len(img_bytes):
                jfif_id = img_bytes[pos+4:pos+9]
                result['jfif_id'] = jfif_id.decode('latin-1', errors='replace')
        
        elif marker == 0xE1:  # APP1 (EXIF)
            result['has_exif'] = True
            result['app_markers'].append('EXIF')
            # Check for thumbnail
            if b'\xff\xd8' in img_bytes[pos+4:pos+seg_len+2]:
                result['has_thumbnail'] = True
        
        elif marker == 0xE2:  # APP2 (ICC/FPXR)
            result['app_markers'].append('ICC')
        
        elif marker == 0xED:  # APP13 (Photoshop/IPTC)
            result['app_markers'].append('Photoshop')
        
        elif marker == 0xEE:  # APP14 (Adobe)
            result['app_markers'].append('Adobe')
        
        elif marker == 0xFE:  # COM (Comment)
            comment_data = img_bytes[pos+4:pos+2+seg_len]
            result['comments'].append(comment_data[:100])
        
        elif marker == 0xDB:  # DQT
            result['dqt_count'] += 1
        
        elif marker in [0xC0, 0xC1, 0xC2]:  # SOF
            if pos + 9 <= len(img_bytes):
                precision = img_bytes[pos+4]
                height = struct.unpack('>H', img_bytes[pos+5:pos+7])[0]
                width = struct.unpack('>H', img_bytes[pos+7:pos+9])[0]
                result['sof_info'] = {'precision': precision, 'width': width, 'height': height}
        
        pos += seg_len + 2
    
    return result

for name, path in files.items():
    doc = fitz.open(path)
    print(f"\n[{name}]")
    
    # Sample pages: first, middle, last
    pages = [0, len(doc)//2, len(doc)-1]
    jpeg_stats = []
    
    for pg_idx in pages:
        page = doc[pg_idx]
        for img_info in page.get_images(full=True):
            try:
                img_raw = doc.extract_image(img_info[0])
                img_bytes = img_raw['image']
                analysis = analyze_jpeg_bytes(img_bytes)
                jpeg_stats.append(analysis)
            except:
                pass
    
    # Aggregate
    if jpeg_stats:
        header_ok = sum(1 for s in jpeg_stats if s['header_ok'])
        trailer_ok = sum(1 for s in jpeg_stats if s['trailer_ok'])
        exif_count = sum(1 for s in jpeg_stats if s['has_exif'])
        thumbnail_count = sum(1 for s in jpeg_stats if s['has_thumbnail'])
        comments_count = sum(1 for s in jpeg_stats if s['comments'])
        
        print(f"  采样{len(jpeg_stats)}张JPEG:")
        print(f"    头部(FFD8)完整: {header_ok}/{len(jpeg_stats)}")
        print(f"    尾部(FFD9)完整: {trailer_ok}/{len(jpeg_stats)}")
        print(f"    含EXIF: {exif_count}/{len(jpeg_stats)}")
        print(f"    含缩略图: {thumbnail_count}/{len(jpeg_stats)}")
        print(f"    含注释: {comments_count}/{len(jpeg_stats)}")
        print(f"    DQT表: {jpeg_stats[0]['dqt_count']}个")
        
        if jpeg_stats[0].get('jfif_id'):
            print(f"    JFIF标识: {jpeg_stats[0]['jfif_id']}")
        if jpeg_stats[0].get('sof_info'):
            print(f"    SOF: {jpeg_stats[0]['sof_info']}")
        
        # Show APP markers
        app_markers = jpeg_stats[0]['app_markers']
        print(f"    APP标记: {app_markers if app_markers else '无'}")
        
        # Show any comments
        for s in jpeg_stats:
            for c in s['comments']:
                try:
                    readable = c.decode('utf-8', errors='replace')
                    if readable.strip():
                        print(f"    注释内容: {readable[:200]}")
                except:
                    pass
    
    doc.close()

# ==========================================
# 2. 像素分布统计分析
# ==========================================
print("\n" + "=" * 60)
print("2. 像素分布统计 — 亮度直方图特征")
print("=" * 60)

for name, path in files.items():
    doc = fitz.open(path)
    print(f"\n[{name}]")
    
    # Sample first, middle, last page at 150 dpi
    pages = [0, len(doc)//2, len(doc)-1]
    
    for pg_idx in pages:
        page = doc[pg_idx]
        pix = page.get_pixmap(dpi=100)
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        arr = np.array(img)
        
        # Per-channel statistics
        mean_r = arr[:,:,0].mean()
        mean_g = arr[:,:,1].mean()
        mean_b = arr[:,:,2].mean()
        std_r = arr[:,:,0].std()
        std_g = arr[:,:,1].std()
        std_b = arr[:,:,2].std()
        
        # Grayscale histogram skewness
        gray = np.mean(arr, axis=2)
        skew = ((gray - gray.mean()) ** 3).mean() / (gray.std() ** 3) if gray.std() > 0 else 0
        
        # Edge density (simple gradient)
        edges_h = np.abs(np.diff(gray, axis=1)).mean()
        edges_v = np.abs(np.diff(gray, axis=0)).mean()
        edge_density = (edges_h + edges_v) / 2
        
        # Percentage of near-white pixels (>240)
        white_pct = (gray > 240).mean() * 100
        
        # Percentage of near-black pixels (<30)
        black_pct = (gray < 30).mean() * 100
        
        print(f"  Page{pg_idx+1}: Rmean={mean_r:.1f} Gmean={mean_g:.1f} Bmean={mean_b:.1f} "
              f"Rstd={std_r:.1f} Gstd={std_g:.1f} Bstd={std_b:.1f} "
              f"Skew={skew:.2f} Edge={edge_density:.1f} "
              f"White%={white_pct:.1f} Black%={black_pct:.1f}")
    
    doc.close()

# ==========================================
# 3. 文件系统残留信息挖掘
# ==========================================
print("\n" + "=" * 60)
print("3. 文件系统残留挖掘")
print("=" * 60)

target_dir = os.path.join(BASE, '供应商投标文件')
print(f"\n目录: {target_dir}")
print(f"文件系统: NTFS (Windows)")

# Check all files in directory including hidden/system
for item in os.listdir(target_dir):
    full_path = os.path.join(target_dir, item)
    stat = os.stat(full_path)
    
    ctime = datetime.fromtimestamp(stat.st_ctime)
    mtime = datetime.fromtimestamp(stat.st_mtime)
    atime = datetime.fromtimestamp(stat.st_atime)
    size = stat.st_size
    
    # Windows file attributes
    try:
        attrs = os.popen(f'attrib "{full_path}"').read().strip()
    except:
        attrs = '?'
    
    # Check for alternate data streams (NTFS ADS)
    has_ads = False
    try:
        import subprocess
        result = subprocess.run(
            ['powershell', '-Command', 
             f'Get-Item -Path "{full_path}" -Stream * | Select-Object -ExpandProperty Stream'],
            capture_output=True, text=True, timeout=5
        )
        streams = result.stdout.strip().split('\n')
        has_ads = len(streams) > 1  # More than just :$DATA
        if has_ads:
            print(f"\n  ⚠️  {item}: NTFS备用数据流(ADS)已检测!")
            for s in streams:
                if s.strip():
                    print(f"     流: {s.strip()}")
    except:
        pass
    
    print(f"  {item}: size={size:,} ctime={ctime} mtime={mtime} attrs={attrs} ADS={'有!' if has_ads else '无'}")
    
    # Check for known file signatures in the raw file (file carving)
    if item.endswith('.pdf'):
        with open(full_path, 'rb') as f:
            header = f.read(20)
        # Check if it's really a PDF or something else disguised as .pdf
        if header[:4] != b'%PDF':
            print(f"    ⚠️  文件头不匹配! 非有效PDF! 实际头部: {header[:20].hex()}")

# ==========================================
# 4. DCT系数重压缩检测 (查找"双重JPEG"痕迹)
# ==========================================
print("\n" + "=" * 60)
print("4. DCT重压缩检测 — 检测'JPEG→编辑→再保存为JPEG'痕迹")
print("=" * 60)

# Method: Check if DCT coefficients show double quantization artifacts
# This would indicate the JPEG was decompressed and recompressed
# Simplification: check JPEG restart markers (RST) count - excessive RST = likely re-encoded

for name, path in files.items():
    doc = fitz.open(path)
    print(f"\n[{name}]")
    
    for pg_idx in [0, len(doc)//2]:
        page = doc[pg_idx]
        for img_info in page.get_images(full=True):
            try:
                img_raw = doc.extract_image(img_info[0])
                img_bytes = img_raw['image']
                
                # Count restart markers
                rst_count = 0
                pos = 0
                while pos < len(img_bytes) - 1:
                    if img_bytes[pos] == 0xFF and img_bytes[pos+1] in [0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7]:
                        rst_count += 1
                    pos += 1
                
                # Count Huffman tables (DHT)
                dht_count = img_bytes.count(b'\xff\xc4')
                
                # Estimate JPEG compression quality from quantization table
                # Extract first DQT luminance table
                dqt_pos = img_bytes.find(b'\xff\xdb')
                if dqt_pos >= 0 and dqt_pos + 70 < len(img_bytes):
                    # First Q-table values
                    qtable = img_bytes[dqt_pos+5:dqt_pos+69]
                    q_values = [b for b in qtable]
                    if len(q_values) >= 8:
                        # Standard quality estimation
                        q_sum = sum(q_values[:8])
                        # Higher sum = lower quality (more compression)
                        # WPS "medium" ~ 40-60, RICOH "standard" ~ 25-35
                        print(f"  Page{pg_idx+1}: RST={rst_count} DHT={dht_count} "
                              f"Q-sum={q_sum} Q-first8={q_values[:8]}")
                else:
                    print(f"  Page{pg_idx+1}: RST={rst_count} DHT={dht_count} (no DQT found)")
            except:
                pass
    doc.close()

# ==========================================
# 5. 搜索隐藏文件/缩略图数据库
# ==========================================
print("\n" + "=" * 60)
print("5. 搜索缩略图缓存和临时文件")
print("=" * 60)

# Windows thumbnail cache and Office temp files
import glob

# Check for Thumbs.db
thumbs_paths = [
    os.path.join(target_dir, 'Thumbs.db'),
    os.path.join(BASE, 'Thumbs.db'),
]

for tp in thumbs_paths:
    if os.path.exists(tp):
        stat = os.stat(tp)
        print(f"  发现Thumbs.db: {tp} ({stat.st_size} bytes, mtime={datetime.fromtimestamp(stat.st_mtime)})")
    else:
        print(f"  无Thumbs.db: {tp}")

# Check for ~$ temp files
temp_files = glob.glob(os.path.join(BASE, '**', '~$*'), recursive=True)
if temp_files:
    print(f"  Office临时文件(~$): {len(temp_files)}个")
    for tf in temp_files:
        print(f"    {tf}")
else:
    print(f"  无Office临时文件(~$)")

print("\nDone!")
