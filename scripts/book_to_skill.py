#!/usr/bin/env python3
"""Rongce book-to-skill: 文档/书籍 → OpenClaw Skill 编译管线
用法: python book_to_skill.py <文件/目录> [skill名称] [--type 技术书|纯文本]
输出: skills/<slug>/SKILL.md + chapters/ + glossary.md + patterns.md
"""

import sys, os, re, json, argparse, shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ─── 配置 ───
SKILLS_HOME = os.path.expanduser("~/.openclaw/skills")
TOKEN_PER_FILE = {"SKILL_CORE": 3000, "CHAPTER": 800, "GLOSSARY": 1000, "PATTERNS": 800}
SUPPORTED = {'.pdf','.docx','.txt','.md','.html','.htm','.epub','.rst'}

# ─── 提取器 ───
def extract_docx(path):
    try:
        from docx import Document
        return '\n'.join(p.text for p in Document(path).paragraphs if p.text.strip())
    except ImportError:
        raise RuntimeError("需要 python-docx: pip install python-docx")

def extract_pdf(path, tech=False):
    """提取PDF文本。tech模式优先用pymupdf保留结构"""
    if tech:
        try:
            import fitz
            pages = []
            for page in fitz.open(path):
                pages.append(page.get_text("text"))
            return '\n'.join(pages)
        except ImportError:
            pass  # fall through
    # 纯文本模式: pdftotext > PyPDF2 > pdfminer
    for extractor in [_pdftotext, _pypdf2, _pdfminer]:
        try:
            return extractor(path)
        except: continue
    raise RuntimeError("无可用PDF提取器。安装: pip install pymupdf 或 PyPDF2 或 pdfminer.six")

def _pdftotext(path): return os.popen(f'pdftotext "{path}" -', 'r').read()
def _pypdf2(path):
    from PyPDF2 import PdfReader
    return '\n'.join(p.age_text for p in PdfReader(path).pages)
def _pdfminer(path):
    from pdfminer.high_level import extract_text
    return extract_text(path)

def extract_txt(path):
    for enc in ['utf-8', 'gbk', 'utf-16']:
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except: continue
    raise RuntimeError(f"无法解码: {path}")

def extract_md(path):
    return extract_txt(path)

def extract_file(path, tech=False):
    """路由到正确的提取器"""
    ext = Path(path).suffix.lower()
    if ext == '.pdf': return extract_pdf(path, tech), ext
    elif ext == '.docx': return extract_docx(path), ext
    elif ext in {'.txt','.html','.htm','.rst'}: return extract_txt(path), ext
    elif ext == '.md': return extract_md(path), ext
    elif ext == '.epub':
        try:
            import ebooklib; from ebooklib import epub
            book = epub.read_epub(path)
            return '\n'.join(doc.get_content().decode() for doc in book.get_items_of_type(9)), ext
        except: raise RuntimeError("需要 ebooklib: pip install ebooklib")
    raise RuntimeError(f"不支持的格式: {ext}")

# ─── 章节分割 ───
CHAPTER_PATTERNS = [
    re.compile(r'^第[一二三四五六七八九十百千]+[章节]', re.MULTILINE),
    re.compile(r'^Chapter\s+\d+', re.MULTILINE),
    re.compile(r'^第\d+[章节]', re.MULTILINE),
    re.compile(r'^[一二三四五六七八九十]、', re.MULTILINE),
    re.compile(r'^#+\s', re.MULTILINE),
]

