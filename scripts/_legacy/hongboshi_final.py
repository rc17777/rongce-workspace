"""Final attempt: scan .doc for property set in raw sectors"""
import struct, os, glob, datetime

base = r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司'

for fpath in sorted(glob.glob(os.path.join(base, '*'))):
    fsize = os.path.getsize(fpath)
    if '~$' in os.path.basename(fpath):
        continue
    fname = os.path.basename(fpath)
    stat = os.stat(fpath)
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
    ctime = datetime.datetime.fromtimestamp(stat.st_ctime)

    print(f'File: {fname} ({fsize/1024/1024:.1f}MB)')
    print(f'FS Created:  {ctime}')
    print(f'FS Modified: {mtime}')

    with open(fpath, 'rb') as f:
        hdr = f.read(512)

        def rd32(buf, off):
            return struct.unpack_from('<I', buf, off)[0]

        def rd16(buf, off):
            return struct.unpack_from('<H', buf, off)[0]

        ss = 1 << rd16(hdr, 0x1E)

        # Read FAT
        fat_secs = []
        for i in range(109):
            sid = rd32(hdr, 0x4C + i * 4)
            if sid < 0xFFFFFFFE:
                fat_secs.append(sid)

        fat = []
        for sec in fat_secs:
            f.seek((sec + 1) * ss)
            buf = f.read(ss)
            if len(buf) < ss:
                break
            for i in range(0, ss, 4):
                fat.append(struct.unpack_from('<I', buf, i)[0])

        def chain(start):
            result, seen, cur = [], set(), start
            while cur < 0xFFFFFFFA and cur not in seen and cur < len(fat):
                seen.add(cur)
                result.append(cur)
                cur = fat[cur]
            return result

        # Read directory entries
        dir_start = rd32(hdr, 0x30)
        entries = []
        for sec in chain(dir_start):
            f.seek((sec + 1) * ss)
            buf = f.read(ss)
            for i in range(0, ss, 128):
                ent = buf[i:i + 128]
                nl = rd16(ent, 0x40)
                if nl == 0:
                    continue
                try:
                    name = ent[:nl].decode('utf-16-le').rstrip(chr(0))
                except:
                    continue
                ssec = rd32(ent, 0x74)
                sz = rd32(ent, 0x78)
                entries.append((name, ssec, sz))

        # List entries
        print('  OLE2 entries:')
        for name, ssec, sz in entries:
            print(f'    [{sz:>10}] sec={ssec:>6}  {name}')

        # Direct scan: search all sectors for property set magic (FE FF 00 00)
        si_names = {
            2: 'Title', 3: 'Subject', 4: 'Author', 5: 'Keywords',
            6: 'Comments', 7: 'Template', 8: 'LastSavedBy',
            12: 'CreateTime', 13: 'LastSavedTime',
            14: 'Pages', 15: 'Words', 16: 'Chars', 18: 'AppName'
        }

        # Scan from sector 3 onwards (skip header + FAT area)
        # Use FAT to know which sectors are allocated
        allocated = set(fat_secs)
        for name, ssec, sz in entries:
            for s in chain(ssec):
                allocated.add(s)

        print(f'  Scanning {fsize//ss} sectors for property sets...')
        found = 0
        for sec in range(3, min(fsize // ss, 50000)):
            f.seek((sec + 1) * ss)
            chunk = f.read(ss)
            if len(chunk) < 4:
                break
            if chunk[:2] == b'\xfe\xff':
                np = rd32(chunk, 0x1C)
                if 1 <= np <= 30:
                    # Verify this looks like a valid property set
                    # Check that each property has valid offset within sector
                    valid = True
                    for i in range(min(np, 20)):
                        voff = 0x20 + np * 8 + i * 4
                        if voff + 3 >= ss:
                            break
                        off = rd32(chunk, voff)
                        if off >= ss:
                            valid = False
                            break
                    if valid:
                        found += 1
                        print(f'\n  [PropertySet at sector {sec}] props={np}')
                        for i in range(min(np, 20)):
                            poff = 0x20 + i * 8
                            pid = rd32(chunk, poff)
                            ptype = rd32(chunk, poff + 4)
                            voff = 0x20 + np * 8 + i * 4
                            off = rd32(chunk, voff)
                            val = None
                            try:
                                if ptype == 0x001E and off < ss - 2:
                                    end = chunk.find(b'\x00\x00', off)
                                    if end > off:
                                        val = chunk[off:end].decode(
                                            'utf-16-le', errors='replace')
                                elif ptype == 0x0040 and off + 7 < ss:
                                    ft = struct.unpack_from('<Q', chunk, off)[0]
                                    if 130000000000000000 < ft < 140000000000000000:
                                        val = datetime.datetime(
                                            1601, 1,
                                            1) + datetime.timedelta(
                                                microseconds=ft / 10)
                                elif ptype == 0x0003 and off + 3 < ss:
                                    val = rd32(chunk, off)
                            except:
                                pass
                            if val is not None:
                                label = si_names.get(pid, f'PID_{pid}')
                                if isinstance(val, datetime.datetime):
                                    val = val.strftime('%Y-%m-%d %H:%M:%S')
                                print(f'    {label}: {val}')
                        if found >= 3:
                            break
        if found == 0:
            print('  No valid property sets found.')
    print()
