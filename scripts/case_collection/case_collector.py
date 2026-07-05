#!/usr/bin/env python3
"""
审计案例采集器 v1.0
每周采集财政部政策和5省审计厅案例，生成待确认清单
"""

import json, sys, hashlib, datetime, re
from pathlib import Path
from urllib.request import Request, urlopen, ProxyHandler, build_opener
from urllib.error import URLError

sys.stdout.reconfigure(encoding='utf-8')

CONFIG = Path(__file__).parent.parent / "config" / "case_sources.json"
HISTORY = Path(__file__).parent.parent / "logs" / "case_collection" / "history.json"
PENDING = Path(__file__).parent.parent / "logs" / "case_collection" / "pending"

def load_config():
    with open(CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_history():
    if HISTORY.exists():
        with open(HISTORY, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"collected": {}, "last_run": None}

def save_history(history):
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_page(url, timeout=20):
    """尝试抓取页面（无代理优先，避免政府网站被墙）"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    # 方法1: 无代理直连（政府网站优先）
    try:
        proxy_support = ProxyHandler({})
        opener = build_opener(proxy_support)
        req = Request(url, headers=headers)
        with opener.open(req, timeout=timeout) as resp:
            content = resp.read()
            # 尝试多种编码
            for enc in ['utf-8', 'gbk', 'gb2312']:
                try:
                    return content.decode(enc)
                except:
                    continue
    except Exception as e:
        print(f"  ⚠ 无代理失败: {e}")
    
    # 方法2: 系统代理
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            for enc in ['utf-8', 'gbk', 'gb2312']:
                try:
                    return content.decode(enc)
                except:
                    continue
    except Exception as e:
        print(f"  ⚠ 系统代理失败: {e}")
    
    return None

def extract_links(html, base_url):
    """从HTML提取文章链接（简单正则，适配常见政府网站列表页）"""
    links = []
    # 匹配常见列表格式: <a href="xxx">标题</a>
    pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    for href, title in matches:
        title = title.strip()
        if len(title) < 5 or len(title) > 200:
            continue
        
        # 补全相对路径
        if href.startswith('http'):
            full_url = href
        elif href.startswith('/'):
            base = base_url.split('/', 3)[:3]
            full_url = '/'.join(base) + href
        else:
            full_url = base_url.rsplit('/', 1)[0] + '/' + href
        
        links.append({"title": title, "url": full_url})
    
    return links

def filter_links(links, filters):
    """按配置过滤链接"""
    filtered = []
    for item in links:
        title = item['title']
        
        # 排除关键词
        if any(kw in title for kw in filters.get('exclude_keywords', [])):
            continue
        
        # 必须包含关键词
        must_contain = filters.get('must_contain_any', [])
        if must_contain and not any(kw in title for kw in must_contain):
            continue
        
        filtered.append(item)
    
    return filtered

def generate_hash(url):
    """生成URL哈希用于去重"""
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:12]

def collect_source(site, filters, history):
    """采集单个来源"""
    print(f"\n📥 采集: {site['name']}")
    print(f"   URL: {site['url']}")
    
    html = fetch_page(site['url'])
    if not html:
        print("  ❌ 抓取失败")
        return []
    
    links = extract_links(html, site['url'])
    print(f"  📋 提取 {len(links)} 条链接")
    
    links = filter_links(links, filters)
    print(f"  ✅ 过滤后 {len(links)} 条")
    
    # 去重
    new_items = []
    for item in links:
        item_hash = generate_hash(item['url'])
        if item_hash not in history['collected']:
            item['hash'] = item_hash
            item['source'] = site['name']
            item['type'] = site['type']
            item['collected_at'] = datetime.datetime.now().isoformat()
            new_items.append(item)
            history['collected'][item_hash] = {
                "url": item['url'],
                "title": item['title'],
                "collected_at": item['collected_at']
            }
    
    print(f"  🆕 新增 {len(new_items)} 条")
    return new_items

def main():
    print("=" * 60)
    print("审计案例采集器 v1.0")
    print("=" * 60)
    
    config = load_config()
    history = load_history()
    filters = config['filters']
    
    all_new_items = []
    
    # 采集财政部政策
    if config['sources']['mof_policies']['enabled']:
        print("\n【财政部绩效相关政策法规】")
        for site in config['sources']['mof_policies']['sites']:
            items = collect_source(site, filters, history)
            all_new_items.extend(items)
    
    # 采集省级审计厅案例
    if config['sources']['provincial_audit']['enabled']:
        print("\n【省级审计厅案例库】")
        for site in config['sources']['provincial_audit']['sites']:
            items = collect_source(site, filters, history)
            all_new_items.extend(items)
    
    # 保存待确认清单
    if all_new_items:
        PENDING.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pending_file = PENDING / f"pending_{timestamp}.json"
        
        with open(pending_file, 'w', encoding='utf-8') as f:
            json.dump({
                "collected_at": datetime.datetime.now().isoformat(),
                "total": len(all_new_items),
                "items": all_new_items
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✅ 采集完成：{len(all_new_items)} 条新案例")
        print(f"📝 待确认清单: {pending_file}")
        print(f"{'='*60}")
        
        # 打印预览
        print("\n【待确认案例预览】")
        for i, item in enumerate(all_new_items[:10], 1):
            print(f"{i}. [{item['type']}] {item['title']}")
            print(f"   来源: {item['source']}")
            print(f"   链接: {item['url']}")
        
        if len(all_new_items) > 10:
            print(f"\n... 还有 {len(all_new_items) - 10} 条")
    else:
        print(f"\n{'='*60}")
        print("ℹ️  本次未发现新案例")
        print(f"{'='*60}")
    
    # 更新历史记录
    history['last_run'] = datetime.datetime.now().isoformat()
    save_history(history)
    
    return len(all_new_items)

if __name__ == "__main__":
    try:
        count = main()
        sys.exit(0 if count > 0 else 1)
    except Exception as e:
        print(f"\n❌ 采集失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
