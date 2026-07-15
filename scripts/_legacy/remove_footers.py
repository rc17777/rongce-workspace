# -*- coding: utf-8 -*-
"""Remove footers from all slides except contact page."""
import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

slides_dir = r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\slides'
keep_footer = {'12-contact.html', '01-cover.html'}

for fname in sorted(os.listdir(slides_dir)):
    if not fname.endswith('.html'):
        continue
    fpath = os.path.join(slides_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if fname in keep_footer:
        print(f'  Kept footer in {fname}')
        continue
    
    # Remove footer divs
    new_content = re.sub(r'<div class="footer[^"]*">.*?</div>\s*', '', content, flags=re.DOTALL)
    
    if new_content != content:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'  Removed footer from {fname}')
    else:
        print(f'  No footer in {fname}')

print('\nDone.')