"""Add 招标问询 as business direction"""
import yaml, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\business_lines.yaml'
with open(path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

for node in data['nodes']:
    if node['id'] == 'L6':
        # Add sub-types
        node['sub_types'] = ['招标文件质疑', '政府采购投诉处理', '招标问询代理', '行政复议与诉讼']

        # Add to primary keywords
        kw = node['keywords']
        kw['primary'] = kw['primary'] + ['招标问询', '质疑投诉', '政府采购质疑']
        kw['secondary'] = kw['secondary'] + ['异议处理', '投诉处理', '行政复议', '行政诉讼', '采购文件澄清',
                                               '评审结果质疑', '合同授予争议']

        # Add detection rule
        node['detection_rules'].append({
            'pattern': '(质疑|投诉|异议|问询|复议|诉讼).{0,2}(招标|采购|投标|评审|中标|成交)'
        })

        print(f"  L6 updated: sub_types={node['sub_types']}")
        print(f"  primary: {len(kw['primary'])} keywords, secondary: {len(kw['secondary'])} keywords")
        print(f"  detection_rules: {len(node['detection_rules'])} rules")
        break

data['tree_version'] = data.get('tree_version', 0) + 1
data['last_updated'] = '2026-07-11'

with open(path, 'w', encoding='utf-8') as f:
    yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=200)

print(f"\n✅ tree_version: {data['tree_version']}")
