#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ABBYY FineCmd v2 - 通过cmd.exe包装调用"""
import os, sys, io, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

log_file = r"C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR\abbyy_log2.txt"

def log(msg):
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(str(msg) + '\n')
    print(msg)

log("="*50)
log("ABBYY FineCmd 测试 v2")

ABBYY = r"C:\Program Files (x86)\ABBYY FineReader 15\FineCmd.exe"
log(f"FineCmd存在: {os.path.exists(ABBYY)}")
log(f"FineCmd大小: {os.path.getsize(ABBYY)} bytes")

# 找PDF
desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
src_dir = None
for item in os.listdir(desktop):
    p = os.path.join(desktop, item)
    if os.path.isdir(p):
        pdfs = [f for f in os.listdir(p) if f.lower().endswith('.pdf')]
        if pdfs:
            src_dir = p
            log(f"源目录: {os.path.basename(p)} ({len(pdfs)}个PDF)")
            break

if not src_dir:
    log("未找到源目录!")
    sys.exit(1)

pdfs = sorted([f for f in os.listdir(src_dir) if f.lower().endswith('.pdf')])
test_pdf = os.path.join(src_dir, pdfs[0])
test_name = os.path.splitext(pdfs[0])[0]

out_dir = r"C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR"
out_txt = os.path.join(out_dir, f"abbyy_{test_name}.txt")
log(f"源文件: {test_pdf}")
log(f"输出: {out_txt}")

# ===== 方法1: 通过cmd.exe包装 =====
log("\n--- 方法1: cmd.exe wrapper ---")
cmd_str = f'""{ABBYY}" /Convert "{test_pdf}" "{out_txt}" /lang ChinesePRC /outFormat TXT"'
log(f"CMD命令: {cmd_str}")

try:
    result = subprocess.run(
        ['cmd.exe', '/c', cmd_str],
        capture_output=True,
        text=True,
        timeout=180,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    log(f"退出码: {result.returncode}")
    log(f"stdout: {result.stdout[:300]}")
    log(f"stderr: {result.stderr[:300]}")
except subprocess.TimeoutExpired:
    log("方法1 超时!")
except Exception as e:
    log(f"方法1 错误: {e}")

if os.path.exists(out_txt):
    with open(out_txt, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    log(f"\n✅ 方法1成功! 识别 {len(content)} 字")
    log(content[:200])
else:
    log(f"\n方法1失败，输出文件未生成")

# ===== 方法2: Popen + wait =====
log("\n--- 方法2: Popen ---")
out_txt2 = os.path.join(out_dir, f"abbyy_{test_name}_v2.txt")
try:
    proc = subprocess.Popen(
        [ABBYY, '/Convert', test_pdf, out_txt2, '/lang', 'ChinesePRC', '/outFormat', 'TXT'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    stdout, stderr = proc.communicate(timeout=180)
    log(f"退出码: {proc.returncode}")
    log(f"stdout: {stdout.decode('utf-8', errors='replace')[:300]}")
    log(f"stderr: {stderr.decode('utf-8', errors='replace')[:300]}")
except subprocess.TimeoutExpired:
    proc.kill()
    log("方法2 超时，已杀死进程")
except Exception as e:
    log(f"方法2 错误: {e}")

if os.path.exists(out_txt2):
    with open(out_txt2, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    log(f"\n✅ 方法2成功! 识别 {len(content)} 字")
    log(content[:200])
else:
    log(f"\n方法2失败，输出文件未生成")

log("\n=== 测试完成 ===")
