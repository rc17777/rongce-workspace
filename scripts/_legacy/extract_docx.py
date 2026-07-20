import sys, os, zipfile, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')

desktop = r'C:\Users\scrccpa\Desktop'
for f in os.listdir(desktop):
    if 'N513401' in f:
        path = os.path.join(desktop, f)
        print(f'Found: {f}')
        with zipfile.ZipFile(path, 'r') as z:
            xml_content = z.read('word/document.xml')
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        root = ET.fromstring(xml_content)
        paragraphs = root.findall('.//w:p', ns)
        text_lines = []
        for p in paragraphs:
            texts = []
            for t in p.findall('.//w:t', ns):
                if t.text:
                    texts.append(t.text)
            line = ''.join(texts)
            if line.strip():
                text_lines.append(line.strip())
        text = '\n'.join(text_lines)
        outpath = r'D:\openclaw-workspace\temp\西昌招标文件_提取.txt'
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Saved {len(text_lines)} lines, {len(text)} chars')
        break
