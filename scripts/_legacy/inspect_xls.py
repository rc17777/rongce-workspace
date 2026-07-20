"""检查xls表格内容"""
import os, xlrd
import sys
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\scrccpa\Desktop\新建文件夹'
for d in os.listdir(base):
    print(f'\n目录: {d}')
    full = os.path.join(base, d)
    for f in os.listdir(full):
        fp = os.path.join(full, f)
        if f.endswith('.xls'):
            book = xlrd.open_workbook(fp, formatting_info=False)
            print(f'  {f}: sheets={book.sheet_names()}')
            sh = book.sheet_by_index(0)
            print(f'    rows={sh.nrows}, cols={sh.ncols}')
            for r in range(min(8, sh.nrows)):
                cells = []
                for c in range(min(15, sh.ncols)):
                    v = sh.cell(r,c).value
                    cells.append(str(v)[:30])
                print(f'    R{r}: {" | ".join(cells)}')
