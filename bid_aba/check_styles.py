import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.oxml.ns import qn

doc = Document(r'D:\openclaw-workspace\bid_aba\阿坝州财政局竣工财务决算审核_投标方案.docx')
body = doc.element.body

count = 0
for el in body:
    tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
    if tag == 'p':
        pPr = el.find(qn('w:pPr'))
        if pPr is not None:
            style = pPr.find(qn('w:style'))
            if style is not None:
                count += 1
                t = el.find(qn('w:r'))
                txt = ''
                if t is not None:
                    tt = t.find(qn('w:t'))
                    if tt is not None and tt.text:
                        txt = tt.text[:50]
                if count == 1:
                    print(f'{count}: [{style.get(qn("w:val"))}] {txt}')

print(f'Total styled paragraphs: {count}')
