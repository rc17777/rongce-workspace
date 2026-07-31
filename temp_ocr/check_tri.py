import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
fp = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\triangle_compare.json'
if os.path.exists(fp):
    sz = os.path.getsize(fp)
    print(f'File: {sz} bytes')
    with open(fp, 'r', encoding='utf-8') as f:
        d = json.load(f)
    for k, r in d.get('per_institution', {}).items():
        name = {'jz':'降扎乡','jsk':'金世康','xmz':'辖曼镇'}[k]
        print(name + ': ' + str(r.get('total',0)) + ' records, ' + str(r.get('patients',0)) + ' patients, avg fee ' + str(r.get('avg_fee',0)) + ', diag_empty ' + str(r.get('diag_empty_pct',0)) + '%')
        print('  Doctors: ' + str(r.get('doctors',[])))
        print('  Years: ' + str(r.get('years',{})))
        print('  Fee buckets: ' + str(r.get('fee_buckets',{})))
        print('  Monthly: ' + str(r.get('monthly',[])[-6:]))
        print('  Top days: ' + str(r.get('top_days',[])[:5]))
        print()
    print('Overlap: ' + str(d.get('overlap',{})))
    print('All 3 shared: ' + str(d.get('all3_count',0)))
    print('JZ+JSK shared count: ' + str(len(d.get('jz_jsk_shared',[]))))
    print('JZ+XMZ shared count: ' + str(len(d.get('jz_xmz_shared',[]))))
    print('Total unique: ' + str(d.get('total_unique_patients',0)))
else:
    print('NOT FOUND')
    # Try to find any existing results
    jz_fp = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\jz_deep_dive.json'
    if os.path.exists(jz_fp):
        print('jz_deep_dive.json exists: ' + str(os.path.getsize(jz_fp)))
