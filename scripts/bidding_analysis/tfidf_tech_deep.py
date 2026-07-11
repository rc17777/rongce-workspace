#!/usr/bin/env python3
"""Deep TF-IDF on 技术方案 only + pricing extraction + Excel output"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

base = r'D:\openclaw-workspace\projects\护理学院培训资料采购'

# ===== 1. Load technical proposal texts =====
tech_texts = {}
for idx, name in enumerate(['建韬科技', '江楼商贸', '拓奇长荣'], 1):
    fpath = os.path.join(base, f'bidder{idx}_技术方案.txt')
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            raw = f.read()
        clean = re.sub(r'=== PAGE \d+ ===', '', raw)
        clean = re.sub(r'[^\u4e00-\u9fffa-zA-Z0-9 \n]', '', clean)
        clean = re.sub(r'\s+', ' ', clean)
        tech_texts[name] = clean
        print(f'{name}: {len(clean)} chars')

# ===== 2. TF-IDF on full technical content =====
print('\n========== 技术方案TF-IDF相似度 ==========')
vectorizer = TfidfVectorizer(max_features=5000, token_pattern=r'[\u4e00-\u9fff]+')
names_list = list(tech_texts.keys())
tfidf_mat = vectorizer.fit_transform(tech_texts.values())
sim_mat = cosine_similarity(tfidf_mat)

results_tfidf = {}
for i in range(3):
    for j in range(i+1, 3):
        pct = sim_mat[i][j] * 100
        flag = 'RED' if pct >= 80 else ('YELLOW' if pct >= 50 else 'GREEN')
        results_tfidf[f'{names_list[i]} vs {names_list[j]}'] = (pct, flag)
        print(f'{names_list[i]} vs {names_list[j]}: {pct:.1f}% [{flag}]')

# ===== 3. Detecting shared unique phrases (not standard templates) =====
print('\n========== 高频技术词对比 ==========')
# Focus on technical terms
tech_keywords = ['设计方案', '备货', '质量保障', '售后服务', '人员配置', '运输配送',
                 '应急处置', '退换货', '党校特色', '色彩搭配', '名称设计',
                 '个性化', '定制', '物流', '仓储', '库存', '审核', '验收',
                 '培训', '管理', '流程', '标准', '规范', '响应', '应急']
for name, text in tech_texts.items():
    counts = {kw: len(re.findall(kw, text)) for kw in tech_keywords}
    total = sum(v for v in counts.values() if v > 0)
    print(f'{name}: {total} tech keyword hits')
    top = sorted(counts.items(), key=lambda x: -x[1])[:8]
    for kw, cnt in top:
        if cnt > 0:
            print(f'  {kw}: {cnt}')

print('\nDone.')
