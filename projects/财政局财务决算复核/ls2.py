import os, sys
sys.stdout.reconfigure(encoding='utf-8')
root = r'C:\Users\scrccpa\Desktop\新建文件夹'
for dp, dn, fs in os.walk(root):
    for f in fs:
        p = os.path.join(dp, f)
        print(f'{os.path.getsize(p)//1024:>8} KB  {os.path.relpath(p, root)}')
