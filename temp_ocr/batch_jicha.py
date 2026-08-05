# -*- coding: utf-8 -*-
"""稽查文件夹剩余9本 批量OCR — 独立进程+看门狗
与 稽查文件3(split_ocr_v2/qwen3.7-plus) 并行, 本脚本用 _ocr_worker(qwen-vl-max)
"""
import os, sys, subprocess, time, json
sys.stdout.reconfigure(encoding='utf-8')

WS = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr'
SRC_DIR = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）\2024-2025违规使用医保基金清单\医保局稽查'
OUT = os.path.join(WS, 'output_new')
LOG = os.path.join(WS, 'watch_batch.log')
WORKER = os.path.join(WS, '_ocr_worker.py')

# 9本待处理: (源文件名, 输出目录名)
tasks = [
    ('医保局稽查13.pdf', '稽查13'),   # 最小先跑,验证链路
    ('医保局稽查7.pdf', '稽查7'),
    ('医保局稽查9.pdf', '稽查9'),
    ('医保局稽查10.pdf', '稽查10'),
    ('医保局稽查文件5.pdf', '稽查文件5'),
    ('医保局稽查11.pdf', '稽查11'),
    ('医保局稽查12.pdf', '稽查12'),
    ('医保局稽查6.pdf', '稽查6'),
    ('医保局稽查文件2.pdf', '稽查文件2'),   # 160MB放最后
]

def log(msg):
    line = f'[{time.strftime("%m-%d %H:%M:%S")}] {msg}'
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

log('=== 稽查9本批量OCR启动 ===')
for name, out_name in tasks:
    pdf = os.path.join(SRC_DIR, name)
    out_dir = os.path.join(OUT, out_name)
    mb = os.path.getsize(pdf) / 1024 / 1024 if os.path.exists(pdf) else 0
    # 确保输出目录存在
    os.makedirs(out_dir, exist_ok=True)
    # 查看已有进度
    pf = os.path.join(out_dir, '_progress.json')
    done, total = 0, 0
    if os.path.exists(pf):
        try:
            p = json.load(open(pf, encoding='utf-8'))
            done, total = len(p.get('done', [])), p.get('total', 0)
        except Exception:
            pass
    left = total - done if total else '?'
    log(f'开始: {out_name} ({mb:.0f}MB, {done}/{total or "?"} done)')
    cmd = [sys.executable, '-X', 'utf8', WORKER, '--pdf', pdf, '--out', out_dir, '--log', LOG]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=21600)  # 6h超时
        el = time.time() - t0
        redo = {}
        if os.path.exists(pf):
            try:
                redo = json.load(open(pf, encoding='utf-8'))
            except:
                pass
        new_done = len(redo.get('done', []))
        log(f'✅ {out_name}: {done}→{new_done} pages ({el:.0f}s)')
        if r.stderr.strip():
            log(f'  stderr: {r.stderr.strip()[:200]}')
    except subprocess.TimeoutExpired:
        log(f'⏰ 超时(>6h): {out_name}')
    except Exception as e:
        log(f'💀 异常: {out_name}: {e}')

log('=== 稽查9本批量OCR结束 ===')
