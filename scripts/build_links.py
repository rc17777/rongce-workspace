"""
知识库双向链接构建器 v2 - build_links.py（优化版）
使用 TF-IDF + 余弦相似度，为每篇笔记自动推荐相关内容。
"""
import os, sys, json, re, time, math
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
KNOWLEDGE = WORKSPACE / "knowledge"
OBSIDIAN = WORKSPACE / "obsidian-vault"
OUTPUT = WORKSPACE / "knowledge" / "related_links.json"

def tokenize(text: str) -> list:
    """轻量中文分词：按标点切分 + 2-3字 n-gram"""
    text = re.sub(r'[^\u4e00-\u9fff\w]', ' ', text)
    words = set()
    for w in text.split():
        w = w.strip()
        if not w or len(w) < 2:
            continue
        words.add(w[:20])
        for n in (2, 3):
            for i in range(len(w)-n+1):
                words.add(w[i:i+n])
    return list(words)

def extract_title(path: Path, content: str) -> str:
    for line in content.split('\n')[:5]:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return path.stem

def has_frontmatter(content: str) -> bool:
    return content.strip().startswith('---')

def update_frontmatter(content: str, related: list) -> str:
    """添加 related 字段到 frontmatter"""
    links = '\n'.join(f'  - "[[{r}]]"' for r in related)
    
    if not has_frontmatter(content):
        fm = f'---\nrelated:\n{links}\n---\n\n{content}'
        return fm
    
    lines = content.split('\n')
    new_lines = []
    in_fm = False
    has_related = False
    
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == '---':
            in_fm = True
            new_lines.append(line)
        elif in_fm and line.strip() == '---':
            if not has_related:
                new_lines.append(f'related:')
                for r in related:
                    new_lines.append(f'  - "[[{r}]]"')
            new_lines.append('---')
            in_fm = False
        elif in_fm and line.strip().startswith('related'):
            has_related = True
        elif in_fm:
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def main(mode="scan"):
    print("=" * 60)
    print("  知识库双向链接构建器 v2")
    print(f"  {time.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 1. 加载文件（过滤：200B-50KB）
    docs = {}
    paths = []
    for root in [KNOWLEDGE, OBSIDIAN]:
        if not root.exists():
            continue
        md_files = list(root.rglob("*.md"))
        print(f"  {root.name}: {len(md_files)} 个 .md 文件")
        for f in md_files:
            fsize = f.stat().st_size
            if fsize < 200 or fsize > 50000:
                continue
            if any(s in f.parts for s in {'.obsidian', '_templates', 'archives', '.git'}):
                continue
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                rel_path = str(f.relative_to(WORKSPACE))
                docs[rel_path] = content[:3000]
                paths.append((rel_path, f))
            except:
                pass
    
    N = len(docs)
    print(f"\n📊 参与计算: {N} 篇")
    if N == 0:
        print("  无有效文件，退出")
        return {}
    
    # 2. TF-IDF
    print("🔧 构建 TF-IDF...")
    t0 = time.time()
    doc_tokens = {k: tokenize(v) for k, v in docs.items()}
    
    df = Counter()
    for tokens in doc_tokens.values():
        for t in set(tokens):
            df[t] += 1
    
    idf = {t: math.log(N / (df[t] + 1)) + 1 for t in df}
    
    vectors = {}
    for path, tokens in doc_tokens.items():
        tf = Counter(tokens)
        vec = {t: tf[t] * idf[t] for t in tf if tf[t] * idf[t] > 0.3}
        vectors[path] = vec
    
    print(f"   完成 ({time.time()-t0:.1f}s)")
    
    # 3. 相似度（预计算范数优化）
    print("🔗 计算相似度...")
    t0 = time.time()
    related_map = {}
    file_list = list(vectors.keys())
    
    norms = {f: math.sqrt(sum(v**2 for v in vec.values())) for f, vec in vectors.items()}
    
    for i, f1 in enumerate(file_list):
        if i % 50 == 0:
            print(f"   {i}/{N}...")
        
        vec1 = vectors[f1]
        norm1 = norms[f1]
        if norm1 == 0:
            related_map[f1] = []
            continue
        
        sims = []
        for f2 in file_list:
            if f1 == f2:
                continue
            # 快速排除：共享词太少的跳过
            common = set(vec1) & set(vectors[f2])
            if len(common) < 3:
                continue
            norm2 = norms[f2]
            if norm2 == 0:
                continue
            dot = sum(vec1[t] * vectors[f2][t] for t in common)
            sim = dot / (norm1 * norm2)
            if sim > 0.08:
                sims.append((f2, sim))
        
        sims.sort(key=lambda x: x[1], reverse=True)
        related_map[f1] = [{"path": p, "score": round(s, 3)} for p, s in sims[:5]]
    
    print(f"   完成 ({time.time()-t0:.1f}s)")
    
    # 统计
    has_links = sum(1 for v in related_map.values() if v)
    avg_links = sum(len(v) for v in related_map.values()) / max(N, 1)
    print(f"\n📊 链接统计")
    print(f"  有链接的文件: {has_links}/{N} ({has_links*100//N}%)")
    print(f"  平均链接数: {avg_links:.1f}")
    
    # 样例
    print(f"\n📋 样例 (Top 5)")
    for path in sorted(related_map, key=lambda p: len(related_map[p]), reverse=True)[:5]:
        links = related_map[path]
        if links:
            print(f"  📄 {path} ({len(links)} 个关联)")
            for l in links[:3]:
                print(f"     [{l['score']:.3f}] → {l['path']}")
    
    # 保存 JSON
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(related_map, f, ensure_ascii=False, indent=2)
    print(f"\n💾 已保存: {OUTPUT}")
    
    # 写入 frontmatter
    if mode == "write":
        written = 0
        for rel_path, abs_path in paths:
            if rel_path in related_map and related_map[rel_path]:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                titles = []
                for r in related_map[rel_path][:3]:
                    rpath = WORKSPACE / r["path"]
                    if rpath.exists():
                        with open(rpath, 'r', encoding='utf-8') as rf:
                            titles.append(extract_title(rpath, rf.read()))
                if titles:
                    nc = update_frontmatter(content, titles)
                    with open(abs_path, 'w', encoding='utf-8') as f:
                        f.write(nc)
                    written += 1
        print(f"✍️ 已更新 {written} 个文件的 frontmatter")
    
    return related_map

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"
    main(mode)
