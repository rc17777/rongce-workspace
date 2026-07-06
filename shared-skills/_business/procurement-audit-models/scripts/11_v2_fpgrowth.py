"""L11 v2.0 — FP-growth关联规则挖掘 找"职业陪标团伙"
基于《中国审计》2023年第4期 审计署太原特派办方法
替换L11 v1.0的简单Jaccard共现 → 频繁项集+置信度
"""
import sys, json
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

try:
    from mlxtend.frequent_patterns import fpgrowth
    from mlxtend.preprocessing import TransactionEncoder
    HAS_MLXTEND = True
except ImportError:
    HAS_MLXTEND = False


class SimpleFPGrowth:
    """简易FP-growth实现（无需mlxtend）
    
    算法：Apriori-like频繁项集挖掘
    """
    def __init__(self, min_support=3):
        self.min_support = min_support
    
    def fit(self, transactions):
        """找出所有频繁项集"""
        self.transactions = transactions
        self.n_transactions = len(transactions)
        
        # 统计单项
        item_counts = defaultdict(int)
        for t in transactions:
            for item in t:
                item_counts[item] += 1
        
        # 频繁单项
        self.freq_items = {k: v for k, v in item_counts.items() 
                          if v >= self.min_support}
        
        # 频繁项集（简化版：仅2-3项集）
        self.frequent_itemsets = []
        
        # 2-itemsets
        pair_counts = defaultdict(int)
        for t in transactions:
            items = sorted([i for i in t if i in self.freq_items])
            for i in range(len(items)):
                for j in range(i+1, len(items)):
                    pair_counts[(items[i], items[j])] += 1
        
        for (a, b), count in pair_counts.items():
            if count >= self.min_support:
                self.frequent_itemsets.append({
                    "items": frozenset([a, b]),
                    "support": count,
                    "support_ratio": round(count / self.n_transactions, 3)
                })
        
        # 3-itemsets
        triple_counts = defaultdict(int)
        for t in transactions:
            items = sorted([i for i in t if i in self.freq_items])
            for i in range(len(items)):
                for j in range(i+1, len(items)):
                    for k in range(j+1, len(items)):
                        triple_counts[(items[i], items[j], items[k])] += 1
        
        for (a, b, c), count in triple_counts.items():
            if count >= self.min_support:
                self.frequent_itemsets.append({
                    "items": frozenset([a, b, c]),
                    "support": count,
                    "support_ratio": round(count / self.n_transactions, 3)
                })
        
        return self
    
    def generate_rules(self, min_confidence=0.8):
        """从频繁项集生成关联规则"""
        rules = []
        
        for itemset_info in self.frequent_itemsets:
            items = list(itemset_info["items"])
            if len(items) < 2:
                continue
            
            from itertools import combinations
            for size in range(1, len(items)):
                for antecedent in combinations(items, size):
                    antecedent_set = frozenset(antecedent)
                    consequent_set = itemset_info["items"] - antecedent_set
                    
                    # 计算置信度
                    antecedent_support = 0
                    for iss in self.frequent_itemsets:
                        if iss["items"] == antecedent_set:
                            antecedent_support = iss["support"]
                            break
                    
                    if antecedent_support > 0:
                        confidence = itemset_info["support"] / antecedent_support
                        if confidence >= min_confidence:
                            rules.append({
                                "antecedent": antecedent_set,
                                "consequent": consequent_set,
                                "support": itemset_info["support"],
                                "confidence": round(confidence, 3)
                            })
        
        rules.sort(key=lambda x: -x["confidence"])
        return rules


def prepare_transactions(projects, min_participation=2):
    """将项目投标人名单转换为事务集
    
    每个项目 = 一个事务，事务内容 = 该项目的投标人集合
    """
    transactions = []
    for proj in projects:
        bidders = proj.get("bidders", [])
        if len(bidders) >= min_participation:
            transactions.append(sorted(bidders))
    return transactions


def find_bid_rings_fp(projects, min_support=3, min_confidence=0.8):
    """FP-growth找出陪标团伙
    
    对标审计署太原办：
    - 频繁项集 = "经常同时出现在同一项目的投标人集合"
    - 置信度 = "A参与 → B也参与"的概率
    - 结合中标集中度 → 识别职业陪标团伙
    """
    transactions = prepare_transactions(projects)
    
    if len(transactions) < min_support:
        return []
    
    fp = SimpleFPGrowth(min_support=min_support)
    fp.fit(transactions)
    rules = fp.generate_rules(min_confidence=min_confidence)
    
    # 对每个规则，检查中标集中度
    results = []
    for rule in rules:
        all_members = set(rule["antecedent"]) | set(rule["consequent"])
        
        # 统计这些成员在所有项目中的中标情况
        win_counts = defaultdict(int)
        for proj in projects:
            winner = proj.get("winner")
            for m in all_members:
                if m in proj.get("bidders", []) and winner == m:
                    win_counts[m] += 1
        
        total_wins = sum(win_counts.values())
        concentration = max(win_counts.values()) / total_wins if total_wins > 0 else 0
        
        results.append({
            "antecedent": sorted(rule["antecedent"]),
            "consequent": sorted(rule["consequent"]),
            "all_members": sorted(all_members),
            "support_count": rule["support"],
            "confidence": rule["confidence"],
            "win_concentration": round(concentration, 3),
            "top_winner": max(win_counts, key=win_counts.get) if win_counts else None,
            "assessment": "职业陪标团伙" if concentration >= 0.8 and rule["confidence"] >= 0.9
                         else "固定陪标伙伴" if concentration >= 0.7
                         else "频繁共同投标"
        })
    
    results.sort(key=lambda x: (-x["confidence"], -x["win_concentration"]))
    return results


# ===== 示例 =====
if __name__ == "__main__":
    # 模拟20个项目的数据
    projects = []
    for i in range(1, 11):
        projects.append({"id": f"P{i}", "bidders": ["A","B","C","D","E"], "winner": "A"})
    for i in range(11, 16):
        projects.append({"id": f"P{i}", "bidders": ["A","B","C","F","G"], "winner": "A"})
    for i in range(16, 21):
        projects.append({"id": f"P{i}", "bidders": ["X","Y","Z","M","N"], "winner": "X"})
    
    print("=" * 60)
    print("FP-growth 关联规则挖掘 — 职业陪标团伙检测")
    print("=" * 60)
    print(f"Projects: {len(projects)}")
    print(f"Min support: 3 | Min confidence: 0.80")
    print()
    
    rings = find_bid_rings_fp(projects, min_support=3, min_confidence=0.8)
    
    print(f"Found {len(rings)}关联规则:")
    for i, ring in enumerate(rings):
        ant = ', '.join(ring['antecedent'])
        con = ', '.join(ring['consequent'])
        ass = ring['assessment']
        flag = "🔴" if '职业' in ass else ("🟡" if '固定' in ass else "🟢")
        print(f"\n  [{i+1}] {flag} {ass}")
        print(f"      规则: {{{ant}}} → {{{con}}}")
        print(f"      支持度: {ring['support_count']}个项目 | 置信度: {ring['confidence']:.3f}")
        print(f"      中标集中度: {ring['win_concentration']:.3f} | 主力: {ring['top_winner']}")
    
    # 对比原始共现方法
    print(f"\n{'='*60}")
    print("对比：传统Jaccard vs FP-growth")
    print("=" * 60)
    print("Jaccard: A和B在多少项目中共现 / (A参与+B参与-共现)")
    print("FP-growth: {A,B}频繁共现AND置信度≥0.8→发现陪标模式")
    print("FP-growth优势: 直接输出'规则'而非'数值'，审计结论更明确")
