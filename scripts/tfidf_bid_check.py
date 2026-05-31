#!/usr/bin/env python3
"""TF-IDF文本雷同检测 + 文档结构分析"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

base = r'D:\openclaw-workspace\projects\护理学院培训资料采购'
bidders = {
    '建韬科技': os.path.join(base, 'bidder1_建韬.txt'),
    '江楼商贸': os.path.join(base, 'bidder2_江楼.txt'),
    '拓奇长荣': os.path.join(base, 'bidder3_拓奇长荣.txt'),
}

texts = {}
for name, path in bidders.items():
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    # Remove OCR artifacts
    clean = re.sub(r'=== .+? ===', '', raw)
    # Keep only CJK chars + common punctuation + alphanumeric
    clean = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbfa-zA-Z0-9\u3000-\u303f\uff00-\uffef \n\r\t.,;:!?()\u2018\u2019\u201c\u201d]', '', clean)
    clean = re.sub(r'\s+', ' ', clean)
    texts[name] = clean[:80000]
    print(f'{name}: {len(clean)} chars cleaned')

# Full text TF-IDF
print('\n======== L3-1: 全文TF-IDF余弦相似度 ========')
vectorizer = TfidfVectorizer(max_features=5000, token_pattern=r'[\u4e00-\u9fff]+')
tfidf_matrix = vectorizer.fit_transform(texts.values())
sim = cosine_similarity(tfidf_matrix)
names = list(texts.keys())
for i in range(3):
    for j in range(i+1, 3):
        pct = sim[i][j] * 100
        flag = 'RED_HIGH' if pct >= 80 else ('YELLOW_MED' if pct >= 50 else 'GREEN_OK')
        print(f'{names[i]} vs {names[j]}: {pct:.1f}% [{flag}]')

# Top shared terms
print('\n======== Top 20 共享高频词 ========')
feature_names = vectorizer.get_feature_names_out()
tfidf_array = tfidf_matrix.toarray()
for name_idx, name in enumerate(names):
    top_indices = tfidf_array[name_idx].argsort()[-20:][::-1]
    top_words = [(feature_names[i], tfidf_array[name_idx][i]) for i in top_indices]
    print(f'\n{name}:')
    for w, s in top_words[:10]:
        print(f'  {w}: {s:.3f}')

print('\nDone.')
