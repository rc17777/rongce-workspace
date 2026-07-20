# -*- coding: utf-8 -*-
"""
融策审计全生命周期工作流引擎 v1.1
=====================================
七阶段状态机：Init → OCR → Classify → Plan → Analyze → Evidence → Report → Archive

用法:
  python workflow_engine.py status --project "XX项目"
  python workflow_engine.py init --name "XX项目" --type "经责"
  python workflow_engine.py ocr --project "XX项目"
  python workflow_engine.py classify --project "XX项目"
  python workflow_engine.py plan --project "XX项目"
  python workflow_engine.py analyze --project "XX项目"
  python workflow_engine.py evidence --project "XX项目"
  python workflow_engine.py report --project "XX项目"
  python workflow_engine.py archive --project "XX项目"
"""
import os, sys, json, argparse, shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

# === 路径配置 ===
WORKSPACE = Path(__file__).parent.parent.parent  # C:\Users\scrccpa\.openclaw\workspace
BLACKBOARD = WORKSPACE / 'audit-blackboard'
PROJECTS = BLACKBOARD / 'projects'
RONGCE_HUB = WORKSPACE / 'RONGCE_AI_HUB'
OBSIDIAN = Path.home() / 'Documents' / 'Obsidian Vault'
SKILLS_DIR = Path.home() / '.openclaw' / 'skills'

# === 业务线别名 ===
BIZ_ALIASES = {
    '经责': ('economic_responsibility', '经济责任审计'),
    '收支': ('revenue_expenditure', '收支审计'),
    '预算': ('budget_execution', '预算执行审计'),
    '专项': ('special_fund', '专项资金审计'),
    '往来款': ('receivables_cleanup', '往来款清理'),
    '招投标': ('bidding', '招投标审计'),
    '国企': ('soe', '国企审计'),
    '工程': ('engineering', '工程竣工决算财务审计'),
    '绩效': ('performance', '预算绩效管理'),
    '补贴': ('subsidy', '政府补贴审计'),
    '能源': ('energy', '能源审计'),
    '成本': ('cost_benefit', '成本效益审计'),
    '预算编制': ('budget_preparation', '工程预算编制'),
    '财评': ('fiscal_review', '财政评审'),
    '全咨': ('full_process_consult', '全过程工程咨询'),
    '结算': ('engineering_settlement', '工程结算'),
}

# === 工作流阶段定义 ===
PHASES = {
    'init':      {'order': 0, 'name': '项目初始化',       'next': 'ocr',      'agent': None},
    'ocr':       {'order': 1, 'name': 'OCR预处理',         'next': 'classify', 'agent': 'ocr_processor'},
    'classify':  {'order': 2, 'name': '资料智能分类',     'next': 'plan',     'agent': 'data_classifier'},
    'plan':      {'order': 3, 'name': '实施方案与资料清单', 'next': 'analyze',  'agent': 'plan_writer'},
    'analyze':   {'order': 4, 'name': '多Agent分析',       'next': 'evidence', 'agent': 'orchestrator'},
    'evidence':  {'order': 5, 'name': '现场核实与取证底稿', 'next': 'report',   'agent': 'workpaper_crafter'},
    'report':    {'order': 6, 'name': '报告撰写',          'next': 'archive',  'agent': 'report_writer'},
    'archive':   {'order': 7, 'name': '反馈闭环归档',     'next': None,       'agent': None},
}

