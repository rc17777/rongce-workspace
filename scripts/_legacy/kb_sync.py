#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三库同步脚本：knowledge/ → obsidian-vault/ → wiki/
扫描 knowledge/ 的新内容，同步到 obsidian-vault/，并更新 wiki 产品化索引。

使用方式：
  python scripts/kb_sync.py              # 全量同步
  python scripts/kb_sync.py --dry-run    # 试运行，不写入
  python scripts/kb_sync.py --report     # 只输出同步报告
  python scripts/kb_sync.py --wiki-only  # 只更新wiki产品化内容
"""

import os, sys, json, re, hashlib, shutil
from datetime import datetime
from pathlib import Path

# ── 路径配置 ──
try:
    WORKSPACE = Path(os.environ.get('OPENCLAW_WORKSPACE', '')).resolve()
except:
    WORKSPACE = Path(__file__).resolve().parent.parent

KNOWLEDGE = WORKSPACE / 'knowledge'
OBSIDIAN = WORKSPACE / 'obsidian-vault'
WIKI = WORKSPACE / 'AuditKB' / 'wiki'
RONGCE_HUB = WORKSPACE / 'RONGCE_AI_HUB'

# 场景→Obsidian目录映射
SCENE_DIR_MAP = {
    '采购招投标审计': '02-主题数据库/采购招投标审计',
    '专项债审计': '02-主题数据库/专项债审计',
    '国企专项审计': '02-主题数据库/国企专项审计',
    '工程竣工决算审计': '02-主题数据库/工程竣工决算审计',
    '往来款清理': '02-主题数据库/往来款清理',
    '政府补贴审计': '02-主题数据库/政府补贴审计',
    '社保资金审计': '02-主题数据库/社保资金审计',
    '经济责任审计': '02-主题数据库/经济责任审计',
    '绩效评价': '02-主题数据库/绩效评价',
    '能源审计': '02-主题数据库/能源审计',
    '营养餐审计': '02-主题数据库/营养餐审计',
    '预算执行审计': '02-主题数据库/预算执行审计',
}

# 知识目录→Obsidian分类映射
KNOWLEDGE_DIR_MAP = {
    'articles': '02-主题数据库',
    'laws': '04-法规案例库',
    'policies': '04-法规案例库',
    'references': '04-法规案例库',
}

# ── 工具函数 ──

def log(msg, level='INFO'):
    print(f'[{level}] {msg}')

def md5_file(path):
    """计算文件MD5"""
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def extract_scene_tags(content):
    """从文件中提取 scene 标签"""
    m = re.search(r'scene:\s*(\S+)', content)
    if m:
        return m.group(1)
    # 尝试从内容中匹配
    for scene in SCENE_DIR_MAP:
        if scene in content:
            return scene
    return None

def extract_title(content):
    """从文件中提取标题"""
    # YAML title
    m = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    # Markdown H1
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return None

def extract_tags(content):
    """从YAML frontmatter提取tags"""
    m = re.search(r'tags:\n((?:\s+-\s+\S+\n)+)', content)
    if m:
        tags = re.findall(r'-\s+(\S+)', m.group(1))
        return tags
    return []

def has_yaml_frontmatter(content):
    """检查是否有YAML frontmatter"""
    return content.startswith('---')

def generate_yaml_frontmatter(title, scene, tags=None, source='', date=''):
    """生成YAML frontmatter"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    yaml = f'---\ntitle: {title}\nsource: {source}\ndate: {date}\n'
    if scene:
        yaml += f'scene: {scene}\n'
    if tags:
        yaml += 'tags:\n'
        for t in tags:
            yaml += f'  - {t}\n'
    yaml += '---\n\n'
    return yaml

# ── 同步功能 ──

