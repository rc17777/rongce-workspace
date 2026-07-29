# encoding: utf-8
import os, json, subprocess, sys

# Discover path without hardcoding Chinese (avoids shell encoding issues)
BASE = r'E:\2026'
# Find directory containing "审计方法"
subdirs = [d for d in os.listdir(BASE) if '审计方法' in d]
if not subdirs:
    print('ERROR: Directory not found')
    sys.exit(1)
BOOKS_DIR = os.path.join(BASE, subdirs[0], '审计相关书籍')
print(f'Books dir: {BOOKS_DIR}', flush=True)

# Find smallest PDF (recursive)
pdfs = []
for root, dirs, files in os.walk(BOOKS_DIR):
    for f in files:
        if f.endswith('.pdf') and not f.startswith('~$'):
            fp = os.path.join(root, f)
            pdfs.append((fp, f, os.path.getsize(fp)))
pdfs.sort(key=lambda x: x[2])

if not pdfs:
    print('ERROR: No PDFs found')
    sys.exit(1)

smallest = pdfs[0]
print(f'Test PDF: {smallest[1]} ({smallest[2]/1024/1024:.1f}MB)', flush=True)

# Write config
CFG = r'C:\Users\scrccpa\.openclaw\workspace\temp_paddle_config.json'
RESULT = r'C:\Users\scrccpa\.openclaw\workspace\temp_paddle_result.json'
cfg = {'pdf_path': smallest[0], 'output_json': RESULT}
with open(CFG, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

# Run worker
PADDLE_PYTHON = r'C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe'
WORKER = r'C:\Users\scrccpa\.openclaw\workspace\scripts\paddle_batch_worker.py'

print('Launching PaddleOCR worker...', flush=True)
proc = subprocess.run(
    [PADDLE_PYTHON, WORKER, CFG],
    capture_output=True, text=True, timeout=7200,
    encoding='utf-8', errors='replace'
)

for line in proc.stdout.split('\n'):
    if line.strip():
        print(line, flush=True)
if proc.stderr:
    print('STDERR:', proc.stderr[:500], flush=True)

# Parse result
if os.path.exists(RESULT) and os.path.getsize(RESULT) > 0:
    with open(RESULT, encoding='utf-8') as f:
        data = json.load(f)
    print(f'\nDone: {data["total_pages"]} pages, {data["total_chars"]} chars, '
          f'confidence {data["avg_confidence"]:.2%}, {data["total_time"]}s', flush=True)
    high = sum(1 for r in data['results'] if r['confidence'] >= 0.90)
    mid = sum(1 for r in data['results'] if 0.70 < r['confidence'] < 0.90)
    low = sum(1 for r in data['results'] if r['confidence'] <= 0.70)
    print(f'Quality: High(>=90%): {high} | Mid: {mid} | Low(<=70%): {low}', flush=True)
else:
    print('ERROR: No result file', flush=True)
