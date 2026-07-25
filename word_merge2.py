import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, time
import win32com.client
import pythoncom

pythoncom.CoInitialize()

DESKTOP = r'C:\Users\scrccpa\Desktop'
OUTPUT = os.path.join(DESKTOP, '融策公司制度体系（完整版）.docx')

SECTIONS = [
    (r'融策制度汇编-人力资源篇.docx', '人力资源篇'),
    (r'融策制度汇编-财务管理篇.docx', '财务管理篇'),
    (r'融策制度汇编-业务部管理篇.docx', '业务部管理篇'),
    (r'融策制度汇编-业务质控篇.docx', '业务质控篇'),
    (r'融策制度汇编-行政综合篇.docx', '行政综合篇'),
]

print('Starting Word...')
try:
    word = win32com.client.Dispatch("Word.Application")
except:
    # Try with explicit progid
    word = win32com.client.Dispatch("Word.Application.16")

word.Visible = False
word.DisplayAlerts = 0

try:
    # Create new document
    doc = word.Documents.Add()
    
    first = True
    for filename, label in SECTIONS:
        filepath = os.path.join(DESKTOP, filename)
        print(f'Inserting: {label}')
        
        if first:
            # For first file, insert its entire content
            word.Selection.InsertFile(
                FileName=filepath,
                ConfirmConversions=False
            )
            first = False
        else:
            # Add page break then insert next file
            word.Selection.InsertBreak(Type=7)  # wdPageBreak
            word.Selection.InsertFile(
                FileName=filepath,
                ConfirmConversions=False
            )
        
        # Go to end
        word.Selection.EndKey(Unit=6)
        time.sleep(1)
    
    print(f'\nSaving...')
    doc.SaveAs2(OUTPUT)
    doc.Close()
    print('Done!')
    
finally:
    try:
        word.Quit()
    except:
        pass
    pythoncom.CoUninitialize()

size = os.path.getsize(OUTPUT)
print(f'Size: {size:,} bytes')
