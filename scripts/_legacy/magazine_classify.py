"""
全量关键词分类 - 不依赖 category 标签，
直接对 1003 篇 MD 的标题做关键词匹配
"""
import os, json
from collections import Counter

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault\杂志资料'

# Keywords per domain (based on actual 融策 business and audit domains)
DOMAINS = {
    '财政审计': ['预算', '财政', '专项债', '专项债券', '国债', '补贴', '政府投资', '基金',
               '政府采购', '公务支出', '三公', '国库', '转移支付', '以旧换新', '非税',
               '债务', '隐性债务', '预留', '结转', '决算', '拨款', '配套资金',
               '专项资金', '财政资金', '预决算', '收支', '一般公共预算'],
    '农业农村': ['农业', '农村', '乡村', '高标准农田', '保险', '涉农', '有机肥', '土地整治',
               '耕地', '粮食', '种粮', '惠农', '农资', '农机', '养殖', '畜牧',
               '退耕', '林地', '草原', '渔业', '水利'],
    '民生审计': ['教育', '医疗', '食品', '殡葬', '养老', '保障房', '工伤', '社保',
               '学校', '医院', '医保', '药品', '营养餐', '低保', '救助', '慈善',
               '住房', '公积金', '公租房', '卫生', '健康'],
    '投资/工程审计': ['工程', '投资', '基建', '造价', '征地', '拆迁', '招标', '投标',
                    '围标', '串标', '施工', '监理', '质量', '结算', '概算', '合同',
                    '工期', '建材', '混凝土', '钢筋', '道路', '桥梁', '隧道'],
    '经责审计': ['经济责任', '经责', '离任', '任中', '领导干部', '廉政', '腐败',
               '公车', '接待', '会议', '差旅', '办公用房', '微腐败', '四风',
               '八项规定', '反四风', '廉洁'],
    '资源环境': ['资源', '环境', '生态', '矿产', '森林', '水资', '大气', '污染',
               '减排', '碳', '能源', '光伏', '风电', '环保', '排污', '河',
               '湖', '遥感', '卫星', 'GIS', '无人机'],
    '企业审计': ['企业', '国企', '公司', '应收', '存货', '关联', '合并报表',
               '商誉', '金融工具', '资产减值', '收入确认', '成本核算', '股权',
               '股东', '分红', '利润'],
    '金融审计': ['银行', '金融', '信贷', '贷款', '保险', '证券', '理财',
               '利率', '汇率', '资金池', '信托', '担保', '融资', '存款'],
}

results = {k: {'count': 0, 'titles': []} for k in DOMAINS}
uncategorized = []
total = 0

for root, dirs, files in os.walk(vault):
    for filename in files:
        if not filename.endswith('.md'):
            continue
        total += 1
        path = os.path.join(root, filename)
        title = filename.replace('.md', '')
        
        # Classify by title keywords
        classified = False
        for domain, keywords in DOMAINS.items():
            if any(kw in title for kw in keywords):
                results[domain]['count'] += 1
                results[domain]['titles'].append(title)
                classified = True
                break  # First match wins
        
        if not classified:
            uncategorized.append(title)

# Print results
print(f'Total MD files scanned: {total}\n')
print('=== Domain Distribution (by title) ===')
total_classified = 0
for domain in DOMAINS:
    c = results[domain]['count']
    total_classified += c
    print(f'  {c:>4}  {domain}')
print(f'  {total - total_classified:>4}  Unclassified')
print(f'\nTotal classified: {total_classified}/{total}')

# Save detailed results
out_path = r'D:\openclaw-workspace\temp\magazine_classification.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'total': total,
        'classified': total_classified,
        'domains': {k: {'count': v['count'], 'sample': v['titles'][:5]} 
                    for k, v in results.items()},
    }, f, ensure_ascii=False, indent=2)
print(f'\nDetailed results: {out_path}')