def sync_knowledge_to_obsidian(dry_run=False):
    """同步 knowledge/ → obsidian-vault/"""
    results = {'created': [], 'updated': [], 'skipped': [], 'errors': []}
    
    # 扫描 knowledge/articles/
    articles_dir = KNOWLEDGE / 'articles'
    if not articles_dir.exists():
        log(f'articles目录不存在: {articles_dir}', 'WARN')
        return results
    
    for fpath in sorted(articles_dir.glob('*.md')):
        try:
            content = fpath.read_text(encoding='utf-8')
            scene = extract_scene_tags(content)
            title = extract_title(content) or fpath.stem
            tags = extract_tags(content)
            
            # 确定目标目录
            if scene and scene in SCENE_DIR_MAP:
                target_dir = OBSIDIAN / SCENE_DIR_MAP[scene]
            else:
                # 无scene标签，放到根目录
                target_dir = OBSIDIAN
            
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / fpath.name
            
            # 检查是否需要同步
            if target_path.exists():
                existing = target_path.read_text(encoding='utf-8')
                if has_yaml_frontmatter(existing) and md5_file(fpath) == md5_file(target_path):
                    results['skipped'].append(fpath.name)
                    continue
            
            # 生成目标内容
            if has_yaml_frontmatter(content):
                target_content = content
            else:
                target_content = generate_yaml_frontmatter(title, scene, tags) + content
            
            if not dry_run:
                target_path.write_text(target_content, encoding='utf-8')
                results['created' if not target_path.exists() else 'updated'].append(fpath.name)
            else:
                results['created' if not target_path.exists() else 'updated'].append(f'{fpath.name} (dry-run)')
            
        except Exception as e:
            results['errors'].append(f'{fpath.name}: {str(e)}')
    
    return results

def sync_knowledge_to_wiki(dry_run=False):
    """从 knowledge/ 提取产品化内容到 wiki/"""
    results = {'created': [], 'updated': [], 'skipped': [], 'errors': []}
    
    # 确保目标目录存在
    for sub in ['procurement', 'regulations', 'cases', 'tools']:
        (WIKI / sub).mkdir(parents=True, exist_ok=True)
    
    # 1. 同步 procurement-audit 相关文章
    procurement_dir = KNOWLEDGE / 'procurement-audit'
    if procurement_dir.exists():
        for fpath in procurement_dir.glob('*.md'):
            target = WIKI / 'procurement' / fpath.name
            if not target.exists():
                content = fpath.read_text(encoding='utf-8')
                if not dry_run:
                    target.write_text(content, encoding='utf-8')
                    results['created'].append(f'procurement/{fpath.name}')
                else:
                    results['created'].append(f'procurement/{fpath.name} (dry-run)')
    
    # 2. 同步 laws
    laws_dir = KNOWLEDGE / 'laws'
    if laws_dir.exists():
        for fpath in laws_dir.glob('*.md'):
            target = WIKI / 'regulations' / fpath.name
            if not target.exists():
                content = fpath.read_text(encoding='utf-8')
                if not dry_run:
                    # 精简版本：只保留标题和核心条款
                    lines = content.split('\n')
                    simplified = []
                    for line in lines:
                        if line.startswith('#') or line.startswith('>') or line.startswith('|') or '条' in line or '款' in line:
                            simplified.append(line)
                    if simplified:
                        target.write_text('\n'.join(simplified), encoding='utf-8')
                        results['created'].append(f'regulations/{fpath.name}')
    
    return results

def update_wiki_index(dry_run=False):
    """更新wiki索引文件"""
    results = {'indexes_updated': []}
    
    # 生成 procurement 索引
    procurement_index = '# 采购审计产品化知识\n\n'
    procurement_index += f'> 最后更新：{datetime.now().strftime("%Y-%m-%d %H:%M")}\n> 来源：knowledge/ 产品化提炼\n\n'
    procurement_index += '| 文件 | 类型 | 说明 |\n|------|------|------|\n'
    
    procurement_dir = WIKI / 'procurement'
    if procurement_dir.exists():
        for fpath in sorted(procurement_dir.glob('*.md')):
            content = fpath.read_text(encoding='utf-8', errors='ignore')
            first_line = content.split('\n')[0] if content else ''
            desc = extract_title(content) or fpath.stem
            procurement_index += f'| [{fpath.name}](procurement/{fpath.name}) | 知识 | {desc} |\n'
    
    if not dry_run:
        (WIKI / 'procurement' / 'index.md').write_text(procurement_index, encoding='utf-8')
        results['indexes_updated'].append('wiki/procurement/index.md')
    
    # 生成 regulations 索引
    reg_index = '# 法规案例产品化知识\n\n'
    reg_index += f'> 最后更新：{datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n'
    reg_index += '| 文件 | 类型 | 说明 |\n|------|------|------|\n'
    
    reg_dir = WIKI / 'regulations'
    if reg_dir.exists():
        for fpath in sorted(reg_dir.glob('*.md')):
            desc = fpath.stem.replace('-', ' ').replace('_', ' ')
            reg_index += f'| [{fpath.name}](regulations/{fpath.name}) | 法规 | {desc} |\n'
    
    if not dry_run:
        (WIKI / 'regulations' / 'index.md').write_text(reg_index, encoding='utf-8')
        results['indexes_updated'].append('wiki/regulations/index.md')
    
    # 生成 wiki 总索引
    total_index = '# 融策产品化知识库\n\n'
    total_index += f'> 最后更新：{datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n'
    total_index += '## 目录\n\n'
    total_index += '- [采购审计](procurement/index.md) — 围标串标检测、采购文件合规审查\n'
    total_index += '- [法规案例](regulations/index.md) — 审计法规、处罚案例\n'
    total_index += '- [工具](tools/index.md) — 审计工具与模板\n\n'
    total_index += '## 同步说明\n\n'
    total_index += '此目录由 `scripts/kb_sync.py` 自动从 `knowledge/` 和 `obsidian-vault/` 同步生成。\n'
    total_index += '来源标注：\n'
    total_index += '- **knowledge/**: 原材料入库（原文收录）\n'
    total_index += '- **obsidian-vault/**: 主题化分类（YAML + 场景导航）\n'
    total_index += '- **AuditKB/wiki/**: 产品化提炼（可直接复用）\n'
    
    if not dry_run:
        (WIKI / 'index.md').write_text(total_index, encoding='utf-8')
        results['indexes_updated'].append('wiki/index.md')
    
    return results

