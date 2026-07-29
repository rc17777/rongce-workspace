# -*- coding: utf-8 -*-
"""
Qwen3.7-plus 批量PDF OCR
输入: E:\2026\审计方法&政策文件\杂志资料\  (未OCR的PDF)
输出: D:\openclaw-workspace\knowledge\11-杂志文献\  (MD)
"""
import json, sys, os, base64, io, time, requests, re
sys.stdout.reconfigure(encoding='utf-8')

# === Config ===
with open('C:/Users/scrccpa/.openclaw/openclaw.json', encoding='utf-8') as f:
    cfg = json.load(f)
p = cfg['models']['providers']['custom-cbwyy-qwen']
API_KEY = p['apiKey']
BASE_URL = p['baseUrl']

SRC_DIR = r'E:\2026\审计方法&政策文件\杂志资料'
DST_DIR = r'D:\openclaw-workspace\knowledge\11-杂志文献'
STATUS_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'qwen_ocr_status.json')
STATUS_FILE = os.path.abspath(STATUS_FILE)
MAX_RETRY = 3

import fitz  # PyMuPDF

# === Helpers ===
def get_magazine_name(path):
    for m in ['财政监督', '四川注册会计师', '中国内部审计', '中国注册会计师', '审计观察', '中国审计']:
        if m in path:
            return m
    return '其他'

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

def pdf_page_to_base64(doc, page_num, dpi=200):
    page = doc[page_num]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes('png')
    return base64.b64encode(img_bytes).decode('utf-8')

def ocr_page(doc, page_num):
    """OCR单页并返回(text, elapsed, tokens)"""
    b64 = pdf_page_to_base64(doc, page_num, dpi=200)
    data_url = f'data:image/png;base64,{b64}'
    
    payload = {
        'model': 'qwen3.7-plus',
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {'url': data_url}},
                {'type': 'text', 'text': '完整识别图片中所有中文文字，保持原文段落结构。只输出文字，不要额外说明。'}
            ]
        }],
        'max_tokens': 4096
    }
    
    t0 = time.time()
    r = requests.post(
        BASE_URL.rstrip('/') + '/chat/completions',
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
        json=payload,
        timeout=120
    )
    elapsed = time.time() - t0
    
    if r.status_code != 200:
        return f'[ERROR HTTP {r.status_code}]', elapsed, 0
    
    result = r.json()
    text = result['choices'][0]['message']['content']
    tokens = result.get('usage', {}).get('total_tokens', 0)
    return text, elapsed, tokens

def ocr_pdf(pdf_path):
    """OCR完整PDF，返回Markdown内容"""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    pages_text = []
    total_tokens = 0
    total_time = 0
    errors = 0
    
    for i in range(total_pages):
        for attempt in range(MAX_RETRY):
            try:
                text, elapsed, tokens = ocr_page(doc, i)
                total_time += elapsed
                total_tokens += tokens
                
                if text.startswith('[ERROR'):
                    errors += 1
                    pages_text.append(f'\n\n--- 第{i+1}页 OCR失败 ---\n\n')
                    print(f'    Page {i+1}: ❌ {text[:50]}')
                    break
                else:
                    pages_text.append(text)
                    rate = tokens / elapsed if elapsed > 0 else 0
                    print(f'    Page {i+1}/{total_pages}: ✅ {elapsed:.1f}s, {tokens}tok ({rate:.0f} tok/s)')
                    break
                    
            except Exception as e:
                if attempt < MAX_RETRY - 1:
                    print(f'    Page {i+1}: 重试{attempt+1}/{MAX_RETRY}: {e}')
                    time.sleep(3)
                else:
                    errors += 1
                    pages_text.append(f'\n\n--- 第{i+1}页 OCR失败: {e} ---\n\n')
                    print(f'    Page {i+1}: ❌ 失败: {e}')
    
    doc.close()
    
    # 合并
    full_text = '\n\n'.join(pages_text)
    
    meta = {
        'total_pages': total_pages,
        'total_tokens': total_tokens,
        'total_time': round(total_time, 1),
        'errors': errors,
    }
    
    return full_text, meta

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {'done': [], 'failed': [], 'in_progress': None}

