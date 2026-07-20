import sys, os, glob, struct, datetime
sys.set_int_max_str_digits(0)

base = r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司'
# Only the 11.6MB qualification bid
for fpath in sorted(glob.glob(os.path.join(base, '*'))):
    if '~$' in os.path.basename(fpath):
        continue
    fsize = os.path.getsize(fpath)
    # Skip the 112.5MB one
    if fsize > 100 * 1024 * 1024:
        continue

    fname = os.path.basename(fpath)
    stat = os.stat(fpath)
    print(f'File: {fname} ({fsize/1024/1024:.1f}MB)')
    print(f'FS Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}')

    import olefile
    ole = olefile.OleFileIO(fpath)
    print('Streams:')
    for s in ole.listdir():
        sn = '/'.join(s)
        sz = ole.get_size(s)
        print(f'  [{sz:>10}] {sn}')

    for s in ole.listdir():
        try:
            props = ole.getproperties(s)
            if props:
                print(f'\n[{"/".join(s)}] Properties:')
                for k, v in sorted(props.items()):
                    if hasattr(v, 'strftime'):
                        v = v.strftime('%Y-%m-%d %H:%M:%S')
                    print(f'  {k}: {v}')
        except Exception as e:
            print(f'  Error: {e}')
    ole.close()
