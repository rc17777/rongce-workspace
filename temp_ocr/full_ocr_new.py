"""
Batch OCR for NEW scanned files - resumes from progress.
Usage: python full_ocr_new.py
"""
import os, sys, json, base64, time
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    config = json.load(f)
api_key = config['models']['providers']['qwen-direct']['apiKey']

from openai import OpenAI
client = OpenAI(api_key=api_key, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')

SRC_BASE = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）'
OUT_BASE = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'

# Priority-ordered tasks: (label, src_rel_path, max_pages_optional)
TASKS = [
    ('DRG支付2025', r'DRG支付\2025DRG支付.pdf', None),  # P0: DRG结算通知
    ('稽查4', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查4.pdf', None),  # P0: 现场检查记录
    ('稽查文件3', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件3.pdf', None),  # P0: 现场检查记录
    ('稽查文件', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件.pdf', None),  # P1: 会议纪要
    ('稽查8', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查8.pdf', None),  # P1: 事务中心文件
    ('DRG支付2024', r'DRG支付\2024DRG支付文件2.pdf', None),  # P2: 药品清单
    ('集中采购协议', r'委托支付协议\集中采购协议.pdf', None),  # P2: 采购协议
]

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

for label, rel_path, _ in TASKS:
    pdf_path = os.path.join(SRC_BASE, rel_path)
    if not os.path.exists(pdf_path):
        print(f'SKIP {label}: file not found')
        continue
    
    out_dir = os.path.join(OUT_BASE, label)
    os.makedirs(out_dir, exist_ok=True)
    
    import fitz
    doc = fitz.open(pdf_path)
    total = doc.page_count
    
    progress_file = os.path.join(out_dir, '_progress.json')
    done = set()
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            done = set(json.load(f).get('done', []))
    
    remaining = [i for i in range(total) if f'p{i:04d}.md' not in done and f'p{i:04d}.png' not in done]
    
    if not remaining:
        print(f'DONE {label}: {total}/{total}')
        doc.close()
        continue
    
    print(f'\n=== {label} ({len(done)}/{total} done, {len(remaining)} remaining) ===')
    
    for idx in remaining:
        png_path = os.path.join(out_dir, f'p{idx:04d}.png')
        md_path = os.path.join(out_dir, f'p{idx:04d}.md')
        
        # Extract page if PNG doesn't exist
        if not os.path.exists(png_path):
            mat = fitz.Matrix(1.5, 1.5)
            pix = doc[idx].get_pixmap(matrix=mat)
            pix.save(png_path)
        
        print(f'  [{len(done)+1}/{total}] p{idx:04d}...', end=' ', flush=True)
        
        try:
            text = ocr_page(png_path)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f'# {label} page {idx+1}/{total}\n\n{text}')
            
            done.add(f'p{idx:04d}.md')
            with open(progress_file, 'w') as f:
                json.dump({'done': list(done), 'total': total, 'label': label}, f)
            
            print(f'OK ({len(text)} chars)')
            
            # Clean up PNG to save disk
            if os.path.exists(png_path):
                os.remove(png_path)
                
        except Exception as e:
            print(f'ERR: {e}')
            time.sleep(10)
        
        time.sleep(0.5)
    
    doc.close()
    print(f'DONE {label}: {len(done)}/{total}')

print('\n=== ALL DONE ===')
