import sys, json
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\jz_deep_dive.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print('=== NEW FINDINGS ===')
for f_n in d['new_findings']:
    print('\n--- {} [{}] ---'.format(f_n['id'], f_n['level']))
    print(f_n['finding'])
    if 'detail' in f_n:
        for item in f_n.get('detail', []):
            if isinstance(item, dict):
                print('  {}: {} records, {}/day'.format(item['name'], item['total_records'], item['avg_daily']))
    if 'diagnoses_found' in f_n:
        print('  Diagnoses found: {}'.format(f_n['diagnoses_found']))
    if 'non_jiangzha_patients' in f_n:
        for np in f_n['non_jiangzha_patients'][:10]:
            print('  {} ({}) - {}'.format(np['patient'], np['visits'], np['addresses']))

print('\n=== TOP 15 PATIENTS ===')
for p, cnt in d['all_patients_ranked'][:15]:
    print('  {}: {} visits'.format(p, cnt))

print('\n=== TOP5 DETAILS ===')
for p in d['top5_patient_details']:
    print('\n--- {}: {} visits, avg {} ---'.format(p['patient'], p['total_visits'], round(p['avg_fee'], 1)))
    dates = [v['time'][:10] for v in p['visits']]
    dc = Counter(dates)
    multi = {k: v for k, v in dc.items() if v >= 2}
    if multi:
        print('  SAME-DAY: {}'.format(multi))
    docs = Counter(v['doctor'] for v in p['visits'])
    print('  Doctors: {}'.format(dict(docs)))
    for v in p['visits'][:10]:
        diag = v['diagnosis']
        if diag and len(diag) > 30:
            diag = diag[:30] + '...'
        print('  {} | {} | drug:{} treat:{} total:{} fund:{} | {}'.format(
            v['time'], v['doctor'], v['drug_fee'], v['treat_fee'], v['total_fee'], v['fund_paid'],
            diag if diag else '(no diagnosis)'))

print('\n=== FEE ===')
print(json.dumps(d['fee_analysis'], ensure_ascii=False, indent=2))
print('\n=== INSURANCE ===')
print(json.dumps(d['insurance_analysis'], ensure_ascii=False, indent=2))
print('\n=== MONTHLY ===')
for m, c in d['basic_stats']['monthly_distribution']:
    bar = '#' * (c // 10)
    print('  {}: {} {}'.format(m, c, bar))
