"""Extract OLE2 doc metadata v3 - handle DIFAT too"""
import os, struct, datetime, re, glob

def extract_ole_meta(fpath):
    fsize = os.path.getsize(fpath)
    fname = os.path.basename(fpath)
    stat = os.stat(fpath)
    ctime = datetime.datetime.fromtimestamp(stat.st_ctime)
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)

    print(f'File: {fname}')
    print(f'Size: {fsize/1024/1024:.1f}MB')
    print(f'FS Created:  {ctime}')
    print(f'FS Modified: {mtime}')
    print()

    with open(fpath, 'rb') as f:
        header = f.read(512)
        if header[:8] != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
            print('  Not OLE2!')
            return

        def rd32(buf, off):
            return struct.unpack_from('<I', buf, off)[0]

        ss = 1 << rd32(header, 0x1E)
        dir_start = rd32(header, 0x30)
        num_fat = rd32(header, 0x2C)
        num_difat = rd32(header, 0x48)

        print(f'  SectorSize={ss}, DirStart={dir_start}, NumFAT={num_fat}, NumDIFAT={num_difat}')

        # Build sector list - use olefile lib instead!
        # Simpler approach: just use the `olefile` library which handles all this correctly
        # But only read the property streams, not the entire file

        import olefile
        ole = olefile.OleFileIO(fpath)
        streams = ole.listdir()
        print(f'  Streams: {len(streams)}')
        for s in streams:
            sn = '/'.join(s)
            sz = ole.get_size(s)
            print(f'    [{sz:>10}] {sn}')

        # Get properties
        for s in streams:
            try:
                props = ole.getproperties(s)
                if props:
                    print(f'\n  [{"/".join(s)}] Properties:')
                    for k, v in sorted(props.items()):
                        if hasattr(v, 'strftime'):
                            v = v.strftime('%Y-%m-%d %H:%M:%S')
                        print(f'    {k}: {v}')
            except:
                pass

        ole.close()

    # Quick search first 1MB for WPS build
    print(f'\n  [Raw WPS search in first 1MB]:')
    with open(fpath, 'rb') as f:
        raw = f.read(min(fsize, 1024*1024))
    wps = re.findall(rb'WPS[^\x00]{5,80}', raw)
    for w in set(wps[:10]):
        c = w.replace(b'\x00',b'').decode('utf-8','replace')
        if len(c)>5: print(f'    {c[:250]}')
    guids = re.findall(rb'[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}', raw)
    for g in sorted(set(guids))[:10]:
        print(f'    GUID: {g.decode()}')

    print()

for f in sorted(glob.glob(os.path.join(r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司', '*'))):
    if '~$' not in os.path.basename(f):
        try:
            extract_ole_meta(f)
        except Exception as e:
            print(f'  ERROR: {e}\n')
