import os, sys
sys.stdout.reconfigure(encoding='utf-8')

# Read Swiss template
tmpl_path = r'C:\Users\Admin\.openclaw\workspace\skills\guizang-ppt\assets\template-swiss.html'
base_dir = r'C:\Users\Admin\.openclaw\workspace\skills\guizang-ppt'

with open(tmpl_path, 'r', encoding='utf-8') as f:
    tmpl = f.read()

# Check if SLIDES_HERE placeholder exists
if 'SLIDES_HERE' in tmpl:
    print('Found SLIDES_HERE placeholder')
else:
    # Find deck div end
    deck_end = tmpl.find('</div>', tmpl.find('<div id="nav"'))
    if deck_end > 0:
        print(f'Using nav insertion point at {deck_end}')
    else:
        print('Could not find insertion point')
        exit(1)

print(f'Template size: {len(tmpl)} chars')
print('OK - ready for generation')
