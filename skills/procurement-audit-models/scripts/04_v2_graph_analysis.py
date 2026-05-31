"""L8 v2.0 — 图数据库多层股权穿透 + 投标人关系网络分析
基于《中国审计》2023年第4期 审计署太原特派办方法
替代Neo4j：使用networkx（免安装图数据库，Python原生）
"""
import sys, json
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

try:
    import networkx as nx
    import numpy as np
except ImportError:
    print("Missing: pip install networkx numpy")
    sys.exit(1)


def build_supplier_network(projects):
    """构建供应商隐性网络（共同投标关系）
    
    输入: projects = [{id, bidders: [...], winner: ...}, ...]
    输出: networkx Graph，节点=投标人，边=共同投标次数
    """
    G = nx.Graph()
    co_occur = defaultdict(int)
    
    for proj in projects:
        bidders = proj.get("bidders", [])
        for i in range(len(bidders)):
            for j in range(i + 1, len(bidders)):
                pair = tuple(sorted([bidders[i], bidders[j]]))
                co_occur[pair] += 1
    
    for (a, b), count in co_occur.items():
        G.add_edge(a, b, weight=count, co_occurrences=count)
    
    return G


def analyze_centrality(G):
    """计算三种中心性指标，识别关键节点
    
    对标审计署太原办：点度中心性、中介中心性、接近中心性
    """
    results = {}
    
    # 点度中心性 - 与多少其他供应商有共同投标关系
    deg = nx.degree_centrality(G)
    
    # 中介中心性 - 桥接不同"团伙"的能力
    bet = nx.betweenness_centrality(G, weight='weight')
    
    # 接近中心性 - 到所有其他节点的平均距离
    clo = nx.closeness_centrality(G)
    
    for node in G.nodes():
        results[node] = {
            "degree": round(deg[node], 4),
            "betweenness": round(bet[node], 4),
            "closeness": round(clo[node], 4),
            "connections": G.degree(node)
        }
    
    return results


def find_cliques(G, min_size=3):
    """发现投标人派系（完全子图）→ 职业陪标团伙"""
    cliques = list(nx.find_cliques(G))
    return [c for c in cliques if len(c) >= min_size]


def detect_communities(G):
    """社区发现（louvain算法）→ 识别'抱团'群体"""
    try:
        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(G)
        return [sorted(list(c)) for c in communities]
    except ImportError:
        # Fallback: simple connected components
        return [sorted(list(c)) for c in nx.connected_components(G)]


def equity_penetration(shareholding_data):
    """股权多层穿透分析（模拟Neo4j Cypher查询）
    
    输入: shareholding_data = [
        {"from": "A公司", "to": "B公司", "ratio": 0.6},
        ...
    ]
    输出: 穿透持股关系（1-4层）
    """
    G = nx.DiGraph()
    for record in shareholding_data:
        G.add_edge(record["from"], record["to"], ratio=record["ratio"])
    
    # 多层穿透：对每一对节点，计算所有路径和穿透持股比例
    results = []
    nodes = list(G.nodes())
    
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i == j: continue
            src, dst = nodes[i], nodes[j]
            
            # 找到所有简单路径（最多4层）
            try:
                paths = list(nx.all_simple_paths(G, src, dst, cutoff=4))
                for path in paths:
                    # 计算穿透持股比例
                    ratio = 1.0
                    for k in range(len(path) - 1):
                        ratio *= G[path[k]][path[k+1]]["ratio"]
                    
                    if ratio >= 0.1:  # 至少10%
                        results.append({
                            "source": src,
                            "target": dst,
                            "path": " → ".join(path),
                            "layers": len(path) - 1,
                            "penetration_ratio": round(ratio, 4)
                        })
            except nx.NetworkXNoPath:
                pass
    
    # 排序：穿透层数深的高优先级
    results.sort(key=lambda x: (-x["layers"], -x["penetration_ratio"]))
    return results


def find_win_concentration(projects, clique_members):
    """评估派系/集团的中标集中度
    
    如果某"团伙"中固定一个人中标 → 围标信号
    """
    win_counts = defaultdict(int)
    total_bids = defaultdict(int)
    
    for proj in projects:
        members_in_proj = [m for m in clique_members if m in proj.get("bidders", [])]
        winner = proj.get("winner")
        
        for m in members_in_proj:
            total_bids[m] += 1
        
        if winner and winner in clique_members:
            win_counts[winner] += 1
    
    total = sum(win_counts.values())
    if total == 0:
        return None
    
    results = {
        "members": sorted(clique_members),
        "total_bids": dict(total_bids),
        "win_counts": dict(win_counts),
        "concentration": round(max(win_counts.values()) / total, 3) if total > 0 else 0,
        "top_winner": max(win_counts, key=win_counts.get) if win_counts else None
    }
    return results


# ===== 示例 =====
if __name__ == "__main__":
    # 模拟数据
    sample_projects = [
        {"id": "P1", "bidders": ["A","B","C","D","E"], "winner": "A"},
        {"id": "P2", "bidders": ["A","B","C","F","G"], "winner": "A"},
        {"id": "P3", "bidders": ["A","B","C","D","H"], "winner": "B"},
        {"id": "P4", "bidders": ["X","Y","Z","E","F"], "winner": "X"},
    ]
    
    print("=" * 60)
    print("图数据库分析 — 投标人关系网络")
    print("=" * 60)
    
    G = build_supplier_network(sample_projects)
    print(f"\nNodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    
    # 中心性分析
    centrality = analyze_centrality(G)
    print("\n--- 中心性排名 Top 5 ---")
    ranked = sorted(centrality.items(), key=lambda x: -x[1]["betweenness"])
    for name, scores in ranked[:5]:
        d, b, c = scores["degree"], scores["betweenness"], scores["closeness"]
        flag = "*** 双高!" if d > 0.3 and b > 0.3 else ""
        print(f"  {name:10s} deg={d:.3f} bet={b:.3f} clo={c:.3f} conn={scores['connections']} {flag}")
    
    # 派系发现
    cliques = find_cliques(G, min_size=3)
    print(f"\n--- 派系（完全子图，≥3人）: {len(cliques)}个 ---")
    for i, clique in enumerate(cliques):
        win_info = find_win_concentration(sample_projects, clique)
        if win_info:
            print(f"  [{i+1}] {clique} → 中标集中度={win_info['concentration']:.3f} "
                  f"主力:{win_info['top_winner']}")
    
    # 社区发现
    communities = detect_communities(G)
    print(f"\n--- 社区（抱团群体）: {len(communities)}个 ---")
    for i, comm in enumerate(communities):
        print(f"  [{i+1}] {comm}")
    
    # 股权穿透示例
    print(f"\n--- 股权穿透示例 ---")
    shareholding = [
        {"from": "A公司", "to": "B公司", "ratio": 1.0},
        {"from": "B公司", "to": "C公司", "ratio": 0.9},
        {"from": "C公司", "to": "D公司", "ratio": 0.9},
    ]
    penetrations = equity_penetration(shareholding)
    for p in penetrations:
        print(f"  {p['source']} → {p['target']}: {p['path']} = {p['penetration_ratio']:.1%}")
