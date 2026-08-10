import os, sys
sys.stdout.reconfigure(encoding='utf-8')
desktop = r'C:\Users\scrccpa\Desktop'
targets = ['校园餐', '食堂', '营养餐', '若尔盖', '医保', '实施方案', '资金明细', '伙食', '台账', '收支', '对比', '预算', '问题清单', '试点', '审计报告', '数据']

for root, dirs, files in os.walk(desktop):
    rel = root.replace(desktop, '').strip(os.sep)
    depth = 0 if rel == '' else rel.count(os.sep) + 1
    prefix = '  ' * depth
    
    for d in dirs[:]:
        for t in targets:
            if t in d:
                print(f'{prefix}📁 {d}/')
                break
    
    for f in files:
        for t in targets:
            if t in f:
                full = os.path.join(root, f)
                size_kb = os.path.getsize(full) / 1024
                ext = os.path.splitext(f)[1].lower()
                icon = {'.xlsx':'📊','.docx':'📝','.doc':'📝','.pdf':'📄','.ofd':'📄','.wps':'📝'}.get(ext, '📎')
                print(f'{prefix}  {icon} {f} ({size_kb:.0f}KB)')
                break
