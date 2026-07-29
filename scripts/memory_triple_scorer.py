#!/usr/bin/env python3
"""
融策记忆系统 — 三重评分引擎 v1.0
═══════════════════════════════════════════
实现 Agent 长期记忆的三重评分框架：
  final_score = α·Relevance + β·Importance + γ·Recency

对应文章：斯坦福 Generative Agents 三重评分 + 融策审计场景定制

用法:
  # 增强RAG检索（三重加权排序）
  python scripts/memory_triple_scorer.py search "预算执行审计 年末突击花钱"
  
  # 对单一chunk打分（调试用）
  python scripts/memory_triple_scorer.py score "path/to/file.md" "查询文本"
  
  # 重建RAG索引并附加重要性+时效性元数据
  python scripts/memory_triple_scorer.py index

设计原则:
  - 不替代rag_query.py，作为其增强层
  - 各项评分独立可调，方便A/B测试
  - 审计领域定制（法规>案例>一般知识）
"""
import sys, os, json, re, pickle, math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

# === 路径 ===
WORKSPACE = Path(__file__).parent.parent
KNOWLEDGE_DIR = WORKSPACE / 'knowledge'
INDEX_DIR = WORKSPACE / '.rag_index'
META_FILE = INDEX_DIR / 'triple_meta.json'
SCORE_LOG = WORKSPACE / 'logs' / 'triple_score_log.jsonl'
os.makedirs(SCORE_LOG.parent, exist_ok=True)

# === 默认权重（可按业务场景调整） ===
DEFAULT_WEIGHTS = {'alpha': 0.60, 'beta': 0.20, 'gamma': 0.20}
# 审计场景调参原则：相关性权重最高（找对内容比内容重要更重要）
# β=0.20 保证"重要性"能微调排序但不会把无关法规推到第一

# === 重要性评分配置 ===
IMPORTANCE_RULES = {
    'directory_priority': {
        # 目录路径关键词 → 基础分 (0-10)
        'laws': 10,
        'regulations': 9,
        'references': 6,
        'strategy': 8,
        'standards': 8,
        'cases': 7,
        'playbooks': 7,
        'agent_specs': 6,
        'reports': 6,
        'methodology': 6,
        'templates': 5,
        'taxonomy': 4,
        'prompt-library': 4,
        'cot-dataset': 4,
        'archive': 2,
        'incoming': 3,
    },
    'keyword_boost': {
        # 内容关键词 → 加分 (0-5)
        '审计重点': 3,
        '法规依据': 3,
        '违法违规': 3,
        '审计发现': 2,
        '典型案例': 2,
        '检查要点': 2,
        '红线': 2,
        '禁止': 2,
        '必须': 1,
        '强制性': 2,
        '处罚': 2,
        '移送': 3,
        '刑事责任': 3,
        '一票否决': 3,
    },
    'min_score': 1,   # 最低重要性分
    'max_score': 10,  # 最高重要性分
}

# === 时效性衰减配置 ===
RECENCY_CONFIG = {
    'half_life_days': 180,      # 半衰期：180天后权重降至50%
    'max_age_days': 730,        # 2年后权重接近0
    'decay_function': 'exponential',  # exponential | linear
    'fresh_boost_days': 30,     # 30天内的文件额外加成
    'fresh_boost_factor': 1.2,
}


# ═══════════════════════════════════════
#  核心评分函数
# ═══════════════════════════════════════

def extract_date_from_path(file_path: str) -> datetime:
    """从文件路径/内容中提取日期"""
    path_str = str(file_path).replace('\\', '/')
    
    # 尝试从路径提取日期 (YYYY-MM-DD)
    date_patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # 2026-07-28
        r'(\d{4})(\d{2})(\d{2})',    # 20260728
    ]
    for pat in date_patterns:
        m = re.search(pat, path_str)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=CST)
            except ValueError:
                pass
    
    # 尝试从文件修改时间获取
    try:
        full_path = KNOWLEDGE_DIR / file_path
        if full_path.exists():
            mtime = os.path.getmtime(full_path)
            return datetime.fromtimestamp(mtime, tz=CST)
    except:
        pass
    
    return None


