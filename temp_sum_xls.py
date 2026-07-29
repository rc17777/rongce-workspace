import sys
sys.stdout.reconfigure(encoding='utf-8')
import xlrd

base = r"C:\Users\scrccpa\Desktop\新建文件夹\财务资料\巴中恩阳医院PPP项目2025年运营审计"

for fname in ['主营业务成本明细.xls', '管理费用明细.xls', '主营业务收入明细.xls', '其他业务收入明细.xls', '其它业务成本明细.xls', '财务费用明细.xls']:
    fpath = base + '\\' + fname
    try:
        wb = xlrd.open_workbook(fpath)
        sheet = wb.sheet_by_index(0)
        print(f"\n=== {fname} ===")
        
        total_debit = 0
        total_credit = 0
        for r in range(sheet.nrows):
            d = sheet.cell(r, 5)
            c = sheet.cell(r, 6)
            dv = float(d.value) if d.value != '' else 0
            cv = float(c.value) if c.value != '' else 0
            total_debit += dv
            total_credit += cv
        
        print(f"  借方合计: {total_debit:,.2f}")
        print(f"  贷方合计: {total_credit:,.2f}")
        print(f"  净额: {total_debit - total_credit:,.2f}")
    except Exception as e:
        print(f"  ERROR: {e}")
