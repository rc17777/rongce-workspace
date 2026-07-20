import sys
sys.stdout.reconfigure(encoding='utf-8')
import xlrd

path = r'C:\Users\scrccpa\Desktop\财政局=财务决算\1.马尔康城市环境质量提升（房屋建筑）工程（州级）项目\1.马尔康城市环境质量提升（房屋建筑）工程（州级）项目----竣工财务决算审核报告（征求意见稿20260720）\附件2：基本建设项目竣工财务决算审核表-马尔康城市环境质量提升（房屋建筑）工程（州级）项目.xls'

wb = xlrd.open_workbook(path, encoding_override='gbk')
out = open(r'C:\Users\scrccpa\.openclaw\workspace\projects\财政局财务决算复核\xls_dump.txt','w',encoding='utf-8')
for si, sh in enumerate(wb.sheets()):
    print(f'===== SHEET {si}: {sh.name} ({sh.nrows}r x {sh.ncols}c) =====', file=out)
    for r in range(sh.nrows):
        vals = []
        for c in range(sh.ncols):
            v = sh.cell_value(r, c)
            if isinstance(v, float):
                if v == int(v):
                    vals.append(str(int(v)))
                else:
                    vals.append(f'{v:,.2f}')
            else:
                vals.append(str(v).strip().replace('\n',' '))
        if any(vals):
            print(f'R{r}: ' + ' | '.join(vals), file=out)
out.close()