def compute_importance(file_path: str, content: str = '') -> float:
    """计算信息重要性分数 (0-1)"""
    score = IMPORTANCE_RULES['min_score']
    path_lower = str(file_path).lower().replace('\\', '/')
    
    # 1. 目录优先级
    for dir_key, base_score in IMPORTANCE_RULES['directory_priority'].items():
        if f'/{dir_key}/' in f'/{path_lower}/' or path_lower.startswith(f'{dir_key}/'):
            score = max(score, base_score)
            break  # 取最高优先级的目录
    
    # 2. 内容关键词加成
    if content:
        for kw, boost in IMPORTANCE_RULES['keyword_boost'].items():
            if kw in content:
                score += boost
    
    # 3. 文件名暗示重要性
    filename = os.path.basename(str(file_path))
    if any(kw in filename for kw in ['标准', '规范', '法规', '法律', '指引', '指南', '手册']):
        score += 2
    if any(kw in filename for kw in ['模板', '示例', '参考']):
        score += 1
    
    # 4. 文件大小代理（大文件通常更结构化/重要）
    try:
        full_path = KNOWLEDGE_DIR / file_path
        if full_path.exists() and content:
            size_kb = len(content.encode('utf-8')) / 1024
            if size_kb > 50:
                score += 1
            if size_kb > 100:
                score += 1
    except:
        pass
    
    # 截断到范围并归一化到0-1
    score = min(max(score, IMPORTANCE_RULES['min_score']), IMPORTANCE_RULES['max_score'])
    return score / 10.0


def compute_recency(file_path: str, reference_time: datetime = None) -> float:
    """计算时效性分数 (0-1)，使用指数衰减"""
    if reference_time is None:
        reference_time = datetime.now(CST)
    
    doc_date = extract_date_from_path(file_path)
    if doc_date is None:
        return 0.5  # 无法确定日期的默认中等
    
    age_days = max(0, (reference_time - doc_date).days)
    half_life = RECENCY_CONFIG['half_life_days']
    
    if RECENCY_CONFIG['decay_function'] == 'exponential':
        # e^(-λt)，λ = ln(2)/half_life
        decay = math.exp(-math.log(2) * age_days / half_life)
    else:
        # 线性衰减
        decay = max(0, 1 - age_days / RECENCY_CONFIG['max_age_days'])
    
    # 新鲜度加成
    if age_days <= RECENCY_CONFIG['fresh_boost_days']:
        decay *= RECENCY_CONFIG['fresh_boost_factor']
        decay = min(1.0, decay)
    
    return decay


def compute_triple_score(relevance: float, importance: float, recency: float,
                         weights: dict = None) -> dict:
    """计算最终三重评分"""
    w = weights or DEFAULT_WEIGHTS
    final = (w['alpha'] * relevance +
             w['beta'] * importance +
             w['gamma'] * recency)
    return {
        'relevance': round(relevance, 4),
        'importance': round(importance, 4),
        'recency': round(recency, 4),
        'final': round(final, 4),
        'weights': w,
    }


# ═══════════════════════════════════════
#  批量索引：为所有RAG chunk预计算元数据
# ═══════════════════════════════════════

