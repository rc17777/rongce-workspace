# -*- coding: utf-8 -*-
"""提取.doc底稿（win32com转文本）+ 关键PDF"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

outdir = r'C:\Users\scrccpa\.openclaw\workspace\temp_review'

# ---- 1. .doc 底稿 via win32com ----
try:
    import win32com.client
    import pythoncom
    pythoncom.CoInitialize()
    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False
    docs = [
        (r'C:\Users\scrccpa\Desktop\新建文件夹\2.底稿\专项审计底稿.doc', 'workpaper.txt'),
        (r'C:\Users\scrccpa\Desktop\新建文件夹\2.底稿\信通院-单面打印签字盖章原件+营业执照复印件返回.doc', 'xingongyuan.txt'),
        (r'C:\Users\scrccpa\Desktop\新建文件夹\2.底稿\科服集团-单面打印签字盖章原件返回.doc', 'kefuji.txt'),
    ]
    for src, dst in docs:
        try:
            d = word.Documents.Open(src, ReadOnly=True)
            txt = d.Content.Text
            d.Close(False)
            with open(os.path.join(outdir, dst), 'w', encoding='utf-8') as f:
                f.write(txt)
            print(f'[OK] {os.path.basename(src)} -> {dst} ({len(txt)} chars)')
        except Exception as e:
            print(f'[FAIL] {os.path.basename(src)}: {e}')
    word.Quit()
except Exception as e:
    print(f'[FAIL] win32com: {e}')
