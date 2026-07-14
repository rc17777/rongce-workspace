import sys, os, zipfile, xml.etree.ElementTree as ET, json

sys.stdout.reconfigure(encoding='utf-8')

def extract_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml')
    root = ET.fromstring(xml)
    lines = []
    for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
        line = ''.join(t.text or '' for t in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
        lines.append(line)
    return '\n'.join(lines)

def extract_xlsx(path):
    with zipfile.ZipFile(path) as z:
        # shared strings
        try:
            ss_xml = z.read('xl/sharedStrings.xml')
            ss_root = ET.fromstring(ss_xml)
            ss_ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
            strings = []
            for si in ss_root.iter(f'{{{ss_ns}}}si'):
                t = si.find(f'{{{ss_ns}}}t')
                if t is not None and t.text:
                    strings.append(t.text)
                else:
                    # could be rich text
                    parts = [t.text or '' for t in si.iter(f'{{{ss_ns}}}t')]
                    strings.append(''.join(parts))
        except:
            strings = []
        
        # sheets
        try:
            sheet_xml = z.read('xl/worksheets/sheet1.xml')
            sheet_root = ET.fromstring(sheet_xml)
            lines = []
            for row in sheet_root.iter(f'{{{ss_ns}}}row'):
                cells = []
                for c in row.iter(f'{{{ss_ns}}}c'):
                    v = c.find(f'{{{ss_ns}}}v')
                    if v is not None and v.text:
                        t = c.get('t', '')
                        if t == 's':
                            idx = int(v.text)
                            if idx < len(strings):
                                cells.append(strings[idx])
                            else:
                                cells.append(v.text)
                        else:
                            cells.append(v.text)
                    else:
                        cells.append('')
                lines.append('\t'.join(cells))
        except:
            lines = ['(no sheet1)']
        
        return '\n'.join(lines)

base = r'C:\Users\scrccpa\Desktop\复核'
results = {}

for root, dirs, files in os.walk(base):
    for f in files:
        fpath = os.path.join(root, f)
        rel = os.path.relpath(fpath, base)
        try:
            if f.endswith('.docx'):
                text = extract_docx(fpath)
                results[rel] = {'type': 'docx', 'content': text}
                print(f'\n===== {rel} =====')
                print(text[:8000])
            elif f.endswith('.xlsx'):
                text = extract_xlsx(fpath)
                results[rel] = {'type': 'xlsx', 'content': text}
                print(f'\n===== {rel} =====')
                print(text[:8000])
        except Exception as e:
            print(f'\n===== {rel} ===== ERROR: {e}')

# Save full results to JSON for later
with open(r'C:\Users\scrccpa\.openclaw\workspace\temp\extracted_docs.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('\n\nDone. Saved to temp/extracted_docs.json')
