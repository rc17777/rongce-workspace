import os, sys
sys.stdout.reconfigure(encoding='utf-8')
hits = []
for root in [r'C:\Users\scrccpa\.openclaw\workspace\knowledge', r'C:\Users\scrccpa\.openclaw\workspace\obsidian-vault']:
    for dp, dn, fs in os.walk(root):
        for f in fs:
            if f.endswith(('.md','.txt')):
                p = os.path.join(dp,f)
                try:
                    t = open(p,'r',encoding='utf-8',errors='ignore').read()
                except Exception:
                    continue
                if ('141号' in t and '造价咨询' in t) or ('川价发' in t and '收费' in t) or '计价格〔2002〕1980号' in t or '计价格[2002]1980号' in t:
                    hits.append(p)
for h in hits[:25]:
    print(h)
print('TOTAL', len(hits))
