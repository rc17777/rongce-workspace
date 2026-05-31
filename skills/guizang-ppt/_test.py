import os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Admin\.openclaw\workspace\skills\guizang-ppt'
with open(os.path.join(base, 'assets', 'template-swiss.html'), 'r', encoding='utf-8') as f:
    tmpl = f.read()
print(f'Template: {len(tmpl)} chars')
print(f'Has SLIDES_HERE: {"SLIDES_HERE" in tmpl}')
if len(tmpl) > 10000:
    print('Template loaded OK')
