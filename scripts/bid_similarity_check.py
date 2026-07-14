#!/usr/bin/env python3
"""
7家公司投标文件雷同检测
基于TF-IDF + 余弦相似度，分文件类型比对 + 综合比对
"""
import os, sys, re, warnings, io
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber

warnings.filterwarnings('ignore')

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# === 配置 ===
BASE_DIR = r"C:\Users\scrccpa\Desktop\新建文件夹"
OUTPUT = os.path.join(BASE_DIR, "投标文件雷同检测结果.xlsx")

# === 1. 提取所有PDF文本 ===
def extract_pdf_text(filepath):
    """提取PDF文本"""
    try:
        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        full_text = '\n'.join(text_parts)
        # 清理：去掉多余空白，保留中文有效内容
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        return full_text
    except Exception as e:
        return f"[[提取失败: {e}]]"

print("=" * 70)
print("  投标文件雷同检测 — 基于TF-IDF文本相似度")
print("=" * 70)

# 扫描所有公司文件夹和PDF
companies = {}
all_files = set()
total_pdfs = 0

for entry in sorted(os.listdir(BASE_DIR)):
    entry_path = os.path.join(BASE_DIR, entry)
    if os.path.isdir(entry_path):
        # 提取公司名（去掉"(包1)"后缀）
        comp_name = re.sub(r'\(包\d+\)', '', entry).strip()
        pdfs = {}
        for f in os.listdir(entry_path):
            if f.lower().endswith('.pdf'):
                fpath = os.path.join(entry_path, f)
                pdfs[f] = fpath
                all_files.add(f)
                total_pdfs += 1
        companies[comp_name] = {
            'folder': entry,
            'pdfs': pdfs
        }

comp_names = sorted(companies.keys())
print(f"\n📁 发现 {len(comp_names)} 家公司，共 {total_pdfs} 个PDF文件")
print(f"📄 文件类型: {len(all_files)} 种")
for cn in comp_names:
    print(f"   · {cn} ({len(companies[cn]['pdfs'])} 个文件)")

# === 2. 提取所有PDF文本 ===
print(f"\n⏳ 正在提取PDF文本...")
text_cache = {}  # key: (公司名, 文件名) -> text

for comp_name in comp_names:
    comp_pdfs = companies[comp_name]['pdfs']
    for fname, fpath in comp_pdfs.items():
        key = (comp_name, fname)
        txt = extract_pdf_text(fpath)
        text_cache[key] = txt
        status = "✓" if not txt.startswith("[[提取失败") else "✗"
        print(f"   {status} {comp_name[:8]}... / {fname} ({len(txt)}字)")

# === 3. 按文件类型分组比对 ===
print(f"\n⏳ 正在计算相似度...")

# 3a. 同名文件交叉比对
filetype_results = []
filetype_matrices = {}  # 保存每个文件类型的矩阵供后续用

for fname in sorted(all_files):
    # 收集该文件类型下所有公司的文本
    texts = []
    labels = []
    for comp_name in comp_names:
        key = (comp_name, fname)
        if key in text_cache:
            txt = text_cache[key]
            if not txt.startswith("[[提取失败") and len(txt) > 30:
                texts.append(txt)
                labels.append(comp_name)
    
    if len(texts) < 2:
        continue
    
    # 中文TF-IDF需要char-level或word-level
    try:
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 4),
            max_features=3000,
            lowercase=False
        )
        tfidf = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf)
    except:
        continue
    
    filetype_matrices[fname] = (sim_matrix, labels)
    
    # 提取高相似度对（>=70%）
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            sim = sim_matrix[i][j]
            if sim >= 0.70:
                filetype_results.append({
                    '文件类型': fname,
                    '公司A': labels[i],
                    '公司B': labels[j],
                    '相似度(%)': round(sim * 100, 2),
                    '风险等级': '🔴 高风险' if sim >= 0.90 else ('🟡 中风险' if sim >= 0.80 else '🟢 低风险')
                })

# 3b. 综合比对（每家公司所有文本合并）
print(f"⏳ 正在计算综合相似度...")
comp_full_texts = {}
for comp_name in comp_names:
    all_text = []
    for fname in sorted(all_files):
        key = (comp_name, fname)
        if key in text_cache and not text_cache[key].startswith("[[提取失败"):
            all_text.append(text_cache[key])
    comp_full_texts[comp_name] = ' '.join(all_text)

try:
    all_labels = sorted(comp_full_texts.keys())
    all_texts_list = [comp_full_texts[l] for l in all_labels]
    
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 4),
        max_features=5000,
        lowercase=False
    )
    tfidf_all = vectorizer.fit_transform(all_texts_list)
    overall_matrix = cosine_similarity(tfidf_all)
    
    overall_results = []
    for i in range(len(all_labels)):
        for j in range(i + 1, len(all_labels)):
            sim = overall_matrix[i][j]
            overall_results.append({
                '公司A': all_labels[i],
                '公司B': all_labels[j],
                '综合相似度(%)': round(sim * 100, 2),
                '风险等级': '🔴 高风险' if sim >= 0.90 else ('🟡 中风险' if sim >= 0.80 else '🟢 低风险')
            })
    overall_results.sort(key=lambda x: x['综合相似度(%)'], reverse=True)
