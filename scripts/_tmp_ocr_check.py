# -*- coding: utf-8 -*-
"""OCR 进度快查"""
import sys, os, json, glob, datetime, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ws = r'C:\Users\scrccpa\.openclaw\workspace'

print('--- 运行中的 python 进程 ---')
r = subprocess.run(['powershell', '-NoProfile', '-Command',
    "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,StartTime,CPU | Format-Table -AutoSize"],
    capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout or '(无 python 进程)')

print('--- output_new 批次 ---')
for pf in sorted(glob.glob(os.path.join(ws, 'temp_ocr', 'output_new', '*', '_progress.json'))):
    d = json.load(open(pf, encoding='utf-8'))
    batch = d.get('label', os.path.basename(os.path.dirname(pf)))
    done = len(d.get('done', [])); total = d.get('total', 0)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(pf)).strftime('%m-%d %H:%M')
    pct = done/total*100 if total else 0
    print(f'  {batch:<24} {done:>4}/{total:<4} {pct:5.1f}%  更新:{mt}')

print('--- ocr_log.txt 末尾 ---')
t = os.path.join(ws, 'temp_ocr', 'ocr_log.txt')
if os.path.exists(t):
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(t)).strftime('%m-%d %H:%M')
    print(f'  (最后更新 {mt})')
    lines = open(t, encoding='utf-8', errors='replace').read().splitlines()
    for l in lines[-10:]:
        print(' ', l)
