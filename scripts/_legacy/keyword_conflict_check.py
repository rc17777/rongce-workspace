"""Detect keyword conflicts across business lines"""
import sys, yaml
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\business_lines.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

nodes = data['nodes']

# Check primary keyword overlaps
primary_map = defaultdict(list)
secondary_map = defaultdict(list)
detection_map = defaultdict(list)

for node in nodes:
    lid = node['id']
    name = node['name']
    for kw in node.get('keywords', {}).get('primary', []):
        primary_map[kw].append(lid)
    for kw in node.get('keywords', {}).get('secondary', []):
        secondary_map[kw].append(lid)
    for rule in node.get('detection_rules', []):
        pat = rule.get('pattern', '')
        detection_map[pat].append(lid)

# Report primary conflicts
print("=" * 60)
print("PRIMARY KEYWORD CONFLICTS (shared across >=2 lines)")
print("=" * 60)
conflicts = 0
for kw, lines in sorted(primary_map.items()):
    if len(lines) >= 2:
        conflicts += 1
        names = [n['name'] for n in nodes if n['id'] in lines]
        print(f"  ⚠️  '{kw}' → {', '.join(f'{l}({n})' for l,n in zip(lines,names))}")
if conflicts == 0:
    print("  ✅ No conflicts!")

# Report secondary conflicts
print("\n" + "=" * 60)
print("SECONDARY KEYWORD CONFLICTS")
print("=" * 60)
sconflicts = 0
for kw, lines in sorted(secondary_map.items()):
    if len(lines) >= 2:
        sconflicts += 1
        names = [n['name'] for n in nodes if n['id'] in lines]
        print(f"  ℹ️  '{kw}' → {', '.join(f'{l}({n})' for l,n in zip(lines,names))}")
if sconflicts == 0:
    print("  ✅ No conflicts!")

# Report detection rule overlaps (broad patterns that might match same text)
print("\n" + "=" * 60)
print("DETECTION RULE PATTERN ANALYSIS")
print("=" * 60)
for pat, lines in sorted(detection_map.items(), key=lambda x: len(x[1]), reverse=True):
    names = [n['name'] for n in nodes if n['id'] in lines]
    flag = '⚠️ BROAD' if len(pat) < 15 else ('✅' if len(lines) == 1 else 'ℹ️')
    if len(lines) >= 1:
        print(f"  {flag} [{len(lines)} lines] {pat[:60]} → {', '.join(f'{l}' for l in lines)}")

# Summary
print(f"\n{'-'*60}")
print(f"Summary: {conflicts} primary conflicts, {sconflicts} secondary overlaps")
print(f"Total unique primaries: {len(primary_map)} | secondaries: {len(secondary_map)} | rules: {len(detection_map)}")
