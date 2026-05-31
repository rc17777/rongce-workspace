"""
补跑剩余12份PDF (顺序OCR) + 全量最终报告
"""
import re, os, sys, json, fitz, subprocess, time, io
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

CONTRACT_DIR = r"C:\Users\scrccpa\Desktop\成都轨道资源资料\业主发送资料\天府广场项目2026年专项审计资料清单（第一批）\1合同协议"
LEDGER_PATH = r"C:\Users\scrccpa\Desktop\成都资源公司=4.30\天府广场合同台账-2024-2025.xlsx"
OUTPUT_DIR = r"D:\openclaw-workspace\output\contract_analysis"
TEMP_DIR = os.path.join(OUTPUT_DIR, "tesseract_batch")
BATCH_OCR = r"D:\openclaw-workspace\scripts\batch_ocr.js"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# 已有结果
existing = set()
for f in os.listdir(TEMP_DIR):
    if f.endswith('_result.json'):
        existing.add(f.replace('_result.json', ''))

# 收集所有PDF
pdf_files = []
for root, dirs, files in os.walk(CONTRACT_DIR):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdf_files.append((os.path.join(root, f), os.path.basename(root), f))

# 找出未处理的
todo = []
for pp, cat, fn in pdf_files:
    safe = re.sub(r'[^\w\-.]', '_', fn)[:40]
    if safe not in existing:
        todo.append((pp, cat, fn, safe))

print(f"需要OCR: {len(todo)}份")
total_img_pages = 0

for idx, (pp, cat, fn, safe) in enumerate(todo):
    t0 = time.time()
    print(f"\n[{idx+1}/{len(todo)}] [{cat}] {fn[:55]}")
    
    # 转图片
    img_dir = os.path.join(TEMP_DIR, safe)
    if not os.path.exists(img_dir):
        os.makedirs(img_dir, exist_ok=True)
        doc = fitz.open(pp)
        n_pages = min(len(doc), 50)
        for i in range(n_pages):
            pix = doc[i].get_pixmap(dpi=200)
            pix.save(os.path.join(img_dir, f"p{i+1:03d}.png"))
        doc.close()
        total_img_pages += n_pages
        print(f"  转换: {n_pages}页 ({time.time()-t0:.0f}s)")
    else:
        imgs = len([f for f in os.listdir(img_dir) if f.endswith('.png')])
        n_pages = imgs
        total_img_pages += n_pages
        print(f"  已有图片: {n_pages}页")
    
    # OCR
    out_json = img_dir + '_result.json'
    if os.path.exists(out_json):
        try:
            with open(out_json, 'r', encoding='utf-8') as fh:
                j = json.load(fh)
            if j.get('total_chars', 0) > 100:
                print(f"  跳过(已有结果: {j['total_chars']}字 {j.get('avg_confidence',0)}%)")
                continue
        except:
            os.remove(out_json)
    
    try:
        t1 = time.time()
        proc = subprocess.run(['node', BATCH_OCR, img_dir, out_json],
                            capture_output=True, text=True, encoding='utf-8', errors='replace',
                            timeout=900, cwd=os.path.dirname(BATCH_OCR))
        elapsed = time.time() - t1
        
        if os.path.exists(out_json) and os.path.getsize(out_json) > 100:
            with open(out_json, 'r', encoding='utf-8') as fh:
                j = json.load(fh)
            chars = j.get('total_chars', 0)
            conf = j.get('avg_confidence', 0)
            print(f"  OK: {chars:,}字 置信{conf}% ({elapsed:.0f}s)")
        else:
            print(f"  失败: 输出为空")
            if proc.stderr:
                print(f"  stderr: {proc.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"  超时(15min), 跳过")
    except Exception as e:
        print(f"  异常: {e}")

print(f"\n\n{'='*50}")
print(f"OCR阶段完成. 总图片页: {total_img_pages}")
