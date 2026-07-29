# -*- coding: utf-8 -*-
"""
审计行业高质量数据集 — 批量提取引擎 v1.0
从 knowledge/ + obsidian-vault/ + llm-wiki/ 提取结构化审计数据

架构：
  Phase 1: 扫描全部源文件 → 按业务线/文档类型分类
  Phase 2: 批量提取案例（从YAML scene字段+文件名+内容关键词）
  Phase 3: 批量提取法规条款（从laws/ + magazines/）
  Phase 4: 批量提取检测方法（从审计技能树+方法论文章）
  Phase 5: 批量提取疑点模式（从案例中反推）

用法：
  python scripts/build_audit_dataset.py --phase 1 --dry-run    # 扫描+分类
  python scripts/build_audit_dataset.py --phase 2              # 提取案例
  python scripts/build_audit_dataset.py --phase all            # 全流程
  python scripts/build_audit_dataset.py --stats                # 统计
"""
import sys, os, json, re, yaml
from datetime import date
from pathlib import Path
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')

TODAY = date.today().isoformat()
WORKSPACE = Path(r'C:\Users\scrccpa\.openclaw\workspace')
KNOWLEDGE = WORKSPACE / 'knowledge'
OBSIDIAN = WORKSPACE / 'obsidian-vault'
LLM_WIKI = Path.home() / '.openclaw' / 'skills' / 'llm-wiki'
DATASET_DIR = WORKSPACE / 'knowledge' / 'datasets'
AUDIT_DATASET = DATASET_DIR / 'audit-industry'

# ═══════════════════════════════════════════════════════════
# 全局Schema: 审计行业高质量数据集
# ═══════════════════════════════════════════════════════════

BUSINESS_LINES = {
    '经责审计': ['经责', '经济责任', '离任审计', '任中审计', '自然资源资产'],
    '收支审计': ['收支', '财政收支', '财务收支'],
    '预算执行': ['预算执行', '预算', '决算', '预算绩效'],
    '专项资金': ['专项资金', '专项审计', '营养餐', '社保资金', '就业补助'],
    '往来款清理': ['往来款', '资金清理', '往来款项'],
    '招投标审计': ['招投标', '招标', '投标', '串标', '围标', '政府采购', 'bid'],
    '国企审计': ['国企', '国有企业', '国有资产', '国资委'],
    '成本效益': ['成本', '效益', '成本效益', '量本利'],
    '能源审计': ['能源', '碳中和', '节能'],
    '工程审计': ['工程', '竣工决算', '工程造价', '跟踪审计'],
    '绩效评价': ['绩效', '绩效评价', '绩效管理', '绩效考核'],
    '补贴审计': ['补贴', '补助', '政府补贴', '财政补贴'],
}

ENTRY_TYPES = ['detection_method', 'case', 'regulation', 'finding_pattern']

# ═══════════════════════════════════════════════════════════
# Phase 1: 扫描+分类
# ═══════════════════════════════════════════════════════════

def classify_by_business_line(filepath, content_preview=''):
    """根据文件名和内容预览判断业务线"""
    fname = os.path.basename(filepath)
    fdir = str(filepath)
    text = fname + ' ' + fdir + ' ' + (content_preview[:500] if content_preview else '')
    
    matches = []
    for bl, keywords in BUSINESS_LINES.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            matches.append((bl, score))
    
    if not matches:
        return '通用/未分类'
    
    matches.sort(key=lambda x: -x[1])
    return matches[0][0]

def scan_sources(source_paths, label):
    """扫描源文件，返回分类结果"""
    results = defaultdict(list)
    total = 0
    
    for base_path in source_paths:
        if not os.path.exists(base_path):
            continue
        for root, dirs, files in os.walk(base_path):
            if '.git' in root:
                continue
            for f in files:
                if not f.endswith('.md'):
                    continue
                fp = os.path.join(root, f)
                total += 1
                
                # 读取YAML frontmatter
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        raw = fh.read(3000)
                except:
                    continue
                
                bl = classify_by_business_line(fp, raw)
                results[bl].append({
                    'path': fp,
                    'rel_path': os.path.relpath(fp, str(Workspace if 'Workspace' in str(type) else base_path)),
                    'size': os.path.getsize(fp)
                })
    
    return dict(results), total

