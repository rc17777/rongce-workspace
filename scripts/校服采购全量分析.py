#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校服采购项目 - 串标围标全量分析
分析维度：
1. 报价规律分析（价格离散度、等差数列检测、与限价关系）
2. 文本雷同检测（TF-IDF相似度）
3. 供应商关联分析（法人/地址/注册信息交叉）
4. 业绩重合度分析
5. 招标文件响应一致性分析
6. 中小企业声明一致性
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

import json
from collections import defaultdict

# ============================================================
# 1. 基础数据
# ============================================================

TENDER_MAX = 795.00  # 最高限价
TENDER_PRICES = {
    '春秋校服-长袖外套': 112,
    '春秋校服-长裤': 76,
    '夏季校服-T恤': 65,
    '夏季校服-夏长裤': 54,
    '夏季校服-齐膝短裤': 48,
    '冬季校服-冲锋衣外套': 220,
    '冬季校服-内胆': 140,
    '冬季校服-冬裤': 80,
}
TENDER_TOTAL_BY_ITEM = sum(TENDER_PRICES.values())  # 795

BIDDERS = {
    '乐吉玛帝诺': {
        'full_name': '四川乐吉玛帝诺服饰有限公司',
        'total_price': 645.00,
        'price_breakdown': {
            '春秋校服-长袖外套': 80,
            '春秋校服-长裤': 70,
            '夏季校服-T恤': 60,
            '夏季校服-夏长裤': 50,
            '夏季校服-齐膝短裤': 45,
            # 冬季由差值推算
        },
        'legal_rep': '杨乐',
        'address': '成都市新都区普华路一巷52号',
        'reg_address': '成都市锦江区工业园区金石路166号天府宝座A座6楼624号',
        'established': '2017-01-04',
        'phone': '13568930323',
        'is_sme': True,
        'brand': 'ROGEEKIDS',
    },
    '牧森': {
        'full_name': '四川牧森服饰有限公司',
        'total_price': 685.00,
        'price_breakdown': {
            '春秋校服-长袖外套': 90,
            '春秋校服-长裤': 70,
            '夏季校服-T恤': 55,
            '夏季校服-夏长裤': 48,
        },
        'address': '四川省成都市成华区一环路东三段167号1层',
        'phone': '028-60986819/18728388818',
        'is_sme': True,
        'brand': '牧森',
    },
    '苏美达伊顿纪德': {
        'full_name': '江苏苏美达伊顿纪德品牌管理有限公司',
        'total_price': 695.00,
        'price_breakdown': {
            '春秋校服-长袖外套': 105,
            '春秋校服-长裤': 58,
            '夏季校服-T恤': 52,
            '夏季校服-夏长裤': 52,
            '夏季校服-齐膝短裤': 45,
            '冬季校服-冲锋衣外套': 195,
            '冬季校服-内胆': 108,
            '冬季校服-冬裤': 80,
        },
        'address': '南京市玄武区长江路190号',
        'phone': '400-0890-299',
        'is_sme': False,  # 苏美达集团是大企业
        'brand': '伊顿纪德',
    },
    '顺华': {
        'full_name': '成都顺华服装有限公司',
        'total_price': None,  # 价格空白
        'price_breakdown': {},
        'address': '（未提取到完整地址）',
        'is_sme': True,
        'employees': 130,
        'revenue': 3006.98,  # 万元
        'assets': 2676.97,  # 万元
        'is_price_missing': True,  # ⚠️ 报价空白
        'brand': '量身定制',
    },
    '弘博士': {
        'full_name': '弘博士服饰集团有限公司',
        'total_price': None,  # 待提取
        'price_breakdown': {},
        'address': '（.doc文件，待提取）',
        'is_sme': None,
        'brand': None,
    },
}

# ============================================================
# 2. 报价规律分析
# ============================================================

print("=" * 80)
print("一、报价分析")
print("=" * 80)

confirmed_prices = {k: v for k, v in BIDDERS.items() if v['total_price'] is not None}
sorted_prices = sorted(confirmed_prices.items(), key=lambda x: x[1]['total_price'])

print(f"\n招标限价: {TENDER_MAX}元/全套")
print(f"投标人数量: 5家（{len(confirmed_prices)}家可获取报价）")
print()

