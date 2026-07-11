"""提取审核汇总表 - 用os.listdir找文件"""
import sys, os, xlrd
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\scrccpa\Desktop\新建文件夹'

for d in os.listdir(BASE):
    full_dir = os.path.join(BASE, d)
    if not os.path.isdir(full_dir):
        continue
    
    # 找附件2文件
    xls_file = None
    for f in os.listdir(full_dir):
        if f.endswith('.xls') and '附件2' in f:
            xls_file = os.path.join(full_dir, f)
            break
    
    if not xls_file:
        print(f"\n{d}: 未找到附件2")
        continue
    
    print(f"\n{'='*70}")
    print(f"  {d}")
    print(f"  文件: {f}")
    print(f"{'='*70}")
    
    book = xlrd.open_workbook(xls_file, formatting_info=False)
    
    for sn in book.sheet_names():
        if any(kw in sn for kw in ['01','审核','汇总']):
            sh = book.sheet_by_name(sn)
            print(f"\n  Sheet: {sn} ({sh.nrows}行 x {sh.ncols}列)")
            print(f"  ─" * 30)
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
