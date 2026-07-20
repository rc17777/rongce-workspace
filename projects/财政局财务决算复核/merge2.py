import sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\scrccpa\.openclaw\workspace\projects\财政局财务决算复核'
a = open(base + r'\gen_fee_a.py','r',encoding='utf-8').read()
b = open(base + r'\gen_fee_b.py','r',encoding='utf-8').read()
open(base + r'\gen_fee.py','w',encoding='utf-8').write(a + '\n' + b)
print('merged fee')
