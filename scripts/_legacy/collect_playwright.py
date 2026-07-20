"""
融策智能采集引擎 v2.0 — Playwright 无头浏览器版
==============================================
支持 NCPSSD（国家哲学社会科学文献中心）自动搜索采集

用法：
  python scripts/collect_playwright.py                    # 采集全部12条业务线
  python scripts/collect_playwright.py --line 经责审计     # 单业务线
  python scripts/collect_playwright.py --keyword "绩效评价" # 自定义关键词
  python scripts/collect_playwright.py --headless          # 无头模式（后台运行）
  python scripts/collect_playwright.py --max 5             # 每关键词最多5条
"""
import os, sys, json, time, hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
INTEL_RAW = WORKSPACE / "knowledge" / "intel_raw"
INTEL_INDEX = WORKSPACE / "knowledge" / "intel_index.json"

BUSINESS_KEYWORDS = [
    ("经责审计", ["经济责任审计", "离任审计"]),
    ("收支审计", ["财政收支审计", "预算收入审计"]),
    ("预算执行", ["预算执行审计", "部门预算审计"]),
    ("专项资金", ["专项资金审计", "专项债审计"]),
    ("往来款清理", ["往来款项审计", "债权债务清理"]),
    ("招投标审计", ["招投标审计", "政府采购审计"]),
    ("国企审计", ["国有企业审计", "国有资产审计"]),
    ("成本效益审计", ["绩效评价", "成本效益分析"]),
    ("能源审计", ["能源审计", "资源环境审计"]),
    ("工程决算审计", ["竣工决算审计", "工程造价审计"]),
    ("预算绩效管理", ["预算绩效管理", "事前绩效评估"]),
    ("政府补贴审计", ["政府补贴审计", "补助资金审计"]),
]

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")

def load_index():
    if INTEL_INDEX.exists():
        return json.load(open(INTEL_INDEX, 'r', encoding='utf-8'))
    return {"items": {}, "last_run": None, "stats": {"total": 0, "by_source": {}, "by_line": {}}}

