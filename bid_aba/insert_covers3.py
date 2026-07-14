import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Inches
from docx.oxml.ns import qn
import lxml.etree as etree

PTH = r'D:\openclaw-workspace\bid_aba\阿坝州财政局竣工财务决算审核_投标方案.docx'
NPTH = r'D:\openclaw-workspace\bid_aba\阿坝州财政局竣工财务决算审核_投标方案_v2.docx'
IMG = r'D:\openclaw-workspace\bid_aba\work_dir'

doc = Document(PTH)
part = doc.part

# Namespaces
NSWP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
NSA = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NSPIC = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
NSR = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
RELS_IMAGE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'

chapter_covers = [
    ('一、项目理解与总体思路', 'cover1-intro.drawio.png'),
    ('二、审核依据与政策解读', 'cover2-laws.drawio.png'),
    ('三、审核范围与审核内容', 'cover3-scope.drawio.png'),
    ('四、审核方法与技术路线', 'cover4-methods.drawio.png'),
    ('五、审核程序与进度安排', 'cover4-methods.drawio.png'),
    ('六、重点难点分析与对策', 'cover5-quality.drawio.png'),
    ('七、审计管理制度与质量保证', 'cover5-quality.drawio.png'),
    ('八、公司概况与服务能力', 'cover6-company.drawio.png'),
    ('九、项目团队配备', 'cover6-company.drawio.png'),
    ('十、类似业绩与履约能力', 'cover7-performance.drawio.png'),
    ('十一、服务承诺与保障措施', 'cover7-performance.drawio.png'),
]

inserted = 0
for heading_text, cover_file in chapter_covers:
    img_path = os.path.join(IMG, cover_file)
    if not os.path.exists(img_path):
        print(f"NOT FOUND: {img_path}")
        continue
    
    # Find the heading paragraph
    for p in doc.paragraphs:
        if heading_text in p.text:
            parent = p._element.getparent()
            idx = list(parent).index(p._element)
            
            # Create image paragraph
            img_para = etree.SubElement(parent, qn('w:p'))
            # Move to correct position
            parent.remove(img_para)
            parent.insert(idx, img_para)
            
            # Add image run
            run_elem = etree.SubElement(img_para, qn('w:r'))
            drawing = etree.SubElement(run_elem, qn('w:drawing'))
            
            # wp:inline
            inline = etree.SubElement(drawing, f'{{{NSWP}}}inline')
            inline.set('distT', '0'); inline.set('distB', '0')
            inline.set('distL', '0'); inline.set('distR', '0')
            
            extent = etree.SubElement(inline, f'{{{NSWP}}}extent')
            cx = int(6.5 * 914400)
            cy = int(6.5 * 300 / 1100 * 914400)
            extent.set('cx', str(cx)); extent.set('cy', str(cy))
            
            effect = etree.SubElement(inline, f'{{{NSWP}}}effectExtent')
            effect.set('l','0'); effect.set('t','0'); effect.set('b','0'); effect.set('r','0')
            
            docPr = etree.SubElement(inline, f'{{{NSWP}}}docPr')
            docPr.set('id', str(100 + inserted))
            docPr.set('name', f'Cover{inserted+1}')
            
            # a:graphic
            graphic = etree.SubElement(inline, f'{{{NSA}}}graphic')
            gd = etree.SubElement(graphic, f'{{{NSA}}}graphicData')
            gd.set('uri', 'http://schemas.openxmlformats.org/drawingml/2006/picture')
            
            # pic:pic
            pic = etree.SubElement(gd, f'{{{NSPIC}}}pic')
            nv = etree.SubElement(pic, f'{{{NSPIC}}}nvPicPr')
            cnv = etree.SubElement(nv, f'{{{NSPIC}}}cNvPr')
            cnv.set('id','0'); cnv.set('name',f'Picture{inserted+1}')
            etree.SubElement(nv, f'{{{NSPIC}}}cNvPicPr')
            
            bf = etree.SubElement(pic, f'{{{NSPIC}}}blipFill')
            blip = etree.SubElement(bf, f'{{{NSA}}}blip')
            # Add relationship
            img_rel = part.relate_to(img_path, RELS_IMAGE, is_external=False)
            blip.set(f'{{{NSR}}}embed', img_rel)
            etree.SubElement(etree.SubElement(bf, f'{{{NSA}}}stretch'), f'{{{NSA}}}fillRect')
            
            sp = etree.SubElement(pic, f'{{{NSPIC}}}spPr')
            xfrm = etree.SubElement(sp, f'{{{NSA}}}xfrm')
            off = etree.SubElement(xfrm, f'{{{NSA}}}off')
            off.set('x','0'); off.set('y','0')
            ext2 = etree.SubElement(xfrm, f'{{{NSA}}}ext')
            ext2.set('cx', str(cx)); ext2.set('cy', str(cy))
            prst = etree.SubElement(sp, f'{{{NSA}}}prstGeom')
            prst.set('prst', 'rect')
            
            # Add blank paragraph after cover
            blank = etree.SubElement(parent, qn('w:p'))
            parent.remove(blank)
            parent.insert(idx+1, blank)
            
            inserted += 1
            print(f"✅ {cover_file} before '{heading_text[:20]}...'")
            break

try:
    doc.save(NPTH)
    print(f'Done. Covers inserted: {inserted}. Size: {os.path.getsize(NPTH)}')
except Exception as e:
    print(f'Error saving: {e}')
    # Try saving to PTH anyway
    doc.save(PTH)
    print(f'Saved to original. Size: {os.path.getsize(PTH)}')
