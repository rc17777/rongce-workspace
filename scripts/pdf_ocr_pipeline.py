# -*- coding: utf-8 -*-
"""
PDF扫描件批量OCR管线
依赖: PaddleOCR 2.7.3 + PyMuPDF (conda env paddleocr)

用法:
  python pdf_ocr_pipeline.py test    # 测试1个PDF
  python pdf_ocr_pipeline.py batch   # 批量处理所有
  python pdf_ocr_pipeline.py status  # 查看进度
"""
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')

PADDLE_PYTHON = r"C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe"
OCR_SCRIPT = os.path.join(os.path.dirname(__file__), "ocr_one_pdf.py")
OCR_OUTPUT = r"C:\Users\scrccpa\.openclaw\workspace\knowledge\magazines_ocr"
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "pdf_ocr_progress.json")
BASE = r"E:\2026\审计方法&政策文件\杂志资料"

def get_all_pdfs():
    pdfs = []
    for root, dirs, files in os.walk(BASE):
        for f in sorted(files):
            if f.endswith('.pdf') and not f.startswith('~$'):
                fp = os.path.join(root, f)
                rel = os.path.relpath(root, BASE)
                mag = rel.split(os.sep)[0] if os.sep in rel else rel
                pdfs.append({
                    'path': fp, 'file': f, 'magazine': mag,
                    'size_mb': round(os.path.getsize(fp) / 1e6, 1)
                })
    return pdfs

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {"done": []}

def save_progress(state):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def ocr_one(pdf_info):
    pdf_path = pdf_info['path']
    pdf_name = pdf_info['file']
    mag = pdf_info['magazine']
    
    print(f"\n  [OCR] {pdf_name} ({pdf_info['size_mb']}MB)...", end="", flush=True)
    start = time.time()
    
    result = subprocess.run(
        [PADDLE_PYTHON, OCR_SCRIPT, pdf_path, mag, OCR_OUTPUT],
        capture_output=True, text=True, timeout=7200,
        encoding='utf-8', errors='replace'
    )
    
    elapsed = time.time() - start
    
    stdout = result.stdout
    stderr = result.stderr
    
    for line in stdout.split('\n'):
        line = line.strip()
        if line.startswith('OCR_RESULT:'):
            outpath = line.split(':', 1)[1].strip()
            print(f" ✅ ({elapsed:.0f}s)", flush=True)
            return {'success': True, 'output': outpath, 'time': elapsed}
    
    # 检查错误
    for line in stderr.split('\n'):
        if 'Error' in line or 'Traceback' in line:
            print(f" ❌")
            print(f"  错误: {line[:200]}", flush=True)
            return {'success': False, 'error': line[:300], 'time': elapsed}
    
    # 无结果标记
    print(f" ⚠️ 无结果标记")
    return {'success': False, 'error': 'no result', 'time': elapsed}

def run_test():
    pdfs = get_all_pdfs()
    if not pdfs:
        print("没有找到PDF")
        return
    smallest = min(pdfs, key=lambda x: x['size_mb'])
    print(f"测试: {smallest['file']} ({smallest['size_mb']}MB) - {smallest['magazine']}")
    print("正在OCR（可能需几分钟）...", flush=True)
    result = ocr_one(smallest)
    if result['success']:
        print(f"✅ 通过！耗时: {result['time']:.0f}s")
        if os.path.exists(result['output']):
            with open(result['output'], 'r', encoding='utf-8') as f:
                c = f.read()
            print(f"识别文字量: {len(c)} 字符")
    else:
        print(f"❌ 失败: {result.get('error', '')}")
    
    # 清理测试文件
    if result.get('output') and os.path.exists(result['output']):
        os.remove(result['output'])

def run_batch():
    pdfs = get_all_pdfs()
    state = load_progress()
    done_paths = set(state.get('done', []))
    
    print(f"共 {len(pdfs)} 个PDF待处理, 已完成 {len(done_paths)}")
    
    for i, pdf in enumerate(pdfs, 1):
        if pdf['path'] in done_paths:
            continue
        
        print(f"[{i}/{len(pdfs)}]", end="")
        result = ocr_one(pdf)
        
        if result['success']:
            done_paths.add(pdf['path'])
            save_progress({"done": list(done_paths)})
        
        remaining = len(pdfs) - len(done_paths)
        print(f"  进度: {len(done_paths)}/{len(pdfs)}, 剩余约{remaining}")
    
    print(f"\n✅ 批量处理完成! {len(done_paths)}/{len(pdfs)}")

def show_status():
    pdfs = get_all_pdfs()
    state = load_progress()
    done = set(state.get('done', []))
    
    print(f"=== PDF OCR 进度 ({len(done)}/{len(pdfs)}) ===")
    for pdf in pdfs:
        status = "✅" if pdf['path'] in done else "⏳"
        print(f"  {status} {pdf['file']} ({pdf['size_mb']}MB)")
    
    ocr_files = []
    ocr_dir = OCR_OUTPUT
    if os.path.exists(ocr_dir):
        for root, dirs, files in os.walk(ocr_dir):
            for f in files:
                ocr_files.append(os.path.join(root, f))
        print(f"\n已输出OCR文件: {len(ocr_files)} 个")

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    
    if cmd == 'test':
        run_test()
    elif cmd == 'batch':
        run_batch()
    elif cmd == 'status':
        show_status()
    else:
        print(__doc__)
