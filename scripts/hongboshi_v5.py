"""OLE2 metadata reader v5 - with error handling, small file first"""
import struct, os, datetime, glob


def read_meta(fpath):
    fname = os.path.basename(fpath)
    fsize = os.path.getsize(fpath)
    stat = os.stat(fpath)
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
    ctime = datetime.datetime.fromtimestamp(stat.st_ctime)

    print(f'File: {fname} ({fsize / 1024 / 1024:.1f}MB)')
    print(f'FS Created:  {ctime}')
    print(f'FS Modified: {mtime}')

    with open(fpath, 'rb') as f:
        hdr = f.read(512)

        def rd16(buf, off):
            return struct.unpack_from('<H', buf, off)[0]

        def rd32(buf, off):
            return struct.unpack_from('<I', buf, off)[0]

        ss = 1 << rd16(hdr, 0x1E)
        print(f'  SectorSize: {ss}')

        # Build FAT sectors list
        fat_secs = []
        for i in range(109):
            sid = rd32(hdr, 0x4C + i * 4)
            if sid < 0xFFFFFFFE:
                fat_secs.append(sid)

        msat_start = rd32(hdr, 0x44)
        num_msat = rd32(hdr, 0x48)
        if num_msat > 0 and msat_start < 0xFFFFFFFE:
            for m in range(num_msat):
                f.seek((msat_start + m + 1) * ss)
                msat_buf = f.read(ss)
                for i in range(0, ss - 4, 4):
                    sid = struct.unpack_from('<I', msat_buf, i)[0]
                    if sid < 0xFFFFFFFE:
                        fat_secs.append(sid)

        print(f'  FAT sectors: {len(fat_secs)}, first: {fat_secs[:5]}')

        # Read FAT
        fat = []
        for idx, sec in enumerate(fat_secs):
            try:
                f.seek((sec + 1) * ss)
                buf = f.read(ss)
                if len(buf) < ss:
                    print(f'    WARNING: FAT sector {sec} read only {len(buf)} bytes')
                    break
                for i in range(0, ss, 4):
                    fat.append(struct.unpack_from('<I', buf, i)[0])
            except Exception as e:
                print(f'    ERROR reading FAT sector {sec}: {e}')
                break

        print(f'  FAT entries: {len(fat)}')

        def get_chain(start, limit=200000):
            chain, seen = [], set()
            cur = start
            for _ in range(limit):
                if cur >= 0xFFFFFFFA or cur in seen:
                    break
                seen.add(cur)
                chain.append(cur)
                if cur >= len(fat):
                    break
                cur = fat[cur]
            return chain

        # Read directory
        dir_start = rd32(hdr, 0x30)
        dir_chain = get_chain(dir_start)

        entries = []
        for sec in dir_chain:
            f.seek((sec + 1) * ss)
            buf = f.read(ss)
            for i in range(0, ss, 128):
                ent = buf[i:i + 128]
                name_len = rd16(ent, 0x40)
                if name_len == 0:
                    continue
                try:
                    name = ent[:name_len].decode('utf-16-le').rstrip('\x00')
                except:
                    continue
                otype = ent[0x42]
                ssec = rd32(ent, 0x74)
                sz = rd32(ent, 0x78)
                entries.append((name, otype, ssec, sz))

        print(f'  Entries: {len(entries)}')
        for name, otype, ssec, sz in entries:
            typ = {1: 'Storage', 2: 'Stream', 5: 'Root'}.get(otype, str(otype))
            print(f'    [{typ:>7}] {sz:>10}  sec={ssec:>6}  {name}')

        # Read property streams
        si_names = {
            2: 'Title', 3: 'Subject', 4: 'Author', 5: 'Keywords',
            6: 'Comments', 7: 'Template', 8: 'LastSavedBy',
            9: 'RevNumber', 10: 'EditTime(min)', 11: 'LastPrinted',
            12: 'CreateTime', 13: 'LastSavedTime',
            14: 'Pages', 15: 'Words', 16: 'Chars', 18: 'AppName', 19: 'Security'
        }
        dsi_names = {14: 'Manager', 15: 'Company'}

        for name, otype, ssec, sz in entries:
            if otype != 2:
                continue
            is_prop = any(kw in name.lower() for kw in ['summary', 'document'])
            if not is_prop:
                continue

            chain = get_chain(ssec)
            data = bytearray()
            for sec in chain:
                f.seek((sec + 1) * ss)
                chunk = f.read(ss)
                if not chunk:
                    break
                data.extend(chunk)
            data = bytes(data[:sz])

            if len(data) < 24:
                continue
            if struct.unpack_from('<H', data, 0)[0] != 0xFFFE:
                continue

            num_props = rd32(data, 0x1C)
            names = si_names if 'summary' in name.lower() else dsi_names

            props = {}
            for i in range(min(num_props, 100)):
                poff = 0x20 + i * 8
                if poff + 7 >= len(data):
                    break
                pid = rd32(data, poff)
                ptype = rd32(data, poff + 4)
                voff = 0x20 + num_props * 8 + i * 4
                if voff + 3 >= len(data):
                    break
                off = rd32(data, voff)

                val = None
                try:
                    if ptype == 0x001E and off < len(data) - 2:
                        end = data.find(b'\x00\x00', off)
                        if end > off:
                            val = data[off:end].decode('utf-16-le', errors='replace')
                    elif ptype == 0x0040 and off + 7 < len(data):
                        ft = struct.unpack_from('<Q', data, off)[0]
                        if 100000000000000000 < ft < 200000000000000000:
                            val = datetime.datetime(1601, 1, 1) + datetime.timedelta(
                                microseconds=ft / 10)
                    elif ptype == 0x0003 and off + 3 < len(data):
                        val = rd32(data, off)
                    elif ptype == 0x001F and off < len(data) - 1:
                        end = data.find(b'\x00', off)
                        if end > off:
                            val = data[off:end].decode('latin-1', errors='replace')
                except:
                    pass
                if val is not None:
                    props[pid] = val

            print(f'\n  [{name}] Properties:')
            for pid in sorted(props):
                label = names.get(pid, f'PID_{pid}')
                v = props[pid]
                if isinstance(v, datetime.datetime):
                    v = v.strftime('%Y-%m-%d %H:%M:%S')
                print(f'    {label}: {v}')

    print()


base = r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司'
# Process smaller file first
for fpath in sorted(glob.glob(os.path.join(base, '*'))):
    if '~$' in os.path.basename(fpath):
        continue
    fsize = os.path.getsize(fpath)
    if fsize < 20 * 1024 * 1024:  # only < 20MB first
        try:
            read_meta(fpath)
        except Exception as e:
            print(f'  ERROR: {e}\n')
