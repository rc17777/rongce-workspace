import os, json
d = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\稽查文件3'
mds = [f for f in os.listdir(d) if f.endswith('.md')]
print(f'Total files: {len(mds)}/506')
pf = os.path.join(d, '_progress.json')
pd = json.load(open(pf, encoding='utf-8'))
done = pd.get('done', [])
print(f'Progress: {len(done)}/506 ({len(done)/506*100:.1f}%)')
print(f'Last 5: {sorted(done)[-5:]}')
