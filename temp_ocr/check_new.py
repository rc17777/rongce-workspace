import os, json, sys
sys.stdout.reconfigure(encoding='utf-8')
out = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
total_done = total_all = 0
for d in sorted(os.listdir(out)):
    dp = os.path.join(out, d)
    if not os.path.isdir(dp): continue
    pf = os.path.join(dp, '_progress.json')
    if os.path.exists(pf):
        with open(pf) as f:
            p = json.load(f)
        done = len(p['done'])
        total = p['total']
        pct = done/total*100
        bar = '#'*int(pct/5) + '-'*(20-int(pct/5))
        print(f'[{bar}] {done:>4}/{total:<4} ({pct:5.1f}%)  {d}')
        total_done += done
        total_all += total
if total_all:
    print(f'\nTotal: {total_done}/{total_all} ({total_done/total_all*100:.1f}%)')
else:
    print('No progress files found - OCR may not have started')
