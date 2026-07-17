# -*- coding: utf-8 -*-
"""
融策多Agent审计平台 v3.0 — 5坐标系并行穿透引擎
═══════════════════════════════════════════════════

v3.0 核心升级：
  → 新增 penetrate 阶段：自动映射5×6矩阵 + 分配坐标系给Agent + RAG增强
  → Agent同步并行：每个Agent拿到不同的坐标系任务，同时开工
  → 碰撞引擎升级：跨坐标系交叉验证（时空×物理、物理×社会关系等）

工作流：
  create → penetrate → spawn agents(并行) → collect → report

用法：
  python orchestrate.py create "XX局预算执行审计" --type 预算执行
  python orchestrate.py penetrate XX局预算执行审计
  → 输出每个Agent的坐标任务和RAG参考 → 主Agent spawn子Agent(并行)
  → 子Agent完成 → python orchestrate.py collect XX局预算执行审计
  python orchestrate.py report XX局预算执行审计
"""

import os, sys, json, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

# === 配置 ===
BLACKBOARD = Path(__file__).parent
PROJECTS = BLACKBOARD / 'projects'
SCHEMA_DIR = BLACKBOARD / 'schemas'
AGENT_SPECS = BLACKBOARD / 'agent_specs'

# ═══════════════════════════════════════════
# v3.0 新增：5坐标系 → Agent任务映射
# ═══════════════════════════════════════════

# 每个坐标系最擅长处理的Agent + 对应E规则 + RAG查询
COORDINATE_AGENT_MAP = {
    '时空': {
        'primary_agent': 'bid_hunter',
        'fallback_agent': 'data_scout',
        'tools': ['e01_door_access_vs_travel', 'e05_bid_metadata_homology', 'e08_satellite_vs_schedule'],
        'rules': ['E01', 'E02', 'E03', 'E04', 'E05', 'E06', 'E07', 'E08', 'E08b'],
        'method': '将声称的时间地点与独立时空数据（门禁/GPS/卫星/街景）交叉比对，验证"人在哪、事在哪"的真实性。',
        'rag_query': '时空交叉验证 审计方法 卫星影像 门禁打卡',
    },
    '物理': {
        'primary_agent': 'contract_hound',
        'fallback_agent': 'data_scout',
        'tools': ['e13_purchase_sales_inventory', 'e10_material_vs_area', 'e12_concrete_vs_quantity'],
        'rules': ['E09', 'E10', 'E11', 'E12', 'E13', 'E14'],
        'method': '用物理守恒定律验证——声称的产出必然消耗对应物质，用独立供货记录反推真实工程量/销售量。',
        'rag_query': '物理消耗反推 工程量审计 进销存比对 耗材验证',
    },
    '社会关系': {
        'primary_agent': 'law_inspector',
        'fallback_agent': 'contract_hound',
        'tools': ['e15_handler_payee', 'e16_shareholder_penetration', 'e17_family_business'],
        'rules': ['E15', 'E16', 'E17', 'E18'],
        'method': '穿透工商股权、亲属关系、任职历史构建关联图谱，识别未披露的利益输送通道。',
        'rag_query': '工商关联穿透 亲属经商 利益输送 交叉任职 审计',
    },
    '行为': {
        'primary_agent': 'data_scout',
        'fallback_agent': 'bid_hunter',
        'tools': ['e19_approval_pattern', 'e20_bid_price_pattern', 'e21_rotation_pattern'],
        'rules': ['E19', 'E19b', 'E20', 'E21'],
        'method': '分析审批节奏、报价规律、签字习惯中隐藏的非随机模式——人会口头说谎，但行为模式难以伪造。',
        'rag_query': '行为模式分析 审批异常 报价规律 围标检测 审计',
    },
    '时间序列': {
        'primary_agent': 'data_scout',
        'fallback_agent': 'report_writer',
        'tools': ['e23_year_end_spending', 'e24_pre_post_comparison'],
        'rules': ['E22', 'E23', 'E24', 'E24b', 'E24c'],
        'method': '绘制全年/全任期的时间序列曲线，检测Q4突击、截止前冲量、离任前突变等异常节奏——时间轴不会撒谎。',
        'rag_query': '时间序列分析 年末突击 支出节奏 任期对比 审计',
    },
}