except Exception as e:
    print(f"   ⚠️ 综合比对出错: {e}")
    overall_results = []

# === 4. 输出Excel ===
print(f"\n⏳ 正在生成Excel报告...")

with pd.ExcelWriter(OUTPUT, engine='openpyxl') as writer:
    # Sheet 1: 综合相似度矩阵
    if overall_results:
        df_overall = pd.DataFrame(overall_results)
        df_overall.to_excel(writer, sheet_name='综合相似度', index=False)
        
        # 构建矩阵表
        matrix_data = []
        for i, label_a in enumerate(all_labels):
            row = [label_a]
            for j, label_b in enumerate(all_labels):
                if i == j:
                    row.append('—')
                else:
                    row.append(f"{overall_matrix[i][j]*100:.1f}%")
            matrix_data.append(row)
        
        col_headers = ['公司名'] + [l.replace('有限公司', '') for l in all_labels]
        df_matrix = pd.DataFrame(matrix_data, columns=col_headers)
        df_matrix.to_excel(writer, sheet_name='综合相似度矩阵', index=False)
    
    # Sheet 2: 同名文件雷同明细
    if filetype_results:
        filetype_results.sort(key=lambda x: x['相似度(%)'], reverse=True)
        df_ft = pd.DataFrame(filetype_results)
        df_ft.to_excel(writer, sheet_name='同名文件雷同明细', index=False)
    
    # Sheet 3-5: 各文件类型相似度矩阵（选相似度最高的几个）
    # 计算每个文件类型的平均相似度，选top5
    ft_avg_sim = {}
    for fname, (sim_matrix, labels) in filetype_matrices.items():
        sims = []
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                sims.append(sim_matrix[i][j])
        ft_avg_sim[fname] = np.mean(sims) if sims else 0
    
    top_files = sorted(ft_avg_sim.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for fname, _ in top_files:
        sim_matrix, labels = filetype_matrices[fname]
        # 安全的sheet名（Excel限制31字符）
        sheet_name = fname.replace('.pdf', '')[:31]
        
        mdata = []
        for i, la in enumerate(labels):
            row = [la]
            for j, lb in enumerate(labels):
                if i == j:
                    row.append('—')
                else:
                    row.append(f"{sim_matrix[i][j]*100:.1f}%")
            mdata.append(row)
        
        short_headers = ['公司'] + [l.replace('有限公司', '')[:8] for l in labels]
        df_m = pd.DataFrame(mdata, columns=short_headers)
        df_m.to_excel(writer, sheet_name=sheet_name, index=False)

# === 5. 汇总报告 ===
print(f"\n{'='*70}")
print(f"  ✅ 分析完成！")
print(f"  输出文件: {OUTPUT}")
print(f"{'='*70}")

# 统计
high_risk = [r for r in filetype_results if r['相似度(%)'] >= 90]
mid_risk = [r for r in filetype_results if 80 <= r['相似度(%)'] < 90]

print(f"\n📊 同名文件雷同统计:")
print(f"   🔴 高风险（≥90%）: {len(high_risk)} 对")
print(f"   🟡 中风险（80-90%）: {len(mid_risk)} 对")
print(f"   🟢 低风险（70-80%）: {len(filetype_results) - len(high_risk) - len(mid_risk)} 对")
print(f"   📝 合计: {len(filetype_results)} 对")

if overall_results:
    print(f"\n📊 综合相似度统计:")
    high_overall = [r for r in overall_results if r['综合相似度(%)'] >= 90]
    mid_overall = [r for r in overall_results if 80 <= r['综合相似度(%)'] < 90]
    print(f"   🔴 高风险（≥90%）: {len(high_overall)} 对")
    print(f"   🟡 中风险（80-90%）: {len(mid_overall)} 对")
    
    print(f"\n   Top 10 综合相似度:")
    for i, r in enumerate(overall_results[:10]):
        abbr_a = r['公司A'].replace('有限公司', '')
        abbr_b = r['公司B'].replace('有限公司', '')
        print(f"   {i+1}. {r['风险等级']} {abbr_a} ↔ {abbr_b} → {r['综合相似度(%)']}%")

print(f"\n   Sheet说明:")
print(f"   · 综合相似度: 21对公司两两综合比对结果")
print(f"   · 综合相似度矩阵: 7×7矩阵一览")
print(f"   · 同名文件雷同明细: 14种文件×21对=所有雷同详情")
print(f"   · 其他sheet: Top5雷同文件类型的详细矩阵")

# 高分文件类型摘要
if filetype_results:
    from collections import Counter
    ft_counter = Counter()
    for r in filetype_results:
        if r['相似度(%)'] >= 80:
            ft_counter[r['文件类型']] += 1
    if ft_counter:
        print(f"\n📄 中高风险最集中的文件类型:")
        for fname, cnt in ft_counter.most_common(5):
            print(f"   · {fname}: {cnt} 对高相似度")

print(f"\n✅ 完成！请打开Excel查看完整结果。")
