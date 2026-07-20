"""Extract .doc OLE2 metadata efficiently - reads only header + property streams"""
import os, struct, datetime, re

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
        # Read only the header (first 512 bytes)
        header = f.read(512)
        if header[:8] != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
            print('  Not OLE2 format!')
            return

        def rd32(buf, off):
            return struct.unpack_from('<I', buf, off)[0]

        sector_size = 1 << rd32(header, 0x1E)
        dir_start = rd32(header, 0x30)
        num_fat = rd32(header, 0x2C)

        # Read FAT sectors
        fat_sectors = []
        for i in range(min(num_fat, 109)):
            fat_sectors.append(rd32(header, 0x4C + i*4))

        # Read FAT into memory
        fat = bytearray()
        for sec in fat_sectors:
            if sec < 0xFFFFFFFE:
                f.seek((sec + 1) * sector_size)
                fat.extend(f.read(sector_size))

        def get_chain(start, max_s=200000):
            chain, sec, visited = [], start, set()
            while sec < 0xFFFFFFFA and len(chain) < max_s:
                if sec in visited: break
                visited.add(sec); chain.append(sec)
                off = sec * 4
                if off + 3 >= len(fat): break
                sec = struct.unpack_from('<I', fat, off)[0]
            return chain

        def read_stream_data(start_sec, size):
            chain = get_chain(start_sec)
            data = bytearray()
            for sec in chain:
                f.seek((sec + 1) * sector_size)
                data.extend(f.read(sector_size))
            return bytes(data[:size])

        # Read directory
        dir_bytes = bytearray()
        dir_chain = get_chain(dir_start)
        for sec in dir_chain:
            f.seek((sec + 1) * sector_size)
            dir_bytes.extend(f.read(sector_size))

        # Find streams
        streams_found = {}
        for i in range(0, len(dir_bytes), 128):
            entry = dir_bytes[i:i+128]
            name_len = struct.unpack_from('<H', entry, 0x40)[0]
            if name_len == 0: continue
            try:
                name = entry[:name_len].decode('utf-16-le').rstrip('\x00')
            except:
                continue
            start_sec = rd32(entry, 0x74)
            stream_sz = rd32(entry, 0x78)
            streams_found[name] = (start_sec, stream_sz)

        # Read property streams
        props_data = {}
        for target in ['SummaryInformation', 'DocumentSummaryInformation']:
            if target in streams_found:
                ss, sz = streams_found[target]
                data = read_stream_data(ss, min(sz, 65536))
                props_data[target] = data
            # WPS uses localized names
            for k in list(streams_found.keys()):
                if target.lower() in k.lower() or 'summary' in k.lower():
                    if k not in props_data:
                        ss, sz = streams_found[k]
                        data = read_stream_data(ss, min(sz, 65536))
                        props_data[k] = data

        # Parse property set
        def parse_props(data, name_map):
            if len(data) < 32: return {}
            if struct.unpack_from('<H', data, 0)[0] != 0xFFFE: return {}
            num = rd32(data, 0x1C)
            props = {}
            for i in range(min(num, 50)):
                poff = 0x20 + i*8
                if poff+7 >= len(data): break
                pid = rd32(data, poff)
                ptype = rd32(data, poff+4)
                voff = 0x20 + num*8 + i*4
                if voff+3 >= len(data): break
                offset = rd32(data, voff)
                try:
                    if ptype == 0x001E:  # string
                        end = data.find(b'\x00\x00', offset)
                        if end > offset:
                            val = data[offset:end].decode('utf-16-le', errors='replace')
                        else: continue
                    elif ptype == 0x0040:  # FILETIME
                        ft = struct.unpack_from('<Q', data, offset)[0]
                        if ft > 0:
                            val = datetime.datetime(1601,1,1) + datetime.timedelta(microseconds=ft/10)
                        else: continue
                    elif ptype == 0x0003:  # VT_I4
                        val = rd32(data, offset)
                    elif ptype == 0x001F:  # LPSTR
                        end = data.find(b'\x00', offset)
                        if end > offset:
                            val = data[offset:end].decode('latin-1', errors='replace')
                        else: continue
                    else:
                        continue
                    name = name_map.get(pid, f'PID_{pid}')
                    props[name] = val
                except:
                    pass
            return props

        SI = {2:'Title',3:'Subject',4:'Author',5:'Keywords',6:'Comments',
              7:'Template',8:'LastSavedBy',9:'RevisionNumber',
              10:'EditingTime',11:'LastPrinted',12:'CreateTime',
              13:'LastSavedTime',14:'PageCount',15:'WordCount',
              16:'CharCount',18:'AppName',19:'Security'}

        DSI = {14:'Manager',15:'Company'}

        for sn, data in props_data.items():
            if 'SummaryInformation' == sn:
                props = parse_props(data, SI)
            else:
                props = parse_props(data, DSI)
            if props:
                print(f'  [{sn}]:')
                for k, v in sorted(props.items()):
                    if hasattr(v, 'strftime'):
                        v = v.strftime('%Y-%m-%d %H:%M:%S')
                    print(f'    {k}: {v}')

        # Also search first 1MB for WPS build string
        f.seek(0)
        raw = f.read(min(fsize, 1*1024*1024))
        wps = re.findall(rb'WPS[^\x00]{5,80}', raw)
        guids = re.findall(rb'[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}', raw)
        if wps or guids:
            print(f'\n  [Raw byte search]:')
            for w in set(wps[:5]):
                c = w.replace(b'\x00',b'').decode('utf-8','replace')
                if len(c)>5: print(f'    WPS: {c[:300]}')
            for g in set(guids[:10]):
                print(f'    GUID: {g.decode()}')

        # List all streams
        print(f'\n  [All OLE2 streams] ({len(streams_found)}):')
        for k, (ss, sz) in sorted(streams_found.items()):
            print(f'    [{sz:>10}] {k}')
    print()

# Run
base = r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司'
import glob
for f in sorted(glob.glob(os.path.join(base, '*'))):
    if not f.startswith('~$'):  # skip temp files
        extract_ole_meta(f)