# 审计类型 → 适用坐标系（从5×6矩阵提取）
BIZ_COORDINATE_MAP = {
    '预算执行':       ['时空', '物理', '社会关系', '行为', '时间序列'],
    '专项资金':       ['时空', '物理', '社会关系', '行为', '时间序列'],
    '采购':           ['时空', '物理', '社会关系', '行为', '时间序列'],
    '招投标':         ['时空', '物理', '社会关系', '行为', '时间序列'],
    '经济责任':       ['时空', '物理', '社会关系', '行为', '时间序列'],
    '工程':           ['时空', '物理', '社会关系', '行为', '时间序列'],
    '两新补贴':       ['时空', '物理', '社会关系', '行为', '时间序列'],
    '绩效':           ['时空', '物理', '社会关系', '行为', '时间序列'],
    '收支':           ['时空', '物理', '社会关系', '行为', '时间序列'],
    '国企':           ['时空', '物理', '社会关系', '行为', '时间序列'],
}

# 合并到现有orchestrate的BIZ_ALIASES
BIZ_ALIASES = {
    '经济责任审计':'经济责任','经责':'经济责任',
    '收支审计':'收支','收支':'收支',
    '预算执行审计':'预算执行','预算执行':'预算执行',
    '专项审计':'专项资金','专项资金':'专项资金',
    '往来款清理':'收支','往来款':'收支',
    '招投标审计':'招投标','招投标':'招投标',
    '国企审计':'国企','国企':'国企',
    '工程审计':'工程','工程':'工程',
    '绩效评价':'绩效','绩效':'绩效',
    '政府补贴':'两新补贴','补贴':'两新补贴',
    '能源审计':'工程','能源':'工程',
    '成本效益':'绩效','成本':'绩效',
    '预算编制':'工程','财政评审':'工程','全过程':'工程','结算':'工程',
}


# ═══════════════════════════════════════════
# v3.0 核心：penetrate — 生成并行穿透任务
# ═══════════════════════════════════════════

def resolve_biz_type(raw_type):
    """将中文别名解析为标准审计类型"""
    if not raw_type:
        return '预算执行'
    for alias, biz in BIZ_ALIASES.items():
        if alias in raw_type or raw_type in alias:
            return biz
    return raw_type


def query_rag(query_text, top_n=3):
    """查询本地RAG知识库"""
    try:
        result = subprocess.run(
            ['python', '-X', 'utf8', 'scripts/rag_query.py', query_text, '--top', str(top_n)],
            capture_output=True, text=True, timeout=60,
            cwd=str(BLACKBOARD.parent)
        )
        return result.stdout if result.returncode == 0 else ''
    except Exception as e:
        return f'(RAG不可用: {e})'


