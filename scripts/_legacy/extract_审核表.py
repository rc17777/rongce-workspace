"""提取审核汇总表01表全部数据"""
import sys, xlrd
sys.stdout.reconfigure(encoding='utf-8')

projs = [
    ('S220', r'C:\Users\scrccpa\Desktop\新建文件夹\S220安羌镇至茸安乡段灾害修复整治工程\附件2：基本建设项目竣工财务决算审核表-S220安羌镇至茸安乡段灾害修复整治工程.xls'),
    ('S452', r'C:\Users\scrccpa\Desktop\新建文件夹\S452垮沙乡至柯河乡段灾害修复整治工程报告\附件2：基本建设项目竣工财务决算审核表-S452垮沙乡至柯河乡段灾害修复整治工程.xls'),
]

for label, fp in projs:
    print(f"\n{'='*70}")
    print(f"  {label}: {fp}")
    print(f"{'='*70}")
    
    book = xlrd.open_workbook(fp, formatting_info=False)
    
    for sn in book.sheet_names():
        if '01' in sn or '审核' in sn or '汇总' in sn:
            sh = book.sheet_by_name(sn)
            print(f"\n  Sheet: {sn} ({sh.nrows}行 x {sh.ncols}列)")
            print(f"  {'─'*60}")
            for r in range(sh.nrows):
                parts = []
                for c in range(sh.ncols):
                    v = sh.cell(r,c).value
                    if isinstance(v, float) and v > 0:
                        parts.append(f"C{c}={v:,.2f}")
                    elif v:
                        txt = str(v).strip()[:40]
                        parts.append(f"C{c}={txt}")
                if parts:
                    print(f"  R{r:2d}: {' | '.join(parts)}")
