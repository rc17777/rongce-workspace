import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.oxml.ns import qn

doc = Document(r'D:\openclaw-workspace\bid_aba\阿坝州财政局竣工财务决算审核_投标方案.docx')
body = doc.element.body

for i, el in enumerate(body[:80]):
    tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
    if tag == 'p':
        pPr = el.find(qn('w:pPr'))
        if pPr is not None:
            ps = pPr.find(qn('w:pStyle'))
            if ps is not None:
                val = ps.get(qn('w:val'))
                t = el.find(qn('w:r'))
                txt = ''
                if t is not None:
                    tt = t.find(qn('w:t'))
                    if tt is not None and tt.text:
                        txt = tt.text[:60]
                print(f'{i}: [{val}] {txt}')
