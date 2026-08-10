import os
base = r'C:\Users\scrccpa\Desktop\若尔盖审计\若尔盖医保审计\2026年审计资料（医保局财务）'
tasks = [
    ('DRG支付2025', r'DRG支付\2025DRG支付.pdf'),
    ('稽查4', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查4.pdf'),
    ('稽查文件3', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件3.pdf'),
    ('稽查文件', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查文件.pdf'),
    ('稽查8', r'2024-2025违规使用医保基金清单\医保局稽查\医保局稽查8.pdf'),
    ('DRG支付2024', r'DRG支付\2024DRG支付文件2.pdf'),
    ('集中采购协议', r'委托支付协议\集中采购协议.pdf'),
]
for name, p in tasks:
    fp = os.path.join(base, p)
    ok = os.path.exists(fp)
    sz = os.path.getsize(fp)/1024/1024 if ok else 0
    print(f'  {name}: {"OK" if ok else "MISSING"} ({sz:.1f}MB)')
