"""L11 — 供应商伴随投标（跨项目共现分析）参考实现
输入: 多个项目的投标人名单 + 中标结果
输出: 共现矩阵 + 围标集团清单
"""
import json, sys
from itertools import combinations

# ===== 示例数据结构 =====
# 实际使用时替换为从数据库/Excel读取
sample_projects = [
    {
        "id": "P001", "name": "宿舍监理", "date": "2025-11-19",
        "bidders": ["伟业启航","五行建设","华宇监理","深圳银建安","德阳鑫华","卓昇","良友建设","元博","衡泰","华西设计", "...总共22家"],
        "winner": "良友建设"
    },
    # ... 更多项目
]

def compute_cross_project_matrix(projects):
    """计算任意两家公司的跨项目共现矩阵"""
    # 收集所有公司和项目映射
    all_companies = set()
    company_projects = {}  # company -> set of project_ids
    
    for p in projects:
        pid = p["id"]
        for c in p["bidders"]:
            all_companies.add(c)
            if c not in company_projects:
                company_projects[c] = set()
            company_projects[c].add(pid)
    
    # 计算共现
    pairs = []
    for a, b in combinations(sorted(all_companies), 2):
        projs_a = company_projects.get(a, set())
        projs_b = company_projects.get(b, set())
        co_projs = projs_a & projs_b
        union_projs = projs_a | projs_b
        
        if len(co_projs) >= 1:
            jaccard = len(co_projs) / len(union_projs) if union_projs else 0
            pairs.append({
                "company_a": a, "company_b": b,
                "co_occurrences": len(co_projs),
                "total_a": len(projs_a), "total_b": len(projs_b),
                "jaccard": round(jaccard, 4),
                "projects": sorted(co_projs)
            })
    
    pairs.sort(key=lambda x: (-x["co_occurrences"], -x["jaccard"]))
    return pairs

def detect_bid_rings(projects, pairs, jaccard_threshold=0.5, co_threshold=2):
    """识别围标集团"""
    # 构建图（共现次数>=阈值 或 Jaccard>=阈值）
    import collections
    graph = collections.defaultdict(set)
    
    for pair in pairs:
        if pair["co_occurrences"] >= co_threshold and pair["jaccard"] >= jaccard_threshold:
            a, b = pair["company_a"], pair["company_b"]
            graph[a].add(b)
            graph[b].add(a)
    
    # 连通分量（集团）
    visited = set()
    rings = []
    
    def dfs(node, component):
        visited.add(node)
        component.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor, component)
    
    for company in graph:
        if company not in visited:
            component = []
            dfs(company, component)
            if len(component) >= 3:
                # 检查中标集中度
                win_counts = {}
                for c in component:
                    for p in projects:
                        if c in p["bidders"] and c == p.get("winner"):
                            win_counts[c] = win_counts.get(c, 0) + 1
                total_wins = sum(win_counts.values())
                concentration = max(win_counts.values()) / total_wins if total_wins else 0
                
                rings.append({
                    "members": sorted(component),
                    "size": len(component),
                    "win_concentration": round(concentration, 3),
                    "top_winner": max(win_counts, key=win_counts.get) if win_counts else None
                })
    
    return rings

# ===== CLI 接口 =====
if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            projects = json.load(f)
    else:
        projects = sample_projects
    
    pairs = compute_cross_project_matrix(projects)
    rings = detect_bid_rings(projects, pairs)
    
    print(f"Projects analyzed: {len(projects)}")
    print(f"Cross-project pairs: {len(pairs)}")
    print(f"Bid rings detected: {len(rings)}")
    print()
    
    for i, ring in enumerate(rings):
        print(f"[Ring {i+1}] Size={ring['size']} WinConcentration={ring['win_concentration']}")
        print(f"  Members: {', '.join(ring['members'])}")
        if ring['top_winner']:
            print(f"  Top winner: {ring['top_winner']}")
    print()
    
    # Top 10 most frequent co-occurrences
    print("Top 10 co-occurring pairs:")
    for pair in pairs[:10]:
        print(f"  {pair['company_a']} ↔ {pair['company_b']}: "
              f"{pair['co_occurrences']}x Jaccard={pair['jaccard']}")
