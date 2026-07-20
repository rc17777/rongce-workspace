"""
融策RAG知识库 · 数据质量监控
==============================
每周运行一次，检查知识库健康状态。
用法: python scripts/kb_qc.py
"""
import os, sys, json, re, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(WORKSPACE, '.rag_vector_index')
REPORT_DIR = os.path.join(WORKSPACE, 'logs', 'kb_qc')
os.makedirs(REPORT_DIR, exist_ok=True)

def run_check():
    print('=' * 60)
    print('融策RAG知识库 · 数据质量检查')
    print('=' * 60)
    
    # 1. 索引状态
    idx_path = os.path.join(INDEX_DIR, 'embeddings.npy')
    meta_path = os.path.join(INDEX_DIR, 'build_meta.json')
    if not os.path.exists(idx_path):
        print('❌ 索引不存在，请先运行 python scripts/rag_vector.py build')
        return
    
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        print(f'✅ 索引存在: {meta.get("chunks","?")} chunks, {meta.get("sources","?")} 文件')
        print(f'   模型: {meta.get("model","?")} | 切分: {meta.get("chunking","?")}')
        print(f'   构建时间: {meta.get("built_at","?")}')
    
    # 2. 加载文档
    pkl_path = os.path.join(INDEX_DIR, 'documents.pkl')
    if not os.path.exists(pkl_path):
        print('❌ documents.pkl 不存在')
        return
    import pickle
    with open(pkl_path, 'rb') as f:
        documents = pickle.load(f)
    
    print(f'\n--- 文档统计 ---')
    print(f'总chunks: {len(documents)}')
    sizes = [d.get('char_count', len(d['text'])) for d in documents]
    avg = sum(sizes) // len(sizes)
    print(f'平均大小: {avg} 字符')
    print(f'大小范围: {min(sizes)} ~ {max(sizes)} 字符')
    
    # 3. 碎片检测（<50字符才算碎片）
    SMALL_THRESHOLD = 50
    small = [d for d in documents if d.get('char_count', len(d['text'])) < SMALL_THRESHOLD]
    if small:
        print(f'\n⚠️ 碎片chunks (<{SMALL_THRESHOLD}字符): {len(small)}')
        for d in small[:5]:
            print(f'   {d["source"][:50]} | {d["text"][:60]}')
    else:
        print(f'\n✅ 无碎片chunks')
    
    # 超大chunks
    LARGE_THRESHOLD = 1500
    large = [d for d in documents if d.get('char_count', len(d['text'])) > LARGE_THRESHOLD]
    if large:
        print(f'⚠️ 超大chunks (>{LARGE_THRESHOLD}字符): {len(large)}')
        for d in large[:3]:
            print(f'   {d["source"][:50]} | {d["char_count"]}字符')
    else:
        print(f'✅ 无超大chunks')
    
    # 4. 跨文件重复检测（仅比较不同文件）
    text_to_source = {}
    real_dups = 0
    dup_pairs = []
    for d in documents:
        t = d['text'][:200]
        if t in text_to_source:
            if text_to_source[t] != d['source']:
                real_dups += 1
                if real_dups <= 5:
                    dup_pairs.append((text_to_source[t][:50], d['source'][:50]))
        else:
            text_to_source[t] = d['source']
    if real_dups:
        print(f'\n⚠️ 跨文件重复chunks: {real_dups}')
        for a, b in dup_pairs:
            print(f'   {a} == {b}')
    else:
        print(f'\n✅ 无重复chunks')
    
    # 5. 日期覆盖
    dated = [d for d in documents if d.get('effective_date')]
    pct = len(dated) * 100 // len(documents) if documents else 0
    print(f'\n📅 日期覆盖: {len(dated)}/{len(documents)} ({pct}%)')
    no_date = [d for d in documents if not d.get('effective_date')]
    if no_date:
        no_date_sources = set(d['source'] for d in no_date)
        print(f'   无日期文件: {len(no_date_sources)} 个')
    
    # 6. 类型分布
    types = {}
    for d in documents:
        t = d.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    print(f'\n📊 类型分布:')
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f'   {t}: {c}')
    
    # 7. 来源文件数
    sources = set(d['source'] for d in documents)
    print(f'\n📁 来源文件: {len(sources)}')
    
    # 8. 生成报告
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_chunks': len(documents),
        'avg_size': avg,
        'fragments': len(small),
        'oversized': len(large),
        'date_coverage': f'{pct}%',
        'duplicates': real_dups,
        'files': len(sources),
        'types': types,
        'issues': [],
    }
    if small: report['issues'].append(f'{len(small)} 碎片chunks(<{SMALL_THRESHOLD}字符)')
    if large: report['issues'].append(f'{len(large)} 超大chunks(>{LARGE_THRESHOLD}字符)')
    if real_dups: report['issues'].append(f'{real_dups} 跨文件重复')
    if pct < 50: report['issues'].append(f'日期覆盖率 {pct}% < 50%')
    
    report_path = os.path.join(REPORT_DIR, f'qc_{time.strftime("%Y%m%d_%H%M%S")}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 最近5次趋势
    reports = sorted(os.listdir(REPORT_DIR))[-5:]
    if len(reports) > 1:
        print(f'\n📈 趋势 (最近{len(reports)}次):')
        for rp in reports:
            with open(os.path.join(REPORT_DIR, rp), 'r', encoding='utf-8') as f:
                r = json.load(f)
            print(f'   {r["timestamp"][:10]} | {r["total_chunks"]} chunks | 碎片:{r["fragments"]} | 重复:{r["duplicates"]}')
    
    print(f'\n报告已保存: {report_path}')
    if report['issues']:
        print(f'\n⚠️ 待处理: {", ".join(report["issues"])}')
    else:
        print(f'\n✅ 知识库状态良好')
    
    return report

if __name__ == '__main__':
    run_check()