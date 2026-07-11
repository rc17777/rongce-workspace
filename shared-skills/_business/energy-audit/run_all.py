#!/usr/bin/env python3
"""energy-audit 一键联动"""
import argparse, sys, subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='能源审计全流程')
    parser.add_argument('--energy','-e', required=True, help='能耗统计表')
    parser.add_argument('--carbon','-c', required=True, help='碳排放报告')
    parser.add_argument('--production','-p', help='产量台账')
    parser.add_argument('--sector', default='水泥', help='行业')
    parser.add_argument('--output','-o', default='能源审计报告/')
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).parent
    
    tasks = [('能耗核查', 'dim1_energy_consumption.py',
              ['-e', args.energy, '-o', str(output_dir/'energy_consumption_anomalies.xlsx')]),
             ('碳排放', 'dim2_carbon_emission.py',
              ['-c', args.carbon, '-e', args.energy, '-o', str(output_dir/'carbon_emission_anomalies.xlsx')])]
    
    if args.production:
        tasks[0][2].extend(['-p', args.production])
    if args.sector:
        tasks[0][2].extend(['--sector', args.sector])
    
    results = []
    for label, script, args_list in tasks:
        print(f'\n--- {label} ---')
        r = subprocess.run([sys.executable, str(script_dir/script)] + args_list,
                          capture_output=True, text=True, timeout=120)
        print(r.stdout)
        results.append((label, r.returncode == 0))
    
    ok = sum(1 for _,r in results if r)
    print(f'\n✅ 能源审计: {ok}/{len(results)} → {output_dir.absolute()}')

if __name__ == '__main__': main()
