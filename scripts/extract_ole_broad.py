#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Broad text extraction from all OLE2 streams for 弘博士"""
import sys, struct, re
sys.stdout.reconfigure(encoding='utf-8')
import olefile

path = r"C:\Users\scrccpa\Desktop\校服\2025年校服采购\校服\2025年\投标文件\投标文件\弘博士服饰集团有限公司\资格性投标文件（电子文件）-弘博士服饰集团有限公司.doc"

ole = olefile.OleFileIO(path)

all_text = []

for stream_path in ole.listdir():
    name = '/'.join(stream_path)
    try:
        data = ole.openstream(stream_path).read()
        size = len(data)
        
        # Try UTF-16LE decoding
        try:
            decoded = data.decode('utf-16-le', errors='replace')
            # Extract Chinese text runs
            runs = re.findall(r'[\u4e00-\u9fff\u3000-\u303f\w，。！？；：、""''（）【】《》…—\s\u0020-\u007f]+', decoded)
            for run in runs:
                cleaned = run.strip()
                if len(cleaned) > 20:
                    all_text.append((name, cleaned))
        except:
            pass
        
        # Try simple ASCII/CP1252 extraction
        if size < 1000000:  # Skip huge streams
            ascii_text = ''.join(chr(b) if 32 <= b < 127 or b in (10, 13) else '' for b in data)
            runs = re.findall(r'[\w\s]{10,}', ascii_text)
            for run in runs:
                cleaned = run.strip()
                if len(cleaned) > 30:
                    all_text.append((name, f"[ASCII] {cleaned}"))
    except Exception as e:
        pass

ole.close()

# Filter and deduplicate
seen = set()
unique = []
for stream, text in all_text:
    key = text[:100]
    if key not in seen:
        seen.add(key)
        unique.append((stream, text))

print(f"Total unique text runs: {len(unique)}")

# Print company info and key sections
for stream, text in unique:
    if any(kw in text for kw in ['公司', '投标', '报价', '项目', '弘博士', '法人', '注册', '地址',
                                   '承诺', '财务', '声明', '业绩', '资格', '校服', '采购',
                                   '法定代表人', '营业执照', '税务', '社保']):
        print(f"\n[{stream}] {text[:300]}")

print(f"\n\nTotal hits shown above.")
