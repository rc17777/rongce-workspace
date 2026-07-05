#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计资料清单查询工具
用法:
  python query_catalog.py "场景名称"           # 按场景筛选
  python query_catalog.py "关键词" --by-name   # 按文件名搜索
  python query_catalog.py "关键词" --by-scene  # 场景关键词匹配
  python query_catalog.py --stats              # 显示统计
  python query_catalog.py --scenes             # 列出所有场景
"""
import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')

VAULT = r'C:\Users\scrccpa\Documents\Obsidian Vault'
JSON_PATH = os.path.join(VAULT, '审计资料清单.json')

def load_index():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def rebuild_index():
    """重新生成JSON索引"""
    index = []
    for root, dirs, files in os.walk(VAULT):
        if '.obsidian' in root or 'node_modules' in root or '.venv' in root:
            continue
        for f in files:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(root, VAULT)
            if not rel.startswith(('审计案例库', '杂志资料', '审计案例库-OCR')):
                continue
            if '按类型' in rel:
                continue
            
            with open(fp, 'r', encoding='utf-8', errors='replace') as ff:
                content = ff.read(2000)
            
            if not content.startswith('---'):
                continue
            end = content.find('---', 3)
            if end < 0:
                continue
            head = content[3:end]
            
            scene = ''
            title = ''
            m = re.search(r'scene:\s*["\']?([^"\'\n]+)', head)
            if m: scene = m.group(1).strip()
            m = re.search(r'title:\s*["\']?([^"\'\n]+)', head)
            if m: title = m.group(1).strip()
            
            rel_path = os.path.relpath(fp, VAULT)
            index.append({
                'path': rel_path,
                'filename': f,
                'scene': scene or '(未分类)',
                'title': title or f,
            })
    
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return index

def show_stats(index):
    by_scene = {}
    for item in index:
        s = item['scene']
        by_scene[s] = by_scene.get(s, 0) + 1
    print(f'\n{"="*50}')
    print(f'审计资料清单统计（共{len(index)}篇）')
    print(f'{"="*50}')
    for s, c in sorted(by_scene.items(), key=lambda x: -x[1]):
        print(f'  {s}: {c}篇')
    print(f'{"="*50}')

def query_scene(index, scene):
    results = [i for i in index if scene in i['scene']]
    if not results:
        # 模糊匹配
        results = [i for i in index if scene.lower() in i['scene'].lower()]
    if not results:
        print(f'未找到场景包含"{scene}"的文章')
        return
    print(f'\n场景包含"{scene}"的文章（共{len(results)}篇）:')
    print('-' * 60)
    for r in results:
        print(f'  [{r["scene"]}] {r["path"]}')

def query_by_name(index, keyword):
    results = [i for i in index if keyword in i['filename'].replace('.md', '') or keyword in i['title']]
    print(f'\n文件名/标题包含"{keyword}"的文章（共{len(results)}篇）:')
    print('-' * 60)
    for r in results:
        print(f'  [{r["scene"]}] {r["path"]}')

def list_scenes(index):
    scenes = sorted(set(i['scene'] for i in index))
    print('\n可用场景列表:')
    for s in scenes:
        cnt = sum(1 for i in index if i['scene'] == s)
        print(f'  {s} ({cnt}篇)')

if __name__ == '__main__':
    args = sys.argv[1:]
    
    # 重建索引
    if '--rebuild' in args:
        print('正在重建索引...')
        index = rebuild_index()
        print(f'完成，共{len(index)}条')
        args.remove('--rebuild')
    
    index = load_index()
    if not index:
        print('正在重建索引...')
        index = rebuild_index()
    
    if not args or '--stats' in args:
        show_stats(index)
    elif '--scenes' in args:
        list_scenes(index)
    elif '--by-name' in args:
        idx = args.index('--by-name')
        keyword = args[idx - 1] if idx > 0 else args[0]
        query_by_name(index, keyword)
    elif '--by-scene' in args:
        idx = args.index('--by-scene')
        keyword = args[idx - 1] if idx > 0 else args[0]
        query_scene(index, keyword)
    else:
        # 默认按场景搜索
        query_scene(index, args[0])
