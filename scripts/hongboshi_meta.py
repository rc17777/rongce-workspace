# -*- coding: utf-8 -*-
"""Extract OLE2 .doc metadata for 弘博士"""
import glob, os, struct, datetime, re, olefile

base = r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司'
files = sorted(glob.glob(os.path.join(base, '*')))

for fpath in files:
    fname = os.path.basename(fpath)
    fsize = os.path.getsize(fpath)
    print(f'{"="*70}')
    print(f'File: {fname}')
    print(f'Size: {fsize/1024/1024:.1f}MB')
    print()

    # Filesystem timestamps
    stat = os.stat(fpath)
    ctime = datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    print(f'  [Filesystem]')
    print(f'    Created:  {ctime}')
    print(f'    Modified: {mtime}')

    # olefile metadata
    print(f'  [OLE2 Properties]')
    try:
        ole = olefile.OleFileIO(fpath)
        # List all streams
        print(f'    Streams: {len(ole.listdir())}')
        for s in ole.listdir():
            stream_name = '/'.join(s)
            size = ole.get_size(s)
            print(f'      [{size:>10}] {stream_name}')

        # Extract properties from SummaryInformation
        for s in ole.listdir():
            sn = '/'.join(s).lower()
            if 'summary' in sn or 'document' in sn or 'custom' in sn:
                try:
                    props = ole.getproperties(s)
                    print(f'\n    [{"/".join(s)}] Properties:')
                    for k, v in props.items():
                        # Format FILETIME
                        if hasattr(v, 'strftime'):
                            v = v.strftime('%Y-%m-%d %H:%M:%S')
                        print(f'      {k}: {v}')
                except Exception as e:
                    print(f'    [Error reading {"/".join(s)}]: {e}')
        ole.close()
    except Exception as e:
        print(f'    olefile error: {e}')

    # Raw search for metadata patterns in file content
    print(f'\n  [Raw Content Search]')
    with open(fpath, 'rb') as f:
        # Read first 10MB only
        search_data = f.read(min(fsize, 10*1024*1024))

    # WPS build
    wps_pattern = rb'WPS[^\x00]{0,80}'
    wps_matches = re.findall(wps_pattern, search_data)
    for m in set(wps_matches[:10]):
        cleaned = m.replace(b'\x00', b'').decode('utf-8', errors='replace')
        if len(cleaned) > 5:
            print(f'    WPS: {cleaned[:200]}')

    # GUID
    guid_pattern = rb'[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}'
    guid_matches = re.findall(guid_pattern, search_data)
    for g in set(guid_matches[:10]):
        print(f'    GUID: {g.decode("ascii")}')

    # Author-like strings near WPS
    # Find Author field
    author_pattern = rb'(Author|LastAuthor|LastSavedBy|RevAuthor)[\x00-\xff]{0,100}'
    author_matches = re.findall(author_pattern, search_data, re.IGNORECASE)
    for m in set(author_matches[:5]):
        cleaned = m.decode('latin-1', errors='replace')[:200]
        print(f'    AuthTag: {cleaned}')

    print()
