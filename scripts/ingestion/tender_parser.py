"""
Tender Parser — 解析 ccgp.gov.cn 搜索页的 web_fetch 输出
因为Python直连被WAF拦截，采集通过OpenClaw cron的web_fetch完成，
本脚本只负责解析和入库。
"""
import re, json, sys, hashlib
from datetime import datetime
from typing import List, Dict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def parse_search_markdown(md_text: str) -> List[Dict]:
    """
    Parse web_fetch markdown output from ccgp.gov.cn search results.
    Each tender entry has:
    - Title as markdown link
    - Date line
    - 采购人 / 代理机构
    - 公告类型
    - 省份
    - Optional: 服务/商务服务/审计服务 (category path)
    """
    results = []

    # Split into tender blocks - each starts with a markdown link
    # Pattern: "- [Title](URL)" followed by description
    blocks = re.split(r'\n- \[', md_text)
    for block in blocks[1:]:  # Skip first (header)
        block = '[' + block  # Restore the markdown link

        # Extract title and URL
        link_match = re.match(r'\[(.*?)\]\((.*?)\)', block)
        if not link_match:
            continue

        title = link_match.group(1).strip()
        url = link_match.group(2).strip()

        if not title or len(title) < 6:
            continue

        # Extract date
        date_match = re.search(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})', block)
        publish_date = date_match.group(1).replace('.', '-').split(' ')[0] if date_match else ''

        # Extract purchaser
        purchaser = ''
        pur_match = re.search(r'采购人[：:]\s*([^\n|]+)', block)
        if pur_match:
            purchaser = pur_match.group(1).strip()

        # Extract agency
        agency = ''
        ag_match = re.search(r'代理机构[：:]\s*([^\n|]+)', block)
        if ag_match:
            agency = ag_match.group(1).strip()

        # Extract announcement type
        atype_match = re.search(r'(中标公告|成交公告|公开招标公告|竞争性磋商|竞争性谈判|询价公告|单一来源|更正公告|终止公告|废标公告)', block)
        atype = atype_match.group(1) if atype_match else ''

        # Extract province
        province = ''
        prov_match = re.search(r'\|\s*([\u4e00-\u9fff]{2,4})\s*\|', block)
        if prov_match:
            province = prov_match.group(1).strip()
        else:
            prov_match2 = re.search(r'\|\s*([\u4e00-\u9fff]{2,4})\s*$', block, re.MULTILINE)
            if prov_match2:
                province = prov_match2.group(1).strip()

        # Extract category path
        cat_match = re.search(r'服务[/\u4e00-\u9fff\w]+', block)
        category = cat_match.group(0).strip() if cat_match else '审计服务'

        results.append({
            'id': hashlib.md5(url.encode()).hexdigest()[:12],
            'title': title,
            'url': url,
            'publish_date': publish_date,
            'procuring_entity': purchaser,
            'agency': agency,
            'announcement_type': atype,
            'province': province,
            'category_path': category,
            'scraped_at': datetime.now().isoformat(),
            'source_type': 'tender_announcement',
        })

    return results


def parse_and_save(md_text: str, output_path: str, keyword: str = '') -> List[Dict]:
    """Parse markdown and save JSON."""
    results = parse_search_markdown(md_text)

    # Save
    out_file = Path(output_path)
    existing = []
    if out_file.exists():
        with open(out_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)

    # Merge, dedup
    existing_ids = {r['id'] for r in existing}
    new_items = [r for r in results if r['id'] not in existing_ids]
    merged = existing + new_items

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f'Keyword: {keyword or "(all)"}')
    print(f'  Found: {len(results)}, New: {len(new_items)}, Total: {len(merged)}')

    # Show summary
    if results:
        types = {}
        provs = {}
        for r in results[:30]:
            t = r['announcement_type'] or '其他'
            types[t] = types.get(t, 0) + 1
            p = r['province'] or '未知'
            provs[p] = provs.get(p, 0) + 1

        print(f'  Types: {types}')
        print(f'  Provinces（四川优先）: ', end='')
        sc = provs.pop('四川', 0)
        if sc:
            print(f'四川({sc}) ', end='')
        print(sorted(provs.items(), key=lambda x: x[1], reverse=True)[:5])

        # Sichuan highlights
        sc_items = [r for r in results if r['province'] == '四川']
        if sc_items:
            print(f'\n  🔥 四川招标:')
            for item in sc_items:
                print(f'    [{item["publish_date"]}] {item["title"][:60]}')
                print(f'    采购人: {item["procuring_entity"]} | {item["announcement_type"]}')

    return results


def to_ingestion_input(items: List[Dict]) -> List[Dict]:
    """Convert to ingestion pipeline input format."""
    docs = []
    for item in items:
        text = f"""招标项目: {item['title']}
采购人: {item['procuring_entity']}
代理机构: {item.get('agency', '')}
公告类型: {item['announcement_type']}
省份: {item['province']}
采购品类: {item.get('category_path', '审计服务')}"""
        docs.append({
            'text': text,
            'title': item['title'],
            'url': item['url'],
            'source_type': 'tender_announcement',
            'publish_date': item['publish_date'],
        })
    return docs


# ============================================================
# CLI - accept web_fetch output from stdin or file
# ============================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Parse ccgp search results')
    parser.add_argument('--input', '-i', help='Input markdown file (from web_fetch)')
    parser.add_argument('--output', '-o', default='knowledge/taxonomy/tenders.json',
                        help='Output JSON file (cumulative)')
    parser.add_argument('--keyword', '-k', default='', help='Search keyword used')
    parser.add_argument('--stdin', action='store_true', help='Read from stdin')
    args = parser.parse_args()

    if args.stdin:
        import sys
        md_text = sys.stdin.read()
    elif args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            md_text = f.read()
    else:
        print('Usage: --input FILE or --stdin')
        sys.exit(1)

    results = parse_and_save(md_text, args.output, args.keyword)

    # Also output in ingestion format
    if results:
        ingestion_docs = to_ingestion_input(results)
        ingest_path = args.output.replace('.json', '_ingestion.json')
        with open(ingest_path, 'w', encoding='utf-8') as f:
            json.dump(ingestion_docs, f, ensure_ascii=False, indent=2)
        print(f'\n  Ingestion-ready: {ingest_path} ({len(ingestion_docs)} docs)')
