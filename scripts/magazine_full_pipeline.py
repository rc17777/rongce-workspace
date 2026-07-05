"""
杂志资料全量提取管线 — 1003篇 → 12大业务场景归类精华
========================================================
放到那台机器（有 Obsidian Vault 的）workspace 根目录运行：
  python magazine_full_pipeline.py

输出: skills/magazine-knowledge/ 下按业务类型归类的精华文件
      每篇300-500字摘要 + 方法论提炼 + 可复用模式

运行完 git add + commit + push，这台自动拉取。
"""
import os, re, json
from collections import defaultdict
from pathlib import Path

# ============================================================
# 配置 — 改这里！
# ============================================================
VAULT_PATH = r'C:\Users\scrccpa\Documents\Obsidian Vault\杂志资料'
OUTPUT_DIR = Path(__file__).parent.parent / 'skills' / 'magazine-knowledge'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 12大业务场景 → 关键词匹配
# ============================================================
SCENARIO_KEYWORDS = {
    '01-经济责任审计': {
        '场景': ['经济责任审计', '经责审计', '任中审计', '离任审计', '自然资源经济责任审计'],
        '关键词': ['经济责任', '经责', '离任', '任中', '领导干部', '廉政', '微腐败', '四风',
                 '八项规定', '公车', '车轮腐败', '办公用房', '三公经费', '权力运行',
                 '三重一大', '廉洁', '述职', '述廉', '个人重大事项'],
    },
    '02-收支审计': {
        '场景': ['收支审计'],
        '关键词': ['收支', '收入确认', '支出管理', '非税收入', '财政收入', '财政支出',
                 '国库', '决算', '预决算', '财政决算', '结转', '结余'],
    },
    '03-部门预算执行审计': {
        '场景': ['部门预算执行情况审计'],
        '关键词': ['预算执行', '部门预算', '预算编制', '预算调整', '预算绩效',
                 '预算管理', '预算单位', '公用经费', '项目支出'],
    },
    '04-政府资金专项审计': {
        '场景': ['政府资金专项审计', '社保资金审计', '营养餐审计'],
        '关键词': ['专项资金', '社保', '社会保障', '营养餐', '教育经费', '医疗资金',
                 '救灾', '救济', '慈善', '彩票', '公积金', '保障房', '公租房',
                 '廉租房', '棚改', '扶贫', '乡村振兴', '惠农'],
    },
    '05-往来款清理': {
        '场景': ['往来款清理', '资金清理'],
        '关键词': ['往来款', '应收', '应付', '挂账', '往来', '应收款', '应付款',
                 '预付', '预收', '其他应收', '其他应付'],
    },
    '06-招投标审计': {
        '场景': ['招投标审计'],
        '关键词': ['招标', '投标', '围标', '串标', '中标', '评标', '开标',
                 '政府采购', '采购方式', '竞争性', '招标文件', '投标文件',
                 '产权交易', '拍卖', '招商引资', '降本增效'],
    },
    '07-国企专项审计': {
        '场景': ['国企专项审计'],
        '关键词': ['国企', '国有企业', '国资', '国资委', '控股', '集团',
                 '薪酬管理', '混改', '改革', '改制', '国有资产', '产权登记',
                 '利润分配', '分红'],
    },
    '08-成本效益审计': {
        '场景': ['成本效益审计'],
        '关键词': ['成本', '效益', '绩效', '投入产出', '性价比', '造价', '经济性',
                 '效率性', '效果性'],
    },
    '09-能源审计': {
        '场景': ['能源审计', '碳中和审计'],
        '关键词': ['能源', '碳', '排放', '节能', '光伏', '风电', '新能源',
                 '减排', '碳中和', '碳达峰', '环保', '绿色'],
    },
    '10-工程竣工决算审计': {
        '场景': ['工程竣工决算财务审计'],
        '关键词': ['竣工', '决算', '结算', '工程造价', '工程量', '签证',
                 '变更', '索赔', '施工', '监理', '质量', '工期', '建材',
                 '混凝土', '钢筋', '路基', '桥梁', '隧道', '道路',
                 '征地', '拆迁', '基建', '工程款', '进度款'],
    },
    '11-预算绩效管理': {
        '场景': ['预算绩效管理', '绩效评价', '事前评估', '事中监控'],
        '关键词': ['绩效', '绩效评价', '绩效目标', '绩效指标', '绩效管理',
                 '事前评估', '事中监控', '结果应用', '第三方评价'],
    },
    '12-政府补贴审计': {
        '场景': ['政府补贴审计'],
        '关键词': ['补贴', '补助', '贴息', '以旧换新', '涉农补贴', '种粮补贴',
                 '油补', '农机补贴', '退耕', '生态补偿', '价格补贴'],
    },
}

