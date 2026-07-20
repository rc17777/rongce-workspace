"""Search for metadata in .doc files by raw byte scanning"""
import os, struct, datetime, glob, re

base = r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司'

for fpath in sorted(glob.glob(os.path.join(base, '*'))):
    if '~$' in os.path.basename(fpath):
        continue
    fname = os.path.basename(fpath)
    fsize = os.path.getsize(fpath)
    stat = os.stat(fpath)
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
    ctime = datetime.datetime.fromtimestamp(stat.st_ctime)

    print(f'========================================')
    print(f'File: {fname}')
    print(f'Size: {fsize/1024/1024:.1f}MB')
    print(f'FS Created:  {ctime}')
    print(f'FS Modified: {mtime}')
    print()

    with open(fpath, 'rb') as f:
        data = f.read(min(fsize, 5*1024*1024))

    # ── Search for property set sections ──
    print('[Property Set Sections]')
    idx = 0
    found = []
    while True:
        idx = data.find(b'\xfe\xff', idx)
        if idx < 0: break
        if idx >= 4:
            sec_sz = struct.unpack_from('<I', data, idx-4)[0]
            if 16 < sec_sz < 65536 and idx + sec_sz <= len(data):
                num_props = struct.unpack_from('<I', data, idx+0x1C)[0]
                if 1 <= num_props <= 50:
                    found.append((idx-4, sec_sz, num_props))
        idx += 1

    print(f'  Found {len(found)} potential property sections')

    si_names = {2:'Title',3:'Subject',4:'Author',5:'Keywords',6:'Comments',
                7:'Template',8:'LastSavedBy',9:'RevNumber',10:'EditTime',
                11:'LastPrinted',12:'CreateTime',13:'LastSavedTime',
                14:'Pages',15:'Words',16:'Chars',18:'AppName'}

    dsi_names = {14:'Manager',15:'Company'}

    for soff, ssz, nprops in found:
        sec = data[soff:soff+ssz]
        # Determine if SI or DSI by checking first property
        first_pid = struct.unpack_from('<I', sec, 0x20)[0]
        is_si = first_pid in si_names
        names = si_names if is_si else dsi_names
        label = 'SummaryInformation' if is_si else 'DocumentSummaryInformation'
        print(f'\n  [{label}] at offset {soff}, size={ssz}, props={nprops}')

        for i in range(min(nprops, 50)):
            poff = 0x20 + i*8
            if poff+7 >= len(sec): break
            pid = struct.unpack_from('<I', sec, poff)[0]
            ptype = struct.unpack_from('<I', sec, poff+4)[0]
            voff = 0x20 + nprops*8 + i*4
            if voff+3 >= len(sec): break
            off = struct.unpack_from('<I', sec, voff)[0]

            val = None
            try:
                if ptype == 0x001E and off < len(sec)-2:
                    end_bytes = sec.find(b'\x00\x00', off)
                    if end_bytes > off:
                        val = sec[off:end_bytes].decode('utf-16-le', errors='replace')
                elif ptype == 0x0040 and off+7 < len(sec):
                    ft = struct.unpack_from('<Q', sec, off)[0]
                    if 100000000000000000 < ft < 200000000000000000:
                        val = datetime.datetime(1601,1,1) + datetime.timedelta(microseconds=ft/10)
                elif ptype == 0x0003 and off+3 < len(sec):
                    val = struct.unpack_from('<I', sec, off)[0]
                elif ptype == 0x001F and off < len(sec)-1:
                    end_bytes = sec.find(b'\x00', off)
                    if end_bytes > off:
                        val = sec[off:end_bytes].decode('latin-1', errors='replace')
            except:
                pass

            if val is not None:
                name = names.get(pid, f'PID_{pid}')
                if isinstance(val, datetime.datetime):
                    val = val.strftime('%Y-%m-%d %H:%M:%S')
                print(f'    {name}: {val}')

    print()
