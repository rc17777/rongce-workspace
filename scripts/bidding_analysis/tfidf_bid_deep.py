#!/usr/bin/env python3
"""Deep TF-IDF analysis: separate 标准模板 vs 技术方案"""
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

# Template markers (standard procurement doc sections)
template_patterns = [
    r'承诺函', r'授权委托书', r'法定代表人.*身份证明',
    r'具有独立承担民事责任', r'具有良好的商业信誉',
    r'具有健全的财务会计', r'具有履行合同所必需',
    r'有依法缴纳税收', r'参加本次采购活动前三年',
    r'法律.*行政.*法规.*规定.*其他条件',
    r'信用中国', r'中国政府采购网', r'国家企业信用信息',
    r'非联合体', r'不分包.*转包', r'单位负责人为同一人',
    r'无行贿犯罪', r'未列入失信',
    r'中小企业声明', r'残疾人福利', r'监狱企业',
    r'营业执照', r'审计报告',
]

def clean_text(raw):
    clean = re.sub(r'=== .+? ===', '', raw)
    clean = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbfa-zA-Z0-9\u3000-\u303f\uff00-\uffef \n\r\t.,;:!?()\u2018\u2019\u201c\u201d]', '', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean

def split_template_vs_custom(text):
    """Split text into template sections and custom content"""
    lines = text.split('\n')
    template_lines = []
    custom_lines = []
    in_template = False
    
    for line in lines:
        is_template = False
        for pat in template_patterns:
            if re.search(pat, line):
                is_template = True
                break
        if is_template:
            template_lines.append(line)
            in_template = True
        else:
            if in_template and len(line.strip()) < 20:
                continue  # short lines near template
            in_template = False
            if len(line.strip()) > 3:
                custom_lines.append(line)
    
    return '\n'.join(template_lines), '\n'.join(custom_lines)

texts = {}
for name, path in bidders.items():
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    texts[name] = clean_text(raw)

# ====== Analysis 1: Full text ======
print('='*60)
print('L3 文本雷同检测 - 分层分析')
print('='*60)

vectorizer = TfidfVectorizer(max_features=5000, token_pattern=r'[\u4e00-\u9fff]+')
all_texts = list(texts.values())
names = list(texts.keys())
tfidf_matrix = vectorizer.fit_transform(all_texts)
sim = cosine_similarity(tfidf_matrix)

print('\n【全文TF-IDF相似度】（含模板承诺函）')
for i in range(3):
    for j in range(i+1, 3):
        pct = sim[i][j] * 100
        print(f'  {names[i]} vs {names[j]}: {pct:.1f}%')

# ====== Analysis 2: Paragraph-level ======
print('\n【段落级检测】（排除<100字短段）')
para_sim_results = {}
for name1, text1 in texts.items():
    paras1 = [p.strip() for p in text1.split('。') if len(p.strip()) > 6]
    for name2, text2 in texts.items():
        if name1 >= name2:
            continue
        paras2 = [p.strip() for p in text2.split('。') if len(p.strip()) > 6]
        # Sample for speed
        paras1_sample = paras1[:500]
        paras2_sample = paras2[:500]
        all_paras = paras1_sample + paras2_sample
        if not all_paras:
            continue
        try:
            vec = TfidfVectorizer(token_pattern=r'[\u4e00-\u9fff]+')
            vec.fit(all_paras)
            m1 = vec.transform(paras1_sample)
            m2 = vec.transform(paras2_sample)
            # Find best match for each para1 in para2
            sim_matrix = cosine_similarity(m1, m2)
            high_matches = (sim_matrix > 0.95).sum()
            total = min(len(paras1_sample), len(paras2_sample))
            print(f'  {name1} vs {name2}: {high_matches}/{total} 段落相似度>95%')
            if high_matches > 0:
                # Show top matching pairs
                max_idx = np.unravel_index(sim_matrix.argmax(), sim_matrix.shape)
                print(f'    最高匹配: para{max_idx[0]} vs para{max_idx[1]} (sim={sim_matrix[max_idx]:.1%})')
                print(f'    p1: {paras1_sample[max_idx[0]][:80]}...')
                print(f'    p2: {paras2_sample[max_idx[1]][:80]}...')
        except Exception as e:
            print(f'  {name1} vs {name2}: Error - {e}')

# ====== Analysis 3: Unique content sections ======
print('\n【技术方案关键词分析】（实施方案、样品设计）')
tech_keywords = ['实施方案', '备货方案', '质量保障', '售后服务', '人员配置', '运输配送',
                 '应急处置', '退换货', '样品设计', '党校特色', '色彩搭配', '名称设计',
                 '业绩', '业绩证明', '合同', '类似项目']

for name, text in texts.items():
    print(f'\n  {name}:')
    for kw in tech_keywords:
        count = len(re.findall(kw, text))
        if count > 0:
            print(f'    {kw}: {count}次')

print('\nDone.')
