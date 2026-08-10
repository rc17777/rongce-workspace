import os, sys
sys.stdout.reconfigure(encoding='utf-8')

desk = r'C:\Users\scrccpa\Desktop\文件'
if os.path.exists(desk):
    for root, dirs, files in os.walk(desk):
        for f in files:
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            rel = os.path.relpath(fp, desk)
            if sz > 1024*1024:
                print(f'  {rel} ({sz/1024/1024:.1f}MB)')
            else:
                print(f'  {rel} ({sz/1024:.0f}KB)')
    total = sum(1 for r,d,fs in os.walk(desk) for f in fs)
    total_sz = sum(os.path.getsize(os.path.join(r,f)) for r,d,fs in os.walk(desk) for f in fs)
    print(f'\n共 {total} 个文件, {total_sz/1024/1024:.1f}MB')
else:
    print('目录不存在: 桌面\\文件')
    desk2 = r'C:\Users\scrccpa\Desktop'
    for item in os.listdir(desk2):
        ip = os.path.join(desk2, item)
        icon = 'D' if os.path.isdir(ip) else 'F'
        print(f'  [{icon}] {item}')
