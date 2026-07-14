"""Add tender monitoring source config to business_lines.yaml"""
import yaml, sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\business_lines.yaml'
with open(path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Add tender monitoring config at top level
data['tender_monitoring'] = {
    'enabled': False,  # 待数据源就绪后启用
    'description': '通过招标公告发现新业务方向 — 仅抓取与经营范围匹配的招标品类',
    'scope': {
        'procurement_categories': [
            '审计服务',
            '工程咨询服务',
            '会计服务',
            '资产评估服务',
            '财务咨询服务',
            '绩效评价服务',
            '税务咨询服务',
            '工程造价咨询服务',
            '招标代理服务',
            '法律服务',
        ],
        'exclude_keywords': [
            '软件开发', '系统集成', '硬件采购', '物业服务',
            '保安服务', '保洁服务', '食堂', '印刷', '车辆',
        ],
        'min_budget_yuan': 50000,  # 最低预算5万元（过滤小额零星采购）
    },
    'data_sources': [
        {'name': '中国政府采购网', 'url': 'http://www.ccgp.gov.cn/', 'status': 'planned'},
        {'name': '四川省政府采购网', 'url': 'http://www.ccgp-sichuan.gov.cn/', 'status': 'planned'},
        {'name': '成都市公共资源交易中心', 'url': 'https://www.cdggzy.com/', 'status': 'planned'},
        {'name': '中国招标投标公共服务平台', 'url': 'http://www.cebpubservice.com/', 'status': 'planned'},
    ],
    'classification': {
        'round1': 'keyword_match',  # 招标公告品类匹配现有业务线
        'round2': '同法规入库',      # 匹配不到的 → Round 3 新领域嗅探
        'signal_weight': 'high',     # 招标信号权重 > 政策信号 (真金白银>方向信号)
        'incubation_threshold': 2,   # 同类型招标公告累计≥2条即推送
    },
    'outputs': [
        '市场机会追踪（谁在买、多少钱、在哪）',
        '新业务方向发现（对应现有业务线覆盖不到的服务需求）',
        '竞品情报（谁中标了、中标价、中标频率）',
    ],
    'created_at': datetime.now().strftime('%Y-%m-%d'),
}

data['tree_version'] = data.get('tree_version', 0) + 1
data['last_updated'] = datetime.now().strftime('%Y-%m-%d')

with open(path, 'w', encoding='utf-8') as f:
    yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=200)

print("✅ tender_monitoring config added")
print(f"   tree_version: {data['tree_version']}")
print(f"   采购品类: {len(data['tender_monitoring']['scope']['procurement_categories'])} categories")
print(f"   数据源: {len(data['tender_monitoring']['data_sources'])} sources (status=planned)")
