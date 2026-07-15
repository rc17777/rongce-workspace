import json
d = json.load(open('C:\\Users\\scrccpa\\.openclaw\\workspace\\tmp_search.json','r',encoding='utf-8'))
for r in d.get('items',[]):
    print(f'Stars: {r["stargazers_count"]:>5} | {r["full_name"]:<45} | {(r["description"] or "-")[:80]}')
    print(f'       {r["html_url"]}')