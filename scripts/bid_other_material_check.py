#!/usr/bin/env python3
"""
7家公司「投标人认为应当提供的其他材料.pdf」深度雷同分析
TF-IDF全文相似度 + 段落级雷同检测 + 相同句子提取
"""
import os, sys, re, io, warnings
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber

warnings.filterwarnings('ignore')
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = r"C:\Users\scrccpa\Desktop\新建文件夹"
TARGET_FILE = "投标人认为应当提供的其他材料.pdf"
OUTPUT = os.path.join(BASE_DIR, "其他材料雷同分析.xlsx")

# === 1. 读取所有公司的目标文件 ===
print("=" * 70)
print(f"  目标文件: {TARGET_FILE}")
print("=" * 70)

comp_data = {}  # {公司名: {text, path, char_count}}
for entry in sorted(os.listdir(BASE_DIR)):
    entry_path = os.path.join(BASE_DIR, entry)
    if not os.path.isdir(entry_path):
        continue
    comp_name = re.sub(r'\(包\d+\)', '', entry).strip()
    fpath = os.path.join(entry_path, TARGET_FILE)
    if not os.path.exists(fpath):
        print(f"   [跳过] {comp_name}: 文件不存在")
        continue
    
    # 提取文本
    try:
        text_parts = []
        with pdfplumber.open(fpath) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        full_text = '\n'.join(text_parts)
        cleaned = re.sub(r'\s+', ' ', full_text).strip()
        
        comp_data[comp_name] = {
            'text': cleaned,
            'path': fpath,
            'char_count': len(cleaned),
            'pages': total_pages
        }
        print(f"   {comp_name}: {total_pages}页, {len(cleaned)}字符")
    except Exception as e:
        print(f"   [错误] {comp_name}: {e}")

comp_names = sorted(comp_data.keys())
print(f"\n   共 {len(comp_names)} 家公司参与比对")

# === 2. 全文TF-IDF相似度 ===
print(f"\n[1/4] 全文TF-IDF相似度分析...")

texts = [comp_data[c]['text'] for c in comp_names]
vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), max_features=5000, lowercase=False)
tfidf = vectorizer.fit_transform(texts)
sim_matrix = cosine_similarity(tfidf)

# 相似度矩阵
matrix_rows = []
for i, name_a in enumerate(comp_names):
    row = [name_a]
    for j, name_b in enumerate(comp_names):
        if i == j:
            row.append('—')
        else:
            row.append(round(sim_matrix[i][j] * 100, 2))
    matrix_rows.append(row)

# pairwise列表
full_sim_pairs = []
for i in range(len(comp_names)):
    for j in range(i + 1, len(comp_names)):
        sim = sim_matrix[i][j]
        if sim >= 0.70:
            level = '🔴 极高' if sim >= 0.95 else ('🔴 高' if sim >= 0.90 else ('🟡 中' if sim >= 0.80 else '🟢 低'))
        else:
            level = '⚪ 正常'
        full_sim_pairs.append({
            '公司A': comp_names[i],
            '公司B': comp_names[j],
            '全文相似度(%)': round(sim * 100, 2),
            '公司A字符数': comp_data[comp_names[i]]['char_count'],
            '公司B字符数': comp_data[comp_names[j]]['char_count'],
            '字符差异率(%)': round(abs(comp_data[comp_names[i]]['char_count'] - comp_data[comp_names[j]]['char_count']) / max(comp_data[comp_names[i]]['char_count'], comp_data[comp_names[j]]['char_count']) * 100, 1),
            '风险等级': level
        })
full_sim_pairs.sort(key=lambda x: x['全文相似度(%)'], reverse=True)

# === 3. 段落级雷同检测 ===
print(f"[2/4] 段落级雷同检测...")

def split_paragraphs(text, min_len=80):
    """按空行/换行分割段落"""
    # 先用空行分
    paras = re.split(r'\n\s*\n', text)
    result = []
    for p in paras:
        p = p.strip()
        if len(p) >= min_len:
            result.append(p)
    return result

# 计算每对公司的段落雷同
para_results = []
for i in range(len(comp_names)):
    for j in range(i + 1, len(comp_names)):
        name_a, name_b = comp_names[i], comp_names[j]
        paras_a = split_paragraphs(comp_data[name_a]['text'])
        paras_b = split_paragraphs(comp_data[name_b]['text'])
        
        matches = []
        # 简单的Jaccard-like段落匹配
        for pa in paras_a:
            pa_words = set(pa)
            for pb in paras_b:
                pb_words = set(pb)
                if len(pa_words | pb_words) > 0:
                    jaccard = len(pa_words & pb_words) / len(pa_words | pb_words)
                    if jaccard >= 0.85:  # 85%以上字符级重叠
                        matches.append((pa[:100], pb[:100], round(jaccard * 100, 1)))
        
        para_results.append({
            '公司A': name_a,
            '公司B': name_b,
            'A段落数': len(paras_a),
            'B段落数': len(paras_b),
            '雷同段落数': len(matches),
            '雷同率(%)': round(len(matches) / max(len(paras_a), len(paras_b)) * 100, 1) if max(len(paras_a), len(paras_b)) > 0 else 0
        })

para_results.sort(key=lambda x: x['雷同段落数'], reverse=True)

# === 4. 完全相同句子提取 ===
print(f"[3/4] 完全相同句子提取...")

def split_sentences(text, min_len=30):
    """按句号/分号等分割句子"""
    sents = re.split(r'[。；;.\n]{1,}', text)
    result = []
    seen = set()
    for s in sents:
        s = s.strip()
        s_clean = re.sub(r'\s+', '', s)
        if len(s_clean) >= min_len and s_clean not in seen:
            result.append(s_clean)
            seen.add(s_clean)
    return result

