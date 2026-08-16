# -*- coding: utf-8 -*-
"""TF-IDF文本雷同检测 + 嵌入图片哈希比对"""
import os, re, glob, hashlib, zipfile, io, struct, json
from pathlib import Path
from collections import Counter

# ═══════════════════════════════════════
# Part 1: TF-IDF Text Similarity
# ═══════════════════════════════════════

# 1a. Extract 顺华 qualification bid text
def extract_qual_text(fpath):
    """Extract text from qualification bid .docx (real ZIP)"""
    try:
        import zipfile
        with zipfile.ZipFile(fpath, 'r') as zf:
            # Try to find document.xml
            if 'word/document.xml' in zf.namelist():
                xml = zf.read('word/document.xml').decode('utf-8')
                # Strip XML tags
                text = re.sub(r'<[^>]+>', ' ', xml)
                text = re.sub(r'\s+', ' ', text).strip()
                return text
    except:
        pass
    return None

# Read existing texts
txt_dir = r'D:\openclaw-workspace\output\校服分析\txt'
texts = {}
for f in os.listdir(txt_dir):
    if '资格' not in f:
        continue
    fpath = os.path.join(txt_dir, f)
    with open(fpath, 'r', encoding='utf-8') as fh:
        content = fh.read()
    # Determine company name
    if '乐吉玛帝诺' in f or '吉玛' in f:
        texts['乐吉玛帝诺'] = content
    elif '牧森' in f:
        texts['牧森'] = content
    elif '苏美达' in f or '伊顿纪德' in f:
        texts['苏美达伊顿纪德'] = content

