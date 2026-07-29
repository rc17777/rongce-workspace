import sys
sys.stdout.reconfigure(encoding='utf-8')
import xlrd

base = r"C:\Users\scrccpa\Desktop\新建文件夹\财务资料\巴中恩阳医院PPP项目2025年运营审计"

for fname in ['主营业务成本明细.xls', '主营业务收入明细.xls', '其他业务收入明细.xls']:
    fpath = base + '\\' + fname
    try:
        wb = xlrd.open_workbook(fpath)
        sheet = wb.sheet_by_index(0)
        print(f"\n=== {fname} ===")
        
        total_debit = 0.0
        total_credit = 0.0
        for r in range(1, sheet.nrows):  # skip header
            d = sheet.cell(r, 5)
            c = sheet.cell(r, 6)
            try:
                dv = float(d.value) if d.ctype == 2 and d.value != '' else 0.0
                cv = float(c.value) if c.ctype == 2 and c.value != '' else 0.0
                total_debit += dv
                total_credit += cv
            except:
                pass
        
        print(f"  借方合计: {total_debit:,.2f}")
        print(f"  贷方合计: {total_credit:,.2f}")
        print(f"  净额: {total_debit - total_credit:,.2f}")
        
        # Find 损益结转 entries for quarterly totals
        for r in range(1, sheet.nrows):
            summary = str(sheet.cell(r, 4).value).strip()
            if '损益结转' in summary:
                d = sheet.cell(r, 5)
                c = sheet.cell(r, 6)
                dv = float(d.value) if d.ctype == 2 else 0
                cv = float(c.value) if c.ctype == 2 else 0
                print(f"  R{r} 损益结转: 借={dv:,.2f} 贷={cv:,.2f}")
                
    except Exception as e:
        print(f"  ERROR: {e}")
