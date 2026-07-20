"""Manual OLE2 metadata extraction - no olefile dependency, minimal memory"""
import os, struct, datetime, sys

sys.set_int_max_str_digits(0)


def read_ole2_props(fpath):
    fsize = os.path.getsize(fpath)
    fname = os.path.basename(fpath)
    stat = os.stat(fpath)

    print(f'File: {fname} ({fsize/1024/1024:.1f}MB)')
    print(f'FS Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}')

    with open(fpath, 'rb') as f:
        hdr = f.read(512)
        if hdr[:8] != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
            print('  Not OLE2')
            return

        def rd(buf, off):
            return struct.unpack_from('<I', buf, off)[0]

        ss = 1 << rd(hdr, 0x1E)
        print(f'  Sector size: {ss}')

        # Read FAT: first 109 FAT sectors are in header, rest in DIFAT
        fat_sectors = []
        for i in range(min(109, rd(hdr, 0x2C))):
            sid = rd(hdr, 0x4C + i * 4)
            if sid < 0xFFFFFFFE:
                fat_sectors.append(sid)

        # Read DIFAT sectors if any
        num_difat = rd(hdr, 0x48)
        if num_difat > 0:
            difat_start = rd(hdr, 0x44)
            if difat_start < 0xFFFFFFFE:
                f.seek((difat_start + 1) * ss)
                difat_buf = f.read(ss)
                for i in range(0, ss - 4, 4):
                    sid = struct.unpack_from('<I', difat_buf, i)[0]
                    if sid < 0xFFFFFFFE:
                        fat_sectors.append(sid)

        print(f'  FAT sectors: {len(fat_sectors)}')

        # Read FAT into a simple array - only what we need
        # Use a compact representation: list of sector IDs
        fat = []
        for sid in fat_sectors:
            f.seek((sid + 1) * ss)
            buf = f.read(ss)
            for i in range(0, ss, 4):
                fat.append(struct.unpack_from('<I', buf, i)[0])

        print(f'  FAT entries: {len(fat)}')

        def get_chain(start, max_steps=500000):
            chain = []
            seen = set()
            cur = start
            for _ in range(max_steps):
                if cur >= 0xFFFFFFFA or cur in seen:
                    break
                seen.add(cur)
                chain.append(cur)
                if cur >= len(fat):
                    break
                cur = fat[cur]
            return chain

        # Read directory
        dir_start = rd(hdr, 0x30)
        dir_chain = get_chain(dir_start)
        print(f'  Directory chain length: {len(dir_chain)}')

        # Read directory entries
        entries = []
        for sec in dir_chain:
            f.seek((sec + 1) * ss)
            buf = f.read(ss)
            for i in range(0, ss, 128):
                entry = buf[i:i + 128]
                name_len = struct.unpack_from('<H', entry, 0x40)[0]
                if name_len == 0:
                    continue
                try:
                    name = entry[:name_len].decode('utf-16-le').rstrip('\x00')
                except:
                    continue
                stream_sec = rd(entry, 0x74)
                stream_sz = rd(entry, 0x78)
                # stream_sz might be the lower 32 bits for large files
                entries.append((name, stream_sec, stream_sz))

        print(f'  Directory entries: {len(entries)}')
        for name, ssec, ssz in entries:
            print(f'    [{ssz:>10}] {name}')

        # Read property streams
        for name, ssec, ssz in entries:
            is_prop = ('summary' in name.lower() or
                       'document' in name.lower())
            if not is_prop:
                continue

            chain = get_chain(ssec)
            data = bytearray()
            for sec in chain:
                f.seek((sec + 1) * ss)
                data.extend(f.read(ss))
            data = bytes(data[:ssz])

            if len(data) < 24:
                continue

            # Parse property set
            if struct.unpack_from('<H', data, 0)[0] != 0xFFFE:
                continue

            num_props = rd(data, 0x1C)
            props = {}

            si_names = {2: 'Title', 3: 'Subject', 4: 'Author', 5: 'Keywords',
                        6: 'Comments', 7: 'Template', 8: 'LastSavedBy',
                        9: 'RevNumber', 10: 'EditTime', 11: 'LastPrinted',
                        12: 'CreateTime', 13: 'LastSavedTime', 14: 'Pages',
                        15: 'Words', 16: 'Chars', 18: 'AppName', 19: 'Security'}

            dsi_names = {14: 'Manager', 15: 'Company'}

            names = si_names if 'summaryinformation' in name.lower() else dsi_names

            for i in range(min(num_props, 100)):
                poff = 0x20 + i * 8
                if poff + 7 >= len(data):
                    break
                pid = rd(data, poff)
                ptype = rd(data, poff + 4)
                voff = 0x20 + num_props * 8 + i * 4
                if voff + 3 >= len(data):
                    break
                off = rd(data, voff)
                val = None
                try:
                    if ptype == 0x001E and off < len(data) - 2:
                        end = data.find(b'\x00\x00', off)
                        if end > off:
                            val = data[off:end].decode('utf-16-le', errors='replace')
                    elif ptype == 0x0040 and off + 7 < len(data):
                        ft = struct.unpack_from('<Q', data, off)[0]
                        if ft > 0:
                            val = datetime.datetime(1601, 1, 1) + datetime.timedelta(
                                microseconds=ft / 10)
                    elif ptype == 0x0003 and off + 3 < len(data):
                        val = rd(data, off)
                    elif ptype == 0x001F and off < len(data) - 1:
                        end = data.find(b'\x00', off)
                        if end > off:
                            val = data[off:end].decode('latin-1', errors='replace')
                except:
                    pass
                if val is not None:
                    label = names.get(pid, f'PID_{pid}')
                    props[label] = val

            print(f'\n  [{name}] Properties:')
            for k in sorted(props):
                v = props[k]
                if isinstance(v, datetime.datetime):
                    v = v.strftime('%Y-%m-%d %H:%M:%S')
                print(f'    {k}: {v}')

    print()


# Run
import glob

base = r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司'
for fpath in sorted(glob.glob(os.path.join(base, '*'))):
    if '~$' in os.path.basename(fpath):
        continue
    try:
        read_ole2_props(fpath)
    except Exception as e:
        print(f'  ERROR: {e}\n')
