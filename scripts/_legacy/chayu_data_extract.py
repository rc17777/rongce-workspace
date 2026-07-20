# -*- coding: utf-8 -*-
"""
察隅台账深度分析 - 提取各表关键字段统计
"""
import pandas as pd
import sys, os, json

sys.stdout.reconfigure(encoding='utf-8')

file_path = r'C:\Users\scrccpa\Desktop\7.10察隅台账 - 最新（以此为准）.xlsx'
output_dir = r'C:\Users\scrccpa\.openclaw\workspace\chayu_analysis'
os.makedirs(output_dir, exist_ok=True)

xl = pd.ExcelFile(file_path)

# ===== 1. 附件3：建成产业项目台账 =====
print('='*60)
print('【附件3：建成产业项目台账】')
s3 = xl.sheet_names[2]
df3 = pd.read_excel(file_path, sheet_name=s3, header=None, skiprows=4)
# 前24列是有效数据
df3 = df3.iloc[:, :34]

# 定义列名（基于分析结果）
cols3 = [
    '项目编号', '地市', '县区', '年度', '项目名称', '申报主体', '实施地点', 
    '建设内容', '计划投资_小计', '计划投资_政策', '计划投资_其他',
    '实际投资_小计', '实际投资_政策', '实际投资_其他',
    '经营主体类别', '经营名称',
    '运营状态', '四批分类',  # 调整/调整等
    '是否经营', '是否脱贫带动', '运营模式', '运营日记',
    '分红金额', '带动就业人数', '带动群众信息',
    '确权状态', '权属来源', '备注',
    '是否现场照片', '是否巡查记录', '是否运营日记填写',
    'col32', 'col33'
]
# 只取有数据的列
df3 = df3.iloc[:, :min(len(cols3), df3.shape[1])]
df3.columns = cols3[:df3.shape[1]]

# 关键字段统计
print(f'\n项目总数: {len(df3)}')
print(f'年度分布:\n{df3["年度"].value_counts().sort_index()}')

# 经营主体类别
print(f'\n经营主体类别分布:\n{df3["经营主体类别"].value_counts()}')

# 运营状态
if '运营状态' in df3.columns:
    print(f'\n运营状态分布:\n{df3["运营状态"].value_counts()}')

# 是否现场照片、巡查记录、运营日记
for col in ['是否现场照片', '是否巡查记录', '是否运营日记填写']:
    if col in df3.columns:
        print(f'\n{col}:\n{df3[col].value_counts(dropna=False)}')

# 分红统计（非空/空）
print(f'\n分红金额非空数: {df3["分红金额"].notna().sum()} / {len(df3)}')
print(f'带动就业人数非空数: {df3["带动就业人数"].notna().sum()} / {len(df3)}')

# ===== 2. 附件2：项目清单 =====
print('\n' + '='*60)
print('【附件2：项目清单】')
s2 = xl.sheet_names[1]
df2 = pd.read_excel(file_path, sheet_name=s2, header=None, skiprows=6)
# 读取关键列
cols2_stub = ['序号', '地市', '县区', '年度', '项目名称', '是否形成资产', '是否产业项目']
# 资金列一大堆，按列位置读取
df2_stub = df2.iloc[:, :7].copy()
# 只取前7列的基本信息
df2_stub.columns = cols2_stub
print(f'项目总数: {len(df2_stub)}')
print(f'年度分布:\n{df2_stub["年度"].value_counts().sort_index()}')
print(f'是否形成资产:\n{df2_stub["是否形成资产"].value_counts(dropna=False)}')
print(f'是否产业项目:\n{df2_stub["是否产业项目"].value_counts(dropna=False)}')

# 统计四个一批分类（从附件3第17列）
print('\n' + '='*60)
print('【附件3四批分类统计】')
if '四批分类' in df3.columns:
    print(f'\n四批分类分布:\n{df3["四批分类"].value_counts()}')

# 找出附件3中是否有'四个一批'相关字段
# 看第17-18列
for col_idx in [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]:
    if col_idx < df3.shape[1]:
        col_data = df3.iloc[:, col_idx]
        unique_vals = col_data.dropna().unique()[:20]
        print(f'列{col_idx} 示例值: {unique_vals}')

# ===== 3. 附件6：低效闲置资产明细 =====
print('\n' + '='*60)
print('【附件6：低效闲置资产台账】')
s6 = xl.sheet_names[5]
df6 = pd.read_excel(file_path, sheet_name=s6, header=None, skiprows=3)
df6 = df6.iloc[:, :25]

