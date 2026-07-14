"""
Tender Scraper v3 — 列表页直爬 + 本地关键词过滤
数据源: http://www.ccgp.gov.cn/cggg/ (采购公告/中标公告/成交公告)
"""
import re, json, sys, time, hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

import requests

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'http://www.ccgp.gov.cn'
# Listing page types: zygg=中央, dfgg=地方
LIST_URLS = [
    f'{BASE_URL}/cggg/zygg/',      # 中央公告（全部类型）
    f'{BASE_URL}/cggg/dfgg/',      # 地方公告
]
# Sub-pages per category
CATEGORY_PATHS = ['gkzb', 'zbgg', 'cjgg', 'jzxcs', 'jzxtpgg', 'dyly', 'fblbgg']

# Business-scope keywords for local filtering
SCOPE_KEYWORDS = [
    '审计', '绩效评价', '绩效管理', '工程咨询', '工程造价', '竣工决算',
    '会计服务', '资产评估', '资产清查', '财务咨询', '税务', '招标代理',
    '政府采购代理', '全过程', '跟踪审计', '经济责任', '专项资金',
    '预算绩效', '监督检查', '补贴', '补助资金', '绩效目标',
    '内部控制', '内控', '合规', '法律服务', '行政复议',
]

EXCLUDE_KEYWORDS = [
    '软件开发', '系统集成', '硬件采购', '信息化平台', '服务器', '网络设备',
    '物业服务', '保安服务', '保洁服务', '食堂', '食材配送', '印刷服务',
    '车辆采购', '消防设备', '医疗设备', '实验室', '家具采购', '服装',
    '绿化养护', '环卫', '垃圾清运', '空调', '电梯', '厨房设备',
    '校舍维修', '宿舍粉刷', '道路施工', '管网', '排水', '路面',
    '体检服务', '健康检查', '职工福利', '慰问品', '体检',
]


@dataclass
class TenderItem:
    id: str
    title: str
    url: str
    publish_date: str
    procuring_entity: str
    announcement_type: str
    province: str
    source_type: str = 'tender_announcement'
    scraped_at: str = ''
    matched_keywords: list = None


def _safe_get(url: str, retries: int = 2) -> Optional[str]:
    """HTTP GET with retry and polite delays."""
    for i in range(retries + 1):
        try:
            resp = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; RongCeBot/1.0)',
                'Accept': 'text/html,application/xhtml+xml',
            }, timeout=30)
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                return resp.text
            elif resp.status_code == 429:
                wait = (i + 1) * 15
                print(f'    Rate limited, waiting {wait}s...')
                time.sleep(wait)
            else:
                time.sleep(3)
        except Exception:
            time.sleep(5)
    return None


def _parse_listing(html: str, base_path: str) -> List[Dict]:
    """Parse a ccgp.gov.cn listing page."""
    results = []

    # Each entry: <li> with <a href="...">Title</a> then metadata
    # Pattern varies by page type but generally:
    # <a href=".../YYYYMM/tYYYYMMDD_XXXXXXXX.htm" ...>Title</a>
    # 公告类型\n发布时间：... 地域：... 采购人：...

    entries = re.split(r'<li[^>]*>', html)[1:]  # Skip before first <li>
    for entry in entries:
        # Extract link and title
        link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', entry, re.DOTALL)
        if not link_match:
            continue

        href = link_match.group(1)
        title = re.sub(r'<[^>]+>', '', link_match.group(2)).strip()

        if not title or len(title) < 6:
            continue

        # Skip non-relevant by title
        matched_kw = [kw for kw in SCOPE_KEYWORDS if kw in title]
        if not matched_kw:
            continue
        if any(kw in title for kw in EXCLUDE_KEYWORDS):
            continue

        # Extract date
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', entry)
        if not date_match:
            # Try alternate format
            date_match = re.search(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2})', entry)
        if not date_match:
            continue

        # Extract announcement type
        atype = ''
        # Type text is usually before or after the link
        type_match = re.search(r'(公开招标|竞争性磋商|竞争性谈判|询价|单一来源|中标|成交|更正|终止|废标)', entry)
        if type_match:
            atype = type_match.group(1)

        # Extract purchaser
        purchaser = ''
        pur_match = re.search(r'采购人[：:]\s*([^\s<]+)', entry)
        if pur_match:
            purchaser = pur_match.group(1).strip()

        # Extract province
        province = ''
        prov_match = re.search(r'地域[：:]\s*([^\s<]+)', entry)
        if prov_match:
            province = prov_match.group(1).strip()

        # Build URL
        if href.startswith('http'):
            full_url = href
        elif href.startswith('./'):
            full_url = urljoin(f'{BASE_URL}{base_path}', href[2:])
        else:
            full_url = urljoin(f'{BASE_URL}{base_path}', href)

        results.append({
            'id': hashlib.md5(full_url.encode()).hexdigest()[:12],
            'title': title,
            'url': full_url,
            'publish_date': date_match.group(1).replace('.', '-').split(' ')[0],
            'procuring_entity': purchaser,
            'announcement_type': atype,
            'province': province,
            'matched_keywords': matched_kw,
        })

    return results


