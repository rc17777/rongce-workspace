# -*- coding: utf-8 -*-
"""Append Word helper functions to gen_word_full.py"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

code = r'''
def sf(run, fn, sz, b=False):
    run.font.name=fn; run.font.size=sz; run.bold=b
    run.element.rPr.rFonts.set(qn('w:eastAsia'), fn)

def mkdoc():
    d=Document()
    s=d.sections[0]
    s.page_width=Cm(21); s.page_height=Cm(29.7)
    s.top_margin=Cm(2.5); s.bottom_margin=Cm(2)
    s.left_margin=Cm(2.8); s.right_margin=Cm(2.8)
    s.header_distance=Cm(1.5); s.footer_distance=Cm(1.5)
    st=d.styles['Normal']
    st.font.name=FF; st.font.size=SI
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FF)
    st.paragraph_format.line_spacing_rule=WD_LINE_SPACING.ONE_POINT_FIVE
    return d

def hdr(sec, txt):
    h=sec.header; h.is_linked_to_previous=False
    p=h.paragraphs[0]; p.text=txt; p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for r in p.runs: r.font.size=Pt(9); r.font.name=FS; r.element.rPr.rFonts.set(qn('w:eastAsia'),FS)

def ftr(sec):
    f=sec.footer; f.is_linked_to_previous=False
    p=f.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r0=p.add_run('-- '); r0.font.size=Pt(9); r0.font.name=FS
    r0.element.rPr.rFonts.set(qn('w:eastAsia'),FS)
    p.add_run()._r.append(parse_xml('<w:fldChar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fldCharType="begin"/>'))
    p.add_run()._r.append(parse_xml('<w:instrText xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xml:space="preserve"> PAGE </w:instrText>'))
    p.add_run()._r.append(parse_xml('<w:fldChar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fldCharType="end"/>'))
    r1=p.add_run(' --'); r1.font.size=Pt(9); r1.font.name=FS
    r1.element.rPr.rFonts.set(qn('w:eastAsia'),FS)

def cover(d, t1, t2, sub, ver, dt):
    for _ in range(6):
        p=d.add_paragraph(); p.paragraph_format.space_after=Pt(0)
    for t in [t1,t2]:
        p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        r=p.add_run(t); sf(r,FH,Pt(26),True)
    d.add_paragraph()
    p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run(sub); sf(r,FH,Pt(36),True)
    for _ in range(3): d.add_paragraph()
    for t in [f'版本：{ver}',dt]:
        p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        r=p.add_run(t); sf(r,FF,SS)
    d.add_page_break()

def toc(d):
    p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run('目    录'); sf(r,FH,SE,True)
    d.add_paragraph()
    p=d.add_paragraph()
    p.add_run()._r.append(parse_xml('<w:fldChar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fldCharType="begin"/>'))
    p.add_run()._r.append(parse_xml('<w:instrText xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText>'))
    p.add_run()._r.append(parse_xml('<w:fldChar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fldCharType="separate"/>'))
    r=p.add_run('（请在Word中右键此处选择更新域以生成目录）'); r.font.color.rgb=RGBColor(128,128,128)
    p.add_run()._r.append(parse_xml('<w:fldChar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fldCharType="end"/>'))
    d.add_page_break()

def parse_table(lines):
    rows=[]
    for i,line in enumerate(lines):
        if i==1: continue
        cells=[c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)
    return rows

def add_tbl(d, rows):
    if not rows: return
    ncols=max(len(r) for r in rows)
    for r in rows:
        while len(r)<ncols: r.append('')
    tbl=d.add_table(rows=len(rows), cols=ncols)
    tbl.style='Table Grid'; tbl.alignment=1
    for i,row_data in enumerate(rows):
        for j,cell_text in enumerate(row_data):
            cell=tbl.cell(i,j); cell.text=''
            p=cell.paragraphs[0]
            p.paragraph_format.space_before=Pt(1)
            p.paragraph_format.space_after=Pt(1)
            p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
            clean=re.sub(r'\*\*(.*?)\*\*', r'\1', cell_text)
            r=p.add_run(clean)
            if i==0:
                sf(r,FH,SW,True); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                shading=parse_xml('<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fill="D9E2F3" w:val="clear"/>')
                cell._tc.get_or_add_tcPr().append(shading)
            else:
                sf(r,FF,SW)
    d.add_paragraph()

def render(d, etype, content):
    if etype=='heading':
        level,text=content
        clean=re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        if level==1:
            p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before=Pt(24); p.paragraph_format.space_after=Pt(12)
            r=p.add_run(clean); sf(r,FH,SE,True)
        elif level==2:
            p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before=Pt(18); p.paragraph_format.space_after=Pt(8)
            r=p.add_run(clean); sf(r,FH,SS,True)
        elif level==3:
            p=d.add_paragraph()
            p.paragraph_format.space_before=Pt(12); p.paragraph_format.space_after=Pt(6)
            r=p.add_run(clean); sf(r,FH,SI,True)
        else:
            p=d.add_paragraph()
            p.paragraph_format.space_before=Pt(6); p.paragraph_format.space_after=Pt(3)
            r=p.add_run(clean); sf(r,FH,SI)

    elif etype=='paragraph':
        p=d.add_paragraph()
        p.paragraph_format.first_line_indent=Cm(0.74)
        p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.ONE_POINT_FIVE
        parts=re.split(r'(\*\*.*?\*\*)', content)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                r=p.add_run(part[2:-2]); sf(r,FF,SI,True)
            elif part:
                r=p.add_run(part); sf(r,FF,SI)

    elif etype=='table':
        rows=parse_table(content); add_tbl(d, rows)

    elif etype=='code':
        for line in content.split('\n'):
            p=d.add_paragraph()
            p.paragraph_format.left_indent=Cm(1)
            p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
            r=p.add_run(line); r.font.name='Consolas'; r.font.size=Pt(10)

    elif etype=='blockquote':
        for line in content.split('\n'):
            if not line.strip(): continue
            p=d.add_paragraph()
            p.paragraph_format.left_indent=Cm(1)
            p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.ONE_POINT_FIVE
            parts=re.split(r'(\*\*.*?\*\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    r=p.add_run(part[2:-2]); sf(r,FF,SW,True)
                elif part:
                    r=p.add_run(part); sf(r,FF,SW)

    elif etype=='ul':
        for indent,text in content:
            p=d.add_paragraph()
            p.paragraph_format.left_indent=Cm(0.74+indent*0.3)
            p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.ONE_POINT_FIVE
            px='* ' if indent==0 else '  - '
            parts=re.split(r'(\*\*.*?\*\*)', text)
            first=True
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    t=(px+part[2:-2]) if first else part[2:-2]
                    r=p.add_run(t); sf(r,FF,SI,True)
                elif part:
                    t=(px+part) if first else part
                    r=p.add_run(t); sf(r,FF,SI)
                first=False

    elif etype=='ol':
        for idx,(indent,text) in enumerate(content,1):
            p=d.add_paragraph()
            p.paragraph_format.left_indent=Cm(0.74+indent*0.3)
            p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.ONE_POINT_FIVE
            px=f'{idx}. '
            parts=re.split(r'(\*\*.*?\*\*)', text)
            first=True
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    t=(px+part[2:-2]) if first else part[2:-2]
                    r=p.add_run(t); sf(r,FF,SI,True)
                elif part:
                    t=(px+part) if first else part
                    r=p.add_run(t); sf(r,FF,SI)
                first=False

    elif etype=='hr':
        pass
'''

with open(r'C:\Users\scrccpa\.openclaw\workspace\gen_word_full.py', 'a', encoding='utf-8') as f:
    f.write(code)
print('Part 3: helpers written')
