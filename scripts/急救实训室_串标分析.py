"""急救实训室项目 串标围标深度分析"""
import os, re, json
from collections import Counter

base = r"D:\openclaw-workspace\output\急救实训室_extracted"

files = {
    '好医助': '投标_四川省好医助医疗器械有限公司.txt',
    '易可天地': '投标_成都易可天地科技有限公司.txt',
    '江西正好': '投标_江西正好医疗器械有限公司.txt'
}

texts = {}
for name, f in files.items():
    texts[name] = open(os.path.join(base, f), 'r', encoding='utf-8').read()

# ===== 1. 报价规律性分析 =====
print("=" * 60)
print("一、报价规律性分析")
print("=" * 60)

prices = {
    '好医助': 1585000,
    '易可天地': 1566000,
    '江西正好': 1574022,
}
budget = 1751000
max_price = 1598400

print(f"采购预算: {budget:,}元")
print(f"最高限价: {max_price:,}元")
print()
for name, p in sorted(prices.items(), key=lambda x: x[1]):
    diff = max_price - p
    pct_of_limit = p / max_price * 100
    pct_of_budget = p / budget * 100
    print(f"{name}: CNY {p:,} | 低于限价{diff:,}元 | 占限价{pct_of_limit:.1f}% | 占预算{pct_of_budget:.1f}%")

sorted_prices = sorted(prices.values())
print(f"\n报价极差: {sorted_prices[-1] - sorted_prices[0]:,}元 ({(sorted_prices[-1] - sorted_prices[0])/sorted_prices[0]*100:.2f}%)")
print(f"报价标准差: {__import__('statistics').stdev(sorted_prices):,.0f}元")

# Check arithmetic progression
diffs = [sorted_prices[i+1] - sorted_prices[i] for i in range(len(sorted_prices)-1)]
print(f"相邻报价差额: {diffs}")
if len(set(diffs)) == 1:
    print("🔴 警告：报价呈等差数列！")
else:
    print("🟢 非等差数列")

# Check for阶梯分布
ratio = max(sorted_prices) / min(sorted_prices)
print(f"最高/最低比: {ratio:.4f}")
if ratio < 1.02:
    print("🔴 警告：报价异常集中（<2%）！")
elif ratio < 1.05:
    print("🟡 注意：报价较为集中（<5%）")
else:
    print("🟢 报价分散正常")

# ===== 2. 投标文件结构对比 =====
print("\n" + "=" * 60)
print("二、投标文件结构对比")
print("=" * 60)

structures = {}
for name, text in texts.items():
    # Find section headers
    sections = re.findall(r'(?:第[一二三四五六七八九十]+[章节部分]|^[一二三四五六七八九十]+[、．.])', text, re.MULTILINE)
    structures[name] = len(sections)
    print(f"{name}: 发现 {len(sections)} 个章节标题")

# ===== 3. 文档长度分析 =====
print("\n" + "=" * 60)
print("三、文档长度分析")
print("=" * 60)
for name, text in texts.items():
    print(f"{name}: {len(text):,} 字符")

# ===== 4. 关键段落相似度（精确匹配） =====
print("\n" + "=" * 60)
print("四、关键段落精确匹配分析")
print("=" * 60)

# Find unique segments that appear in multiple bidders
def find_common_segments(t1, t2, min_len=50):
    """Find segments >= min_len chars that appear in both texts"""
    common = []
    for i in range(0, len(t1) - min_len, min_len // 2):
        seg = t1[i:i+min_len]
        if seg in t2 and len(seg.strip()) > 30:
            # Check it's not just spaces/punctuation
            if sum(1 for c in seg if '\u4e00' <= c <= '\u9fff') > 5:
                common.append(seg)
    return common

names = list(texts.keys())
for i in range(3):
    for j in range(i+1, 3):
        n1, n2 = names[i], names[j]
        common = find_common_segments(texts[n1], texts[n2], min_len=80)
        # Deduplicate
        unique_common = []
        for seg in common:
            if not any(seg in s for s in unique_common):
                unique_common.append(seg)
        print(f"\n{n1} vs {n2}: {len(unique_common)} 个≥80字精确匹配段")
        if unique_common:
            for k, seg in enumerate(unique_common[:5]):
                snippet = seg[:120].replace('\n', ' ')
                print(f"  [{k+1}] {snippet}...")
                # Check if it's template text
                if '政府采购' in seg or '招标文件' in seg or '投标人' in seg or '供应商' in seg:
                    print(f"       → 模板化文本")

# ===== 5. 供应商公司信息交叉分析 =====
print("\n" + "=" * 60)
print("五、供应商基本信息")
print("=" * 60)

# Extract addresses
addr_patterns = {
    '好医助': r'四川省成都市.{5,30}',
    '易可天地': r'成都市.{5,30}',
    '江西正好': r'江西省.{5,30}',
}

for name, text in texts.items():
    # Find company address
    addr_match = re.search(r'(?:地址|住所|通讯地址)[：:]\s*(.{5,50})', text)
    if addr_match:
        print(f"{name} 地址: {addr_match.group(1).strip()}")
    # Phone
    phone = re.findall(r'(?:电话|联系电话|手机)[：:]\s*(\d[\d-]{8,15})', text)
    if phone:
        print(f"  联系电话: {phone[:3]}")
    
print("\n" + "=" * 60)
print("六、综合判定")
print("=" * 60)

print("""
关键发现：
1. 报价集中度：三家公司报价极差仅19,000元（1.21%），异常集中
2. TF-IDF全文相似度：89.9%-93.8%（char级），需区分模板化文本
3. 词级相似度：3.5%-8.0%（正常水平）
4. 投标文件长度：需进一步分析
5. 三家均来自不同省份（四川成都×2、江西×1），需查工商关联
""")

# Save results
results = {
    'prices': {k: v for k, v in prices.items()},
    'price_stats': {
        'budget': budget,
        'max_limit': max_price,
        'range': sorted_prices[-1] - sorted_prices[0],
        'range_pct': (sorted_prices[-1] - sorted_prices[0])/sorted_prices[0]*100,
        'std': __import__('statistics').stdev(sorted_prices),
    }
}
with open(os.path.join(base, '串标分析结果.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nResults saved to {base}/串标分析结果.json")
