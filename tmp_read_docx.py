import sys
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
doc = Document(r'C:\Users\scrccpa\Desktop\融策公司制度体系（完整版）.docx')

# Print all non-empty paragraphs with line numbers to understand structure
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if not t:
        continue
    # Check if any run is bold and text looks like a heading
    is_bold = any(r.bold for r in p.runs if r.bold)
    is_large = any(r.font.size and r.font.size >= 140000 for r in p.runs if r.font.size)
    if is_bold or is_large:
        print(f'[{"B" if is_bold else ""}{"L" if is_large else ""}] {t[:100]}')
    if i > 600:
        break
