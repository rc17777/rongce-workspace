"""
Fast sampler: OCR first 2 pages of each document to identify content.
"""
import os, sys, json, base64, time

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    config = json.load(f)

api_key = config['models']['providers']['qwen-direct']['apiKey']
base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

from openai import OpenAI
client = OpenAI(api_key=api_key, base_url=base_url)

PAGES_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\pages'
OUTPUT_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output'

def ocr_page(image_path):
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
    resp = client.chat.completions.create(
        model='qwen3.7-plus',
        messages=[{'role': 'user', 'content': [
            {'type': 'text', 'text': '请OCR识别这张扫描文档的全部文字，逐字输出不要总结。如果第一页，请特别注意文档标题、文号、发文单位。'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
        ]}],
        max_tokens=4096
    )
    return resp.choices[0].message.content

for doc_name in sorted(os.listdir(PAGES_DIR)):
    doc_dir = os.path.join(PAGES_DIR, doc_name)
    if not os.path.isdir(doc_dir):
        continue
    
    out_dir = os.path.join(OUTPUT_DIR, doc_name)
    os.makedirs(out_dir, exist_ok=True)
    
    pages = sorted([f for f in os.listdir(doc_dir) if f.endswith('.png')])
    sample_pages = pages[:2]  # First 2 pages
    
    # Check if already done
    all_done = True
    for pf in sample_pages:
        md_path = os.path.join(out_dir, pf.replace('.png', '.md'))
        if not os.path.exists(md_path):
            all_done = False
            break
    
    if all_done:
        print(f'SKIP {doc_name} (already sampled)')
        continue
    
    print(f'\n=== {doc_name} ({len(pages)} pages) ===')
    for pf in sample_pages:
        md_path = os.path.join(out_dir, pf.replace('.png', '.md'))
        if os.path.exists(md_path):
            print(f'  {pf}: already done')
            continue
        
        img_path = os.path.join(doc_dir, pf)
        print(f'  {pf}: OCR...', end=' ', flush=True)
        try:
            text = ocr_page(img_path)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f'# {doc_name} - {pf}\n\n{text}')
            # Show first 200 chars as preview
            preview = text[:200].replace('\n', ' | ')
            print(f'OK: {preview}...')
        except Exception as e:
            print(f'ERR: {e}')
        time.sleep(0.5)

print('\n=== SAMPLING COMPLETE ===')
