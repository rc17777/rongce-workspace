#!/usr/bin/env python3
"""budget-audit 一键全流程"""
import argparse, os, sys, subprocess
from pathlib import Path
from datetime import datetime

def find_file(directory, keywords):
    for f in Path(directory).iterdir():
        if f.suffix.lower() in ('.xlsx','.xls'):
            name = f.name.lower()
            if all(k.lower() in name for k in keywords):
                return str(f)
    return None

def main():
    parser = argparse.ArgumentParser(description='收支审计全流程')
    parser.add_argument('--data', required=True, help='审计数据目录')
    parser.add_argument('--output','-o', default='收支审计报告/')
    args = parser.parse_args()
    
    data_dir = Path(args.data)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).parent
    
    tasks = []
    
    # dim1: 预算执行偏差
    budget = find_file(data_dir, ['预算','批复']) or find_file(data_dir, ['预算'])
    final = find_file(data_dir, ['决算'])
    if budget and final:
        tasks.append(('预算执行偏差', str(script_dir/'dim1_budget_variance.py'),
            ['-b', budget, '-d', final, '-o', str(output_dir/'budget_variance_result.xlsx')]))
    else:
        print('  ⚠️ 缺预算/决算数据，跳过预算执行偏差')
    
    # dim2: 三公经费
    pub_exp = find_file(data_dir, ['三公','经费']) or find_file(data_dir, ['公务','接待'])
    if pub_exp:
        tasks.append(('三公经费', str(script_dir/'dim2_public_expense.py'),
            ['-i', pub_exp, '-o', str(output_dir/'public_expense_result.xlsx')]))
    
    # dim3: 非税收入
    non_tax = find_file(data_dir, ['非税','收入']) or find_file(data_dir, ['征缴'])
    if non_tax:
        tasks.append(('非税收入', str(script_dir/'dim3_non_tax.py'),
            ['-i', non_tax, '-o', str(output_dir/'non_tax_result.xlsx')]))
    
    # dim4: 转移支付
    directive = find_file(data_dir, ['转移','支付','下达']) or find_file(data_dir, ['指标','文件'])
    flow = find_file(data_dir, ['拨付','流水']) or find_file(data_dir, ['资金','流水'])
    if directive and flow:
        tasks.append(('转移支付', str(script_dir/'dim4_transfer_payment.py'),
            ['-d', directive, '-f', flow, '-o', str(output_dir/'transfer_result.xlsx')]))
    
    print(f'🚀 收支审计全流程 ({len(tasks)}项)')
    
    results = []
    for name, script, args_list in tasks:
        print(f'\n--- {name} ---')
        r = subprocess.run([sys.executable, script] + args_list,
                          capture_output=True, text=True, timeout=120,
                          cwd=str(script_dir))
        print(r.stdout)
        if r.stderr: print(f'  ⚠️ {r.stderr[:300]}')
        results.append((name, r.returncode == 0))
    
    # Summary
    ok = sum(1 for _,r in results if r)
    print(f'\n✅ 收支审计完成: {ok}/{len(tasks)}模块成功')
    print(f'   报告: {output_dir.absolute()}')
    for name, r in results:
        print(f'   {"✅" if r else "❌"} {name}')

if __name__ == '__main__':
    main()