def scrape_listing(url: str, max_pages: int = 3) -> List[TenderItem]:
    """Scrape paginated listing pages."""
    items = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        if page == 1:
            page_url = url if url.endswith('/') else f'{url}/'
        else:
            page_url = f'{url.rstrip("/")}/index_{page}.htm'

        html = _safe_get(page_url)
        if not html:
            print(f'  page {page}: failed to fetch')
            break

        # Determine base path for URL resolution
        base_path = '/cggg/zygg/' if 'zygg' in url else '/cggg/dfgg/'

        results = _parse_listing(html, base_path)
        new_count = 0
        for r in results:
            if r['id'] not in seen_ids:
                seen_ids.add(r['id'])
                items.append(TenderItem(
                    **r, scraped_at=datetime.now().isoformat()
                ))
                new_count += 1

        print(f'  page {page}: {new_count} items (total: {len(items)})')
        if new_count == 0:
            break
        time.sleep(1.5)

    return items


def scrape(days_back: int = 7, max_pages: int = 3) -> List[TenderItem]:
    """Main scraper: all listing types."""
    all_items = []

    for list_url in LIST_URLS:
        label = '中央' if 'zygg' in list_url else '地方'
        print(f'\n[{label}公告] {list_url}')
        items = scrape_listing(list_url, max_pages)
        all_items.extend(items)

    # Deduplicate across listing types
    seen = set()
    unique = []
    for item in all_items:
        if item.id not in seen:
            seen.add(item.id)
            unique.append(item)

    # Filter by date
    cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    filtered = [i for i in unique if i.publish_date >= cutoff]

    print(f'\nTotal: {len(unique)} unique, {len(filtered)} within {days_back} days')
    return filtered


# ============================================================
# CLI
# ============================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--pages', type=int, default=2)
    parser.add_argument('--output', '-o')
    args = parser.parse_args()

    print(f'Tender Scraper v3: {args.days} days, {args.pages} pages')
    print('=' * 60)

    items = scrape(days_back=args.days, max_pages=args.pages)

    # Stats
    types = {}
    provs = {}
    kws = {}
    for item in items:
        t = item.announcement_type or '其他'
        types[t] = types.get(t, 0) + 1
        p = item.province or '未知'
        provs[p] = provs.get(p, 0) + 1
        for kw in (item.matched_keywords or []):
            kws[kw] = kws.get(kw, 0) + 1

    print(f'\n公告类型: {types}')
    print(f'省份TOP10: {dict(sorted(provs.items(), key=lambda x:x[1], reverse=True)[:10])}')
    print(f'高频关键词: {dict(sorted(kws.items(), key=lambda x:x[1], reverse=True)[:10])}')

    if args.output and items:
        data = [asdict(i) for i in items]
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f'\nSaved: {args.output}')

    print(f'\nRecent tenders:')
    for item in items[:8]:
        kws_str = ','.join(item.matched_keywords[:3])
        print(f'  [{item.publish_date}] {item.title[:55]}...')
        print(f'    {item.procuring_entity} | {item.province} | {item.announcement_type} | {kws_str}')
