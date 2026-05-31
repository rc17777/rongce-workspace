import json
with open(r'D:\openclaw-workspace\output\contract_analysis\contract_nlp_ocr_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== OCR Extraction Summary ===")
for name, info in list(data['nlp_details'].items()):
    text_len = info['text_length']
    clauses = info['clauses_count']
    risks = info['risks_count']
    method = info['method']
    cls = info.get('clauses', {})
    risk_list = info.get('risks', [])
    print(f"\n[{method}] {name[:60]}")
    print(f"  chars={text_len}, clauses={clauses}, risks={risks}")
    if cls:
        print(f"  clauses found: {list(cls.keys())}")
    for r in risk_list:
        print(f"  risk: [{r['级别']}] {r['类型']}")
