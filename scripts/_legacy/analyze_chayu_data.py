# -*- coding: utf-8 -*-
"""
察隅县"四个一批"项目台账分析脚本
"""
import pandas as pd
import sys

file_path = r'C:\Users\scrccpa\Desktop\7.10察隅台账 - 最新（以此为准）.xlsx'

print('【察隅县"四个一批"项目台账摘要】\n')

# 读取所有表格
xl = pd.ExcelFile(file_path)

for i, sheet in enumerate(xl.sheet_names, 1):
    df = pd.read_excel(file_path, sheet_name=sheet)
    print(f'{i}. {sheet}')
    print(f'   数据行数: {len(df)}')
    print(f'   数据列数: {len(df.columns)}')
    print()

# 重点分析表格2（项目清单）
print('=' * 60)
print('【核心表：项目清单（表格2）】\n')
sheet_name_2 = xl.sheet_names[1]  # 第2个sheet
df2 = pd.read_excel(file_path, sheet_name=sheet_name_2, skiprows=2)
df2.columns = [str(col).strip() if isinstance(col, str) else col for col in df2.columns]

print(f'项目总数: {len(df2)}')
print(f'\n前10个字段名:')
for idx, col in enumerate(df2.columns[:10], 1):
    print(f'  {idx}. {col}')

# 显示前3行样本
print('\n前3行数据样本:')
print(df2.head(3).to_string(max_colwidth=30))

# 分析表格3（建成类项目）
print('\n' + '=' * 60)
print('【表格3：建成类项目台账】\n')
sheet_name_3 = xl.sheet_names[2]  # 第3个sheet
df3 = pd.read_excel(file_path, sheet_name=sheet_name_3, skiprows=2)
df3.columns = [str(col).strip() if isinstance(col, str) else col for col in df3.columns]
print(f'建成项目数: {len(df3)}')
print(f'\n前10个字段名:')
for idx, col in enumerate(df3.columns[:10], 1):
    print(f'  {idx}. {col}')
