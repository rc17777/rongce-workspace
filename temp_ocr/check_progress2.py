import os, json
fp = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\稽查4\_progress.json'
if os.path.exists(fp):
    d = json.load(open(fp))
    done = d.get('done', [])
    print(f'稽查4: {len(done)} / {d.get("total","?")}')
    print(f'最后5个: {done[-5:]}')
else:
    print('progress.json not found')