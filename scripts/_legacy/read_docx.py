import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document

doc = Document(r'C:\Users\scrccpa\Desktop\轨道培训\四川轨道公司审计风险培训-演讲稿.docx')
for i, p in enumerate(doc.paragraphs):
    style = p.style.name if p.style else 'None'
    text = p.text.strip()
    if text:
        print(f'[P{i}|{style}] {text}')
