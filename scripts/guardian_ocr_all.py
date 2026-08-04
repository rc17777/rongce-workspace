# encoding: utf-8
"""
55本全量OCR守护脚本 v1.0
========================
平头哥指令（2026-08-03）：不关机，尽量把55本书OCR完。
职责：每3分钟检查 nightly_ocr 主进程，挂了自动重启（新配置），直到全部完成。
独立运行（不挂 OpenClaw exec session）。
"""
import os, sys, json, time, subprocess, datetime

sys.stdout.reconfigure(encoding='utf-8')

STATE = r'C:\Users\scrccpa\.openclaw\workspace\scripts\hybrid_ocr_state.json'
PID_FILE = r'C:\Users\scrccpa\.openclaw\workspace\scripts\nightly_ocr.pid'
SOURCE_DIR = r'E:\2026\审计方法&政策文件\审计相关书籍'
LOG = r'C:\Users\scrccpa\.openclaw\workspace\logs\nightly_ocr_guardian.log'
PY = r'C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe'
SCRIPT = r'C:\Users\scrccpa\.openclaw\workspace\scripts\nightly_ocr.py'
WORKDIR = r'C:\Users\scrccpa\.openclaw\workspace'

def log(msg):
    line = f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}'
    print(line, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def pid_alive(pid):
    try:
        r = subprocess.run(['tasklist', '/fi', f'PID eq {pid}', '/fo', 'csv', '/nh'],
                           capture_output=True, text=True, timeout=15)
        return str(pid) in r.stdout
    except Exception:
        return False

def count_done():
    try:
        with open(STATE, encoding='utf-8') as f:
            return len(json.load(f).get('done', []))
    except Exception:
        return 0

def total_pdfs():
    n = 0
    for root, dirs, files in os.walk(SOURCE_DIR):
        for f in files:
            if f.lower().endswith('.pdf') and not f.startswith('~$'):
                n += 1
    return n

def start_ocr():
    ps = (
        f"$p = Start-Process -FilePath '{PY}' "
        f"-ArgumentList '-X','utf8','{SCRIPT}' "
        f"-WorkingDirectory '{WORKDIR}' -WindowStyle Hidden -PassThru; "
        f"Write-Host ('PID=' + $p.Id)"
    )
    r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    out = r.stdout.strip()
    log(f'🚀 启动 nightly_ocr: {out}')
    return out

log('=' * 60)
log('55本全量OCR守护启动 | 目标: 全部完成')
total = total_pdfs()
log(f'源目录PDF总数: {total}, 当前已完成: {count_done()}')

last_report = 0
while True:
    done = count_done()
    # 完成判定
    if done >= total:
        log(f'🎉 全部完成! {done}/{total}')
        break
    
    # 检查主进程
    running = False
    if os.path.exists(PID_FILE):
        try:
            pid = open(PID_FILE).read().strip()
            if pid and pid_alive(pid):
                running = True
                main_pid = pid
        except Exception:
            pass
    
    if not running:
        log(f'⚠️ 主进程不在运行 (已完成 {done}/{total})，自动重启...')
        # 清理过期PID文件
        try:
            os.unlink(PID_FILE)
        except Exception:
            pass
        start_ocr()
        time.sleep(60)  # 给启动时间
    else:
        # 每30分钟报告一次进度
        now = time.time()
        if now - last_report > 1800:
            log(f'📊 进行中: {done}/{total} (主进程 {main_pid} 正常)')
            last_report = now
    
    time.sleep(180)  # 3分钟一轮
