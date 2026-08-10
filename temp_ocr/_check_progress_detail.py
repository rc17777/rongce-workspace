import json
d = json.load(open(r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\稽查文件3\_progress.json', encoding='utf-8'))
done = d.get('done', [])
print(f'Total done: {len(done)}')
print(f'Last 10: {sorted(done)[-10:]}')
