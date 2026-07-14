# -*- coding: utf-8 -*-
"""
察隅县"四个一批"项目台账深度分析
"""
import pandas as pd
import sys, os, json

sys.stdout.reconfigure(encoding='utf-8')

file_path = r'C:\Users\scrccpa\Desktop\7.10察隅台账 - 最新（以此为准）.xlsx'
output_dir = r'C:\Users\scrccpa\.openclaw\workspace\chayu_analysis'
os.makedirs(output_dir, exist_ok=True)

xl = pd.ExcelFile(file_path)

# 1. 输出各sheet名称
print('#' * 60)
print('【Sheet名称与实际内容】')
for s in xl.sheet_names:
    df = pd.read_excel(file_path, sheet_name=s, header=None)
    # 读取前3行看标题
    print(f'\nSheet: [{s}] 行数:{len(df)} 列数:{len(df.columns)}')
    for r in range(min(5, len(df))):
        vals = [str(v)[:30] for v in df.iloc[r].values if str(v) != 'nan' and str(v) != '']
        if vals:
            print(f'  行{r}: {vals[:8]}')

# 2. 不同起始行读取关键表格
print('\n' + '=' * 60)
print('【关键表格列名分析】\n')

for sname, skip, label in [
    (xl.sheet_names[1], 3, '项目清单总表'),
    (xl.sheet_names[2], 3, '建成类项目台账'),
]:
    df = pd.read_excel(file_path, sheet_name=sname, header=None)
    # 获取有效数据行（跳过汇总行和说明行）
    data_start = None
    for r in range(len(df)):
        first_val = str(df.iloc[r, 0])
        # 找到序号列以数字开头
        if first_val.strip().isdigit():
            data_start = r
            break
        # 或者找到包含项目信息的行
        if first_val and '项目' in first_val and len(str(df.iloc[r, 0])) < 5:
            data_start = r
            break
    
    print(f'★ {label} (Sheet: {sname})')
    if data_start:
        print(f'  数据起始行: {data_start}')
        # 检查这行的真实列
        data_row = df.iloc[data_start]
        cols_with_data = [(i, str(v)[:20]) for i, v in enumerate(data_row) if str(v) != 'nan' and str(v) != '']
        print(f'  数据列: {len(cols_with_data)}列')
        for i, (idx, val) in enumerate(cols_with_data, 1):
            print(f'    {i:2d}. 列[{idx:2d}]: {val}')
    print()

# 3. 获取实际项目数据（跳过多行表头）
print('=' * 60)
print('【项目数据提取与分析】\n')

# 表格3的数据提取
s3name = xl.sheet_names[2]
df3_raw = pd.read_excel(file_path, sheet_name=s3name, header=None)

# 找数据起始行
data_start_3 = None
for r in range(len(df3_raw)):
    v = str(df3_raw.iloc[r, 0])
    # 找数字开头
    if v.strip().isdigit():
        data_start_3 = r
        break

if data_start_3:
    print(f'★ 建成类项目（表格3）- 数据从第{data_start_3}行开始')
    # 列名从上一行获取
    header_row = data_start_3 - 1 if data_start_3 > 0 else 0
    headers = [str(v)[:30] for v in df3_raw.iloc[header_row].values]
    df3 = df3_raw.iloc[data_start_3:].copy()
    df3.columns = headers
    
    print(f'  项目数: {len(df3)}')
    print(f'  列数: {len(df3.columns)}')
    
    # 输出统计关键字段
    key_fields = ['项目状态', '项目类别', '项目实施地点', '计划投资', '实际投资', 
                  '是否已确权', '资产来源', '运营单位', '分红', '带动就业',
                  '现场照片', '巡查记录', '运营日记']
    
    for kf in key_fields:
        for col in df3.columns:
            if kf in col or col[:2] == kf[:2]:
                non_null = df3[col].notna().sum()
                print(f'  字段[{col}]: {non_null}/{len(df3)} 非空')
                break
    
    # 导出样本
    df3.to_csv(os.path.join(output_dir, '表格3_建成项目_样本.csv'), index=False, encoding='utf-8-sig')
    print(f'  → 导出csv: 表格3_建成项目_样本.csv')

# 4. 表格5-1 资产台账
s5name = xl.sheet_names[3]
df51_raw = pd.read_excel(file_path, sheet_name=s5name, header=None)
data_start_51 = None
for r in range(len(df51_raw)):
    v = str(df51_raw.iloc[r, 0])
    if v.strip().isdigit():
        data_start_51 = r
        break

if data_start_51:
    print(f'\n★ 建成项目资产台账（表格5-1）- 数据从第{data_start_51}行开始')
    header_row = data_start_51 - 1
    headers = [str(v)[:30] for v in df51_raw.iloc[header_row].values]
    df51 = df51_raw.iloc[data_start_51:].copy()
    df51.columns = headers
    print(f'  资产数: {len(df51)}')
    print(f'  列数: {len(df51.columns)}')
    
    # 找确权相关字段
    print(f'  列名列表:')
    for idx, h in enumerate(headers):
        if str(h) != 'nan':
            print(f'    列[{idx:2d}]: {h}')
    
    # 确权统计
    for col in df51.columns:
        if '确权' in str(col) or '权属' in str(col):
            val_counts = df51[col].value_counts(dropna=False)
            print(f'\n  ⚠️  字段: [{col}]')
            print(f'    统计: {dict(val_counts.head(10))}')

# 5. 表格6 低效闲置资产
s6name = xl.sheet_names[5]
df6_raw = pd.read_excel(file_path, sheet_name=s6name, header=None)
data_start_6 = None
for r in range(len(df6_raw)):
    v = str(df6_raw.iloc[r, 0])
    if v.strip().isdigit():
        data_start_6 = r
        break

if data_start_6:
    print(f'\n★ 低效闲置资产台账（表格6）- 数据从第{data_start_6}行开始')
    header_row = data_start_6 - 1
    headers = [str(v)[:30] for v in df6_raw.iloc[header_row].values]
    df6 = df6_raw.iloc[data_start_6:].copy()
    df6.columns = headers
    print(f'  资产数: {len(df6)}')
    print(f'  列数: {len(df6.columns)}')
    
    # 列名
    print(f'  列名列表:')
    for idx, h in enumerate(headers):
        if str(h) != 'nan':
            print(f'    列[{idx:2d}]: {h}')
    
    # 统计关键字段
    for col in df6.columns:
        col_s = str(col)
        if any(k in col_s for k in ['状态', '闲置', '盘活', '原因', '利用', '运营']):
            non_null = df6[col].notna().sum()
            print(f'  字段[{col_s[:25]}]: {non_null}/{len(df6)} 非空')

print('\n' + '#' * 60)
print('分析完成。数据已导出到:', output_dir)