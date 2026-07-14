import sys, os, copy
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PTH = r'D:\openclaw-workspace\bid_aba\阿坝州财政局竣工财务决算审核_投标方案.docx'

doc = Document(PTH)
body = doc.element.body

# Build element index: find all paragraphs with heading info
elements = []  # (xml_element, is_heading, heading_level, heading_text)
for el in body:
    tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
    if tag != 'p':
        elements.append((el, False, 0, ''))
        continue
    
    pPr = el.find(qn('w:pPr'))
    h_text = ''
    h_level = 0
    is_heading = False
    
    if pPr is not None:
        ps = pPr.find(qn('w:pStyle'))
        if ps is not None:
            val = ps.get(qn('w:val'))
            if val and val.startswith('Heading'):
                is_heading = True
                level = val.replace('Heading', '')
                try:
                    h_level = int(level)
                except:
                    pass
                r_elem = el.find(qn('w:r'))
                if r_elem is not None:
                    t_elem = r_elem.find(qn('w:t'))
                    if t_elem is not None and t_elem.text:
                        h_text = t_elem.text

    elements.append((el, is_heading, h_level, h_text))

# Find the appendix section
appendix_start = -1
appendix_end = len(elements)
for i, (el, is_h, level, text) in enumerate(elements):
    if is_h and level == 1 and '附：项目建设管理专题分析' in text:
        appendix_start = i
    if appendix_start >= 0 and i > appendix_start and is_h and level == 1 and '附' not in text:
        appendix_end = i
        break

print(f"Appendix: elements[{appendix_start}:{appendix_end}]")

# Find H2 topics within appendix
appendix_topics = []
for i in range(appendix_start + 1, appendix_end):
    el, is_h, level, text = elements[i]
    if is_h and level == 2:
        appendix_topics.append((i, text))

print(f"Found {len(appendix_topics)} appendix topics:")
for idx, txt in appendix_topics:
    print(f"  [{idx}] {txt}")

# Define topic -> chapter mapping  
topic_to_chapter = {
    '阿坝州区域发展与项目特征': '一、项目理解与总体思路',
    '基本建设财务规则体系': '三、审核范围与审核内容',
    '政府投资项目概算管理': '三、审核范围与审核内容',
    '工程造价管理与控制': '三、审核范围与审核内容',
    '工程价款支付与结算': '三、审核范围与审核内容',
    '建设资金管理与审计': '四、审核方法与技术路线',
    '竣工财务决算编制与审核': '三、审核范围与审核内容',
    '资产移交与档案管理': '三、审核范围与审核内容',
    '专项审核领域': '四、审核方法与技术路线',
    '项目监督与绩效评价': '四、审核方法与技术路线',
    '建设管理与内控': '七、审计管理制度与质量保证',
    '合同管理': '三、审核范围与审核内容',
    '物资采购管理': '四、审核方法与技术路线',
    '高原施工专题': '六、重点难点分析与对策',
    '竣工验收与交付': '三、审核范围与审核内容',
    '法律法规专题': '二、审核依据与政策解读',
    '项目管理创新': '八、公司概况与服务能力',
    '数据与信息化': '五、审核程序与进度安排',
}

# Find each H1 chapter's last element position
chapter_positions = {}
for i, (el, is_h, level, text) in enumerate(elements):
    if is_h and level == 1:
        # Find next H1
        next_h1 = len(elements)
        for j in range(i + 1, len(elements)):
            if elements[j][1] and elements[j][2] == 1:
                next_h1 = j
                break
        chapter_positions[text] = (el, i, next_h1)

print(f"\nChapter positions: {list(chapter_positions.keys())}")

# Now do the moving:
# For each appendix topic, find the target chapter and insert the content
# We do this by moving XML elements

# Strategy: We'll work backwards from end of appendix to avoid index shifting issues
# For each topic in the appendix:
#   1. Extract topic heading + content elements
#   2. Find target chapter's insertion point (before the next chapter's H1)
#   3. Insert there
# After all moved, remove the appendix header

# Process in reverse order (from end to start of appendix)
topics_processed = []
for topic_idx, topic_text in reversed(appendix_topics):
    # Find topic end (next H2 or end of appendix)
    topic_end = appendix_end
    for j in range(topic_idx + 1, appendix_end):
        if elements[j][1] and elements[j][2] == 2:
            topic_end = j
            break
    
    # Get elements to move: from topic_idx to topic_end-1
    els_to_move = elements[topic_idx:topic_end]
    
    chapter = topic_to_chapter.get(topic_text)
    if not chapter or chapter not in chapter_positions:
        print(f"  SKIP: {topic_text} -> {chapter}")
        continue
    
    # Find insertion point: before the next H1 after target chapter
    target_el, t_start, t_end = chapter_positions[chapter]
    # Insert before the first element of the next chapter (or at end of body)
    insert_before = None
    if t_end < appendix_start:
        insert_before = elements[t_end][0]
    
    if insert_before is None:
        print(f"  SKIP: cannot find insertion point for {topic_text} -> {chapter}")
        continue
    
    # Move elements (copy and insert, then mark for deletion)
    insert_idx = list(body).index(insert_before)
    
    for m_el, _, _, _ in els_to_move:
        # Skip image paragraphs (they have drawing elements)
        drawing = m_el[0].find('.//' + qn('w:drawing'))
        if drawing is not None:
            continue
        # Deep copy
        copied = copy.deepcopy(m_el[0])
        body.insert(insert_idx, copied)
        insert_idx += 1
    
    # Add a spacer paragraph
    spacer = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:after'), '200')
    pPr.append(spacing)
    spacer.append(pPr)
    body.insert(insert_idx, spacer)
    
    topics_processed.append((topic_text, chapter, len(els_to_move)))
    print(f"  ✅ {topic_text} ({len(els_to_move)} el) -> {chapter}")

# Now remove appendix elements (including the heading)
# Mark which elements to remove
to_remove = set()
for i in range(appendix_start, appendix_end):
    el = elements[i][0]
    # Check for images - keep them
    drawing = el.find('.//' + qn('w:drawing'))
    if drawing is not None:
        continue
    to_remove.add(el)

# Also remove the appendix H1 heading
# (elements[appendix_start] is the "附" heading)
for el in to_remove:
    try:
        body.remove(el)
    except:
        pass

print(f"\nSummary: {len(topics_processed)} topics merged into chapters")
for topic, ch, count in topics_processed:
    print(f"  {topic} ({count} paragraphs) -> {ch}")

doc.save(PTH)
print(f'Saved! Size: {os.path.getsize(PTH)}')