def penetrate(project_name, biz_type=None, project_dir=None):
    """
    v3.0 penetrate阶段：
    1. 解析审计类型 → 匹配5×6矩阵坐标系
    2. 为每个坐标系分配Agent + E规则 + RAG参考
    3. 生成并行任务文件（每个Agent独立运行，互不依赖）
    4. 输出 spawn plan v3
    """
    if project_dir:
        proj_dir = Path(project_dir)
    else:
        pid = project_name.replace(' ', '_')
        proj_dir = PROJECTS / pid

    if not proj_dir.exists():
        print(f'❌ 项目 [{project_name}] 不存在，请先 create')
        return None

    # 读取项目状态
    sf = proj_dir / 'status.json'
    if sf.exists():
        status = json.loads(sf.read_text(encoding='utf-8'))
        raw_type = status.get('biz_type', biz_type or '')
    else:
        raw_type = biz_type or ''

    biz = resolve_biz_type(raw_type)
    coordinates = BIZ_COORDINATE_MAP.get(biz, ['时空', '物理', '社会关系', '行为', '时间序列'])

    print(f'═══ v3.0 穿透引擎启动 ═══')
    print(f'项目: {project_name}')
    print(f'审计类型: {biz}')
    print(f'适用坐标系: {", ".join(coordinates)}')
    print()

    # 为每个坐标系生成Agent任务
    tasks_dir = proj_dir / 'tasks'
    tasks_dir.mkdir(exist_ok=True)

    parallel_tasks = []
    assigned_agents = set()

    for i, coord in enumerate(coordinates):
        coord_cfg = COORDINATE_AGENT_MAP[coord]
        agent = coord_cfg['primary_agent']
        # 避免同一Agent被重复分配
        if agent in assigned_agents:
            agent = coord_cfg['fallback_agent']
        assigned_agents.add(agent)

        # RAG查询
        print(f'[{i+1}/{len(coordinates)}] {coord}坐标系 → {agent}')
        print(f'  方法: {coord_cfg["method"][:80]}...')
        print(f'  规则: {", ".join(coord_cfg["rules"])}')
        rag_result = query_rag(coord_cfg['rag_query'])
        rag_lines = [l for l in rag_result.split('\n') if l.strip() and not l.startswith('=')]
        rag_summary = ' '.join(rag_lines[:3])[:300] if rag_lines else '(RAG未检索到)'
        print(f'  RAG: {rag_summary[:100]}...')

        # 生成Agent专属任务
        task = {
            'coordinate': coord,
            'agent_id': agent,
            'index': i + 1,
            'method_description': coord_cfg['method'],
            'applicable_rules': coord_cfg['rules'],
            'available_tools': coord_cfg['tools'],
            'rag_reference': rag_summary,
            'spawn_task': f"""你是融策审计黑板的{agent}Agent，负责**{coord}坐标系**的深度穿透审计。

## 你的坐标系

**{coord}** — {coord_cfg['method']}

## 项目背景
- 项目: {project_name}
- 审计类型: {biz}

## 适用筛查规则
{chr(10).join(f'- {r}' for r in coord_cfg['rules'])}

## 可用工具脚本
{chr(10).join(f'- {t}' for t in coord_cfg['tools'])}

## RAG知识库参考
{rag_summary}

## 你的任务
1. 从项目数据中提取{coord}维度的异常信号
2. 对每个异常信号执行深度验证（不要只停在表面）
3. 输出标准格式的审计发现

## 输出要求
- 文件: audit-blackboard/projects/{proj_dir.name}/findings/{agent}_{coord}.json
- 格式: JSON数组，每条遵守finding_schema.json
- 每个发现标注coordinate: "{coord}"
- finding_id格式: F-{datetime.now().year}-{coord[:2]}-{{序号}}
""",
            'output_file': f'findings/{agent}_{coord}.json',
        }
        parallel_tasks.append(task)
        print()

    # 写入穿透计划
    penetrate_plan = {
        'version': '3.0',
        'project': project_name,
        'biz_type': biz,
        'coordinates': coordinates,
        'parallel_tasks': parallel_tasks,
        'total_agents': len(assigned_agents),
        'generated_at': datetime.now(CST).isoformat(),
        'note': '所有Agent任务互不依赖，可完全并行执行。每个Agent负责不同的坐标系。',
    }

    plan_path = tasks_dir / 'penetrate_plan_v3.json'
    plan_path.write_text(json.dumps(penetrate_plan, ensure_ascii=False, indent=2), encoding='utf-8')

    # 更新状态
    if sf.exists():
        status['phase'] = 'penetrated'
        status['penetration'] = {
            'coordinates': coordinates,
            'agents': list(assigned_agents),
            'parallel': True,
        }
        status['logs'].append(f'[{datetime.now(CST).strftime("%H:%M")}] v3.0穿透: {len(coordinates)}坐标系→{len(assigned_agents)}个Agent并行')
        sf.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

    # 打印并行执行指令
    print(f'═══ 并行执行计划 ═══')
    print(f'共 {len(parallel_tasks)} 个坐标系任务 → {len(assigned_agents)} 个Agent 同时开工')
    print()
    print(f'📋 穿透计划: {plan_path}')
    print()
    print(f'主Agent执行:')
    print(f'  读取 {plan_path}')
    print(f'  对以下Agent执行 sessions_spawn（可同时发起）:')
    for t in parallel_tasks:
        print(f'    → {t["agent_id"]} ({t["coordinate"]}坐标系) → {t["output_file"]}')
    print()
    print(f'所有Agent完成后: python orchestrate.py collect {project_name}')

    return penetrate_plan


# ═══════════════════════════════════════════
# v3.0 升级：跨坐标系碰撞
# ═══════════════════════════════════════════

