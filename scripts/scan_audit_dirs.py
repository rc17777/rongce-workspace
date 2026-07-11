import os

dir1 = r'C:\Users\scrccpa\Desktop\护理学院任中经济责任审计审计\国资处有关制度'
dir2 = r'C:\Users\scrccpa\Desktop\护理学院任中经济责任审计审计\递交经责审计资料（第一次，20260415，李欣）'

def scan(d, indent=0):
    prefix = '  ' * indent
    try:
        items = sorted(os.listdir(d))
    except:
        print(f'{prefix}⚠️ 无法访问')
        return 0
    total = 0
    for item in items:
        if item.startswith('~$'):
            continue
        fp = os.path.join(d, item)
        if os.path.isfile(fp):
            ext = os.path.splitext(item)[1]
            total += 1
        else:
            sub_count = len([x for x in os.listdir(fp) if not x.startswith('~$')])
            file_count = sum(1 for root,_,files in os.walk(fp) for f in files if not f.startswith('~$'))
            print(f'{prefix}[{item}] ({file_count} files)')
            total += file_count
    return total

print('===== 国资处有关制度 =====')
count1 = scan(dir1)
print(f'总文件数: {count1}')
print()
print('===== 递交经责审计资料 =====')
count2 = scan(dir2)
print(f'总文件数: {count2}')
