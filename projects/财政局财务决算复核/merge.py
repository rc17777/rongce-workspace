import sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\scrccpa\.openclaw\workspace\projects\财政局财务决算复核'
p1 = open(base + r'\gen_p1.py','r',encoding='utf-8').read()
p2 = open(base + r'\gen_p2.py','r',encoding='utf-8').read()
open(base + r'\gen_review_excel.py','w',encoding='utf-8').write(p1 + '\n' + p2)
print('merged')
