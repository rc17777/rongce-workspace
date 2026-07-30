import os, json, sys
sys.stdout.reconfigure(encoding='utf-8')

out = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output'
for d in sorted(os.listdir(out)):
    dp = os.path.join(out, d)
    if os.path.isdir(dp):
        pf = os.path.join(dp, '_progress.json')
        if os.path.exists(pf):
            with open(pf) as f:
                p = json.load(f)
            done = len(p['done'])
            total = p['total']
            print(f'{d}: {done}/{total}')
        else:
            mds = [f for f in os.listdir(dp) if f.endswith('.md')]
            print(f'{d}: {len(mds)} md files')