# ============================================================
#  Phase 0: 项目初始化
# ============================================================
def phase_init(project_name, biz_type_raw):
    """创建项目目录结构 + 业务线信息"""
    # 解析业务类型
    biz_key, biz_name = BIZ_ALIASES.get(biz_type_raw, (biz_type_raw, biz_type_raw))

    slug = project_name.replace(' ', '_').replace('/', '_')
    project_dir = PROJECTS / slug

    if project_dir.exists():
        return {'status': 'exists', 'project': slug, 'dir': str(project_dir)}

    # 创建完整目录结构
    dirs = [
        'raw_data',              # 原始资料
        'raw_data/财务',         'raw_data/合同',       'raw_data/招投标',
        'raw_data/制度',         'raw_data/工商',       'raw_data/项目',
        'raw_data/绩效',         'raw_data/资产',       'raw_data/往来',
        'raw_data/工程',
        'outputs',               # Phase输出物
        'outputs/实施方案',      'outputs/问题清单',
        'outputs/取证单',        'outputs/底稿',
        'outputs/报告',
        'findings',              # Agent发现JSON
        'collision',             # 交叉碰撞结果
        'archive',               # 归档材料
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # 写入项目元信息
    status = {
        'project_name': slug,
        'display_name': project_name,
        'biz_type': biz_key,
        'biz_name': biz_name,
        'created_at': datetime.now(CST).isoformat(),
        'current_phase': 'init',
        'phases_completed': [],
        'files_count': {'raw_data': 0, 'classified': 0},
        'agents_spawned': [],
        'findings_count': 0,
        'issues_total': 0,
        'issues_P0': 0,
        'issues_P1': 0,
        'issues_P2': 0,
    }
    with open(project_dir / 'status.json', 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    # 在Obsidian中创建项目目录
    obsidian_project = OBSIDIAN / biz_name / slug
    obsidian_project.mkdir(parents=True, exist_ok=True)

    return {
        'status': 'created',
        'project': slug,
        'biz_type': biz_key,
        'biz_name': biz_name,
        'dir': str(project_dir),
        'obsidian_dir': str(obsidian_project),
        'dirs_created': dirs,
    }

# ============================================================
#  Phase 1: OCR预处理（新增）
# ============================================================
def phase_ocr(project_slug):
    """扫描raw_data，识别需OCR的文件，执行OCR+结构化提取"""
    project_dir = PROJECTS / project_slug
    raw_dir = project_dir / 'raw_data'
    ocr_cache_dir = raw_dir / '.ocr_cache'

    if not raw_dir.exists():
        return {'status': 'error', 'message': 'raw_data目录不存在，请先放入资料'}

    status = _load_status(project_dir)
    status['current_phase'] = 'ocr'

    # 扫描所有文件，判断哪些需要OCR
    ocr_needed = []
    skip_files = []
    total_files = 0

    for root, dirs, filenames in os.walk(raw_dir):
        # 跳过.ocr_cache目录
        if '.ocr_cache' in root:
            continue
        for f in filenames:
            fp = Path(root) / f
            ext = fp.suffix.lower()
            total_files += 1
            rel = str(fp.relative_to(raw_dir))

            # 分类：需要OCR vs 跳过
            if ext in ('.pdf',):
                # PDF需要检测是否有文本层
                ocr_needed.append({
                    'file': rel, 'type': 'pdf', 'size': fp.stat().st_size,
                    'action': 'detect_text_layer'
                })
            elif ext in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'):
                ocr_needed.append({
                    'file': rel, 'type': 'image', 'size': fp.stat().st_size,
                    'action': 'ocr_full'
                })
            elif ext in ('.ofd',):
                ocr_needed.append({
                    'file': rel, 'type': 'ofd', 'size': fp.stat().st_size,
                    'action': 'ofd_parse'
                })
            elif ext in ('.rar', '.zip', '.7z'):
                ocr_needed.append({
                    'file': rel, 'type': 'archive', 'size': fp.stat().st_size,
                    'action': 'extract_then_recurse'
                })
            else:
                skip_files.append({'file': rel, 'type': ext})

    # OCR缓存目录
    ocr_cache_dir.mkdir(parents=True, exist_ok=True)
    for sub in ['发票', '合同', '招投标', '银行', '通用']:
        (ocr_cache_dir / sub).mkdir(exist_ok=True)

    # 按文件特征预分类（发票/合同/银行单据/招投标/通用）
    doc_type_hints = _guess_doc_types(ocr_needed)

    status['ocr_stats'] = {
        'total_files': total_files,
        'ocr_needed': len(ocr_needed),
        'skip': len(skip_files),
        'by_type': doc_type_hints['counts'],
    }
    _save_status(project_dir, status)

    spawn_plan = {
        'phase': 'ocr',
        'project': project_slug,
        'ocr_needed': len(ocr_needed),
        'ocr_files': ocr_needed[:20],  # 只传前20个样本给Agent看
        'doc_type_breakdown': doc_type_hints['counts'],
        'ocr_cache_dir': str(ocr_cache_dir),
        'task': f"""对 {len(ocr_needed)} 个文件执行OCR预处理。

文件分布：
{json.dumps(doc_type_hints['counts'], ensure_ascii=False, indent=2)}

处理步骤：
1. PDF文件：先用pdfplumber检测文本层
   - 有文本层（>50字）：直接提取文本，不做OCR
   - 无文本层：转换为图片 → PaddleOCR
2. 图片文件：PaddleOCR识别
3. 发票类文件：OCR后 → qwen-vl-max 结构化提取（发票号/日期/金额/购销方）
4. 合同类文件：OCR后 → qwen3.7-plus 提取关键字段（合同号/金额/日期/甲乙方/条款）
5. 招投标文件：OCR后 → 提取报价/得分/投标人
6. 银行单据：OCR后 → 提取交易日期/金额/对方户名
7. 通用文档：OCR后保留全文.md
8. 输出到 {ocr_cache_dir} 下对应子目录

已有的OCR脚本参考：
- scripts/paddleocr_audit_batch.py（PaddleOCR批量PDF）
- scripts/contract_ocr_v5.py（合同OCR+结构化）
- scripts/ocr_intelligent_audit_v3.py（智能审计OCR）""",
        'next': 'OCR完成后，运行: python workflow_engine.py classify --project ' + project_slug,
    }

    with open(project_dir / 'outputs' / 'spawn_plan_ocr.json', 'w', encoding='utf-8') as f:
        json.dump(spawn_plan, f, ensure_ascii=False, indent=2)

    return {
        'status': 'ready_to_spawn',
        'phase': 'ocr',
        'project': project_slug,
        'ocr_needed': len(ocr_needed),
        'total_files': total_files,
        'doc_types': doc_type_hints['counts'],
        'spawn_plan': spawn_plan,
    }


def _guess_doc_types(ocr_files):
    """根据文件名猜测文档类型（发票/合同/银行/招投标/通用）"""
    counts = {'发票': 0, '合同': 0, '招投标': 0, '银行': 0, '通用': 0}
    samples = {'发票': [], '合同': [], '招投标': [], '银行': [], '通用': []}

    rules = [
        (['发票', '票据', 'invoice', 'receipt', '增值税', '普通发票'], '发票'),
        (['合同', '协议', 'contract', 'agreement', '框架'], '合同'),
        (['招标', '投标', '开标', '评标', '中标', 'bid', '标书', '报价'], '招投标'),
        (['银行', '流水', '回单', '对账单', 'bank', 'statement', '交易'], '银行'),
    ]

    for f in ocr_files:
        name = f['file'].lower()
        matched = False
        for keywords, category in rules:
            if any(kw in name for kw in keywords):
                counts[category] += 1
                if len(samples[category]) < 3:
                    samples[category].append(f['file'])
                matched = True
                break
        if not matched:
            counts['通用'] += 1
            if len(samples['通用']) < 3:
                samples['通用'].append(f['file'])

    return {'counts': counts, 'samples': samples}

# ============================================================
#  Phase 1: 资料导入与智能分类
# ============================================================
def phase_classify(project_slug):
    """扫描raw_data，自动分类打标签，同步到Obsidian"""
    project_dir = PROJECTS / project_slug
    raw_dir = project_dir / 'raw_data'

    if not raw_dir.exists():
        return {'status': 'error', 'message': 'raw_data目录不存在，请先放入资料'}

    # 更新状态
    status = _load_status(project_dir)
    status['current_phase'] = 'classify'

    # 扫描文件
    files = []
    for root, dirs, filenames in os.walk(raw_dir):
        for f in filenames:
            fp = Path(root) / f
            rel = fp.relative_to(raw_dir)
            files.append({
                'name': f,
                'path': str(rel),
                'size': fp.stat().st_size,
                'ext': fp.suffix.lower(),
            })

    # 自动分类（基于扩展名+内容关键词）
    classified = _auto_classify(files, raw_dir)

    # 更新状态
    status['files_count'] = {
        'raw_data': len(files),
        'classified': {cat: len(items) for cat, items in classified.items()},
    }
    status['phases_completed'].append('classify')

    _save_status(project_dir, status)

    # 生成spawn plan（供主Agent spawn data_classifier做深度分类）
    spawn_plan = {
        'phase': 'classify',
        'project': project_slug,
        'files_summary': {
            'total': len(files),
            'by_category': status['files_count']['classified'],
        },
        'suggested_actions': [
            f"分类完成：{cat} {cnt}个文件" for cat, cnt in status['files_count']['classified'].items()
        ],
        'next': '用户确认分类结果后，运行: python workflow_engine.py plan --project ' + project_slug,
    }

    return {
        'status': 'classified',
        'project': project_slug,
        'total_files': len(files),
        'categories': status['files_count']['classified'],
        'spawn_plan': spawn_plan,
    }


def _auto_classify(files, raw_dir):
    """基于文件名关键词和扩展名的自动分类"""
    categories = {
        '财务': [], '合同': [], '招投标': [], '制度': [],
        '工商': [], '项目': [], '绩效': [], '资产': [],
        '往来': [], '工程': [], '其他': [],
    }

    # 分类规则：(关键词列表, 类别)
    rules = [
        (['序时账', '科目余额', '辅助账', '报表', '凭证', '日记账', '总账', '明细账'], '财务'),
        (['合同', '协议', '采购', '供应商', '台账'], '合同'),
        (['招标', '投标', '开标', '评标', '中标', '标书'], '招投标'),
        (['制度', '办法', '规定', '细则', '流程', '权限', '审批'], '制度'),
        (['工商', '股权', '章程', '营业执照', '统一社会信用代码'], '工商'),
        (['立项', '可研', '批复', '概算', '预算书', '初设', '施工图'], '项目'),
        (['绩效', '目标', '自评', '指标', '佐证'], '绩效'),
        (['资产', '盘点', '台账', '折旧', '处置'], '资产'),
        (['往来', '应收', '应付', '函证', '账龄', '坏账'], '往来'),
        (['结算', '变更', '签证', '竣工', '决算', '工程量清单', '计价'], '工程'),
    ]

    for f in files:
        name_lower = f['name'].lower()
        matched = False
        for keywords, category in rules:
            if any(kw in name_lower for kw in keywords):
                categories[category].append(f)
                matched = True
                break
        if not matched:
            categories['其他'].append(f)

    # 去掉空类别
    return {k: v for k, v in categories.items() if v}


# ============================================================
#  Phase 2: 实施方案与资料清单
# ============================================================
def phase_plan(project_slug):
    """生成实施方案框架 + 资料清单"""
    project_dir = PROJECTS / project_slug
    status = _load_status(project_dir)

    if 'ocr' not in status.get('phases_completed', []):
        return {'status': 'error', 'message': '请先完成OCR预处理（ocr）'}

    status['current_phase'] = 'plan'

    # 读取DATA_SPEC中该业务线的取数清单
    biz_type = status['biz_type']
    data_checklist = _load_data_checklist(biz_type)

    # 生成spawn plan（供主Agent spawn plan_writer）
    spawn_plan = {
        'phase': 'plan',
        'project': project_slug,
        'biz_type': biz_type,
        'biz_name': status['biz_name'],
        'classified_files': status['files_count']['classified'],
        'data_checklist': data_checklist,
        'task': f"""为{status['biz_name']}项目"{status['display_name']}"撰写实施方案和资料清单。

已提供资料：{json.dumps(status['files_count']['classified'], ensure_ascii=False)}

请按以下结构撰写实施方案：
1. 审计目标与范围
2. 审计重点与难点（标注高风险领域）
3. 审计方法与程序（引用SCENARIO-SKILL-MAP中的技能推荐）
4. 人员安排与时间计划
5. 预期成果

同时输出资料清单（Excel格式），分为：
- 已提供资料
- 待补充资料
- 建议索取资料（基于DATA_SPEC取数规范）""",
        'next': '用户确认方案后，运行: python workflow_engine.py analyze --project ' + project_slug,
    }

    with open(project_dir / 'outputs' / '实施方案' / 'spawn_plan_plan.json', 'w', encoding='utf-8') as f:
        json.dump(spawn_plan, f, ensure_ascii=False, indent=2)

    status['phases_completed'].append('plan')
    _save_status(project_dir, status)

    return {
        'status': 'ready_to_spawn',
        'phase': 'plan',
        'project': project_slug,
        'spawn_plan': spawn_plan,
    }


def _load_data_checklist(biz_type):
    """从DATA_SPEC.md加载对应业务线的取数清单"""
    dataspec_path = BLACKBOARD / 'DATA_SPEC.md'
    if not dataspec_path.exists():
        return {'error': 'DATA_SPEC.md not found'}

    # 简化版：返回业务线对应的Agent列表
    from orchestrate import BIZ_AGENT_MAP
    agents = BIZ_AGENT_MAP.get(biz_type, {})
    return {
        'biz_type': biz_type,
        'required_agents': agents.get('required', []),
        'optional_agents': agents.get('optional', []),
    }


# ============================================================
#  Phase 3: 多Agent分析
# ============================================================
def phase_analyze(project_slug):
    """准备多Agent分析环境，生成spawn plan"""
    project_dir = PROJECTS / project_slug
    status = _load_status(project_dir)

    if 'plan' not in status.get('phases_completed', []):
        return {'status': 'error', 'message': '请先完成实施方案（plan）'}

    # ✅ 人工签核检查：实施方案需项目经理确认
    signoffs = status.get('signoffs', {})
    if not signoffs.get('plan_approved'):
        return {
            'status': 'blocked',
            'message': '⚠️ 人工签核未完成：实施方案需项目经理确认后才能启动Agent分析。\n运行: python workflow_engine.py signoff --project ' + project_slug + ' --gate plan_approved --approved-by "<你的名字>"',
            'missing_gate': 'plan_approved',
            'required_for': 'analyze',
        }

    status['current_phase'] = 'analyze'

    # 调用audit-blackboard的prepare
    biz_type = status['biz_type']
    try:
        sys.path.insert(0, str(BLACKBOARD))
        from orchestrate import BIZ_AGENT_MAP
        agents_config = BIZ_AGENT_MAP.get(biz_type, BIZ_AGENT_MAP['special_fund'])
    except ImportError:
        agents_config = {'required': ['data_scout','law_inspector','report_writer','review_sentinel'], 'optional': []}

    # 模型路由推荐（按Agent分配，已修正：境外模型→国内合规替代）
    model_routing = {
        'data_scout':      {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro', 'fallback': 'gemini-3.1-pro-preview'},
        'contract_hound':  {'primary': 'dashscope/qwen3.7-plus', 'fallback': 'custom-cbwyy-top-v1/deepseek-v4-pro'},  # ← sonnet→qwen（数据不出境）
        'bid_hunter':      {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro', 'fallback': 'dashscope/qwen3.7-plus'},
        'law_inspector':   {'primary': 'dashscope/qwen3.7-plus', 'fallback': 'custom-cbwyy-top-v1/deepseek-v4-flash'},
        'performance_evaluator': {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro', 'fallback': 'dashscope/qwen3.7-plus'},
        'report_writer':   {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro', 'fallback': 'dashscope/qwen3.7-plus'},
        'review_sentinel': {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro', 'fallback': 'dashscope/qwen3.7-plus'},  # ← sonnet→v4-pro（数据不出境）
        'workpaper_crafter': {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro', 'fallback': 'dashscope/qwen3.7-plus'},
    }

    spawn_plan = {
        'phase': 'analyze',
        'project': project_slug,
        'biz_type': biz_type,
        'agents': {
            'required': agents_config.get('required', []),
            'optional': agents_config.get('optional', []),
        },
        'model_routing': {k: v for k, v in model_routing.items()
                         if k in agents_config.get('required', []) + agents_config.get('optional', [])},
        'spawn_order': agents_config.get('required', []),  # 必选Agent并行spawn
        'finding_schema': str(BLACKBOARD / 'schemas' / 'finding_schema.json'),
        'raw_data_dir': str(project_dir / 'raw_data'),
        'findings_dir': str(project_dir / 'findings'),
        'task': f"""对{status['biz_name']}项目"{status['display_name']}"执行多Agent并行分析。

已分类资料：{json.dumps(status['files_count']['classified'], ensure_ascii=False)}

请按Agent分工执行分析，每个Agent将发现写入 findings/<agent_name>.json，
使用统一的finding_schema格式。
分析完成后运行 collect 碰撞合并去重。""",
        'next': 'Agent分析完成后，运行: python workflow_engine.py evidence --project ' + project_slug,
    }

    with open(project_dir / 'outputs' / 'spawn_plan_analyze.json', 'w', encoding='utf-8') as f:
        json.dump(spawn_plan, f, ensure_ascii=False, indent=2)

    status['phases_completed'].append('analyze')
    _save_status(project_dir, status)

    return {
        'status': 'ready_to_spawn',
        'phase': 'analyze',
        'project': project_slug,
        'agents_required': agents_config.get('required', []),
        'agents_optional': agents_config.get('optional', []),
        'spawn_plan': spawn_plan,
    }


# ============================================================
#  Phase 4: 取证单与底稿生成
# ============================================================
def phase_evidence(project_slug):
    """基于确认的问题清单生成取证单和底稿"""
    project_dir = PROJECTS / project_slug
    status = _load_status(project_dir)

    findings_dir = project_dir / 'findings'
    collision_dir = project_dir / 'collision'

    # 检查是否有findings
    findings_files = list(findings_dir.glob('*.json')) if findings_dir.exists() else []
    collision_files = list(collision_dir.glob('*.json')) if collision_dir.exists() else []

    if not findings_files and not collision_files:
        return {'status': 'error', 'message': '未找到Agent分析结果，请先执行analyze'}

    status['current_phase'] = 'evidence'

    spawn_plan = {
        'phase': 'evidence',
        'project': project_slug,
        'findings_count': len(findings_files),
        'collision_count': len(collision_files),
        'findings_dir': str(findings_dir),
        'collision_dir': str(collision_dir),
        'output_evidence_dir': str(project_dir / 'outputs' / '取证单'),
        'output_workpaper_dir': str(project_dir / 'outputs' / '底稿'),
        'task': f"""基于已确认的问题清单（存放在findings/和collision/目录），
为每个确认的问题生成：
1. 审计取证单（模板：审计厅格式）
2. 审计工作底稿（模板：审计厅格式）

对每个问题，取证单需包含：
- 审计事项
- 审计发现（问题描述）
- 违反规定（法条引用）
- 问题金额
- 证据附件清单
- 被审计单位意见栏（留白）

底稿需包含：
- 审计目标
- 审计过程（检查方法+抽样范围）
- 审计发现（问题描述+金额+法规）
- 审计结论（定性+处理建议）
- 附件索引（取证单编号+证据清单）""",
        'next': '确认取证单底稿后，运行: python workflow_engine.py report --project ' + project_slug,
    }

    with open(project_dir / 'outputs' / 'spawn_plan_evidence.json', 'w', encoding='utf-8') as f:
        json.dump(spawn_plan, f, ensure_ascii=False, indent=2)

    status['phases_completed'].append('evidence')
    _save_status(project_dir, status)

    return {
        'status': 'ready_to_spawn',
        'phase': 'evidence',
        'project': project_slug,
        'findings_available': len(findings_files) + len(collision_files),
        'spawn_plan': spawn_plan,
    }


# ============================================================
#  Phase 5: 报告撰写
# ============================================================
def phase_report(project_slug):
    """撰写审计报告初稿 + 征求意见稿"""
    project_dir = PROJECTS / project_slug
    status = _load_status(project_dir)

    if 'evidence' not in status.get('phases_completed', []):
        return {'status': 'error', 'message': '请先完成取证底稿（evidence）'}

    # ✅ 人工签核检查：疑点核实需审计组长确认
    signoffs = status.get('signoffs', {})
    if not signoffs.get('analysis_ready'):
        return {
            'status': 'blocked',
            'message': '⚠️ 人工签核未完成：疑点清单需审计组长筛选确认后才能写报告。\n运行: python workflow_engine.py signoff --project ' + project_slug + ' --gate analysis_ready --approved-by "<你的名字>"',
            'missing_gate': 'analysis_ready',
            'required_for': 'report',
        }

    status['current_phase'] = 'report'

    spawn_plan = {
        'phase': 'report',
        'project': project_slug,
        'biz_type': status['biz_type'],
        'biz_name': status['biz_name'],
        'findings_dir': str(project_dir / 'findings'),
        'workpaper_dir': str(project_dir / 'outputs' / '底稿'),
        'evidence_dir': str(project_dir / 'outputs' / '取证单'),
        'output_report_dir': str(project_dir / 'outputs' / '报告'),
        'task': f"""撰写{status['biz_name']}审计报告。

步骤：
1. 汇总所有底稿中的审计发现
2. 按问题类型分组，按重要性排序
3. 按审计报告标准结构组织：
   - 基本情况（从实施方案中取）
   - 审计评价
   - 审计发现及问题（从底稿中取，逐条列出）
   - 审计建议（从问题+法规中生成）
4. 生成初稿
5. 调用review_sentinel执行15维深度复核
6. 根据复核意见修改
7. 生成征求意见稿（附征求意见函）""",
        'review_config': {
            'mode': 'comprehensive',  # 15维深度复核
            'checklist': [
                '金额合计校验', '日期一致性', '法规引用准确性',
                '报告↔附表一致性', '取证单→报告完整闭环', '全链路金额追踪',
                '问题定性准确性', '建议针对性', '格式规范性',
            ],
        },
        'next': '报告定稿后，运行: python workflow_engine.py archive --project ' + project_slug,
    }

    with open(project_dir / 'outputs' / 'spawn_plan_report.json', 'w', encoding='utf-8') as f:
        json.dump(spawn_plan, f, ensure_ascii=False, indent=2)

    status['phases_completed'].append('report')
    _save_status(project_dir, status)

    return {
        'status': 'ready_to_spawn',
        'phase': 'report',
        'project': project_slug,
        'spawn_plan': spawn_plan,
    }


# ============================================================
#  Phase 6: 反馈闭环归档
# ============================================================
def phase_archive(project_slug):
    """客户确认后，沉淀案例/规则/技能，更新RAG"""
    project_dir = PROJECTS / project_slug
    status = _load_status(project_dir)

    status['current_phase'] = 'archive'

    # ✅ 人工签核检查：归档前必须确认所有问题已客户确认
    signoffs = status.get('signoffs', {})
    if not signoffs.get('report_finalized'):
        return {
            'status': 'blocked',
            'message': '⚠️ 人工签核未完成：请先确认报告已客户确认并定稿。\n运行: python workflow_engine.py signoff --project ' + project_slug + ' --gate report_finalized --approved-by "<你的名字>"',
            'missing_gate': 'report_finalized',
            'required_for': 'archive',
        }

    archive_plan = {
        'phase': 'archive',
        'project': project_slug,
        'biz_type': status['biz_type'],
        'biz_name': status['biz_name'],
        'actions': [
            {
                'step': 'case_extraction',
                'desc': '从确认的问题清单+取证单+底稿中提取结构化案例',
                'output': f"obsidian-vault/cases/{status['biz_name']}/{project_slug}_案例.md",
                'format': '问题表现 → 命中特征 → 检测逻辑 → 证据链 → 报告表述',
            },
            {
                'step': 'rule_extraction',
                'desc': '从案例中按rule-template.md格式提取审计规则',
                'output': f"RONGCE_AI_HUB/rule-library/drafts/{project_slug}_rules.md",
                'grading': 'A底稿级 / B疑点级 / C提示级',
            },
            {
                'step': 'skill_update',
                'desc': '检查是否有新的分析方法/检测模型需要更新到Skill',
                'skills_to_check': _get_relevant_skills(status['biz_type']),
            },
            {
                'step': 'rag_sync',
                'desc': '增量重建RAG索引，将新案例纳入检索范围',
                'script': 'scripts/rag_rebuild.py --incremental',
            },
            {
                'step': 'template_optimize',
                'desc': '更新实施方案模板中的重难点库',
                'target': f"RONGCE_AI_HUB/business-lines/{status['biz_name']}.md",
            },
        ]
    }

    with open(project_dir / 'outputs' / 'archive_plan.json', 'w', encoding='utf-8') as f:
        json.dump(archive_plan, f, ensure_ascii=False, indent=2)

    status['phases_completed'].append('archive')
    _save_status(project_dir, status)

    return {
        'status': 'ready_to_archive',
        'phase': 'archive',
        'project': project_slug,
        'archive_plan': archive_plan,
        'total_actions': len(archive_plan['actions']),
    }


def _get_relevant_skills(biz_type):
    """根据业务类型返回相关技能列表"""
    skill_map = {
        'economic_responsibility': ['audit-jingze', 'cot-capture', 'gov-audit-methodology'],
        'bidding': ['procurement-audit-models', 'bid-document', 'special-bond-audit'],
        'performance': ['perf-audit-checklist', 'forecast-simulation'],
        'special_fund': ['special-fund-audit', 'subsidy-audit'],
        'engineering': ['engineering-audit', 'bim-engineering-audit', 'energy-audit'],
        'soe': ['financial-fraud-detection', 'audit-knowledge-graph'],
        'subsidy': ['subsidy-audit', 'gov-audit-methodology'],
    }
    return skill_map.get(biz_type, ['data-analyst-cn', 'audit-data-analysis-methods'])


# ============================================================
#  人工签核系统（三模型共识P0）
# ============================================================
# 关键节点必须人工签核才能进入下一阶段：
#   plan_approved:    实施方案经项目经理确认
#   analysis_ready:   疑点清单经审计组长筛选
#   report_draft_ok:  报告初稿经项目负责人把关
#   report_finalized: 报告定稿经客户确认
#   archive_approved: 归档材料经质控复核

REQUIRED_SIGNOFFS = {
    'plan': 'plan_approved',       # ②→③：实施方案必须人审
    'analyze': 'analysis_ready',   # ③→④：疑点清单必须人审
    'report': 'report_draft_ok',   # ⑤内部：报告初稿必须人审
    'archive': 'report_finalized', # ⑥：归档前必须客户确认
}


def signoff_gate(project_slug, gate_name, approved_by, notes=''):
    """人工签核：审批通过某个关卡"""
    project_dir = PROJECTS / project_slug
    status = _load_status(project_dir)

    if not status:
        return {'status': 'error', 'message': f'项目"{project_slug}"不存在'}

    signoffs = status.get('signoffs', {})
    signoffs[gate_name] = {
        'approved': True,
        'approved_by': approved_by,
        'approved_at': datetime.now(CST).isoformat(),
        'notes': notes,
    }
    status['signoffs'] = signoffs
    _save_status(project_dir, status)

    # 判断下一步
    next_phase = None
    for phase, gate in REQUIRED_SIGNOFFS.items():
        if gate == gate_name:
            next_phase = phase
            break

    return {
        'status': 'signed_off',
        'project': project_slug,
        'gate': gate_name,
        'approved_by': approved_by,
        'next_phase_unblocked': next_phase,
        'all_signoffs': list(signoffs.keys()),
    }


def check_signoffs(project_slug):
    """检查当前项目的签核状态"""
    project_dir = PROJECTS / project_slug
    status = _load_status(project_dir)

    if not status:
        return {'status': 'error', 'message': f'项目"{project_slug}"不存在'}

    signoffs = status.get('signoffs', {})
    current_phase = status.get('current_phase', 'init')

    checks = {}
    for phase, gate in REQUIRED_SIGNOFFS.items():
        checks[gate] = {
            'required_for': phase,
            'status': '✅ 已完成' if gate in signoffs else '⬜ 待签核',
            'details': signoffs.get(gate, None),
        }

    return {
        'project': project_slug,
        'current_phase': current_phase,
        'signoffs': checks,
    }


# ============================================================
#  项目状态查看
# ============================================================
def show_status(project_slug):
    """查看项目进度"""
    project_dir = PROJECTS / project_slug
    status = _load_status(project_dir)

    if not status:
        return {'status': 'error', 'message': f'项目"{project_slug}"不存在'}

    completed = status.get('phases_completed', [])
    current = status.get('current_phase', 'init')

    # 生成进度条
    phase_order = ['init', 'ocr', 'classify', 'plan', 'analyze', 'evidence', 'report', 'archive']
    progress_bar = []
    for p in phase_order:
        if p in completed:
            progress_bar.append(f"[✅ {PHASES.get(p, {}).get('name', p)}]")
        elif p == current:
            progress_bar.append(f"[🔄 {PHASES.get(p, {}).get('name', p)}]")
        else:
            progress_bar.append(f"[⬜ {PHASES.get(p, {}).get('name', p)}]")

    return {
        'project': project_slug,
        'display_name': status.get('display_name', ''),
        'biz_type': status.get('biz_type', ''),
        'biz_name': status.get('biz_name', ''),
        'current_phase': current,
        'progress': ' → '.join(progress_bar),
        'phases_completed': completed,
        'files_count': status.get('files_count', {}),
        'issues': {
            'total': status.get('issues_total', 0),
            'P0': status.get('issues_P0', 0),
            'P1': status.get('issues_P1', 0),
            'P2': status.get('issues_P2', 0),
        },
        'agents_spawned': status.get('agents_spawned', []),
    }


# ============================================================
#  工具函数
# ============================================================
def _load_status(project_dir):
    status_file = project_dir / 'status.json'
    if not status_file.exists():
        return {}
    with open(status_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_status(project_dir, status):
    status['updated_at'] = datetime.now(CST).isoformat()
    with open(project_dir / 'status.json', 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


# ============================================================
#  CLI入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='融策审计全生命周期工作流引擎')
    subparsers = parser.add_subparsers(dest='command')

    # status
    p_status = subparsers.add_parser('status', help='查看项目进度')
    p_status.add_argument('--project', required=True)

    # init
    p_init = subparsers.add_parser('init', help='初始化项目')
    p_init.add_argument('--name', required=True, help='项目名称')
    p_init.add_argument('--type', required=True, help='业务类型（经责/收支/预算/专项/往来款/招投标/国企/工程/绩效/补贴/能源/成本/预算编制/财评/全咨/结算）')

    # classify
    p_classify = subparsers.add_parser('classify', help='资料智能分类（需先完成OCR）')
    p_classify.add_argument('--project', required=True)

    # ocr
    p_ocr = subparsers.add_parser('ocr', help='OCR预处理（扫描件/图片→文本→结构化提取）')
    p_ocr.add_argument('--project', required=True)

    # plan
    p_plan = subparsers.add_parser('plan', help='生成实施方案与资料清单')
    p_plan.add_argument('--project', required=True)

    # analyze
    p_analyze = subparsers.add_parser('analyze', help='多Agent分析')
    p_analyze.add_argument('--project', required=True)

    # evidence
    p_evidence = subparsers.add_parser('evidence', help='生成取证单和底稿')
    p_evidence.add_argument('--project', required=True)

    # report
    p_report = subparsers.add_parser('report', help='撰写审计报告')
    p_report.add_argument('--project', required=True)

    # archive
    p_archive = subparsers.add_parser('archive', help='反馈闭环归档')
    p_archive.add_argument('--project', required=True)

    # signoff
    p_signoff = subparsers.add_parser('signoff', help='人工签核（通过审批关卡）')
    p_signoff.add_argument('--project', required=True)
    p_signoff.add_argument('--gate', required=True, help='关卡名（plan_approved/analysis_ready/report_draft_ok/report_finalized）')
    p_signoff.add_argument('--approved-by', required=True, help='签核人')
    p_signoff.add_argument('--notes', default='')

    # signoffs
    p_signoffs = subparsers.add_parser('signoffs', help='查看签核状态')
    p_signoffs.add_argument('--project', required=True)

    args = parser.parse_args()

    if args.command == 'init':
        result = phase_init(args.name, args.type)
    elif args.command == 'ocr':
        result = phase_ocr(args.project)
    elif args.command == 'classify':
        result = phase_classify(args.project)
    elif args.command == 'plan':
        result = phase_plan(args.project)
    elif args.command == 'analyze':
        result = phase_analyze(args.project)
    elif args.command == 'evidence':
        result = phase_evidence(args.project)
    elif args.command == 'report':
        result = phase_report(args.project)
    elif args.command == 'archive':
        result = phase_archive(args.project)
    elif args.command == 'signoff':
        result = signoff_gate(args.project, args.gate, getattr(args, 'approved_by', ''), args.notes)
    elif args.command == 'signoffs':
        result = check_signoffs(args.project)
    elif args.command == 'status':
        result = show_status(args.project)
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 非status命令输出下一步指令
    if args.command != 'status' and 'spawn_plan' in result:
        print(f"\n{'='*60}")
        print("  📋 下一步：将上述 spawn_plan 发送给 OpenClaw 主Agent")
        print(f"     说：「按这个spawn plan spawn对应Agent」")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
