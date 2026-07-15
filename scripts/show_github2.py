import json, os

for fname in ['tmp_search.json', 'tmp_search2.json']:
    path = f'C:\\Users\\scrccpa\\.openclaw\\workspace\\{fname}'
    if not os.path.exists(path): continue
    d = json.load(open(path,'r',encoding='utf-8'))
    print(f'\n=== {fname} (total: {d.get("total_count",0)}) ===')
    for r in d.get('items',[]):
        print(f'{r["stargazers_count"]:>5} stars | {r["full_name"]}')
        print(f'  {(r["description"] or "-")[:100]}')
        print(f'  {r["html_url"]}')
        print()