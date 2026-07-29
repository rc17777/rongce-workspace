"""Extract text from .doc and .docx files using win32com"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

import pythoncom
from win32com.client import Dispatch

files = [
    (r"D:\xwechat_files\jjion17_a2d1\msg\attach\2e126e90acc04fe9c41ee3d13df77ec8\2026-07\Rec\bae6fa29e587ca4e\F\5\2.巴中市恩阳医养园PPP项目借款利息审计报告2.doc", "借款利息审计报告"),
    (r"C:\Users\scrccpa\Desktop\1.巴中市恩阳医养园PPP项目可用性付费测算结果报告（2000只还本)(1).docx", "可用性付费测算结果报告"),
]

output_dir = r"C:\Users\scrccpa\Desktop\新建文件夹\政府合同\ocr_output"
os.makedirs(output_dir, exist_ok=True)

pythoncom.CoInitialize()
word = Dispatch("Word.Application")
word.Visible = False

for filepath, label in files:
    print(f"\n{'='*60}")
    print(f"Reading: {label}")
    print(f"Path: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found!")
        continue
    
    try:
        doc = word.Documents.Open(filepath)
        text = doc.Content.Text
        
        # Save to txt
        txt_path = os.path.join(output_dir, f"{label}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Saved: {txt_path} ({len(text)} chars)")
        doc.Close()
    except Exception as e:
        print(f"ERROR: {e}")

word.Quit()
pythoncom.CoUninitialize()
print("\nDone!")
