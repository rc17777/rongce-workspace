import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\plan_sections.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print('=== 1. COUNTY SUMMARY ===')
cs = d['county_summary']
print('Total records: ' + str(cs['total_records']))
print('Total fee: ' + str(cs['total_fee']))
print('Total fund (pooling): ' + str(cs['total_fund']))
print('Medical rescue: ' + str(cs['total_medical_rescue']))
print('Big illness: ' + str(cs['total_big_illness']))
print('Personal acct: ' + str(cs['total_personal_acct']))
print('Personal cash: ' + str(cs['total_personal_cash']))
print('Unique institutions: ' + str(cs['unique_institutions']))
print()
print('By medical type:')
for mt, v in sorted(cs['by_med_type'].items(), key=lambda x: -x[1]['fee']):
    print('  ' + mt + ': ' + str(v['count']) + ' recs, fee ' + str(v['fee']) + ', fund ' + str(v['fund']))

print('\n=== 2. INPATIENT ===')
ip = d['inpatient']
print('Total inpatient: ' + str(ip['total']))
print('Same-day discharge (<=1 day): ' + str(ip['same_day_discharge']) + ' (' + str(ip['same_day_pct']) + '%)')
print('Total inpatient fee: ' + str(ip['total_fee']))
print('Total inpatient fund: ' + str(ip['total_fund']))
print()
print('Hospital days distribution:')
for days, cnt in ip['hospital_days_top'][:15]:
    print('  ' + str(days) + ' days: ' + str(cnt))
print()
print('Fee buckets:')
for k, v in ip['fee_buckets'].items():
    print('  ' + k + ': ' + str(v))
print()
print('Top inpatient institutions:')
for inst, cnt in ip['top_institutions'][:15]:
    print('  ' + inst[:40] + ': ' + str(cnt) + ' recs')

print('\n=== 3. SUSPICIOUS INPATIENT (Same-day discharge top) ===')
for r in d['suspicious_inpatient'][:15]:
    print('  ' + r['name'] + '(' + r['cert'] + ') ' + r['date'] + ' ' + r['inst'][:25] + ' days:' + str(r['days']) + ' fee:' + str(r['total_fee']) + ' fund:' + str(r['fund_paid']))

print('\n=== 4. DUPLICATE REIMBURSEMENT ===')
dup = d['duplicate']
print('Cross-inst same day patients: ' + str(dup['cross_inst_same_day_count']))
print('Multi-channel patients (2+ fund sources): ' + str(dup['multi_channel_patients']))
print()
print('Top cross-inst same day:')
for x in dup['cross_inst_same_day_top'][:15]:
    print('  ' + x['key'] + ': ' + str(x['records']) + ' recs, ' + str(x['institutions']) + ', funds:' + str(x['total_funds']))
    for s in x['sample'][:3]:
        print('    ' + s['name'] + ' ' + s['inst'][:25] + ' fee:' + str(s['fee']) + ' fund:' + str(s['fund']))

print('\nTop multi-channel patients:')
for m in d['multi_fund_top'][:15]:
    print('  ' + m['patient'] + ': ' + str(m['channels']) + ' channels, fund:' + str(m['fund']) + ', big_illness:' + str(m['big_illness']) + ', rescue:' + str(m['rescue']) + ', records:' + str(m['records']))

print('\n=== 5. REMOTE MEDICAL ===')
rm = d['remote']
print('Total remote: ' + str(rm['total']) + ' (' + str(round(rm['total']/cs['total_records']*100,1)) + '%)')
print('Remote total fee: ' + str(rm['total_fee']))
print('Remote total fund: ' + str(rm['total_fund']))
print('Top remote institutions:')
for inst, cnt in rm['top_institutions'][:15]:
    print('  ' + inst[:50] + ': ' + str(cnt))

print('\n=== 6. INSTITUTION RANKING (Top 20 by fee) ===')
for i, inst in enumerate(d['institution_ranking'][:20]):
    print('  ' + str(i+1) + '. ' + inst['name'][:35] + ': recs:' + str(inst['total_records']) + ' fee:' + str(inst['total_fee']) + ' fund:' + str(inst['fund_paid']) + ' patients:' + str(inst['patients']) + ' zero_diag:' + str(inst['zero_diag_pct']) + '%')

print('\n=== 7. SPECIAL POPULATIONS ===')
sp = d['special_pop']
print('Special types (top):')
for t, c in sp['special_types'][:10]:
    print('  ' + t + ': ' + str(c))
print('Rescue types (top):')
for t, c in sp['rescue_types'][:10]:
    print('  ' + t + ': ' + str(c))
