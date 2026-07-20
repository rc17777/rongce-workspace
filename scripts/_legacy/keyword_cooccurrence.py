"""
方案A v3：区分度比率分析 — 找出每条业务线的特征词
ratio = 该线频率 / 全库频率，ratio高=该线独有特征
"""
import json, sys, re, yaml, math
from collections import Counter, defaultdict
import jieba

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\scrccpa\.openclaw\workspace\.rag_index\chunks.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

with open(r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\business_lines.yaml', 'r', encoding='utf-8') as f:
    bl_data = yaml.safe_load(f)

lines = bl_data['nodes']

# Custom dictionary
for t in ['经济责任审计','预算执行','绩效评价','专项转移支付','政府采购',
          '竣工财务决算','往来款项','坏账准备','呆账核销','收支两条线',
          '国有资产','保值增值','三重一大','八项规定','财会监督',
          '预算绩效管理','直达资金','事前绩效评估','事中绩效监控',
          '财政承受能力','地方政府债务','隐性债务','高标准农田',
          '农村集体三资','工程量清单','招标控制价','穿透式监管',
          '审计整改','审计移送','严肃财经纪律','会计信息质量',
          '预决算公开','公平竞争审查','奖补资金','稳岗返还',
          '就业补贴','政府采购质疑','行政复议','行政诉讼',
          '除险加固','以工代赈','民生实事']:
    jieba.add_word(t, freq=100)

NOISE_WORDS = {
    '的','了','在','是','和','就','都','一','也','很','到','说','要','去',
    '会','着','没有','好','这','他','她','它','们','那','之','及','与','或',
    '等','对','其','可','应','但','为','中','并','已','如','从','所','被',
    '将','以','能','该','各','请','按','据','由','经','向','同','此','元',
    '表示','具有','需要','进行','通过','包括','以及','对于','同时','因此',
    '所以','如果','虽然','但是','然而','另外','此外','其中','例如','比如',
    '亿元','万元','年的','以来','以上','以下','一种','不同','方面','情况',
    '问题','目前','当前','今后','近年','每年','年度','相关','有关','基本',
    '主要','重要','实施','工作','规定','要求','单位','部门','应当','根据',
    '按照','确保','加强','进一步','推动','促进','实现','落实','支撑','保障',
    '坚持','持续','全面','深入','形成','构建','建立','完善','健全','加快',
    '强化','不断','方案','计划','规划','措施','行动','任务','目标','内容',
    '文章','作者','来源','日期','图片','原文','阅读','原文链接','保持',
    '格式','中文','文字','完整','说明','专题','案例','体系','机制','关键',
    '核心','重点','运用','最后','通知','意见','办法','条例','规则','细则',
    '规范','标准','一方面','另一方面','为此','截至','截至目前',
    '十五五','十四五','本期','引擎','期数','关键词','关于','涉及','纳入',
    '结合','支持','属于','编制','执行','批复','调整','公开','项目','资金',
    '财政','政府','预算','政策','企业','使用','风险','成本','审计',
    '监督','检查','管理','发展','建设','数据','分析',
}

# Step 1: Compute global word frequency across ALL chunks
print("Computing global word frequencies...")
global_counter = Counter()
for chunk in chunks:
    text = chunk.get('text', '')[:3000]
    words = set()  # per-document word frequency (boolean)
    for w in jieba.cut(text):
        w = w.strip()
        if len(w) < 2 or w in NOISE_WORDS:
            continue
        words.add(w)
    for w in words:
        global_counter[w] += 1

total_docs = len(chunks)
print(f"  {total_docs} docs, {len(global_counter)} unique terms")

# Step 2: For each business line, compute word frequency and ratio
all_existing = set()
for line in lines:
    for kw in line.get('keywords', {}).get('primary', []):
        all_existing.add(kw)
    for kw in line.get('keywords', {}).get('secondary', []):
        all_existing.add(kw)

print("\n" + "=" * 75)
print("  区分度分析 — 每条线的特征词 (ratio = 该线频率/全库频率)")
print("=" * 75)

for line in lines:
    lid = line['id']
    name = line['name']
    pk = line.get('keywords', {}).get('primary', [])
    sk = line.get('keywords', {}).get('secondary', [])
    if not pk:
        continue

    # Find matching chunks and count word frequency
    matching = [c['text'] for c in chunks if any(kw in c.get('text', '') for kw in pk)]
    if len(matching) < 5:
        continue

    line_counter = Counter()
    for text in matching:
        words = set()
        for w in jieba.cut(text[:3000]):
            w = w.strip()
            if len(w) < 2 or w in NOISE_WORDS:
                continue
            words.add(w)
        for w in words:
            line_counter[w] += 1

    n = len(matching)
    existing = set(pk + sk) | all_existing

    # Compute distinctiveness ratio
    candidates = []
    for word, line_count in line_counter.most_common(300):
        if word in existing:
            continue
        if len(word) < 2:
            continue

        global_count = global_counter.get(word, 1)
        line_freq = line_count / n
        global_freq = global_count / total_docs
        ratio = line_freq / global_freq if global_freq > 0 else 0

        # Filter: ratio > 2.0 means 2x more likely in this line's docs
        # AND line_count >= 3 to avoid spurious hits
        if ratio > 2.0 and line_count >= 3:
            candidates.append((word, line_count, line_count/n*100, ratio))

    # Sort by ratio (distinctiveness)
    candidates.sort(key=lambda x: x[3], reverse=True)

    print(f"\n  {lid} {name} ({n} chunks)")
    print(f"    existing: {pk}")

    for word, cnt, freq, ratio in candidates[:10]:
        is_new_primary = ratio > 5.0 and freq > 10
        tag = '🆕 primary' if is_new_primary else ('🆕 secondary' if ratio > 3.0 and freq > 5 else '   review')
        print(f"    {tag} | {word} (x{ratio:.1f}, {cnt}docs/{freq:.0f}%)")

print("\n" + "=" * 75)
print("  ✅ 完成。ratio>5且覆盖>10%=强烈建议 primary")
print("  ✅ ratio>3且覆盖>5%=建议 secondary")
print("=" * 75)