def build_triple_index(rag_index_path=None):
    """
    读取RAG索引，为每个chunk预计算 importance + recency 元数据
    注意：relevance 是查询时动态计算的，不在此缓存
    """
    if rag_index_path is None:
        rag_index_path = INDEX_DIR / 'rag_index.json'
    
    if not os.path.exists(rag_index_path):
        print(f'❌ RAG索引不存在: {rag_index_path}')
        print('   请先运行 scripts/rag_rebuild.py 重建索引')
        return None
    
    with open(rag_index_path, 'rb') as f:
        data = pickle.load(f)
    
    chunks = data['chunks']
    print(f'加载 {len(chunks)} 个chunk，正在计算元数据...')
    
    meta = {}
    now = datetime.now(CST)
    total = len(chunks)
    
    for i, chunk in enumerate(chunks):
        source = chunk['source']
        content = chunk['text']
        
        if source not in meta:
            meta[source] = {
                'importance': compute_importance(source, content),
                'recency': compute_recency(source, now),
                'date_extracted': extract_date_from_path(source),
                'chunk_indices': [],
            }
        meta[source]['chunk_indices'].append(i)
        
        if (i + 1) % 1000 == 0:
            print(f'  处理中... {i+1}/{total}')
    
    # 保存
    os.makedirs(os.path.dirname(META_FILE), exist_ok=True)
    with open(META_FILE, 'w', encoding='utf-8') as f:
        # 将datetime序列化
        serializable = {}
        for src, m in meta.items():
            serializable[src] = {
                'importance': m['importance'],
                'recency': m['recency'],
                'date_extracted': m['date_extracted'].isoformat() if m['date_extracted'] else None,
                'chunk_indices': m['chunk_indices'],
            }
        json.dump(serializable, f, ensure_ascii=False, indent=1)
    
    print(f'✅ 元数据已保存: {META_FILE}')
    print(f'   覆盖 {len(meta)} 个文件')
    
    # 统计分布
    imp_scores = [m['importance'] for m in meta.values()]
    rec_scores = [m['recency'] for m in meta.values()]
    print(f'   重要性: min={min(imp_scores):.2f} max={max(imp_scores):.2f} avg={sum(imp_scores)/len(imp_scores):.2f}')
    print(f'   时效性: min={min(rec_scores):.2f} max={max(rec_scores):.2f} avg={sum(rec_scores)/len(rec_scores):.2f}')
    
    return meta


# ═══════════════════════════════════════
#  三重加权检索
# ═══════════════════════════════════════

def search_with_triple(query: str, top_k: int = 5, weights: dict = None,
                       rag_index_path=None, meta_path=None) -> list:
    """
    三重评分增强检索 —— 替代原有 search() 函数
    
    流程：
    1. TF-IDF计算relevance（原有逻辑）
    2. 从预计算元数据读取importance + recency
    3. 加权融合 → 重排序 → 返回top_k
    """
    if rag_index_path is None:
        rag_index_path = INDEX_DIR / 'rag_index.json'
    if meta_path is None:
        meta_path = META_FILE
    
    w = weights or DEFAULT_WEIGHTS
    
    # 加载RAG索引
    if not os.path.exists(rag_index_path):
        return [{'error': 'RAG索引不存在，请先运行 scripts/rag_rebuild.py'}]
    
    with open(rag_index_path, 'rb') as f:
        data = pickle.load(f)
    
    vectorizer = data['vectorizer']
    tfidf_matrix = data['matrix']
    chunks = data['chunks']
    
    # 加载元数据
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    # TF-IDF检索
    from sklearn.metrics.pairwise import cosine_similarity
    q_vec = vectorizer.transform([query])
    relevance_scores = cosine_similarity(q_vec, tfidf_matrix)[0]
    
    # 三重加权
    now = datetime.now(CST)
    scored = []
    
    for idx, rel_score in enumerate(relevance_scores):
        if rel_score < 0.01:
            continue
        
        source = chunks[idx]['source']
        file_meta = meta.get(source, {})
        
        importance = file_meta.get('importance', 0.5)
        recency = file_meta.get('recency', 0.5)
        
        # 如果元数据不存在，动态计算
        if not file_meta:
            importance = compute_importance(source, chunks[idx]['text'])
            recency = compute_recency(source, now)
        
        triple = compute_triple_score(
            relevance=float(rel_score),
            importance=importance,
            recency=recency,
            weights=w,
        )
        
        scored.append({
            'idx': idx,
            'score': triple['final'],
            'relevance': triple['relevance'],
            'importance': triple['importance'],
            'recency': triple['recency'],
            'source': source,
            'text': chunks[idx]['text'][:500],
        })
    
    # 按最终分排序
    scored.sort(key=lambda x: -x['score'])
    
    # 去重（同源文件只保留最高分的一条）
    seen_sources = set()
    deduped = []
    for item in scored:
        if item['source'] not in seen_sources:
            deduped.append(item)
            seen_sources.add(item['source'])
    
    return deduped[:top_k]


