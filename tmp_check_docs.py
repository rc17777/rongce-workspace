import sys
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document

for filename, label in [
    (r'C:\Users\scrccpa\Desktop\融策制度汇编-业务质控篇.docx', '业务质控'),
    (r'C:\Users\scrccpa\Desktop\融策制度汇编-财务管理篇.docx', '财务管理'),
    (r'C:\Users\scrccpa\Desktop\融策制度汇编-行政综合篇.docx', '行政综合'),
]:
    print(f'\n{"="*60}')
    print(f'【{label}】')
    print(f'{"="*60}')
    try:
        doc = Document(filename)
        for i, p in enumerate(doc.paragraphs):
            t = p.text.strip()
            if not t:
                continue
            is_bold = any(r.bold for r in p.runs if r.bold)
            is_large = any(r.font.size and r.font.size >= 140000 for r in p.runs if r.font.size)
            if is_bold or is_large:
                print(f'  [{label}] {t[:120]}')
            if i > 400:
                break
    except Exception as e:
        print(f'  Error: {e}')
