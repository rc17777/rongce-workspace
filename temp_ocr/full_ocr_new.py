"""
Batch OCR for NEW scanned files - small PDFs first, then large.
Usage: python full_ocr_new.py
"""
import os, sys, json, base64, time, traceback
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    config = json.load(f)
api_key = config['models']['providers']['qwen-direct']['apiKey']

from openai import OpenAI
import httpx
client = OpenAI(
    api_key=api_key,
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    timeout=httpx.Timeout(180.0, connect=30.0, read=180.0, write=60.0),
    max_retries=0
)

SRC_BASE = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）'
OUT_BASE = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'

# Ordered by page count: small first, large last
TASKS = [
    ('稽查8', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查8.pdf'),
    ('集中采购协议', r'委托支付协议\集中采购协议.pdf'),
    ('DRG支付2024', r'DRG支付\2024DRG支付文件2.pdf'),
    ('稽查文件', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件.pdf'),
    ('DRG支付2025', r'DRG支付\2025DRG支付.pdf'),
    ('稽查文件3', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件3.pdf'),
    ('稽查4', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查4.pdf'),
]

LOG_FILE = os.path.join(os.path.dirname(OUT_BASE), 'ocr_log.txt')

# Page counts (avoids opening large PDFs just to count)
PAGE_COUNTS = {
    '稽查8': 98,
    '集中采购协议': 164,
    'DRG支付2024': 164,
    '稽查文件': 180,
    'DRG支付2025': 154,
    '稽查文件3': 506,
    '稽查4': 514,
}
ESTIMATED_SECONDS_PER_PAGE = 40

def log(msg):
    ts = time.strftime('%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

def ocr_page(img_path):
    """OCR single page - simple, no threading wrapper"""
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

log('=== OCR 批次启动（小文件优先） ===')

total_estimated = sum(PAGE_COUNTS.get(label, 0) * ESTIMATED_SECONDS_PER_PAGE for label, _ in TASKS)
log(f'预估总耗时: {total_estimated/3600:.1f} 小时')

import fitz

for label, rel_path in TASKS:
    try:
        pdf_path = os.path.join(SRC_BASE, rel_path)
        if not os.path.exists(pdf_path):
            log(f'SKIP {label}: file not found')
            continue
        
        out_dir = os.path.join(OUT_BASE, label)
        os.makedirs(out_dir, exist_ok=True)
        
        doc = fitz.open(pdf_path)
        total = doc.page_count
        
        progress_file = os.path.join(out_dir, '_progress.json')
        done = set()
        if os.path.exists(progress_file):
            try:
                with open(progress_file, encoding='utf-8') as f:
                    done = set(json.load(f).get('done', []))
            except:
                pass
        
        # Only .md counts as done
        remaining = [i for i in range(total) if f'p{i:04d}.md' not in done]
        
        if not remaining:
            log(f'DONE {label}: {total}/{total}')
            doc.close()
            continue
        
        est = len(remaining) * ESTIMATED_SECONDS_PER_PAGE
        log(f'=== {label} ({len(done)}/{total} done, {len(remaining)} left, ~{est/60:.0f}min) ===')
        
        for idx in remaining:
            png_path = os.path.join(out_dir, f'p{idx:04d}.png')
            md_path = os.path.join(out_dir, f'p{idx:04d}.md')
            
            # Extract page if PNG doesn't exist
            if not os.path.exists(png_path):
                try:
                    mat = fitz.Matrix(1.5, 1.5)
                    pix = doc[idx].get_pixmap(matrix=mat)
                    pix.save(png_path)
                except Exception as e:
                    log(f'  p{idx:04d} RENDER_ERR: {e}')
                    time.sleep(5)
                    continue
            
            # Retry up to 3 times with backoff
            text = None
            for attempt in range(3):
                try:
                    text = ocr_page(png_path)
                    break
                except Exception as e:
                    err_msg = str(e)[:100]
                    log(f'  p{idx:04d} ERR(attempt {attempt+1}/3): {err_msg}')
                    time.sleep(20 * (attempt + 1))
            
            if text is None:
                log(f'  p{idx:04d} SKIP (3 fails)')
                time.sleep(5)
                continue
            
            try:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f'# {label} page {idx+1}/{total}\n\n{text}')
                
                done.add(f'p{idx:04d}.md')
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump({'done': list(done), 'total': total, 'label': label}, f)
                
                log(f'  [{len(done)}/{total}] p{idx:04d} OK ({len(text)} chars)')
                
                # Clean up PNG
                if os.path.exists(png_path):
                    os.remove(png_path)
                    
            except Exception as e:
                log(f'  p{idx:04d} WRITE_ERR: {e}')
                time.sleep(5)
            
            time.sleep(0.5)
        
        doc.close()
        log(f'DONE {label}: {len(done)}/{total}')
        
    except Exception as e:
        log(f'CRASH {label}: {traceback.format_exc()[:500]}')
        time.sleep(10)

log('=== 全部批次完成 ===')
