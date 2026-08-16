#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text from OLE2 .doc (弘博士) using binary parsing"""
import sys, struct, re
sys.stdout.reconfigure(encoding='utf-8')
import olefile

path = r"C:\Users\scrccpa\Desktop\校服\2025年校服采购\校服\2025年\投标文件\投标文件\弘博士服饰集团有限公司\资格性投标文件（电子文件）-弘博士服饰集团有限公司.doc"

ole = olefile.OleFileIO(path)

# List all streams
print("Streams in OLE2 file:")
for s in ole.listdir():
    name = '/'.join(s)
    try:
        size = ole.get_size(s)
        print(f"  {name} ({size} bytes)")
    except:
        print(f"  {name} (error)")

# Get WordDocument stream
word_stream = ole.openstream('WordDocument').read()

# Parse FIB
magic = struct.unpack_from('<H', word_stream, 0)[0]
print(f"\nMagic: 0x{magic:04X} (expected 0xA5EC for Word)")

# Get flags
flags = struct.unpack_from('<H', word_stream, 0x000A)[0]
print(f"Flags at 0x0A: 0x{flags:04X}")
is_complex = bool(flags & 0x0004)  # fWhichTblStm
is_1table = bool(flags & 0x0200)  # fComplex 
print(f"fComplex: {bool(flags & 0x0200)}, fWhichTblStm: {is_complex}")

# Try to find text using UTF-16LE scanning
# In .doc files, the main text body often starts after the FIB header
# Let's try different approaches

# Approach 1: Scan for Chinese characters in UTF-16LE
text_bytes = word_stream
chinese_chars = []
i = 0
while i < len(text_bytes) - 1:
    # Try to decode a UTF-16LE character
    try:
        code_unit = struct.unpack_from('<H', text_bytes, i)[0]
        char = chr(code_unit)
        if '\u4e00' <= char <= '\u9fff' or '\u3000' <= char <= '\u303f' or char in '，。！？；：""''（）【】《》…—\n\r\t ' or char.isdigit() or char.isascii() and char.isprintable():
            chinese_chars.append(char)
            i += 2
            continue
    except:
        pass
    i += 1

extracted = ''.join(chinese_chars)
print(f"\nExtracted {len(extracted)} characters via UTF-16LE scanning")

# Find Chinese text runs
runs = re.findall(r'[\u4e00-\u9fff\u3000-\u303f\d\w，。！？；：、""''（）【】《》…—\s]+', extracted)
meaningful = [r.strip() for r in runs if len(r.strip()) > 10]
print(f"Found {len(meaningful)} meaningful text runs")

# Print key information
for run in meaningful[:50]:
    if any(kw in run for kw in ['公司', '有限', '集团', '投标', '项目', '报价', '地址', '法人', '注册',
                                '资格', '承诺', '财务', '纳税', '社保', '设备', '人员', '业绩',
                                '校服', '采购', '招标', '合同', '服务', '技术']):
        print(f"  [{len(run)}] {run[:200]}")

# Also try extracting from 1Table or 0Table streams
if ole.exists('1Table'):
    table1 = ole.openstream('1Table').read()
    print(f"\n1Table stream: {len(table1)} bytes")

# Approach 2: Look for the text in pieces (piece table)
# This is complex but let's try the simpler approach first

ole.close()
print("\nDone!")
