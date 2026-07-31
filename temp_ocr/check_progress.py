import os, json
out = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
for label in os.listdir(out):
    fp = os.path.join(out, label)
    if not os.path.isdir(fp): continue
    pf = os.path.join(fp, '_progress.json')
    if os.path.exists(pf):
        d = json.load(open(pf))
        print(f"{label}: {len(d.get('done',[]))} / {d.get('total','?')}")
    else:
        mds = [f for f in os.listdir(fp) if f.endswith('.md')]
        print(f"{label}: {len(mds)} md")
