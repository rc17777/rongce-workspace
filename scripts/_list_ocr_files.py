import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')

dirs = [
    (r'E:\2026\审计方法&政策文件\_ocr_output\1中国审计_7期', '中国审计7期'),
    (r'E:\2026\审计方法&政策文件\_ocr_output\2经济责任审计_6期', '经济责任审计6期'),
]

all_files = []
for d, label in dirs:
    files = sorted([f for f in os.listdir(d) if f.endswith('.md')])
    for f in files:
        fp = os.path.join(d, f)
        sz = os.path.getsize(fp)
        all_files.append({'path': fp, 'label': label, 'name': f.replace('.md',''), 'size': sz})

with open(r'C:\Users\scrccpa\.openclaw\workspace\scripts\_ocr_file_list.json', 'w', encoding='utf-8') as f:
    json.dump(all_files, f, ensure_ascii=False, indent=2)

print(f'Total: {len(all_files)} files')
for i, item in enumerate(all_files, 1):
    nm = item['name'][:60]
    print(f'  [{i:02d}] [{item["label"]}] {nm} ({item["size"]}B)')
