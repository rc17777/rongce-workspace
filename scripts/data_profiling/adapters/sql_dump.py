# -*- coding: utf-8 -*-
"""
SQL dump 适配器 — 解析 .sql 导出文件
适用: 被审计单位IT配合导出的数据库备份 (CREATE TABLE + INSERT)
流程: 编码检测 → 注释剥离 → CREATE TABLE解析 → INSERT数据行提取 → 每表一个SDF

用法: python sql_dump.py --source "dump.sql" --out outdir [--table 表名]
输出: outdir/<label>_<表名>_sdf.json (多表时每表一个)
"""
import sys, os, json, re, argparse, datetime
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import build_sdf, save_sdf, print_sdf_summary, sha256_file

# ─── 编码检测 ─────────────────────────────────────────
def read_sql_text(path):
    raw = Path(path).read_bytes()
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'latin-1'):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, ValueError):
            continue
    return raw.decode('utf-8', errors='replace')

# ─── 注释剥离 ─────────────────────────────────────────
def strip_comments(sql):
    """剥离 -- 行注释 / # 行注释 / /* */ 块注释 (保留字符串内)"""
    out = []
    i = 0
    n = len(sql)
    in_str = None  # None / "'" / '"' / '`'
    while i < n:
        c = sql[i]
        if in_str:
            out.append(c)
            if c == '\\' and in_str in ("'", '"'):
                if i + 1 < n:
                    out.append(sql[i + 1])
                    i += 2
                    continue
            elif c == in_str:
                in_str = None
            i += 1
            continue
        if c in ("'", '"', '`'):
            in_str = c
            out.append(c)
            i += 1
            continue
        if c == '-' and sql[i:i+2] == '--':
            j = sql.find('\n', i)
            i = n if j == -1 else j + 1
            continue
        if c == '#':
            j = sql.find('\n', i)
            i = n if j == -1 else j + 1
            continue
        if c == '/' and sql[i:i+2] == '/*':
            j = sql.find('*/', i + 2)
            i = n if j == -1 else j + 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)

# ─── SQL语句切分 ──────────────────────────────────────
def split_statements(sql):
    """按分号切分, 尊重引号/括号"""
    stmts = []
    cur = []
    i = 0
    n = len(sql)
    in_str = None
    depth = 0
    while i < n:
        c = sql[i]
        if in_str:
            cur.append(c)
            if c == '\\' and in_str in ("'", '"'):
                if i + 1 < n:
                    cur.append(sql[i + 1])
                    i += 2
                    continue
            elif c == in_str:
                in_str = None
            i += 1
            continue
        if c in ("'", '"', '`'):
            in_str = c
            cur.append(c)
            i += 1
            continue
        if c == '(':
            depth += 1
            cur.append(c)
        elif c == ')':
            depth = max(0, depth - 1)
            cur.append(c)
        elif c == ';' and depth == 0:
            stmts.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if ''.join(cur).strip():
        stmts.append(''.join(cur).strip())
    return [s for s in stmts if s]

# ─── CREATE TABLE 解析 ────────────────────────────────
CREATE_RE = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?\s*\((.*?)\)\s*(?:ENGINE\s*=|DEFAULT\s+CHARSET|COLLATE\s*=|CHARSET\s*=|;|$)',
    re.IGNORECASE | re.DOTALL
)

def split_top_level(s, sep=','):
    """顶层切分(尊重引号/括号)"""
    parts = []
    cur = []
    i = 0
    n = len(s)
    in_str = None
    depth = 0
    while i < n:
        c = s[i]
        if in_str:
            cur.append(c)
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c in ("'", '"', '`'):
            in_str = c
            cur.append(c)
            i += 1
            continue
        if c == '(':
            depth += 1
            cur.append(c)
        elif c == ')':
            depth -= 1
            cur.append(c)
        elif c == sep and depth == 0:
            parts.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if ''.join(cur).strip():
        parts.append(''.join(cur).strip())
    return parts

def parse_column_def(def_str):
    """解析列定义: `name` TYPE [约束...] → {name, type, nullable, primary_key, auto_increment}"""
    def_str = def_str.strip()
    if not def_str or re.match(r'^(PRIMARY|KEY|UNIQUE|CONSTRAINT|INDEX|FOREIGN|CHECK|FULLTEXT|SPATIAL)', def_str, re.IGNORECASE):
        return None  # 表级约束跳过
    m = re.match(r'^`?([^`\s]+)`?\s+([A-Za-z]+(?:\([^)]*\))?(?:[A-Za-z\s]*(?:unsigned|zerofill|binary))?)\s*(.*)$', def_str, re.IGNORECASE)
    if not m:
        return None
    name, dtype, rest = m.group(1), m.group(2), (m.group(3) or '').upper()
    return {
        'name': name,
        'type': dtype,
        'nullable': 'NOT NULL' not in rest,
        'primary_key': 'PRIMARY KEY' in rest,
        'auto_increment': 'AUTO_INCREMENT' in rest,
        'default': re.search(r'DEFAULT\s+(.+?)(?=\s+(NOT|NULL|PRIMARY|UNIQUE|AUTO_INCREMENT|COMMENT)|$)', rest, re.IGNORECASE).group(1).strip() if re.search(r'DEFAULT\s+', rest, re.IGNORECASE) else '',
    }

# ─── INSERT 解析 ──────────────────────────────────────
INSERT_RE = re.compile(
    r'INSERT\s+(?:IGNORE\s+)?INTO\s+`?(\w+)`?\s*(?:\(([^)]*)\))?\s*VALUES\s*(.*)$',
    re.IGNORECASE | re.DOTALL
)