# Extract 顺华
shunhua_paths = glob.glob(r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\成都顺华服装有限公司\*资格*')
if not shunhua_paths:
    shunhua_paths = glob.glob(r'C:\Users\scrccpa\Desktop\校服\*\*\*\顺华*\资格*')

for sp in shunhua_paths:
    text = extract_qual_text(sp)
    if text and len(text) > 100:
        texts['顺华'] = text
        print(f'[顺华资格标] Extracted {len(text)} chars')
        break

# Also try extracting text from the .doc using zipfile for 顺华
if '顺华' not in texts:
    # Try from 校服 dir
    for sp in glob.glob(r'C:\Users\scrccpa\Desktop\校服\**\*顺华*\资格*', recursive=True):
        text = extract_qual_text(sp)
        if text and len(text) > 100:
            texts['顺华'] = text
            print(f'[顺华资格标] Extracted {len(text)} chars from alternate path')
            break

# 1b. TF-IDF computation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd

print(f'\n=== Available qualification bid texts: {list(texts.keys())} ===')
for name, t in texts.items():
    print(f'  {name}: {len(t)} chars')

# Run TF-IDF
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
names = sorted(texts.keys())
corpus = [texts[n] for n in names]

try:
    tfidf_matrix = vectorizer.fit_transform(corpus)
    sim_matrix = cosine_similarity(tfidf_matrix)
except Exception as e:
    print(f'TF-IDF error: {e}')
    sim_matrix = np.eye(len(names))

print('\n=== TF-IDF Cosine Similarity Matrix ===')
print(f'{"":>16} ' + ' '.join(f'{n:>12}' for n in names))
for i, name in enumerate(names):
    row = ' '.join(f'{sim_matrix[i][j]:>12.4f}' for j in range(len(names)))
    print(f'{name:>16} {row}')

# 1c. Top-K similar paragraph detection
print('\n=== Top-5 Most Similar Sentence Pairs (Cross-Company) ===')
# Simple approach: split into paragraphs, find most similar pairs
paragraphs_by_company = {}
for name, text in texts.items():
    # Split by newlines, keep paragraphs > 50 chars
    paras = [p.strip() for p in re.split(r'\n+', text) if len(p.strip()) > 50]
    paragraphs_by_company[name] = paras

# Create TF-IDF for paragraphs
all_paras = []
para_map = []
for name in names:
    for p in paragraphs_by_company[name]:
        all_paras.append(p)
        para_map.append((name, p[:80]))

if len(all_paras) >= 2:
    try:
        para_vecs = vectorizer.transform(all_paras)
        para_sim = cosine_similarity(para_vecs)
        # Find top cross-company matches
        matches = []
        for i in range(len(all_paras)):
            for j in range(i+1, len(all_paras)):
                ci, cj = para_map[i][0], para_map[j][0]
                if ci != cj and para_sim[i][j] > 0.5:
                    matches.append((para_sim[i][j], ci, cj, all_paras[i][:100], all_paras[j][:100]))
        matches.sort(reverse=True)
        for sim, ci, cj, p1, p2 in matches[:10]:
            print(f'  [{sim:.3f}] {ci} vs {cj}')
            print(f'    A: {p1}')
            print(f'    B: {p2}')
            print()
    except Exception as e:
        print(f'  Paragraph comparison error: {e}')

# ═══════════════════════════════════════
# Part 2: Embedded Image Hash Comparison
# ═══════════════════════════════════════
print('\n' + '='*60)
print('Part 2: Embedded Image Hash Comparison')
print('='*60)

def extract_images_from_docx(docx_path, label):
    """Extract all images from a .docx file and compute hashes"""
    images = {}
    try:
        with zipfile.ZipFile(docx_path, 'r') as zf:
            media_files = [f for f in zf.namelist() if f.startswith('word/media/')]
            for mf in media_files:
                data = zf.read(mf)
                md5 = hashlib.md5(data).hexdigest()
                sha1 = hashlib.sha1(data).hexdigest()
                size = len(data)
                # Detect image type
                if data[:4] == b'\x89PNG':
                    img_type = 'PNG'
                elif data[:2] == b'\xff\xd8':
                    img_type = 'JPEG'
                elif data[:4] == b'RIFF':
                    img_type = 'WEBP'
                elif data[:2] == b'BM':
                    img_type = 'BMP'
                else:
                    img_type = f'UNKNOWN({data[:4].hex()})'
                key = f'{label}|{os.path.basename(mf)}'
                images[key] = {'md5': md5, 'sha1': sha1, 'size': size, 'type': img_type, 'filename': os.path.basename(mf)}
        return images
    except Exception as e:
        print(f'  Error reading {label}: {e}')
        return {}

# Find all .docx files in both directories
all_images = {}
for base_dir in [r'C:\Users\scrccpa\Desktop\校服2', r'C:\Users\scrccpa\Desktop\校服']:
    for docx_path in glob.glob(os.path.join(base_dir, '**', '*.docx'), recursive=True):
        # Skip very large files (>200MB)
        if os.path.getsize(docx_path) > 200 * 1024 * 1024:
            continue
        # Determine company label from path
        parts = docx_path.replace('\\', '/').split('/')
        # Find company name in path
        label = 'unknown'
        for p in parts:
            if '乐吉' in p or '吉玛' in p:
                label = '乐吉玛帝诺'
            elif '牧森' in p:
                label = '牧森'
            elif '苏美达' in p or '伊顿' in p:
                label = '苏美达伊顿纪德'
            elif '顺华' in p:
                label = '顺华'
            elif '弘博士' in p or '博士' in p:
                label = '弘博士'

        bid_type = '资格标' if '资格' in docx_path else '商务标'
        file_label = f'{label}-{bid_type}'
        print(f'  Processing: {file_label} ({os.path.getsize(docx_path)/1024/1024:.1f}MB)')
        imgs = extract_images_from_docx(docx_path, file_label)
        all_images.update(imgs)

print(f'\nTotal images extracted: {len(all_images)}')
for k, v in sorted(all_images.items()):
    print(f'  [{v["type"]:>5}] {v["size"]:>8} bytes  {v["md5"]}  {k}')

# Cross-company MD5 match detection
print('\n=== Cross-Company Image Duplicates (MD5 Match) ===')
md5_map = {}
for key, info in all_images.items():
    md5 = info['md5']
    if md5 not in md5_map:
        md5_map[md5] = []
    md5_map[md5].append(key)

duplicate_count = 0
for md5, keys in md5_map.items():
    if len(keys) >= 2:
        # Check if different company (or same company but different bid type)
        companies = set(k.split('-')[0] for k in keys)
        if len(companies) >= 2:
            duplicate_count += 1
            print(f'\n  MD5: {md5}')
            info = all_images[keys[0]]
            print(f'  Type: {info["type"]}, Size: {info["size"]} bytes, File: {info["filename"]}')
            print(f'  Cross-company match:')
            for k in sorted(keys):
                print(f'    - {k}')
        else:
            # Same company, different bid types (qual vs business)
            if len(set(k.split('-')[1] for k in keys)) >= 2:
                duplicate_count += 1
                print(f'\n  Same Company, Different Bid Type:')
                print(f'  MD5: {md5}, Type: {all_images[keys[0]]["type"]}')
                for k in sorted(keys):
                    print(f'    - {k}')

if duplicate_count == 0:
    print('  None found - all images are unique across companies.')
else:
    print(f'\n  Total duplicate groups: {duplicate_count}')

# Summary stats
print('\n=== Summary ===')
for company in ['乐吉玛帝诺', '牧森', '苏美达伊顿纪德', '顺华', '弘博士']:
    company_imgs = [k for k in all_images if company in k]
    if company_imgs:
        unique_md5s = len(set(all_images[k]['md5'] for k in company_imgs))
        print(f'  {company}: {len(company_imgs)} images, {unique_md5s} unique MD5s')
