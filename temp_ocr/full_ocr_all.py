# -*- coding: utf-8 -*-
"""
全量OCR脚本 v3 — 小文件优先 + 断点续跑
扫描全部源PDF，按大小排序，跳过已完成的
"""
import os, sys, json, base64, time, traceback, re, gc
sys.stdout.reconfigure(encoding='utf-8')
import fitz  # 顶层导入，避免循环加载

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    api_key = json.load(f)['models']['providers']['qwen-direct']['apiKey']

from openai import OpenAI
import httpx
client = OpenAI(
    api_key=api_key,
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    timeout=httpx.Timeout(180.0, connect=30.0, read=180.0, write=60.0),
    max_retries=0
)

SRC = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）'
OUT = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
LOG_FILE = os.path.join(os.path.dirname(OUT), 'ocr_log.txt')

def log(msg):
    ts = time.strftime('%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

def sanitize_label(filename):
    """从文件名生成合法的输出目录名"""
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    return name.strip()[:60]  # 去掉首尾空格

def ocr_page(img_path):
    with open(img_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
    resp = client.chat.completions.create(
        model='qwen3.7-plus',
        messages=[{'role': 'user', 'content': [
            {'type': 'text', 'text': 'OCR识别扫描文档全部文字，逐字输出不要总结。注意表格结构用制表符保留。'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
        ]}],
        max_tokens=4096
    )
    return resp.choices[0].message.content

# ─── 扫描全部源PDF ───
log('=== 扫描源PDF ===')
all_pdfs = []
for root, dirs, files in os.walk(SRC):
    for f in files:
        if f.lower().endswith('.pdf'):
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            all_pdfs.append((sz, f, fp))

all_pdfs.sort()
log(f'共 {len(all_pdfs)} 个PDF')

# ─── 检查已有进度 ───
existing = {}
for d in os.listdir(OUT):
    dp = os.path.join(OUT, d)
    if not os.path.isdir(dp): continue
    pf = os.path.join(dp, '_progress.json')
    if os.path.exists(pf):
        try:
            p = json.load(open(pf, encoding='utf-8'))
            done = set(p.get('done', []))
            total = p.get('total', 0)
            if len(done) >= total and total > 0:
                existing[d] = {'done': done, 'total': total, 'complete': True}
            else:
                existing[d] = {'done': done, 'total': total, 'complete': False}
        except:
            pass

# ─── 匹配PDF到已有目录 ───
# 已知映射: PDF文件名关键词 → 输出目录
known_map = {
    '稽查4.pdf': '稽查4', '稽查8.pdf': '稽查8', '稽查文件3.pdf': '稽查文件3',
    '稽查文件.pdf': '稽查文件', '2025DRG': 'DRG支付2025', '2024DRG': 'DRG支付2024',
    '集中采购协议': '集中采购协议',
}

def find_existing_dir(pdf_name):
    for keyword, dirname in known_map.items():
        if keyword in pdf_name and dirname in existing:
            return dirname
    label = sanitize_label(pdf_name)
    return label if label in existing else None

# ─── 构建队列 ───
queue = []
for sz, name, path in all_pdfs:
    label = find_existing_dir(name)
    if label and existing.get(label, {}).get('complete'):
        continue  # 已完成，跳过
    queue.append((sz, name, path, label))

log(f'待处理: {len(queue)} 本')
total_mb = sum(sz/1024/1024 for sz,_,_,_ in queue)
log(f'总大小: {total_mb:.0f}MB，预估 ~{total_mb*0.4/60:.0f} 小时')

# ─── 逐本处理 ───
import fitz
stats = {'done': 0, 'pages': 0, 'failed': 0}

for sz, name, path, existing_label in queue:
    try:
        if not os.path.exists(path):
            log(f'SKIP {name}: file not found')
            continue

        label = existing_label or sanitize_label(name)
        out_dir = os.path.join(OUT, label)
        os.makedirs(out_dir, exist_ok=True)

        doc = fitz.open(path)
        total = doc.page_count

        # 加载已有进度
        progress_file = os.path.join(out_dir, '_progress.json')
        done = set()
        if os.path.exists(progress_file):
            try:
                with open(progress_file, encoding='utf-8') as f:
                    done = set(json.load(f).get('done', []))
            except:
                pass

        remaining = [i for i in range(total) if f'p{i:04d}.md' not in done]

        if not remaining:
            log(f'DONE {label}: {total}/{total}')
            doc.close()
            stats['done'] += 1
            continue

        est_min = len(remaining) * 0.5  # ~30s/page
        log(f'=== {label} ({len(done)}/{total}, {len(remaining)} left, ~{est_min:.0f}min, {sz/1024/1024:.1f}MB) ===')

        for idx in remaining:
            png_path = os.path.join(out_dir, f'p{idx:04d}.png')
            md_path = os.path.join(out_dir, f'p{idx:04d}.md')

            if not os.path.exists(png_path):
                try:
                    mat = fitz.Matrix(1.5, 1.5)
                    pix = doc[idx].get_pixmap(matrix=mat)
                    pix.save(png_path)
                except Exception as e:
                    log(f'  p{idx:04d} RENDER_ERR: {e}')
                    time.sleep(5)
                    continue

            text = None
            for attempt in range(3):
                try:
                    text = ocr_page(png_path)
                    break
                except Exception as e:
                    err = str(e)[:80]
                    log(f'  p{idx:04d} ERR(a{attempt+1}/3): {err}')
                    time.sleep(20 * (attempt + 1))

            if text is None:
                log(f'  p{idx:04d} SKIP (3 fails)')
                stats['failed'] += 1
                time.sleep(5)
                continue

            try:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f'# {label} page {idx+1}/{total}\n\n{text}')
                done.add(f'p{idx:04d}.md')
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump({'done': list(done), 'total': total, 'label': label}, f)
                stats['pages'] += 1
                if os.path.exists(png_path):
                    os.remove(png_path)
            except Exception as e:
                log(f'  p{idx:04d} WRITE_ERR: {e}')
                time.sleep(5)

            time.sleep(0.5)

        doc.close()
        del doc
        log(f'DONE {label}: {len(done)}/{total}')
        stats['done'] += 1
        gc.collect()  # 每本后强制回收内存
        
        # 内存超2GB自动重启
        import psutil
        mem = psutil.Process().memory_info().rss / 1024 / 1024 / 1024
        if mem > 2.0:
            log(f'⚠️ 内存 {mem:.1f}GB 超限，保存进度后自动退出（重启可续跑）')
            time.sleep(3)
            sys.exit(0)

    except Exception as e:
        log(f'CRASH {name}: {traceback.format_exc()[:300]}')
        time.sleep(10)

log(f'=== 全部完成: {stats["done"]}本, {stats["pages"]}页, 失败{stats["failed"]}页 ===')