def save_status(status):
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

# === Main ===
def main():
    # Collect PDFs that need OCR
    all_pdfs = []
    for root, dirs, files in os.walk(SRC_DIR):
        for f in files:
            if f.lower().endswith('.pdf') and not f.startswith('~$'):
                all_pdfs.append(os.path.join(root, f))
    
    all_pdfs.sort()
    print(f'找到 {len(all_pdfs)} 个PDF')
    
    # Load progress
    status = load_status()
    done_set = set(status.get('done', []))
    failed_set = set(status.get('failed', []))
    
    pending = [p for p in all_pdfs if p not in done_set]
    print(f'已完成: {len(done_set)}, 剩余: {len(pending)}\n')
    
    if not pending:
        print('全部完成！')
        return
    
    for pdf_path in pending:
        rel = os.path.relpath(pdf_path, SRC_DIR)
        mag = get_magazine_name(pdf_path)
        
        # Output path
        out_dir = os.path.join(DST_DIR, mag)
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        out_name = sanitize_filename(base) + '.md'
        out_path = os.path.join(out_dir, out_name)
        
        print(f'\n{"="*60}')
        print(f'[{mag}] {base}')
        print(f'  PDF: {pdf_path}')
        print(f'  大小: {os.path.getsize(pdf_path)/1024/1024:.1f} MB')
        
        # Check if MD already exists
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f'  ⏭ MD已存在 ({os.path.getsize(out_path)/1024:.0f} KB)，跳过')
            done_set.add(pdf_path)
            status['done'] = list(done_set)
            save_status(status)
            continue
        
        t_pdf_start = time.time()
        text, meta = ocr_pdf(pdf_path)
        t_elapsed = time.time() - t_pdf_start
        
        # Build YAML frontmatter
        yaml = [
            '---',
            f'title: "{base}"',
            f'magazine: "{mag}"',
            f'source: "{rel}"',
            f'type: magazine',
            f'ocr_model: qwen3.7-plus',
            f'ocr_date: {time.strftime("%Y-%m-%d %H:%M")}',
            f'ocr_pages: {meta["total_pages"]}',
            f'ocr_tokens: {meta["total_tokens"]}',
            f'ocr_time: {meta["total_time"]}s',
            '---',
            '',
        ]
        md_content = '\n'.join(yaml) + '\n' + text
        
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        md_size = os.path.getsize(out_path)
        
        print(f'  🏁 完成: {t_elapsed:.0f}s, {meta["total_tokens"]}tok, {md_size/1024:.0f}KB')
        print(f'  📄 {out_path}')
        
        if meta['errors'] > 0:
            print(f'  ⚠️ {meta["errors"]}/{meta["total_pages"]}页失败')
        
        # Update status
        if meta['errors'] < meta['total_pages']:
            done_set.add(pdf_path)
            failed_set.discard(pdf_path)
        else:
            failed_set.add(pdf_path)
        
        status['done'] = list(done_set)
        status['failed'] = list(failed_set)
        save_status(status)
        
        # 打印汇总
        done_count = len(done_set)
        print(f'\n  📊 进度: {done_count}/{len(all_pdfs)}  ({done_count/len(all_pdfs)*100:.0f}%)')
    
    print(f'\n{"="*60}')
    print(f'全部完成! {len(done_set)}/{len(all_pdfs)}')
    if failed_set:
        print(f'失败: {len(failed_set)}个')
        for f in failed_set:
            print(f'  - {f}')
    
    # 重建RAG索引建议
    print(f'\nTip: 完成后运行 python scripts/rag_rebuild.py 更新RAG索引')

if __name__ == '__main__':
    main()
