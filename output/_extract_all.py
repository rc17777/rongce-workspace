import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    from docx.oxml.ns import qn
    for child in parent.element.body.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)

def dump(path):
    doc = Document(path)
    out = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            t = block.text.strip()
            if t:
                out.append(t)
        else:
            out.append('[TABLE]')
            for row in block.rows:
                cells = [c.text.strip().replace('\n',' ') for c in row.cells]
                out.append(' | '.join(cells))
            out.append('[/TABLE]')
    return '\n'.join(out)

base = r'C:\Users\scrccpa\.openclaw\workspace\output\\'
files = [
 '融策-项目回款与清欠专项考核办法.docx',
 '融策-员工绩效考核办法.docx',
 '融策-部门绩效考核办法.docx',
 '融策-投标管理办法.docx',
 '融策-经营激励办法.docx',
 '融策-岗位职责卡（8岗位）.docx',
]
results = []
for f in files:
    results.append('#'*25 + ' ' + f + ' ' + '#'*25)
    try:
        results.append(dump(base+f))
    except Exception as e:
        results.append('ERROR ' + str(e))
    results.append('')
open(base+'_all_extracted.txt','w',encoding='utf-8').write('\n'.join(results))
print('done', sum(len(r) for r in results))
