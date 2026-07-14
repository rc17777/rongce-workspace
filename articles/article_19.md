# 审计人必备：Python 8 个高频数据分析函数（直接复制）

> **来源：** 数审派 微信公众号  
> **原文链接：** https://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483869&idx=1&sn=9292bd9e5a51df6117c5f6b2813ac16d  
> **抓取时间：** 2026-05-06 20:05:01  
> **抓取方式：** curl + WeChat UA → HTML 提取

---

做审计的人，数据处理是日常。Excel 表格动不动就卡死，VBA 写起来又太麻烦——Python 恰恰填补了这个空缺。

审计工作中把 Python 用熟了之后，数据处理效率至少提升了 3 倍。今天不整虚的，直接给诸位分享我工作中最高频用到的 8 个 Python 函数，代码都是可以直接复制使用的。

### 1. pd.read_excel() + 数据类型优化

基础读取谁都会，但数据类型没指定清楚，后面的分析会处处碰壁：

import pandas as pd****df = pd.read_excel(**    '审计数据.xlsx',**    sheet_name='凭证明细',**    dtype={'凭证号': str, '银行流水号': str, '金额': float},**    parse_dates=['交易日期', '记账日期'],**    na_values=['', 'NA', 'null']**)

dtype 直接定死字段类型，避免 Excel 读取时把数字变成文本、把日期变成浮点数。parse_dates 自动解析日期，na_values 把各种空值形式统一成 NaN。审计数据里"看起来是数实际是文本"的坑，这个可以一次性绕过。

### 2. merge() + 脏数据自动清理

两表合并对不上是审计常态——一方写着"供应商A"，另一方写着"供应商 A"（多个空格）。合并前先做个清洗：

def clean_merge(df_left, df_right, on, how='left', suffix=('_账', '_行')):**    for col in on:**        df_left[col] = df_left[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)**        df_right[col] = df_right[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)**    **    return pd.merge(df_left, df_right, on=on, how=how, suffixes=suffix)****result = clean_merge(df_voucher, df_bank, on=['银行流水号'], how='left')

空格、全角半角、中英文混用这些数据质量问题，合并前不处理干净，对出来的结果会让你怀疑人生。这个函数一步到位。

### 3. groupby() + transform 标记异常值

传统 groupby 返回的是聚合结果，如果想把聚合值写回原表做对比，需要 transform：

df['部门招待费均值'] = df.groupby('部门')['招待费'].transform('mean')**df['部门招待费标准差'] = df.groupby('部门')['招待费'].transform('std')**df['招待费异常度'] = (df['招待费'] - df['部门招待费均值']) / df['部门招待费标准差']****# 超过2个标准差的标记为异常**df['是否异常'] = df['招待费异常度'].apply(lambda x: '异常' if abs(x) > 2 else '正常')

每个部门的招待费均值和异常度直接算出来并回填到原表，行级别的审计判断就这么实现了。比起先 groupby 再 join 回去，transform 少了好几步。

### 4. query() + 变量动态拼接

query 不只是写死条件，配合 @ 引用外部变量才能真正解放生产力：

threshold = 1000000**departments = ['销售部', '市场部']**date_start = '2024-01-01'****high_value = df.query(**    '金额 > @threshold '**    'and 部门 in @departments '**    'and 日期 >= @date_start'**)

例行审计每个月改一次阈值、换一个部门，手动改代码太蠢。变量引用让 query 成为真正的审计工具。

### 5. fillna() + 分组插值 + 条件填充

简单填充均值太粗糙，按组内插值才更合理：

# 按部门分组，用组内均值填充空值**df['招待费'] = df.groupby('部门')['招待费'].transform(**    lambda x: x.fillna(x.mean())**)****# 按时间段填充，用前后值的均值**df['收入'] = df.sort_values('日期').groupby('部门')['收入'].transform(**    lambda x: x.interpolate(method='linear')**)****# 金额为空且供应商为空的，填0；有供应商但金额为空的，填均值**df['金额'] = df.apply(**    lambda row: 0 if pd.isna(row['金额']) and pd.isna(row['供应商']) **    else row['金额'] if pd.isna(row['金额']) **    else row['金额'],**    axis=1**)

时间序列的收入数据用插值比填0科学得多，审计看到的波动才不会失真。

### 6. to_excel() + 样式与条件格式

导出不是只要数据，审计报告需要一眼看出异常：

from openpyxl import load_workbook**from openpyxl.styles import PatternFill, Font****with pd.ExcelWriter('审计分析结果.xlsx', engine='openpyxl') as writer:**    df_result.to_excel(writer, sheet_name='费用明细', index=False)**    **    workbook = writer.book**    worksheet = writer.sheets['费用明细']**    **    # 超过阈值的标红**    red_fill = PatternFill(start_color='FF0000', end_color='FF0000', fill_type='solid')**    for row in range(2, len(df_result) + 2):**        amount = worksheet.cell(row=row, column=5).value**        if amount and amount > 500000:**            worksheet.cell(row=row, column=5).fill = red_fill**            worksheet.cell(row=row, column=5).font = Font(color='FFFFFF')

审计报告交出去，异常值一眼就能看到，这才是有效的数据呈现。

### 7. groupby().filter() + 复杂条件筛选组

有时候不是筛选行，而是筛选"哪些组符合条件"：

# 筛选出招待费总额超过100万的部门**high_expense_depts = df.groupby('部门').filter(**    lambda x: x['招待费'].sum() > 1000000**)****# 筛选出金额标准差过大的月份（可能存在异常波动）**volatile_months = df.groupby('月份').filter(**    lambda x: x['金额'].std() > x['金额'].mean() * 0.5**)****# 筛选出空值占比超过10%的字段**dirty_cols = df.columns[df.isnull().mean() > 0.1].tolist()

过滤组级别的异常比逐行筛选高效得多，审计直觉先锁定可疑群体，再细查组内记录。

### 8. agg() + 多层级聚合 + named agg

单层统计已经不够用了，named agg 让你输出清晰的命名：

audit_summary = df.groupby('部门').agg(**    招待费总额=('招待费', 'sum'),**    招待费均值=('招待费', 'mean'),**    招待费最大值=('招待费', 'max'),**    交易笔数=('凭证号', 'count'),**    异常笔数=('是否异常', lambda x: (x == '异常').sum()),**    供应商数量=('供应商', 'nunique')**).round(2)****audit_summary['异常率'] = (audit_summary['异常笔数'] / audit_summary['交易笔数'] * 100).round(2)

直接输出带列名的统计表，异常率一并算出来，往审计报告里一贴就能用。

这 8 个函数覆盖了审计数据处理的完整链路：读入、清洗、筛选、分组、合并、输出。相比基础版本，这些进阶技巧能处理更复杂的数据质量问题、输出更专业的审计报告。

说到底，Python 提升的是数据处理的颗粒度和自动化程度。基础函数能跑出结果，进阶函数能跑出经得起推敲的结果。

代码就在这儿了，直接复制去试吧。有问题欢迎留言交流。

如果觉得文章可以的话，欢迎点赞+关注哦，持续为你带来干货！
