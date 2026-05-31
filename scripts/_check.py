import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'D:\openclaw-workspace\output\宿舍维修项目串标分析\分析数据.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== All bidders (from metadata) ===')
for i, (k, v) in enumerate(sorted(data['metadata'].items()), 1):
    pages = v.get('pages', '?')
    author = v.get('Author', '?')
    created = v.get('CreationDate', '?')
    print(f'{i:2d}. {k} | Author={author} | Created={created} | Pages={pages}')

print()
print(f'Prices extracted: {len(data["prices"])} / {len(data["metadata"])}')
for k, v in data['prices'].items():
    print(f'  {k}: {v}')
