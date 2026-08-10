import os, sys
sys.stdout.reconfigure(encoding='utf-8')

ob = r'C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR'
subs = [d for d in os.listdir(ob) if os.path.isdir(os.path.join(ob, d))]

for sd in sorted(subs):
    sdp = os.path.join(ob, sd)
    md = sum(1 for f in os.listdir(sdp) if f.endswith('.md'))
    docx = sum(1 for f in os.listdir(sdp) if f.endswith('.docx'))
    pdf = sum(1 for f in os.listdir(sdp) if f.endswith('.pdf'))
    parts = []
    if md: parts.append(f'{md}篇md')
    if docx: parts.append(f'{docx}篇docx')
    if pdf: parts.append(f'{pdf}篇pdf')
    # sample filenames
    samples = [f for f in sorted(os.listdir(sdp))[:5]]
    print(f'\n=== {sd} ({", ".join(parts)}) ===')
    for s in samples:
        print(f'  {s}')
