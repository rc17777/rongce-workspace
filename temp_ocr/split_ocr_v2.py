# -*- coding: utf-8 -*-
"""
稽查文件3拆分补跑 v2 —— 写入正确目录，更强的错误处理
"""
import os, sys, json, base64, time, glob

sys.stdout.reconfigure(encoding='utf-8')

CHUNKS_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\split_chunks'
OUT_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\稽查文件3'
LOG_FILE = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\ocr_split_v2_log.txt'

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    api_key = json.load(f)['models']['providers']['qwen-direct']['apiKey']

from openai import OpenAI
import httpx
client = OpenAI(
    api_key=api_key, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    timeout=httpx.Timeout(180.0, connect=30.0, read=180.0, write=60.0), max_retries=0
)
import fitz

def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

# Load existing done list (filenames like 'p0000.md')
progress_file = os.path.join(OUT_DIR, '_progress.json')
done_set = set()
if os.path.exists(progress_file):
    with open(progress_file, encoding='utf-8') as f:
        done_set = set(json.load(f).get('done', []))
log(f'Existing done pages: {len(done_set)}')

# Get chunks sorted
chunks = sorted(glob.glob(os.path.join(CHUNKS_DIR, '稽查文件3_chunk_*.pdf')))
log(f'Chunks to process: {len(chunks)}')

total_processed = 0
for ci, chunk_path in enumerate(chunks):
    basename = os.path.basename(chunk_path)
    # Parse chunk start page from filename: 稽查文件3_chunk_0000-0049.pdf
    start_page = int(basename.split('_')[-1].split('-')[0])
    
    try:
        doc = fitz.open(chunk_path)
        total_pages = doc.page_count
        skipped = 0
        
        for cp in range(total_pages):
            orig_page = start_page + cp
            
            page_filename = f'p{orig_page:04d}.md'
            if page_filename in done_set:
                skipped += 1
                continue
            
            # Render
            page = doc[cp]
            pix = page.get_pixmap(dpi=200)
            img_path = os.path.join(OUT_DIR, f'_tmp_{orig_page:04d}.png')
            pix.save(img_path)
            
            # OCR
            with open(img_path, 'rb') as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            ok = False
            last_err = ''
            for attempt in range(4):
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
                    ok = True
                    break
                except Exception as e:
                    last_err = str(e)[:120]
                    if attempt < 3:
                        wait = (attempt + 1) * 10
                        time.sleep(wait)
            
            # Cleanup temp
            try: os.remove(img_path)
            except: pass
            
            if not ok:
                log(f'  p{orig_page:04d} FAILED after 4 attempts: {last_err}')
                continue
            
            # Save
            md_path = os.path.join(OUT_DIR, page_filename)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            done_set.add(page_filename)
            total_processed += 1
            
            # Save progress every 10 pages
            if total_processed % 10 == 0:
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump({'done': sorted(done_set), 'total': 506}, f, ensure_ascii=False)
            
            if total_processed % 20 == 0:
                log(f'  Progress: {len(done_set)}/506 ({(len(done_set)/506)*100:.1f}%)')
        
        doc.close()
        log(f'Chunk {ci+1}/{len(chunks)}: {basename} (skipped {skipped}, processed {total_pages-skipped})')
        
    except Exception as e:
        log(f'FATAL chunk {basename}: {e}')
        break

# Final save
with open(progress_file, 'w', encoding='utf-8') as f:
    json.dump({'done': sorted(done_set), 'total': 506}, f)
log(f'DONE. Total pages: {len(done_set)}/506')
