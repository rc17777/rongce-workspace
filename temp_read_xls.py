"""Read financial data from XLS files for 2025运营审计"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

import xlrd

data_dir = r"C:\Users\scrccpa\Desktop\新建文件夹\财务资料\巴中恩阳医院PPP项目2025年运营审计"

for fname in sorted(os.listdir(data_dir)):
    fpath = os.path.join(data_dir, fname)
    if not fname.endswith('.xls'):
        continue
    
    print(f"\n{'='*70}")
    print(f"FILE: {fname}")
    print(f"{'='*70}")
    
    try:
        wb = xlrd.open_workbook(fpath)
        for sname in wb.sheet_names():
            sheet = wb.sheet_by_name(sname)
            print(f"\n  Sheet: {sname} ({sheet.nrows} rows × {sheet.ncols} cols)")
            
            # Print all rows (up to 50)
            limit = min(sheet.nrows, 50)
            for r in range(limit):
                row_vals = []
                for c in range(sheet.ncols):
                    cell = sheet.cell(r, c)
                    if cell.ctype == xlrd.XL_CELL_DATE:
                        import datetime
                        try:
                            dt = xlrd.xldate_as_datetime(cell.value, wb.datemode)
                            row_vals.append(dt.strftime('%Y-%m-%d'))
                        except:
                            row_vals.append(str(cell.value))
                    elif cell.ctype == xlrd.XL_CELL_NUMBER:
                        if cell.value == int(cell.value):
                            row_vals.append(f"{int(cell.value):,}")
                        else:
                            row_vals.append(f"{cell.value:,.2f}")
                    else:
                        row_vals.append(str(cell.value).strip())
                
                print(f"  R{r}: {' | '.join(row_vals)}")
            
            if sheet.nrows > limit:
                print(f"  ... ({sheet.nrows - limit} more rows)")
    except Exception as e:
        print(f"  ERROR: {e}")
