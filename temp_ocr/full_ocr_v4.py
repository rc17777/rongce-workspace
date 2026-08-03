# -*- coding: utf-8 -*-
"""
全量OCR脚本 v4 — 子进程沙箱 + 断点续跑
每个PDF用独立子进程处理，crash也不会拖垮主进程
"""
import os, sys, json, time, subprocess, shutil
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SRC = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）'
OUT = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
LOG_FILE = os.path.join(os.path.dirname(OUT), 'ocr_log_v4.txt')
SKIP_FILE = os.path.join(os.path.dirname(OUT), 'skipped_pdfs.txt')
WORKER_SCRIPT = os.path.join(os.path.dirname(OUT), '_ocr_worker.py')

def log(msg):
    ts = time.strftime('%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

log('=== OCR v4 启动（子进程沙箱模式） ===')

# 扫描所有PDF
pdfs = []
for root, dirs, files in os.walk(SRC):
    for f in files:
        if f.lower().endswith('.pdf'):
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            pdfs.append((sz, f, fp, root))

pdfs.sort()  # 小的优先

log(f'找到 {len(pdfs)} 个PDF')

# 扫描已有完成批次
done_set = set()
partial_set = set()  # base -> (done, total)
for d in os.listdir(OUT):
    dp = os.path.join(OUT, d)
    if not os.path.isdir(dp): continue
    pf = os.path.join(dp, '_progress.json')
    if not os.path.exists(pf): continue
    try:
        p = json.load(open(pf, encoding='utf-8'))
        t = p.get('total', 0)
        d_cnt = len(p.get('done', []))
        if d_cnt >= t and t > 0:
            done_set.add(d)
        elif t > 0:
            partial_set[d] = (d_cnt, t)
    except:
        pass

# 读取已跳过列表
skipped = set()
if os.path.exists(SKIP_FILE):
    for line in open(SKIP_FILE, encoding='utf-8').readlines():
        skipped.add(line.strip())

log(f'已完成: {len(done_set)} 本, 部分完成: {len(partial_set)} 本, 已跳过: {len(skipped)} 本')

# 筛选待处理
TO_DO = []
for sz, name, fp, root in pdfs:
    base = os.path.splitext(name)[0]
    # 跳过已完全完成的
    if base in done_set:
        continue
    # 跳过已标记损坏的
    if base in skipped:
        log(f'⏭️ 跳过（已标记损坏）: {name}')
        continue
    TO_DO.append((sz, name, fp, root))

pending_mb = sum(s[0] for s in TO_DO) / 1024 / 1024
log(f'待处理: {len(TO_DO)} 本, 共 {pending_mb:.0f}MB')

# 预估时间（大文件 ~2秒/页，小文件 ~1秒/页，API限流）
def estimate():
    total_pages = 0
    for sz, name, fp, root in TO_DO:
        base = os.path.splitext(name)[0]
        if base in partial_set:
            done_cnt, total = partial_set[base]
            total_pages += (total - done_cnt)
        else:
            # 粗略预估：1MB ≈ 5页
            total_pages += max(1, int(sz / 200000))
    est_sec = total_pages * 2  # 2秒/页含API
    est_h = est_sec / 3600
    return total_pages, est_h

est_pages, est_h = estimate()
log(f'预估剩余页数: ~{est_pages}, 耗时: ~{est_h:.1f}小时 @ 2s/页')

# 主循环
stats = {'ok': 0, 'skip': 0, 'crash': 0, 'pages': 0}
start_time = time.time()
crash_list = []  # 记录crash的文件路径，避免重复尝试

for idx, (sz, name, fp, root) in enumerate(TO_DO):
    base = os.path.splitext(name)[0]
    mb = sz / 1024 / 1024
    
    # 部分完成？传进度
    resume_json = None
    if base in partial_set:
        done_cnt, total = partial_set[base]
        log(f'=== {name} ({done_cnt}/{total} done, {total-done_cnt} left, ~{(total-done_cnt)*2//60:.0f}min, {mb:.1f}MB) ===')
    else:
        log(f'=== {name} (0/? left, ~?min, {mb:.1f}MB) ===')
    
    # 子进程处理
    out_dir = os.path.join(OUT, base)
    os.makedirs(out_dir, exist_ok=True)
    
    cmd = [
        sys.executable, '-X', 'utf8', WORKER_SCRIPT,
        '--pdf', fp,
        '--out', out_dir,
        '--log', LOG_FILE,
        '--index', str(idx),
        '--total', str(len(TO_DO)),
    ]
    
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2小时超时
        elapsed = time.time() - t0
        
        if r.returncode == 0:
            # 成功
            for line in r.stdout.strip().split('\n'):
                if line.startswith('PAGES:'):
                    pages = int(line.split(':')[1])
                    stats['pages'] += pages
                    break
            stats['ok'] += 1
            log(f'✅ DONE: {name} ({elapsed:.0f}s)')
        elif r.returncode == 42:
            # 子进程标记为损坏PDF
            stats['skip'] += 1
            crash_list.append(base)
            with open(SKIP_FILE, 'a', encoding='utf-8') as f:
                f.write(base + '\n')
            log(f'⛔ SKIP (PDF损坏): {name} ({elapsed:.0f}s)')
        else:
            stats['crash'] += 1
            log(f'💀 CRASH (rc={r.returncode}): {name} stderr: {r.stderr[:200]}')
        if r.stderr.strip():
            # 记录stderr
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f'    STDERR: {r.stderr.strip()[:500]}\n')
    except subprocess.TimeoutExpired:
        stats['crash'] += 1
        log(f'💀 TIMEOUT (>7200s): {name} - 跳过')
    except Exception as e:
        stats['crash'] += 1
        log(f'💀 ERROR: {name}: {e}')
    
    # 进度
    elapsed_total = time.time() - start_time
    done_sofar = idx + 1
    rate = elapsed_total / done_sofar if done_sofar > 0 else 0
    remaining = len(TO_DO) - done_sofar
    eta_min = remaining * rate / 60
    log(f'  进度: {done_sofar}/{len(TO_DO)} ({100*done_sofar/len(TO_DO):.0f}%), OK:{stats["ok"]} SKIP:{stats["skip"]} CRASH:{stats["crash"]}, ETA:{eta_min:.0f}min')

log(f'=== 全部完成 ===')
log(f'成功: {stats["ok"]}, 跳过: {stats["skip"]}, 崩溃: {stats["crash"]}, 页数: {stats["pages"]}')
if crash_list:
    log(f'损坏/问题PDF列表:')
    for b in crash_list:
        log(f'  - {b}')
