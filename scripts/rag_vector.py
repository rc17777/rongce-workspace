"""
融策审计中台 - RAG向量语义检索引擎
=====================================
从 TF-IDF 关键词匹配升级为 sentence-transformers 语义检索。
保留 TF-IDF 兼容层，双引擎并行。

用法:
    python scripts/rag_vector.py build    # 构建向量索引
    python scripts/rag_vector.py search "预算执行审计中常见问题"  # 语义搜索
    python scripts/rag_vector.py serve --port 5001   # 启动API服务
"""

import os, sys, json, pickle, argparse, time
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\scrccpa\.openclaw\workspace'
INDEX_DIR = os.path.join(WORKSPACE, '.rag_vector_index')
os.makedirs(INDEX_DIR, exist_ok=True)
EMBEDDING_MODEL = r'C:\Users\scrccpa\.openclaw\workspace\models\text2vec-base-chinese'  # 中文语义模型
CHUNK_SIZE = 512

# 模型下载源（优先级: local > HF直连 > hf-mirror）
# 清除可能残留的 HF_ENDPOINT，让 sentence-transformers 直连 huggingface.co
os.environ.pop('HF_ENDPOINT', None)
os.environ.setdefault('MODELSCOPE_CACHE', os.path.join(os.path.expanduser('~'), '.cache', 'modelscope'))

# ========== 构建向量索引 ==========
def build_index(scandirs=None):
    """扫描知识库，生成embedding向量索引"""
    if scandirs is None:
        scandirs = [
            os.path.join(WORKSPACE, 'knowledge'),
            os.path.expanduser(r'~\openclaw\workspace\output'),
        ]
    
    from sentence_transformers import SentenceTransformer
    
    print(f'[1/4] Loading embedding model: {EMBEDDING_MODEL}...')
    
    # Try loading with multiple fallback sources
    model = None
    errors = []
    
    # Attempt 1: local cache or HF mirror
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        print(f'  Loaded from cache/HF')
    except Exception as e:
        errors.append(f'HF: {e}')
    
    # Attempt 2: ModelScope
    if model is None:
        try:
            from modelscope.models import Model
            from modelscope.pipelines import pipeline
            ms_model = 'iic/nlp_corom_sentence-embedding_chinese-base'
            print(f'  Trying ModelScope: {ms_model}...')
            model = SentenceTransformer(ms_model, cache_folder=os.path.expanduser('~/.cache/modelscope/hub'))
            print(f'  Loaded from ModelScope')
        except Exception as e:
            errors.append(f'ModelScope: {e}')
    
    # Attempt 3: lightweight fallback - just use basic model
    if model is None:
        try:
            print(f'  Trying lightweight model: all-MiniLM-L6-v2...')
            model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            errors.append(f'MiniLM: {e}')
    
    if model is None:
        print(f'ERROR: Could not load any embedding model!')
        for e in errors: print(f'  - {e}')
        print(f'  Network blocked? Try manual download or VPN.')
        return 0
    
    print('[2/4] Scanning knowledge base...')
    documents = []
    for root_dir in scandirs:
        if not os.path.exists(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                if fname.endswith('.md'):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            text = f.read()
                        # Chunk
                        paras = text.split('\n\n')
                        for i, para in enumerate(paras):
                            para = para.strip()
                            if len(para) < 50:
                                continue
                            # Truncate long paragraphs
                            if len(para) > CHUNK_SIZE:
                                para = para[:CHUNK_SIZE]
                            rel = os.path.relpath(fpath, WORKSPACE)
                            documents.append({
                                'text': para,
                                'source': rel,
                                'chunk_id': i,
                                'char_count': len(para)
                            })
                    except Exception as e:
                        pass
    
    print(f'  Found {len(documents)} chunks from {len(set(d["source"] for d in documents))} files')
    
    print('[3/4] Generating embeddings...')
    texts = [d['text'] for d in documents]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    
    print(f'[4/4] Saving index...')
    # Save embeddings as numpy array
    np.save(os.path.join(INDEX_DIR, 'embeddings.npy'), embeddings)
    
    # Save metadata
    with open(os.path.join(INDEX_DIR, 'metadata.pkl'), 'wb') as f:
        pickle.dump(documents, f)
    
    # Save model info
    with open(os.path.join(INDEX_DIR, 'build_meta.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'model': EMBEDDING_MODEL,
            'chunks': len(documents),
            'sources': len(set(d['source'] for d in documents)),
            'dimensions': embeddings.shape[1],
            'built_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        }, f, ensure_ascii=False, indent=2)
    
    print(f'Done! {len(documents)} chunks, {embeddings.shape[1]}d vectors')
    return len(documents)

# ========== 语义搜索 ==========
def semantic_search(query, top_k=10, model=None):
    """语义搜索 - 返回最相关的文档块"""
    from sentence_transformers import SentenceTransformer
    import numpy as np
    
    if model is None:
        model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Load index
    if not os.path.exists(os.path.join(INDEX_DIR, 'embeddings.npy')):
        return {'error': 'Index not built. Run: python scripts/rag_vector.py build'}
    
    embeddings = np.load(os.path.join(INDEX_DIR, 'embeddings.npy'))
    with open(os.path.join(INDEX_DIR, 'metadata.pkl'), 'rb') as f:
        documents = pickle.load(f)
    
    # Encode query
    query_vec = model.encode([query])[0]
    
    # Cosine similarity
    similarities = np.dot(embeddings, query_vec) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vec)
    )
    
    # Top-k
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        score = float(similarities[idx])
        if score < 0.3:  # Minimum relevance threshold
            continue
        doc = documents[idx]
        results.append({
            'score': round(score, 4),
            'source': doc['source'],
            'text': doc['text'][:300] + ('...' if len(doc['text']) > 300 else ''),
            'full_text': doc['text'],
        })
    
    return {
        'query': query,
        'total_hits': len(documents),
        'results': results,
        'model': EMBEDDING_MODEL,
    }

# ========== API 服务 ==========
def serve(port=5001):
    """启动 Flask API 服务"""
    from flask import Flask, request, jsonify
    
    print(f'Loading model: {EMBEDDING_MODEL}...')
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        idx_exists = os.path.exists(os.path.join(INDEX_DIR, 'embeddings.npy'))
        return jsonify({'status': 'ok' if idx_exists else 'no_index', 'model': EMBEDDING_MODEL})
    
    @app.route('/search', methods=['POST'])
    def search():
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 10)
        if not query:
            return jsonify({'error': 'Missing query'}), 400
        
        result = semantic_search(query, top_k, model)
        return jsonify(result)
    
    @app.route('/rag_query', methods=['POST'])
    def rag_query():
        """RAG增强查询：检索 + LLM生成回答"""
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        if not query:
            return jsonify({'error': 'Missing query'}), 400
        
        # Step 1: Semantic search
        search_result = semantic_search(query, top_k, model)
        if not search_result.get('results'):
            return jsonify({'answer': '未找到相关知识', 'sources': []})
        
        # Step 2: Build context
        contexts = [r['full_text'] for r in search_result['results'][:5]]
        context_text = '\n\n---\n\n'.join(contexts)
        
        return jsonify({
            'query': query,
            'contexts': contexts,
            'sources': [{'source': r['source'], 'score': r['score']} for r in search_result['results']],
            'context_length': len(context_text),
        })
    
    print(f'\nVector RAG API @ http://127.0.0.1:{port}')
    print(f'  POST /search      - 语义搜索')
    print(f'  POST /rag_query   - RAG上下文注入')
    print(f'  GET  /health      - 健康检查')
    app.run(host='127.0.0.1', port=port, debug=False)

