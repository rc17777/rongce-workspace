# -*- coding: utf-8 -*-
"""用 Word COM 批量把 .doc / .wps 转为纯文本。"""
import os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client as win32
import pythoncom

SRC = r"C:\Users\scrccpa\Desktop\若尔盖审计局提供\校园餐相关文件"
OUT = r"C:\Users\scrccpa\.openclaw\workspace\projects\若尔盖校园餐审计\raw_text"
os.makedirs(OUT, exist_ok=True)

def safe_name(full):
    rel = os.path.relpath(full, SRC)
    return rel.replace("\\", "__").replace("/", "__")

TASKS = []
for full in glob.glob(os.path.join(SRC, "**", "*"), recursive=True):
    if os.path.isdir(full):
        continue
    ext = os.path.splitext(full)[1].lower()
    if ext in ('.doc', '.wps'):
        TASKS.append(full)

pythoncom.CoInitialize()
word = win32.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = False

# wdFormatText = 2 ; wdFormatUnicodeText = 7
for full in TASKS:
    name = safe_name(full)
    out = os.path.join(OUT, os.path.splitext(name)[0] + ".txt")
    try:
        doc = word.Documents.Open(full, ReadOnly=True, ConfirmConversions=False)
        text = doc.Content.Text
        # also grab tables text (Content.Text usually includes it)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        doc.Close(False)
        print(f"[OK {len(text):>7}] {os.path.relpath(full, SRC)}")
    except Exception as e:
        print(f"[ERR] {os.path.relpath(full, SRC)} -> {e}")
        try:
            doc.Close(False)
        except Exception:
            pass

word.Quit()
pythoncom.CoUninitialize()
print("DONE")