# 找出在所有公司间高频率出现的句子
all_sents_by_comp = {}
all_sents_global = []
for name in comp_names:
    sents = split_sentences(comp_data[name]['text'], min_len=30)
    all_sents_by_comp[name] = set(sents)
    all_sents_global.extend(sents)

# 统计每条句子出现了几次（跨公司）
from collections import Counter
sent_counter = Counter(all_sents_global)
repeated_sents = [(sent, cnt) for sent, cnt in sent_counter.items() if cnt >= 3]
repeated_sents.sort(key=lambda x: x[1], reverse=True)
repeated_sents = repeated_sents[:50]  # top 50

# 标记每条句子被哪些公司使用
sent_company_map = []
for sent, cnt in repeated_sents:
    owners = [c for c in comp_names if sent in all_sents_by_comp[c]]
    sent_company_map.append({
        '完全相同句子': sent[:200],
        '出现公司数': cnt,
        '涉及公司': '、'.join([o.replace('有限公司', '') for o in owners]),
        '句子长度': len(sent)
    })

# === 5. 逐对完全相同句子统计 ===
print(f"[4/4] 逐对完全相同句子统计...")

pairwise_sent_matches = []
for i in range(len(comp_names)):
    for j in range(i + 1, len(comp_names)):
        name_a, name_b = comp_names[i], comp_names[j]
        sents_a = all_sents_by_comp[name_a]
        sents_b = all_sents_by_comp[name_b]
        common = sents_a & sents_b
        
        total_sents = max(len(sents_a), len(sents_b))
        overlap_rate = round(len(common) / total_sents * 100, 1) if total_sents > 0 else 0
        
        sample_sents = list(common)[:5]
        sample_text = ' | '.join([s[:80] for s in sample_sents])
        
        pairwise_sent_matches.append({
            '公司A': name_a,
            '公司B': name_b,
            'A句子总数': len(sents_a),
            'B句子总数': len(sents_b),
            '完全相同句子数': len(common),
            '句子重叠率(%)': overlap_rate,
            '示例（前5句）': sample_text
        })

pairwise_sent_matches.sort(key=lambda x: x['完全相同句子数'], reverse=True)

# === 6. 输出Excel ===
print(f"\n[输出] 生成Excel报告...")

with pd.ExcelWriter(OUTPUT, engine='openpyxl') as writer:
    # Sheet1: 全文相似度矩阵
    headers = ['公司名'] + [c.replace('有限公司', '') for c in comp_names]
    pd.DataFrame(matrix_rows, columns=headers).to_excel(writer, sheet_name='1-全文相似度矩阵', index=False)
    
    # Sheet2: 全文相似度排名
    pd.DataFrame(full_sim_pairs).to_excel(writer, sheet_name='2-全文相似度排名', index=False)
    
    # Sheet3: 段落雷同检测
    if para_results:
        pd.DataFrame(para_results).to_excel(writer, sheet_name='3-段落雷同检测', index=False)
    
    # Sheet4: 逐对句级重叠
    if pairwise_sent_matches:
        pd.DataFrame(pairwise_sent_matches).to_excel(writer, sheet_name='4-逐对句级重叠', index=False)
    
    # Sheet5: 跨公司重复句子
    if sent_company_map:
        pd.DataFrame(sent_company_map).to_excel(writer, sheet_name='5-跨公司重复句子', index=False)

# === 7. 汇总报告 ===
print(f"\n{'='*70}")
print(f"  分析完成！输出: {OUTPUT}")
print(f"{'='*70}")

print(f"\n[全文相似度 Top 5]")
for i, r in enumerate(full_sim_pairs[:5]):
    a = r['公司A'].replace('有限公司', '')
    b = r['公司B'].replace('有限公司', '')
    print(f"  {i+1}. {r['风险等级']} {a} <-> {b}: {r['全文相似度(%)']}%")

print(f"\n[段落雷同 Top 5]")
for i, r in enumerate(para_results[:5]):
    if r['雷同段落数'] > 0:
        a = r['公司A'].replace('有限公司', '')
        b = r['公司B'].replace('有限公司', '')
        print(f"  {i+1}. {a} <-> {b}: {r['雷同段落数']}/{max(r['A段落数'],r['B段落数'])} 段雷同 ({r['雷同率(%)']}%)")

print(f"\n[句级重叠 Top 5]")
for i, r in enumerate(pairwise_sent_matches[:5]):
    if r['完全相同句子数'] > 0:
        a = r['公司A'].replace('有限公司', '')
        b = r['公司B'].replace('有限公司', '')
        print(f"  {i+1}. {a} <-> {b}: {r['完全相同句子数']} 句完全相同 (重叠率 {r['句子重叠率(%)']}%)")

if sent_company_map:
    print(f"\n[跨公司高频重复句子 Top 10]")
    for i, r in enumerate(sent_company_map[:10]):
        print(f"  {i+1}. [{r['出现公司数']}家] {r['完全相同句子'][:80]}...")
        print(f"     涉及: {r['涉及公司']}")

print(f"\nSheet清单:")
print(f"  1-全文相似度矩阵: 7x7热力矩阵")
print(f"  2-全文相似度排名: 21对排名+字符差异率")
print(f"  3-段落雷同检测: 段落级Jaccard匹配")
print(f"  4-逐对句级重叠: 每对公司完全相同句子数")
print(f"  5-跨公司重复句子: 出现>=3家公司的完全重复句子TOP50")

print(f"\n✅ 完成！")