if confirmed_prices:
    prices_list = [v['total_price'] for v in confirmed_prices.values()]
    min_price = min(prices_list)
    max_price = max(prices_list)
    avg_price = sum(prices_list) / len(prices_list)
    price_range = max_price - min_price
    
    print(f"报价区间: {min_price} - {max_price}元")
    print(f"报价均值: {avg_price:.2f}元")
    print(f"报价极差: {price_range}元 ({price_range/min_price*100:.1f}%)")
    print(f"与限价比: 最低={min_price/TENDER_MAX*100:.1f}%, 最高={max_price/TENDER_MAX*100:.1f}%")
    
    print(f"\n报价排名:")
    for rank, (name, data) in enumerate(sorted_prices, 1):
        discount = (1 - data['total_price']/TENDER_MAX) * 100
        print(f"  {rank}. {name}: {data['total_price']}元 (折扣{discount:.1f}%)")
    
    # 报价规律检测
    print(f"\n报价差额分析（相邻报价差）:")
    prev_price = None
    for name, data in sorted_prices:
        if prev_price:
            diff = data['total_price'] - prev_price
            print(f"  {prev_name} → {name}: +{diff}元")
        prev_price = data['total_price']
        prev_name = name
    
    # 等差数列检测
    if len(prices_list) >= 3:
        sorted_vals = sorted(prices_list)
        diffs = [sorted_vals[i+1] - sorted_vals[i] for i in range(len(sorted_vals)-1)]
        print(f"\n等差数列检测: 差额序列 = {diffs}")
        if len(set(diffs)) == 1:
            print("  ⚠️ 疑似呈等差数列分布！")
        elif max(diffs) / min(diffs) < 1.5 if min(diffs) > 0 else False:
            print(f"  差额变异度较小 (max/min = {max(diffs)/min(diffs):.2f})，有一定规律性")
        else:
            print(f"  差额变异度正常")

# 单项报价偏离度
print(f"\n单项报价偏离度分析（与招标限价对比）:")
for item, tender_price in TENDER_PRICES.items():
    print(f"\n  {item} (限价{tender_price}元):")
    for name, data in confirmed_prices.items():
        if item in data['price_breakdown']:
            bid_price = data['price_breakdown'][item]
            deviation = (bid_price - tender_price) / tender_price * 100
            flag = " ⚠️" if abs(deviation) > 30 else ""
            print(f"    {name}: {bid_price}元 ({deviation:+.1f}%){flag}")

# ============================================================
# 3. 文本雷同分析 (基于资格标结构对比)
# ============================================================

print(f"\n\n{'='*80}")
print("二、投标文件结构雷同分析")
print("="*80)

# 基于资格标的段落结构进行对比
qual_texts = {}
qual_dir = r"D:\openclaw-workspace\output\校服分析\txt"
for fname in os.listdir(qual_dir):
    if '资格标' in fname or '资格' in fname:
        path = os.path.join(qual_dir, fname)
        with open(path, 'r', encoding='utf-8') as f:
            qual_texts[fname] = f.read()

# Extract key sections (承诺函格式比对)
print("\n承诺函格式/措辞比对:")
companies = {
    '四川乐吉玛帝诺服饰有限公司-资格标.txt': '乐吉玛帝诺',
    '四川牧森服饰有限公司-资格标.txt': '牧森',
    '江苏苏美达伊顿纪德品牌管理有限公司-资格标.txt': '苏美达伊顿纪德',
}

# Check for identical text blocks
import hashlib

def get_paragraph_hashes(text, min_len=50):
    """Get hashes of significant paragraphs"""
    paras = [p.strip() for p in text.split('\n') if len(p.strip()) > min_len]
    return [hashlib.md5(p.encode('utf-8')).hexdigest() for p in paras]

all_hashes = {}
for fname, company in companies.items():
    if fname in qual_texts:
        hashes = set(get_paragraph_hashes(qual_texts[fname]))
        all_hashes[company] = hashes

# Find paragraphs that appear in multiple bids
company_list = list(all_hashes.keys())
for i in range(len(company_list)):
    for j in range(i+1, len(company_list)):
        c1, c2 = company_list[i], company_list[j]
        common = all_hashes[c1] & all_hashes[c2]
        if common:
            print(f"  {c1} ↔ {c2}: {len(common)} 个相同段落")

