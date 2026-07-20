#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABBYY FineCmd 测试 v3 - 精确定位源目录 + Popen直调"""
import os, sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
log_file = r"C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR\abbyy_log3.txt"

def log(msg):
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(str(msg) + '\n')
    print(msg)

ABBYY = r"C:\Program Files (x86)\ABBYY FineReader 15\FineCmd.exe"

# 扫描桌面所有目录及其PDF数量
desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
dirs_with_pdfs = []
for item in os.listdir(desktop):
    p = os.path.join(desktop, item)
    if os.path.isdir(p):
        pdfs = sorted([f for f in os.listdir(p) if f.lower().endswith('.pdf')], key=len)
        if pdfs:
            dirs_with_pdfs.append((item, p, pdfs))
            log(f"[{len(pdfs):3d}个] {item} (首文件: {pdfs[0][:30]}...)")

# 找到90个PDF的那个目录（审计观察）
target = None
for name, path, pdfs in dirs_with_pdfs:
    if len(pdfs) >= 90:
        target = (name, path, pdfs)
        log(f"\n✅ 选中源目录: {name} ({len(pdfs)}个PDF)")

if not target:
    log("未找到90个以上PDF的目录!")
    # 用最大的目录
    target = max(dirs_with_pdfs, key=lambda x: len(x[2]))
    log(f"回退到: {target[0]} ({len(target[2])}个)")

name, src_path, pdfs = target
test_pdf = os.path.join(src_path, pdfs[0])
test_name = os.path.splitext(pdfs[0])[0]

out_dir = r"C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR"
out_txt = os.path.join(out_dir, f"[ABBYY]{test_name}.txt")
out_pdf = os.path.join(out_dir, f"[ABBYY]{test_name}.pdf")
out_docx = os.path.join(out_dir, f"[ABBYY]{test_name}.docx")

log(f"\n测试PDF: {test_pdf}")
log(f"大小: {os.path.getsize(test_pdf)} bytes")
log(f"\n启动ABBYY...")

# 尝试三种输出格式
results = {}
for fmt, out_path in [("TXT", out_txt), ("PDF", out_pdf), ("DOCX", out_docx)]:
    log(f"\n--- 格式: {fmt} -> {os.path.basename(out_path)} ---")
    try:
        proc = subprocess.Popen(
            [ABBYY, "/Convert", test_pdf, out_path, "/lang", "ChinesePRC", "/outFormat", fmt],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        stdout, stderr = proc.communicate(timeout=300)
        log(f"退出码: {proc.returncode}")
        log(f"stdout: {stdout.decode('utf-8', errors='replace')[:200]}")
        log(f"stderr: {stderr.decode('utf-8', errors='replace')[:200]}")
        
        if os.path.exists(out_path):
            sz = os.path.getsize(out_path)
            log(f"✅ 成功! 文件大小: {sz} bytes")
            results[fmt] = ("OK", sz)
        else:
            log(f"❌ 文件未生成")
            results[fmt] = ("FAIL", None)
    except subprocess.TimeoutExpired:
        proc.kill()
        log(f"⏰ {fmt} 超时")
        results[fmt] = ("TIMEOUT", None)

# 如果TXT成功，看内容
log("\n" + "="*50)
log("结果汇总:")
for fmt, (status, sz) in results.items():
    log(f"  {fmt}: {status}" + (f" ({sz} bytes)" if sz else ""))

if results.get("TXT")[0] == "OK":
    with open(out_txt, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    log(f"\nTXT内容 ({len(content)}字):")
    log(content[:300])

log("\n=== 测试完成 ===")
