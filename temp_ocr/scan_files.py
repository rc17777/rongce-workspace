import os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）'

cats = {}
for root, dirs, files in os.walk(base):
    for f in files:
        fp = os.path.join(root, f)
        sz = os.path.getsize(fp)
        ext = os.path.splitext(f)[1].lower()
        rel = fp.replace(base, '').replace('\\', '/')
        
        if '古英' in rel and ext == '.xlsx' and sz > 10*1024*1024:
            cat = 'A_结算数据(大xlsx)'
        elif '收入支出' in rel or '支出户' in rel or '收入户' in rel:
            cat = 'B_收入支出明细'
        elif '参保' in rel:
            cat = 'C_参保名单'
        elif '违规' in rel or '追回' in rel or '监管追回' in rel:
            cat = 'D_违规追回清单'
        elif 'DRG' in rel:
            cat = 'E_DRG支付'
        elif '集采' in rel or '张琴' in rel:
            cat = 'F_集采药品耗材'
        elif '预算' in rel:
            cat = 'G_预算文件'
        elif '委托' in rel or '协议' in rel or '集中采购协议' in rel:
            cat = 'H_委托协议'
        elif ext == '.pdf':
            cat = 'I_PDF文件'
        else:
            cat = 'Z_其他'
        
        if cat not in cats:
            cats[cat] = []
        cats[cat].append((sz, rel))

for cat in sorted(cats.keys()):
    files = cats[cat]
    total_sz = sum(sz for sz, _ in files)
    label = cat.split('_',1)[1]
    file_count = len(files)
    print('\n' + '='*60)
    print(label + ': ' + str(file_count) + ' files, ' + str(round(total_sz/1024/1024,1)) + 'MB')
    print('='*60)
    for sz, rel in sorted(files, key=lambda x: -x[0]):
        if sz > 1024*1024:
            s = str(round(sz/1024/1024,1)) + 'MB'
        elif sz > 1024:
            s = str(round(sz/1024,1)) + 'KB'
        else:
            s = str(sz) + 'B'
        print('  ' + s.rjust(8) + '  ' + rel)
