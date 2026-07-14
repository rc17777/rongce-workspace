#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融策知识自动化管道 — 从项目/报告/文章/案例自动提炼知识并同步三库

核心能力：
1. 项目报告复核 → 自动提取发现→分类→入库
2. 扫描文章/案例 → 自动分类→补YAML→同步
3. 网页文章抓取 → 自动下载→分类→入库
4. 技能提炼 → 从重复发现中→自动生成技能文件
5. 三库分发 → 自动同步到 knowledge/ obsidian/ wiki/

使用方式：
  python scripts/kb_pipeline.py                  # 全量运行
  python scripts/kb_pipeline.py --watch          # 持续监控模式
  python scripts/kb_pipeline.py --ingest FILE    # 单文件入库
  python scripts/kb_pipeline.py --report         # 输出管道报告
  python scripts/kb_pipeline.py --status         # 查看管道状态

依赖：
  pip install watchdog  # 文件监控（可选， --watch 模式需要）
"""

import os, sys, json, re, hashlib, yaml
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

try:
    WORKSPACE = Path(os.environ.get('OPENCLAW_WORKSPACE', '')).resolve()
except:
    WORKSPACE = Path(__file__).resolve().parent.parent

# ── 路径配置 ──
KNOWLEDGE = WORKSPACE / 'knowledge'
OBSIDIAN = WORKSPACE / 'obsidian-vault'
WIKI = WORKSPACE / 'AuditKB' / 'wiki'
SKILLS = Path(os.path.expanduser('~/.openclaw/skills'))
OUTPUT = WORKSPACE / 'output'

# 管道状态文件
PIPELINE_STATE = WORKSPACE / 'config' / 'pipeline_state.json'

# 业务线场景映射
SCENE_DIR_MAP = {
    '经济责任审计': '02-主题数据库/经济责任审计',
    '预算执行审计': '02-主题数据库/预算执行审计',
    '专项资金审计': '02-主题数据库/社保资金审计',
    '采购招投标审计': '02-主题数据库/采购招投标审计',
    '绩效评价': '02-主题数据库/绩效评价',
    '工程竣工决算审计': '02-主题数据库/工程竣工决算审计',
    '往来款清理': '02-主题数据库/往来款清理',
    '政府补贴审计': '02-主题数据库/政府补贴审计',
    '能源审计': '02-主题数据库/能源审计',
    '国企专项审计': '02-主题数据库/国企专项审计',
    '专项债审计': '02-主题数据库/专项债审计',
    '营养餐审计': '02-主题数据库/营养餐审计',
    '监督检查': '02-主题数据库/采购招投标审计',
}

# 场景关键词（用于自动分类）
SCENE_KEYWORDS = {
    '经济责任审计': ['经责', '经济责任', '离任', '任中', '领导干部'],
    '预算执行审计': ['预算', '预算执行', '部门预算', '财政预算'],
    '专项资金审计': ['专项', '专项资金', '社保', '医保', '营养餐', '补贴'],
    '采购招投标审计': ['采购', '招标', '投标', '围标', '串标', '政府采购', 'IP地址', 'MAC', '报价'],
    '绩效评价': ['绩效', '绩效评价', '绩效目标', '绩效监控'],
    '工程竣工决算审计': ['工程', '竣工', '决算', '基建', '项目', '造价'],
    '往来款清理': ['往来', '应收', '应付', '预收', '预付'],
    '政府补贴审计': ['补贴', '补助', '专项资金'],
    '能源审计': ['能源', '能耗', '碳中和', '节能'],
    '国企专项审计': ['国企', '国有', '国资委', '国有企业'],
    '专项债审计': ['专项债', '专项债券', '地方债'],
    '监督检查': ['监督', '检查', '财政监督', '专项整治'],
}

# ── 工具函数 ──

def log(msg, level='INFO'):
    print(f'[{level}] {msg}')

def load_state():
    """加载管道状态"""
    if PIPELINE_STATE.exists():
        return json.loads(PIPELINE_STATE.read_text(encoding='utf-8'))
    return {'processed_files': {}, 'last_run': None, 'skills_extracted': []}

def save_state(state):
    """保存管道状态"""
    state['last_run'] = datetime.now().isoformat()
    PIPELINE_STATE.parent.mkdir(parents=True, exist_ok=True)
    PIPELINE_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

def classify_content(text, title=''):
    """自动分类内容到场景"""
    combined = title + ' ' + text[:2000]
    scores = {}
    for scene, keywords in SCENE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            count = combined.count(kw)
            score += count * 2 if kw in title else count
        if score > 0:
            scores[scene] = score
    
    if scores:
        return max(scores, key=scores.get)
    return None

def extract_findings_from_report(text):
    """从报告文本中提取审计发现"""
    findings = []
    
    # 常见发现标记
    patterns = [
        (r'(?:发现|问题|存在|违规)[：:]\s*([^。\n]+)', '问题'),
        (r'(?:建议|整改)[：:]\s*([^。\n]+)', '建议'),
        (r'(?:金额|涉及)[：:]\s*([^。\n]+)', '金额'),
        (r'(?:依据|法规|违反)[：:]\s*([^。\n]+)', '法规'),
    ]
    
    for pattern, ftype in patterns:
        for m in re.finditer(pattern, text):
            finding = m.group(1).strip()
            if len(finding) > 10:  # 过滤太短的
                findings.append({
                    'type': ftype,
                    'text': finding,
                    'source': '报告提取',
                })
    
    return findings

# ── 1. 报告复核自动提取 ──

def process_report(filepath, dry_run=False):
    """处理审计报告/复核文件，提取发现并入库"""
    result = {'findings': [], 'scene': None, 'keywords': [], 'errors': []}
    
    try:
        text = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        title = Path(filepath).stem
        
        # 1. 自动分类
        result['scene'] = classify_content(text, title)
        
        # 2. 提取审计发现
        findings = extract_findings_from_report(text)
        result['findings'] = findings
        
        # 3. 提取关键词（简单高频词）
        words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        word_freq = defaultdict(int)
        for w in words:
            word_freq[w] += 1
        result['keywords'] = [w for w, c in sorted(word_freq.items(), key=lambda x: -x[1])[:20]]
        
        # 4. 如果发现>3条，自动生成知识条目
        if len(findings) >= 3 and result['scene']:
            kb_entry = generate_kb_entry(title, result['scene'], findings, text)
            if not dry_run and kb_entry:
                save_kb_entry(kb_entry)
                result['kb_saved'] = True
        
    except Exception as e:
        result['errors'].append(str(e))
    
    return result

def generate_kb_entry(title, scene, findings, full_text):
    """从报告发现生成知识条目"""
    entry = {
        'title': f'{title} - 审计发现摘要',
        'scene': scene,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'findings_count': len(findings),
        'findings': findings[:10],
        'source': f'项目报告: {title}',
        'tags': ['审计发现', '项目提炼', scene],
    }
    return entry

def save_kb_entry(entry):
    """保存知识条目到 knowledge/ 和 obsidian/"""
    # 生成标准化文件名
    safe_title = re.sub(r'[^\w\u4e00-\u9fff-]', '_', entry['title'])[:60]
    
    # 转成Markdown
    md = f'---\n'
    md += f'title: {entry["title"]}\n'
    md += f'scene: {entry["scene"]}\n'
    md += f'date: {entry["date"]}\n'
    md += f'source: {entry["source"]}\n'
    md += 'tags:\n'
    for t in entry.get('tags', []):
        md += f'  - {t}\n'
    md += '---\n\n'
    md += f'# {entry["title"]}\n\n'
    md += f'> 来源: {entry["source"]} | 日期: {entry["date"]}\n\n'
    md += f'## 审计发现（{entry["findings_count"]}条）\n\n'
    for i, f in enumerate(entry['findings'], 1):
        md += f'{i}. **[{f["type"]}]** {f["text"]}\n'
    
    # 保存到 knowledge/articles/ 和 obsidian-vault/
    for base_dir, sub in [(KNOWLEDGE, 'articles'), (OBSIDIAN, SCENE_DIR_MAP.get(entry['scene'], ''))]:
        if sub:
            target_dir = base_dir / sub
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f'{safe_title}.md'
            target.write_text(md, encoding='utf-8')
            log(f'  已保存: {target}')
    
    return True

# ── 2. 文章/案例自动入库 ──

def process_article(filepath, dry_run=False):
    """处理文章/案例文件，自动分类并入库"""
    result = {'scene': None, 'synced': False, 'errors': []}
    
    try:
        text = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        title = Path(filepath).stem
        
        # 1. 自动分类
        scene = classify_content(text, title)
        result['scene'] = scene
        
        # 2. 补YAML frontmatter（如果没有）
        if not text.startswith('---'):
            yaml_header = '---\n'
            yaml_header += f'title: {title}\n'
            if scene:
                yaml_header += f'scene: {scene}\n'
            yaml_header += f'date: {datetime.now().strftime("%Y-%m-%d")}\n'
            yaml_header += '---\n\n'
            
            if not dry_run:
                Path(filepath).write_text(yaml_header + text, encoding='utf-8')
                result['yaml_added'] = True
        
        # 3. 同步到obsidian
        if scene and scene in SCENE_DIR_MAP:
            target_dir = OBSIDIAN / SCENE_DIR_MAP[scene]
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / Path(filepath).name
            if not target.exists() or not dry_run:
                if not dry_run:
                    content = text if text.startswith('---') else yaml_header + text
                    target.write_text(content, encoding='utf-8')
                    result['synced'] = True
                    log(f'  已同步到obsidian: {target}')
        
    except Exception as e:
        result['errors'].append(str(e))
    
    return result

# ── 3. 技能提炼引擎 ──

def extract_skills_from_findings(all_findings, dry_run=False):
    """从跨项目审计发现中提炼可复用技能"""
    skills = []
    
    # 1. 按类型统计
    type_counts = defaultdict(int)
    type_texts = defaultdict(list)
    for f in all_findings:
        type_counts[f['type']] += 1
        if len(type_texts[f['type']]) < 10:
            type_texts[f['type']].append(f['text'])
    
    # 2. 发现重复模式（同一问题在不同项目中出现≥3次=可提炼为技能）
    pattern_groups = defaultdict(list)
    for f in all_findings:
        # 简化文本为关键词集合
        key = ''.join(sorted(set(re.findall(r'[\u4e00-\u9fff]{2,3}', f['text']))))
        if key:
            pattern_groups[key].append(f)
    
    # 3. 生成技能建议
    for key, group in pattern_groups.items():
        if len(group) >= 3:  # 同一问题出现3次以上
            # 这是一个可复用的检测模式
            skill_suggestion = {
                'pattern': group[0]['text'][:50],
                'frequency': len(group),
                'sources': list(set(f.get('source', '') for f in group)),
                'type': group[0]['type'],
                'suggested_skill': f'自动检测: {group[0]["text"][:30]}',
            }
            skills.append(skill_suggestion)
    
    return skills

def generate_skill_file(skill_suggestion, dry_run=False):
    """从技能建议生成SKILL.md文件"""
    if dry_run:
        return
    
    # 生成技能名
    skill_name = re.sub(r'[^\w\u4e00-\u9fff]', '-', skill_suggestion['suggested_skill'])[:30]
    skill_dir = SKILLS / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    skill_md = f'---\n'
    skill_md += f'name: {skill_name}\n'
    skill_md += f'description: "自动从项目发现中提炼 — {skill_suggestion["pattern"]}"\n'
    skill_md += f'triggers: ["{skill_suggestion["type"]}", "审计发现"]\n'
    skill_md += '---\n\n'
    skill_md += f'# {skill_name}\n\n'
    skill_md += f'> 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
    skill_md += f'> 来源: {len(skill_suggestion["sources"])} 个项目\n\n'
    skill_md += f'## 检测模式\n\n'
    skill_md += f'{skill_suggestion["pattern"]}\n\n'
    skill_md += f'## 出现频率\n\n'
    skill_md += f'在 {skill_suggestion["frequency"]} 个项目中重复出现\n\n'
    skill_md += f'## 来源项目\n\n'
    for s in skill_suggestion['sources']:
        skill_md += f'- {s}\n'
    
    (skill_dir / 'SKILL.md').write_text(skill_md, encoding='utf-8')
    log(f'  技能已生成: {skill_dir / "SKILL.md"}')

# ── 4. 管道编排器 ──

def run_pipeline(dry_run=False, watch=False):
    """运行完整管道"""
    state = load_state()
    log('=' * 50)
    log('融策知识自动化管道 — 启动')
    log('=' * 50)
    
    pipeline_results = {
        'reports_processed': 0,
        'articles_ingested': 0,
        'skills_extracted': 0,
        'kb_entries_created': 0,
        'errors': [],
    }
    
    # ── Step 1: 处理报告/复核文件 ──
    log('\n[Step 1/4] 处理报告/复核文件...')
    report_dirs = [
        WORKSPACE / 'projects',
        WORKSPACE / 'output' / 'report_reviews',
    ]
    for rd in report_dirs:
        if rd.exists():
            for fpath in rd.rglob('*.md'):
                if fpath.name in state.get('processed_files', {}):
                    continue
                log(f'  处理报告: {fpath.name}')
                result = process_report(str(fpath), dry_run)
                if result['findings']:
                    pipeline_results['reports_processed'] += 1
                    pipeline_results['kb_entries_created'] += 1 if result.get('kb_saved') else 0
                    # 记录状态
                    state.setdefault('processed_files', {})[fpath.name] = {
                        'processed_at': datetime.now().isoformat(),
                        'findings': len(result['findings']),
                        'scene': result['scene'],
                    }
    
    # ── Step 2: 处理新文章/案例 ──
    log('\n[Step 2/4] 处理新文章/案例...')
    article_dirs = [
        KNOWLEDGE / 'articles',
        KNOWLEDGE / 'laws/_incoming',
    ]
    for ad in article_dirs:
        if ad.exists():
            for fpath in ad.glob('*.md'):
                if fpath.name in state.get('processed_files', {}):
                    continue
                log(f'  处理文章: {fpath.name}')
                result = process_article(str(fpath), dry_run)
                if result['scene']:
                    pipeline_results['articles_ingested'] += 1
                    state.setdefault('processed_files', {})[fpath.name] = {
                        'processed_at': datetime.now().isoformat(),
                        'scene': result['scene'],
                        'synced': result.get('synced', False),
                    }
    
    # ── Step 3: 技能提炼 ──
    log('\n[Step 3/4] 技能提炼...')
    # 收集所有已处理文件的发现
    all_findings = []
    for fname, info in state.get('processed_files', {}).items():
        if info.get('findings'):
            all_findings.append({
                'type': '问题',
                'text': f'来自项目 {fname}',
                'source': fname,
            })
    
    if all_findings:
        skills = extract_skills_from_findings(all_findings, dry_run)
        for skill in skills[:5]:  # 每次最多生成5个技能
            log(f'  发现可复用模式: {skill["pattern"]} (频率:{skill["frequency"]})')
            generate_skill_file(skill, dry_run)
            pipeline_results['skills_extracted'] += 1
    
    # ── Step 4: 三库同步 ──
    log('\n[Step 4/4] 三库同步...')
    try:
        # 调用 kb_sync.py
        import subprocess
        sync_script = WORKSPACE / 'scripts' / 'kb_sync.py'
        if sync_script.exists() and not dry_run:
            result = subprocess.run(
                [sys.executable, '-X', 'utf8', str(sync_script)],
                capture_output=True, text=True, timeout=60
            )
            log(f'  同步完成: {result.stdout[-200:]}')
    except Exception as e:
        log(f'  同步失败: {e}', 'WARN')
    
    # 保存状态
    save_state(state)
    
    # 输出报告
    log('\n' + '=' * 50)
    log('管道运行报告')
    log('=' * 50)
    log(f'处理报告: {pipeline_results["reports_processed"]} 份')
    log(f'入库文章: {pipeline_results["articles_ingested"]} 篇')
    log(f'提炼技能: {pipeline_results["skills_extracted"]} 个')
    log(f'创建条目: {pipeline_results["kb_entries_created"]} 条')
    log(f'错误: {len(pipeline_results["errors"])} 个')
    if pipeline_results['errors']:
        for e in pipeline_results['errors'][:5]:
            log(f'  • {e}', 'ERROR')
    log(f'状态文件: {PIPELINE_STATE}')
    
    # 保存管道报告
    report_path = OUTPUT / 'pipeline_reports' / f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = []
    report.append('# 知识自动化管道报告\n')
    report.append(f'运行时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
    for k, v in pipeline_results.items():
        if k != 'errors':
            report.append(f'- {k}: {v}')
    report_path.write_text('\n'.join(report), encoding='utf-8')
    log(f'管道报告: {report_path}')
    
    return pipeline_results

# ── 文件监控模式（可选） ──

def start_watcher():
    """启动文件监控（需要 watchdog 库）"""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class KnowledgeHandler(FileSystemEventHandler):
            def on_created(self, event):
                if event.src_path.endswith('.md'):
                    log(f'检测到新文件: {event.src_path}')
                    run_pipeline(dry_run=False)
        
        observer = Observer()
        paths_to_watch = [
            str(KNOWLEDGE / 'articles'),
            str(KNOWLEDGE / 'laws/_incoming'),
            str(WORKSPACE / 'projects'),
        ]
        for p in paths_to_watch:
            if os.path.exists(p):
                observer.schedule(KnowledgeHandler(), p, recursive=False)
                log(f'监控目录: {p}')
        
        log('文件监控已启动 (Ctrl+C 停止)')
        observer.start()
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        
    except ImportError:
        log('watchdog 未安装。请执行: pip install watchdog', 'WARN')
        log('或者直接运行: python scripts/kb_pipeline.py')

# ── 主入口 ──

def main():
    import argparse
    parser = argparse.ArgumentParser(description='融策知识自动化管道')
    parser.add_argument('--watch', action='store_true', help='持续监控模式')
    parser.add_argument('--dry-run', action='store_true', help='试运行')
    parser.add_argument('--ingest', type=str, help='单文件入库')
    parser.add_argument('--report', action='store_true', help='输出管道报告')
    parser.add_argument('--status', action='store_true', help='查看管道状态')
    args = parser.parse_args()
    
    if args.status:
        state = load_state()
        print(f'管道状态:')
        print(f'  最后运行: {state.get("last_run", "从未")}')
        print(f'  已处理文件: {len(state.get("processed_files", {}))} 个')
        print(f'  已提炼技能: {len(state.get("skills_extracted", []))} 个')
        return
    
    if args.report:
        # 显示最近管道报告
        report_dir = OUTPUT / 'pipeline_reports'
        if report_dir.exists():
            reports = sorted(report_dir.glob('*.md'), reverse=True)
            if reports:
                print(reports[0].read_text(encoding='utf-8'))
            else:
                print('暂无管道报告')
        return
    
    if args.ingest:
        # 单文件入库
        fpath = Path(args.ingest)
        if fpath.exists():
            result = process_article(str(fpath))
            print(f'文件: {fpath.name}')
            print(f'分类: {result["scene"]}')
            print(f'同步: {"✅" if result.get("synced") else "❌"}')
        else:
            print(f'文件不存在: {fpath}')
        return
    
    if args.watch:
        start_watcher()
    else:
        run_pipeline(dry_run=args.dry_run)

if __name__ == '__main__':
    main()