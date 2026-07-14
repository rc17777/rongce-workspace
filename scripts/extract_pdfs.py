import sys, os, fitz, json
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\scrccpa\Desktop\复核'
results = {}
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.pdf'):
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, base)
            try:
                doc = fitz.open(fpath)
                text = '\n'.join(page.get_text() for page in doc)
                doc.close()
                results[rel] = text
                print(f'\n===== {rel} =====')
                print(text[:8000])
            except Exception as e:
                print(f'\n===== {rel} ===== ERROR: {e}')
with open(r'C:\Users\scrccpa\.openclaw\workspace\temp\pdf_docs.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('\nDone.')
