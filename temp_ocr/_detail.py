import os,json,time,glob
out=r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new'
recent=[]
for d in os.listdir(out):
    dp=os.path.join(out,d)
    if not os.path.isdir(dp): continue
    pf=os.path.join(dp,'_progress.json')
    if not os.path.exists(pf): continue
    mt=os.path.getmtime(pf)
    dct=json.load(open(pf,encoding='utf-8'))
    done=len(dct.get('done',[])); total=dct.get('total',0)
    md=len(glob.glob(os.path.join(dp,'p*.md')))
    recent.append((mt,d,done,total,md))
recent.sort(reverse=True)
for mt,name,done,total,md in recent:
    ts=time.strftime('%H:%M:%S',time.localtime(mt))
    pct=f'{done/total*100:.0f}%' if total else '-'
    print(f'  {ts}  {name[:45]:<47} {done:>4}/{total:<4} ({pct})  .md:{md}')
