#!/usr/bin/env python3
"""
7家公司「投标人认为应当提供的其他材料.pdf」逐项雷同内容提取 v4
TF-IDF全文向量化 + 逐句匹配 — 高效精确
"""
import os, sys, re, io, warnings
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber
from collections import defaultdict

warnings.filterwarnings('ignore')
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = r"C:\Users\scrccpa\Desktop\新建文件夹"
TARGET_FILE = "投标人认为应当提供的其他材料.pdf"
OUTPUT = os.path.join(BASE_DIR, "其他材料_逐项雷同明细.xlsx")

# === 1. 提取文本 ===
print("=" * 70)
print("  逐项雷同内容提取（TF-IDF句子匹配）")
print("=" * 70)

comp_sentences = {}    # {公司名: [原始句子]}
comp_raw_text = {}

for entry in sorted(os.listdir(BASE_DIR)):
    entry_path = os.path.join(BASE_DIR, entry)
    if not os.path.isdir(entry_path):
        continue
    comp_name = re.sub(r'\(包\d+\)', '', entry).strip()
    fpath = os.path.join(entry_path, TARGET_FILE)
    if not os.path.exists(fpath):
        continue
    try:
        with pdfplumber.open(fpath) as pdf:
            parts = []
            for page in pdf.pages:
                t = page.extract_text()
                if t and len(t.strip()) > 15:
                    parts.append(t.strip())
        raw = '\n'.join(parts)
        comp_raw_text[comp_name] = raw
        
        # 按句号、分号、换行分句
        sents = re.split(r'[。；;]\s*|\n{2,}', raw)
        valid = []
        for s in sents:
            s = s.strip()
            clean = re.sub(r'\s+', '', s)
            if len(clean) >= 20:
                valid.append(s)
        comp_sentences[comp_name] = valid
        print(f"   {comp_name}: {len(valid)} 句")
    except Exception as e:
        print(f"   [错误] {comp_name}: {e}")

comp_names = sorted(comp_sentences.keys())
short_names = {c: c.replace('有限公司', '').replace('有限责任公司', '') for c in comp_names}

# === 2. 构建全局句子TF-IDF矩阵 ===
print(f"\n[1/4] 构建TF-IDF句子矩阵...")

all_sentences = []      # 所有句子
sent_meta = []          # [(公司名, 原始句, 句子索引)]
for name in comp_names:
    for si, sent in enumerate(comp_sentences[name]):
        all_sentences.append(sent)
        sent_meta.append((name, sent, si))

print(f"   总计 {len(all_sentences)} 句")

vectorizer = TfidfVectorizer(
    analyzer='char_wb',
    ngram_range=(2, 4),
    max_features=4000,
    lowercase=False
)
tfidf_matrix = vectorizer.fit_transform(all_sentences)
print(f"   TF-IDF矩阵: {tfidf_matrix.shape}")

# === 3. 逐对匹配 ===
print(f"\n[2/4] 逐对匹配高相似度句子...")
SIM_THRESHOLD = 0.85

all_items = []
pair_summary = []

for i in range(len(comp_names)):
    for j in range(i + 1, len(comp_names)):
        name_a, name_b = comp_names[i], comp_names[j]
        
        # 获取两家公司的句子索引
        idx_a = [k for k, m in enumerate(sent_meta) if m[0] == name_a]
        idx_b = [k for k, m in enumerate(sent_meta) if m[0] == name_b]
        
        if not idx_a or not idx_b:
            continue
        
        # 提取子矩阵计算相似度
        sub_a = tfidf_matrix[idx_a]
        sub_b = tfidf_matrix[idx_b]
        
        # 分块计算避免内存爆炸
        batch_size = 200
        matched = []
        
        for start in range(0, len(idx_a), batch_size):
            end = min(start + batch_size, len(idx_a))
            batch = sub_a[start:end]
            sims = cosine_similarity(batch, sub_b)
            
            for bi in range(sims.shape[0]):
                best_j = np.argmax(sims[bi])
                best_sim = sims[bi][best_j]
                if best_sim >= SIM_THRESHOLD:
                    global_i = idx_a[start + bi]
                    global_j = idx_b[best_j]
                    matched.append((
                        sent_meta[global_i][1],   # 原始句A
                        sent_meta[global_j][1],   # 原始句B
                        best_sim
                    ))
        
        matched.sort(key=lambda x: x[2], reverse=True)
        
        max_sents = max(len(idx_a), len(idx_b))
        overlap = round(len(matched) / max_sents * 100, 1) if max_sents > 0 else 0
        avg_sim = round(sum(m[2] for m in matched) / len(matched) * 100, 1) if matched else 0
        
        pair_summary.append({
            '公司A': name_a,
            '公司B': name_b,
            'A句子数': len(idx_a),
            'B句子数': len(idx_b),
            '雷同句对数': len(matched),
            '句子重叠率(%)': overlap,
            '平均相似度(%)': avg_sim
        })
        
        for idx, (sa, sb, sim) in enumerate(matched):
            all_items.append({
                '公司A': name_a,
                '公司B': name_b,
                '序号': idx + 1,
                '相似度(%)': round(sim * 100, 1),
                '公司A内容': sa[:400],
                '公司B内容': sb[:400],
                'A句长度': len(sa),
                'B句长度': len(sb)
            })
        
        print(f"   {short_names[name_a][:8]} <-> {short_names[name_b][:8]}: {len(matched)} 对匹配")

