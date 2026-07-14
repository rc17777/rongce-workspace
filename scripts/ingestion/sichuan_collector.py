"""
批量采集脚本 — 生成搜索URL + 解析HEARTBEAT采集结果
"""
import json, sys, re
from datetime import datetime, timedelta
from urllib.parse import quote
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 咨询服务品类 × 可投标状态 = 真正的商业机会
# 不是搜"审计概念"，是搜"我们能做什么服务"
# 分类依据：政府采购品目 + 融策实际业务能力
# ============================================================

# 咨询服务品类（政府会招标采购的服务）
CONSULTING_CATEGORIES = {
    # --- 审计类 ---
    '财务审计': ['审计服务', '财务审计', '内部审计', '预算执行审计', '收支审计'],
    '经责审计': ['经济责任审计', '经责审计', '离任审计', '任中审计'],
    '竣工决算': ['竣工财务决算', '竣工决算审计', '工程结算审计', '工程竣工决算'],
    '专项审计': ['专项资金审计', '专项审计调查', '社保审计', '营养餐'],
    '跟踪审计': ['跟踪审计', '全过程造价控制', '工程过程控制'],

    # --- 绩效类 ---
    '绩效评价': ['绩效评价', '预算绩效', '绩效管理', '绩效目标', '事前评估', '事中监控'],

    # --- 工程咨询类 ---
    '工程造价': ['工程造价咨询', '造价咨询', '工程量清单编制', '招标控制价编制', '财政评审'],
    '工程咨询': ['全过程工程咨询', '工程咨询', '项目管理咨询', '工程项目管理'],
    '招标代理': ['政府采购代理', '招标代理', '采购代理'],

    # --- 财务类 ---
    '会计服务': ['会计服务', '代理记账', '财务咨询', '税务咨询'],
    '资产评估': ['资产评估', '资产清查', '国有资产清查', '资产盘点'],
    '内部控制': ['内部控制', '内控建设', '内控体系', '合规咨询'],

    # --- 专项服务 ---
    '监督检查': ['监督检查', '财会监督', '财政监督'],
    '政府补贴': ['补贴审计', '补助资金审计', '政府补贴核查'],
}

# 投标用的搜索关键词（合并去重）
BID_KEYWORDS = [
    # 量大面广的核心品类
    '审计服务',
    '工程造价咨询',
    '绩效评价',
    '跟踪审计',
    # 高频具体品类
    '竣工财务决算',
    '资产清查',
    '经济责任审计',
    '全过程工程咨询',
    '会计服务',
    '资产评估',
    # 专项
    '预算绩效管理',
    '财政评审',
    '内部控制',
    '政府采购代理',
    '监督检查 财会监督',
]

# 可投标的公告类型（排除已中标/已成交/已过期）
BID_ANNOUNCEMENT_TYPES = [
    '公开招标', '竞争性磋商', '竞争性谈判',
    '询价', '单一来源', '框架协议', '征集公告'
]

# 排除公告类型（已确定中标人，不能再投标）
CLOSED_ANNOUNCEMENT_TYPES = [
    '中标', '成交', '废标', '终止', '流标'
]

# 四川相关的采购人关键词（快速识别）
SICHUAN_SIGNALS = ['四川', '成都', '绵阳', '德阳', '宜宾', '泸州', '南充',
                    '达州', '乐山', '凉山', '甘孜', '阿坝', '广安', '广元',
                    '遂宁', '内江', '自贡', '攀枝花', '眉山', '资阳', '巴中',
                    '雅安', '冕宁', '西昌', '阆中', '都江堰', '彭州', '崇州',
                    '邛崃', '简阳', '大邑', '蒲江', '新津']


def generate_search_urls(keywords: list, days_back: int = 60) -> dict:
    """Generate search URLs for all keywords."""
    end_date = datetime.now().strftime('%Y:%m:%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y:%m:%d')

    urls = {}
    for kw in keywords:
        encoded = quote(kw)
        url = (f'https://search.ccgp.gov.cn/bxsearch?'
               f'searchtype=1&page_index=1&bidSort=0'
               f'&kw={encoded}'
               f'&start_time={start_date}'
               f'&end_time={end_date}'
               f'&timeType=6&dbselect=bidx')
        urls[kw] = url

    return urls


def filter_sichuan(items: list) -> list:
    """Filter tenders to Sichuan province only."""
    sc_items = []
    for item in items:
        # Check province field
        if item.get('province') == '四川':
            sc_items.append(item)
            continue
        # Check title for Sichuan signals
        title = item.get('title', '')
        purch = item.get('procuring_entity', '')
        for sig in SICHUAN_SIGNALS:
            if sig in title or sig in purch:
                sc_items.append(item)
                break
    return sc_items


