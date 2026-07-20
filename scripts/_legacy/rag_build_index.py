"""融策审计知识库 RAG 系统 - 索引构建"""
import sys, os, json, glob, re, hashlib
sys.stdout.reconfigure(encoding='utf-8')

KNOWLEDGE_DIR = r'D:\openclaw-workspace\knowledge'
INDEX_DIR = r'D:\openclaw-workspace\.rag_index'
os.makedirs(INDEX_DIR, exist_ok=True)

# ---------- 1. 读取所有 .md 文件 ----------
def read_md_files(root):
    files = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.md') and not fn.startswith('.'):
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                except:
                    continue
                # Skip binary files
                if len(text) < 100:
                    continue
                # Relative path for reference
                rel = os.path.relpath(fp, root)
                files.append((rel, text))
    return files

print(f"Scanning {KNOWLEDGE_DIR}...")
files = read_md_files(KNOWLEDGE_DIR)
print(f"Found {len(files)} .md files")

# ---------- 2. 分段 ----------
def chunk_text(text, rel_path, max_chars=500, overlap=50):
    """按段落分块，每块最多 max_chars 字符"""
    # Split by double newline (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current = ''
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < max_chars:
            current = current + '\n\n' + para if current else para
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    
    # Further split very long chunks
    result = []
    for chunk in chunks:
        if len(chunk) > max_chars * 1.5:
            # Split by sentence
            sentences = re.split(r'(?<=[。！？；])', chunk)
            cur = ''
            for sent in sentences:
                if len(cur) + len(sent) < max_chars:
                    cur += sent
                else:
                    if len(cur) > 50:
                        result.append(cur)
                    cur = sent
            if len(cur) > 50:
                result.append(cur)
        else:
            if len(chunk) > 50:
                result.append(chunk)
    
    # Build metadata
    chunks_meta = []
    for c in result:
        chunks_meta.append({
            'text': c,
            'source': rel_path,
            'len': len(c)
        })
    return chunks_meta

all_chunks = []
for rel, text in files:
    chunks = chunk_text(text, rel)
    all_chunks.extend(chunks)

print(f"Total chunks: {len(all_chunks)}")
print(f"Average chunk length: {sum(c['len'] for c in all_chunks) // len(all_chunks)} chars")

# Save chunks for later use
import json
with open(os.path.join(INDEX_DIR, 'chunks.json'), 'w', encoding='utf-8') as f:
    json.dump(all_chunks, f, ensure_ascii=False)
print(f"Saved {len(all_chunks)} chunks to chunks.json")

# ---------- 3. 生成向量并建立索引 ----------
print("Loading embedding model...")
from sentence_transformers import SentenceTransformer

# Use small Chinese model
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
print("Model loaded")

texts = [c['text'] for c in all_chunks]

print("Encoding...")
embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
print(f"Embeddings shape: {embeddings.shape}")

import numpy as np
import faiss

dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity (normalized)
index.add(embeddings)
print(f"FAISS index size: {index.ntotal} vectors, dim={dim}")

faiss.write_index(index, os.path.join(INDEX_DIR, 'audit_kb.index'))
np.save(os.path.join(INDEX_DIR, 'embeddings.npy'), embeddings)
print("Index saved!")

# ---------- 4. 测试 ----------
print("\n--- Test Queries ---")
test_queries = [
    "串标围标怎么取证",
    "竣工财务决算审核流程",
    "绩效评价的方法",
    "经济责任审计一票否决",
    "政府投资条例主要规定",
]

for q in test_queries:
    q_vec = model.encode([q], normalize_embeddings=True)
    scores, idxs = index.search(q_vec, 3)
    print(f"\nQ: {q}")
    for i, idx in enumerate(idxs[0]):
        ch = all_chunks[idx]
        print(f"  [{scores[0][i]:.3f}] {ch['source']}: {ch['text'][:100]}...")
