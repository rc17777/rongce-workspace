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
word = win32com.client.gencache.EnsureDispatch('Word.Application')
word.Visible = False
word.DisplayAlerts = 0

try:
    # Create blank doc
    master = word.Documents.Add()
    
    first_doc = True
    for filename, label in SECTIONS:
        filepath = os.path.join(DESKTOP, filename)
        print(f'Processing: {label}...')
        
        # Open section doc
        try:
            section = word.Documents.Open(filepath, ReadOnly=True, Visible=False)
        except Exception as e:
            print(f'  ERROR opening {filename}: {e}')
            continue
        
        # Select all and copy
        section.Content.Copy()
        section.Close(SaveChanges=0)  # wdDoNotSaveChanges
        
        if not first_doc:
            # Insert page break
            master.ActiveWindow.Selection.InsertBreak(Type=7)  # wdPageBreak
        else:
            first_doc = False
        
        # Paste copied content
        master.ActiveWindow.Selection.Paste()
        
        # Go to end of document
        word.Selection.EndKey(Unit=6)  # wdStory
        
        time.sleep(1)
        print(f'  Done')
    
    print(f'\nSaving...')
    master.SaveAs2(OUTPUT)
    master.Close()
    print('Complete!')
    
finally:
    try:
        word.Quit()
    except:
        pass
    pythoncom.CoUninitialize()

size = os.path.getsize(OUTPUT)
print(f'File size: {size:,} bytes')