def cross_coordinate_collide(all_findings):
    """
    v3.0 跨坐标系碰撞规则：
    同一实体的发现跨越2+个坐标系 → 多维交叉验证 → 置信度大幅提升
    """
    cross_hits = []

    # 按实体+坐标系分组
    entity_coord_map = {}
    for f_item in all_findings:
        coord = f_item.get('coordinate', '')
        for ent in f_item.get('entities', []):
            ekey = ent.strip().lower()
            entity_coord_map.setdefault(ekey, {}).setdefault(coord, []).append(f_item['finding_id'])

    # 跨坐标系碰撞
    for entity, coord_findings in entity_coord_map.items():
        coords_involved = list(coord_findings.keys())
        if len(coords_involved) >= 2:
            all_fids = []
            for fids in coord_findings.values():
                all_fids.extend(fids)
            level = '🔴高' if len(coords_involved) >= 3 else '🟡中'
            cross_hits.append({
                'rule': '跨坐标系交叉验证',
                'entity': entity,
                'coordinates': coords_involved,
                'findings': all_fids,
                'severity': '高' if len(coords_involved) >= 3 else '中',
                'action': f'实体 [{entity}] 在{", ".join(coords_involved)}坐标系均被标记 → 多维度交叉锁定，置信度大幅提升',
                'timestamp': datetime.now(CST).isoformat(),
            })

    return cross_hits


# ═══════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='融策多Agent审计平台 v3.0 — 5坐标系并行穿透')
    sub = parser.add_subparsers(dest='command')

    # 兼容v2.0的create/collect/status/report（转发给v2脚本）
    p_pen = sub.add_parser('penetrate', help='v3.0 生成5坐标系并行穿透任务')
    p_pen.add_argument('name', help='项目名称')
    p_pen.add_argument('--type', default=None, help='审计类型')
    p_pen.add_argument('--dir', default=None, help='项目目录（覆盖默认路径）')

    p_demo = sub.add_parser('demo', help='演示v3.0并行穿透流程')

    args = parser.parse_args()

    if args.command == 'penetrate':
        penetrate(args.name, args.type, args.dir)

    elif args.command == 'demo':
        # 演示：创建项目 → 穿透 → 展示并行计划
        demo_name = 'demo_预算执行审计'
        demo_dir = PROJECTS / demo_name
        demo_dir.mkdir(parents=True, exist_ok=True)
        for d in ['findings', 'collision', 'workpapers', 'output', 'tasks', 'raw_data']:
            (demo_dir / d).mkdir(exist_ok=True)

        status = {
            'project_id': demo_name, 'project_name': 'XX局2026年度预算执行审计（演示）',
            'biz_type': '预算执行', 'created_at': datetime.now(CST).isoformat(),
            'phase': 'created', 'logs': []
        }
        (demo_dir / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

        print('═══ v3.0 多Agent并行穿透演示 ═══\n')
        print('📁 创建项目: XX局2026年度预算执行审计')
        print('🔍 执行 penetrate...\n')

        plan = penetrate('XX局2026年度预算执行审计（演示）', '预算执行', str(demo_dir))

        if plan:
            print()
            print('═══ 并行执行示意图 ═══')
            print()
            print('  时间轴 →')
            print('  ┌─────────────────────────────────────────┐')
            for t in plan['parallel_tasks']:
                bar = '█' * 30
                print(f'  │ {t["coordinate"]:6s} ({t["agent_id"]:15s}): {bar} │')
            print('  └─────────────────────────────────────────┘')
            print('  ↑ 全部并行，同时完成 ↑')
            print()
            print(f'  碰撞引擎收集 {len(plan["coordinates"])} 个坐标系的发现')
            print(f'  跨坐标系交叉验证 → 多维锁定')
            print()
            print('═══ 完整流程 ═══')
            print('  1. python orchestrate.py create "项目名" --type 审计类型')
            print('  2. python orchestrate.py penetrate 项目名')
            print('  3. 主Agent读取 penetrate_plan_v3.json → sessions_spawn(并行)')
            print('  4. python orchestrate.py collect 项目名')
            print('  5. python orchestrate.py report 项目名')

    else:
        print('融策多Agent审计平台 v3.0')
        print()
        print('v3.0命令（新增）:')
        print('  python orchestrate_v3.py penetrate <项目名>    # 生成5坐标系并行穿透任务')
        print('  python orchestrate_v3.py demo                  # 演示并行流程')
        print()
        print('v2.0命令（兼容，使用原orchestrate.py）:')
        print('  python orchestrate.py create <项目名> --type <类型>')
        print('  python orchestrate.py prepare <项目名> --agents <列表>')
        print('  python orchestrate.py collect <项目名>')
        print('  python orchestrate.py status <项目名>')
        print('  python orchestrate.py report <项目名>')
