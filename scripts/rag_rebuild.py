"""重建融策 RAG 索引 v2 (2026-07-15)
数据源: C工作区knowledge + D归档knowledge + D obsidian-vault + Documents Obsidian Vault
新增: 文档级/块级 content_hash 去重、规范化哈希、build_meta.json
借鉴: 《RAG知识库如何实现动态与持续更新》(knowledge/articles/RAG知识库动态更新架构.md)
"""
import sys, os, json, re, time, hashlib
sys.stdout.reconfigure(encoding='utf-8')

# 数据源（顺序=去重优先级，排前面的先入库，重复内容保留先见者）
KNOWLEDGE_DIRS = [
    (r'D:\openclaw-workspace\knowledge', 'knowledge-D'),
    (r'D:\openclaw-workspace\obsidian-vault', 'obsidian-D'),
    (r'C:\Users\scrccpa\Documents\Obsidian Vault', 'obsidian-vault'),
]
INDEX_FILE = r'D:\openclaw-workspace\.rag_index\rag_index.json'
META_FILE = r'D:\openclaw-workspace\.rag_index\build_meta.json'

# 目录排除（路径包含任一片段即跳过）
SKIP_SEGMENTS = [
    '.git', '__pycache__', 'node_modules', '.obsidian', '.trash',
    '.venv', 'site-packages', 'venv_paddleocr', '.omc', '.clawhub',
    'templates', '未命名', '_已清理_审计案例库_旧版',
    os.sep + 'skills' + os.sep,          # SKILL.md是Agent指令，不是审计知识
    '融策工作区' + os.sep + 'memory',     # 私人记忆文件
    '融策工作区' + os.sep + 'output',
    '融策工作区' + os.sep + 'knowledge',  # KB副本（D盘已有，避免RAG重复索引）
]

FRONTMATTER_RE = re.compile(r'^---\s*\n.*?\n---\s*\n', re.DOTALL)

def normalize_text(text: str) -> str:
    """规范化正文用于哈希：去frontmatter、去抓取日期行、折叠空白。
    避免仅元数据/格式差异造成的假性不重复。"""
    text = FRONTMATTER_RE.sub('', text)
    text = re.sub(r'(抓取日期|更新时间|爬取时间)[:：]?\s*\d{4}-\d{2}-\d{2}.*', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode('utf-8')).hexdigest()

def should_skip(dirpath: str) -> bool:
    probe = dirpath + os.sep
    return any(s in probe for s in SKIP_SEGMENTS)

def read_md_files(dirs):
    """读取所有md文件，文档级content_hash去重（先见者保留）"""
    files, seen_hashes = [], {}
    stats = {}
    for root, label in dirs:
        n_read, n_dup = 0, 0
        if not os.path.exists(root):
            stats[label] = {'read': 0, 'dup_skipped': 0, 'missing': True}
            continue
        for dirpath, _, filenames in os.walk(root):
            if should_skip(dirpath):
                continue
            for fn in filenames:
                if not fn.endswith('.md') or fn.startswith('.'):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                except Exception:
                    continue
                if len(text) < 100:
                    continue
                h = content_hash(text)
                if h in seen_hashes:
                    n_dup += 1
                    continue
                seen_hashes[h] = fp
                rel = os.path.relpath(fp, root)
                files.append((rel, text, label))
                n_read += 1
        stats[label] = {'read': n_read, 'dup_skipped': n_dup}
    return files, stats

def chunk_text(text, rel_path, root_label='', max_chars=500):
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
            if current and len(current) > 50:
                chunks.append({'text': current, 'source': rel_path, 'label': root_label})
            current = para
    if current and len(current) > 50:
        chunks.append({'text': current, 'source': rel_path, 'label': root_label})
    return chunks

t0 = time.time()
print("Scanning directories...")
files, source_stats = read_md_files(KNOWLEDGE_DIRS)
print(f"Unique docs after dedup: {len(files)}")
for label, s in source_stats.items():
    print(f"  {label}: read={s['read']} dup_skipped={s.get('dup_skipped', 0)}{' MISSING' if s.get('missing') else ''}")

all_chunks = []
chunk_hashes = set()
n_chunk_dup = 0
for rel, text, label in files:
    for c in chunk_text(text, rel, label):
        ch = hashlib.sha256(re.sub(r'\s+', ' ', c['text']).strip().encode('utf-8')).hexdigest()
        if ch in chunk_hashes:
            n_chunk_dup += 1
            continue
        chunk_hashes.add(ch)
        all_chunks.append(c)

print(f"Total chunks: {len(all_chunks)} (chunk-level dup skipped: {n_chunk_dup})")

from sklearn.feature_extraction.text import TfidfVectorizer
texts = [c['text'] for c in all_chunks]

print("Building TF-IDF index...")
vectorizer = TfidfVectorizer(
    max_features=15000,
    ngram_range=(1, 2),
    analyzer='char_wb',
    max_df=0.8,
    min_df=2
)
tfidf_matrix = vectorizer.fit_transform(texts)
print(f"TF-IDF matrix: {tfidf_matrix.shape}")

import pickle
os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
with open(INDEX_FILE, 'wb') as f:
    pickle.dump({
        'vectorizer': vectorizer,
        'matrix': tfidf_matrix,
        'chunks': all_chunks,
        'texts': texts
    }, f)

elapsed = round(time.time() - t0, 1)
meta = {
    'build_time': time.strftime('%Y-%m-%d %H:%M:%S'),
    'elapsed_sec': elapsed,
    'sources': {label: root for root, label in KNOWLEDGE_DIRS},
    'source_stats': source_stats,
    'unique_docs': len(files),
    'chunks': len(all_chunks),
    'chunk_dup_skipped': n_chunk_dup,
    'matrix_shape': list(tfidf_matrix.shape),
    'chunk_strategy': 'para_merge_500c_v1',
    'vectorizer': 'tfidf_char_wb_1-2_max15000',
    'index_file_mb': round(os.path.getsize(INDEX_FILE) / 1048576, 1),
}
with open(META_FILE, 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print("Index saved!")
print(f"Build meta: {META_FILE}")
print(f"\nDone! {len(all_chunks)} chunks indexed in {elapsed}s")
