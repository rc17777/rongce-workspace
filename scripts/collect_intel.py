"""
融策智能采集引擎 v3.0 — Bing 搜索版（轻量级，无需浏览器）
========================================================
用法：
  python scripts/collect_intel.py --search         # 生成搜索指令供 web_fetch
  python scripts/collect_intel.py --save '<json>'   # 保存文章
  python scripts/collect_intel.py --report          # 生成日报
  python scripts/collect_intel.py --run             # 全量采集（实时）
  python scripts/collect_intel.py --line 经责审计   # 单业务线
"""
import os, sys, json, hashlib, re, time, requests
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
INTEL_RAW = WORKSPACE / "knowledge" / "intel_raw"
INTEL_INDEX = WORKSPACE / "knowledge" / "intel_index.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

BUSINESS_LINES = {
    "经责审计": ["经济责任审计", "离任审计", "领导干部审计"],
    "收支审计": ["财政收支审计", "预算收入审计", "决算审计"],
    "预算执行": ["预算执行审计", "部门预算审计"],
    "专项资金": ["专项资金审计", "专项债审计", "社会保障资金"],
    "往来款清理": ["往来款项审计", "债权债务清理", "债务化解"],
    "招投标审计": ["招投标审计", "政府采购审计", "围标串标"],
    "国企审计": ["国有企业审计", "国有资产审计", "国企改革"],
    "成本效益审计": ["绩效评价", "成本效益分析", "财政支出绩效"],
    "能源审计": ["能源审计", "资源环境审计", "碳中和审计"],
    "工程决算审计": ["竣工决算审计", "工程造价审计", "基本建设审计"],
    "预算绩效管理": ["预算绩效管理", "事前绩效评估", "事中绩效监控"],
    "政府补贴审计": ["政府补贴审计", "补助资金审计", "惠农资金"],
}

# 入库质量门禁：搜索结果只是候选，不得直接视为知识。
TRUSTED_DOMAINS = (
    ".gov.cn", ".audit.gov.cn", ".mof.gov.cn", ".npc.gov.cn",
    ".nssd.cn", ".ncpssd.cn", ".cass.cn", ".ciia.com.cn",
)
REJECT_DOMAINS = ("baike.baidu.com", "zhidao.baidu.com", "wenku.baidu.com")
REJECT_TITLE_PATTERNS = (
    "百度百科", "汉语词典", "新华字典", "汉语国学", "字典释义",
    "报名系统", "考试报名", "招聘", "职位", "上坡辅助系统",
)
AUDIT_TERMS = ("审计", "财政", "预算", "绩效", "资金", "债务", "采购", "招标", "工程", "国企", "资产", "补贴", "能源", "环境")


def assess_quality(item, line_name, keyword):
    """对搜索结果打分：A正式入库、B候选池、C拒收。"""
    title = item.get("title", "").strip()
    snippet = item.get("snippet", "").strip()
    url = item.get("url", "")
    domain = item.get("domain", "").lower()
    text = f"{title} {snippet}"
    reasons = []
    score = 0

    if not title or not url:
        return {"status": "C", "score": 0, "reasons": ["缺少标题或链接"]}
    if any(p in title for p in REJECT_TITLE_PATTERNS):
        return {"status": "C", "score": 0, "reasons": ["标题命中噪声黑名单"]}
    if any(d in domain for d in REJECT_DOMAINS):
        score -= 30
        reasons.append("低优先级平台")
    if domain.endswith(TRUSTED_DOMAINS) or any(domain.endswith(d) for d in TRUSTED_DOMAINS):
        score += 35
        reasons.append("权威来源")
    if keyword in text:
        score += 35
        reasons.append("完整关键词命中")
    else:
        # 不能用单字词误命中；只允许至少两个业务相关词共同出现
        hits = sum(1 for t in AUDIT_TERMS if t in text)
        if hits >= 2:
            score += 15
            reasons.append(f"相关词命中{hits}个")
        else:
            reasons.append("标题/摘要缺少业务相关词")
    if len(snippet) >= 40:
        score += 15
        reasons.append("有有效摘要")
    if len(title) >= 8:
        score += 5
    
    status = "A" if score >= 65 else ("B" if score >= 35 else "C")
    if status == "B":
        reasons.append("需抓正文后复核")
    return {"status": status, "score": score, "reasons": reasons}


def save_candidate(item, line_name, keyword, quality):
    """B/C档进入审查队列，不污染正式知识库。"""
    path = WORKSPACE / "knowledge" / "intel_candidates.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {**item, "matched_line": line_name, "matched_keyword": keyword,
           "quality": quality, "queued_at": datetime.now().isoformat()}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "ℹ️", "OK": "✅", "SKIP": "⏭️", "ERROR": "❌", "WARN": "⚠️"}.get(level, "•")
    print(f"[{ts}] {prefix} {msg}")