def parse_value(v):
    v = v.strip()
    if not v:
        return None
    up = v.upper()
    if up == 'NULL':
        return None
    if v.startswith("'") or v.startswith('"'):
        # 字符串: 处理转义
        quote = v[0]
        body = v[1:]
        if body.endswith(quote):
            body = body[:-1]
        body = body.replace('\\' + quote, quote).replace('\\\\', '\\').replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
        return body
    if up in ('TRUE',):
        return True
    if up in ('FALSE',):
        return False
    if re.fullmatch(r'[-+]?\d+', v):
        return int(v)
    if re.fullmatch(r'[-+]?\d+\.\d+', v):
        return float(v)
    if re.fullmatch(r'0x[0-9a-fA-F]+', v):
        try:
            return bytes.fromhex(v[2:]).decode('utf-8', errors='replace')
        except:
            return v
    if v.startswith('NOW()') or v.startswith('CURRENT_') or v.startswith('CURDATE()'):
        return v  # 函数值保留原样
    return v

def parse_values_tuple(t):
    """解析一行 VALUES 元组 → [值...]"""
    vals = []
    cur = []
    i = 0
    n = len(t)
    in_str = None
    while i < n:
        c = t[i]
        if in_str:
            cur.append(c)
            if c == '\\' and in_str in ("'", '"'):
                if i + 1 < n:
                    cur.append(t[i + 1])
                    i += 2
                    continue
            elif c == in_str:
                in_str = None
            i += 1
            continue
        if c in ("'", '"'):
            in_str = c
            cur.append(c)
            i += 1
            continue
        if c == ',':
            vals.append(parse_value(''.join(cur)))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    if ''.join(cur).strip():
        vals.append(parse_value(''.join(cur)))
    return vals

def parse_insert(stmt):
    """解析 INSERT 语句 → (表名, 列名列表, [行...])"""
    m = INSERT_RE.match(stmt)
    if not m:
        return None
    table = m.group(1)
    cols_str = m.group(2)
    values_str = m.group(3)
    columns = [c.strip().strip('`') for c in cols_str.split(',')] if cols_str else None
    # 提取元组: 尊重括号深度
    tuples = []
    depth = 0
    cur = []
    in_str = None
    for c in values_str:
        if in_str:
            cur.append(c)
            if c == in_str:
                in_str = None
            continue
        if c in ("'", '"'):
            in_str = c
            cur.append(c)
            continue
        if c == '(':
            depth += 1
            if depth == 1:
                cur = []
                continue
        elif c == ')':
            depth -= 1
            if depth == 0:
                tuples.append(''.join(cur))
                continue
        cur.append(c)
    rows = [parse_values_tuple(t) for t in tuples]
    return table, columns, rows

# ─── 主流程 ───────────────────────────────────────────
def parse_dump(source):
    """解析整个dump → {表名: {'columns': [...], 'rows': [...]}}"""
    sql = strip_comments(read_sql_text(source))
    stmts = split_statements(sql)
    tables = {}
    for stmt in stmts:
        m = CREATE_RE.search(stmt)
        if m and m.group(1) not in tables:
            table_name = m.group(1)
            cols = []
            for part in split_top_level(m.group(2)):
                cd = parse_column_def(part)
                if cd:
                    cols.append(cd)
            tables[table_name] = {'columns': cols, 'rows': []}
            continue
        ins = parse_insert(stmt)
        if ins:
            table, cols, rows = ins
            if table not in tables:
                tables[table] = {'columns': [], 'rows': []}
            if cols and not tables[table]['columns']:
                tables[table]['columns'] = [{'name': c, 'type': 'string'} for c in cols]
            tables[table]['rows'].extend(rows)
    return tables

def convert(source, out_dir=None, table_filter=None, label='sql'):
    """
    主入口: 每表构建一个SDF
    返回 [(表名, sdf路径, sdf), ...]
    """
    checksum = sha256_file(source)
    tables = parse_dump(source)
    if not tables:
        raise ValueError(f'未解析到任何表: {source}')

    results = []
    for tname, tdata in tables.items():
        if table_filter and tname != table_filter:
            continue
        columns = tdata['columns']
        col_names = [c['name'] for c in columns]
        rows = []
        for r in tdata['rows']:
            if col_names:
                rec = {col_names[i]: (r[i] if i < len(r) else None) for i in range(len(col_names))}
            else:
                rec = {f'col{i+1}': v for i, v in enumerate(r)}
            rows.append(rec)

        sdf = build_sdf('sql_dump', os.path.basename(source), rows,
                        checksum=checksum,
                        extra_source={'table': tname, 'sql_tables': list(tables.keys())})
        # 列类型优先用CREATE TABLE定义
        for c in sdf['schema']['columns']:
            for cd in columns:
                if cd['name'] == c['name']:
                    c['sql_type'] = cd['type']
                    c['sql_nullable'] = cd['nullable']
                    c['sql_primary_key'] = cd['primary_key']
                    break

        path = None
        if out_dir:
            out_dir = Path(out_dir)
            fname = f'{label}_{tname}_sdf.json'
            path = save_sdf(sdf, out_dir / fname)
        results.append((tname, path, sdf))
    return results

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='SQL dump 适配器')
    p.add_argument('--source', required=True, help='.sql 文件路径')
    p.add_argument('--out', help='输出目录')
    p.add_argument('--table', help='只处理指定表')
    p.add_argument('--label', default='sql', help='SDF文件名前缀')
    args = p.parse_args()

    results = convert(args.source, args.out, args.table, args.label)
    for tname, path, sdf in results:
        print(f'  📦 表 [{tname}]:')
        print_sdf_summary(sdf)
        if path:
            print(f'     保存: {path}')
