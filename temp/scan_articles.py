# -*- coding: utf-8 -*-
"""Scan article directories, extract essence: headings, numeric lines, key-term lines."""
import os, sys, re, json
sys.stdout.reconfigure(encoding='utf-8')

KEYWORDS = ['疑点','模型','比对','阈值','异常','信号','方法','查证','核实','分析','指标','筛查','预警',
            '规则','逻辑','穿透','勾稽','抽样','样本','占比','同比','环比','偏离','偏差','排序','排名',
            '聚类','关联','风险','漏洞','问题','违规','骗取','套取','虚报','重复','不符','差异','预警']
NUM_RE = re.compile(r'\d+(?:\.\d+)?\s*(?:万|亿|元|%|％|倍|人|户|亩|吨|米|公里|家|项|笔|张|次)?')

def read_any(path):
    raw = open(path, 'rb').read()
    for enc in ['utf-16', 'utf-8-sig', 'utf-8', 'gbk']:
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode('utf-8', errors='replace')

def extract_essence(path, max_lines=6000):
    try:
        text = read_any(path)
        lines = text.splitlines()
    except Exception as e:
        return f"[ERR {e}]"
    out = []
    total = len(lines)
    out.append(f"<len={total}>")
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            continue
        # headings
        if re.match(r'^#{1,4}\s', s):
            out.append("H: " + s[:80])
        # lines with numbers
        elif NUM_RE.search(s) and len(s) < 200 and not re.match(r'^\s*$', s):
            if any(k in s for k in ['万','亿','元','%','％','亩','吨','户','人','家','笔','张','倍']):
                out.append("N: " + s[:150])
        # keyword lines (short)
        elif len(s) < 160 and sum(1 for k in KEYWORDS if k in s) >= 2:
            out.append("K: " + s[:150])
        if len(out) > 400:
            out.append("...[truncated]")
            break
    return "\n".join(out)

if __name__ == '__main__':
    base = r'D:\杂志资料\按类型'
    dirs = sys.argv[1:] or sorted(os.listdir(base))
    out_path = None
    if dirs and dirs[-1].startswith('--out='):
        out_path = dirs.pop(-1)[6:]
    buf = []
    for d in dirs:
        p = os.path.join(base, d)
        if not os.path.isdir(p):
            continue
        buf.append(f"\n{'='*70}\n### {d}\n{'='*70}")
        for f in sorted(os.listdir(p)):
            fp = os.path.join(p, f)
            buf.append(f"\n--- {f} ---")
            buf.append(extract_essence(fp))
    text = "\n".join(buf)
    if out_path:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"written {len(text)} chars -> {out_path}")
    else:
        print(text)