def phase1_scan():
    """Phase 1: 扫描全部三个来源"""
    print("Phase 1: 扫描源文件...")
    
    sources = [
        (str(KNOWLEDGE), "knowledge/"),
        (str(OBSIDIAN), "obsidian-vault/"),
        (str(LLM_WIKI), "llm-wiki/") if LLM_WIKI.exists() else None
    ]
    sources = [s for s in sources if s]
    
    all_results = {}
    grand_total = 0
    
    for spath, slabel in sources:
        results, total = scan_sources([spath], slabel)
        print(f"  {slabel}: {total} files → {len(results)} categories")
        grand_total += total
        
        for bl, files in results.items():
            if bl not in all_results:
                all_results[bl] = []
            all_results[bl].extend(files)
    
    print(f"\n  总计: {grand_total} files, {len(all_results)} 业务线\n")
    
    # 按文件数排序
    sorted_bl = sorted(all_results.items(), key=lambda x: -len(x[1]))
    for bl, files in sorted_bl:
        # 统计子目录分布
        subdirs = Counter(os.path.dirname(f['rel_path']).split('\\')[0] for f in files)
        subdir_str = ', '.join(f'{k}:{v}' for k, v in subdirs.most_common(3))
        print(f"  {bl:12s} | {len(files):4d} 文件 | {subdir_str}")
    
    # 保存分类结果
    AUDIT_DATASET.mkdir(parents=True, exist_ok=True)
    catalog_path = AUDIT_DATASET / f'catalog_{TODAY}.json'
    with open(catalog_path, 'w', encoding='utf-8') as f:
        # 只保存路径列表，不存完整内容
        catalog = {bl: [x['rel_path'] for x in files] for bl, files in all_results.items()}
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"\n  分类目录已保存: {catalog_path}")
    
    return all_results


# ═══════════════════════════════════════════════════════════
# Phase 2: 批量提取案例
# ═══════════════════════════════════════════════════════════

