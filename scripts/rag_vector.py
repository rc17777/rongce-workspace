"""
融策审计中台 - RAG向量语义检索引擎 v2.0
=========================================
升级内容：
1. 审计语义切分（按段落/标题/表格/法规条款，不用固定512）
2. 混合检索（BM25关键词 + 向量语义 + RRF融合）
3. Reranker重排（BGE-reranker）
4. 日期元数据（生效/废止日期，检索时时间过滤）
5. 数据质量报告

用法:
    python scripts/rag_vector.py build           # 构建索引
    python scripts/rag_vector.py search "查询"   # 搜索
    python scripts/rag_vector.py qc              # 数据质量报告
    python scripts/rag_vector.py serve --port 5001
"""

import os, sys, json, pickle, argparse, time, re
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(WORKSPACE, '.rag_vector_index')
os.makedirs(INDEX_DIR, exist_ok=True)
EMBEDDING_MODEL = os.path.join(WORKSPACE, 'models', 'text2vec-base-chinese')
os.environ.pop('HF_ENDPOINT', None)

# ========== 审计语义切分 ==========
def audit_chunk_text(text, source=''):
    """审计语义切分，不是固定512字符硬切"""
    chunks = []
    meta = {}
    
    # 提取YAML frontmatter
    fm = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if fm:
        yaml_block = fm.group(1)
        text = text[fm.end():]
        for line in yaml_block.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                meta[k] = v
    
    effective_date = meta.get('date', meta.get('effective_date', ''))
    expiry_date = meta.get('expiry_date', meta.get('废止日期', ''))
    status = meta.get('status', 'active')
    
    # 从文件名提取日期（YYYYMMDD_ 或 YYYY-MM-DD 格式）
    if not effective_date:
        fname = os.path.basename(source)
        fm = re.match(r'(\d{8})_', fname)
        if fm:
            d = fm.group(1)
            effective_date = f'{d[:4]}-{d[4:6]}-{d[6:8]}'
        else:
            fm2 = re.match(r'(\d{4}-\d{2}-\d{2})', fname)
            if fm2:
                effective_date = fm2.group(1)
    
    # 1. 按表格切（完整表格单独成chunk，不拆散成行）
    lines = text.split('\n')
    non_table_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('|') and '|' in line.strip()[1:]:
            # 检测到表格：收集连续的表行
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|') and '|' in lines[i].strip()[1:]:
                table_lines.append(lines[i])
                i += 1
            tbl_text = '\n'.join(table_lines).strip()
            if len(tbl_text) > 30:
                chunks.append({
                    'text': tbl_text,
                    'type': 'table',
                    'effective_date': effective_date,
                    'expiry_date': expiry_date,
                    'status': status,
                    'meta': meta,
                })
        else:
            non_table_lines.append(line)
            i += 1
    text = '\n'.join(non_table_lines)
    
    # 2. 按markdown标题切分
    sections = re.split(r'\n(?=#{1,3}\s)', text)
    
    for section in sections:
        section = section.strip()
        if not section or len(section) < 30:
            continue
        
        title = ''
        tm = re.match(r'(#{1,3})\s+(.*)', section)
        if tm:
            title = tm.group(2).strip()
        
        # 3. 按段落切分（\n\n）
        paras = re.split(r'\n\n+', section)
        current_chunk = ''
        for para in paras:
            para = para.strip()
            if not para:
                continue
            
            # 检测法规条款边界
            if re.match(r'第[一二三四五六七八九十百千]+[条章节]', para):
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'type': 'paragraph',
                        'heading': title,
                        'effective_date': effective_date,
                        'expiry_date': expiry_date,
                        'status': status,
                        'meta': meta,
                    })
                current_chunk = para
            elif len(current_chunk) + len(para) > 1500:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'type': 'paragraph',
                        'heading': title,
                        'effective_date': effective_date,
                        'expiry_date': expiry_date,
                        'status': status,
                        'meta': meta,
                    })
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += '\n\n' + para
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'type': 'paragraph',
                'heading': title,
                'effective_date': effective_date,
                'expiry_date': expiry_date,
                'status': status,
                'meta': meta,
            })
    
    return chunks