# ============================================================
# 通用方法论模式
# ============================================================
METHOD_PATTERNS = [
    (r'(\d+)[步级]', '分步审计法'),
    (r'([三四五六七八九]|[1-9]\d*)[个项种条][关维点]', '多维检查法'),
    (r'穿透|追踪|追溯|逆查|顺查', '穿透追踪法'),
    (r'比对|对比|匹配|核对|碰撞', '数据比对法'),
    (r'大数据|SQL|Python|数据分析|建模|算法|聚类|回归', '数据分析法'),
    (r'GIS|空间|地理|卫星|遥感|无人机', '空间分析法'),
    (r'访谈|座谈|问卷|走访|实地|暗访|现场', '实地调查法'),
    (r'函证|询证|外调|协查', '外部取证法'),
    (r'盘点|清查|实地|测量|称重', '实物核查法'),
    (r'关联|网络|图谱|Neo4j|图数据', '关联分析法'),
]

# ============================================================
# 核心处理
# ============================================================

def extract_article(filepath):
    """提取单篇文章的结构化信息"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        with open(filepath, 'r', encoding='gbk') as f:
            content = f.read()
    
    # Frontmatter
    meta = {}
    fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).split('\n'):
            kv = re.match(r'(\w+):\s*["\']?(.+?)["\']?\s*$', line)
            if kv:
                meta[kv.group(1)] = kv.group(2).strip('"\'')
    
    # Body
    parts = content.split('---', 2)
    body = parts[2].strip() if len(parts) > 2 else content
    
    # 提取前500字作为摘要
    summary = body[:500].replace('\n', ' ').strip()
    
    # 检测方法论模式
    methods = []
    for pattern, method_name in METHOD_PATTERNS:
        if re.search(pattern, body):
            if method_name not in methods:
                methods.append(method_name)
    
    # 提取关键数字/比例（审计发现中的量化指标）
    amounts = re.findall(r'(\d+(?:\.\d+)?\s*(?:万|亿|元|%|％|个百分点))', body[:1000])
    
    return {
        'title': meta.get('title', os.path.basename(filepath).replace('.md', '')),
        'issue': meta.get('issue', ''),
        'category': meta.get('category', ''),
        'tags': [t.strip() for t in meta.get('tags', '').split(',') if t.strip()],
        'summary': summary,
        'methods': methods,
        'key_findings': amounts[:5],
        'length': len(body),
    }


def classify_to_scenario(article):
    """将文章归类到12大业务场景"""
    title = article['title'] + ' ' + ' '.join(article['tags'])
    summary = article['summary']
    text = title + ' ' + summary
    
    matches = []
    for scenario_id, config in SCENARIO_KEYWORDS.items():
        score = 0
        for kw in config['关键词']:
            if kw in text:
                score += 1
        if score > 0:
            matches.append((scenario_id, score, config['场景'][0]))
    
    # 多匹配时取最高分
    if matches:
        matches.sort(key=lambda x: -x[1])
        return matches[0][0], matches[0][2], matches[0][1]
    return '00-通用', '通用/跨领域', 0


def main():
    print("=" * 60)
    print("杂志资料全量提取管线")
    print(f"源目录: {VAULT_PATH}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Step 1: 扫描所有MD文件
    print("\n[1/5] 扫描文章...")
    articles = []
    uncategorized_count = 0
    
    for root, dirs, files in os.walk(VAULT_PATH):
        for filename in files:
            if not filename.endswith('.md'):
                continue
            filepath = os.path.join(root, filename)
            article = extract_article(filepath)
            articles.append(article)
    
    print(f"  共扫描 {len(articles)} 篇文章")
    
    # Step 2: 归类到12大业务场景
    print("\n[2/5] 归类到12大业务场景...")
    scenario_buckets = defaultdict(list)
    stats = defaultdict(lambda: {'count': 0, 'methods': set(), 'total_length': 0})
    
    for art in articles:
        sid, sname, score = classify_to_scenario(art)
        scenario_buckets[sid].append(art)
        stats[sid]['count'] += 1
        stats[sid]['total_length'] += art['length']
        for m in art['methods']:
            stats[sid]['methods'].add(m)
    
    # Step 3: 打印统计
    print("\n[3/5] 归类统计:")
    for sid in sorted(scenario_buckets.keys()):
        s = stats[sid]
        print(f"  {sid}: {s['count']}篇 | 方法: {', '.join(s['methods']) if s['methods'] else '通用'}")
    
    # Step 4: 生成精华文件
    print("\n[4/5] 生成业务场景精华文件...")
    generated = []
    
    for sid in sorted(scenario_buckets.keys()):
        arts = scenario_buckets[sid]
        sname = list(SCENARIO_KEYWORDS.values())[list(SCENARIO_KEYWORDS.keys()).index(sid)]['场景'][0] if sid in SCENARIO_KEYWORDS else '通用审计'
        sname_clean = sname.replace('/', '-')
        
        # 按文章长度排序（长文优先）
        arts.sort(key=lambda x: -x['length'])
        
        # 生成Markdown
        md_lines = [
            f"# {sname} — 杂志案例精华",
            f"",
            f"> 来源：《中国审计》《审计案例》2024-2026",
            f"> 收录：{len(arts)} 篇相关文章",
            f"> 生成日期：2026-06-21",
            f"",
            f"---",
            f"",
            f"## 方法论概览",
            f"",
        ]
        
        all_methods = set()
        for a in arts:
            all_methods.update(a['methods'])
        md_lines.append(f"本领域涉及审计方法：{'、'.join(sorted(all_methods)) if all_methods else '通用审计方法'}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("## 案例目录")
        md_lines.append("")
        
        for i, art in enumerate(arts[:50], 1):  # 最多50篇
            md_lines.append(f"### {i}. {art['title']}")
            if art['issue']:
                md_lines.append(f"> 来源：{art['issue']}")
            if art['methods']:
                md_lines.append(f"> 方法：{'、'.join(art['methods'])}")
            if art['key_findings']:
                md_lines.append(f"> 关键数据：{'、'.join(art['key_findings'][:3])}")
            md_lines.append(f"")
            md_lines.append(art['summary'][:300])
            md_lines.append("")
        
        if len(arts) > 50:
            md_lines.append(f"...（共 {len(arts)} 篇，显示前 50 篇）")
        
        # 写入文件
        filename = f"{sid}-{sname_clean}.md"
        filepath = OUTPUT_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        
        generated.append(filename)
        print(f"  ✅ {filename} ({len(arts)}篇)")
    
    # Step 5: 生成总索引
    print("\n[5/5] 生成总索引...")
    index_lines = [
        "# 杂志资料全量索引 — Magazine Knowledge Master Index",
        "",
        f"> 总收录：{len(articles)} 篇文章（《中国审计》《审计案例》2024-2026）",
        f"> 生成日期：2026-06-21",
        "",
        "---",
        "",
        "## 按业务场景分布",
        "",
        "| 业务场景 | 篇数 | 主要方法 |",
        "|---------|:--:|------|",
    ]
    
    for sid in sorted(scenario_buckets.keys()):
        s = stats[sid]
        methods_str = '、'.join(list(s['methods'])[:3]) if s['methods'] else '通用'
        index_lines.append(f"| {sid} | {s['count']} | {methods_str} |")
    
    index_lines.extend([
        "",
        "---",
        "",
        "## 精华文件列表",
        "",
    ])
    for f in sorted(generated):
        index_lines.append(f"- `{f}`")
    
    index_lines.extend([
        "",
        "---",
        "",
        "## 使用方法",
        "",
        "在 OpenClaw 中说 `查杂志 <业务关键词>` 即可自动检索对应精华文件。",
        "例如：`查杂志 高标准农田` → 自动读取 04-政府资金专项审计 的案例列表。",
    ])
    
    index_path = OUTPUT_DIR / '00-INDEX-master.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))
    
    print(f"  ✅ 00-INDEX-master.md")
    print(f"\n{'='*60}")
    print(f"✅ 完成！共生成 {len(generated) + 1} 个文件")
    print(f"   输出目录: {OUTPUT_DIR}")
    print(f"   请执行: git add skills/magazine-knowledge/ && git commit -m 'feat: 杂志1003篇全量归类精华' && git push")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
