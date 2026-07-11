"""融策审计知识库 RAG 系统 v1 - 纯本地版
使用 TF-IDF + 关键词检索，生成阶段调用 DeepSeek API
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

KNOWLEDGE_DIR = r'D:\openclaw-workspace\knowledge'
INDEX_DIR = r'D:\openclaw-workspace\.rag_index'
os.makedirs(INDEX_DIR, exist_ok=True)

def read_md_files(root):
    files = []
    for dirpath, _, filenames in os.walk(root):
        skip_dirs = ['.git', '__pycache__', 'node_modules']
        if any(s in dirpath for s in skip_dirs):
            continue
        for fn in filenames:
            if fn.endswith('.md') and not fn.startswith('.'):
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                except:
                    continue
                if len(text) < 100:
                    continue
                rel = os.path.relpath(fp, root)
                files.append((rel, text))
    return files

def chunk_text(text, rel_path, max_chars=500):
    """按段落分块"""
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
                chunks.append({'text': current, 'source': rel_path})
            current = para
    if current and len(current) > 50:
        chunks.append({'text': current, 'source': rel_path})
    return chunks

# ---------- Build or load index ----------
INDEX_FILE = os.path.join(INDEX_DIR, 'rag_index.json')

if not os.path.exists(INDEX_FILE):
    print("Building index for the first time...")
    files = read_md_files(KNOWLEDGE_DIR)
    print(f"Found {len(files)} .md files")
    
    all_chunks = []
    for rel, text in files:
        chunks = chunk_text(text, rel)
        all_chunks.extend(chunks)
    
    print(f"Total chunks: {len(all_chunks)}")
    
    # Build TF-IDF index
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    texts = [c['text'] for c in all_chunks]
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        analyzer='char_wb',  # character-level for Chinese
        max_df=0.8,
        min_df=2
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    print(f"TF-IDF matrix: {tfidf_matrix.shape}")
    
    # Save
    import pickle
    with open(INDEX_FILE, 'wb') as f:
        pickle.dump({
            'vectorizer': vectorizer,
            'matrix': tfidf_matrix,
            'chunks': all_chunks,
            'texts': texts
        }, f)
    print("Index saved!")
else:
    import pickle
    with open(INDEX_FILE, 'rb') as f:
        data = pickle.load(f)
    vectorizer = data['vectorizer']
    tfidf_matrix = data['matrix']
    texts = data['texts']
    all_chunks = data['chunks']
    print(f"Loaded index: {len(all_chunks)} chunks, matrix {tfidf_matrix.shape}")

# ---------- Search ----------
def search(query, top_k=5):
    """检索最相关的chunk"""
    q_vec = vectorizer.transform([query])
    from sklearn.metrics.pairwise import cosine_similarity
    scores = cosine_similarity(q_vec, tfidf_matrix)[0]
    
    top_idx = scores.argsort()[::-1][:top_k]
    results = []
    for idx in top_idx:
        if scores[idx] > 0.01:  # ignore very low scores
            results.append({
                'score': float(scores[idx]),
                'source': all_chunks[idx]['source'],
                'text': all_chunks[idx]['text'][:500]
            })
    return results

# ---------- RAG Query with Zhipu GLM-4-Plus ----------
ZHIPU_API = '6fd63d70ad8944e597ab5c2d3609fbf1.U41vqcRuzi8V8EBH'
ZHIPU_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
ZHIPU_MODEL = 'glm-4-plus'
if not ZHIPU_API:
    # Try to find in config
    config_paths = [
        r'D:\openclaw-workspace\.openclaw\profile.json',
        r'D:\openclaw-workspace\config\api_keys.json'
    ]
    for cp in config_paths:
        if os.path.exists(cp):
            try:
                with open(cp, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                # Search for zhipu key
                for k, v in cfg.items():
                    if 'zhipu' in k.lower() and isinstance(v, str) and v.startswith('sk-'):
                        ZHIPU_API = v
                        break
            except:
                pass

def rag_query(query, use_api=True):
    """RAG 查询"""
    results = search(query, top_k=5)
    
    print(f"\n{'='*60}")
    print(f"Q: {query}")
    print(f"{'='*60}")
    
    if not results:
        print("\n未找到相关文档。")
        return
    
    print(f"\n📚 检索到 {len(results)} 条相关文档：")
    for i, r in enumerate(results):
        score_pct = int(r['score'] * 100)
        bar = '█' * (score_pct // 5) + '░' * (20 - score_pct // 5)
        print(f"\n[{i+1}] [{bar}] ({score_pct}%) {r['source']}")
        print(f"    {r['text'][:200]}...")
    
    if use_api and ZHIPU_API:
        context = "\n\n---\n\n".join([f"【{r['source']}】\n{r['text']}" for r in results])
        
        prompt = f"""你是一名审计专家，请基于以下知识库内容回答用户问题。

知识库内容：
{context}

用户问题：{query}

请给出专业、准确的回答，并在引用时标注来源文件名。如果知识库内容不足以回答问题，请如实说明。"""

        import requests
        try:
            resp = requests.post(
                ZHIPU_URL,
                headers={
                    'Authorization': f'Bearer {ZHIPU_API}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': ZHIPU_MODEL,
                    'messages': [
                        {'role': 'system', 'content': '你是一名中国审计专家，精通政府审计、工程审计、财务审计。回答专业、简洁、准确。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 2000
                },
                timeout=30
            )
            if resp.status_code == 200:
                answer = resp.json()['choices'][0]['message']['content']
                print(f"\n🤖 AI 回答：\n{answer}")
            else:
                print(f"\nAPI error: {resp.status_code}")
        except Exception as e:
            print(f"\nAPI call failed: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = input("请输入审计问题：")
    
    rag_query(query)
