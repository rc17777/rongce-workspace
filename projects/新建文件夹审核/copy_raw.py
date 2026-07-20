import shutil, os, sys
sys.stdout.reconfigure(encoding='utf-8')
src_dir = r'C:\Users\scrccpa\Desktop\新建文件夹'
dst_dir = r'C:\Users\scrccpa\.openclaw\workspace\projects\新建文件夹审核\raw_data'
os.makedirs(dst_dir, exist_ok=True)
for f in os.listdir(src_dir):
    if f.endswith('.pdf'):
        shutil.copyfile(os.path.join(src_dir, f), os.path.join(dst_dir, f))
        print('copied', f)
