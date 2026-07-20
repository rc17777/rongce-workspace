from pathlib import Path
from pypdf import PdfReader

p = Path(r'C:\Users\scrccpa\Desktop\融策-政府审计简介7.10.pdf')
print('exists', p.exists(), 'size', p.stat().st_size if p.exists() else None)
reader = PdfReader(str(p))
print('pages', len(reader.pages))
for idx in [0, 1, 11]:
    print('\n' + '=' * 20 + f' PAGE {idx + 1} ' + '=' * 20)
    try:
        text = reader.pages[idx].extract_text() or ''
    except Exception as e:
        text = 'ERR ' + repr(e)
    print(text[:4000])