def load_index():
    if INTEL_INDEX.exists():
        try:
            return json.load(open(INTEL_INDEX, 'r', encoding='utf-8'))
        except:
            pass
    return {"items": {}, "last_run": None, "stats": {"total": 0, "by_source": {}, "by_line": {}}}

def save_index(idx):
    INTEL_INDEX.parent.mkdir(parents=True, exist_ok=True)
    json.dump(idx, open(INTEL_INDEX, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def make_id(url, title=""):
    # 清理URL: 去掉Bing追踪参数
    clean_url = re.sub(r'[?&]msclkid=[^&]+', '', url)
    clean_url = re.sub(r'[?&]utm_[^&]+', '', clean_url)
    clean_url = re.sub(r'[?&]ref_src=[^&]+', '', clean_url)
    return hashlib.md5(f"{clean_url}{title}".encode()).hexdigest()[:12]

def save_article(source, title, url, snippet, matched_line, source_domain=""):
    """保存文章到知识库"""
    article_id = make_id(url, title)
    date_str = datetime.now().strftime("%Y%m%d")
    
    source_dir = INTEL_RAW / source
    source_dir.mkdir(parents=True, exist_ok=True)
    filepath = source_dir / f"{date_str}_{article_id}.md"
    
    meta = {
        "id": article_id,
        "source": source,
        "source_domain": source_domain,
        "title": title,
        "url": url,
        "snippet": snippet,
        "matched_line": matched_line,
        "fetched_at": datetime.now().isoformat(),
    }
    
    content = f"---\n{json.dumps(meta, ensure_ascii=False, indent=2)}\n---\n\n"
    content += f"# {title}\n\n"
    content += f"> 来源: [{source_domain or source}]({url})\n"
    content += f"> 业务线: {matched_line}\n"
    content += f"> 采集时间: {date_str}\n\n"
    content += f"## 摘要\n\n{snippet}\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    idx = load_index()
    idx["items"][article_id] = meta
    idx["stats"]["total"] = idx["stats"].get("total", 0) + 1
    idx["stats"]["by_source"][source] = idx["stats"]["by_source"].get(source, 0) + 1
    idx["stats"]["by_line"][matched_line] = idx["stats"]["by_line"].get(matched_line, 0) + 1
    idx["last_run"] = datetime.now().isoformat()
    save_index(idx)
    
    return filepath

def search_bing(keyword, max_results=10):
    """搜索 Bing 并返回结构化结果"""
    url = f"https://cn.bing.com/search?q={quote(keyword)}&setlang=zh-cn&count={max_results}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
        
        # Bing 搜索结果解析 - 用正则从 HTML 提取
        results = []
        
        # 匹配 Bing 搜索结果的链接
        # 现代Bing: <a class="tilk" href="..."><h2>...</h2></a>
        # 也匹配: <h2><a href="...">text</a></h2>
        pattern1 = re.findall(
            r'<a[^>]*class="[^"]*tilk[^"]*"[^>]*href="(https?://[^"]+)"[^>]*>.*?<h2[^>]*>(.*?)</h2>',
            html, re.DOTALL | re.IGNORECASE
        )
        
        # 备用模式
        pattern2 = re.findall(
            r'<a[^>]*href="(https?://[^"]+)"[^>]*>\s*<h2[^>]*>(.*?)</h2>',
            html, re.DOTALL | re.IGNORECASE
        )
        
        # 再备用: 从 cite 标签获取域名
        pattern3 = re.findall(
            r'<h2[^>]*>.*?<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>.*?</h2>',
            html, re.DOTALL | re.IGNORECASE
        )
        
        seen = set()
        snippets = re.findall(r'<p[^>]*class="[^"]*(?:b_lineclamp|b_caption)[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
        
        for pat in [pattern1, pattern2, pattern3]:
            for i, (link, title) in enumerate(pat):
                if link in seen:
                    continue
                seen.add(link)
                
                # 清理 HTML 标签
                title = re.sub(r'<[^>]+>', '', title).strip()
                title = re.sub(r'&amp;', '&', title)
                title = re.sub(r'&lt;', '<', title)
                title = re.sub(r'&gt;', '>', title)
                title = re.sub(r'&quot;', '"', title)
                title = re.sub(r'&#\d+;', '', title)
                
                if not title or len(title) < 4:
                    continue
                    
                snippet = snippets[i] if i < len(snippets) else ""
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                snippet = re.sub(r'&[a-z]+;', '', snippet)
                
                domain = re.search(r'https?://([^/]+)', link)
                source_domain = domain.group(1) if domain else "unknown"
                
                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet[:200],
                    "domain": source_domain,
                })
            
            if len(results) >= max_results:
                break
        
        return results[:max_results]
        
    except Exception as e:
        log(f"搜索失败: {e}", "ERROR")
        return []

def collect_line(line_name, keywords, max_per_kw=5):
    """采集一条业务线"""
    log(f"\n{'─'*50}")
    log(f"📂 {line_name}: {', '.join(keywords)}")
    
    total = 0
    idx = load_index()
    
    for kw in keywords:
        # 不重复加"审计"前缀（关键词已包含）
        if "审计" not in kw:
            search_query = f"审计 {kw}"
        else:
            search_query = kw
        
        log(f"  🔍 {search_query}")
        results = search_bing(search_query, max_per_kw)
        
        for item in results:
            article_id = make_id(item['url'], item['title'])
            
            # 先质量评分，再决定去向；B/C 不进入正式索引
            quality = assess_quality(item, line_name, kw)
            if quality["status"] != "A":
                save_candidate(item, line_name, kw, quality)
                log(f"    [{quality['status']}/{quality['score']}] {item['title'][:55]}", "WARN")
                continue
            
            # 去重
            if article_id in idx['items']:
                log(f"    {item['title'][:50]}", "SKIP")
                continue
            
            save_article(
                source="bing",
                title=item['title'],
                url=item['url'],
                snippet=item['snippet'],
                matched_line=line_name,
                source_domain=item['domain'],
            )
            log(f"    [A/{quality['score']}] {item['title'][:60]}", "OK")
            total += 1
            
            if total >= max_per_kw:
                break
        
        time.sleep(1.5)  # 礼貌间隔
    
    return total

def generate_report():
    """生成采集日报"""
    idx = load_index()
    today = datetime.now().strftime("%Y-%m-%d")
    
    report = f"""# 融策智能采集日报 — {today}

## 📊 统计
- **累计入库**: {idx['stats']['total']} 篇
- **上次运行**: {idx.get('last_run', '首次运行')}

### 按业务线
"""
    for line_name in BUSINESS_LINES:
        cnt = idx['stats']['by_line'].get(line_name, 0)
        report += f"- {line_name}: {cnt} 篇\n"
    
    report += f"\n### 最新入库（5篇）\n"
    # 按时间倒序
    sorted_items = sorted(
        idx['items'].items(),
        key=lambda x: x[1].get('fetched_at', ''),
        reverse=True
    )[:5]
    
    for item_id, meta in sorted_items:
        lines = meta.get('matched_line', '')
        domain = meta.get('source_domain', '')
        report += f"- [{meta['title']}]({meta['url']}) — `{lines}` | {domain}\n"
    
    report += "\n---\n*融策智能采集引擎 v3.0 · Bing搜索版*"
    
    report_path = WORKSPACE / "knowledge" / "intel_summaries" / f"intel_report_{today}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    log(f"📊 报告: {report_path}")
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="融策智能采集引擎 v3.0")
    parser.add_argument("--run", action="store_true", help="全量采集")
    parser.add_argument("--line", type=str, help="单业务线")
    parser.add_argument("--max", type=int, default=3, help="每关键词最多条数")
    parser.add_argument("--report", action="store_true", help="生成日报")
    parser.add_argument("--save", type=str, help="保存文章(JSON)")
    parser.add_argument("--stats", action="store_true", help="统计信息")
    
    args = parser.parse_args()
    
    log("=" * 50)
    log("  融策智能采集引擎 v3.0 (Bing搜索)")
    log("=" * 50)
    
    INTEL_RAW.mkdir(parents=True, exist_ok=True)
    
    if args.stats:
        idx = load_index()
        print(json.dumps(idx["stats"], ensure_ascii=False, indent=2))
        return
    
    if args.report:
        generate_report()
        return
    
    if args.save:
        try:
            data = json.loads(args.save)
            path = save_article(
                data.get("source", "manual"),
                data.get("title", "无标题"),
                data.get("url", ""),
                data.get("snippet", ""),
                data.get("matched_line", "未分类"),
                data.get("source_domain", ""),
            )
            log(f"✅ {path}")
        except json.JSONDecodeError as e:
            log(f"JSON 解析失败: {e}", "ERROR")
        return
    
    # 采集
    if args.line:
        if args.line not in BUSINESS_LINES:
            log(f"未知业务线: {args.line}", "ERROR")
            log(f"可选: {list(BUSINESS_LINES.keys())}", "INFO")
            return
        lines = [(args.line, BUSINESS_LINES[args.line])]
    elif args.run:
        lines = list(BUSINESS_LINES.items())
    else:
        parser.print_help()
        return
    
    total = 0
    for line_name, keywords in lines:
        total += collect_line(line_name, keywords, args.max)
    
    log(f"\n{'='*50}")
    log(f"✅ 采集完成: {total} 篇新文章")
    
    # 生成日报
    generate_report()
    
    # 最终统计
    idx = load_index()
    log(f"📊 累计入库: {idx['stats']['total']} 篇")

if __name__ == "__main__":
    main()