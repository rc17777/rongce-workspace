import os
from docx import Document

SRC = r'C:\Users\scrccpa\Desktop\医保资金政策文件'
KB = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\policies\医保'
OBS = r'C:\Users\scrccpa\Documents\Obsidian Vault\raw\法规政策\医保'

os.makedirs(KB, exist_ok=True)
os.makedirs(OBS, exist_ok=True)

results = []

for f in os.listdir(SRC):
    if not f.endswith('.docx'):
        continue
    src_path = os.path.join(SRC, f)
    doc = Document(src_path)
    text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
    
    # Auto-detect title from first meaningful line
    lines = text.split('\n')
    title = lines[0].strip()
    
    # Generate safe filename
    safe_name = f.replace('.docx', '.md')
    # Remove special chars for obsidian compatibility
    # Just keep it as-is since both systems handle Chinese
    
    # YAML frontmatter
    frontmatter = '---\n'
    frontmatter += 'title: "' + title + '"\n'
    frontmatter += 'category: 医保政策\n'
    frontmatter += 'source: 国务院/国家医保局\n'
    frontmatter += 'sync_date: 2026-07-07\n'
    frontmatter += '---\n\n'
    
    md_content = frontmatter + text
    
    # Write to KB
    kb_path = os.path.join(KB, safe_name)
    with open(kb_path, 'w', encoding='utf-8') as out:
        out.write(md_content)
    
    # Write to Obsidian
    obs_path = os.path.join(OBS, safe_name)
    with open(obs_path, 'w', encoding='utf-8') as out:
        out.write(md_content)
    
    results.append(safe_name + ': OK (' + str(len(text)) + ' chars)')

for r in results:
    print(r)
print('\nDone. KB:', KB, '| Obsidian:', OBS)
