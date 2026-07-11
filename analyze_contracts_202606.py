import pandas as pd, os, io, json, re, math
from pathlib import Path
import msoffcrypto

src=Path(r'C:\Users\scrccpa\Desktop\2026年6月合同情况.xlsx')
out=Path(r'C:\Users\scrccpa\.openclaw\workspace\outputs\2026年6月合同情况_解密.xlsx')
out.parent.mkdir(parents=True, exist_ok=True)
password='scrc888'

with open(src,'rb') as f:
    office=msoffcrypto.OfficeFile(f)
    print('encrypted', office.is_encrypted())
    office.load_key(password=password)
    bio=io.BytesIO()
    office.decrypt(bio)
    out.write_bytes(bio.getvalue())
print('decrypted_to', out)

xl=pd.ExcelFile(out, engine='openpyxl')
print('sheets', xl.sheet_names)
# Load all sheets, infer header maybe first non-empty row
sheets={}
for s in xl.sheet_names:
    raw=pd.read_excel(out, sheet_name=s, header=None, engine='openpyxl')
    # drop all-empty rows/cols
    raw=raw.dropna(how='all').dropna(axis=1, how='all')
    print('\nRAW', s, raw.shape)
    print(raw.head(8).to_string(index=False, header=False))
    # choose header row with most non-null / keyword hits in first 10 rows
    best_i=0; best_score=-1
    keywords='合同 客户 委托 单位 项目 金额 业务 类型 签订 签约 日期 收款 回款 负责人 状态 编号'.split()
    for idx in raw.index[:15]:
        vals=[str(x) for x in raw.loc[idx].tolist() if pd.notna(x)]
        score=len(vals)+sum(any(k in v for k in keywords) for v in vals)*3
        if score>best_score:
            best_score=score; best_i=idx
    df=pd.read_excel(out, sheet_name=s, header=best_i, engine='openpyxl')
    df=df.dropna(how='all').dropna(axis=1, how='all')
    # remove unnamed all empty-ish columns
    df.columns=[str(c).strip() if not str(c).startswith('Unnamed') else '' for c in df.columns]
    df=df.loc[:, [c!='' for c in df.columns]]
    sheets[s]=df
    print('DF', s, df.shape, list(df.columns))
    print(df.head(10).to_string(index=False))

# Pick main sheet: max rows*cols containing amount/contract keywords
main_name=max(sheets, key=lambda s: sheets[s].shape[0]*sheets[s].shape[1])
df=sheets[main_name].copy()
print('\nMAIN_SHEET', main_name, df.shape)

# helpers
def find_col(patterns):
    cols=list(df.columns)
    for pat in patterns:
        for c in cols:
            if re.search(pat, str(c), re.I): return c
    return None

amount_col=find_col([r'合同.*金额|金额|收入|收费|价款|审计费|咨询费'])
date_col=find_col([r'签.*日期|签约|签订|合同日期|日期|时间'])
client_col=find_col([r'客户|委托|单位|甲方|业主|采购人'])
project_col=find_col([r'项目|合同.*名|名称|内容'])
type_col=find_col([r'业务.*类型|类型|类别|项目类型|业务'])
leader_col=find_col([r'负责人|经理|承办|经办|项目组'])
status_col=find_col([r'状态|进度|履行|完成'])
received_col=find_col([r'已收|收款|到账|回款|已付'])

print('inferred_cols', dict(amount_col=amount_col,date_col=date_col,client_col=client_col,project_col=project_col,type_col=type_col,leader_col=leader_col,status_col=status_col,received_col=received_col))

# clean amount-like columns
for c in df.columns:
    if df[c].dtype=='object':
        # convert object monetary-looking when majority convertible
        ser=df[c].astype(str).str.replace(',','', regex=False).str.replace('¥','', regex=False).str.replace('元','', regex=False).str.strip()
        conv=pd.to_numeric(ser, errors='coerce')
        if conv.notna().sum()>=max(3, len(df)*0.2):
            # avoid converting date columns that are serial? only if col keyword monetary or inferred
            if c==amount_col or c==received_col or any(k in str(c) for k in ['金额','收入','收费','价款','收款','回款','到账','已付']):
                df[c+'_num']=conv

if amount_col and amount_col+'_num' in df.columns: amount_num=amount_col+'_num'
elif amount_col: amount_num=amount_col
else: amount_num=None
if received_col and received_col+'_num' in df.columns: received_num=received_col+'_num'
elif received_col: received_num=received_col
else: received_num=None

