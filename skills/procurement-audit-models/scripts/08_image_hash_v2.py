"""L4 v2.0 — 感知哈希（DCT+Hamming）图片同源检测
基于《中国审计》2023年21期 北京市审计局OpenCV查重方法
支持检测: 同一图片的不同扫描/压缩/裁剪版本
"""
import os, sys, struct, hashlib
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

try:
    import numpy as np
    from PIL import Image
    from scipy.fftpack import dct
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install: pip install numpy Pillow scipy")
    sys.exit(1)

# ===== Perceptual Hash (DCT-based) =====

def dct_hash(img_array, hash_bits=128):
    """DCT-based perceptual hash (基于北京市审计局方法)
    
    流程:
    1. 灰度图 → 64x64像素
    2. 分割为8x8个8x8像素块
    3. 每个8x8块做DCT变换
    4. 取前2个低频系数 → 2 bits/块 → 128 bits
    5. 哈明距离比较相似度
    """
    # Resize to 64x64
    img = Image.fromarray(img_array)
    img = img.resize((64, 64), Image.LANCZOS)
    pixels = np.array(img)
    
    bits = []
    # 8x8 blocks of 8x8 pixels each
    for row_block in range(8):
        for col_block in range(8):
            block = pixels[row_block*8:(row_block+1)*8, col_block*8:(col_block+1)*8]
            # DCT transform
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
            # Extract 2 bits from low-frequency components
            # Bit 0: sign of dct_block[0,1] (horizontal edge energy)
            # Bit 1: sign of dct_block[1,0] (vertical edge energy)
            bit0 = 1 if dct_block[0, 1] > 0 else 0
            bit1 = 1 if dct_block[1, 0] > 0 else 0
            bits.append(bit0)
            bits.append(bit1)
    
    # Convert to bytes
    hash_bytes = bytearray()
    for i in range(0, len(bits), 8):
        byte_val = 0
        for j in range(8):
            if i + j < len(bits):
                byte_val = (byte_val << 1) | bits[i + j]
        hash_bytes.append(byte_val)
    
    return bytes(hash_bytes)[:hash_bits // 8]


def standard_phash(img_array, hash_size=8):
    """Standard perceptual hash (industry standard pHash)
    More compact: 64-bit hash, good for quick comparison
    """
    img = Image.fromarray(img_array)
    img = img.convert('L').resize((hash_size * 4, hash_size * 4), Image.LANCZOS)
    pixels = np.array(img, dtype=np.float64)
    
    # DCT
    dct_result = dct(dct(pixels.T, norm='ortho').T, norm='ortho')
    # Take top-left hash_size x hash_size
    dct_low = dct_result[:hash_size, :hash_size]
    # Median threshold
    median = np.median(dct_low)
    # Build hash bits
    diff = dct_low > median
    return diff.flatten()


def hamming_distance(hash1_bytes, hash2_bytes):
    """Compute Hamming distance between two hashes"""
    if isinstance(hash1_bytes, np.ndarray):
        # Boolean array
        return np.sum(hash1_bytes != hash2_bytes)
    else:
        # Byte array
        dist = 0
        for b1, b2 in zip(hash1_bytes, hash2_bytes):
            xor = b1 ^ b2
            dist += bin(xor).count('1')
        # Adjust if lengths differ
        len_diff = abs(len(hash1_bytes) - len(hash2_bytes))
        return dist + len_diff * 8


def similarity(hash1, hash2, bits=128):
    """Compute similarity score (0-1) between two hashes"""
    if isinstance(hash1, np.ndarray):
        # Boolean array (standard pHash)
        dist = hamming_distance(hash1, hash2)
        total_bits = len(hash1)
    else:
        dist = hamming_distance(hash1, hash2)
        total_bits = bits
    return 1.0 - (dist / total_bits)


# ===== PDF Image Extraction =====

def extract_images_from_pdf(pdf_path, max_images_per_page=50):
    """Extract embedded images from PDF using PyMuPDF"""
    try:
        import fitz
    except ImportError:
        print("Missing PyMuPDF: pip install PyMuPDF")
        return []
    
    images = []
    doc = fitz.open(pdf_path)
    
    for pg_num in range(len(doc)):
        if len(images) >= 10000:  # safety limit
            break
        try:
            img_list = doc[pg_num].get_images(full=True)
            for img_info in img_list[:max_images_per_page]:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    try:
                        pil_img = Image.open(io.BytesIO(base_image["image"]))
                        images.append({
                            "page": pg_num + 1,
                            "xref": xref,
                            "width": base_image.get("width"),
                            "height": base_image.get("height"),
                            "ext": base_image.get("ext"),
                            "pil": pil_img
                        })
                    except Exception:
                        pass
        except Exception:
            pass
    
    doc.close()
    return images


# ===== Batch Analysis =====

def analyze_bidder(pdf_path, bidder_name, hash_type="dct"):
    """Extract and hash all images from a bidder's PDF"""
    import io
    results = []
    
    if not os.path.exists(pdf_path):
        print(f"  File not found: {pdf_path}")
        return results
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  Failed to open: {e}")
        return results
    
    img_count = 0
    for pg_num in range(len(doc)):
        if img_count >= 5000:
            break
        try:
            img_list = doc[pg_num].get_images(full=True)
        except Exception:
            continue
        
        for img_info in img_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if not base_image or not base_image.get("image"):
                    continue
                
                pil_img = Image.open(io.BytesIO(base_image["image"]))
                if pil_img.mode not in ('L', 'RGB'):
                    pil_img = pil_img.convert('RGB')
                
                # Convert to grayscale numpy array
                gray = np.array(pil_img.convert('L'))
                
                # Compute hashes
                if hash_type == "dct":
                    phash = dct_hash(gray)
                else:
                    phash = standard_phash(gray)
                
                # Exact hash for reference
                md5 = hashlib.md5(base_image["image"]).hexdigest()
                
                results.append({
                    "bidder": bidder_name,
                    "page": pg_num + 1,
                    "xref": xref,
                    "width": base_image.get("width"),
                    "height": base_image.get("height"),
                    "ext": base_image.get("ext"),
                    "phash": phash,
                    "md5": md5
                })
                img_count += 1
                
            except Exception:
                continue
    
    doc.close()
    return results


def cross_compare(images_by_bidder, threshold=0.80):
    """Compare images across bidders using perceptual hash"""
    matches = []
    bidders = list(images_by_bidder.keys())
    
    for i in range(len(bidders)):
        for j in range(i + 1, len(bidders)):
            a, b = bidders[i], bidders[j]
            imgs_a = images_by_bidder[a]
            imgs_b = images_by_bidder[b]
            
            # Skip if too many (sample)
            if len(imgs_a) * len(imgs_b) > 1000000:
                # Sample comparison
                sample_size = min(100, max(len(imgs_a), len(imgs_b)))
                imgs_a_sample = imgs_a[:sample_size]
                imgs_b_sample = imgs_b[:sample_size]
            else:
                imgs_a_sample = imgs_a
                imgs_b_sample = imgs_b
            
            for img_a in imgs_a_sample:
                for img_b in imgs_b_sample:
                    sim = similarity(img_a["phash"], img_b["phash"])
                    if sim >= threshold:
                        matches.append({
                            "bidder_a": a,
                            "bidder_b": b,
                            "sim": round(sim, 4),
                            "dist": hamming_distance(img_a["phash"], img_b["phash"]) 
                                    if not isinstance(img_a["phash"], np.ndarray) 
                                    else int((1 - sim) * len(img_a["phash"])),
                            "img_a": f"pg{img_a['page']}_x{img_a['xref']}",
                            "img_b": f"pg{img_b['page']}_x{img_b['xref']}",
                            "md5_same": img_a["md5"] == img_b["md5"]
                        })
    
    matches.sort(key=lambda x: -x["sim"])
    return matches


# ===== CLI =====
if __name__ == "__main__":
    import argparse, io
    
    parser = argparse.ArgumentParser(description="L4 v2.0 感知哈希图片同源检测")
    parser.add_argument("--dir", required=True, help="投标文件目录")
    parser.add_argument("--threshold", type=float, default=0.80, help="相似度阈值(默认0.80)")
    parser.add_argument("--hash-type", default="dct", choices=["dct", "standard"],
                        help="哈希算法: dct(128bit) / standard(64bit)")
    
    args = parser.parse_args()
    
    print(f"L4 v2.0 感知哈希检测 (DCT+Hamming)")
    print(f"阈值: {args.threshold}")
    print(f"算法: {args.hash_type}")
    print()
    
    # Extract images and compute hashes
    images_by_bidder = {}
    
    if os.path.isdir(args.dir):
        pdfs = sorted(f for f in os.listdir(args.dir) if f.lower().endswith('.pdf'))
    else:
        pdfs = [os.path.basename(args.dir)]
        args.dir = os.path.dirname(args.dir)
    
    for fname in pdfs:
        path = os.path.join(args.dir, fname)
        bidder_name = fname.replace('.pdf', '').replace('.PDF', '')[:40]
        print(f"Processing: {bidder_name}...", end=" ", flush=True)
        imgs = analyze_bidder(path, bidder_name, args.hash_type)
        images_by_bidder[bidder_name] = imgs
        print(f"{len(imgs)} images")
    
    print(f"\nTotal images: {sum(len(v) for v in images_by_bidder.values())}")
    print(f"Cross-comparing {len(images_by_bidder)} bidders...")
    
    matches = cross_compare(images_by_bidder, args.threshold)
    
    if matches:
        print(f"\n=== Found {len(matches)} similar image pairs ===")
        for m in matches[:50]:
            flag = " [MD5 SAME]" if m["md5_same"] else " [VISUAL ONLY]"
            print(f"  {m['sim']:.4f} [{m['bidder_a']}] ↔ [{m['bidder_b']}] "
                  f"({m['img_a']} ↔ {m['img_b']}){flag}")
    else:
        print("\nNo similar image pairs found above threshold.")
