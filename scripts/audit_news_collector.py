#!/usr/bin/env python3
"""
审计数据采集演示：web_fetch → html2text → 结构化提取 → 业务过滤
基于 AgentClaw 文章的 fetch_url + html2text 组合模式

使用场景：
1. 每天定时抓取财政部/审计署新闻列表
2. 自动按业务关键词分级过滤
3. 输出结构化摘要供决策参考
"""

import re
import json
from datetime import datetime

# ============================================
# 模拟 web_fetch(markdown模式) 从财政部新闻页返回的数据
# 实际使用时，这就是 web_fetch 的返回结果
# ============================================
RAW_MARKDOWN = """
- [财政部发行2026年记账式贴现（二十九期）国债](http://zwgls.mof.gov.cn/ywgg/202605/t20260512_3989608.htm)2026-05-13
- [财政部青海监管局：以全面落实党政机关习惯过紧日子要求为引领 持续推动财政监管工作提质增效](http://qh.mof.gov.cn/gzdt/caizhengjiancha/202604/t20260428_3988651.htm)2026-05-13
- [财政部山西监管局：数智赋能 构建会计监督新模式](http://sn.mof.gov.cn/gzdt/caizhengjiancha/202604/t20260422_3988027.htm)2026-05-13
- [廖岷与英国财政部国际金融事务总司长怀特举行视频通话](https://www.mof.gov.cn/zhengwuxinxi/caizhengxinwen/202605/t20260512_3989637.htm)2026-05-12
- [财政部第二次续发行2026年记账式附息（七期）国债](http://zwgls.mof.gov.cn/ywgg/202605/t20260508_3989287.htm)2026-05-12
- [财政部陕西监管局："三维一体"推动财政金融监管提质增效](http://sx.mof.gov.cn/gzdt/caizhengjiancha/202604/t20260417_3987764.htm)2026-05-12
- [财政部浙江监管局：精准发力提质效 扎实做好部门决算审核工作](http://zj.mof.gov.cn/caizhengjiancha/202604/t20260427_3988510.htm)2026-05-12
- [财政部发行2026年记账式附息（十期）国债](http://zwgls.mof.gov.cn/ywgg/202605/t20260508_3989285.htm)2026-05-11
- [财政部河北监管局："四个加强"推动超长期特别国债监管提质增效](http://he.mof.gov.cn/caizhengjiancha/202604/t20260422_3988103.htm)2026-05-11
- [财政部下达支持学前教育发展资金458亿元 推进学前教育普及普惠安全优质发展](http://jkw.mof.gov.cn/gongzuodongtai/202605/t20260508_3989228.htm)2026-05-09
- [财政部第一次续发行2026年记账式附息（九期）国债](http://zwgls.mof.gov.cn/ywgg/202605/t20260507_3989167.htm)2026-05-09
- [财政部吉林监管局：加强转移支付资金监管助力地方生态环境保护高质量发展](http://jl.mof.gov.cn/caizhengjiancha/202604/t20260422_3988024.htm)2026-05-09
- [两家内地会计师事务所获准从事H股企业审计](http://kjs.mof.gov.cn/gongzuotongzhi/202605/t20260506_3989012.htm)2026-05-08
- [财政部第二次续发行2026年记账式附息（六期）国债](http://zwgls.mof.gov.cn/ywgg/202604/t20260428_3988633.htm)2026-05-08
- [财政部会计司发布金融保险相关会计准则实施问答和应用案例](http://kjs.mof.gov.cn/gongzuotongzhi/202604/t20260430_3988959.htm)2026-05-08
- [财政部宁夏监管局：把握"时度效" 持续提升属地中央预算单位预算监管工作质效](http://nx.mof.gov.cn/caizhengjiancha/202603/t20260331_3986642.htm)2026-05-08
- [财政部组织开展公共数据资源治理成本归集试点工作](http://kjs.mof.gov.cn/gongzuotongzhi/202605/t20260506_3989010.htm)2026-05-07
- [财政部天津监管局：全面开展2025年度中央对地方转移支付绩效自评复核工作](http://tj.mof.gov.cn/gzdt2/caizhengjiancha/202603/t20260309_3984959.htm)2026-05-07
- [财政部黑龙江监管局：以精准监管推动财政金融协同政策落地见效](http://hlj.mof.gov.cn/caizhengjiancha/202604/t20260413_3987421.htm)2026-05-07
- [财政部今年将在香港发行840亿元人民币国债](https://www.mof.gov.cn/zhengwuxinxi/caizhengxinwen/202605/t20260506_3989062.htm)2026-05-06
- [财政部发行2026年记账式贴现（二十八期）国债](http://zwgls.mof.gov.cn/ywgg/202604/t20260430_3988879.htm)2026-05-06
- [财政部四川监管局：强化财政监管与服务 倾力支持大熊猫国家公园建设](http://sc.mof.gov.cn/caizhengjiancha/202603/t20260323_3985821.htm)2026-05-06
"""

