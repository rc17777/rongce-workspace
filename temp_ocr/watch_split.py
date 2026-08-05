# -*- coding: utf-8 -*-
"""稽查文件3 OCR 看门狗 — 检测 split_ocr_v2 进程,死了自动重启(断点续跑,幂等)
通过 Start-Process 独立启动,脱离 OpenClaw 会话管理"""
import subprocess, sys, time, os, json, datetime

PY = sys.executable
SPLIT = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\split_ocr_v2.py'
SPLIT_DIR = os.path.dirname(SPLIT)
LOG = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\watchdog.log'
PROGRESS = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\稽查文件3\_progress.json'

def log(msg):
    line = f'[{time.strftime("%m-%d %H:%M:%S")}] {msg}'
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def split_running():
    try:
        result = subprocess.run(
            ['wmic', 'process', 'where', "name='python.exe'", 'get', 'commandline', '/format:list'],
            capture_output=True, text=True, timeout=30)
        out = result.stdout or ''
        return 'split_ocr_v2' in out
    except Exception as e:
        log(f'进程检查失败: {e}')
        return True  # 保守:无法检查时当作在跑,避免重复启动

def progress_pages():
    try:
        p = json.load(open(PROGRESS, encoding='utf-8'))
        return len(p.get('done', []))
    except Exception:
        return -1

restarts = 0
last_pages = progress_pages()
log(f'看门狗启动, 当前进度: {last_pages}/506')

while True:
    if not split_running():
        pages = progress_pages()
        log(f'split_ocr_v2 未运行, 当前进度: {pages}/506')
        if pages > last_pages:
            restarts = 0  # 有进展,重置重启计数
        last_pages = pages
        if restarts >= 5:
            log('!!! 连续5次重启无进展, 看门狗退出, 需人工介入')
            break
        try:
            p = subprocess.Popen(
                [PY, '-X', 'utf8', SPLIT],
                cwd=SPLIT_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            restarts += 1
            log(f'已重启 split_ocr_v2, pid={p.pid} (第{restarts}次)')
        except Exception as e:
            log(f'重启失败: {e}')
            time.sleep(300)
            continue
    time.sleep(120)
