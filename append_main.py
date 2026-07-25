# -*- coding: utf-8 -*-
"""Append md parser and main() to gen_word_full.py"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

code = r'''

def parse_md(text):
    lines=text.split('\n'); elements=[]; pos=0
    while pos<len(lines):
        line=lines[pos]
        if line.strip()=='': pos+=1; continue
        if line.strip() in('---','***','___'): elements.append(('hr','')); pos+=1; continue
        m=re.match(r'^(#{1,6})\s+(.*)', line)
        if m: elements.append(('heading',(len(m.group(1)), m.group(2).strip()))); pos+=1; continue
        if '|' in line and pos+1<len(lines) and re.match(r'\s*\|[\s\-:|]+\|', lines[pos+1]):
            tl=[]
            while pos<len(lines) and '|' in lines[pos] and lines[pos].strip(): tl.append(lines[pos]); pos+=1
            elements.append(('table', tl)); continue
        if line.strip().startswith('```'):
            pos+=1; cl=[]
            while pos<len(lines) and not lines[pos].strip().startswith('```'): cl.append(lines[pos]); pos+=1
            if pos<len(lines): pos+=1
            elements.append(('code', '\n'.join(cl))); continue
        if line.strip().startswith('>'):
            ql=[]
            while pos<len(lines) and lines[pos].strip().startswith('>'): ql.append(lines[pos].strip().lstrip('>').strip()); pos+=1
            elements.append(('blockquote', '\n'.join(ql))); continue
        m_ul=re.match(r'^(\s*)[-*]\s+(.*)', line)
        if m_ul:
            items=[]
            while pos<len(lines):
                mi=re.match(r'^(\s*)[-*]\s+(.*)', lines[pos])
                if mi: items.append((len(mi.group(1)), mi.group(2))); pos+=1
                elif lines[pos].strip()=='': pos+=1; break
                else: break
            elements.append(('ul', items)); continue
        m_ol=re.match(r'^(\s*)\d+[.、]\s*(.*)', line)
        if m_ol:
            items=[]
            while pos<len(lines):
                mi=re.match(r'^(\s*)\d+[.、]\s*(.*)', lines[pos])
                if mi: items.append((len(mi.group(1)), mi.group(2))); pos+=1
                elif lines[pos].strip()=='': pos+=1; break
                else: break
            elements.append(('ol', items)); continue
        pl=[]
        while pos<len(lines):
            l=lines[pos]
            if l.strip()=='' or l.strip() in('---','***','___') or l.strip().startswith('#') or l.strip().startswith('```') or l.strip().startswith('>') or re.match(r'\s*[-*]\s+',l) or re.match(r'\s*\d+[.、]\s*',l): break
            if '|' in l and pos+1<len(lines) and re.match(r'\s*\|[\s\-:|]+\|', lines[pos+1]): break
            pl.append(l); pos+=1
        if pl: elements.append(('paragraph', ' '.join(pl)))
    return elements

def gen_one(doc_ids, outname, title_sub, version_str="V1.0"):
    print(f'Generating: {outname}')
    d=mkdoc()
    sec=d.sections[0]
    hdr(sec, '四川融策会计师/工程咨询有限公司')
    ftr(sec)
    
    cover(d, '四川融策会计师事务所有限公司', '四川融策工程咨询有限公司', title_sub, version_str, '2026年7月')
    toc(d)
    
    for did in doc_ids:
        info=[x for x in DOCS if x[0]==did]
        if not info: continue
        _, fname, dcode, dname, dgroup = info[0]
        fpath=os.path.join(SRC, fname)
        if not os.path.exists(fpath):
            print(f'  WARN: {fname} not found')
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            text=f.read()
        
        # Apply modifications
        text=mods(text, did)
        
        # Parse and render
        elements=parse_md(text)
        
        # Add doc header
        p=d.add_paragraph()
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        r=p.add_run(f'{dcode}  {dname}')
        sf(r,FH,SE,True)
        d.add_page_break()
        
        for etype, content in elements:
            render(d, etype, content)
        
        # Page break between docs (except last)
        if did!=doc_ids[-1]:
            d.add_page_break()
        
        print(f'  OK: {dcode} {dname}')
    
    outpath=os.path.join(DESK, outname)
    d.save(outpath)
    print(f'Saved: {outpath}')
    return outpath

if __name__=='__main__':
    all_ids=[d[0] for d in DOCS]
    
    print('=== Generating Complete Version ===')
    gen_one(all_ids, '融策公司制度体系（完整版）.docx', '制 度 体 系')
    
    for name, ids in ASMS.items():
        print(f'=== Generating Assembly: {name} ===')
        gen_one(ids, f'融策制度汇编-{name}.docx', f'制度汇编\\\\n{name}')
    
    print('=== ALL DONE ===')
'''

with open(r'C:\Users\scrccpa\.openclaw\workspace\gen_word_full.py', 'a', encoding='utf-8') as f:
    f.write(code)
print('Part 4: main logic written')
