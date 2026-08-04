# -*- coding: utf-8 -*-
"""
稽查文件3拆分补跑脚本
处理11个拆分的chunks，断点续跑
"""
import os, sys, json, base64, time, glob, re

sys.stdout.reconfigure(encoding='utf-8')

# Config
CHUNKS_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\split_chunks'
OUT_BASE = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
LOG_FILE = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\ocr_split_log.txt'
PROGRESS_FILE = os.path.join(CHUNKS_DIR, '_chunk_progress.json')

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
import fitz

def log(msg):
    ts = time.strftime('%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

# Resume progress
done_chunks = []
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, encoding='utf-8') as f:
        done_chunks = json.load(f).get('done', [])

# Main output dir
main_out = os.path.join(OUT_BASE, '医保局稽查文件3')
os.makedirs(main_out, exist_ok=True)

# Get sorted chunks
chunks = sorted(glob.glob(os.path.join(CHUNKS_DIR, '稽查文件3_chunk_*.pdf')))
log(f'Found {len(chunks)} chunks, {len(done_chunks)} already done')

for chunk_path in chunks:
    basename = os.path.basename(chunk_path)
    if basename in done_chunks:
        log(f'SKIP {basename} (already done)')
        continue
    
    log(f'=== Processing {basename} ===')
    try:
        doc = fitz.open(chunk_path)
        total = doc.page_count
        
        # Per-chunk output dir (not really needed, we just want to merge later)
        # We'll save to main_out with original page numbers embedded
        
        progress_file = os.path.join(main_out, f'_progress_{basename}.json')
        done_pages = []
        if os.path.exists(progress_file):
            with open(progress_file, encoding='utf-8') as f:
                done_pages = json.load(f).get('done', [])
        
        for pg in range(total):
            if pg in done_pages:
                continue
            
            # Render page to png
            page = doc[pg]
            pix = page.get_pixmap(dpi=200)
            img_path = os.path.join(main_out, f'_temp_{basename}_{pg:04d}.png')
            pix.save(img_path)
            
            # OCR via Qwen API
            with open(img_path, 'rb') as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            for attempt in range(3):
                try:
                    resp = client.chat.completions.create(
                        model='qwen3.7-plus',
                        messages=[{'role': 'user', 'content': [
                            {'type': 'text', 'text': 'OCR识别此扫描文档的全部文字，逐字输出不要总结。保留表格结构。'},
                            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
                        ]}],
                        max_tokens=4096
                    )
                    text = resp.choices[0].message.content
                    break
                except Exception as e:
                    if attempt < 2:
                        log(f'  p{pg:04d} retry {attempt+1}: {e}')
                        time.sleep(5)
                    else:
                        raise
            
            # Save result (simple page numbering)
            page_label = f'chunk{chunks.index(chunk_path):02d}_p{pg:04d}'
            md_path = os.path.join(main_out, f'{page_label}.md')
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Cleanup temp
            try:
                os.remove(img_path)
            except:
                pass
            
            done_pages.append(pg)
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump({'done': done_pages, 'total': total}, f)
            
            if (len(done_pages) % 10 == 0) or len(done_pages) == total:
                log(f'  {basename}: {len(done_pages)}/{total} ({(len(done_pages)/total)*100:.0f}%)')
        
        doc.close()
        done_chunks.append(basename)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'done': done_chunks, 'total_chunks': len(chunks)}, f)
        log(f'DONE {basename}')
        
    except Exception as e:
        log(f'ERROR {basename}: {e}')
        log(f'Stopping. Resume later from next chunk.')
        break

log(f'=== Complete: {len(done_chunks)}/{len(chunks)} chunks ===')
