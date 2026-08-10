import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\scrccpa\.openclaw\workspace\temp\build_algorithm_lib_v4.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Extract all algorithm SNs
sns = re.findall(r"'sn':\s*'([^']+)'", text)
print(f'Total algorithm SNs found: {len(sns)}')
print()

# Group by prefix
from collections import Counter
prefixes = Counter(sn.split('-')[0] for sn in sns)
print('By source/prefix:')
for p, cnt in sorted(prefixes.items()):
    print(f'  {p}: {cnt}')

print('\nAll algorithms:')
for i, sn in enumerate(sns, 1):
    # try to find name
    m = re.search(r"'" + re.escape(sn) + r"'.*?'name':\s*'([^']+)'", text)
    name = m.group(1) if m else '?'
    print(f'  {i:2d}. {sn:25s} {name[:60]}')

# Check for duplicates
dups = [sn for sn, cnt in Counter(sns).items() if cnt > 1]
if dups:
    print(f'\n⚠️  DUPLICATE SNs: {dups}')
else:
    print(f'\n✅ All {len(sns)} SNs unique')

# Count v1/v2/v3/v4 
print(f'\nOrigin breakdown:')
v1plus = [sn for sn in sns if sn in ['PERF-OUTLIER-001','PROC-CONCEN-001','BID-PATTERN-001','FUND-FRAUD-001','HR-RF-001','HR-RF-002','REV-PREDICT-001','ENG-SAMPLE-001','ENG-SCORE-001','CHK-RECON-001','ASSET-MATCH-001','SUPV-ANOMALY-001','RULE-MATCH-001']]
v2 = [sn for sn in sns if sn.startswith(('SUPV-POCKET','SUPV-TRAVEL','FUND-SIPHON','CHK-LOSS','PROC-FAKE','PROC-RELATED','CHK-RD','ENG-FINAL','SUPV-WARNING','ENV-CHECKLIST'))]
v3 = [sn for sn in sns if sn.startswith(('SOE-MIDMAN','AGR-INSFAKE','FIN-SHELL','FIN-INSFAKE','ENG-RATIO','MED-BIDRIG','ENV-RS','BUD-CHECKLIST'))]
v4 = [sn for sn in sns if sn.startswith(('SOCIAL-INS','SOCIAL-MAT','SOCIAL-WORK','SOCIAL-WELFARE','BIGDATA-SERVICE','BIGDATA-SQL','PERF-DEVIATION','TRANSFER-TRACE','BOND-PENETRATE'))]
print(f'  v1 (papers): {len(v1plus)}')
print(f'  v2 (references): {len(v2)}')
print(f'  v3 (Obsidian cases): {len(v3)}')
print(f'  v4 (magazine articles): {len(v4)}')
print(f'  TOTAL: {len(v1plus)+len(v2)+len(v3)+len(v4)}')