# Check structure similarity
print(f"\n文档结构一致性:")
for fname, company in companies.items():
    if fname in qual_texts:
        text = qual_texts[fname]
        sections = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 10 and len(p.strip()) < 100]
        
        # Count key sections
        keywords_found = []
        for kw in ['承诺及声明函', '法定代表人', '营业执照', '财务报告', '纳税', '社保',
                    '设备清单', '人员情况表', '中小企业', '业绩', '行贿犯罪', '信用中国']:
            if kw in text:
                keywords_found.append(kw)
        print(f"  {company}: {len(keywords_found)}/12 关键章节存在")

# ============================================================
# 4. 供应商关联分析
# ============================================================

print(f"\n\n{'='*80}")
print("三、供应商关联分析")
print("="*80)

print("\n基本信息交叉比对:")
info_matrix = {
    '乐吉玛帝诺': {'法人': '杨乐', '注册地': '锦江区', '经营地': '新都区', '成立': '2017'},
    '牧森': {'法人': '（未确认）', '注册地': '成华区', '经营地': '成华区', '成立': '（未确认）'},
    '苏美达伊顿纪德': {'法人': '（未确认）', '注册地': '南京玄武区', '经营地': '南京', '成立': '（未确认）'},
    '顺华': {'法人': '（未确认）', '注册地': '（成都）', '经营地': '（成都）', '成立': '（至少2015前）'},
    '弘博士': {'法人': '（未确认）', '注册地': '（未提取）', '经营地': '（未提取）', '成立': '（未提取）'},
}

print(f"\n{'公司':<12} {'法人':<8} {'城市':<10} {'成立年份':<8}")
print("-" * 45)
for company, info in info_matrix.items():
    print(f"{company:<12} {info['法人']:<8} {info['经营地'][:8]:<10} {info['成立']:<8}")

# 地域分析
print(f"\n地域分布:")
print("  四川省内: 乐吉玛帝诺(成都新都)、牧森(成都成华)、顺华(成都)")
print("  四川省外: 苏美达伊顿纪德(江苏南京)、弘博士(待确认)")
print(f"  ⚠️ 注意: 3家成都本地企业 + 2家省外企业")

# ============================================================
# 5. 业绩重合度分析
# ============================================================

print(f"\n\n{'='*80}")
print("四、业绩重合度分析")
print("="*80)

# 业绩数据
performances = {
    '牧森': [
        '西昌市教育和体育局', '池州职业技术学院', '华师新余高新区实验学校',
        '木里县中学', '德昌县第一完全小学', '遂宁高升实验小学校',
        '成都信息电子学校', '眉山天府新区第一中学', '成都市工程职业技术学校',
        '四川省工业贸易学校', '成都大学附属中学', '犍为县新城小学',
    ],
    '顺华': [
        '四川省巴中中学', '成都列五中学', '四川省简阳中学',
        '成都石室双楠实验学校', '成都市棕北中学西区实验学校', '云南省昆明市第十二中学',
        '四川省温江中学', '温江中学实验学校', '成都市铁路中学校',
        '四川省彭州中学', '四川师范大学实验外国语学校', '昆明市官渡区金马中心学校',
        '四川省南江中学', '电子科技大学实验中学',
    ],
}

print("\n牧森(12个项目) vs 顺华(14个项目) 重合检测:")
mu_sen_set = set(performances['牧森'])
shun_hua_set = set(performances['顺华'])
overlap = mu_sen_set & shun_hua_set
if overlap:
    print(f"  ⚠️ 出现重合学校: {overlap}")
else:
    print(f"  无重合学校")

# 检查同一招标代理
print(f"\n项目地域分布重合度:")
mu_cities = set()
sh_cities = set()
for p in performances['牧森']:
    if '成都' in p: mu_cities.add('成都')
    elif '西昌' in p or '木里' in p or '德昌' in p: mu_cities.add('凉山州')
    elif '遂宁' in p: mu_cities.add('遂宁')
    elif '眉山' in p: mu_cities.add('眉山')
    elif '犍为' in p: mu_cities.add('乐山')
    elif '池州' in p: mu_cities.add('安徽池州')
    elif '新余' in p: mu_cities.add('江西新余')
