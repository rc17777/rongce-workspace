"""技能⑧ 隐性网络构建 — "共同服务同一采购方"的供应商自动关联
来源：山东财大/审计厅 社会网络分析（《中国审计》2023年第8期）
核心：隐藏采购方 → 仅保留供应商关系 → 发现隐性围标集团

显性：A→[中标]→教育局 ←[中标]←B → 隐性：A————B
"""
import sys, json
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

try:
    import networkx as nx
except ImportError:
    print("需要: pip install networkx"); sys.exit(1)


def build_explicit_network(project_data):
    """构建显性网络：采购方 ⟷ 供应商（双向）
    
    输入: [{"采购方":"教育局","供应商":"A","金额":100}, ...]
    输出: networkx Graph
    """
    G = nx.Graph()
    for record in project_data:
        buyer = record.get("采购方")
        supplier = record.get("供应商")
        amount = record.get("金额", 1)
        
        if buyer and supplier:
            # 累加边的权重
            if G.has_edge(buyer, supplier):
                G[buyer][supplier]["weight"] += amount
                G[buyer][supplier]["count"] = G[buyer][supplier].get("count", 0) + 1
            else:
                G.add_edge(buyer, supplier, weight=amount, count=1)
    
    return G


def build_implicit_supplier_network(project_data):
    """构建隐性供应商网络（隐藏采购方）
    
    算法：
    1. 找出每个采购方关联的所有供应商
    2. 共同服务同一采购方的供应商之间建立边
    3. 边权重=共同服务的采购方数量
    
    这就是审计署太原办说的"隐性网络"
    """
    # 按采购方分组
    buyer_suppliers = defaultdict(set)
    for record in project_data:
        buyer = record.get("采购方")
        supplier = record.get("供应商")
        if buyer and supplier:
            buyer_suppliers[buyer].add(supplier)
    
    # 构建供应商间的关系
    G = nx.Graph()
    edge_weights = defaultdict(lambda: {"weight": 0, "buyers": set()})
    
    for buyer, suppliers in buyer_suppliers.items():
        suppliers = list(suppliers)
        for i in range(len(suppliers)):
            G.add_node(suppliers[i])  # 确保孤立节点也存在
            for j in range(i+1, len(suppliers)):
                a, b = sorted([suppliers[i], suppliers[j]])
                edge_weights[(a, b)]["weight"] += 1
                edge_weights[(a, b)]["buyers"].add(buyer)
    
    for (a, b), data in edge_weights.items():
        G.add_edge(a, b, 
                   weight=data["weight"],
                   shared_buyers=sorted(data["buyers"]),
                   shared_count=len(data["buyers"]))
    
    return G


def analyze_implicit_network(G):
    """分析隐性供应商网络
    
    输出:
    - 核心供应商（中心性最高）
    - 供应商聚类（可能围标集团）
    - 孤立供应商（单打独斗，不太可能是围标）
    """
    results = {}
    
    # 1. 中心性分析
    deg_cent = nx.degree_centrality(G) if G.number_of_nodes() > 0 else {}
    between_cent = (nx.betweenness_centrality(G, weight='weight') 
                    if G.number_of_nodes() > 0 else {})
    
    # 核心节点（度中心性 > 均值的1.5倍）
    avg_deg = sum(deg_cent.values()) / len(deg_cent) if deg_cent else 0
    hubs = {node: {"degree_cent": round(deg, 3),
                   "between_cent": round(between_cent.get(node, 0), 3),
                   "connections": G.degree(node)}
            for node, deg in deg_cent.items() 
            if deg >= avg_deg * 1.5}
    
    results["核心节点"] = sorted(hubs.items(), 
                               key=lambda x: -x[1]["between_cent"])
    
    # 2. 聚类/社区发现
    try:
        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(G)
        results["社区"] = [sorted(list(c)) for c in communities 
                          if len(c) >= 2]
    except:
        # Fallback: 连通分量
        results["社区"] = [sorted(list(c)) 
                          for c in nx.connected_components(G)
                          if len(c) >= 2]
    
    # 3. 强边（共享多个采购方）
    strong_edges = []
    for u, v, data in G.edges(data=True):
        if data.get("shared_count", 0) >= 2:
            strong_edges.append({
                "供应商A": u,
                "供应商B": v,
                "共同客户数": data["shared_count"],
                "客户": data.get("shared_buyers", [])
            })
    results["强关联边"] = sorted(strong_edges, 
                                key=lambda x: -x["共同客户数"])
    
    # 4. 孤立节点
    isolated = [n for n in G.nodes() if G.degree(n) == 0]
    results["孤立供应商"] = isolated
    
    return results


