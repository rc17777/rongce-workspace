"""
Single robust OCR runner - resumes from progress.json, processes all remaining pages.
"""
import os, sys, json, base64, time

sys.stdout.reconfigure(encoding='utf-8')

# --- Config ---
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    config = json.load(f)

# Get qwen key from provider level
api_key = config['models']['providers']['qwen-direct']['apiKey']
base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
model_id = 'qwen3.7-plus'

from openai import OpenAI
client = OpenAI(api_key=api_key, base_url=base_url)

PAGES_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\pages'
OUTPUT_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output'

def ocr_page(image_path):
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{'role': 'user', 'content': [
            {'type': 'text', 'text': '请OCR识别这张扫描文档图片中的所有文字，逐字输出，不要总结、不要解释、不要遗漏任何内容。保持原文格式。'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
        ]}],
        max_tokens=4096
    )
    return resp.choices[0].message.content

# --- Find all remaining pages ---
all_tasks = []
total_remaining = 0

for doc_name in sorted(os.listdir(PAGES_DIR)):
    doc_dir = os.path.join(PAGES_DIR, doc_name)
    if not os.path.isdir(doc_dir):
        continue
    
    pages = sorted([f for f in os.listdir(doc_dir) if f.endswith('.png')])
    out_dir = os.path.join(OUTPUT_DIR, doc_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # Load progress
    progress_file = os.path.join(out_dir, '_progress.json')
    done = set()
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            done = set(json.load(f).get('done', []))
    
    for pf in pages:
        if pf not in done:
            all_tasks.append((
                doc_name,
                os.path.join(doc_dir, pf),
                os.path.join(out_dir, pf.replace('.png', '.md')),
                os.path.join(out_dir, '_progress.json'),
                pf
            ))
            total_remaining += 1

if not all_tasks:
    print('ALL DONE! Nothing to process.')
    sys.exit(0)

print(f'Remaining: {total_remaining} pages across {len(set(t[0] for t in all_tasks))} documents')
print(f'Starting now...\n')

# --- Process ---
for i, (doc_name, img_path, md_path, prog_path, page_file) in enumerate(all_tasks):
    page_num = int(os.path.splitext(page_file)[0].lstrip('p'))
    print(f'[{i+1}/{total_remaining}] {doc_name} p{page_num:03d}...', end=' ', flush=True)
    
    try:
        text = ocr_page(img_path)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f'# {doc_name} - p{page_num:03d}\n\n{text}')
        
        # Update progress
        done = set()
        if os.path.exists(prog_path):
            with open(prog_path) as f:
                done = set(json.load(f).get('done', []))
        done.add(page_file)
        pages_in_dir = len([x for x in os.listdir(os.path.dirname(img_path)) if x.endswith('.png')])
        with open(prog_path, 'w') as f:
            json.dump({'done': list(done), 'total': pages_in_dir, 'doc': doc_name}, f)
        
        print(f'OK ({len(text)} chars)')
    except Exception as e:
        print(f'ERR: {e}')
        time.sleep(10)
    
    time.sleep(0.5)  # rate limit

print(f'\n=== DONE ===')
