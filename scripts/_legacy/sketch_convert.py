"""Batch add sketch=1 to drawio mxCell styles"""
import re, os, glob

def add_sketch_to_file(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    content = raw.decode('utf-8', errors='replace')
    
    def add_sketch(match):
        full = match.group(0)
        style_attr = match.group(1)
        styles = match.group(2)
        close = match.group(3)
        if 'sketch=1' in styles:
            return full
        new_styles = 'sketch=1;' + styles
        return f'{style_attr}"{new_styles}"{close}'
    
    content = re.sub(
        r'(style=)(")([^"]*)(")',
        add_sketch,
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

targets = [
    r'D:\openclaw-workspace\data\audit-bench\diagrams\*.drawio',
    r'D:\openclaw-workspace\output\test-critic*.drawio',
]

count = 0
for pattern in targets:
    for f in glob.glob(pattern):
        add_sketch_to_file(f)
        count += 1
        print(f'OK {os.path.basename(f)}')

print(f'All done! {count} files converted.')