def save_index(idx):
    INTEL_INDEX.parent.mkdir(parents=True, exist_ok=True)
    json.dump(idx, open(INTEL_INDEX, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def save_article(source, title, url, abstract, authors, keywords, matched_line):
    """保存一篇文章"""
    article_id = hashlib.md5(f"{url}{title}".encode()).hexdigest()[:12]
    date_str = datetime.now().strftime("%Y%m%d")
    
    source_dir = INTEL_RAW / source
    source_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = source_dir / f"{date_str}_{article_id}.md"
    
    meta = {
        "id": article_id,
        "source": source,
        "title": title,
        "url": url,
        "authors": authors,
        "keywords": keywords,
        "matched_line": matched_line,
        "fetched_at": datetime.now().isoformat(),
    }
    
    content = f"---\n{json.dumps(meta, ensure_ascii=False, indent=2)}\n---\n\n"
    content += f"# {title}\n\n"
    content += f"> 来源: [{source}]({url})\n"
    if authors:
        content += f"> 作者: {', '.join(authors)}\n"
    if keywords:
        content += f"> 关键词: {', '.join(keywords)}\n"
    content += f"> 业务线: {matched_line}\n\n"
    content += f"## 摘要\n\n{abstract}\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 更新索引
    idx = load_index()
    idx["items"][article_id] = meta
    idx["stats"]["total"] = idx["stats"].get("total", 0) + 1
    idx["stats"]["by_source"][source] = idx["stats"]["by_source"].get(source, 0) + 1
    idx["stats"]["by_line"][matched_line] = idx["stats"]["by_line"].get(matched_line, 0) + 1
    idx["last_run"] = datetime.now().isoformat()
    save_index(idx)
    
    return filepath

def collect_ncpssd(page, keyword, matched_line, max_results=5):
    """从 NCPSSD 搜索并采集"""
    results = []
    
    try:
        # 方案A: 直接访问搜索页面（NCPSSD 可能支持 GET 参数）
        log(f"  访问 NCPSSD 搜索页...", "INFO")
        encoded = quote(keyword)
        
        # 尝试多个可能的搜索 URL
        search_urls = [
            f"https://www.ncpssd.cn/search?keyword={encoded}",
            f"https://www.ncpssd.cn/literature/search?keyword={encoded}",
            f"https://www.ncpssd.cn/search/list?keyword={encoded}",
            f"https://www.ncpssd.cn/search?q={encoded}",
        ]
        
        for url in search_urls:
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
                time.sleep(2)
                
                # 检查页面是否有实际内容（不是404或空白）
                body_text = page.inner_text("body")
                if len(body_text) > 100 and "404" not in body_text[:200]:
                    log(f"  ✅ 直接搜索: {keyword}", "INFO")
                    break
                else:
                    log(f"  ⚠️ 该URL无结果，尝试下一个", "WARN")
            except:
                continue
        else:
            # 全部URL失败，走交互搜索
            log(f"  🔄 切换到交互搜索...", "WARN")
            page.goto("https://www.ncpssd.cn", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            
            # 尝试多种方式触发搜索
            for attempt in range(3):
                try:
                    # 尝试 Ctrl+K 打开搜索（常见快捷键）
                    page.keyboard.press("Control+k")
                    time.sleep(1)
                    
                    # 找可见输入框
                    inputs = page.locator('input[type="text"]:visible, input:visible, [contenteditable="true"]:visible')
                    count = inputs.count()
                    for i in range(min(count, 5)):
                        inp = inputs.nth(i)
                        try:
                            inp.click()
                            time.sleep(0.3)
                            inp.fill(keyword)
                            page.keyboard.press("Enter")
                            time.sleep(3)
                            page.wait_for_load_state("networkidle", timeout=10000)
                            
                            # 检查是否有搜索结果
                            body_text = page.inner_text("body")
                            if keyword in body_text:
                                log(f"  ✅ 交互搜索成功", "INFO")
                                break
                        except:
                            continue
                    break
                except Exception as e:
                    log(f"  尝试 {attempt+1}/3 失败: {e}", "WARN")
                    time.sleep(1)
        
        # 等待搜索结果加载
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)
        
        # 提取搜索结果
        try:
            # 先截图看看页面状态
            page.screenshot(path=str(WORKSPACE / "logs" / f"ncpssd_result_{keyword}.png"))
            
            # 提取所有链接和文本
            items = page.evaluate("""
                () => {
                    const results = [];
                    // 尝试多种选择器找到搜索结果
                    const selectors = [
                        '.result-item', '.search-result', '.doc-item',
                        '.el-card', 'li[class*="result"]', 'div[class*="item"]',
                        '.list-item', 'a[href*="detail"]', 'a[href*="literature"]'
                    ];
                    
                    for (const sel of selectors) {
                        const elements = document.querySelectorAll(sel);
                        for (const el of elements) {
                            const title = el.querySelector('a, h3, h4, .title')?.textContent?.trim();
                            const link = el.querySelector('a')?.href;
                            const text = el.textContent?.trim()?.substring(0, 300);
                            if (title && link) {
                                results.push({ title, link, text });
                            }
                        }
                        if (results.length > 0) break;
                    }
                    
                    // fallback: 提取所有包含中文的链接
                    if (results.length === 0) {
                        const allLinks = document.querySelectorAll('a');
                        for (const a of allLinks) {
                            const text = a.textContent.trim();
                            if (text.length > 10 && /[\\u4e00-\\u9fff]/.test(text)) {
                                results.push({ title: text, link: a.href, text: '' });
                            }
                        }
                    }
                    
                    return results.slice(0, 20);
                }
            """)
            
            log(f"  找到 {len(items)} 条结果", "INFO")
            
            for item in items[:max_results]:
                title = item.get('title', '').strip()
                url = item.get('link', '')
                text = item.get('text', '')
                
                if not title or not url:
                    continue
                    
                # 判断是否已采集
                idx = load_index()
                article_id = hashlib.md5(f"{url}{title}".encode()).hexdigest()[:12]
                if article_id in idx['items']:
                    log(f"    ⏭️ 已采集: {title[:50]}", "SKIP")
                    continue
                
                # 保存
                filepath = save_article(
                    source="ncpssd",
                    title=title,
                    url=url,
                    abstract=text[:500] if text else "（需进入详情页获取摘要）",
                    authors=[],
                    keywords=[keyword],
                    matched_line=matched_line,
                )
                
                results.append({
                    "title": title,
                    "url": url,
                    "file": str(filepath),
                    "line": matched_line,
                })
                
                log(f"    ✅ {title[:60]}", "OK")
                
        except Exception as e:
            log(f"  ⚠️ 提取结果失败: {e}", "WARN")
            page.screenshot(path=str(WORKSPACE / "logs" / f"ncpssd_error_{keyword}.png"))
            
    except Exception as e:
        log(f"  ❌ NCPSSD 采集失败: {e}", "ERROR")
    
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description="融策智能采集引擎 v2.0")
    parser.add_argument("--line", type=str, help="限定业务线")
    parser.add_argument("--keyword", type=str, help="自定义关键词")
    parser.add_argument("--max", type=int, default=5, help="每关键词最多条数")
    parser.add_argument("--headless", action="store_true", default=True, help="无头模式")
    parser.add_argument("--show", action="store_true", help="显示浏览器窗口")
    
    args = parser.parse_args()
    
    log("=" * 50)
    log("  融策智能采集引擎 v2.0 (Playwright)")
    log("=" * 50)
    
    INTEL_RAW.mkdir(parents=True, exist_ok=True)
    (WORKSPACE / "logs").mkdir(parents=True, exist_ok=True)
    
    # 确定采集任务
    if args.keyword:
        tasks = [("自定义搜索", [args.keyword])]
    elif args.line:
        tasks = [(ln, kw) for ln, kw in BUSINESS_KEYWORDS if ln == args.line]
        if not tasks:
            log(f"未找到业务线: {args.line}", "ERROR")
            return
    else:
        tasks = BUSINESS_KEYWORDS
    
    total_results = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.show)
        context = browser.new_context(
            locale="zh-CN",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            for line_name, keywords in tasks:
                log(f"\n{'─'*40}")
                log(f"📂 业务线: {line_name}")
                log(f"{'─'*40}")
                
                for kw in keywords:
                    log(f"🔍 {kw}")
                    results = collect_ncpssd(page, kw, line_name, args.max)
                    total_results += len(results)
                    time.sleep(2)  # 礼貌间隔
                    
        finally:
            context.close()
            browser.close()
    
    log(f"\n{'='*50}")
    log(f"✅ 采集完成: {total_results} 篇新文章")
    
    # 打印统计
    idx = load_index()
    log(f"📊 累计入库: {idx['stats']['total']} 篇")
    for line, cnt in sorted(idx['stats'].get('by_line', {}).items(), key=lambda x: -x[1]):
        log(f"  {line}: {cnt}")

if __name__ == "__main__":
    main()