# ========== 构建索引 ==========
def build_index(scandirs=None):
    """构建向量索引 + BM25索引"""
    if scandirs is None:
        scandirs = [os.path.join(WORKSPACE, 'knowledge')]
    
    from sentence_transformers import SentenceTransformer
    from rank_bm25 import BM25Okapi
    import jieba
    
    print(f'[1/4] Loading model: {EMBEDDING_MODEL}...')
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    print('[2/4] Scanning + audit chunking...')
    documents = []
    total_files = 0
    for root_dir in scandirs:
        if not os.path.exists(root_dir): continue
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                if not fname.endswith('.md'): continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        text = f.read()
                    rel = os.path.relpath(fpath, WORKSPACE)
                    chunks = audit_chunk_text(text, rel)
                    for c in chunks:
                        c['source'] = rel
                        c['char_count'] = len(c['text'])
                    documents.extend(chunks)
                    total_files += 1
                except Exception as e:
                    pass
    
    print(f'  {len(documents)} chunks from {total_files} files')
    print(f'  Types: {len([d for d in documents if d["type"]=="table"])} tables, '
          f'{len([d for d in documents if d["type"]=="paragraph"])} paragraphs')
    print(f'  Avg chunk size: {sum(d["char_count"] for d in documents)//len(documents) if documents else 0} chars')
    
    # 统计日期覆盖
    dated = [d for d in documents if d.get('effective_date')]
    print(f'  With date: {len(dated)}/{len(documents)}')
    
    print('[3/4] Generating embeddings...')
    texts = [d['text'] for d in documents]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    
    print('[3b/4] Building BM25 index...')
    tokenized = [list(jieba.cut(t)) for t in texts]
    bm25 = BM25Okapi(tokenized)
    
    print('[4/4] Saving index...')
    np.save(os.path.join(INDEX_DIR, 'embeddings.npy'), embeddings)
    with open(os.path.join(INDEX_DIR, 'documents.pkl'), 'wb') as f:
        pickle.dump(documents, f)
    with open(os.path.join(INDEX_DIR, 'bm25.pkl'), 'wb') as f:
        pickle.dump(bm25, f)
    with open(os.path.join(INDEX_DIR, 'tokenized.pkl'), 'wb') as f:
        pickle.dump(tokenized, f)
    with open(os.path.join(INDEX_DIR, 'build_meta.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'model': EMBEDDING_MODEL,
            'chunks': len(documents),
            'sources': total_files,
            'dimensions': embeddings.shape[1],
            'chunking': 'audit_semantic',
            'hybrid_search': 'BM25+vector+RRF',
            'built_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        }, f, ensure_ascii=False, indent=2)
    
    print(f'Done! {len(documents)} chunks, {embeddings.shape[1]}d')
    return len(documents)

# ========== 混合搜索 ==========
def _load_index():
    embeddings = np.load(os.path.join(INDEX_DIR, 'embeddings.npy'))
    with open(os.path.join(INDEX_DIR, 'documents.pkl'), 'rb') as f:
        documents = pickle.load(f)
    with open(os.path.join(INDEX_DIR, 'bm25.pkl'), 'rb') as f:
        bm25 = pickle.load(f)
    with open(os.path.join(INDEX_DIR, 'tokenized.pkl'), 'rb') as f:
        tokenized = pickle.load(f)
    return embeddings, documents, bm25, tokenized

def hybrid_search(query, top_k=10, model=None, year_filter=None):
    """BM25 + 向量混合检索，RRF融合"""
    from sentence_transformers import SentenceTransformer
    import jieba
    
    if model is None:
        model = SentenceTransformer(EMBEDDING_MODEL)
    
    embeddings, documents, bm25, tokenized = _load_index()
    
    # 1. 向量检索
    query_vec = model.encode([query])[0]
    vec_scores = np.dot(embeddings, query_vec) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vec) + 1e-10
    )
    
    # 2. BM25检索
    tokenized_q = list(jieba.cut(query))
    bm25_scores = bm25.get_scores(tokenized_q)
    
    # 3. RRF融合
    K = 60  # RRF常数
    rrf_scores = np.zeros(len(documents))
    
    # BM25排名
    bm25_rank = np.argsort(bm25_scores)[::-1]
    for rank, idx in enumerate(bm25_rank):
        rrf_scores[idx] += 1.0 / (K + rank + 1)
    
    # 向量排名
    vec_rank = np.argsort(vec_scores)[::-1]
    for rank, idx in enumerate(vec_rank):
        rrf_scores[idx] += 1.0 / (K + rank + 1)
    
    # 4. 时间过滤
    if year_filter:
        for i, doc in enumerate(documents):
            d = doc.get('effective_date', '')
            if d and d[:4].isdigit():
                if int(d[:4]) > year_filter:
                    rrf_scores[i] = -1
    
    # 5. Top-K
    top_indices = np.argsort(rrf_scores)[-top_k*2:][::-1]  # 取2倍供Reranker用
    
    results = []
    for idx in top_indices:
        score = float(rrf_scores[idx])
        if score < 0.01:
            continue
        doc = documents[idx]
        results.append({
            'score': round(score, 4),
            'vec_score': round(float(vec_scores[idx]), 4),
            'bm25_score': round(float(bm25_scores[idx]), 4),
            'source': doc['source'],
            'type': doc.get('type', ''),
            'heading': doc.get('heading', ''),
            'effective_date': doc.get('effective_date', ''),
            'text': doc['text'][:200] + ('...' if len(doc['text']) > 200 else ''),
            'full_text': doc['text'],
            'char_count': doc.get('char_count', 0),
            '_idx': idx,
        })
    
    return {
        'query': query,
        'total_hits': len(documents),
        'results': results,
        'model': EMBEDDING_MODEL,
    }

