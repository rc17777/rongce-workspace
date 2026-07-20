# -*- coding: utf-8 -*-
"""提取报告docx全文（含表格）"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document

path = r'C:\Users\scrccpa\Desktop\新建文件夹\制造业数字化转型促进中心深度行（四川站）活动经费审核报告-修改.docx'
doc = Document(path)

out = []
# 按文档顺序遍历段落和表格
from docx.document import Document as _Doc
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    parent_elm = parent.element.body
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)

for block in iter_block_items(doc):
    if isinstance(block, Paragraph):
        t = block.text.strip()
        if t:
            out.append(t)
    else:
        out.append('[表格开始]')
        for row in block.rows:
            cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
            out.append(' | '.join(cells))
        out.append('[表格结束]')

text = '\n'.join(out)
with open(r'C:\Users\scrccpa\.openclaw\workspace\temp_review\report_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print(f'提取完成，共 {len(text)} 字符，{len(out)} 行')
