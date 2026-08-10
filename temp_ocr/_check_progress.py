import os, json, glob, time
ws = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
for pf in sorted(glob.glob(os.path.join(ws, '*', '_progress.json'))):
    d = json.load(open(pf, encoding='utf-8'))
    done = len(d.get('done', []))
    total = d.get('total', 0)
    mt = time.strftime('%H:%M', time.localtime(os.path.getmtime(pf)))
    pct = done/total*100 if total else 0
    print(f'{d.get("label","?"):<14} {done:>4}/{total:<4} {pct:5.1f}%  更新:{mt}')