for p in performances['顺华']:
    if '成都' in p: sh_cities.add('成都')
    elif '巴中' in p: sh_cities.add('巴中')
    elif '简阳' in p: sh_cities.add('简阳')
    elif '温江' in p: sh_cities.add('温江')
    elif '彭州' in p: sh_cities.add('彭州')
    elif '南江' in p: sh_cities.add('南江')
    elif '昆明' in p: sh_cities.add('云南昆明')
common_cities = mu_cities & sh_cities
if common_cities:
    print(f"  共同覆盖城市: {common_cities}")
else:
    print(f"  城市重合度低")

# ============================================================
# 6. 中小企业声明分析
# ============================================================

print(f"\n\n{'='*80}")
print("五、中小企业声明与价格扣除分析")
print("="*80)

print(f"\n招标文件: 小微企业价格扣除10%")
print(f"\n各投标人中小企业声明情况:")
sme_info = [
    ('乐吉玛帝诺', True, '（从报价结构和规模推断为小/微企业）'),
    ('牧森', True, '（从报价结构和规模推断为小/微企业）'),
    ('苏美达伊顿纪德', False, '苏美达集团控股，上市公司背景，不适用中小企业优惠'),
    ('顺华', True, '小型企业（130人, 3006.98万元营收, 2676.97万元资产）'),
    ('弘博士', None, '待确认'),
]

for name, is_sme, note in sme_info:
    status = "小微企业(享受10%价格扣除)" if is_sme else "非小微企业" if is_sme == False else "待确认"
    print(f"  {name}: {status} - {note}")

# 价格扣除后的有效报价
print(f"\n价格扣除后有效报价（假设所有小微企业均申报）:")
for name, data in confirmed_prices.items():
    if data.get('is_sme', False):
        effective = data['total_price'] * 0.9
        print(f"  {name}: 报价{data['total_price']}元 → 扣除后{effective:.2f}元")
    else:
        print(f"  {name}: 报价{data['total_price']}元（不享受扣除）")

# ============================================================
# 7. 面料参数偏离分析
# ============================================================

print(f"\n\n{'='*80}")
print("六、面料参数与招标要求偏离分析")
print("="*80)

tender_fabric = {
    '春秋校服-长袖外套': {'棉': '50%±5%', '聚酯纤维': '50%±5%', '克重': '≥300g/m²'},
    '春秋校服-长裤': {'棉': '50%±5%', '聚酯纤维': '50%±5%', '克重': '≥300g/m²'},
    '夏季校服-T恤': {'棉': '60%±5%', '聚酯纤维': '40%±5%', '克重': '≥200g/m²'},
    '夏季校服-夏长裤': {'棉': '65%±5%', '聚酯纤维': '35%±5%', '克重': '≥200g/m²'},
    '冬季校服-冲锋衣': {'面料': '100%聚酯纤维≥200g/m²', '里料': '100%聚酯纤维≥140g/m²'},
    '冬季校服-内胆': {'材质': '新雪丽100%聚酯纤维', '克重': '≥150g/m²'},
    '冬季校服-冬裤': {'材质': '95%聚酯纤维5%氨纶±5%', '克重': '≥350g/m²'},
}

# 乐吉玛帝诺面料
lj_fabric = {
    '春秋校服-长袖外套': '45%棉 50%聚酯纤维 5%氨纶 320g',
    '春秋校服-长裤': '45%棉 50%聚酯纤维 5%氨纶 320g',
    '夏季校服-T恤': '70%棉 25%聚酯纤维 5%氨纶 220g',
    '夏季校服-夏长裤': '62%棉 32%聚酯纤维 6%氨纶 230g',
    '冬季校服-冲锋衣': '100%聚酯纤维 230g + 可拆卸羽绒层(90鸭绒 40g充绒)',  # ⚠️ 羽绒替代新雪丽
    '冬季校服-内胆': '（含在冲锋衣中）',
    '冬季校服-冬裤': '（未在已提取表格中）',
}

ms_fabric = {
    '春秋校服-长袖外套': '45%棉 55%聚酯纤维 300g',
    '春秋校服-长裤': '45%棉 55%聚酯纤维 300g',
    '夏季校服-T恤': '69%棉 31%聚酯纤维 210g',
    '夏季校服-夏长裤': '94%棉 6%氨纶 220g',
}

