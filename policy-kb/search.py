#!/usr/bin/env python3
"""
政策资料库检索工具
用法:
  python search.py "政府采购"           # 按关键词检索
  python search.py --domain 03          # 按领域编号检索
  python search.py --audit 绩效评价     # 按审计场景检索
  python search.py --list-domains       # 列出所有领域
  python search.py --stats              # 资料库统计信息
"""

import argparse
import json
import os
import sys
import glob

KB_ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(KB_ROOT, '.index', 'catalog.json')


def load_catalog():
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_domains(catalog):
    """列出所有领域"""
    for cat_key, cat_data in catalog['catalogs'].items():
        print(f"\n{'='*50}")
        print(f"  {cat_data['name']}（{cat_data['count']} 个领域）")
        print(f"{'='*50}")
        for d in cat_data['domains']:
            path = f"policy-kb/{cat_data['name']}/{d['id']}-{d['name']}/"
            files = glob.glob(os.path.join(KB_ROOT, cat_data['name'], f"{d['id']}-{d['name']}", '*.txt'))
            count = len(files)
            status = '📁' if count > 0 else '📭'
            print(f"  {status} [{d['id']}] {d['name']:12s} — {', '.join(d['keywords'][:4])}  ({count}份)")
            print(f"      {path}")


def search_by_keyword(catalog, keyword):
    """按关键词检索领域"""
    results = []
    kw = keyword.lower()
    for cat_key, cat_data in catalog['catalogs'].items():
        for d in cat_data['domains']:
            match_in = []
            if kw in d['name'].lower():
                match_in.append('领域名')
            matched_kw = [k for k in d['keywords'] if kw in k.lower()]
            if matched_kw:
                match_in.append(f"关键词: {', '.join(matched_kw)}")
            if match_in:
                results.append({
                    'catalog': cat_data['name'],
                    'id': d['id'],
                    'name': d['name'],
                    'match': ' | '.join(match_in),
                    'path': os.path.join(cat_data['name'], f"{d['id']}-{d['name']}"),
                })

    if not results:
        print(f'未找到与 "{keyword}" 相关的领域')
        return

    print(f'\n🔍 关键词 "{keyword}" 匹配 {len(results)} 个领域:\n')
    for r in results:
        full_path = os.path.join(KB_ROOT, r['path'])
        files = glob.glob(os.path.join(full_path, '*.txt'))
        count = len(files)
        print(f"  [{r['id']}] {r['name']:12s}  [{r['catalog']}]")
        print(f"       匹配: {r['match']}")
        print(f"       路径: policy-kb/{r['path']}/")
        print(f"       已收录: {count} 份政策文件\n")


def search_by_audit_scene(catalog, scene):
    """按审计场景检索"""
    audit_map = catalog.get('audit_mapping', {})
    if scene not in audit_map:
        print(f'未知审计场景: {scene}')
        print(f'可用场景: {", ".join(audit_map.keys())}')
        return

    refs = audit_map[scene]
    print(f'\n📋 审计场景: {scene}')
    print(f'{"─"*40}')
    print(f'涉及领域:')
    for ref in refs:
        cat_key, domain_id = ref.split('/')
        cat_data = catalog['catalogs'].get(cat_key, {})
        for d in cat_data.get('domains', []):
            if d['id'] == domain_id:
                print(f'  [{d["id"]}] {d["name"]:12s}  [{cat_data["name"]}]')
                print(f'       {", ".join(d["keywords"][:5])}')
                break


def show_stats(catalog):
    """统计信息"""
    total_domains = 0
    total_files = 0
    for cat_key, cat_data in catalog['catalogs'].items():
        for d in cat_data['domains']:
            total_domains += 1
            full_path = os.path.join(KB_ROOT, cat_data['name'], f"{d['id']}-{d['name']}")
            files = glob.glob(os.path.join(full_path, '*.txt'))
            total_files += len(files)

    print(f'\n📊 政策资料库统计')
    print(f'{"─"*40}')
    print(f'  总领域数: {total_domains}')
    print(f'  已收录政策: {total_files} 份')
    print(f'  审计场景: {len(catalog.get("audit_mapping", {}))} 个')
    print(f'  空目录 (待填充): {total_domains - total_files if total_files < total_domains else 0} 个\n')


def main():
    parser = argparse.ArgumentParser(description='政策资料库检索工具')
    parser.add_argument('keyword', nargs='?', help='检索关键词')
    parser.add_argument('--list-domains', '-l', action='store_true', help='列出所有领域')
    parser.add_argument('--audit', '-a', help='按审计场景检索')
    parser.add_argument('--stats', '-s', action='store_true', help='统计信息')
    args = parser.parse_args()

    catalog = load_catalog()

    if args.list_domains:
        list_domains(catalog)
        return

    if args.stats:
        show_stats(catalog)
        return

    if args.audit:
        search_by_audit_scene(catalog, args.audit)
        return

    if args.keyword:
        search_by_keyword(catalog, args.keyword)
        return

    # 默认
    show_stats(catalog)
    print('用法:')
    print('  python search.py "关键词"         按关键词检索领域')
    print('  python search.py -a "绩效评价"    按审计场景检索')
    print('  python search.py -l             列出全部领域')
    print('  python search.py -s             查看统计')


if __name__ == '__main__':
    main()
