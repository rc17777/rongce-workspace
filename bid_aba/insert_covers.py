import sys, os, copy
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree

PTH = r'D:\openclaw-workspace\bid_aba\阿坝州财政局竣工财务决算审核_投标方案.docx'
IMG = r'D:\openclaw-workspace\bid_aba\work_dir'

doc = Document(PTH)

# Map chapter headings to cover images
chapter_covers = {
    '一、项目理解与总体思路': 'cover1-intro.drawio.png',
    '二、审核依据与政策解读': 'cover2-laws.drawio.png',
    '三、审核范围与审核内容': 'cover3-scope.drawio.png',
    '四、审核方法与技术路线': 'cover4-methods.drawio.png',
    '五、审核程序与进度安排': 'cover4-methods.drawio.png',  # same cover
    '六、重点难点分析与对策': 'cover5-quality.drawio.png',
    '七、审计管理制度与质量保证': 'cover5-quality.drawio.png',
    '八、公司概况与服务能力': 'cover6-company.drawio.png',
    '九、项目团队配备': 'cover6-company.drawio.png',
    '十、类似业绩与履约能力': 'cover7-performance.drawio.png',
    '十一、服务承诺与保障措施': 'cover7-performance.drawio.png',
}

# Find Heading 1 paragraphs and insert cover images before them
# python-docx doesn't support inserting before easily, but we can manipulate the XML

body = doc.element.body
paragraphs = list(body)
h1_indices = []
for i, el in enumerate(paragraphs):
    tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
    if tag == 'p':
        # Check if it's a heading 1
        pPr = el.find(qn('w:pPr'))
        if pPr is not None:
            pStyle = pPr.find(qn('w:pStyle'))
            if pStyle is not None and pStyle.get(qn('w:val')) == 'Heading1':
                text_el = el.find(qn('w:r')) 
                if text_el is not None:
                    t = text_el.find(qn('w:t'))
                    if t is not None and t.text:
                        h1_indices.append((i, t.text))

print(f"Found {len(h1_indices)} H1 headings")
for idx, text in h1_indices:
    print(f"  {idx}: {text[:50]}")

# Now insert images before each matching heading
# We need to insert drawio: picture elements
# Since this is complex with python-docx, let's use a helper

