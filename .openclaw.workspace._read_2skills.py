import os,sys
sys.stdout.reconfigure(encoding='utf-8')
d=r'C:\Users\Admin\.openclaw\workspace\skills'
for s in ['audit-data-analyst','analysis-report']:
    p=os.path.join(d,s,'SKILL.md')
    c=open(p,encoding='utf-8').read()
    print(f'{s}: {len(c)} chars')
    print(c[-200:])
    print()