# ============================================
# 业务关键词配置（可随时调整）
# ============================================
BUSINESS_KEYWORDS = {
    "🔥🔥🔥 核心业务": [
        ("绩效评价|绩效自评", "绩效评价业务"),
        ("会计监督|审计", "审计监督业务"),
        ("监管局.*监管", "财政监管动态"),
    ],
    "🔥🔥 重点关注": [
        ("转移支付", "转移支付审计"),
        ("部门决算", "决算审计"),
        ("专项债|特别国债|超长期.*国债", "专项债/国债"),
        ("学前教育|资金.*亿元", "专项资金"),
    ],
    "🔥 行业参考": [
        ("会计师事务所|会计准则", "行业动态"),
        ("预算监管|资金监管", "预算管理"),
        ("四川", "四川本地"),
    ],
}

# ============================================
# 核心处理流程
# ============================================

def extract_articles(markdown_text):
    """步骤1: 从 markdown 文本中提取结构化数据"""
    pattern = r'\[(.+?)\]\((https?://[^)]+)\)(\d{4}-\d{2}-\d{2})'
    matches = re.findall(pattern, markdown_text)
    return [{"title": m[0], "url": m[1], "date": m[2]} for m in matches]


def score_relevance(article):
    """步骤2: 按业务关键词评分分级"""
    title = article["title"]
    for level, kws in BUSINESS_KEYWORDS.items():
        for pattern_str, tag in kws:
            if re.search(pattern_str, title):
                return level, tag
    return None, None


def filter_and_rank(articles):
    """步骤3: 过滤 + 分级 + 排序"""
    relevant = []
    for a in articles:
        level, tag = score_relevance(a)
        if level:
            a["relevance"] = level
            a["tag"] = tag
            relevant.append(a)
    
    # 按优先级排序：核心 > 重点 > 参考，同级按日期
    level_order = {k: i for i, k in enumerate(BUSINESS_KEYWORDS.keys())}
    relevant.sort(key=lambda a: (level_order.get(a["relevance"], 99), a["date"]), reverse=False)
    return relevant


def format_report(articles, source_name):
    """步骤4: 生成可读报告"""
    total_raw = len(articles)
    relevant = filter_and_rank(articles)
    ratio = len(relevant) / total_raw * 100 if total_raw else 0

    lines = [
        f"## {source_name} 业务情报 ({datetime.now().strftime('%Y-%m-%d')})",
        f"",
        f"📊 抓取 {total_raw} 条 | 🎯 相关 {len(relevant)} 条 ({ratio:.0f}%) | ❌ 过滤 {total_raw - len(relevant)} 条",
        f"",
    ]

    current_level = None
    for a in relevant:
        if a["relevance"] != current_level:
            current_level = a["relevance"]
            lines.append(f"### {current_level}")
        lines.append(f"- [{a['date']}] [{a['title']}]({a['url']}) `{a['tag']}`")
    
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"💡 Token 效率：原始HTML约15K字符 → Markdown约3K字符 → 结构化报告约1.5K字符（压缩率90%）")
    
    return "\n".join(lines)


def export_json(relevant_articles, path="audit_news.json"):
    """步骤5 (可选): 导出结构化数据供后续处理"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(relevant_articles, f, ensure_ascii=False, indent=2)
    return path


# ============================================
# 主流程
# ============================================

if __name__ == "__main__":
    # 模拟完整工作流
    print("=" * 60)
    print("  审计数据采集 Pipeline 演示")
    print("  web_fetch → html2text → 结构化 → 业务过滤")
    print("=" * 60)
    print()

    # Step 1: 提取
    articles = extract_articles(RAW_MARKDOWN)
    print(f"[Step 1] 提取结构化数据: {len(articles)} 条")
    print(f"         样本: {articles[0]['title'][:40]}...")
    print()

    # Step 2+3: 过滤分级
    relevant = filter_and_rank(articles)
    level_counts = {}
    for a in relevant:
        level_counts[a['relevance']] = level_counts.get(a['relevance'], 0) + 1
    
    print(f"[Step 2+3] 业务过滤分级结果:")
    for level, count in level_counts.items():
        print(f"         {level}: {count} 条")
    print(f"         过滤掉: {len(articles) - len(relevant)} 条（国债发行、国际交流等非核心内容）")
    print()

    # Step 4: 生成报告
    report = format_report(articles, "财政部新闻")
    print(report)

    # Step 5: 导出 JSON
    path = export_json(relevant)
    print(f"\n[Step 5] 结构化数据已导出: {path}")
    print(f"         可用于：知识库入库 / 邮件推送 / 日报生成")