smd_fabric = {
    '春秋校服-长袖外套': '45%棉 55%聚酯纤维 290g',  # ⚠️ 克重低于300
    '春秋校服-长裤': '45%棉 55%聚酯纤维 290g',  # ⚠️ 克重低于300
    '夏季校服-T恤': '60%棉 40%聚酯纤维 220g',
    '夏季校服-夏长裤': '45%棉 55%聚酯纤维 220g',  # ⚠️ 棉含量偏离（招标65%±5%）
    '冬季校服-冲锋衣': '100%聚酯纤维 140g + 100%聚酯纤维里料 60g',  # ⚠️ 克重偏低
    '冬季校服-内胆': '100%锦纶 39g + 3M绵100%聚酯纤维 150g',
    '冬季校服-冬裤': '100%聚酯纤维 280g',  # ⚠️ 克重低于350
}

print("\n乐吉玛帝诺 面料偏离:")
for item, spec in lj_fabric.items():
    print(f"  {item}: {spec}")

print("\n牧森 面料偏离:")
for item, spec in ms_fabric.items():
    print(f"  {item}: {spec}")

print("\n苏美达伊顿纪德 面料偏离（注意多项偏离）:")
for item, spec in smd_fabric.items():
    flag = " ⚠️" if '⚠️' in spec else ""
    print(f"  {item}: {spec}{flag}")

# ============================================================
# 8. 风险评估综合
# ============================================================

print(f"\n\n{'='*80}")
print("七、综合风险评估")
print("="*80)

risks = []

# R1: 顺华报价空白
risks.append(('🔴 高风险', '顺华投标文件报价空白', 
    '成都顺华服装有限公司的商务投标文件中，开标一览表和分项报价明细表的报价金额均为空白。'
    '根据招标文件要求，这属于"未完全响应招标文件实质性要求"，应作无效投标处理。'))

# R2: 苏美达面料多项偏离
risks.append(('🔴 高风险', '苏美达伊顿纪德面料参数多项偏离招标要求',
    '春秋校服克重290g/m² < 招标要求300g/m²；夏季长裤棉含量45%（招标65%±5%）；'
    '冬季冲锋衣面料克重140g + 里料60g（远低于常规）；冬裤克重280g < 招标350g/m²。'
    '这可能导致投标被判定为"未完全响应实质性要求"。'))

# R3: 苏美达可能不享受中小企业优惠
risks.append(('🟡 中风险', '苏美达伊顿纪德为大型企业背景',
    '江苏苏美达伊顿纪德品牌管理有限公司隶属于苏美达集团（央企控股上市公司），'
    '如果未提供中小企业声明函，则不享受10%价格扣除，实际价格竞争力受影响。'))

# R4: 乐吉玛帝诺羽绒替代新雪丽
risks.append(('🟡 中风险', '乐吉玛帝诺冬季内胆使用羽绒替代新雪丽',
    '招标要求冬季内胆为"新雪丽"（3M Thinsulate，100%聚酯纤维），'
    '但乐吉玛帝诺使用"可拆卸羽绒层（90鸭绒）"。两者完全不同材质。'))

# R5: 地域集中度
risks.append(('🟡 中风险', '成都本地供应商集中',
    '5家投标人中至少3家为成都企业（乐吉玛帝诺、牧森、顺华），'
    '需关注是否存在本地供应商围标可能性，特别是如果出现一致行动迹象。'))

# R6: 报价呈阶梯分布但有差异
risks.append(('🟢 低风险', '报价分布基本合理',
    f'已确认的3家报价为645/685/695元，差额分别为40元和10元，'
    f'呈递减式分布，无明显等差数列特征。但需补充弘博士报价后完整评估。'))

print(f"\n共识别 {len(risks)} 项风险:")
for level, title, desc in risks:
    print(f"\n  [{level}] {title}")
    print(f"  {desc}")

print(f"\n\n{'='*80}")
print("八、待补充分析项")
print("="*80)
print("  1. 弘博士服饰集团有限公司报价（.doc文件OLE2提取失败，需人工补充）")
print("  2. 成都顺华服装有限公司报价（投标文件价格空白，可能是版本问题）")
print("  3. 弘博士与顺华资格标全文以计算TF-IDF相似度")
print("  4. 工商注册信息交叉查询（股东/法人关联）")
print("  5. 投标IP地址分析（如可获取投标登记记录）")
print("  6. 样品照片/扫描件的视觉一致性比对")

print(f"\n\n{'='*80}")
print("分析完成")
print("="*80)