# Remove summary rows maybe where project/client contains 合计
work=df.copy()
for c in [client_col, project_col, type_col]:
    if c and c in work.columns:
        work=work[~work[c].astype(str).str.contains('合计|总计|小计', na=False)]

# ensure amount numeric
if amount_num:
    work['_amount']=pd.to_numeric(work[amount_num], errors='coerce')
else:
    work['_amount']=pd.NA
if received_num:
    work['_received']=pd.to_numeric(work[received_num], errors='coerce')
else:
    work['_received']=pd.NA

# dates
if date_col:
    work['_date']=pd.to_datetime(work[date_col], errors='coerce')
else:
    work['_date']=pd.NaT

valid=work[work['_amount'].notna()].copy()
summary={
    'source': str(src), 'decrypted': str(out), 'main_sheet': main_name,
    'rows_total': int(len(work)), 'rows_with_amount': int(len(valid)),
    'columns': list(df.columns),
    'inferred_cols': dict(amount_col=amount_col,date_col=date_col,client_col=client_col,project_col=project_col,type_col=type_col,leader_col=leader_col,status_col=status_col,received_col=received_col),
}
if len(valid):
    amt=valid['_amount']
    summary.update({
        'contract_count': int(len(valid)),
        'total_amount': float(amt.sum()),
        'avg_amount': float(amt.mean()),
        'median_amount': float(amt.median()),
        'max_amount': float(amt.max()),
        'min_amount': float(amt.min()),
    })
    if valid['_received'].notna().any():
        summary['total_received']=float(valid['_received'].fillna(0).sum())
        summary['collection_rate']=float(valid['_received'].fillna(0).sum()/amt.sum()) if amt.sum() else None
        summary['unreceived']=float(amt.sum()-valid['_received'].fillna(0).sum())

# aggregations
def agg_by(col, top=20):
    if not col or col not in valid.columns or not len(valid): return []
    g=valid.groupby(col, dropna=False).agg(合同数=('_amount','count'), 合同金额=('_amount','sum'), 平均金额=('_amount','mean'))
    if valid['_received'].notna().any():
        g['已收款']=valid.groupby(col)['_received'].sum()
        g['未收款']=g['合同金额']-g['已收款']
    g=g.sort_values('合同金额', ascending=False).head(top).reset_index()
    return g.to_dict('records')

aggs={
    'by_type': agg_by(type_col),
    'by_client': agg_by(client_col),
    'by_leader': agg_by(leader_col),
    'by_status': agg_by(status_col),
}
# Top contracts
show_cols=[]
for c in [client_col, project_col, type_col, date_col, leader_col, status_col]:
    if c and c in valid.columns and c not in show_cols: show_cols.append(c)
top=valid.sort_values('_amount', ascending=False).head(20)[show_cols+['_amount']+(['_received'] if valid['_received'].notna().any() else [])]

# export analysis workbook
report_xlsx=Path(r'C:\Users\scrccpa\.openclaw\workspace\outputs\2026年6月合同经营分析.xlsx')
with pd.ExcelWriter(report_xlsx, engine='openpyxl') as writer:
    pd.DataFrame([summary]).to_excel(writer, sheet_name='总体概况', index=False)
    pd.DataFrame(aggs['by_type']).to_excel(writer, sheet_name='按业务类型', index=False)
    pd.DataFrame(aggs['by_client']).to_excel(writer, sheet_name='按客户', index=False)
    pd.DataFrame(aggs['by_leader']).to_excel(writer, sheet_name='按负责人', index=False)
    pd.DataFrame(aggs['by_status']).to_excel(writer, sheet_name='按状态', index=False)
    top.to_excel(writer, sheet_name='TOP合同', index=False)
    work.to_excel(writer, sheet_name='清洗明细', index=False)

# write json for assistant
analysis_json=Path(r'C:\Users\scrccpa\.openclaw\workspace\outputs\2026年6月合同经营分析.json')
analysis_json.write_text(json.dumps({'summary':summary,'aggs':aggs,'top_contracts':top.to_dict('records')}, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
print('\nSUMMARY_JSON')
print(json.dumps({'summary':summary,'aggs':aggs,'top_contracts':top.to_dict('records')[:10], 'report_xlsx': str(report_xlsx)}, ensure_ascii=False, indent=2, default=str))
