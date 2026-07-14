import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.oxml.ns import qn

doc = Document(r'D:\openclaw-workspace\bid_aba\阿坝州财政局竣工财务决算审核_投标方案.docx')
body = doc.element.body

# Find "附" heading
for i, el in enumerate(body):
    tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
    if tag == 'p':
        pPr = el.find(qn('w:pPr'))
        if pPr is not None:
            ps = pPr.find(qn('w:pStyle'))
            if ps is not None and ps.get(qn('w:val')) == 'Heading1':
                t = el.find(qn('w:r'))
                if t is not None:
                    tt = t.find(qn('w:t'))
                    if tt is not None and tt.text and '附' in tt.text:
                        print(f'Found "附" at element {i}: {tt.text}')
                        break
else:
    print('"附" heading NOT FOUND - already removed! ✅')
