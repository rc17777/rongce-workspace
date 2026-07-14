"""Validate ingestion modules"""
import sys
sys.path.insert(0, r'C:\Users\scrccpa\.openclaw\workspace\scripts\ingestion')

from taxonomy_manager import get_taxonomy, TaxonomyManager

t = get_taxonomy()
stats = t.get_stats()
print('=== Taxonomy Status ===')
for k, v in stats.items():
    print(f'  {k}: {v}')

lines = t.get_active_lines()
print(f'\n=== Active Business Lines ({len(lines)}) ===')
for l in lines:
    subs = l.get('sub_types', [])
    sub_str = f' ({", ".join(subs)})' if subs else ''
    print(f'  {l["id"]} {l["name"]}{sub_str}')
    print(f'    primary keywords: {len(l.get("keywords", {}).get("primary", []))}')

# Test dedup
print('\n=== Test Dedup ===')
result = TaxonomyManager.deduplicate_lines(
    ['L4', 'L12'],
    [
        {'line_id': 'L4', 'relevance': 'high'},
        {'line_id': 'L11', 'relevance': 'medium'},
        {'line_id': 'L1', 'relevance': 'low'},
    ]
)
print(f'  Input: direct=[L4,L12] + radiation=[L4,L11,L1(low)]')
print(f'  Output: {result}')

# Test Round 1
from ingestion_round1 import classify_round1, extract_doc_number

test_text = """
财政部关于印发《XX专项资金管理办法》的通知
财预〔2026〕15号

各有关单位：
为进一步规范和加强专项资金管理，提高资金使用绩效，根据《预算法》等有关规定，
现制定本办法。专项资金必须专款专用，不得截留挪用...
"""

r1 = classify_round1(test_text, 'XX专项资金管理办法', '财预〔2026〕15号')
print(f'\n=== Test Round 1 ===')
print(f'  Direct hits: {r1.direct_hits}')
print(f'  Matched by: {r1.matched_by}')

dn = extract_doc_number(test_text)
print(f'  Document number: {dn}')
