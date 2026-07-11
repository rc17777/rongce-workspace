import os, openpyxl
tmp = os.path.join(os.environ['TEMP'], 'audit_review')
for f in os.listdir(tmp):
    if '@@' in f:
        att_path = os.path.join(tmp, f)
        break

wb = openpyxl.load_workbook(att_path, read_only=True, data_only=True)

for sn in wb.sheetnames:
    ws = wb[sn]
    hdr = [c.value for c in next(ws.iter_rows(max_row=1))]
    print(f'[{sn}] {ws.max_row}R x {ws.max_column}C')
    hdr_strs = [str(h) for h in hdr]
    print(f'  Hdr: {hdr_strs}')
    rows = list(ws.iter_rows(values_only=True))
    for r in rows[-3:]:
        vals = [str(v) if v else '' for v in r]
        print(f'  Row: {vals}')
    print()
wb.close()