# ========== Reranker重排 ==========
def rerank(query, results, top_k=5):
    """用BGE-reranker对结果重排"""
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import torch
        import glob
        # 优先用ModelScope缓存，找不到则尝试HF
        ms_path = os.path.expanduser(r'~\.cache\modelscope\hub\BAAI\bge-reranker-large')
        if os.path.exists(ms_path):
            reranker_model = ms_path
        else:
            # 尝试HF缓存
            hf_pattern = os.path.expanduser(r'~\.cache\huggingface\hub\models--BAAI--bge-reranker-large\snapshots\*')
            hf_paths = glob.glob(hf_pattern)
            reranker_model = hf_paths[0] if hf_paths else 'BAAI/bge-reranker-large'
        
        tokenizer = AutoTokenizer.from_pretrained(reranker_model)
        model = AutoModelForSequenceClassification.from_pretrained(reranker_model)
        
        pairs = [[query, r['full_text']] for r in results]
        inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
        with torch.no_grad():
            scores = model(**inputs, return_dict=True).logits.view(-1).float().numpy()
        
        for i, r in enumerate(results):
            r['rerank_score'] = round(float(scores[i]), 4)
        
        results.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
        return results[:top_k]
    except Exception as e:
        print(f'Reranker unavailable: {e}')
        return results[:top_k]

def semantic_search(query, top_k=10, model=None):
    """兼容旧接口：调用混合搜索"""
    return hybrid_search(query, top_k, model)

# ========== 数据质量报告 ==========
def qc_report():
    """生成数据质量报告"""
    if not os.path.exists(os.path.join(INDEX_DIR, 'documents.pkl')):
        print('No index. Run: python scripts/rag_vector.py build')
        return
    
    _, documents, _, _ = _load_index()
    
    print('=' * 50)
    print('融策RAG知识库 · 数据质量报告')
    print('=' * 50)
    print(f'总chunks: {len(documents)}')
    
    # 1. 分块大小分布
    sizes = [d['char_count'] for d in documents]
    print(f'\n[分块大小]')
    print(f'  平均: {sum(sizes)//len(sizes)} 字符')
    print(f'  最小: {min(sizes)} 字符')
    print(f'  最大: {max(sizes)} 字符')
    small = sum(1 for s in sizes if s < 100)
    large = sum(1 for s in sizes if s > 1500)
    print(f'  <100字符(疑似碎片): {small} ({small*100//len(sizes)}%)')
    print(f'  >1500字符(可能过大): {large} ({large*100//len(sizes)}%)')
    
    # 2. 类型分布
    types = {}
    for d in documents:
        t = d.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    print(f'\n[类型分布]')
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f'  {t}: {c}')
    
    # 3. 日期覆盖
    dated = [d for d in documents if d.get('effective_date')]
    expired = [d for d in documents if d.get('status') == 'expired']
    print(f'\n[日期覆盖]')
    print(f'  有日期: {len(dated)}/{len(documents)} ({len(dated)*100//len(documents)}%)')
    print(f'  已废止: {len(expired)}')
    
    # 4. 重复检测
    texts = [d['text'] for d in documents]
    dup_count = 0
    for i in range(len(texts)):
        for j in range(i+1, min(i+50, len(texts))):
            if len(texts[i]) > 50 and texts[i] == texts[j]:
                dup_count += 1
                print(f'  重复: {documents[i]["source"]} == {documents[j]["source"]}')
                break
    print(f'\n[重复检测]')
    print(f'  发现重复: {dup_count} 组')
    
    # 5. 来源分布
    sources = {}
    for d in documents:
        s = d['source']
        sources[s] = sources.get(s, 0) + 1
    top_sources = sorted(sources.items(), key=lambda x: -x[1])[:10]
    print(f'\n[Top 10来源]')
    for s, c in top_sources:
        print(f'  {c:4d} | {s[:60]}')
    
    print(f'\n建议:')
    if small > 0:
        print(f'  ⚠️ {small} 个chunk <100字符，建议检查是否为碎片')
    if dup_count > 0:
        print(f'  ⚠️ 发现 {dup_count} 组重复，建议清理')
    if len(dated) < len(documents) * 0.5:
        print(f'  ⚠️ 日期覆盖率仅 {len(dated)*100//len(documents)}%，建议补充')