# 附件6列定义
cols6 = ['项目编号', '县区', '资产编号', '资产名称', '构建时间', '位置', 
         '型号', '预计年限', '资产类别', '原值',
         '累计折旧', '净值', '资产形态', '资产明细类型',
         '资产权属', '资产状态', '资产使用状况', '使用方式',
         '经营类型', '低效闲置类型', '资产权属主体', '盘活措施',
         '是否已盘活', '盘活时间', '备注']

if df6.shape[1] <= len(cols6):
    df6.columns = cols6[:df6.shape[1]]

# 统计
print(f'低效闲置资产总数: {len(df6)}')
if '低效闲置类型' in df6.columns:
    print(f'低效vs闲置分布:\n{df6["低效闲置类型"].value_counts(dropna=False)}')
if '资产状态' in df6.columns:
    print(f'资产状态分布:\n{df6["资产状态"].value_counts(dropna=False)}')
if '资产形态' in df6.columns:
    print(f'资产形态分布:\n{df6["资产形态"].value_counts(dropna=False)}')
if '资产权属' in df6.columns:
    print(f'资产权属:\n{df6["资产权属"].value_counts(dropna=False)}')
if '是否已盘活' in df6.columns:
    print(f'是否已盘活:\n{df6["是否已盘活"].value_counts(dropna=False)}')
if '盘活措施' in df6.columns:
    print(f'盘活措施非空: {df6["盘活措施"].notna().sum()}/{len(df6)}')

# 资产类型
if '资产明细类型' in df6.columns:
    print(f'明细类型:\n{df6["资产明细类型"].value_counts()}')

# 示例
print(f'\n前5个低效闲置资产:')
for i in range(min(5, len(df6))):
    row = df6.iloc[i]
    print(f'  {row["资产名称"]} | {row["位置"]} | 类型:{row.get("低效闲置类型","")} | 状态:{row.get("资产状态","")}')

# ===== 4. 附件5-1：资产台账 =====
print('\n' + '='*60)
print('【附件5-1：项目资产总台账】')
s51 = xl.sheet_names[3]
df51 = pd.read_excel(file_path, sheet_name=s51, header=None, skiprows=5)
df51 = df51.iloc[:, :16]

cols51 = ['项目编号', '县区', '年度', '项目名称', '实际投入', '资产个数',
          '原值', '净值', '资产类型', '所有权主体', '经营权主体',
          '收益权主体', '监督权主体', '处置权主体', '备注1', '备注2']
if df51.shape[1] <= len(cols51):
    df51.columns = cols51[:df51.shape[1]]

print(f'项目资产条目: {len(df51)}')
if '资产类型' in df51.columns:
    print(f'资产类型:\n{df51["资产类型"].value_counts(dropna=False)}')
if '所有权主体' in df51.columns:
    print(f'所有权主体:\n{df51["所有权主体"].value_counts(dropna=False)}')
if '经营权主体' in df51.columns:
    print(f'经营权主体:\n{df51["经营权主体"].value_counts(dropna=False)}')

# ===== 5. 附件9：待处置资产 =====
print('\n' + '='*60)
print('【附件9：待处置资产台账】')
s9 = xl.sheet_names[6]
df9 = pd.read_excel(file_path, sheet_name=s9, header=None, skiprows=3)
df9 = df9.iloc[:, :25]

print(f'待处置资产数: {len(df9)}')

# ===== 6. 四个一批分类（基于年度分析） =====
print('\n' + '='*60)
print('【年度项目分布（基于附件2）】')
year_counts = df2_stub.groupby('年度').size()
print(year_counts.to_string())

# 分类统计
early = (df2_stub['年度'] <= 2020).sum()
mid = ((df2_stub['年度'] >= 2021) & (df2_stub['年度'] <= 2023)).sum()
recent = (df2_stub['年度'] >= 2024).sum()
print(f'\n2013-2020年(一期): {early}个项目')
print(f'2021-2023年(二期): {mid}个项目')
print(f'2024-2026年(三期): {recent}个项目')

# 汇总统计
summary = {
    '项目清单_总数': len(df2_stub),
    '建成项目_总数': len(df3),
    '项目资产_总条目': len(df51),
    '资产明细_总数': len(pd.read_excel(file_path, sheet_name=xl.sheet_names[4], header=0)),
    '低效闲置资产': len(df6),
    '待处置资产': len(df9),
}

print('\n' + '='*60)
print('【汇总统计】')
for k, v in summary.items():
    print(f'  {k}: {v}')

# 写出统计JSON
with open(os.path.join(output_dir, '分析统计.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f'\n分析完成. 输出目录: {output_dir}')