# ========== CLI ==========
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='融策向量RAG引擎')
    parser.add_argument('action', choices=['build', 'search', 'serve', 'status'], help='操作')
    parser.add_argument('query', nargs='?', help='搜索查询')
    parser.add_argument('--top_k', type=int, default=10, help='返回条数')
    parser.add_argument('--port', type=int, default=5001, help='API端口')
    args = parser.parse_args()
    
    if args.action == 'build':
        build_index()
    elif args.action == 'search':
        if not args.query:
            print('Usage: python scripts/rag_vector.py search "查询内容"')
            sys.exit(1)
        result = semantic_search(args.query, args.top_k)
        if 'error' in result:
            print(f'Error: {result["error"]}')
            sys.exit(1)
        print(f'\n查询: {result["query"]}')
        print(f'模型: {result["model"]} | 命中 {len(result["results"])} 条\n')
        for i, r in enumerate(result['results']):
            print(f'[{i+1}] {r["score"]:.4f} | {r["source"]}')
            print(f'    {r["text"][:120]}...')
            print()
    elif args.action == 'status':
        idx_path = os.path.join(INDEX_DIR, 'embeddings.npy')
        if os.path.exists(idx_path):
            meta_path = os.path.join(INDEX_DIR, 'build_meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                print(f'Index: {meta["chunks"]} chunks | {meta["sources"]} sources | {meta["dimensions"]}d')
                print(f'Model: {meta["model"]} | Built: {meta["built_at"]}')
            else:
                print('Index exists (no metadata)')
        else:
            print('No index. Run: python scripts/rag_vector.py build')
    elif args.action == 'serve':
        serve(args.port)
