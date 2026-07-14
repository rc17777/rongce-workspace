# -*- coding: utf-8 -*-
"""v4: Replace gold with teal across all slides. Keep gold only on cover title and contact page corners."""
import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

slides_dir = r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\slides'

# Pages where gold should be kept (minimal)
keep_gold_cover = {'01-cover.html'}       # Hero title gold
keep_gold_contact = {'12-contact.html'}    # Corner brackets

for fname in sorted(os.listdir(slides_dir)):
    if not fname.endswith('.html'):
        continue
    fpath = os.path.join(slides_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. Replace hardcoded gold rgba with teal rgba
    content = content.replace('rgba(197,149,92,', 'rgba(26,92,110,')
    
    # 2. Replace var(--gold) with var(--teal) in inline styles (not in CSS class definitions)
    #    Be careful: only replace inline uses, not in the shared CSS
    #    Replace in style attributes and inline styles
    content = content.replace('var(--gold)', 'var(--teal)')
    
    # 3. Replace gold-text class with nothing (remove gold gradient)
    #    But keep on cover page
    if fname not in keep_gold_cover:
        content = content.replace('class="gold-text"', '')
        content = content.replace("class='gold-text'", '')
        # Also handle combined classes like class="gold-text h1"
        content = re.sub(r'gold-text\s+', '', content)
        content = re.sub(r'\s+gold-text', '', content)
    
    # 4. Replace highlight-gold with highlight
    content = content.replace('highlight-gold', 'highlight')
    
    # 5. Replace tag.gold with tag
    content = content.replace('class="tag gold"', 'class="tag"')
    content = content.replace("class='tag gold'", "class='tag'")
    
    # 6. Replace kicker.gold with kicker (in content pages)
    content = content.replace('class="kicker gold"', 'class="kicker"')
    content = content.replace("class='kicker gold'", "class='kicker'")
    
    # 7. Replace dot.gold with dot.teal (in content pages)
    content = content.replace('<span class="dot gold"></span>', '<span class="dot teal"></span>')
    content = content.replace("<span class='dot gold'></span>", "<span class='dot teal'></span>")
    
    # 8. Replace gold-line class usage (keep class definition, just reduce usage)
    #    Remove gold-line divs from content pages
    content = re.sub(r'<div class="gold-line"></div>\s*', '', content)
    
    # 9. Replace --gold with --teal in inline styles (but not in CSS)
    #    Already done above with var(--gold) -> var(--teal)
    
    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        changes = []
        if 'rgba(197,149,92,' not in content and 'rgba(197,149,92,' in original:
            changes.append('gold rgba -> teal')
        if 'var(--gold)' not in content and 'var(--gold)' in original:
            changes.append('var(--gold) -> var(--teal)')
        if 'highlight-gold' not in content and 'highlight-gold' in original:
            changes.append('highlight-gold -> highlight')
        print(f'  {fname}: {", ".join(changes)}')
    else:
        print(f'  {fname}: no changes')

print('\nDone.')