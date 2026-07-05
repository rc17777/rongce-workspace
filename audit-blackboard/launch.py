# -*- coding: utf-8 -*-
"""
融策多Agent审计平台 — 一键启动器

用法:
  python launch.py "校服采购审计" --type "招投标审计"
  python launch.py "经开区绩效评价" --type "绩效评价"
  python launch.py "财政局往来款清理" --type "往来款清理"
"""
import subprocess, sys, os

sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout,'reconfigure') else None

ORCH = os.path.join(os.path.dirname(__file__), 'orchestrate.py')

BIZ_QUICK = {
    '经责':   ('经济责任审计', 'economic_responsibility'),
    '收支':   ('收支审计',       'revenue_expenditure'),
    '预算':   ('预算执行审计',   'budget_execution'),
    '专项':   ('专项审计',       'special_fund'),
    '往来款': ('往来款清理',     'receivables_cleanup'),
    '招投标': ('招投标审计',     'bidding'),
    '国企':   ('国企审计',       'soe'),
    '工程':   ('工程审计',       'engineering'),
    '绩效':   ('绩效评价',       'performance'),
    '补贴':   ('政府补贴审计',   'subsidy'),
    '能源':   ('能源审计',       'energy'),
    '成本':   ('成本效益审计',   'cost_benefit'),
    # 工程咨询
    '预算编制': ('工程预算编制',     'budget_preparation'),
    '财评':   ('财政评审',         'fiscal_review'),
    '全咨':   ('全过程工程咨询',   'full_process_consult'),
    '结算':   ('工程结算审计',     'engineering_settlement'),
}

def main():
    if len(sys.argv) < 2:
        print('\n用法:')
        print('  python launch.py <项目名称> --type <业务类型>')
        print('\n业务类型（可用简称）:')
        for short, (name, _) in BIZ_QUICK.items():
            print(f'  {short:　<4s} → {name}')
        return

    name = sys.argv[1]
    biz_type = None
    for i, arg in enumerate(sys.argv):
        if arg in ('--type','-t') and i+1 < len(sys.argv):
            raw = sys.argv[i+1]
            for short, (biz_name, biz_key) in BIZ_QUICK.items():
                if raw in (short, biz_name):
                    biz_type = biz_key
                    print(f'[OK] 识别业务: {biz_name}')
                    break
            if not biz_type:
                biz_type = raw
                biz_name = raw
                print(f'[!] 未识别类型: {raw}，使用原文')

    biz_name = '通用审计'
    if not biz_type:
        print('[!] 未指定业务类型，使用通用配置')
        biz_type = 'special_fund'

    # Step 0: Token预算检查（如果项目目录有数据）
    project_dir = os.path.join(os.path.dirname(__file__), 'projects', name.replace(' ','_'), 'raw_data')
    if os.path.exists(project_dir) and os.listdir(project_dir):
        print(f'\n{"="*50}')
        print(f'  Step 0: Token预算检查')
        print(f'{"="*50}')
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
            from workflow_with_budget import check_budget
            ok, est = check_budget(
                directory=project_dir,
                task="分析",
                reasoning=True,
                auto_confirm=True,
                quiet=False
            )
            if not ok:
                print('[!] 预算检查未通过，任务已取消')
                return
        except ImportError:
            print('[!] 预算检查模块未找到，跳过')

    # Step 1: 创建项目（传中文业务名）
    print(f'\n{"="*50}')
    print(f'  Step 1/2: 创建项目 [{name}]')
    print(f'{"="*50}')
    subprocess.run([sys.executable, ORCH, 'create', name, '--type', biz_name], check=False)

    # Step 2: 准备Agent任务
    print(f'\n{"="*50}')
    print(f'  Step 2/2: 准备Agent任务')
    print(f'{"="*50}')
    subprocess.run([sys.executable, ORCH, 'prepare', name], check=False)

    pid = name.replace(' ','_')
    print(f'\n{"="*50}')
    print(f'  [OK] 项目 [{name}] 准备就绪')
    print(f'     任务文件: audit-blackboard/projects/{pid}/tasks/spawn_plan.json')
    print(f'{"="*50}')
    print(f'\n下一步：告诉融策右护卫"开始审计 {name}"')
    print(f'右护卫会读取spawn plan → 派出多个Agent → 收集发现 → 碰撞分析')

if __name__ == '__main__':
    main()
