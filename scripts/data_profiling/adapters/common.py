# -*- coding: utf-8 -*-
"""
审盾数据帧 (SDF) 公共层 — 六入口适配器共享
提供: SDF构建 / 数据清洗 / 列类型推断 / 语义标注 / OCR质量分层 / 输出

SDF结构见: knowledge/strategy/审盾-数据理解底座-离线异构适配器设计-20260804.md
"""
import sys, os, json, hashlib, datetime, statistics, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

# ─── 语义角色关键词（与 profile_builder.py 对齐） ───────────
AMOUNT_KEYWORDS = ['金额', '元', '万元', '亿元', '预算', '支出', '收入', '余额', '资金', '经费', '成本', '费用', '价', 'amount']
QUANTITY_KEYWORDS = ['数量', '人', '次', '个', '项', '件', '台', '辆', '㎡', 'm²', '天', '小时', '张', '笔', 'quantity']
DATE_KEYWORDS = ['日期', '时间', '年', '月', '日', 'date', 'time', 'period']
CATEGORY_KEYWORDS = ['类型', '分类', '类别', '科目', '项目', '部门', '单位', '名称', '编号', '类别']
TEXT_KEYWORDS = ['说明', '描述', '备注', '意见', '内容', '事由', '摘要', 'text', 'note']
IDENTIFIER_KEYWORDS = ['编号', '代码', 'id', 'ID', '序号', '编码', '凭证号', '合同号', '发票号', 'code', 'no.']

DATE_PATTERNS = [
    re.compile(r'^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}([ T]\d{1,2}:\d{1,2}(:\d{1,2})?)?$'),
    re.compile(r'^\d{4}年\d{1,2}月\d{1,2}日?$'),
    re.compile(r'^\d{8}$'),  # 20250101
    re.compile(r'^\d{4}[-/.]\d{1,2}$'),
]

def now_iso():
    return datetime.datetime.now().astimezone().isoformat()

def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def clean_value(v):
    """统一清洗单个值: 去空白 / 空串→None / 数字串→数值"""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip().strip('"').strip("'")
        if s == '' or s.lower() in ('null', 'none', 'nan', 'n/a', '—', '-', '/', '\\'):
            return None
        # 数字串 → 数值（千分位、中文逗号）
        t = s.replace(',', '').replace('，', '')
        try:
            if re.fullmatch(r'[-+]?\d+', t):
                return int(t)
            if re.fullmatch(r'[-+]?\d+\.\d+', t):
                return float(t)
        except:
            pass
        return s
    return v

def clean_rows(rows, keys=None):
    """统一清洗行列表: 空值归一 / 类型推断后的值转换"""
    if not rows:
        return rows
    cleaned = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        cleaned.append({k: clean_value(v) for k, v in r.items()})
    return cleaned

def infer_col_type(values):
    """列类型推断: number / decimal / date / boolean / string"""
    samples = [v for v in values if v is not None]
    if not samples:
        return 'string'
    numeric = 0
    date_hits = 0
    bool_hits = 0
    for v in samples[:500]:
        s = str(v).strip()
        if isinstance(v, bool):
            bool_hits += 1
            continue
        if re.fullmatch(r'[-+]?\d+', s):
            numeric += 1
        elif re.fullmatch(r'[-+]?\d+\.\d+', s):
            numeric += 1
        elif any(p.match(s) for p in DATE_PATTERNS):
            date_hits += 1
        elif s.lower() in ('true', 'false', '是', '否', 'yes', 'no'):
            bool_hits += 1
    n = len(samples)
    if numeric / n > 0.9:
        # int vs decimal
        has_dec = any('.' in str(v) for v in samples if v is not None)
        return 'decimal' if has_dec else 'number'
    if date_hits / n > 0.8:
        return 'date'
    if bool_hits / n > 0.8:
        return 'boolean'
    return 'string'

def detect_field_role(name, samples):
    """列名+样本 → 语义角色（与 profile_builder 规则对齐）"""
    name_lower = name.lower()
    for kw in IDENTIFIER_KEYWORDS:
        if kw in name:
            return 'identifier'
    for kw in AMOUNT_KEYWORDS:
        if kw in name:
            return 'amount'
    for kw in DATE_KEYWORDS:
        if kw in name:
            return 'date'
    for kw in CATEGORY_KEYWORDS:
        if kw in name:
            return 'category'
    for kw in TEXT_KEYWORDS:
        if kw in name:
            return 'text'
    for kw in QUANTITY_KEYWORDS:
        if kw in name:
            return 'quantity'
    # 值推断兜底
    t = infer_col_type(samples)
    if t in ('number', 'decimal'):
        return 'amount'
    if t == 'date':
        return 'date'
    return 'unknown'

