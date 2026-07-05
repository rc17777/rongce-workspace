#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABBYY FineReader PDF 15 测试 - 输出到日志文件"""
import os, sys, subprocess

log_file = r"C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR\abbyy_log.txt"

def log(msg):
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

ABBYY = r"C:\Program Files (x86)\ABBYY FineReader 15\FineCmd.exe"

# 检查ABBYY是否存在
log(f"ABBYY存在: {os.path.exists(ABBYY)}")
log(f"ABBYY大小: {os.path.getsize(ABBYY)} bytes")

# 扫描PDF
desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
log(f"Desktop: {desktop}")
log(f"Desktop exists: {os.path.exists(desktop)}")

src_dirs = []
for item in os.listdir(desktop):
    p = os.path.join(desktop, item)
    if os.path.isdir(p):
        pdfs = [f for f in os.listdir(p) if f.lower().endswith('.pdf')]
        if pdfs:
            src_dirs.append((p, len(pdfs)))
            log(f"找到目录: {item} -> {len(pdfs)}个PDF")

if not src_dirs:
    log("未找到PDF目录!")
    sys.exit(1)

# 取第一个PDF
src_dir, count = src_dirs[0]
pdfs = sorted([f for f in os.listdir(src_dir) if f.lower().endswith('.pdf')])
test_pdf = os.path.join(src_dir, pdfs[0])
test_name = os.path.splitext(pdfs[0])[0]

out_txt = os.path.join(r"C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR", f"{test_name}.txt")

log(f"\n源: {test_pdf}")
log(f"文件大小: {os.path.getsize(test_pdf)} bytes")
log(f"输出: {out_txt}")

# 运行ABBYY
log(f"\n运行命令: {ABBYY} /Convert ...")
try:
    result = subprocess.run(
        [ABBYY, "/Convert", test_pdf, out_txt, "/lang", "ChinesePRC", "/outFormat", "TXT"],
        capture_output=True, text=True, timeout=180
    )
    log(f"退出码: {result.returncode}")
    log(f"stdout: {result.stdout[:500]}")
    log(f"stderr: {result.stderr[:500]}")
except subprocess.TimeoutExpired:
    log("超时!")
except Exception as e:
    log(f"错误: {e}")

# 检查输出
if os.path.exists(out_txt):
    with open(out_txt, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    log(f"\n✅ 成功! 识别 {len(content)} 字")
    log(f"前200字: {content[:200]}")
else:
    log(f"\n❌ 输出文件未生成")
    out_dir = os.path.dirname(out_txt)
    for f in os.listdir(out_dir):
        fp = os.path.join(out_dir, f)
        log(f"  {f} ({os.path.getsize(fp)} bytes)")

log("=== 测试完成 ===")