def find_bid_ring_implicit(project_data, min_shared_buyers=2):
    """从隐性网络中发现围标团伙
    
    规则：
    1. 多个供应商共同服务同一采购方≥min_shared_buyers次
    2. 这些供应商在网络中形成密集子图
    3. 且至少有一家中标率异常高
    """
    G = build_implicit_supplier_network(project_data)
    
    # 找出所有完全子图（clique）
    cliques = [sorted(c) for c in nx.find_cliques(G) if len(c) >= 3]
    
    # 为每个clique计算中标集中度
    rings = []
    for clique in cliques:
        # 统计每个成员在项目中的中标次数
        win_counts = defaultdict(int)
        total_bids = defaultdict(int)
        
        for record in project_data:
            supplier = record.get("供应商")
            if supplier in clique:
                total_bids[supplier] += 1
                if record.get("是否中标"):
                    win_counts[supplier] += 1
        
        total_wins = sum(win_counts.values())
        concentration = max(win_counts.values()) / total_wins \
                        if total_wins > 0 else 0
        
        if concentration >= 0.7:  # 中标集中度高
            rings.append({
                "成员": clique,
                "规模": len(clique),
                "中标集中度": round(concentration, 3),
                "主中标人": max(win_counts, key=win_counts.get) if win_counts else None,
                "投标记录": dict(total_bids),
                "中标记录": dict(win_counts)
            })
    
    rings.sort(key=lambda x: (-x["中标集中度"], -x["规模"]))
    return rings


# ===== 示例 =====
if __name__ == "__main__":
    print("=" * 60)
    print("隐性供应商网络构建 — 围标集团发现")
    print("=" * 60)
    
    # 模拟：6个采购方，多方多次中标记录
    data = [
        # 教育局 — A/B/C三家轮流中标
        {"采购方":"教育局","供应商":"A建设","金额":100,"是否中标":True},
        {"采购方":"教育局","供应商":"B建设","金额":95,"是否中标":False},
        {"采购方":"教育局","供应商":"C建设","金额":98,"是否中标":False},
        {"采购方":"教育局","供应商":"A建设","金额":200,"是否中标":True},
        {"采购方":"教育局","供应商":"B建设","金额":190,"是否中标":False},
        {"采购方":"教育局","供应商":"C建设","金额":195,"是否中标":False},
        # 交通局 — A/B/C再次出现
        {"采购方":"交通局","供应商":"A建设","金额":300,"是否中标":True},
        {"采购方":"交通局","供应商":"B建设","金额":280,"是否中标":False},
        {"采购方":"交通局","供应商":"C建设","金额":290,"是否中标":False},
        # 住建局 — A/B/C再次出现
        {"采购方":"住建局","供应商":"A建设","金额":150,"是否中标":True},
        {"采购方":"住建局","供应商":"B建设","金额":145,"是否中标":False},
        {"采购方":"住建局","供应商":"C建设","金额":148,"是否中标":False},
        # 另一组 — X/Y/Z固定搭配
        {"采购方":"水务局","供应商":"X咨询","金额":80,"是否中标":True},
        {"采购方":"水务局","供应商":"Y咨询","金额":75,"是否中标":False},
        {"采购方":"水务局","供应商":"Z咨询","金额":78,"是否中标":False},
        {"采购方":"环保局","供应商":"X咨询","金额":120,"是否中标":True},
        {"采购方":"环保局","供应商":"Y咨询","金额":115,"是否中标":False},
        {"采购方":"环保局","供应商":"Z咨询","金额":118,"是否中标":False},
        # 独立供应商（不跟别人搭伙）
        {"采购方":"教育局","供应商":"独立建设","金额":50,"是否中标":True},
    ]
    
    # 构建隐性网络
    G = build_implicit_supplier_network(data)
    print(f"\n显性边(采购方-供应商): {len([r for r in data if r.get('采购方')])}")
    print(f"隐性节点(供应商): {G.number_of_nodes()}")
    print(f"隐性边(供应商-供应商): {G.number_of_edges()}")
    
    # 分析
    analysis = analyze_implicit_network(G)
    
    print(f"\n--- 核心供应商 ---")
    for name, info in analysis["核心节点"][:5]:
        print(f"  {name}: 连接{info['connections']}家 | "
              f"度中心={info['degree_cent']:.3f} | 中介中心={info['between_cent']:.3f}")
    
    print(f"\n--- 供应商社区 ---")
    for i, comm in enumerate(analysis["社区"]):
        print(f"  社区{i+1}: {', '.join(comm)}")
    
    print(f"\n--- 强关联边（共同客户≥2）---")
    for edge in analysis["强关联边"]:
        print(f"  {edge['供应商A']} ↔ {edge['供应商B']}: "
              f"{edge['共同客户数']}个共同客户: {edge['客户']}")
    
    if analysis["孤立供应商"]:
        print(f"\n--- 孤立供应商 ---")
        print(f"  {', '.join(analysis['孤立供应商'])}")
    
    # 围标团伙发现
    print(f"\n--- 围标团伙 ---")
    rings = find_bid_ring_implicit(data, min_shared_buyers=2)
    for i, ring in enumerate(rings):
        print(f"\n  🔴 团伙{i+1}: {'+'.join(ring['成员'])}")
        print(f"     中标集中度: {ring['中标集中度']:.3f}")
        print(f"     主中标人: {ring['主中标人']}")
        for member, bids in ring["投标记录"].items():
            wins = ring["中标记录"].get(member, 0)
            print(f"       {member}: {wins}/{bids}中标")
