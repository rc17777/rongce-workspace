#!/usr/bin/env python3
"""special-fund-audit 一键联动"""
import argparse, sys, subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='政府资金专项审计全流程')
    parser.add_argument('--data', required=True, help='审计数据目录')
    parser.add_argument('--output','-o', default='专项审计报告/')
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
        ('社保', 'dim1_social_security.py', find(['社保','参保']), ['-i']),
        ('教育', 'dim2_education.py', find(['教育']), ['-i']),
        ('民政', 'dim3_civil_relief.py', find(['救济','民政']), ['-r']),
        ('保障房', 'dim4_housing.py', find(['保障房','住房']), ['-i']),
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
    print(f'\n✅ 专项审计: {ok}/{len(results)} → {output_dir.absolute()}')

if __name__ == '__main__': main()