def split_chapters(text):
    """尝试自动分割章节。返回 [(标题,内容),...]"""
    for pat in CHAPTER_PATTERNS:
        matches = list(pat.finditer(text))
        if len(matches) >= 3:
            chapters = []
            for i, m in enumerate(matches):
                start = m.start()
                end = matches[i+1].start() if i+1 < len(matches) else len(text)
                title = text[m.start():text.find('\n', m.start()) if text.find('\n', m.start())>0 else m.end()].strip()
                if len(title) > 80: title = title[:80] + '...'
                chapters.append((title, text[start:end].strip()))
            return chapters
    # Fallback: 按空行分块，前N个最长块作为"章节"
    blocks = re.split(r'\n{2,}', text)
    big_blocks = [(f"第{i+1}部分", b) for i, b in enumerate(blocks) if len(b) > 200]
    return big_blocks if len(big_blocks) >= 3 else [("全文", text)]

# ─── 术语提取 ───
def extract_glossary(text, chapters):
    """从文本提取关键术语（中英文、专有名词、法规编号）"""
    terms = set()
    # 法规编号
    for m in re.finditer(r'《([^》]{3,30})》', text):
        terms.add(('法规', m.group(0)))
    # 全大写英文缩写（3-8字符）
    for m in re.finditer(r'\b[A-Z]{3,8}\b', text):
        if m.group() not in {'PDF','DOC','XML','TXT','URL'}:
            terms.add(('缩略语', m.group()))
    # 引号内术语
    for m in re.finditer(r'["\u201c]([^"\u201d]{2,20})["\u201d]', text):
        t = m.group(1).strip()
        if len(t) >= 3 and not re.match(r'^[\d\s\.]+$', t):
            terms.add(('术语', t))
    # 章节关键词提取（每章取最高频的5个非停用词）
    stop = set('的了一是我不们他她它这在有个和就都也还到要为能你上下中把被让给从自对与及其所可之而因由以说但去没有来如如果后前当时候比并很或着过等会可以更只已经虽然因为所以'.split())
    for title, content in chapters[:10]:
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', content)
        from collections import Counter
        for w, _ in Counter(w for w in words if w not in stop).most_common(3):
            terms.add(('关键词', w))
    return sorted(terms, key=lambda x: x[0])

