import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\jsk_deep_dive.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print('=== BASIC ===')
print('Total records: ' + str(d['total_records']))
print('Total patients: ' + str(d['total_patients']))
print('Avg/patient: ' + str(d['avg_per_patient']))
print('Total fee: ' + str(d['total_fee_all']))
print('Total fund: ' + str(d['total_fund_all']))

print('\n=== TOP 15 PATIENTS ===')
for p in d['top20_patients'][:15]:
    print('  ' + p['patient'] + ': ' + str(p['visits']) + ' visits, total ' + str(p['total_fee']) + ', avg ' + str(p['avg_fee']) + ', same-day-multi: ' + str(p['same_day_count']) + ' days')
    print('    Years: ' + str(p['years']))
    if p['same_day_details']:
        print('    Multi-days: ' + str(p['same_day_details']))

print('\n=== HOURLY ===')
for h, c in d['hourly_distribution']:
    bar = '#' * (c // 50)
    print('  ' + str(h).rjust(2) + 'h: ' + str(c).rjust(5) + ' ' + bar)

print('\n=== WEEKDAY ===')
for w, c in d['weekday_distribution']:
    print('  ' + w + ': ' + str(c))

print('\n=== MONTHLY BY YEAR ===')
for y, mdata in d['monthly_by_year'].items():
    print('  --- ' + y + ' ---')
    for m, c in mdata:
        bar = '#' * (c // 50)
        print('    ' + m + ': ' + str(c).rjust(5) + ' ' + bar)

print('\n=== FEE BUCKETS ===')
for k, v in d['fee_buckets'].items():
    print('  ' + k + ': ' + str(v))

print('\n=== INSURANCE ===')
for k, v in d['insurance_types'].items():
    print('  ' + k + ': ' + str(v))

print('\n=== TOP TOWNSHIPS ===')
for t, c in d['top_townships'][:15]:
    print('  ' + t + ': ' + str(c))

print('\n=== DAY 2025-11-10 (126 visits) ===')
d11 = d['day_2025_11_10']
print('  Total: ' + str(d11['total']) + ' records, ' + str(d11['patients']) + ' patients')
print('  Fee range: ' + str(d11['fee_range']) + ', avg: ' + str(d11['avg_fee']))
print('  Total fee: ' + str(d11['total_fee']) + ', fund: ' + str(d11['total_fund']))
print('  Hourly: ' + str(d11['hourly']))
print('  First 15 records:')
for r in d11['sample_records'][:15]:
    print('    ' + r['name'] + '(' + r['cert'] + ') ' + r['time'] + ' ' + str(r['fee']))

print('\n=== TOP BUSIEST DAYS ===')
for d_t in d['top_busiest_days']:
    print('  ' + d_t['date'] + ' (' + d_t['weekday'] + '): ' + str(d_t['count']) + ' visits, ' + str(d_t['patients']) + ' patients, ' + str(d_t['same_day_multi']) + ' same-day-multi, hours ' + d_t['hour_range'] + ', avg ' + str(d_t['avg_fee']))
