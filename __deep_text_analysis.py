# -*- coding: utf-8 -*-
import os, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_distances
import numpy as np

# ========== 配置 ==========
BASE = r'C:\Users\15528\Desktop\四川护理职业学院2025年校级艺术团专业技能培训与迎新晚会编导服务响应文件\__ocr_text'
OUT_DIR = os.path.join(BASE, '__deep_analysis')
os.makedirs(OUT_DIR, exist_ok=True)

# ========== 读取文本 ==========
texts = {}
for fname in os.listdir(BASE):
    if not fname.endswith('.txt'):
        continue
    path = os.path.join(BASE, fname)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
        # 提取文件名（去掉页码）
        base_name = re.sub(r'_p[0-9]+\.txt$', '', fname)
        if base_name not in texts:
            texts[base_name] = []
        texts[base_name].append(text)

# ========== TF-IDF向量化 ==========
# 合并所有文本
all_texts = []
file_names = []
for fname, texts_list in texts.items():
    for t in texts_list:
        all_texts.append(t)
        file_names.append(fname)

# 创建TF-IDF向量化器
vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
# 转换为TF-IDF矩阵
tfidf_matrix = vectorizer.fit_transform(all_texts)

# ========== 计算余弦相似度 ==========
similarity_matrix = cosine_distances(tfidf_matrix)

# ========== 输出结果 ==========
print('=== 深度文本相似性分析 ===')
print('TF-IDF特征数:', len(vectorizer.get_feature_names_out()))
print('文档数量:', len(all_texts))

# 打印相似度矩阵
print('\n相似度矩阵:')
for i, name1 in enumerate(file_names):
    row = []
    for j, name2 in enumerate(file_names):
        sim = similarity_matrix[i][j]
        row.append(f'{sim:.3f}')
    print(f'  {name1} vs {name2}: {" | ".join(row)}')

# 保存结果
out_path = os.path.join(OUT_DIR, 'similarity_matrix.csv')
np.savetxt(out_path, similarity_matrix, delimiter=',', fmt='%.3f')
print(f'\n相似度矩阵已保存: {out_path}')