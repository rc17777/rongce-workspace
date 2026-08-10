# -*- coding: utf-8 -*-
"""
OCR Worker — 子进程处理单个PDF
返回码: 0=成功, 42=PDF损坏需跳过, 其他=未知错误
"""
import os, sys, json, base64, time, traceback, re, gc, argparse

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

parser = argparse.ArgumentParser()
parser.add_argument('--pdf', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--log', default=None)
parser.add_argument('--index', type=int, default=0)
parser.add_argument('--total', type=int, default=0)
args = parser.parse_args()

LOG_FILE = args.log

def log(msg):
    ts = time.strftime('%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    if LOG_FILE:
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except:
            pass

pdf_path = args.pdf
out_dir = args.out
base = os.path.basename(pdf_path)

# --- Init ---
try:
    with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
        api_key = json.load(f)['models']['providers']['qwen-direct']['apiKey']
except Exception as e:
    log(f'FATAL: cannot read api key: {e}')
    sys.exit(1)

from openai import OpenAI
import httpx
client = OpenAI(
    api_key=api_key,
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    timeout=httpx.Timeout(180.0, connect=30.0, read=180.0, write=60.0),
    max_retries=0
)

import fitz

# --- 打开PDF ---
try:
    doc = fitz.open(pdf_path)
except Exception as e:
    log(f'⛔ fitz.open 失败 ({base}): {e}')
    sys.exit(42)

total = doc.page_count
log(f'  打开: {base} ({total}页)')

# --- 恢复进度 ---
progress_file = os.path.join(out_dir, '_progress.json')
done = []
if os.path.exists(progress_file):
    try:
        p = json.load(open(progress_file, encoding='utf-8'))
        done = p.get('done', [])
    except:
        pass

# --- 逐页OCR ---
pages_processed = 0
for pg in range(total):
    if pg in done:
        continue
    
    out_md = os.path.join(out_dir, f'p{pg:04d}.md')
    out_png = os.path.join(out_dir, f'p{pg:04d}.png')
    
    # 如果.md已存在，跳过
    if os.path.exists(out_md) and os.path.getsize(out_md) > 50:
        done.append(pg)
        continue
    
    try:
        # 渲染页面为图片
        page = doc[pg]
        pix = page.get_pixmap(dpi=200)
        img_data = pix.tobytes('png')
        
        # 保存PNG
        with open(out_png, 'wb') as f:
            f.write(img_data)
        
        # Base64编码
        img_b64 = base64.b64encode(img_data).decode('ascii')
        
        # 调用Qwen-VL-Max OCR
        r = client.chat.completions.create(
            model='qwen-vl-max',
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}},
                    {'type': 'text', 'text': '请用OCR方式逐字识别这张图片中的所有文字，保持原有格式（标题、段落、表格等）。不要添加任何解释，只输出识别到的文字。'}
                ]
            }],
            max_tokens=4096
        )
        
        text = r.choices[0].message.content
        if not text:
            text = '[空白页]'
        
        with open(out_md, 'w', encoding='utf-8') as f:
            f.write(text)
        
        done.append(pg)
        pages_processed += 1
        
        # 保存进度（每页）
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({'done': done, 'total': total}, f, ensure_ascii=False)
        
        log(f'  {base} p{pg:04d}/{total}')
        
    except Exception as e:
        err = str(e)[:200]
        log(f'  ⚠️ {base} p{pg:04d} ERROR: {err}')
        
        # 如果是API错误，写入错误标记
        with open(out_md, 'w', encoding='utf-8') as f:
            f.write(f'[OCR_ERROR: {err}]')
        
        done.append(pg)
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({'done': done, 'total': total}, f, ensure_ascii=False)
    
    # 每页后 gc
    if pages_processed % 10 == 0:
        gc.collect()

doc.close()
log(f'  ✅ {base}: done={len(done)}/{total}')
print(f'PAGES:{len(done)}')
sys.exit(0)