pair_summary.sort(key=lambda x: x['雷同句对数'], reverse=True)

# === 4. 检测完全相同的句子（跨公司） ===
print(f"\n[3/4] 检测完全相同句子...")

# 用标准化后的句子做完全匹配
global_sents = defaultdict(list)  # clean_sent -> [(公司, 原始句)]
for name in comp_names:
    for sent in comp_sentences[name]:
        clean = re.sub(r'\s+', '', sent)
        if len(clean) >= 20:
            global_sents[clean].append((name, sent))

shared = []
for clean, entries in global_sents.items():
    comps = set(e[0] for e in entries)
    if len(comps) >= 3:
        shared.append({
            '完全相同的句子': entries[0][1][:500],
            '出现公司数': len(comps),
            '涉及公司': ' / '.join(short_names[c] for c in sorted(comps)),
            '句子长度': len(clean)
        })

shared.sort(key=lambda x: x['出现公司数'], reverse=True)
print(f"   发现 {len(shared)} 个跨>=3家公司的完全相同句子")

# === 5. 输出Excel ===
print(f"\n[4/4] 生成Excel报告...")

with pd.ExcelWriter(OUTPUT, engine='openpyxl') as writer:
    # Sheet1: 逐对汇总
    pd.DataFrame(pair_summary).to_excel(writer, sheet_name='逐对汇总', index=False)
    
    # Sheet2: 逐句雷同明细
    if all_items:
        pd.DataFrame(all_items).to_excel(writer, sheet_name='逐句雷同明细', index=False)
    
    # Sheet3: 完全相同句子
    if shared:
        pd.DataFrame(shared).to_excel(writer, sheet_name='完全相同句子(>=3家)', index=False)
    
    # 每对公司的独立sheet
    for i in range(len(comp_names)):
        for j in range(i + 1, len(comp_names)):
            name_a, name_b = comp_names[i], comp_names[j]
            pair_data = [d for d in all_items if d['公司A'] == name_a and d['公司B'] == name_b]
            if pair_data:
                sheet = f"{short_names[name_a][:12]} vs {short_names[name_b][:12]}"
                sheet = sheet[:31]
                pd.DataFrame(pair_data).to_excel(writer, sheet_name=sheet, index=False)

# === 6. 报告 ===
print(f"\n{'='*70}")
print(f"  分析完成！输出: {OUTPUT}")
print(f"{'='*70}")

print(f"\n[逐对雷同句统计 Top 10]")
for r in pair_summary[:10]:
    a = short_names[r['公司A']]
    b = short_names[r['公司B']]
    print(f"  {a} <-> {b}: {r['雷同句对数']}句雷同 | 重叠率{r['句子重叠率(%)']}% | 均相似度{r['平均相似度(%)']}%")

print(f"\n[完全相同句子 Top 10]")
for r in shared[:10]:
    print(f"  [{r['出现公司数']}家] {r['完全相同的句子'][:100]}...")
    print(f"  涉及: {r['涉及公司']}")

# 统计高频相似度档位
if all_items:
    hi95 = sum(1 for it in all_items if it['相似度(%)'] >= 95)
    hi90 = sum(1 for it in all_items if 90 <= it['相似度(%)'] < 95)
    hi85 = sum(1 for it in all_items if 85 <= it['相似度(%)'] < 90)
    print(f"\n[相似度分布]")
    print(f"   >=95%: {hi95} 对")
    print(f"   90-95%: {hi90} 对")  
    print(f"   85-90%: {hi85} 对")

print(f"\n✅ 共 {len(all_items)} 条逐句雷同明细 + {len(shared)} 个跨公司完全相同句子")
