#!/usr/bin/env python3
"""engineering-audit 一键联动"""
import argparse, sys, subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='工程竣工决算审计全流程')
    parser.add_argument('--data', required=True, help='审计数据目录')
    parser.add_argument('--output','-o', default='工程审计报告/')
    args = parser.parse_args()
    
    data_dir = Path(args.data)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).parent
    
    def find(kw):
        for f in data_dir.iterdir():
            if f.suffix.lower() in ('.xlsx','.xls'):
                if all(k.lower() in f.name.lower() for k in kw):
                    return str(f)
        return None
    
    tasks = [
        ('变更签证', 'dim1_change_order.py', find(['变更','签证']), ['-c']),
        ('造价偏差', 'dim2_cost_deviation.py', find(['清单']), ['-b']),
        ('进度款', 'dim3_progress_payment.py', find(['进度款']), ['-p']),
        ('合规性', 'dim4_compliance.py', find(['项目','信息']), ['-i']),
    ]
    
    results = []
    for label, script, data, prefix in tasks:
        if not data:
            print(f'  ⚠️ 缺{label}数据，跳过')
            continue
        args_list = prefix + [data, '-o', str(output_dir/f'{script.split(".")[0]}_anomalies.xlsx')]
        print(f'\n--- {label} ---')
        r = subprocess.run([sys.executable, str(script_dir/script)] + args_list,
                          capture_output=True, text=True, timeout=120)
        print(r.stdout)
        results.append((label, r.returncode == 0))
    
    ok = sum(1 for _,r in results if r)
    print(f'\n✅ 工程审计: {ok}/{len(results)} → {output_dir.absolute()}')

if __name__ == '__main__': main()
