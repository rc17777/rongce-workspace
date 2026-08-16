"""技能③ 模糊名称匹配 — 发现关联企业/名称变体
来源：泉州医保 utl_match.edit_distance_similarity
替代：Python fuzzywuzzy / rapidfuzz (无需Oracle)
用途：自动发现名称高度相似但不同的投标人/供应商
"""
import sys
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

try:
    from rapidfuzz import fuzz, process
    HAS_FUZZ = True
except ImportError:
    try:
        from difflib import SequenceMatcher
        HAS_FUZZ = False
        
        def fuzz_ratio(a, b):
            return int(SequenceMatcher(None, a, b).ratio() * 100)
    except:
        print("安装: pip install rapidfuzz (或 pip install fuzzywuzzy)"); sys.exit(1)


def fuzzy_match_names(names, threshold=80):
    """对名称列表进行两两模糊匹配
    
    names: ["四川XX建设工程有限公司", "四川XX建设工程集团有限公司", ...]
    threshold: 相似度阈值(0-100)，默认80
    
    返回: 超过阈值的相似对
    """
    if HAS_FUZZ:
        from rapidfuzz import fuzz
    
    results = []
    seen_pairs = set()
    
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pair = tuple(sorted([names[i], names[j]]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            
            if HAS_FUZZ:
                sim = fuzz.ratio(names[i], names[j])
            else:
                sim = fuzz_ratio(names[i], names[j])
            
            if sim >= threshold:
                results.append({
                    "名称A": names[i],
                    "名称B": names[j],
                    "相似度%": sim,
                    "长度差": abs(len(names[i]) - len(names[j]))
                })
    
    results.sort(key=lambda x: -x["相似度%"])
    return results


def extract_core_name(full_name):
    """从公司全名中提取核心名称
    
    "四川融策建设工程有限公司" → "融策"
    去掉：省市区县 + 行业后缀(建设/工程/咨询/管理) + 公司类型(有限公司/集团)
    """
    # 常见前缀
    prefixes = ["中国", "四川", "成都", "重庆", "北京", "上海", "广东",
                "四川省", "成都市", "重庆市", "北京市", "上海市", "广东省",
                "成都市", "绵阳市", "德阳市", "宜宾市", "泸州市", "南充市",
                "武侯区", "高新区", "天府新区"]
    
    # 常见后缀
    suffixes = [
        "建设工程有限公司", "建设工程集团有限公司", "建设集团有限公司",
        "工程咨询有限公司", "项目管理有限公司", "项目管理咨询有限公司",
        "工程管理有限公司", "工程造价咨询有限公司", "招标代理有限公司",
        "勘察设计有限公司", "监理有限公司", "工程监理有限公司",
        "集团有限公司", "有限公司", "有限责任公司", "股份公司",
        "建筑工程有限公司", "市政工程有限公司", "公路工程有限公司",
        "建筑设计有限公司", "规划设计有限公司", "勘察设计院有限公司",
        "会计师事务所", "资产评估有限公司", "房地产评估有限公司",
        "咨询有限公司", "科技有限公司", "信息技术有限公司",
        "建设有限公司", "工程有限公司", "实业有限公司",
    ]
    
    core = full_name
    
    # 去前缀
    for p in sorted(prefixes, key=len, reverse=True):
        if core.startswith(p):
            core = core[len(p):]
            break
    
    # 去后缀
    for s in sorted(suffixes, key=len, reverse=True):
        if core.endswith(s):
            core = core[:-len(s)]
            break
    
    return core if core else full_name


def cluster_similar_names(names, threshold=80):
    """将相似名称聚类为组
    
    用途：发现同一老板注册的多家公司
    输出：[["公司A","公司A1","公司A2"], ["公司B","公司B1"]]
    """
    # 构建相似图
    graph = defaultdict(set)
    pairs = fuzzy_match_names(names, threshold)
    
    for pair in pairs:
        graph[pair["名称A"]].add(pair["名称B"])
        graph[pair["名称B"]].add(pair["名称A"])
    
    # DFS找连通组件
    visited = set()
    clusters = []
    
    def dfs(node, cluster):
        visited.add(node)
        cluster.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor, cluster)
    
    for name in names:
        if name not in visited:
            cluster = []
            dfs(name, cluster)
            if len(cluster) >= 2:  # 只保留>=2的簇
                clusters.append(cluster)
    
    clusters.sort(key=lambda x: -len(x))
    return clusters


# ===== 自定义规则匹配 =====
CUSTOM_PATTERNS = {
    "核心词相同+后缀不同": {
        "pattern": "同一核心名称，不同的企业类型后缀",
        "risk": "🟡 中风险：可能是同一母公司下的不同业务板块",
        "examples": ["融策建设 vs 融策咨询 vs 融策管理"]
    },
    "核心词相同+行政区划不同": {
        "pattern": "同一核心名称，不同省市前缀",
        "risk": "🔴 高风险：可能是跨省围标策略",
        "examples": ["四川融策建设 vs 重庆融策建设"]
    },
    "顺序颠倒": {
        "pattern": "名称中词语排列顺序不同",
        "risk": "🔴 高风险：刻意制造名称差异",
        "examples": ["华西建设工程 vs 华西建设 工程"]
    },
    "添加/减少修饰词": {
        "pattern": "增加或减少修饰词（如'新'、'大'、'鑫'）",
        "risk": "🟡 中风险",
        "examples": ["宏达建设 vs 新宏达建设"]
    }
}


# ===== 示例 =====
if __name__ == "__main__":
    print("=" * 60)
    print("模糊名称匹配 — 关联企业发现")
    print("=" * 60)
    
    names = [
        "四川融策建设工程有限公司",
        "四川融策建设工程集团有限公司",
        "四川融策工程咨询有限公司",
        "重庆融策建设工程有限公司",
        "成都华西建筑工程有限公司",
        "成都华西建设工程有限公司",
        "德阳宏达建设有限公司",
        "四川新宏达建设有限公司",
        "四川宏达建设工程有限公司",
        "成都明远项目管理有限公司",
        "成都明远项目管理咨询有限公司",
        "四川凯德建设工程有限公司",
        "四川凯德建筑设计有限公司",
        "成都天府建筑设计有限公司",
        "成都天府规划建筑设计有限公司",
        "西南建筑设计研究院有限公司",
        "中国建筑西南设计研究院有限公司",
    ]
    
    print(f"\n名称总数: {len(names)}")
    print(f"阈值: 80%相似度\n")
    
    # 模糊匹配
    matches = fuzzy_match_names(names, threshold=80)
    print(f"找到 {len(matches)} 对相似名称:\n")
    
    for m in matches:
        bar = "█" * int((m["相似度%"] - 80) * 2)
        core_a = extract_core_name(m["名称A"])
        core_b = extract_core_name(m["名称B"])
        shared = "同一核心" if core_a == core_b else f"{core_a} vs {core_b}"
        print(f"  {m['相似度%']}% {bar}")
        print(f"  A: {m['名称A']}")
        print(f"  B: {m['名称B']}")
        print(f"     核心: {shared} | 长度差:{m['长度差']}")
        print()
    
    # 聚类
    clusters = cluster_similar_names(names, threshold=75)
    print(f"--- 名称聚类 ({len(clusters)}个簇) ---")
    for i, cluster in enumerate(clusters):
        if len(cluster) >= 3:
            print(f"\n  🔴 簇{i+1} ({len(cluster)}家):")
        else:
            print(f"\n  🟡 簇{i+1} ({len(cluster)}家):")
        for name in cluster:
            print(f"    · {name}")