# ========== API服务 ==========
def serve(port=5001):
    from flask import Flask, request, jsonify
    from sentence_transformers import SentenceTransformer
    import torch
    
    print(f'Loading model: {EMBEDDING_MODEL}...')
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
        use_rerank = data.get('rerank', False)
        year = data.get('year', None)
        if not query:
            return jsonify({'error': 'Missing query'}), 400
        result = hybrid_search(query, top_k, model, year_filter=year)
        if use_rerank and result.get('results'):
            result['results'] = rerank(query, result['results'], top_k)
        return jsonify(result)
    
    @app.route('/rag_query', methods=['POST'])
    def rag_query():
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        year = data.get('year', None)
        if not query:
            return jsonify({'error': 'Missing query'}), 400
        result = hybrid_search(query, top_k*2, model, year_filter=year)
        if not result.get('results'):
            return jsonify({'answer': '未找到相关知识', 'sources': []})
        result['results'] = rerank(query, result['results'], top_k)
        contexts = [r['full_text'] for r in result['results']]
        return jsonify({
            'query': query,
            'contexts': contexts,
            'sources': [{'source': r['source'], 'score': r['score'], 'rerank_score': r.get('rerank_score', 0)} for r in result['results']],
            'context_length': sum(len(c) for c in contexts),
        })
    
    @app.route('/qc', methods=['GET'])
    def qc():
        buf = io.StringIO()
        sys.stdout = buf
        qc_report()
        sys.stdout = sys.__stdout__
        return jsonify({'report': buf.getvalue()})
    
    print(f'\nRAG v2 API @ http://127.0.0.1:{port}')
    print(f'  POST /search?rerank=true  - 混合搜索+可选重排')
    print(f'  POST /rag_query           - RAG上下文')
    print(f'  GET  /qc                  - 数据质量报告')
    app.run(host='127.0.0.1', port=port, debug=False)

# ========== CLI ==========
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='融策RAG v2引擎')
    parser.add_argument('action', choices=['build', 'search', 'qc', 'serve'], help='操作')
    parser.add_argument('query', nargs='?')
    parser.add_argument('--top_k', type=int, default=10)
    parser.add_argument('--port', type=int, default=5001)
    parser.add_argument('--rerank', action='store_true', help='启用Reranker重排')
    parser.add_argument('--year', type=int, help='过滤年份（如2023）')
    args = parser.parse_args()
    
    if args.action == 'build':
        build_index()
    elif args.action == 'search':
        if not args.query:
            print('Usage: python scripts/rag_vector.py search "查询"')
            sys.exit(1)
        result = hybrid_search(args.query, args.top_k, year_filter=args.year)
        if args.rerank and result.get('results'):
            result['results'] = rerank(args.query, result['results'], args.top_k)
        print(f'\n查询: {result["query"]}')
        print(f'命中 {len(result["results"])} 条\n')
        for i, r in enumerate(result['results']):
            d = f' [{r["effective_date"]}]' if r.get('effective_date') else ''
            rk = f' rerank={r["rerank_score"]}' if 'rerank_score' in r else ''
            print(f'[{i+1}] score={r["score"]}{rk} | {r["source"]}{d}')
            print(f'    {r["text"][:120]}...')
            print()
    elif args.action == 'qc':
        qc_report()
    elif args.action == 'serve':
        serve(args.port)