def map_to_business_line(item: dict) -> list:
    """Map tender to business line(s)."""
    title = item.get('title', '')
    category = item.get('category_path', '')
    text = f'{title} {category}'

    mappings = {
        'L10_工程竣工决算': ['竣工财务决算', '竣工决算', '工程结算审计'],
        'L11_预算绩效': ['绩效评价', '预算绩效', '绩效管理', '绩效目标'],
        'L6_招投标审计': ['招投标', '政府采购代理', '采购代理'],
        'L1_经责审计': ['经济责任审计', '经责审计', '领导干部'],
        'L4_专项资金': ['专项资金', '专项审计'],
        'L5_往来款清理': ['资产清查', '资产盘点', '往来款', '资金清理'],
        'L7_国企审计': ['国有企业', '国企'],
        'L8_成本效益': ['成本效益'],
        'L9_能源审计': ['能源审计', '碳中和', '节能'],
        'L12_政府补贴': ['补贴', '补助资金'],
        'L13_监督检查': ['监督检查', '财会监督'],
        'L2_收支审计': ['收支审计'],
        'L3_预算执行': ['预算执行'],
    }

    matched = []
    for bline, keywords in mappings.items():
        for kw in keywords:
            if kw in text:
                matched.append(bline)
                break

    # Default: general audit/consulting
    if not matched:
        if any(kw in text for kw in ['审计', '跟踪审计', '审计服务', '工程咨询', '工程造价']):
            matched = ['L10_工程竣工决算']  # Most common

    return matched or ['L0_通用审计']


def summarize_sc_items(items: list) -> str:
    """Generate a summary report of Sichuan tenders."""
    if not items:
        return '本期无四川相关招标。'

    lines = []
    lines.append(f'\n📊 四川招标采集报告 ({datetime.now().strftime("%Y-%m-%d")})')
    lines.append(f'共 {len(items)} 条\n')

    # By business line
    bl_count = {}
    for item in items:
        for bl in item.get('business_lines', ['未知']):
            bl_count[bl] = bl_count.get(bl, 0) + 1

    lines.append('**按业务线:**')
    bl_labels = {
        'L1_经责审计': '经济责任审计', 'L2_收支审计': '收支审计',
        'L3_预算执行': '预算执行', 'L4_专项资金': '专项资金',
        'L5_往来款清理': '往来款/资产清查', 'L6_招投标审计': '招投标',
        'L7_国企审计': '国企审计', 'L8_成本效益': '成本效益',
        'L9_能源审计': '能源审计', 'L10_工程竣工决算': '工程竣工决算',
        'L11_预算绩效': '预算绩效', 'L12_政府补贴': '政府补贴',
        'L13_监督检查': '监督检查', 'L0_通用审计': '通用审计'
    }
    for bl, cnt in sorted(bl_count.items(), key=lambda x: x[1], reverse=True):
        label = bl_labels.get(bl, bl)
        lines.append(f'  {label}: {cnt}条')

    # City distribution
    cities = {}
    for item in items:
        purch = item.get('procuring_entity', '')
        # Extract city from purchaser
        for sig in SICHUAN_SIGNALS:
            if sig in purch:
                cities[sig] = cities.get(sig, 0) + 1
                break

    if cities:
        lines.append('\n**城市分布:**')
        for city, cnt in sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f'  {city}: {cnt}条')

    # Top items
    lines.append('\n**最新招标:**')
    recent = sorted(items, key=lambda x: x.get('publish_date', ''), reverse=True)
    for item in recent[:10]:
        date = item.get('publish_date', '?')
        title = item.get('title', '')[:70]
        purch = item.get('procuring_entity', '')
        atype = item.get('announcement_type', '')
        bls = ','.join([bl_labels.get(b, b) for b in item.get('business_lines', [])])
        lines.append(f'  [{date}] {title}')
        lines.append(f'    采购人: {purch} | {atype} | {bls}')

    return '\n'.join(lines)


# ============================================================
# CLI
# ============================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['urls', 'filter', 'report'])
    parser.add_argument('--input', '-i', help='Input JSON file')
    parser.add_argument('--days', type=int, default=60)
    parser.add_argument('--output', '-o', default='knowledge/taxonomy/sichuan_tenders.json')
    args = parser.parse_args()

    if args.action == 'urls':
        urls = generate_search_urls(CORE_KEYWORDS, args.days)
        print(f'# Search URLs ({len(urls)} keywords, {args.days} days)\n')
        for kw, url in urls.items():
            print(f'## {kw}')
            print(f'{url}\n')

        # Save for automated processing
        with open('knowledge/taxonomy/search_urls.json', 'w', encoding='utf-8') as f:
            json.dump(urls, f, ensure_ascii=False, indent=2)
        print(f'Saved: knowledge/taxonomy/search_urls.json')

    elif args.action == 'filter':
        if not args.input:
            print('Need --input')
            sys.exit(1)
        with open(args.input, 'r', encoding='utf-8') as f:
            items = json.load(f)

        sc = filter_sichuan(items)
        for item in sc:
            item['business_lines'] = map_to_business_line(item)

        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(sc, f, ensure_ascii=False, indent=2)

        print(f'四川招标: {len(sc)}/{len(items)} 条')
        print(summarize_sc_items(sc))

    elif args.action == 'report':
        # Generate report from saved sichuan tenders
        path = args.input or 'knowledge/taxonomy/sichuan_tenders.json'
        if not Path(path).exists():
            print('No data yet')
            sys.exit(0)
        with open(path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        print(summarize_sc_items(items))
