#!/usr/bin/env python3
"""
审计情报采集器 - 单文件自包含版
用法: python audit_collector.py [source]
  source: mof (财政部) | audit (审计署) | all (全部)
  
无需任何外部依赖，纯标准库实现 html2text 转换。
专为 OpenClaw cron 子代理优化：单次 exec 调用，5-15 秒完成。
"""
import re, sys, json
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ============================================================
# 配置
# ============================================================
# 北京时间
CST = timezone(timedelta(hours=8))

# 数据源
SOURCES = {
    "mof": {
        "name": "财政部新闻",
        "url": "https://www.mof.gov.cn/zhengwuxinxi/caizhengxinwen/",
        "timeout": 15,
    },
    "audit": {
        "name": "审计署报告及解读",
        "url": "https://www.audit.gov.cn/n5/n26/index.html",
        "timeout": 15,
    },
}

# 业务关键词（融策定制）
KEYWORDS = [
    # (优先级, 正则, 标签)
    (1, r"绩效评价|绩效自评|绩效管理", "绩效评价"),
    (1, r"会计监督|审计监督|审计工作|H股.*审计", "审计监督"),
    (1, r"监管局.*监管|财政监管.*提质|监管.*提质增效", "监管动态"),
    (2, r"转移支付|部门决算|决算审核|决算审计", "决算/转移支付"),
    (2, r"专项债|特别国债|超长期.*国债", "专项债/国债"),
    (2, r"财政金融协同|资金监管.*助力", "资金监管"),
    (3, r"会计师事务所|会计准则|会计司", "行业动态"),
    (3, r"四川|成都", "四川本地"),
    (3, r"学前教育|资金\d+亿元|下达.*资金", "专项资金"),
]

# ============================================================
# 核心函数
# ============================================================

def fetch_page(url, timeout=15):
    """抓取页面，返回原始 HTML 文本"""
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        # 尝试自动检测编码
        content_type = resp.headers.get("Content-Type", "")
        charset_match = re.search(r"charset=([\w-]+)", content_type)
        if charset_match:
            encoding = charset_match.group(1)
        else:
            # 从 HTML meta 标签中找
            head = raw[:2000].decode("utf-8", errors="ignore")
            meta_match = re.search(r'charset[="\s]+([\w-]+)', head, re.I)
            encoding = meta_match.group(1) if meta_match else "utf-8"
        return raw.decode(encoding, errors="ignore")


def html_to_text(html):
    """简易 HTML → 纯文本（替代 html2text，零依赖）"""
    # 移除 script/style 标签及其内容
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.I)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.I)
    # 移除 HTML 注释
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # 将常见块级标签替换为换行
    html = re.sub(r'</?(?:div|p|li|tr|h\d|br|ul|ol|table|hr)[^>]*>', '\n', html, flags=re.I)
    # 移除所有剩余标签
    html = re.sub(r'<[^>]+>', '', html)
    # 解码 HTML 实体
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    html = html.replace('&quot;', '"').replace('&#39;', "'")
    # 压缩多余空白
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()


def extract_articles_mof(text):
    """从财政部新闻页提取文章列表"""
    articles = []
    # 匹配: [标题](url)日期  或  标题 url 日期
    # 财政部页面常见格式: <a href="...">标题</a> <span>日期</span>
    patterns = [
        # Markdown格式: [标题](url)日期
        (r'\[([^\]]+?)\]\((https?://[^)]+?)\)\s*(\d{4}-\d{2}-\d{2})', 1),
        # HTML格式: href="url" ... >标题< ... 日期
        (r'href="(https?://[^"]+?/[^"]*\d{8}[^"]*?)"[^>]*>([^<]+)</a>.*?(\d{4}-\d{2}-\d{2})', 2),
        # 更宽松: href="url" ... 标题 ... 日期
        (r'href="(https?://[^"]+?/\d{4,6}/[^"]+?)".*?title=["\']([^"\']+)["\'].*?(\d{4}-\d{2}-\d{2})', 3),
    ]
    
    for pattern, _ in patterns:
        for m in re.finditer(pattern, text, re.DOTALL):
            url, title, date = m.group(1), m.group(2), m.group(3) if len(m.groups()) >= 3 else ""
            title = re.sub(r'\s+', ' ', title).strip()
            if title and url and len(title) > 5:
                articles.append({"title": title, "url": url, "date": date.strip() if date else ""})
        if articles:
            break
    
    # 去重
    seen = set()
    unique = []
    for a in articles:
        key = a["url"]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


