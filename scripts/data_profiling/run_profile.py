# -*- coding: utf-8 -*-
"""
数据剖析统一入口 v0.1
一键四件套：建档 → 口径检查 → 数据理解 → 智能分类
用法: python run_profile.py --source "data.xlsx" --project pidou_2026 --mode full
"""
import sys, os, json, argparse
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent

# 导入各模块
sys.path.insert(0, str(HERE))
from profile_builder import build_profile
from caliber_checker import run_caliber_check, print_report
from data_understanding_base import run_full_pipeline as run_understanding
from smart_classify import run_full_pipeline as run_classify, load_from_excel

def main():
    p = argparse.ArgumentParser(description='审盾数据剖析四件套 v0.1')
    p.add_argument('--source', help='Excel/CSV 数据源路径')
    p.add_argument('--project', required=True, help='项目标识 (如 pidou_2026)')
    p.add_argument('--client', default='', help='委托方')
    p.add_argument('--year', type=int, default=2026, help='年度')
    p.add_argument('--type', default='绩效评价', dest='audit_type', help='审计类型')
    p.add_argument('--label', required=True, help='数据集标签 (如 运行经费)')
    p.add_argument('--classify-col', help='智能分类列名')
    p.add_argument('--report', help='要检查的报告 docx 路径')
    p.add_argument('--mode', default='full', choices=['profile_only', 'understand_only', 'classify_only', 'check_only', 'full'],
                   help='运行模式')
    p.add_argument('--confirmed-by', default='', help='口径确认人')
    
    args = p.parse_args()
    
    out_dir = HERE / 'profiles' / args.project
    out_dir.mkdir(parents=True, exist_ok=True)
    
    profile_path = None
    rows = None
    
    # ─── Step 1: 建档 ────────────────────────
    if args.mode in ('profile_only', 'full') and args.source:
        print('='*60)
        print('  📋 Step 1/4: 构建数据理解档案')
        print('='*60)
        profile, pp = build_profile(
            args.source, args.project, args.project, args.client,
            args.year, args.audit_type, args.label, args.confirmed_by
        )
        profile_path = str(pp)
        print()
    
    # ─── Step 2: 数据理解底座 ────────────────
    if args.mode in ('understand_only', 'full') and args.source:
        print('='*60)
        print('  🔬 Step 2/4: 数据理解底座分析')
        print('='*60)
        run_understanding(args.source, f'{args.project}/{args.label}', str(out_dir / 'understanding'))
        print()
    
    # ─── Step 3: 智能分类 ────────────────────
    if args.mode in ('classify_only', 'full') and args.source and args.classify_col:
        print('='*60)
        print('  🏷️ Step 3/4: 智能分类三步法')
        print('='*60)
        rows = load_from_excel(args.source)
        if rows:
            run_classify(rows, args.classify_col, str(out_dir / 'classify'), args.label)
        print()
    
    # ─── Step 4: 口径检查 ────────────────────
    if args.mode in ('check_only', 'full') and args.report:
        print('='*60)
        print('  📐 Step 4/4: 口径一致性检查')
        print('='*60)
        result = run_caliber_check(
            str(out_dir), 
            args.report, 
            project_label=f'{args.project}/{args.label}'
        )
        print_report(result)
        # 保存
        check_path = out_dir / 'caliber_checks' / f'{args.label}_check_report.json'
        check_path.parent.mkdir(parents=True, exist_ok=True)
        with open(check_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f'\n  💾 检查报告已保存: {check_path}\n')
    
    # ─── Summary ──────────────────────────────
    print('='*60)
    print('  ✅ 四件套完成')
    print(f'   输出: {out_dir}')
    print('='*60)

if __name__ == '__main__':
    main()