# ═══════════════════════════════════════
#  单文件评分（调试用）
# ═══════════════════════════════════════

def score_single(file_path: str, query: str = '', weights: dict = None) -> dict:
    """对单个文件/记忆条目评分"""
    w = weights or DEFAULT_WEIGHTS
    
    # 读取内容
    full_path = KNOWLEDGE_DIR / file_path
    content = ''
    if full_path.exists():
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    
    importance = compute_importance(file_path, content)
    recency = compute_recency(file_path)
    
    # Relevance 需要RAG索引才能计算，没有索引时设为N/A
    relevance = None
    
    result = {
        'file': file_path,
        'importance': round(importance, 4),
        'recency': round(recency, 4),
        'importance_raw': importance * 10,  # 还原到0-10
        'date_extracted': extract_date_from_path(file_path),
        'relevance': 'N/A (需要RAG索引+查询文本)',
    }
    
    if relevance is not None:
        result['triple'] = compute_triple_score(relevance, importance, recency, w)
    
    return result


# ═══════════════════════════════════════
#  日志记录
# ═══════════════════════════════════════

def log_query(query: str, results: list, weights: dict = None):
    """记录查询日志用于A/B测试和权重调优"""
    entry = {
        'timestamp': datetime.now(CST).isoformat(),
        'query': query,
        'weights': weights or DEFAULT_WEIGHTS,
        'top_result_scores': [r['score'] for r in results[:5]],
        'top_result_sources': [r['source'] for r in results[:5]],
        'avg_relevance': sum(r.get('relevance', 0) for r in results[:5]) / max(len(results[:5]), 1),
        'avg_importance': sum(r.get('importance', 0) for r in results[:5]) / max(len(results[:5]), 1),
        'avg_recency': sum(r.get('recency', 0) for r in results[:5]) / max(len(results[:5]), 1),
    }
    with open(SCORE_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ═══════════════════════════════════════
#  CLI
# ═══════════════════════════════════════

def print_results(results, query, weights):
    """格式化输出检索结果"""
    print(f'\n{"="*70}')
    print(f'🔍 三重评分检索: {query}')
    print(f'   权重: α(相关性)={weights["alpha"]} β(重要性)={weights["beta"]} γ(时效性)={weights["gamma"]}')
    print(f'{"="*70}')
    
    if not results:
        print('\n未找到相关文档。')
        return
    
    for i, r in enumerate(results):
        final_pct = int(r['score'] * 100)
        rel_pct = int(r['relevance'] * 100)
        imp_pct = int(r['importance'] * 100)
        rec_pct = int(r['recency'] * 100)
        
        bar = '█' * (final_pct // 5) + '░' * (20 - final_pct // 5)
        
        print(f'\n[{i+1}] [{bar}] 最终分: {final_pct}%')
        print(f'    📊 相关性:{rel_pct}% | 重要性:{imp_pct}% | 时效性:{rec_pct}%')
        print(f'    📁 {r["source"]}')
        print(f'    📝 {r["text"][:200]}...')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策记忆三重评分引擎 v1.0')
    sub = parser.add_subparsers(dest='command')
    
    p_search = sub.add_parser('search', help='三重评分增强检索')
    p_search.add_argument('query', help='查询文本')
    p_search.add_argument('--top', type=int, default=5, help='返回条数')
    p_search.add_argument('--alpha', type=float, default=0.50, help='相关性权重')
    p_search.add_argument('--beta', type=float, default=0.30, help='重要性权重')
    p_search.add_argument('--gamma', type=float, default=0.20, help='时效性权重')
    p_search.add_argument('--log', action='store_true', help='记录查询日志')
    
    p_score = sub.add_parser('score', help='单文件评分（调试）')
    p_score.add_argument('file', help='相对于knowledge/的文件路径')
    p_score.add_argument('--query', default='', help='查询文本（用于计算相关性）')
    
    p_index = sub.add_parser('index', help='重建三重评分元数据索引')
    
    p_stats = sub.add_parser('stats', help='查看元数据统计')
    
    p_compare = sub.add_parser('compare', help='对比：只用相关性 vs 三重评分')
    p_compare.add_argument('query', help='查询文本')
    p_compare.add_argument('--top', type=int, default=5, help='返回条数')
    
    args = parser.parse_args()
    
    if args.command == 'search':
        weights = {'alpha': args.alpha, 'beta': args.beta, 'gamma': args.gamma}
        results = search_with_triple(args.query, top_k=args.top, weights=weights)
        print_results(results, args.query, weights)
        if args.log:
            log_query(args.query, results, weights)
    
    elif args.command == 'score':
        result = score_single(args.file, args.query)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    
    elif args.command == 'index':
        build_triple_index()
    
    elif args.command == 'stats':
        if not os.path.exists(META_FILE):
            print('❌ 元数据索引不存在，请先运行: python scripts/memory_triple_scorer.py index')
            return
        with open(META_FILE, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        imps = [m['importance'] for m in meta.values()]
        recs = [m['recency'] for m in meta.values()]
        
        print(f'元数据统计 ({len(meta)} 个文件)')
        print(f'  重要性: min={min(imps):.2f} max={max(imps):.2f} mean={sum(imps)/len(imps):.2f}')
        print(f'  时效性: min={min(recs):.2f} max={max(recs):.2f} mean={sum(recs)/len(recs):.2f}')
        
        # Top 10 最重要文件
        by_imp = sorted(meta.items(), key=lambda x: -x[1]['importance'])[:10]
        print(f'\n  Top 10 最重要文件:')
        for src, m in by_imp:
            print(f'    [{m["importance"]:.2f}] {src}')
        
        # Bottom 10 最过时文件
        by_rec = sorted(meta.items(), key=lambda x: x[1]['recency'])[:10]
        print(f'\n  Bottom 10 最过时文件:')
        for src, m in by_rec:
            print(f'    [{m["recency"]:.2f}] {src}')
    
    elif args.command == 'compare':
        # 对比检索
        print(f'\n{"="*70}')
        print(f'🔬 对比实验: 纯相关性 vs 三重评分')
        print(f'   查询: {args.query}')
        print(f'{"="*70}')
        
        # 1. 纯相关性
        triple_results = search_with_triple(
            args.query, top_k=args.top,
            weights={'alpha': 1.0, 'beta': 0.0, 'gamma': 0.0}
        )
        print(f'\n--- 纯相关性 (α=1.0) ---')
        for r in triple_results:
            print(f'  [{r["score"]:.0%}] {r["source"]}')
        
        # 2. 三重评分
        w = DEFAULT_WEIGHTS
        triple_results = search_with_triple(args.query, top_k=args.top)
        print(f'\n--- 三重评分 (α={w["alpha"]} β={w["beta"]} γ={w["gamma"]}) ---')
        for r in triple_results:
            print(f'  [{r["score"]:.0%}] R{r["relevance"]:.0%} I{r["importance"]:.0%} T{r["recency"]:.0%} {r["source"]}')
        
        # 差异分析
        pure_sources = set()
        pure_results = search_with_triple(
            args.query, top_k=args.top,
            weights={'alpha': 1.0, 'beta': 0.0, 'gamma': 0.0}
        )
        for r in pure_results:
            pure_sources.add(r['source'])
        
        triple_sources = set()
        for r in triple_results:
            triple_sources.add(r['source'])
        
        only_pure = pure_sources - triple_sources
        only_triple = triple_sources - pure_sources
        
        if only_pure or only_triple:
            print(f'\n--- 排序差异 ---')
            if only_triple:
                print(f'  三重评分新增 (高重要性/高时效性补偿):')
                for src in only_triple:
                    print(f'    + {src}')
            if only_pure:
                print(f'  纯相关性独占 (被重要性/时效性压下):')
                for src in only_pure:
                    print(f'    - {src}')
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