def extract_articles_audit(text):
    """从审计署报告列表提取"""
    articles = []
    # 审计署页面格式: <a href="...content.html">标题</a> ... [MM-DD]
    pattern = r'href="([^"]+?/content\.html)"[^>]*>([^<]+)</a>.*?\[(\d{2}-\d{2})\]'
    for m in re.finditer(pattern, text, re.DOTALL):
        url, title, date = m.group(1), m.group(2), m.group(3)
        # 处理相对路径: ../../n5/n26/xxx → https://www.audit.gov.cn/n5/n26/xxx
        if url.startswith("http"):
            pass
        elif "../" in url:
            # ../../n5/n26/c10619920/content.html → /n5/n26/c10619920/content.html
            url = "/" + url.split("/../")[-1].lstrip("/")
            url = "https://www.audit.gov.cn" + url
        elif url.startswith("/"):
            url = "https://www.audit.gov.cn" + url
        else:
            url = "https://www.audit.gov.cn/n5/n26/" + url
        title = re.sub(r'\s+', ' ', title).strip()
        # 推断年份
        year = datetime.now(CST).year
        month = int(date.split('-')[0])
        if month > datetime.now(CST).month:
            year -= 1
        full_date = f"{year}-{date}"
        if title and len(title) > 5:
            articles.append({"title": title, "url": url, "date": full_date})
    return articles


def filter_articles(articles):
    """按业务关键词过滤分级"""
    results = {"1": [], "2": [], "3": []}
    for a in articles:
        for priority, pattern, tag in KEYWORDS:
            if re.search(pattern, a["title"]):
                a["tag"] = tag
                results[str(priority)].append(a)
                break
    return results


def format_report(source_name, filtered, total_count):
    """格式化日报"""
    today = datetime.now(CST).strftime("%Y-%m-%d")
    relevant = sum(len(v) for v in filtered.values())
    
    lines = [f"📰 {source_name} ({today})"]
    lines.append(f"抓取 {total_count} 条 | 相关 {relevant} 条\n")
    
    labels = {"1": "🔥🔥🔥 核心业务", "2": "🔥🔥 重点关注", "3": "🔥 行业参考"}
    
    for level in ["1", "2", "3"]:
        items = filtered[level]
        if not items:
            continue
        lines.append(labels[level])
        for a in items:
            lines.append(f"[{a['date']}] {a['title']}")
            lines.append(f"{a['url']}")
            lines.append("")
    
    if relevant == 0:
        lines.append("今日无相关审计政策动态。")
    
    return "\n".join(lines)


def run_source(source_key):
    """运行单个数据源采集"""
    cfg = SOURCES[source_key]
    
    # 1. 抓取
    try:
        html = fetch_page(cfg["url"], cfg["timeout"])
    except (URLError, HTTPError, OSError) as e:
        return f"❌ {cfg['name']}: 抓取失败 - {e}"
    
    # 2. HTML → 文本
    text = html_to_text(html)
    
    # 3. 提取文章
    if source_key == "mof":
        articles = extract_articles_mof(text)
        # 如果正则没匹配到，尝试用纯文本方法
        if not articles:
            articles = extract_articles_mof(html)  # 用原始HTML再试
    else:
        articles = extract_articles_audit(text)
        if not articles:
            articles = extract_articles_audit(html)
    
    if not articles:
        return f"⚠️ {cfg['name']}: 未提取到文章（页面结构可能已变化）"
    
    # 4. 过滤分级
    filtered = filter_articles(articles)
    
    # 5. 格式化
    return format_report(cfg["name"], filtered, len(articles))


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    sources = sys.argv[1:] if len(sys.argv) > 1 else ["mof"]
    
    # 确保编码
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    
    for s in sources:
        if s == "all":
            for key in SOURCES:
                print(run_source(key))
                print()
        elif s in SOURCES:
            print(run_source(s))
            print()
        else:
            print(f"未知数据源: {s}，可选: {list(SOURCES.keys())} / all")
