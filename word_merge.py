import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import time
import win32com.client
import pythoncom

pythoncom.CoInitialize()

DESKTOP = r'C:\Users\scrccpa\Desktop'
OUTPUT = os.path.join(DESKTOP, '融策公司制度体系（完整版）.docx')

# Section files in order
SECTIONS = [
    (r'融策制度汇编-人力资源篇.docx', '人力资源篇'),
    (r'融策制度汇编-财务管理篇.docx', '财务管理篇'),
    (r'融策制度汇编-业务部管理篇.docx', '业务部管理篇'),
    (r'融策制度汇编-业务质控篇.docx', '业务质控篇'),
    (r'融策制度汇编-行政综合篇.docx', '行政综合篇'),
]

print('Starting Word...')
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0  # wdAlertsNone

try:
    # ============================================
    # Step 1: Open first section as base
    # ============================================
    base_path = os.path.join(DESKTOP, SECTIONS[0][0])
    print(f'Opening base: {SECTIONS[0][1]}')
    doc = word.Documents.Open(base_path)
    
    # Go to end of document
    word.Selection.EndKey(Unit=6)  # wdStory
    
    # ============================================
    # Step 2: Append remaining sections
    # ============================================
    for filename, label in SECTIONS[1:]:
        filepath = os.path.join(DESKTOP, filename)
        print(f'Appending: {label} ({filename})')
        
        # Insert page break before new section
        word.Selection.InsertBreak(Type=7)  # wdPageBreak
        
        # Insert the section file
        word.Selection.InsertFile(
            FileName=filepath,
            Range='',
            ConfirmConversions=False,
            Link=False,
            Attachment=False
        )
        
        # Go to end again
        word.Selection.EndKey(Unit=6)
        time.sleep(0.5)
    
    # ============================================
    # Step 3: Save as complete
    # ============================================
    print(f'\nSaving to: {OUTPUT}')
    doc.SaveAs2(OUTPUT)
    doc.Close()
    
    print('Done!')
    
finally:
    word.Quit()
    pythoncom.CoUninitialize()

# Verify
size = os.path.getsize(OUTPUT)
print(f'File size: {size:,} bytes')
