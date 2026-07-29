# -*- coding: utf-8 -*-
import sys, os, pickle
sys.stdout.reconfigure(encoding='utf-8')

INDEX = r'D:\openclaw-workspace\.rag_index\rag_index.json'
META = r'D:\openclaw-workspace\.rag_index\build_meta.json'

# 加载pickle
with open(INDEX, 'rb') as f:
    idx = pickle.load(f)

# 遍历chunks找dataset相关
total = len(idx['chunks'])
dataset_chunks = []
for i, chunk in enumerate(idx['chunks']):
    src = chunk.get('source', '')
    if '_rag_indexed' in src or 'datasets' in src.lower():
        dataset_chunks.append({
            'idx': i,
            'source': os.path.basename(src),
            'text_preview': chunk.get('text', '')[:80]
        })

print(f'总chunks: {total}')
print(f'数据集chunks: {len(dataset_chunks)}')

if dataset_chunks:
    # 按文件统计
    from collections import Counter
    files = Counter(c['source'] for c in dataset_chunks)
    print(f'唯一文件: {len(files)}')
    
    # 按业务线
    by_type = Counter()
    for fname in files:
        if fname.startswith('CASE-'):
            by_type['case'] += 1
        elif fname.startswith('REG-'):
            by_type['regulation'] += 1
        elif fname.startswith('DM-'):
            by_type['method'] += 1
        elif fname.startswith('FP-'):
            by_type['pattern'] += 1
    
    print(f'\n类型分布:')
    for t, c in by_type.most_common():
        print(f'  {t}: {c} files')
    
    print(f'\n样本（前15个文件）:')
    for fname, count in files.most_common(15):
        print(f'  [{count} chunks] {fname}')
    
    print(f'\n✅ 数据集已入库RAG: {len(dataset_chunks)} chunks from {len(files)} files')
else:
    print('\n❌ 数据集未入库RAG！')