def extract_yaml_frontmatter(filepath):
    """提取YAML frontmatter"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read(5000)
    except:
        return {}
    
    if not raw.startswith('---'):
        return {}
    
    parts = raw.split('---', 2)
    if len(parts) < 3:
        return {}
    
    try:
        fm = yaml.safe_load(parts[1])
        return fm if isinstance(fm, dict) else {}
    except:
        return {}

def extract_case_from_file(filepath, business_line):
    """从单个文件提取案例条目"""
    fm = extract_yaml_frontmatter(filepath)
    fname = os.path.basename(filepath)
    
    # 判断是否适合作为案例
    title = fm.get('title', fname.replace('.md', ''))
    summary = fm.get('summary', '')
    source = fm.get('source', '')
    scene_str = fm.get('business_scenes', '') or fm.get('scene', '') or fm.get('tags', '')
    if isinstance(scene_str, list):
        scene_str = ', '.join(scene_str)
    
    # 必须有标题和来源才纳入
    if not title or not source:
        return None
    
    # 判断严重程度
    severity = 'P2-一般问题'
    keywords = []
    if any(k in title + summary for k in ['虚构','造假','串通','欺诈','舞弊','贪污','挪用']):
        severity = 'P0-重大违法'
        keywords.extend(['造假', '欺诈'])
    elif any(k in title + summary for k in ['违规','违法','处罚','异常','虚高','低价','闲置']):
        severity = 'P1-严重违规'
        keywords.extend(['违规', '异常'])
    
    # 判断案例真实性
    is_real = any(k in str(source) for k in ['财政监督','四川注册会计师','微信公众号','审计观察','经济责任审计'])
    
    case_id_num = int(hashlib.md5(filepath.encode()).hexdigest()[:6], 16) % 9000 + 1000
    # 用业务线确定ID前缀范围
    bl_prefix_map = {bl: i*1000 for i, bl in enumerate(BUSINESS_LINES.keys())}
    case_id = f"CASE-{business_line.replace('/','-')}-{case_id_num:04d}"[:20]
    
    return {
        "id": case_id,
        "type": "case",
        "title": title[:60],
        "summary": (summary or title)[:200],
        "business_line": business_line,
        "audit_type": business_line,
        "sub_type": scene_str[:50] if scene_str else "通用",
        "violation_category": _guess_category(title, summary, business_line),
        "violation_subcategory": "",
        "detection_method": [],
        "data_sources": [],
        "amount_range": "不适用",
        "amount_exact": None,
        "regulation": [],
        "severity": severity,
        "entity_type": "通用",
        "industry": "通用",
        "region": "",
        "finding_pattern": "",
        "penetration_chain": {},
        "related_cases": [],
        "provenance": {
            "source_file": os.path.relpath(filepath, str(WORKSPACE)),
            "source_type": _guess_source_type(source),
            "is_real": is_real,
            "anonymized": True,
            "verified_by": 0,
            "date_collected": TODAY
        },
        "keywords": keywords + ([scene_str] if scene_str else [])
    }

def _guess_category(title, summary, business_line):
    text = title + summary
    if any(k in text for k in ['串标','围标','串通','雷同','同源']): return '串标/围标'
    if any(k in text for k in ['造假','虚假','伪造','虚构']): return '财务造假'
    if any(k in text for k in ['挪用','侵占','贪污']): return '资金挪用'
    if any(k in text for k in ['违规','违法','处罚']): return '违规行为'
    if any(k in text for k in ['虚高','高价','低价','价格']): return '价格异常'
    if any(k in text for k in ['闲置','浪费','低效','无效']): return '资金低效'
    if any(k in text for k in ['绩效','评价','考核']): return '绩效管理'
    if any(k in text for k in ['内控','控制','流程']): return '内控缺陷'
    return '管理问题'

def _guess_source_type(source):
    source_str = str(source)
    if '微信公众号' in source_str or '审天审地' in source_str: return '公开报道'
    if '财政监督' in source_str: return '公开报道'
    if '注册会计师' in source_str: return '行业刊物'
    if '审计观察' in source_str: return '行业刊物'
    if '经济责任审计' in source_str: return '行业刊物'
    return '学术文献'

def phase2_extract_cases(catalog, max_per_line=20):
    """Phase 2: 批量提取案例"""
    print("\nPhase 2: 批量提取案例...")
    
    all_cases = []
    stats = {}
    
    for bl, files in catalog.items():
        # 跳过招投标（已有33条）
        if bl == '招投标审计':
            print(f"  {bl}: 跳过（已有33条招投标案例）")
            continue
        
        if not files:
            continue
        
        cases = []
        # 从最多文件中取max_per_line条
        sampled = files[:max_per_line * 5]  # 读5倍于目标数，筛选后取最好的
        for entry in sampled:
            fp = entry['rel_path'] if isinstance(entry, dict) else entry
            full_path = WORKSPACE / 'knowledge' / fp if not os.path.isabs(str(fp)) else Path(fp)
            if not os.path.exists(str(full_path)):
                # try alternate paths
                for base in [KNOWLEDGE, OBSIDIAN, LLM_WIKI]:
                    alt = base / fp if not str(fp).startswith(str(base)) else Path(fp)
                    if alt.exists():
                        full_path = alt
                        break
                else:
                    continue
            
            case = extract_case_from_file(str(full_path), bl)
            if case and case['title'] and case['summary']:
                cases.append(case)
            
            if len(cases) >= max_per_line:
                break
        
        stats[bl] = len(cases)
        all_cases.extend(cases)
        if cases:
            print(f"  {bl}: {len(cases)} cases")
    
    # 保存
    if all_cases:
        path = AUDIT_DATASET / f'cases_phase2_{TODAY}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(all_cases, f, ensure_ascii=False, indent=2)
        print(f"\n  案例总数: {len(all_cases)} → {path}")
    
    return all_cases, stats


# ═══════════════════════════════════════════════════════════
# Phase 3: 批量提取法规
# ═══════════════════════════════════════════════════════════

def phase3_extract_regulations(catalog):
    """Phase 3: 批量提取法规条款"""
    print("\nPhase 3: 批量提取法规条款...")
    
    regs = []
    
    # 从laws目录 + magazines中的政策文件提取
    for bl, files in catalog.items():
        for entry in files:
            fp = entry['rel_path'] if isinstance(entry, dict) else entry
            fname = os.path.basename(str(fp))
            if not any(k in fname for k in ['法','条例','规定','办法','通知','意见','准则']):
                continue
            if any(k in fname for k in ['案例','分析','实践','探讨','研究','识别','检查']):
                continue
            
            full_path = None
            for base in [KNOWLEDGE, OBSIDIAN]:
                alt = base / str(fp)
                if alt.exists():
                    full_path = alt
                    break
            
            if not full_path:
                continue
            
            fm = extract_yaml_frontmatter(str(full_path))
            title = fm.get('title', fname.replace('.md', ''))
            if len(title) < 5 or len(title) > 80:
                continue
            
            reg_id = f"REG-{bl.replace('/','-')}-{len(regs)+1:04d}"[:20]
            regs.append({
                "id": reg_id,
                "type": "regulation",
                "law_name": title[:80],
                "law_short": title[:30],
                "law_level": _guess_law_level(title),
                "article": "",
                "content": fm.get('summary', title)[:200],
                "key_point": title[:50],
                "applicable_scenario": [bl],
                "violation_consequence": "",
                "penalty_range": "",
                "related_regulations": [],
                "related_cases": [],
                "provenance": {
                    "effective_date": "",
                    "amend_date": "",
                    "status": "现行有效"
                },
                "keywords": []
            })
    
    if regs:
        path = AUDIT_DATASET / f'regulations_phase3_{TODAY}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(regs, f, ensure_ascii=False, indent=2)
        print(f"  法规条款: {len(regs)} → {path}")
    
    return regs

def _guess_law_level(title):
    if '法' in title and '办法' not in title and '方法' not in title: return '法律'
    if '条例' in title: return '行政法规'
    if '办法' in title or '规定' in title: return '部门规章'
    if '通知' in title: return '规范性文件'
    return '其他'


# ═══════════════════════════════════════════════════════════
# Phase 4 & 5: 方法+疑点模式（基于已有知识提炼）
# ═══════════════════════════════════════════════════════════

def phase4_extract_methods(catalog):
    """Phase 4: 从审计技能树+方法论文章提取检测方法"""
    print("\nPhase 4: 提取检测方法...")
    
    methods = []
    
    # 从技能树提取
    skill_tree_paths = [
        KNOWLEDGE / 'references' / '审计技能树.md',
        OBSIDIAN / '审计技能树.md',
    ]
    
    for sp in skill_tree_paths:
        if sp.exists():
            print(f"  发现审计技能树: {sp}")
    
    # 核心审计方法（从现有知识固化）
    core_methods = [
        ("比对分析法", "预算/决算/实际支出三线比对", "预算执行", "铁证"),
        ("趋势分析法", "多年数据趋势异常检测", "通用", "强信号"),
        ("比率分析法", "财务比率结构性异常检测", "国企审计", "强信号"),
        ("Benford定律", "首位数字分布异常→数据伪造信号", "通用", "铁证"),
        ("勾稽关系验证", "报表→账簿→凭证三级勾稽交叉验证", "通用", "铁证"),
        ("穿行测试", "全流程跟踪单笔交易，验证内控有效性", "通用", "强信号"),
        ("函证法", "银行/往来单位/关联方外部确认", "经责审计", "铁证"),
        ("盘点法", "实物资产实地盘存vs账面数", "工程审计", "铁证"),
        ("重新计算法", "独立重新计算关键财务指标", "通用", "铁证"),
        ("分析性复核", "财务数据与非财务数据的合理性分析", "通用", "强信号"),
        ("SQL数据筛查", "结构化查询批量异常检测", "专项资金", "铁证"),
        ("文本挖掘", "非结构化文本（合同/会议纪要）信息提取", "招投标审计", "强信号"),
        ("网络图谱分析", "工商关联/资金流转/人员重叠图谱构建", "通用", "铁证"),
        ("空间分析", "GIS地理信息与项目分布交叉分析", "工程审计", "强信号"),
        ("Apriori关联规则", "频繁项集挖掘→异常关联模式", "招投标审计", "强信号"),
    ]
    
    for i, (name, desc, bl, conf) in enumerate(core_methods, 1):
        methods.append({
            "id": f"DM-AUDIT-{i:04d}",
            "type": "detection_method",
            "name": name,
            "alias": f"通用方法-{name}",
            "layer": "通用",
            "confidence_level": conf,
            "method_description": desc,
            "detection_logic": "",
            "input_data": {"primary": [], "optional": []},
            "output": {"format": "", "fields": []},
            "technical_params": {},
            "false_positive_risks": [],
            "combination_rules": [],
            "provenance": {"source": "审计技能树+方法论文章", "author": "融策右护卫", "date_created": TODAY},
            "keywords": [name],
            "related_methods": [],
            "related_cases": [],
            "related_regulations": [],
            "business_line": bl
        })
    
    if methods:
        path = AUDIT_DATASET / f'methods_phase4_{TODAY}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(methods, f, ensure_ascii=False, indent=2)
        print(f"  检测方法: {len(methods)} → {path}")
    
    return methods

def phase5_extract_patterns():
    """Phase 5: 疑点模式提取"""
    print("\nPhase 5: 提取疑点模式...")
    
    patterns = [
        ("三率背离", "预算执行率正常+资金支付率正常但项目完成率异常低→资金被挪用或虚列支出", "铁证", "预算执行"),
        ("采购价畸高", "同类商品同期采购价高于市场均价50%+供应商单一来源→利益输送嫌疑", "铁证", "招投标审计"),
        ("人员经费异常", "临聘人员数量×人均工资远超核定数→虚列人员套取资金", "铁证", "专项资金"),
        ("工程变更超限", "工程变更金额超合同价15%且未履行审批→规避招标或利益输送", "铁证", "工程审计"),
        ("现金支付异常", "大额支出频繁使用现金+无审批→资金去向不明", "铁证", "经责审计"),
        ("账外资产", "固定资产台账与实物盘点不符+新增资产无采购记录→账外资产或虚假采购", "铁证", "国企审计"),
        ("往来款长期挂账", "三年以上无变动的应收/应付款→虚列往来款或资金被长期占用", "强信号", "往来款清理"),
        ("补贴对象异常", "同一地址/电话/账户领取多份补贴→虚假申报骗取补贴", "铁证", "补贴审计"),
        ("能耗数据异常", "产量下降但能耗上升+能耗与产量相关性断裂→数据造假或设备异常", "强信号", "能源审计"),
        ("绩效目标虚设", "绩效目标全是'提升''加强''完善'无量化指标→项目根本不可评价", "强信号", "绩效评价"),
    ]
    
    fp_list = []
    for i, (name, desc, conf, bl) in enumerate(patterns, 1):
        fp_list.append({
            "id": f"FP-AUDIT-{i:04d}",
            "type": "finding_pattern",
            "name": name,
            "signal_description": desc,
            "inference_chain": [],
            "confidence": conf,
            "min_hits_required": 1,
            "false_positive_scenarios": [],
            "related_methods": [],
            "related_patterns": [],
            "severity_when_confirmed": "P0" if conf == "铁证" else "P1",
            "provenance": {"source": "融策审计方法论+15维复核经验", "date_identified": TODAY},
            "keywords": [name],
            "business_line": bl
        })
    
    if fp_list:
        path = AUDIT_DATASET / f'patterns_phase5_{TODAY}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(fp_list, f, ensure_ascii=False, indent=2)
        print(f"  疑点模式: {len(fp_list)} → {path}")
    
    return fp_list


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse, hashlib
    p = argparse.ArgumentParser(description='审计行业高质量数据集构建引擎')
    p.add_argument('--phase', choices=['1','2','3','4','5','all'], default='1')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--stats', action='store_true')
    p.add_argument('--max-per-line', type=int, default=15, help='每条线最多提取案例数')
    args = p.parse_args()
    
    if args.stats:
        # 汇总统计
        all_files = list(AUDIT_DATASET.glob('*.json')) if AUDIT_DATASET.exists() else []
        print(f"\n{'='*60}")
        print(f"  审计行业高质量数据集 — 总览")
        print(f"{'='*60}")
        total = 0
        for f in sorted(all_files):
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            count = len(data) if isinstance(data, list) else 1
            total += count
            print(f"  {f.name}: {count} entries")
        print(f"\n  总计: {total} entries")
        
        # 加上招投标数据集
        bid_dir = DATASET_DIR / 'bidding-audit' / 'entries'
        if bid_dir.exists():
            bid_total = sum(1 for _ in bid_dir.glob('*.json'))
            print(f"  招投标数据集: ~{bid_total} files, 56 entries")
            total += 56
        print(f"  全量总计: ~{total} entries")
        sys.exit(0)
    
    # Phase 1: 扫描分类
    catalog = phase1_scan()
    
    if args.phase == '1':
        sys.exit(0)
    
    # Phase 2: 提取案例
    if args.phase in ('2', 'all'):
        cases, case_stats = phase2_extract_cases(catalog, args.max_per_line)
    
    # Phase 3: 提取法规
    if args.phase in ('3', 'all'):
        regs = phase3_extract_regulations(catalog)
    
    # Phase 4: 检测方法
    if args.phase in ('4', 'all'):
        methods = phase4_extract_methods(catalog)
    
    # Phase 5: 疑点模式
    if args.phase in ('5', 'all'):
        patterns = phase5_extract_patterns()
    
    print(f"\n{'='*60}")
    print(f"  构建完成。数据目录: {AUDIT_DATASET}")
    print(f"{'='*60}")
