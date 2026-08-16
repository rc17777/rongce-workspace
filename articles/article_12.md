# 审计人员数字技能修炼手册 | 进阶篇（一）：Python数据分析

> **来源：** http://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483832&idx=1&sn=9dd48593e528f2fe23f22cd68d9cc8f5&chksm=c4c26382f3b5ea94296e5421a75dffdb17522e5737287c5c218fc8ffe81544fd00164cf73948#rd
> **抓取时间：** 2026-05-06 12:12:38 +08:00 (Asia/Shanghai)
> **公众号：** 数审派

---

各位审计同仁，大家好！

经过入门篇的学习，相信大家已经掌握了Excel高级功能、SQL基础和Python爬虫技术。从今天开始，我们进入进阶篇**的学习。

进阶篇的第一站，我们来学习Python数据分析**。

## 一、为什么审计人员要学Python？

### 1.1 Python在审计领域的应用

Python已经成为数据分析领域最流行的编程语言之一，在审计领域也有广泛应用：
| **| 应用领域 | 具体场景 
| 财务分析 | 自动化财务数据处理和分析 
| 异常检测 | 使用算法自动识别异常交易 
| 文档处理 | 自动读取和分析合同、发票 
| 报告生成 | 自动生成审计报告 
| 可视化 | 数据可视化展示 

### 1.2 Python vs Excel/SQL

| **| 特性 | Excel | SQL | Python 
| 适合数据量 | 万级 | 亿级 | 亿级以上 
| 学习门槛 | 低 | 中 | 中高 
| 自动化程度 | 需VBA | 需脚本 | 高度自动化 
| 高级分析 | 困难 | 困难 | 容易 
| 团队协作 | 一般 | 优秀 | 优秀 

### 1.3 Python的优势

- 1. 功能强大**：可以做从简单计算到机器学习的各种分析
- 2. 生态丰富**：有大量专门为数据分析开发的库
- 3. 开源免费**：社区活跃，资源丰富
- 4. 可复用**：一次编写，多次运行
- 5. 跨平台**：Windows、Mac、Linux都能运行

## 二、环境准备

### 2.1 安装Anaconda

对于数据分析，我们推荐安装Anaconda**（一个Python发行版）：
- 1. 访问 https://www.anaconda.com/download
- 2. 下载Python 3.x版本的安装包
- 3. 运行安装程序，按提示完成安装

Anaconda已经包含了：
- • Python解释器
- • Jupyter Notebook（交互式编程环境）
- • 常用的数据分析库

### 2.2 常用数据分析库

| **| 库名 | 用途 | 重要性 
| Pandas** | 数据处理和分析 | ⭐⭐⭐ 
| NumPy** | 数值计算 | ⭐⭐⭐ 
| Matplotlib** | 数据可视化 | ⭐⭐⭐ 
| SciPy** | 科学计算 | ⭐⭐ 
| Scikit-learn** | 机器学习 | ⭐⭐ 

## 三、Pandas入门

Pandas是Python数据分析的核心库，专门用于数据处理和分析。

### 3.1 Pandas数据结构

Pandas有两种主要数据结构：Series**和DataFrame**。

Series**：一维数据结构，类似Excel中的一列

