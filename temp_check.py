import sys; sys.stdout.reconfigure(encoding='utf-8')

# 1. K factor
a1 = 5341344.03 * 1.0799
print(f'[K] Yr1*1.0799 = {a1:,.2f} vs orig 5,768,117.42: {"OK" if abs(a1-5768117.42)<1 else "FAIL"}')
a2 = 5948956.93 * 1.0799
a3 = 431456.22 * 1.0799
print(f'[K] Yr2*1.0799 = {a2:,.2f}, partial*1.0799 = {a3:,.2f}, sum = {a2+a3:,.2f} vs orig 6,890,208.16: {"OK" if abs(a2+a3-6890208.16)<1 else "FAIL"}')

# 2. 2025+ should *1.0799
a4 = 5713241.86 * 1.0799
a5 = 5710000 * 1.0799
print(f'[K] 2025 audit *1.0799 = {a4:,.2f}')
print(f'[K] 2026+ *1.0799 = {a5:,.2f}')

# 3. 14-month issue
print(f'\n[14MONTH] 2023 cap return = 8,530,246.96 (annual, for 14-month period)')
print(f'           annualized = {8530246.96*12/14:,.2f}/yr vs {8530246.96*14/12:,.2f}/yr if prorated')

# 4. Year by year op cost comparison
print(f'\n[OP COST] Year-by-year:')
print(f'Year      Original(K)     Our v4(no K)   Correct(*K)     Diff')
orig = [5768117.42, 6890208.16] + [6090636]*16
ours = [5768117.42, 6890208.16, 5713241.86] + [5710000]*15
corr = [5768117.42, 6890208.16, a4] + [a5]*15
for i in range(18):
    d = corr[i] - ours[i]
    flag = ' !!!' if abs(d) > 100 else ''
    print(f'{2023+i}  {orig[i]:>14,.2f}  {ours[i]:>14,.2f}  {corr[i]:>14,.2f}  {d:>10,.0f}{flag}')
print(f'SUM   {sum(orig):>14,.2f}  {sum(ours):>14,.2f}  {sum(corr):>14,.2f}  {sum(corr)-sum(ours):>10,.0f}')

# 5. Corrected total
cap = 175842523.10
bank = 710822119.33
op_corr = sum(corr)
inc_new = sum([4285070.31, 6229093.45, 5564017.88] + [5560000]*15)
total = cap + bank + op_corr - inc_new
print(f'\n[CORRECTED TOTAL]')
print(f'  Capital: {cap:>15,.2f}')
print(f'  Bank:    {bank:>15,.2f}')
print(f'  Op(*K):  {op_corr:>15,.2f}')
print(f'  Income:  {inc_new:>15,.2f}')
print(f'  TOTAL:   {total:>15,.2f} ({total/1e8:.2f}yi)')

# Current v4 total for comparison
v4_total = cap + bank + sum(ours) - inc_new
print(f'\n  v4 was:  {v4_total:>15,.2f} ({v4_total/1e8:.2f}yi)')
print(f'  BUG:     {total-v4_total:>15,.2f} (op cost not *1.0799 for 2025+)')
