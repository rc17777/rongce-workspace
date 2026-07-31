"""OCR sample pages from new scans using qwen API."""
import os, sys, json, base64, time
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    config = json.load(f)
api_key = config['models']['providers']['qwen-direct']['apiKey']

from openai import OpenAI
client = OpenAI(api_key=api_key, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')

base = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\pages_new'
out = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
os.makedirs(out, exist_ok=True)

# Sample first page of each
for d in sorted(os.listdir(base)):
    dp = os.path.join(base, d)
    p01 = os.path.join(dp, 'p01.png')
    if not os.path.exists(p01):
        continue
    
    md_path = os.path.join(out, f'{d}_p01.md')
    if os.path.exists(md_path):
        with open(md_path, encoding='utf-8') as f:
            txt = f.read()
        print(f'SKIP {d} (already done, {len(txt)} chars)')
        continue
    
    with open(p01, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
    
    print(f'OCR {d}...', end=' ', flush=True)
    try:
        resp = client.chat.completions.create(
            model='qwen3.7-plus',
            messages=[{'role': 'user', 'content': [
                {'type': 'text', 'text': 'OCR识别这张扫描文档的全部文字，特别注意标题、文号、发文单位、表格标题。逐字输出不要总结。'},
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}}
            ]}],
            max_tokens=4096
        )
        text = resp.choices[0].message.content
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f'# {d}\n\n{text}')
        preview = text[:200].replace('\n', ' | ')
        print(f'OK: {preview}')
    except Exception as e:
        print(f'ERR: {e}')
    time.sleep(1)

print('\nDone.')