import pandas as pd# 创建Seriess = pd.Series([1000, 2000, 3000, 4000])print(s)`
```

DataFrame**：二维数据结构，类似Excel中的一张表

# 创建DataFramedata = {    '科目代码': ['1001', '1002', '1122'],    '科目名称': ['库存现金', '银行存款', '应收账款'],    '期末余额': [5000, 800000, 200000]}df = pd.DataFrame(data)print(df)`
```

### 3.2 读取数据

Pandas支持读取多种格式的数据：

# 读取Excel文件df = pd.read_excel('科目余额表.xlsx')# 读取CSV文件df = pd.read_csv('银行流水.csv')# 读取SQL数据库（需要SQLAlchemy）from sqlalchemy import create_engineengine = create_engine('mysql+pymysql://user:pass@localhost/audit_db')df = pd.read_sql('SELECT * FROM GL_BALANCE', engine)`
```

### 3.3 数据查看

# 查看前5行print(df.head())# 查看后5行print(df.tail())# 查看数据基本信息print(df.info())# 查看数值列的统计信息print(df.describe())# 查看列名print(df.columns.tolist())# 查看数据维度print(df.shape)  # 输出：(行数, 列数)`
```

### 3.4 数据筛选

# 选择单列df['科目名称']# 选择多列df[['科目代码', '科目名称', '期末余额']]# 条件筛选：筛选余额大于100万的科目df[df['期末余额'] > 1000000]# 多条件筛选：资产类科目且余额大于100万df[(df['科目代码'].str.startswith('1')) & (df['期末余额'] > 1000000)]`
```

### 3.5 数据排序

# 按余额降序排列df.sort_values('期末余额', ascending=False)# 按多个字段排序df.sort_values(['科目大类', '期末余额'], ascending=[True, False])`
```

### 3.6 数据统计

# 单列统计df['期末余额'].sum()    # 求和df['期末余额'].mean()   # 平均值df['期末余额'].median() # 中位数df['期末余额'].std()    # 标准差df['期末余额'].min()    # 最小值df['期末余额'].max()    # 最大值# 分组统计df.groupby('科目大类')['期末余额'].sum()  # 按科目大类统计余额合计# 分组统计（多指标）df.groupby('科目大类').agg({    '期末余额': ['sum', 'mean', 'count'],    '借方发生额': ['sum', 'max']})`
```

## 四、实战案例

### 案例一：银行流水分析

import pandas as pd# 读取银行流水数据df = pd.read_excel('银行流水_2024.xlsx')# 1. 数据清洗# 去除空行df = df.dropna(subset=['交易日期', '金额'])# 统一日期格式df['交易日期'] = pd.to_datetime(df['交易日期'])# 清理金额字段（去除千分位和货币符号）df['金额'] = df['金额'].astype(str).str.replace(',', '').str.replace('¥', '').astype(float)# 2. 数据分析# 按月份统计df['月份'] = df['交易日期'].dt.to_period('M')monthly_summary = df.groupby('月份')['金额'].agg(['sum', 'count', 'mean'])# 3. 识别大额交易（超过50万）large_transactions = df[df['金额'].abs() > 500000]# 4. 查找可疑模式：同一金额多次出现amount_counts = df['金额'].value_counts()suspicious_amounts = amount_counts[amount_counts > 3]  # 同一金额出现超过3次print(f"月度汇总：\n{monthly_summary}")print(f"\n大额交易数量：{len(large_transactions)}")print(f"\n可疑金额（重复出现超过3次）：{suspicious_amounts}")`
```

### 案例二：费用异常检测

import pandas as pdimport numpy as np# 读取费用数据df = pd.read_excel('管理费用明细.xlsx')# 计算统计指标mean = df['金额'].mean()std = df['金额'].std()# 使用2倍标准差法识别异常df['Z分数'] = (df['金额'] - mean) / stddf['是否异常'] = df['Z分数'].abs() > 2# 查看异常费用anomalies = df[df['是否异常'] == True]print(f"平均金额：{mean:,.2f}")print(f"标准差：{std:,.2f}")print(f"\n发现 {len(anomalies)} 笔异常费用：")print(anomalies[['日期', '费用项目', '金额', 'Z分数']])`
```

### 案例三：应收账款账龄分析

import pandas as pdfrom datetime import datetime# 读取应收账款数据df = pd.read_excel('应收账款明细.xlsx')# 计算账龄today = pd.to_datetime('2024-12-31')df['账龄天数'] = (today - pd.to_datetime(df['到期日期'])).dt.days# 账龄分组def age_group(days):    if days < 0:        return '未到期'    elif days <= 30:        return '0-30天'    elif days <= 60:        return '31-60天'    elif days <= 90:        return '61-90天'    else:        return '90天以上'df['账龄分组'] = df['账龄天数'].apply(age_group)# 按账龄分组汇总aging_summary = df.groupby('账龄分组').agg({    '应收金额': ['sum', 'count'],    '客户名称': 'nunique'}).round(2)# 计算各账龄区间占比total = df['应收金额'].sum()aging_summary['占比'] = (aging_summary[('应收金额', 'sum')] / total * 100).round(2)print("应收账款账龄分析表")print("="*50)print(aging_summary)print(f"\n应收账款总额：{total:,.2f}")print(f"平均账龄：{df['账龄天数'].mean():.1f}天")`
```

## 五、NumPy基础

NumPy是Python数值计算的基础库，提供了高效的数组操作功能。

### 5.1 创建数组

import numpy as np# 创建一维数组arr1 = np.array([1, 2, 3, 4, 5])# 创建二维数组（矩阵）arr2 = np.array([[1, 2, 3], [4, 5, 6]])# 创建特殊数组zeros = np.zeros((3, 4))  # 3行4列的零矩阵ones = np.ones((2, 3))    # 2行3列的1矩阵range_arr = np.arange(0, 10, 2)  # 0到10，步长2`
```

### 5.2 数组运算

arr = np.array([1, 2, 3, 4, 5])# 基础运算print(arr * 2)      # 每个元素乘2print(arr + 10)     # 每个元素加10print(arr ** 2)     # 每个元素平方# 统计运算print(np.sum(arr))      # 求和print(np.mean(arr))     # 平均值print(np.std(arr))      # 标准差print(np.max(arr))      # 最大值print(np.min(arr))      # 最小值`
```

### 5.3 在审计中的应用

import numpy as np# 假设我们有1000笔交易金额transactions = np.random.lognormal(10, 1, 1000)# 计算置信区间（95%）mean = np.mean(transactions)std = np.std(transactions)ci_lower = mean - 1.96 * stdci_upper = mean + 1.96 * stdprint(f"平均交易金额：{mean:,.2f}")print(f"95%置信区间：[{ci_lower:,.2f}, {ci_upper:,.2f}]")# 识别异常值（超出置信区间）outliers = transactions[(transactions < ci_lower) | (transactions > ci_upper)]print(f"\n异常交易数量：{len(outliers)}")`
```

## 六、Matplotlib数据可视化

Matplotlib是Python最常用的数据可视化库。

### 6.1 基本图表

import matplotlib.pyplot as pltimport pandas as pd# 设置中文字体plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']plt.rcParams['axes.unicode_minus'] = False# 1. 柱状图：各月费用对比months = ['1月', '2月', '3月', '4月', '5月']expenses = [120, 150, 130, 180, 160]plt.figure(figsize=(10, 6))plt.bar(months, expenses, color='steelblue')plt.title('2024年各月管理费用', fontsize=14)plt.xlabel('月份', fontsize=12)plt.ylabel('金额（万元）', fontsize=12)plt.show()# 2. 折线图：收入趋势revenue = [850, 780, 920, 1100, 980]plt.figure(figsize=(10, 6))plt.plot(months, revenue, marker='o', linewidth=2, color='green')plt.title('2024年各月营业收入', fontsize=14)plt.xlabel('月份', fontsize=12)plt.ylabel('金额（万元）', fontsize=12)plt.grid(True)plt.show()# 3. 饼图：费用结构expense_items = ['人力成本', '租金', '营销', '研发', '其他']expense_values = [40, 20, 15, 15, 10]plt.figure(figsize=(8, 8))plt.pie(expense_values, labels=expense_items, autopct='%1.1f%%', startangle=90)plt.title('管理费用结构', fontsize=14)plt.show()`
```

### 6.2 审计分析图表

import matplotlib.pyplot as pltimport pandas as pdimport numpy as np# 账龄分析图aging_data = pd.DataFrame({    '账龄区间': ['0-30天', '31-60天', '61-90天', '90天以上'],    '金额': [250, 180, 120, 350],    '占比': [25, 18, 12, 35]})fig, axes = plt.subplots(1, 2, figsize=(14, 5))# 左图：金额柱状图colors = ['green', 'yellow', 'orange', 'red']axes[0].bar(aging_data['账龄区间'], aging_data['金额'], color=colors)axes[0].set_title('应收账款账龄分析', fontsize=14)axes[0].set_xlabel('账龄区间')axes[0].set_ylabel('金额（万元）')# 右图：占比饼图axes[1].pie(aging_data['占比'], labels=aging_data['账龄区间'], autopct='%1.1f%%', colors=colors)axes[1].set_title('账龄占比分布', fontsize=14)plt.tight_layout()plt.show()`
```

## 七、数据清洗实战

数据清洗是数据分析中最耗时的环节，通常占用80%的时间。

### 7.1 常见数据问题及处理

import pandas as pdimport numpy as np# 1. 缺失值处理df = pd.DataFrame({    '日期': ['2024-01-01', '2024-01-02', None, '2024-01-04'],    '金额': [1000, None, 3000, 4000],    '备注': ['正常', '正常', '', '异常']})# 查看缺失值print(df.isnull().sum())# 处理缺失值df['金额'].fillna(0, inplace=True)  # 用0填充# 或 df['金额'].fillna(df['金额'].mean(), inplace=True)  # 用均值填充df.dropna(subset=['日期'], inplace=True)  # 删除日期为空的行df['备注'].replace('', '无', inplace=True)  # 空字符串替换为"无"# 2. 重复值处理df.drop_duplicates(inplace=True)  # 删除重复行# 3. 异常值处理# 方法一：Z分数法df['Z分数'] = (df['金额'] - df['金额'].mean()) / df['金额'].std()df = df[df['Z分数'].abs() < 3]  # 剔除3倍标准差以外的异常值# 方法二：IQR法Q1 = df['金额'].quantile(0.25)Q3 = df['金额'].quantile(0.75)IQR = Q3 - Q1lower_bound = Q1 - 1.5 * IQRupper_bound = Q3 + 1.5 * IQRdf = df[(df['金额'] >= lower_bound) & (df['金额'] <= upper_bound)]print(df)`
```

### 7.2 数据类型转换

# 日期转换df['日期'] = pd.to_datetime(df['日期'])# 字符串处理df['金额'] = df['金额'].astype(str).str.replace(',', '').astype(float)# 分类变量编码df['类别'] = df['类别'].astype('category').cat.codes`
```

## 八、学习路径建议

| **| 阶段 | 学习内容 | 建议时间 
| 第一周 | Python基础语法、Jupyter使用 | 1周 
| 第二周 | Pandas数据读写、数据查看 | 1周 
| 第三周 | 数据筛选、排序、分组 | 1周 
| 第四周 | 数据清洗实战 | 1周 
| 第五周 | NumPy数值计算 | 1周 
| 第六周 | Matplotlib可视化 | 1周 

## 九、实践作业

- 1. 安装Anaconda**：完成Python环境安装
- 2. 完成Jupyter入门练习**：

- • 熟悉Jupyter Notebook的基本操作
- • 运行第一个"Hello World"程序

- 3. Pandas练习**：

- • 找一份Excel数据文件
- • 使用Pandas读取并完成以下操作：

- • 查看数据基本信息
- • 按条件筛选数据
- • 进行分组统计
- • 生成简单的可视化图表

## 总结

今天我们学习了Python数据分析的基础知识：
| **| 库 | 核心功能 | 审计应用 
| Pandas | 数据处理和分析 | 财务数据清洗、分析 
| NumPy | 数值计算 | 统计计算、异常检测 
| Matplotlib | 数据可视化 | 图表生成、趋势展示 

Python是审计人员进阶的必备技能。它可以帮助你：
- • 处理Excel无法胜任的大数据量
- • 自动化重复性的数据工作
- • 进行更高级的统计分析
- • 为后续学习机器学习打下基础

下期预告**：我们将学习Power BI数据可视化**——一款强大的商业智能工具，帮助你创建专业的数据可视化报表。敬请期待！

如果觉得有帮助，欢迎转发给需要的同事！
