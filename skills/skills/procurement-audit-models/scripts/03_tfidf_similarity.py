#!/usr/bin/env python3
"""
模型3: 技术标文本相似度对比 — 围标串标特征（文件雷同）
来源：群众语言堂公众号《政府采购审计大数据技术超详细操作》
依赖：pip install pandas openpyxl scikit-learn
"""
import pandas as pd
import argparse
import sys
import os
from sklearn.feature_extraction.text import TfidfVectorizer

def read_file(filepath):
    """读取文本文件（支持txt/docx）"""
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.docx':
            # 尝试python-docx
            try:
                from docx import Document
                doc = Document(filepath)
                return '\n'.join([p.text for p in doc.paragraphs])
            except ImportError:
                print("  ⚠️ python-docx未安装，将尝试读取为纯文本")
                return open(filepath, 'r', encoding='utf-8', errors='ignore').read()
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        return f"[[读取失败: {e}]]"

def main():
    parser = argparse.ArgumentParser(description='技术标文本相似度对比')
    parser.add_argument('--input', '-i', required=True, help='投标文件清单.xlsx（需含"投标单位"和"文件路径"列）')
    parser.add_argument('--dir', '-d', default='.', help='标书文件所在目录（如果文件路径是相对路径）')
    parser.add_argument('--output', '-o', default='疑点_标书相似度.xlsx', help='输出文件')
    parser.add_argument('--threshold', type=float, default=0.9, help='相似度阈值（默认0.9=90%）')
    args = parser.parse_args()

    try:
        df = pd.read_excel(args.input)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    required = ['投标单位', '文件路径']
    for col in required:
        if col not in df.columns:
            print(f"❌ 缺少必要字段: {col}")
            print(f"   现有字段: {list(df.columns)}")
            sys.exit(1)

    # 读取文件内容
    contents = []
    valid_indices = []
    for i, row in df.iterrows():
        fpath = row['文件路径']
        if not os.path.isabs(fpath):
            fpath = os.path.join(args.dir, fpath)
        if os.path.exists(fpath):
            text = read_file(fpath)
            if len(text) > 50:  # 忽略空文件
                contents.append(text)
                valid_indices.append(i)
        else:
            print(f"  ⚠️ 文件不存在: {fpath}")

    if len(contents) < 2:
        print("❌ 有效文件不足2份，无法进行相似度对比")
        sys.exit(1)

    # TF-IDF + 余弦相似度
    vectorizer = TfidfVectorizer(max_features=5000, stop_words=None)
    tfidf = vectorizer.fit_transform(contents)
    similarity = (tfidf * tfidf.T).toarray()

    # 提取高相似度对
    results = []
    for i in range(len(similarity)):
        for j in range(i+1, len(similarity)):
            sim = similarity[i][j]
            if sim >= args.threshold:
                results.append({
                    '投标单位A': df.iloc[valid_indices[i]]['投标单位'],
                    '投标单位B': df.iloc[valid_indices[j]]['投标单位'],
                    '文件A': df.iloc[valid_indices[i]]['文件路径'],
                    '文件B': df.iloc[valid_indices[j]]['文件路径'],
                    '相似度': round(sim * 100, 2)
                })

    if len(results) == 0:
        print(f"✅ 未发现相似度超过 {args.threshold*100:.0f}% 的标书")
        pd.DataFrame(columns=['投标单位A', '投标单位B', '相似度']).to_excel(args.output, index=False)
        return

    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values('相似度', ascending=False)
    result_df.to_excel(args.output, index=False)

    print(f"✅ 完成！共发现 {len(result_df)} 对高相似度标书")
    print(f"   阈值: ≥{args.threshold*100:.0f}%")
    print(f"   输出文件: {args.output}")
    print(f"\n   疑点明细:")
    for _, row in result_df.head(15).iterrows():
        print(f"   🔗 {row['投标单位A']} ↔ {row['投标单位B']} → 相似度 {row['相似度']}%")
    if len(results) > 15:
        print(f"   ... 还有 {len(results)-15} 条，详见输出文件")

if __name__ == '__main__':
    main()
