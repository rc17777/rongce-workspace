import json

path = r"C:\Users\scrccpa\Desktop\报告\2.部门预算项目绩效自评复核报告20260722\成都市郫都区民政局2025年度部门预算项目绩效自评复核结果.json"
data = json.load(open(path, encoding="utf-8"))
for sheet in data["sheets"]:
    print(f"=== SHEET {sheet['sheet']} ===")
    for index, row in enumerate(sheet["rows"], 1):
        print(index, " | ".join(row))
for table in data["tables"]:
    print(f"=== WORD TABLE {table['table']} ===")
    for index, row in enumerate(table["rows"], 1):
        print(index, " | ".join(row))
