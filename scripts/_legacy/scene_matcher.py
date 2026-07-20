#!/usr/bin/env python3
"""场景-案例快速匹配器
用法: python scene_matcher.py "经济责任审计 投标方案"
      python scene_matcher.py "工程变更签证 疑点"
      python scene_matcher.py --list-scenarios
"""
import os, sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

KB = Path(r'D:\openclaw-workspace\knowledge\杂志资料')
INDEX = Path(r'D:\openclaw-workspace\temp\scene_match.json')

def load_index():
    if not INDEX.exists():
        print('请先运行 scene_match_index.py 生成索引')
        sys.exit(1)
    with open(INDEX, 'r', encoding='utf-8') as f:
        return json.load(f)

def search(query, articles, top=10):
    """多关键词加权搜索"""
    qkw = query.lower().split()
    if not qkw:
        return []
    
    scored = []
    for a in articles:
        text = f"{a['title']} {' '.join(a['biz'])} {' '.join(a['scenario'])}".lower()
        score = sum(1 for kw in qkw if kw in text)
        # Title match bonus
        score += sum(2 for kw in qkw if kw in a['title'].lower())
        # Exact phrase match bonus
        score += 3 if query.lower() in text else 0
        
        if score > 0:
            scored.append((score, a))
    
    scored.sort(key=lambda x: -x[0])
    return scored[:top]

def list_scenarios():
    scenarios = {'投标方案编制':[],'项目实施疑点':[],'审计评价思路':[],'报告撰写':[]}
    articles = load_index()
    for a in articles:
        for s in a['scenario']:
            if len(scenarios.get(s, [])) < 5:
                scenarios[s].append(a['title'][:60])
    
    for sc, titles in scenarios.items():
        print(f'\n=== {sc} ===')
        for t in titles[:5]:
            print(f'  📄 {t}')

def main():
    if '--list-scenarios' in sys.argv:
        list_scenarios()
        return
    
    query = ' '.join([a for a in sys.argv[1:] if not a.startswith('--')])
    if not query:
        print('用法: python scene_matcher.py "关键词"')
        print('示例: python scene_matcher.py "经济责任审计 投标方案"')
        print('      python scene_matcher.py "工程变更 疑点"')
        print('      python scene_matcher.py --list-scenarios')
        sys.exit(1)
    
    articles = load_index()
    
    # Also allow scenario shortcuts
    SCENE_MAP = {
        '投标': '投标方案编制', '方案': '投标方案编制', '标书': '投标方案编制',
        '疑点': '项目实施疑点', '问题': '项目实施疑点', '异常': '项目实施疑点',
        '思路': '审计评价思路', '方法': '审计评价思路', '框架': '审计评价思路',
        '报告': '报告撰写', '撰写': '报告撰写', '底稿': '报告撰写',
    }
    for kw, sc in SCENE_MAP.items():
        if kw in query:
            query = f'{query} {sc}'
    
    results = search(query, articles, top=15)
    
    if not results:
        print(f'未找到匹配 "{query}" 的文章')
        return
    
    print(f'\n🔍 "{query}" → {len(results)}篇匹配\n')
    
    for score, a in results:
        star = '⭐' if score >= 5 else ('🔴' if score >= 3 else '  ')
        print(f'{star} [{",".join(a["scenario"][:1])}] {a["title"][:80]}')
        if a['biz']:
            print(f'   业务: {", ".join(a["biz"][:2])}')
        print(f'   路径: {a["path"]}')
        print()

if __name__ == '__main__':
    main()