# ─── Skill生成 ───
def generate_skill(title, author, chapters, glossary, skill_dir, tech=False):
    """生成完整Skill文件结构"""
    os.makedirs(f"{skill_dir}/chapters", exist_ok=True)
    slug = os.path.basename(skill_dir)

    # SKILL.md
    core = f"""---
name: {slug}
description: "{title} — 审计知识技能库。按需加载，按章查询。"
source: "{title}"
author: "{author}"
---

# {title}

> 作者：{author} | 编译日期：2026-07-29

## 核心框架

"""
    # 提取前几条关键术语作为"框架"
    frameworks = [(t, w) for cat, (t, w) in enumerate(glossary) if w[0] == '法规' or w[0] == '术语'][:5]
    for f_type, term in glossary:
        if f_type == '法规':
            core += f"- {term}\n"
    core += "\n## 章节索引\n\n| # | 章节 | Token估算 |\n|:--|:--|:--|\n"
    for i, (title, content) in enumerate(chapters[:30], 1):
        tokens = len(content) // 2  # 粗略估算
        chap_slug = f"{i:02d}_{re.sub(r'[^\w\u4e00-\u9fff]+', '_', title[:30]).strip('_')}"
        core += f"| {i} | {title[:40]} | ~{tokens} |\n"
        # 写章节文件
        with open(f"{skill_dir}/chapters/{chap_slug}.md", 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{content[:4000]}")
    core += f"""
## 使用方式

查询指定章节：
```
/skill {slug} 第3章
```

查询术语：
```
/skill {slug} glossary 政府采购
```

全文搜索：
```
/skill {slug} search <关键词>
```
"""
    with open(f"{skill_dir}/SKILL.md", 'w', encoding='utf-8') as f:
        f.write(core)

    # glossary.md
    gl = "# 术语表\n\n"
    for cat, term in glossary:
        gl += f"- **[{cat}]** {term}\n"
    with open(f"{skill_dir}/glossary.md", 'w', encoding='utf-8') as f:
        f.write(gl)

    # patterns.md — 提取方法论/技巧/反模式
    patterns = "# 方法论与模式\n\n"
    # 从章节中提取"审计线索""信号""技巧""陷阱""误区"等关键词所在段落
    for ch_title, ch_content in chapters[:10]:
        for kw in ['线索', '信号', '技巧', '陷阱', '误区', '关键', '注意', '方法', '步骤']:
            for m in re.finditer(rf'[^。]*{kw}[^。]*[。]', ch_content):
                snippet = m.group().strip()[:200]
                if len(snippet) > 20:
                    patterns += f"### {ch_title[:30]} — {kw}\n{snippet}\n\n"
                if len(patterns) > 6000: break
            if len(patterns) > 6000: break
        if len(patterns) > 6000: break
    with open(f"{skill_dir}/patterns.md", 'w', encoding='utf-8') as f:
        f.write(patterns)

    print(f"✅ Skill 已生成: {skill_dir}/")
    print(f"   SKILL.md     (~{TOKEN_PER_FILE['SKILL_CORE']} tokens)")
    print(f"   chapters/    ({len(chapters)} 章)")
    print(f"   glossary.md  ({len(glossary)} 术语)")
    print(f"   patterns.md  (方法论速查)")

# ─── 主流程 ───
def main():
    parser = argparse.ArgumentParser(description='融策 book-to-skill: 文档→Skill编译')
    parser.add_argument('input', nargs='+', help='文件/目录/glob')
    parser.add_argument('--name', '-n', help='Skill名称(slug)，默认从文件名提取')
    parser.add_argument('--type', '-t', choices=['technical','text'], default='text', help='技术书/纯文本')
    parser.add_argument('--output', '-o', help='输出目录，默认 ~/.openclaw/skills/<slug>')
    args = parser.parse_args()

    # 收集输入文件
    files = []
    for inp in args.input:
        p = Path(inp)
        if p.is_dir():
            for ext in SUPPORTED:
                files.extend(p.glob(f'**/*{ext}'))
        elif p.is_file():
            files.append(p)
        else:
            # glob
            files.extend(Path('.').glob(inp))

    if not files:
        print("❌ 未找到支持的文档文件")
        return

    print(f"📖 找到 {len(files)} 个文件")
    tech = (args.type == 'technical')

    # 提取所有文本
    all_text = []
    for f in sorted(files):
        print(f"   提取: {f.name}...", end=' ')
        try:
            text, ext = extract_file(str(f), tech)
            all_text.append(f"=== {f.name} (格式:{ext} 字符:{len(text)}) ===\n{text}")
            print(f"✅ {len(text)}字符")
        except Exception as e:
            print(f"❌ {e}")

    if not all_text:
        print("❌ 所有文件提取失败")
        return

    combined = '\n\n'.join(all_text)

    # 提取元数据
    first_lines = combined[:500]
    title_match = re.search(r'(?:#|title:|Title:)\s*(.+?)$', first_lines, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else Path(str(files[0])).stem
    author_match = re.search(r'(?:作者|Author|author)[:：]\s*(.+?)$', first_lines, re.MULTILINE)
    author = author_match.group(1).strip() if author_match else "未知"

    slug = args.name or re.sub(r'[^\w\u4e00-\u9fff]+', '_', title)[:40].strip('_')
    skill_dir = args.output or os.path.join(SKILLS_HOME, slug)

    print(f"\n📊 总字符: {len(combined):,} | 标题: {title} | Slug: {slug}")
    print(f"🔪 分割章节...")
    chapters = split_chapters(combined)
    print(f"   发现 {len(chapters)} 个章节")
    print(f"📝 提取术语...")
    glossary = extract_glossary(combined, chapters)
    print(f"   发现 {len(glossary)} 个术语")
    print(f"🎨 生成Skill...")
    generate_skill(title, author, chapters, glossary, skill_dir, tech)

if __name__ == '__main__':
    main()
