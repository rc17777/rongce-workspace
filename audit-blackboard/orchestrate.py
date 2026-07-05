# -*- coding: utf-8 -*-
"""
融策多Agent审计平台 — 通用调度中枢 v2.0
Blackboard架构: prepare(准备任务) → [主Agent spawn子Agent] → collect(收集碰撞) → report

用法:
  python orchestrate.py create "校服采购审计" --type procurement
  python orchestrate.py prepare 校服采购审计 --agents data,contract,bid
  → 输出 spawn plan JSON，主Agent据此 sessions_spawn 子Agent
  → 子Agent完成任务后写 findings/*.json
  python orchestrate.py collect 校服采购审计
  python orchestrate.py status 校服采购审计
  python orchestrate.py report 校服采购审计
"""
import os, sys, json, time, argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

# === 配置 ===
BLACKBOARD = Path(__file__).parent
PROJECTS = BLACKBOARD / 'projects'
SCHEMA_DIR = BLACKBOARD / 'schemas'
AGENT_SPECS = BLACKBOARD / 'agent_specs'

BIZ_AGENT_MAP = {
    'economic_responsibility': {'required': ['data_scout','contract_hound','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['bid_hunter','expert_bias_detector']},
    'revenue_expenditure':   {'required': ['data_scout','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['contract_hound','expert_bias_detector']},
    'budget_execution':      {'required': ['data_scout','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['contract_hound','expert_bias_detector']},
    'special_fund':          {'required': ['data_scout','contract_hound','bid_hunter','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['expert_bias_detector']},
    'receivables_cleanup':   {'required': ['data_scout','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['contract_hound','law_inspector','expert_bias_detector']},
    'bidding':               {'required': ['bid_hunter','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['data_scout','contract_hound','expert_bias_detector']},
    'soe':                   {'required': ['data_scout','contract_hound','bid_hunter','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['expert_bias_detector']},
    'engineering':           {'required': ['data_scout','contract_hound','bid_hunter','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['expert_bias_detector']},
    'performance':           {'required': ['data_scout','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['contract_hound','expert_bias_detector']},
    'subsidy':               {'required': ['data_scout','contract_hound','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['bid_hunter','expert_bias_detector']},
    'energy':                {'required': ['data_scout','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['contract_hound','expert_bias_detector']},
    'cost_benefit':          {'required': ['data_scout','contract_hound','law_inspector','workpaper_crafter','report_writer','review_sentinel'], 'optional': ['expert_bias_detector']},
}

BIZ_ALIASES = {
    '经济责任审计':'economic_responsibility','经责':'economic_responsibility',
    '收支审计':'revenue_expenditure','收支':'revenue_expenditure',
    '预算执行审计':'budget_execution','预算执行':'budget_execution',
    '专项审计':'special_fund','专项资金':'special_fund',
    '往来款清理':'receivables_cleanup','往来款':'receivables_cleanup',
    '招投标审计':'bidding','招投标':'bidding',
    '国企审计':'soe','国企':'soe',
    '工程审计':'engineering','工程':'engineering',
    '绩效评价':'performance','绩效':'performance',
    '政府补贴':'subsidy','补贴':'subsidy',
    '能源审计':'energy','能源':'energy',
    '成本效益':'cost_benefit','成本':'cost_benefit',
}

MCP_TOOLS = {
    'data_scout':      ['clean_journal','map_accounts','config_voucher_rules'],
    'contract_hound':  ['contract_review','confirmation_match'],
    'bid_hunter':      [],
    'law_inspector':   [],
    'workpaper_crafter':['workpaper_archive'],
    'report_writer':   [],
    'review_sentinel': [],
    'expert_bias_detector': ['expert_bias_detection'],
    'data_desensitizer': ['desensitize_excel'],
}

AGENT_LABELS = {
    'data_scout':'数据侦察兵','contract_hound':'合同猎犬','bid_hunter':'招投标猎手',
    'law_inspector':'法规检察官','workpaper_crafter':'底稿工匠','report_writer':'报告笔杆子','review_sentinel':'复核哨兵',
    'expert_bias_detector':'评标偏离度检测','data_desensitizer':'数据脱敏',
}


# ================================================================
# 项目管理
# ================================================================

def create_project(name, biz_type=None):
    pid = name.replace(' ','_')
    proj_dir = PROJECTS / pid
    if proj_dir.exists():
        print(f'项目 [{name}] 已存在')
        return pid
    for d in ['findings','collision','workpapers','output','tasks']:
        (proj_dir / d).mkdir(parents=True, exist_ok=True)
    # Resolve biz_type: accept both Chinese alias and English key
    biz_key = BIZ_ALIASES.get(biz_type) if biz_type else None
    if not biz_key and biz_type:
        # Try reverse lookup: is it already an English key?
        if biz_type in BIZ_AGENT_MAP:
            biz_key = biz_type
    agents_cfg = BIZ_AGENT_MAP.get(biz_key, BIZ_AGENT_MAP['special_fund']) if biz_key else {}
    status = {
        'project_id':pid,'project_name':name,'biz_type':biz_type or '未指定',
        'created_at':datetime.now(CST).isoformat(),
        'phase':'created','agents':agents_cfg,'findings_count':0,'collision_count':0,'logs':[]
    }
    (proj_dir/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'✅ 创建项目: [{name}]')
    if biz_type:
        req=agents_cfg.get('required',[])
        print(f'   业务线: {biz_type} → 必选Agent: {", ".join(req)}')
    return pid

def get_project(name):
    pid=name.replace(' ','_')
    proj_dir=PROJECTS/pid
    if not proj_dir.exists():
        print(f'项目 [{name}] 不存在')
        return None
    return proj_dir

def read_status(proj_dir):
    sf=proj_dir/'status.json'
    return json.loads(sf.read_text(encoding='utf-8')) if sf.exists() else None

def write_status(proj_dir, status):
    (proj_dir/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')


# ================================================================
# Step 1: prepare — 生成子Agent任务文件
# ================================================================

def prepare_agent_tasks(proj_dir, agents_list, data_path=None, audit_scope=None):
    """为每个Agent生成详细任务描述，输出spawn plan JSON"""
    tasks_dir = proj_dir / 'tasks'
    tasks_dir.mkdir(exist_ok=True)
    pid = proj_dir.name

    # === Step 0: Token预算检查 ===
    raw_data_dir = proj_dir / 'raw_data'
    if raw_data_dir.exists() and any(raw_data_dir.iterdir()):
        print(f'\n💰 Token预算检查...')
        try:
            sys.path.insert(0, str(BLACKBOARD.parent / 'scripts'))
            from workflow_with_budget import check_budget
            ok, est = check_budget(
                directory=str(raw_data_dir),
                task="分析",
                reasoning=True,
                auto_confirm=True,
                quiet=False
            )
            if not ok:
                print('[!] 预算检查未通过，任务取消')
                return None
        except ImportError:
            print('[!] 预算模块未找到，跳过')
        except Exception as e:
            print(f'[!] 预算检查出错: {e}，继续执行')

    # === 数据脱敏检查 ===
    raw_data_dir = proj_dir / 'raw_data'
    if raw_data_dir.exists():
        desensitized_count = 0
        for f in raw_data_dir.glob('*'):
            if f.suffix.lower() in ('.xlsx', '.xls', '.csv'):
                if '_脱敏' not in f.name:
                    try:
                        # 自动脱敏
                        import sys
                        sys.path.insert(0, str(BLACKBOARD / 'standards' / 'scripts'))
                        from desensitize_excel import desensitize_excel, desensitize_csv
                        output_path = f.parent / f'{f.stem}_脱敏{f.suffix}'
                        if f.suffix.lower() in ('.xlsx', '.xls'):
                            desensitize_excel(str(f), str(output_path), verbose=False)
                        else:
                            desensitize_csv(str(f), str(output_path), verbose=False)
                        desensitized_count += 1
                        print(f'   🔒 自动脱敏: {f.name} → {output_path.name}')
                    except Exception as e:
                        print(f'   ⚠️ 脱敏失败 {f.name}: {e}')
        if desensitized_count > 0:
            print(f'✅ 自动脱敏完成: {desensitized_count} 个文件')
    # === 脱敏检查结束 ===

    # 读取Schema
    schema = json.loads((SCHEMA_DIR/'finding_schema.json').read_text(encoding='utf-8'))

    # 加载Agent规格
    agent_specs = {}
    for a in agents_list:
        sf = AGENT_SPECS / f'{a}.json'
        if sf.exists():
            agent_specs[a] = json.loads(sf.read_text(encoding='utf-8'))
        else:
            # 回退默认
            agent_specs[a] = {'name':AGENT_LABELS.get(a,a),'desc':'','tools':MCP_TOOLS.get(a,[]),
                'prompt':f'你是{a}审计Agent。输出格式严格遵循finding_schema.json。'}

    spawn_plan = {
        'project_id': pid,
        'data_path': data_path or '(由主Agent指定)',
        'audit_scope': audit_scope or '',
        'agents': [],
        'total_agents': len(agents_list),
        'schema': schema,
    }

    for i, agent_name in enumerate(agents_list):
        spec = agent_specs[agent_name]
        tools = spec.get('tools', [])
        label = spec.get('name', agent_name)

        task = {
            'agent_id': agent_name,
            'label': label,
            'index': i+1,
            'task_file': f'{agent_name}_task.json',
            'output_file': f'findings/{agent_name}.json',
            'spawn_args': {
                'task': f"""你是融策审计黑板的{label}Agent。

{spec.get('prompt','')}

## 任务
项目: {pid}
审计范围: {audit_scope or '全量'}
数据路径: {data_path or '请主Agent提供'}

## 输出要求
1. 分析数据，产出审计发现
2. 每条发现必须严格遵循以下Schema生成JSON：
```json
{schema.get('properties',{})}
```
3. finding_id格式: F-{datetime.now().year}-{{序号从001开始}}
4. 所有发现写入文件: D:\\openclaw-workspace\\audit-blackboard\\projects\\{pid}\\findings\\{agent_name}.json
5. 格式: JSON数组，每个元素一条发现

## 可用工具
{chr(10).join(f'- {t}' for t in tools) if tools else '无限制（用你全部能力）'}

## 关键原则
- 每个发现必须带entities（涉及的实体名称），这是碰撞分析的基础
- confidence: ≥80高置信/50-80需验证/<50初步线索
- 禁止直接下审计结论，所有发现写"疑似"
- 发现越多越好，但每条必须有证据支撑""",
                'mode': 'run',
                'sandbox': 'inherit',
            }
        }
        spawn_plan['agents'].append(task)

        # 写单个任务文件
        (tasks_dir / f'{agent_name}_task.json').write_text(
            json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')

    # 写总plan
    plan_file = tasks_dir / 'spawn_plan.json'
    plan_file.write_text(json.dumps(spawn_plan, ensure_ascii=False, indent=2), encoding='utf-8')

    # 更新状态
    status = read_status(proj_dir)
    if status:
        status['phase'] = 'tasks_prepared'
        status['logs'].append(f'[{datetime.now(CST).strftime("%H:%M")}] 准备{len(agents_list)}个Agent任务')
        write_status(proj_dir, status)

    return spawn_plan


# ================================================================
# Step 2: collect — 收集发现并碰撞
# ================================================================

def normalize_finding(finding):
    """容错规范化：子Agent输出的字段名不一致时自动映射+填充默认值"""
    now = datetime.now(CST).isoformat()
    # 字段映射：子Agent常用别名 → 标准Schema字段
    FIELD_MAP = {
        'title': 'summary',
        'risk_level': 'severity',
        'level': 'severity',
        'risk': 'severity',
        'description': '_description',
    }
    for alt, std in FIELD_MAP.items():
        if alt in finding and std not in finding:
            finding[std] = finding.pop(alt)
    # 默认值填充
    if 'timestamp' not in finding:
        finding['timestamp'] = now
    if 'severity' not in finding:
        finding['severity'] = '中'
    if 'summary' not in finding:
        finding['summary'] = finding.get('_description', finding.get('title', ''))[:200]
    if 'confidence' not in finding:
        finding['confidence'] = 80
    if 'entities' not in finding:
        finding['entities'] = []
    if 'evidence' not in finding:
        finding['evidence'] = []
    if 'law_refs' not in finding:
        finding['law_refs'] = []
    if 'related_findings' not in finding:
        finding['related_findings'] = []
    if 'status' not in finding:
        finding['status'] = '未确认'
    if 'amount' not in finding:
        finding['amount'] = None
    # 清理临时字段
    finding.pop('_description', None)
    finding.pop('title', None)
    finding.pop('risk_level', None)
    finding.pop('level', None)
    finding.pop('risk', None)
    return finding


def validate_finding(finding):
    """验证发现是否符合Schema"""
    required = ['finding_id','agent','timestamp','type','severity','summary']
    errors = []
    for field in required:
        if field not in finding or not finding[field]:
            errors.append(f'缺少: {field}')
    if 'finding_id' in finding and not str(finding['finding_id']).startswith('F-'):
        errors.append(f'finding_id格式应为F-YYYY-NNN')
    if finding.get('severity') not in ('高','中','低'):
        errors.append(f'severity值无效: {finding.get("severity")}')
    return len(errors)==0, errors


def collect_and_collide(proj_dir):
    """收集findings目录下所有JSON，验证Schema，执行碰撞"""
    findings_dir = proj_dir / 'findings'
    collision_dir = proj_dir / 'collision'
    collision_dir.mkdir(exist_ok=True)

    # === 收集前预算检查 ===
    all_jsons = list(findings_dir.glob('*.json')) if findings_dir.exists() else []
    if all_jsons:
        total_size = sum(f.stat().st_size for f in all_jsons)
        # findings JSON通常1KB≈500token
        est_tokens = int(total_size * 0.5)
        if est_tokens > 50000:
            print(f'\n💰 收集阶段预算提示: {len(all_jsons)}个发现文件，预估{est_tokens:,} token')
            print(f'   建议：如数据量过大，可分批次collect或精简发现')

    all_findings = []
    validation_report = []

    if findings_dir.exists():
        for f in findings_dir.glob('*.json'):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if 'agent' not in item:
                        item['agent'] = f.stem
                    item = normalize_finding(item)
                    valid, errors = validate_finding(item)
                    if valid:
                        all_findings.append(item)
                    else:
                        validation_report.append({'finding_id':item.get('finding_id','?'), 'errors':errors})
            except Exception as e:
                validation_report.append({'finding_id':f.name, 'errors':[str(e)]})

    print(f'\n📥 收集结果: {len(all_findings)}个有效发现')
    if validation_report:
        print(f'⚠️ Schema验证失败: {len(validation_report)}个')
        for v in validation_report:
            print(f'   {v["finding_id"]}: {v["errors"]}')

    # 写入汇总
    (findings_dir / '_all_findings.json').write_text(
        json.dumps(all_findings, ensure_ascii=False, indent=2), encoding='utf-8')

    if len(all_findings) < 2:
        print('发现数量不足，无法碰撞')
        return all_findings, []

    # === 碰撞引擎 ===
    collisions = []

    # 规则1: 实体碰撞
    entity_map = {}
    for f_item in all_findings:
        for ent in f_item.get('entities', []):
            ekey = ent.strip().lower()
            entity_map.setdefault(ekey, []).append(f_item['finding_id'])
    for entity, fids in entity_map.items():
        agents_involved = set()
        for fid in fids:
            for f_item in all_findings:
                if f_item['finding_id'] == fid:
                    agents_involved.add(f_item.get('agent','unknown'))
        if len(agents_involved) >= 2:
            collisions.append({
                'rule':'实体碰撞','entity':entity,'findings':fids,
                'agents':list(agents_involved),
                'severity':'高' if len(agents_involved)>=3 else '中',
                'action':f'同一实体 [{entity}] 被{len(agents_involved)}个Agent同时标记 → 建议深度核查',
                'timestamp':datetime.now(CST).isoformat()
            })

    # 规则2: 逻辑碰撞
    logic_rules = [
        (['财务异常','资金挪用','合同违规'], '财务资金+合同违规交叉 → 疑似利益输送'),
        (['围标串标','合同违规'], '围标+合同违规交叉 → 围标中标后续利益安排'),
        (['财务异常','虚增成本'], '财务异常+虚增成本交叉 → 虚构交易套取资金'),
        (['资金挪用','程序违规'], '资金挪用+程序违规交叉 → 审批绕过+资金转移'),
        (['履职缺失','财务异常'], '履职缺失+财务异常交叉 → 管理失职致损'),
    ]
    for types_combo, action in logic_rules:
        matching = [f_item for f_item in all_findings if f_item.get('type') in types_combo]
        if len(matching) >= 2:
            agents_involved = set(f_item.get('agent') for f_item in matching)
            if len(agents_involved) >= 2:
                collisions.append({
                    'rule':'逻辑碰撞','types':types_combo,
                    'findings':[f_item['finding_id'] for f_item in matching],
                    'agents':list(agents_involved),'severity':'高',
                    'action':action,'timestamp':datetime.now(CST).isoformat()
                })

    # 规则3: 时间碰撞
    time_buckets = {}
    for f_item in all_findings:
        bucket = f_item.get('timestamp','')[:7]
        if bucket: time_buckets.setdefault(bucket, []).append(f_item['finding_id'])
    for bucket, fids in time_buckets.items():
        if len(fids) >= 3:
            agents_involved = set()
            for fid in fids:
                for f_item in all_findings:
                    if f_item['finding_id'] == fid:
                        agents_involved.add(f_item.get('agent','unknown'))
            if len(agents_involved) >= 2:
                collisions.append({
                    'rule':'时间碰撞','period':bucket,'findings':fids,
                    'agents':list(agents_involved),'severity':'中',
                    'action':f'{bucket}月份集中{len(fids)}个发现 → 疑似系统性风险',
                    'timestamp':datetime.now(CST).isoformat()
                })

    # 去重
    seen = set(); unique = []
    for c in collisions:
        key = ','.join(sorted(c.get('findings',[])))
        if key not in seen:
            seen.add(key); unique.append(c)

    # 写collision
    (collision_dir/'cross_hits.json').write_text(json.dumps(unique,ensure_ascii=False,indent=2),encoding='utf-8')

    # 更新related_findings
    for c in unique:
        for fid in c.get('findings',[]):
            for f_item in all_findings:
                if f_item['finding_id'] == fid:
                    if 'related_findings' not in f_item: f_item['related_findings'] = []
                    for other in c['findings']:
                        if other != fid and other not in f_item['related_findings']:
                            f_item['related_findings'].append(other)

    # 写回各Agent文件
    for agent_name in set(f_item.get('agent','') for f_item in all_findings):
        agent_findings = [f_item for f_item in all_findings if f_item.get('agent') == agent_name]
        af = findings_dir / f'{agent_name}.json'
        if agent_findings:
            af.write_text(json.dumps(agent_findings, ensure_ascii=False, indent=2), encoding='utf-8')

    # 更新状态
    status = read_status(proj_dir)
    if status:
        status['phase'] = 'collision_done'
        status['findings_count'] = len(all_findings)
        status['collision_count'] = len(unique)
        status['logs'].append(f'[{datetime.now(CST).strftime("%H:%M")}] 收集:{len(all_findings)}发现 碰撞:{len(unique)}交叉线索')
        write_status(proj_dir, status)

    return all_findings, unique


# ================================================================
# 状态与报告
# ================================================================

def show_status(proj_dir):
    status = read_status(proj_dir)
    if not status: print('状态文件不存在'); return
    print(f'\n📋 [{status["project_name"]}] ({status["project_id"]})')
    print(f'   业务线: {status["biz_type"]} | 阶段: {status["phase"]}')
    print(f'   发现: {status["findings_count"]} | 碰撞: {status["collision_count"]}')
    for log in status.get('logs', [])[-5:]:
        print(f'   {log}')
    for sub in ['findings','collision','workpapers','output','tasks']:
        files = list((proj_dir/sub).glob('*')) if (proj_dir/sub).exists() else []
        print(f'   {sub}/: {len(files)}个文件')


def show_report(proj_dir):
    collision_dir = proj_dir / 'collision'
    findings_dir = proj_dir / 'findings'
    cf = collision_dir / 'cross_hits.json'

    all_findings = []
    for f in findings_dir.glob('*.json'):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            all_findings.extend(data if isinstance(data,list) else [data])
        except: pass

    if cf.exists():
        collisions = json.loads(cf.read_text(encoding='utf-8'))
    else:
        collisions = []

    status = read_status(proj_dir)
    name = status['project_name'] if status else proj_dir.name

    print(f'\n{"="*60}')
    print(f'  审计发现摘要 — {name}')
    print(f'{"="*60}')

    by_sev = {'高':[],'中':[],'低':[]}
    for f_item in all_findings:
        by_sev.get(f_item.get('severity',''), []).append(f_item)

    print(f'\n📊 发现: 高{len(by_sev["高"])}/中{len(by_sev["中"])}/低{len(by_sev["低"])}')
    print(f'🔗 碰撞: {len(collisions)}条\n')

    for level in ['高','中','低']:
        items = by_sev[level]
        if items:
            print(f'--- {level}风险 ({len(items)}条) ---')
            for i, f_item in enumerate(items[:8]):
                related = f_item.get('related_findings',[])
                tag = ' 🔗' if related else ''
                print(f'  {i+1}. [{f_item.get("agent","?")}]{tag} {f_item.get("summary","")}')
            if len(items) > 8: print(f'  ... 还有{len(items)-8}条')
            print()

    if collisions:
        print('--- 交叉碰撞 ---')
        for c in collisions:
            icon = '🔴' if c['severity']=='高' else '🟡'
            print(f'  {icon} [{c["rule"]}] {c["action"]}')
            print(f'     涉及: {", ".join(c["agents"])}')
        print()

    print('⚠️ AI生成摘要，请人工复核')


# ================================================================
# 获取spawn plan（供主Agent读取）
# ================================================================

def get_spawn_plan(proj_dir):
    """返回spawn plan，主Agent据此调用sessions_spawn"""
    pf = proj_dir / 'tasks' / 'spawn_plan.json'
    if not pf.exists():
        print('未找到spawn plan，请先 prepare')
        return None
    return json.loads(pf.read_text(encoding='utf-8'))


# ================================================================
# Main
# ================================================================

def main():
    parser = argparse.ArgumentParser(description='融策多Agent审计平台 v2.0')
    sub = parser.add_subparsers(dest='command')

    p1=sub.add_parser('create'); p1.add_argument('name'); p1.add_argument('--type',default=None)
    p2=sub.add_parser('prepare'); p2.add_argument('name'); p2.add_argument('--agents'); p2.add_argument('--data-path'); p2.add_argument('--scope',default='全量审计')
    p3=sub.add_parser('collect'); p3.add_argument('name')
    p4=sub.add_parser('status'); p4.add_argument('name')
    p5=sub.add_parser('report'); p5.add_argument('name')

    args = parser.parse_args()

    if args.command == 'create':
        create_project(args.name, args.type)

    elif args.command == 'prepare':
        proj_dir = get_project(args.name)
        if not proj_dir: return
        status = read_status(proj_dir)
        if args.agents:
            agents_list = [a.strip() for a in args.agents.split(',')]
        elif status and status.get('agents'):
            agents_list = status['agents'].get('required',[])
        else:
            agents_list = ['data_scout','contract_hound','bid_hunter']

        plan = prepare_agent_tasks(proj_dir, agents_list, args.data_path, args.scope)

        print(f'\n📦 已生成 {len(agents_list)} 个Agent任务:')
        for a in plan['agents']:
            print(f'  [{a["index"]}] {a["label"]} ({a["agent_id"]})')

        print(f'\n📋 Spawn Plan: {proj_dir}/tasks/spawn_plan.json')
        print(f'   主Agent读取此文件 → sessions_spawn 派发子Agent')
        print(f'   子Agent完成后 → python orchestrate.py collect {args.name}')

    elif args.command == 'collect':
        proj_dir = get_project(args.name)
        if not proj_dir: return
        findings, collisions = collect_and_collide(proj_dir)
        if collisions:
            print(f'\n碰撞: {len(collisions)}个交叉线索')
            for c in collisions[:8]:
                icon = '🔴' if c['severity']=='高' else '🟡'
                print(f'  {icon} [{c["rule"]}] {c["action"][:100]}')

    elif args.command == 'status':
        proj_dir = get_project(args.name)
        if proj_dir: show_status(proj_dir)

    elif args.command == 'report':
        proj_dir = get_project(args.name)
        if proj_dir: show_report(proj_dir)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
