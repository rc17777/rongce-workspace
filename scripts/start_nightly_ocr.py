# encoding: utf-8
"""用 Windows 独立进程启动 nightly_ocr，不挂 OpenClaw exec session"""
import subprocess, sys, time
sys.stdout.reconfigure(encoding='utf-8')

PY = r'C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe'
SCRIPT = r'C:\Users\scrccpa\.openclaw\workspace\scripts\nightly_ocr.py'
WORKDIR = r'C:\Users\scrccpa\.openclaw\workspace'

ps = (
    f"$p = Start-Process -FilePath '{PY}' "
    f"-ArgumentList '-X','utf8','{SCRIPT}' "
    f"-WorkingDirectory '{WORKDIR}' -WindowStyle Hidden -PassThru; "
    f"Write-Host ('PID=' + $p.Id)"
)
r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
print('启动输出:', r.stdout.strip())
if r.stderr:
    print('STDERR:', r.stderr[:300])

# 等 15 秒确认进程存活 + 日志有写入
time.sleep(15)
r2 = subprocess.run(['tasklist', '/fi', 'IMAGENAME eq python.exe', '/fo', 'csv', '/nh'],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
print('存活 python 进程:')
print(r2.stdout)
