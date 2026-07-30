"""
Batch OCR for scanned PDFs using qwen3.7-plus (supports vision).
Usage: python batch_ocr.py --doc "DOC_NAME" [--start N] [--end M]
"""
import os, sys, json, base64, time, argparse

sys.stdout.reconfigure(encoding='utf-8')

# Load config
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    config = json.load(f)

# Find qwen provider with vision support
api_key = None
base_url = None
model_id = None

providers = config['models']['providers']
for pid in ['custom-cbwyy-qwen', 'qwen-direct']:
    if pid in providers:
        pdata = providers[pid]
        api_key = pdata.get('apiKey', '')
        base_url = pdata.get('baseUrl', '')
        for m in pdata.get('models', []):
            if 'qwen' in m.get('id', '').lower():
                model_id = m.get('id', '')
                break
    if api_key and model_id:
        break

if not api_key:
    print('ERROR: no qwen model found')
    sys.exit(1)

print(f'Using: {model_id} @ {base_url}')

from openai import OpenAI
client = OpenAI(api_key=api_key, base_url=base_url)

PAGES_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\pages'
OUTPUT_DIR = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output'

def ocr_page(image_path):
    """Send one image to qwen for OCR."""
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
    
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': '请OCR识别这张扫描文档图片中的所有文字，逐字输出，不要总结、不要解释、不要遗漏任何内容。'},
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
            ]
        }],
        max_tokens=4096
    )
    return resp.choices[0].message.content

def process_doc(doc_name, start=1, end=None):
    doc_dir = os.path.join(PAGES_DIR, doc_name)
    if not os.path.exists(doc_dir):
        print(f'Doc dir not found: {doc_dir}')
        return
    
    pages = sorted([f for f in os.listdir(doc_dir) if f.endswith('.png')])
    if end is None:
        end = len(pages)
    
    out_dir = os.path.join(OUTPUT_DIR, doc_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # Load/save progress
    progress_file = os.path.join(out_dir, '_progress.json')
    done = set()
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            done = set(json.load(f).get('done', []))
    
    pages_to_do = [p for p in pages if p not in done]
    pages_to_do = [p for p in pages_to_do 
                   if start <= int(os.path.splitext(p)[0].lstrip('p')) <= end]
    
    total = len(pages_to_do)
    already = len(done)
    print(f'{doc_name}: {already} done, {total} to go (pages {start}-{end})')
    
    for i, page_file in enumerate(pages_to_do):
        page_path = os.path.join(doc_dir, page_file)
        page_num = int(os.path.splitext(page_file)[0].lstrip('p'))
        
        print(f'[{i+1}/{total}] {page_file}...', end=' ', flush=True)
        
        try:
            text = ocr_page(page_path)
            
            md_file = os.path.join(out_dir, page_file.replace('.png', '.md'))
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f'# {doc_name} - 第{page_num}页\n\n{text}')
            
            done.add(page_file)
            with open(progress_file, 'w') as f:
                json.dump({'done': list(done), 'total': len(pages), 'doc': doc_name}, f)
            
            print(f'OK ({len(text)} chars)')
        except Exception as e:
            print(f'ERR: {e}')
            time.sleep(5)
        
        time.sleep(1)
    
    print(f'\n{doc_name}: DONE ({len(done)}/{len(pages)})')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--doc', required=True)
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=None)
    args = parser.parse_args()
    process_doc(args.doc, args.start, args.end)
