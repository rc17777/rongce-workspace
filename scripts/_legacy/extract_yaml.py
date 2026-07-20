"""Extract YAML from design doc and write standalone business_lines.yaml"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\INGESTION_V2_DESIGN.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Find first ```yaml block after "### 2.1"
start_marker = '### 2.1 业务线树'
start_idx = content.find(start_marker)
if start_idx == -1:
    print('Start marker not found!')
    sys.exit(1)

# Find ```yaml after the marker
yaml_start = content.find('```yaml', start_idx)
if yaml_start == -1:
    print('```yaml not found!')
    sys.exit(1)

# Find closing ```
yaml_content_start = yaml_start + len('```yaml\n')
yaml_end = content.find('```', yaml_content_start)
if yaml_end == -1:
    print('Closing ``` not found!')
    sys.exit(1)

yaml_content = content[yaml_content_start:yaml_end].strip()

# Fix tree_version
yaml_content = yaml_content.replace('tree_version: 13', 'tree_version: 14')

outpath = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\business_lines.yaml'
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(yaml_content)
print(f'Wrote {len(yaml_content)} chars to {outpath}')
