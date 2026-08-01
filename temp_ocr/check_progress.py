import os, json
d = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
for b in sorted(os.listdir(d)):
    bp = os.path.join(d, b)
    if os.path.isdir(bp):
        pf = os.path.join(bp, '_progress.json')
        if os.path.exists(pf):
            j = json.load(open(pf, 'r', encoding='utf-8'))
            print('{}: {}/{}'.format(b, len(j['done']), j['total']))
        else:
            print('{}: no progress file'.format(b))