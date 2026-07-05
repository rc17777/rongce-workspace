import os, shutil, glob

# Source directories
src1_policy = r'C:\Users\scrccpa\Desktop\护理学院任中经济责任审计审计\国资处有关制度'
src2_data = r'C:\Users\scrccpa\Desktop\护理学院任中经济责任审计审计\递交经责审计资料（第一次，20260415，李欣）'
dst = r'D:\openclaw-workspace\projects\护理学院任中经责审计'

# Copy 述职报告
report_dir = os.path.join(src2_data, '1.个人述职报告')
dst_report = os.path.join(dst, '述职报告')
os.makedirs(dst_report, exist_ok=True)

for f in os.listdir(report_dir):
    if f.startswith('~$'):
        continue
    src = os.path.join(report_dir, f)
    shutil.copy2(src, os.path.join(dst_report, f))
    print(f'✅ 述职报告: {f}')

# Copy key policy files (国有资产管理 + 招标采购)
policy_subs = [
    os.path.join('国资处现行执行的制度', '国有资产管理制度'),
    os.path.join('国资处现行执行的制度', '招标采购制度'),
    '新增制度',
]
for sub in policy_subs:
    sub_path = os.path.join(src1_policy, sub)
    if os.path.exists(sub_path):
        dst_sub = os.path.join(dst, '制度分析', sub.rsplit('\\',1)[-1] if '\\' in sub else sub)
        os.makedirs(dst_sub, exist_ok=True)
        for f in os.listdir(sub_path):
            if f.startswith('~$'):
                continue
            src = os.path.join(sub_path, f)
            shutil.copy2(src, os.path.join(dst_sub, f))
            print(f'✅ 制度: {f[:60]}')

print('\n复制完成！')
