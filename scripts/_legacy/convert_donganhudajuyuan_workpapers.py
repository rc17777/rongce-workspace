import json
import os
import sys
from pathlib import Path

import win32com.client

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\scrccpa\Desktop\新建文件夹')
WORKPAPER_DIR = BASE / '底稿-龙泉驿区文广体旅局-东安湖大剧院运营补贴'
OUT = Path(r'C:\Users\scrccpa\.openclaw\workspace\outputs\donganhudajuyuan_review')
DOCX_OUT = OUT / 'converted_docx'
TXT_OUT = OUT / 'converted_doc_text'
DOCX_OUT.mkdir(parents=True, exist_ok=True)
TXT_OUT.mkdir(parents=True, exist_ok=True)

word = win32com.client.Dispatch('Word.Application')
word.Visible = False
records = []
try:
    for doc_path in WORKPAPER_DIR.glob('*.doc'):
        rec = {'source': str(doc_path), 'docx': None, 'txt': None, 'status': 'pending'}
        try:
            out_docx = DOCX_OUT / (doc_path.stem + '.docx')
            doc = word.Documents.Open(str(doc_path), ReadOnly=True, ConfirmConversions=False)
            doc.SaveAs2(str(out_docx), FileFormat=16)  # wdFormatXMLDocument
            doc.Close(False)
            rec['docx'] = str(out_docx)
            # Extract text via Word to preserve tables reasonably.
            doc2 = word.Documents.Open(str(out_docx), ReadOnly=True, ConfirmConversions=False)
            text = doc2.Content.Text
            doc2.Close(False)
            out_txt = TXT_OUT / (doc_path.stem + '.txt')
            out_txt.write_text(text, encoding='utf-8')
            rec['txt'] = str(out_txt)
            rec['chars'] = len(text)
            rec['status'] = 'converted_and_extracted'
        except Exception as e:
            rec['status'] = f'error: {type(e).__name__}: {e}'
            try:
                word.ActiveDocument.Close(False)
            except Exception:
                pass
        records.append(rec)
finally:
    word.Quit()

(OUT / 'workpaper_doc_conversion.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(records, ensure_ascii=False, indent=2))
