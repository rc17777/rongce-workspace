#!/usr/bin/env python3
"""subsidy-audit 三阶段联动"""
import argparse, sys, subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='政府补贴审计全流程')
    parser.add_argument('--declare', required=True, help='补贴申报清册')
    parser.add_argument('--disburse', required=True, help='拨付流水')
    parser.add_argument('--usage', help='使用记录(可选)')
    parser.add_argument('--verify', help='实地核查数据(可选)')
    parser.add_argument('--output','-o', default='补贴审计报告/')
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).parent
    
    tasks = [
        ('申报合规性', 'dim1_declaration.py',
         ['-i', args.declare, '-o', str(output_dir/'subsidy_declaration_anomalies.xlsx')]),
        ('拨付追踪', 'dim2_disbursement.py',
         ['-i', args.disburse, '--declare', args.declare,
          '-o', str(output_dir/'subsidy_disbursement_anomalies.xlsx')]),
    ]
    
    if args.usage:
        cmd = ['-i', args.usage, '-o', str(output_dir/'subsidy_usage_anomalies.xlsx')]
        if args.verify:
            cmd += ['--verify', args.verify]
        tasks.append(('使用核查', 'dim3_usage.py', cmd))
    
    print(f'🚀 政府补贴审计 ({len(tasks)}阶段)')
    results = []
    for name, script, args_list in tasks:
        print(f'\n--- {name} ---')
        r = subprocess.run([sys.executable, str(script_dir/script)] + args_list,
                          capture_output=True, text=True, timeout=120)
        print(r.stdout)
        if r.stderr: print(f'  ⚠️ {r.stderr[:200]}')
        results.append((name, r.returncode == 0))
    
    ok = sum(1 for _,r in results if r)
    print(f'\n✅ 补贴审计完成: {ok}/{len(tasks)}')
    for name, r in results:
        print(f'   {"✅" if r else "❌"} {name}')

if __name__ == '__main__':
    main()