def generate_sync_report(results):
    """生成同步报告"""
    report = []
    report.append('=' * 50)
    report.append(f'三库同步报告 - {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    report.append('=' * 50)
    
    total = 0
    for key in ['created', 'updated', 'skipped', 'errors']:
        items = results.get(key, [])
        if items:
            report.append(f'\n[{key.upper()}] {len(items)} 项:')
            for item in items[:20]:
                report.append(f'  • {item}')
            if len(items) > 20:
                report.append(f'  ... 还有 {len(items)-20} 项')
            total += len(items)
    
    report.append(f'\n总计: {total} 项操作')
    return '\n'.join(report)

# ── 主流程 ──

def main():
    import argparse
    parser = argparse.ArgumentParser(description='三库同步脚本')
    parser.add_argument('--dry-run', action='store_true', help='试运行，不写入文件')
    parser.add_argument('--report', action='store_true', help='只输出同步报告（不写文件）')
    parser.add_argument('--wiki-only', action='store_true', help='只更新wiki产品化内容')
    args = parser.parse_args()
    
    dry_run = args.dry_run or args.report
    all_results = {}
    
    if not args.wiki_only:
        log('=== 同步 knowledge/ → obsidian-vault/ ===')
        results1 = sync_knowledge_to_obsidian(dry_run)
        all_results['knowledge→obsidian'] = results1
        log(f'创建: {len(results1["created"])}, 更新: {len(results1["updated"])}, 跳过: {len(results1["skipped"])}, 错误: {len(results1["errors"])}')
    
    log('\n=== 同步到 wiki/ ===')
    results2 = sync_knowledge_to_wiki(dry_run)
    all_results['knowledge→wiki'] = results2
    log(f'创建: {len(results2["created"])}, 更新: {len(results2["updated"])}, 跳过: {len(results2["skipped"])}, 错误: {len(results2["errors"])}')
    
    log('\n=== 更新wiki索引 ===')
    results3 = update_wiki_index(dry_run)
    all_results['wiki索引'] = results3
    log(f'更新索引: {len(results3["indexes_updated"])}')
    
    # 汇总报告
    report = []
    report.append('=' * 60)
    report.append(f'三库同步报告 - {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    report.append('=' * 60)
    for scope, results in all_results.items():
        report.append(f'\n[{scope}]')
        for action, items in results.items():
            if items:
                report.append(f'  {action}: {len(items)} 项')
                for item in items[:5]:
                    report.append(f'    • {item}')
                if len(items) > 5:
                    report.append(f'    ... 还有 {len(items)-5} 项')
    
    report_path = KNOWLEDGE / 'sync_report_last.json'
    if not dry_run:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': {k: {kk: len(vv) for kk, vv in v.items()} for k, v in all_results.items()}
            }, f, ensure_ascii=False, indent=2)
    
    print('\n' + '\n'.join(report))
    
    if dry_run and args.report:
        # 保存报告到文件
        report_file = WORKSPACE / 'output' / 'sync_reports' / f'sync_report_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text('\n'.join(report), encoding='utf-8')
        log(f'报告已保存: {report_file}')

if __name__ == '__main__':
    main()