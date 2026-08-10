"""
深度内容去重：余弦相似度 + 关键词指纹
"""
import os, sys, re, json, hashlib
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

KB = r'D:\openclaw-workspace\knowledge'
SIMILARITY_THRESHOLD = 0.75  # 相似度阈值

def tokenize(text):
    """简单中文分词：2-gram字符级"""
    text = re.sub(r'[^\u4e00-\u9fff\w]', '', text)
    return [text[i:i+3] for i in range(len(text)-2)]

def get_fingerprint(text):
    """内容指纹（前1000字符的3-gram哈希）"""
    tokens = tokenize(text[:3000])
    if len(tokens) < 10:
        return None
    # 取Top 50的3-gram做指纹
    counter = Counter(tokens)
    top = [t for t, _ in counter.most_common(50)]
    return hashlib.md5(''.join(sorted(top)).encode()).hexdigest()

def jaccard_similarity(text1, text2, sample_size=100):
    """快速Jaccard相似度（采样）"""
    t1 = set(tokenize(text1[:5000])[:sample_size])
    t2 = set(tokenize(text2[:5000])[:sample_size])
    if not t1 or not t2:
        return 0
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union if union > 0 else 0

def main():
    print("扫描知识库...")
    all_files = []
    for root, dirs, files in os.walk(KB):
        rel = os.path.relpath(root, KB)
        # 跳过非业务目录
        skip = False
        for s in ['literature', 'laws', 'policies', '_cleaned', '_bak', '.rag']:
            if rel.startswith(s):
                skip = True
                break
        if skip:
            continue
        
        for f in files:
            if f.endswith('.md'):
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                if sz < 200:
                    continue  # 跳过空文件
                all_files.append((fp, rel, f))
    
    print(f"待检查: {len(all_files)} 个文件（已跳过<200B空文件）")
    
    # === 按内容指纹分组 ===
    print("\n计算内容指纹...")
    fp_groups = {}
    for i, (fp, rel, f) in enumerate(all_files):
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read(10000)
            sig = get_fingerprint(content)
            if sig:
                if sig not in fp_groups:
                    fp_groups[sig] = []
                fp_groups[sig].append((fp, rel, f))
        except:
            pass
        if (i+1) % 500 == 0:
            print(f"  进度: {i+1}/{len(all_files)}")
    
    # === 指纹去重 ===
    dup_count = 0
    dup_groups = {}
    for sig, group in fp_groups.items():
        if len(group) > 1:
            dup_groups[sig] = group
            dup_count += len(group) - 1
    
    print(f"\n指纹重复: {len(dup_groups)} 组, 可去重 {dup_count} 篇")
    
    # === 跨指纹相似度检查 ===
    print("\n跨指纹相似度检查（采样模式）...")
    # 只在同目录内做相似度比较（效率）
    dir_groups = {}
    for fp, rel, f in all_files:
        d = os.path.dirname(rel)
        if d not in dir_groups:
            dir_groups[d] = []
        dir_groups[d].append((fp, rel, f))
    
    similar_pairs = []
    for d, files in dir_groups.items():
        if len(files) < 2:
            continue
        for i in range(len(files)):
            for j in range(i+1, min(i+20, len(files))):  # 限制比较范围
                # 快速预筛：文件大小相差>50%跳过
                sz1 = os.path.getsize(files[i][0])
                sz2 = os.path.getsize(files[j][0])
                if sz1 > 0 and sz2 > 0:
                    ratio = min(sz1, sz2) / max(sz1, sz2)
                    if ratio < 0.5:
                        continue
                
                try:
                    with open(files[i][0], 'r', encoding='utf-8', errors='ignore') as fh:
                        t1 = fh.read(5000)
                    with open(files[j][0], 'r', encoding='utf-8', errors='ignore') as fh:
                        t2 = fh.read(5000)
                    
                    sim = jaccard_similarity(t1, t2)
                    if sim > SIMILARITY_THRESHOLD:
                        similar_pairs.append((files[i], files[j], sim))
                except:
                    pass
    
    print(f"  高相似度对: {len(similar_pairs)} 对")
    
    # === 输出报告 ===
    print("\n" + "=" * 60)
    print("  重复分析报告")
    print("=" * 60)
    
    # 指纹重复
    if dup_groups:
        print(f"\n指纹完全相同 ({len(dup_groups)}组):")
        for sig, group in list(dup_groups.items())[:20]:
            sizes = [os.path.getsize(f[0]) for f in group]
            print(f"\n  组 ({len(group)}份):")
            for fp, rel, f in group:
                sz = os.path.getsize(fp)
                print(f"    [{rel}] {f[:80]} ({sz/1024:.0f}KB)")
    
    # 高相似度
    if similar_pairs:
        print(f"\n\n高相似度 ({len(similar_pairs)}对, 阈值>{SIMILARITY_THRESHOLD}):")
        for (fp1, r1, f1), (fp2, r2, f2), sim in sorted(similar_pairs, key=lambda x: -x[2])[:20]:
            print(f"\n  {sim:.0%} 相似:")
            print(f"    A [{r1}] {f1[:80]}")
            print(f"    B [{r2}] {f2[:80]}")
    
    total_dup = dup_count + len(similar_pairs)
    print(f"\n{'='*60}")
    print(f"总计可去重: {dup_count} (指纹) + {len(similar_pairs)} (高相似) = {total_dup} 篇")
    print(f"如需执行，运行: python scripts/_deep_dedup.py --execute")

if __name__ == '__main__':
    main()