def insert_pic_before(doc, body, before_elem, img_path, width_inches=6.5):
    """Insert an image before a specific element in the document body"""
    if not os.path.exists(img_path):
        return False
    
    # Create a new paragraph with the image
    new_p = OxmlElement('w:p')
    
    # Add paragraph properties for center alignment
    pPr = OxmlElement('w:pPr')
    jc = OxmlElement('w:jc')
    jc.set(qn('w:val'), 'center')
    pPr.append(jc)
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:after'), '200')
    spacing.set(qn('w:before'), '200')
    pPr.append(spacing)
    new_p.append(pPr)
    
    # Create the picture run
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    r.append(rPr)
    
    # Add the drawing element
    drawing = OxmlElement('w:drawing')
    
    # WPML: inline shape
    wp = OxmlElement('wp:inline')
    wp.set(qn('xmlns:wp'), 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing')
    wp.set(qn('distT'), '0')
    wp.set(qn('distB'), '0')
    wp.set(qn('distL'), '0')
    wp.set(qn('distR'), '0')
    
    # extent
    extent = OxmlElement('wp:extent')
    cx = int(width_inches * 914400)
    cy = int(width_inches * 914400 * 300 / 1100)  # 300/1100 aspect ratio
    extent.set(qn('cx'), str(cx))
    extent.set(qn('cy'), str(cy))
    wp.append(extent)
    
    # effectExtent
    eff = OxmlElement('wp:effectExtent')
    eff.set(qn('l'), '0')
    eff.set(qn('t'), '0')
    eff.set(qn('r'), '0')
    eff.set(qn('b'), '0')
    wp.append(eff)
    
    # docPr
    docPr = OxmlElement('wp:docPr')
    docPr.set(qn('id'), '1')
    docPr.set(qn('name'), 'Picture')
    wp.append(docPr)
    
    # graphic
    graphic = OxmlElement('a:graphic')
    graphic.set(qn('xmlns:a'), 'http://schemas.openxmlformats.org/drawingml/2006/main')
    
    # graphicData
    gd = OxmlElement('a:graphicData')
    gd.set(qn('uri'), 'http://schemas.openxmlformats.org/drawingml/2006/picture')
    
    # picture
    pic = OxmlElement('pic:pic')
    pic.set(qn('xmlns:pic'), 'http://schemas.openxmlformats.org/drawingml/2006/picture')
    
    # nvPicPr
    nv = OxmlElement('pic:nvPicPr')
    cNvPr = OxmlElement('pic:cNvPr')
    cNvPr.set(qn('id'), '0')
    cNvPr.set(qn('name'), 'Picture 1')
    nv.append(cNvPr)
    cNvPicPr = OxmlElement('pic:cNvPicPr')
    nv.append(cNvPicPr)
    pic.append(nv)
    
    # blipFill
    blipFill = OxmlElement('pic:blipFill')
    blip = OxmlElement('a:blip')
    blip.set(qn('r:embed'), 'rId1')
    blip.set(qn('xmlns:r'), 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
    blipFill.append(blip)
    stretch = OxmlElement('a:stretch')
    fillRect = OxmlElement('a:fillRect')
    stretch.append(fillRect)
    blipFill.append(stretch)
    pic.append(blipFill)
    
    # spPr
    spPr = OxmlElement('pic:spPr')
    xfrm = OxmlElement('a:xfrm')
    off = OxmlElement('a:off')
    off.set(qn('x'), '0')
    off.set(qn('y'), '0')
    xfrm.append(off)
    ext = OxmlElement('a:ext')
    ext.set(qn('cx'), str(cx))
    ext.set(qn('cy'), str(cy))
    xfrm.append(ext)
    spPr.append(xfrm)
    prstGeom = OxmlElement('a:prstGeom')
    prstGeom.set(qn('prst'), 'rect')
    spPr.append(prstGeom)
    noFill = OxmlElement('a:noFill')
    spPr.append(noFill)
    pic.append(spPr)
    
    gd.append(pic)
    graphic.append(gd)
    wp.append(graphic)
    drawing.append(wp)
    r.append(drawing)
    new_p.append(r)
    
    # Insert before the target element
    body.insert(list(body).index(before_elem), new_p)
    
    # Also add a blank paragraph after for spacing
    blank = OxmlElement('w:p')
    blankPPr = OxmlElement('w:pPr')
    blankSpacing = OxmlElement('w:spacing')
    blankSpacing.set(qn('w:after'), '200')
    blankPPr.append(blankSpacing)
    blank.append(blankPPr)
    body.insert(list(body).index(before_elem), blank)
    
    return True

# This manual XML approach is fragile. Let me instead use python-docx's paragraph-level operation
# which is simpler: add the image at the end of previous section

# Actually let me try a much simpler approach: 
# Just replace the H1 section with the cover image before the heading text
# I'll use a "section intro" approach - add a paragraph before each H1

def add_image_before_h1(doc, heading_text, img_filename):
    """Add image paragraph before the first paragraph that contains heading_text"""
    img_path = os.path.join(IMG, img_filename)
    if not os.path.exists(img_path):
        print(f"  WARN: {img_path} not found")
        return
    
    for p in doc.paragraphs:
        if heading_text in p.text:
            # Add image paragraph before this heading
            # Get the element
            parent = p._element.getparent()
            idx = list(parent).index(p._element)
            
            # Create image paragraph
            new_p = OxmlElement('w:p')
            # Center alignment
            pPr = OxmlElement('w:pPr')
            jc = OxmlElement('w:jc')
            jc.set(qn('w:val'), 'center')
            pPr.append(jc)
            new_p.append(pPr)
            
            # Add image
            r = OxmlElement('w:r')
            rPr = OxmlElement('w:rPr')
            r.append(rPr)
            drawing = OxmlElement('w:drawing')
            inline = OxmlElement('wp:inline')
            inline.set(qn('xmlns:wp'), 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing')
            extent = OxmlElement('wp:extent')
            cx = int(6.5 * 914400)
            cy = int(6.5 * 300 / 1100 * 914400)
            extent.set(qn('cx'), str(cx))
            extent.set(qn('cy'), str(cy))
            inline.append(extent)
            docPr = OxmlElement('wp:docPr')
            docPr.set(qn('id'), '100')
            docPr.set(qn('name'), img_filename)
            inline.append(docPr)
            graphic = OxmlElement('a:graphic')
            graphic.set(qn('xmlns:a'), 'http://schemas.openxmlformats.org/drawingml/2006/main')
            gd = OxmlElement('a:graphicData')
            gd.set(qn('uri'), 'http://schemas.openxmlformats.org/drawingml/2006/picture')
            graphic.append(gd)
            inline.append(graphic)
            drawing.append(inline)
            r.append(drawing)
            new_p.append(r)
            
            # Insert before heading
            parent.insert(idx, new_p)
            print(f"  Inserted {img_filename} before '{heading_text}'")
            break

# Insert covers
for heading, cover_file in chapter_covers.items():
    add_image_before_h1(doc, heading, cover_file)

doc.save(PTH)
print(f'Saved. size={os.path.getsize(PTH)}')
