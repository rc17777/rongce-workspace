import struct, os, datetime, glob

base = r'C:\Users\scrccpa\Desktop\校服2\投标文件\投标文件\弘博士服饰集团有限公司'

for fpath in sorted(glob.glob(os.path.join(base, '*'))):
    fsize = os.path.getsize(fpath)
    if '~$' in os.path.basename(fpath) or fsize > 20 * 1024 * 1024:
        continue
    fname = os.path.basename(fpath)
    stat = os.stat(fpath)
    print(f'File: {fname} ({fsize/1024/1024:.1f}MB)')
    print(f'FS Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}')

    with open(fpath, 'rb') as f:
        hdr = f.read(512)

        def rd16(b, o):
            return struct.unpack_from('<H', b, o)[0]

        def rd32(b, o):
            return struct.unpack_from('<I', b, o)[0]

        ss = 1 << rd16(hdr, 0x1E)

        fat_secs = []
        for i in range(109):
            sid = rd32(hdr, 0x4C + i * 4)
            if sid < 0xFFFFFFFE:
                fat_secs.append(sid)

        fat = []
        for sec in fat_secs:
            f.seek((sec + 1) * ss)
            buf = f.read(ss)
            for i in range(0, ss, 4):
                fat.append(struct.unpack_from('<I', buf, i)[0])

        def chain(start):
            result, seen, cur = [], set(), start
            while cur < 0xFFFFFFFA and cur not in seen and cur < len(fat):
                seen.add(cur)
                result.append(cur)
                cur = fat[cur]
            return result

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
                entries.append((name, rd32(ent, 0x74), rd32(ent, 0x78)))

        # Read WpsCustomData
        for name, ssec, sz in entries:
            if 'wps' in name.lower():
                print(f'  [{name}] sec={ssec} sz={sz}')
                ch = chain(ssec)
                data = bytearray()
                for sec in ch:
                    f.seek((sec + 1) * ss)
                    data.extend(f.read(ss))
                data = bytes(data[:sz])
                print(f'    Raw: {data}')

        # Scan entire file for FEFF
        f.seek(0)
        data = f.read()
        feff_pos = []
        pos = 0
        while True:
            idx = data.find(b'\xfe\xff', pos)
            if idx < 0:
                break
            feff_pos.append(idx)
            pos = idx + 1
        print(f'  FEFF found at: {feff_pos}')

        for pos in feff_pos:
            if pos >= 4:
                sec_sz = rd32(data, pos - 4)
                if 100 < sec_sz < 65536 and pos + sec_sz <= len(data):
                    nprops = rd32(data, pos + 0x1C)
                    if 1 <= nprops <= 30:
                        print(
                            f'    Valid property set at {pos-4}: size={sec_sz} props={nprops}'
                        )
                        # Parse and print
                        si_names = {
                            2: 'Title',
                            3: 'Subject',
                            4: 'Author',
                            5: 'Keywords',
                            6: 'Comments',
                            7: 'Template',
                            8: 'LastSavedBy',
                            9: 'RevNumber',
                            10: 'EditTimeMin',
                            11: 'LastPrinted',
                            12: 'CreateTime',
                            13: 'LastSavedTime',
                            14: 'Pages',
                            15: 'Words',
                            16: 'Chars',
                            18: 'AppName',
                            19: 'Security'
                        }
                        sec = data[pos - 4:pos - 4 + sec_sz]
                        for i in range(min(nprops, 30)):
                            poff = 0x20 + i * 8
                            pid = rd32(sec, poff)
                            ptype = rd32(sec, poff + 4)
                            voff = 0x20 + nprops * 8 + i * 4
                            off = rd32(sec, voff)
                            val = None
                            try:
                                if ptype == 0x001E and off < len(sec) - 2:
                                    end = sec.find(b'\x00\x00', off)
                                    if end > off:
                                        val = sec[off:end].decode(
                                            'utf-16-le', errors='replace')
                                elif ptype == 0x0040 and off + 7 < len(sec):
                                    ft = struct.unpack_from('<Q', sec, off)[0]
                                    if 100000000000000000 < ft < 200000000000000000:
                                        val = datetime.datetime(
                                            1601, 1,
                                            1) + datetime.timedelta(
                                                microseconds=ft / 10)
                                elif ptype == 0x0003 and off + 3 < len(sec):
                                    val = rd32(sec, off)
                            except:
                                pass
                            if val is not None:
                                label = si_names.get(pid, f'PID_{pid}')
                                if isinstance(val, datetime.datetime):
                                    val = val.strftime('%Y-%m-%d %H:%M:%S')
                                print(f'      {label}: {val}')

    print()