def guess_unit(name, samples):
    if '亿元' in name: return '亿元'
    if '万元' in name: return '万元'
    if '元' in name: return '元'
    if '%' in name or '率' in name or '比例' in name: return '%'
    if '人' in name: return '人'
    if '次' in name: return '次'
    if '个' in name: return '个'
    return ''

def semantic_annotate(columns, rows):
    """
    语义标注层: 对列做角色标注 + 生成 semantic_tags 分组
    columns: [{'name': str, 'type': str, ...}]
    rows: [dict]
    返回 (columns_annotated, semantic_tags)
    """
    tags = {'financial': [], 'date': [], 'entity': [], 'id': [], 'quantity': [], 'text': []}
    for col in columns:
        name = col['name']
        samples = [r.get(name) for r in rows if r.get(name) is not None]
        role = detect_field_role(name, samples)
        col['role'] = role
        col['unit'] = guess_unit(name, samples) if role in ('amount', 'quantity') else ''
        if role == 'amount':
            tags['financial'].append(name)
        elif role == 'date':
            tags['date'].append(name)
        elif role in ('category',):
            tags['entity'].append(name)
        elif role == 'identifier':
            tags['id'].append(name)
        elif role == 'quantity':
            tags['quantity'].append(name)
        elif role == 'text':
            tags['text'].append(name)
    return columns, {k: v for k, v in tags.items() if v}

def column_stats(values):
    """数值列统计: min/max/mean/std"""
    nums = []
    for v in values:
        if v is None:
            continue
        try:
            nums.append(float(v))
        except:
            pass
    if len(nums) < 3:
        return {}
    stats = {'min': min(nums), 'max': max(nums), 'mean': round(statistics.mean(nums), 2)}
    if len(nums) > 2:
        stats['std'] = round(statistics.stdev(nums), 2)
    return stats

def build_sdf(source_type, original_file, rows, columns=None, checksum='', extra_source=None, semantic_tags=None):
    """
    构建标准 SDF（审盾数据帧）
    rows: [dict] 清洗后数据行
    columns: 可选 [{'name','type',...}]，缺省自动推断
    """
    rows = clean_rows(rows)
    if columns is None:
        keys = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        columns = []
        for k in keys:
            vals = [r.get(k) for r in rows]
            columns.append({
                'name': k,
                'type': infer_col_type(vals),
                'nullable': any(v is None for v in vals),
                'unique_rate': round(len(set(str(v) for v in vals if v is not None)) / max(len([v for v in vals if v is not None]), 1), 4) if any(v is not None for v in vals) else 0,
                'sample': [str(v)[:50] for v in vals if v is not None][:5],
                'stats': column_stats(vals) if infer_col_type(vals) in ('number', 'decimal') else {}
            })

    columns, auto_tags = semantic_annotate(columns, rows)
    if semantic_tags is None:
        semantic_tags = auto_tags

    nulls = sum(1 for r in rows for v in r.values() if v is None)
    total = max(sum(len(r) for r in rows), 1)
    seen = set()
    dup = 0
    for r in rows:
        sig = json.dumps(r, ensure_ascii=False, sort_keys=True)
        if sig in seen:
            dup += 1
        else:
            seen.add(sig)

    sdf = {
        'source': {
            'type': source_type,
            'original_file': original_file,
            'ingestion_time': now_iso(),
            'checksum': checksum,
        },
        'profile': {
            'row_count': len(rows),
            'col_count': len(columns),
            'encoding': 'utf-8',
            'null_rate': round(nulls / total, 4) if total else 0,
            'duplicate_rows': dup,
        },
        'schema': {'columns': columns},
        'semantic_tags': semantic_tags,
        'data': rows,
    }
    if extra_source:
        sdf['source'].update(extra_source)
    return sdf

def save_sdf(sdf, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(sdf, f, ensure_ascii=False, indent=2)
    return out_path

def print_sdf_summary(sdf):
    s = sdf['profile']
    src = sdf['source']
    print(f'  📦 SDF: {src["type"]} | 文件: {src["original_file"]}')
    print(f'    行: {s["row_count"]} | 列: {s["col_count"]} | 空值率: {s["null_rate"]*100:.1f}% | 重复行: {s["duplicate_rows"]}')
    roles = {}
    for c in sdf['schema']['columns']:
        roles[c.get('role', 'unknown')] = roles.get(c.get('role', 'unknown'), 0) + 1
    print(f'    角色: {roles}')

def quality_layer(mean_conf):
    """
    OCR 质量分层 (设计文档 4.3):
    >=0.95 高质量自动入库 / 0.85-0.95 标记抽检 / <0.85 暂停人工确认
    """
    if mean_conf >= 0.95:
        return 'high'
    if mean_conf >= 0.85:
        return 'medium'
    return 'low'
