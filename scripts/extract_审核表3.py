"""提取审核汇总表 - 用glob找文件"""
import sys, os, glob, xlrd
sys.stdout.reconfigure(encoding='utf-8')

# Use glob with wildcard to avoid encoding issues
pattern = r'C:\Users\scrccpa\Desktop\新建文件夹\*\附件2*.xls'
files = glob.glob(pattern)

for fp in files:
    fname = os.path.basename(fp)
    # Get project name from path
    proj_dir = os.path.basename(os.path.dirname(fp))
    
    print(f"\n{'='*70}")
    print(f"  项目: {proj_dir}")
    print(f"  文件: {fname}")
    print(f"{'='*70}")
    
    book = xlrd.open_workbook(fp, formatting_info=False)
    
    for sn in book.sheet_names():
        if any(kw in sn for kw in ['01','审核','汇总']):
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
                        parts.append(f" C{c}={txt}")
                if parts:
                    print(f"  R{r:2d}: {' | '.join(parts)}")
    
    # Also get 待摊投资sheet
    for sn in book.sheet_names():
        if '待摊' in sn:
            sh = book.sheet_by_name(sn)
            print(f"\n  Sheet: {sn} ({sh.nrows}行 x {sh.ncols}列)")
            for r in range(min(sh.nrows, 10)):
                parts = []
                for c in range(sh.ncols):
                    v = sh.cell(r,c).value
                    if isinstance(v, float) and v > 0:
                        parts.append(f"C{c}={v:,.2f}")
                    elif v:
                        txt = str(v).strip()[:40]
                        parts.append(f" C{c}={txt}")
                if parts:
                    print(f"  R{r:2d}: {' | '.join(parts)}")
