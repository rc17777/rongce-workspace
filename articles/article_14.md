# 审计人员数字技能修炼手册 | 进阶篇（三）：统计学基础——用于异常检测

> **来源：** http://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483843&idx=1&sn=1f98f0b4e5b6c597419b8e6168474843&chksm=c4c263f9f3b5eaef1fc5d68e8fc790bde6b124ee69da37d88d72f8fb30f7528f2fbb9a68f503#rd
> **抓取时间：** 2026-05-06 12:12:38 +08:00 (Asia/Shanghai)
> **公众号：** 数审派

---

各位审计同仁，大家好！

上期我们完成了Power BI数据可视化学习。今天我们继续进阶篇第三站——统计学基础**。

很多审计人员可能一听到"统计学"就头疼，觉得太理论、太抽象。但实际上，统计学是审计异常检测的核心基础。掌握基本的统计概念和方法，你就能用数据驱动的方式发现审计风险，而不是仅凭经验和直觉。

## 一、为什么审计人员要学统计学？

### 1.1 统计学在审计中的应用

| **| 应用领域 | 具体场景 
| 异常检测 | 识别偏离正常模式的交易 
| 抽样方法 | 确定审计样本量 
| 区间估计 | 推断总体金额 
| 趋势分析 | 预测未来财务数据 
| 风险评估 | 量化控制风险 

### 1.2 从"经验审计"到"数据驱动审计"

传统审计主要依赖审计人员的经验判断：
- • "这家公司收入增长30%，好像有点快..."
- • "这笔招待费20万，感觉有点高..."

统计学帮助我们量化判断标准**：
- • "收入增长30%，超出行业平均水平2个标准差"
- • "招待费20万，超过99%的同类企业水平"

### 1.3 统计学 vs 职业判断

统计学不是要取代审计人员的职业判断，而是提供客观的量化依据**。

职业判断 + 统计方法 = 更科学的审计结论`
```

## 二、描述性统计

描述性统计是对数据基本特征的概括和总结。

### 2.1 中心趋势度量

均值（Mean）**：数据的算术平均值

import numpy as npexpenses = [100, 150, 120, 180, 200, 130, 160]mean_expense = np.mean(expenses)print(f"平均费用：{mean_expense:.2f}")  # 输出：148.57`
```

中位数（Median）**：数据排序后位于中间位置的值

median_expense = np.median(expenses)print(f"中位数费用：{median_expense:.2f}")`
```

均值 vs 中位数的区别**：
| **| 指标 | 均值 | 中位数 
| 计算方式 | 所有值相加除以个数 | 排序后中间的值 
| 对极端值敏感度 | 敏感（会被极端值拉偏） | 不敏感 
| 适用场景 | 数据分布较均匀 | 数据存在偏态或极端值 

审计应用**：

在审计中，如果收入数据的均值远大于中位数，说明数据呈右偏态（少数大额交易拉高了均值）。这种情况下，中位数可能更能反映"典型"水平。

### 2.2 离散程度度量

方差（Variance）**：各数据与均值的差的平方的平均值

variance = np.var(expenses)print(f"方差：{variance:.2f}")`
```

标准差（Standard Deviation）**：方差的平方根，与原数据单位相同

std = np.std(expenses)print(f"标准差：{std:.2f}")`
```

标准差的意义**：

68%的数据落在 [均值-1个标准差, 均值+1个标准差] 范围内95%的数据落在 [均值-2个标准差, 均值+2个标准差] 范围内99.7%的数据落在 [均值-3个标准差, 均值+3个标准差] 范围内`
```

审计应用**：

如果某笔交易金额超出均值3个标准差，说明这是一个极不寻常的值，需要重点关注。

### 2.3 分位数

四分位数**：将数据分成四等份的三个点

q1 = np.percentile(expenses, 25)   # 第一四分位数（25%分位）q2 = np.percentile(expenses, 50)   # 第二四分位数（中位数）q3 = np.percentile(expenses, 75)   # 第三四分位数（75%分位）iqr = q3 - q1                        # 四分位距（IQR）print(f"Q1: {q1}, Q2: {q2}, Q3: {q3}")print(f"IQR: {iqr}")`
```

箱线图**：

箱线图是展示数据分布的经典可视化方式：

    ●异常值     |─────┤  ← 上边缘（Q3 + 1.5×IQR）│    │─────┤  ← Q3│█████│ ← Q3到Q2的矩形（包含50%的数据）│█████││█████│ ← Q2（中位数）│    │ ← Q1到Q2的矩形─────┤  ← Q1│    │─────┤  ← 下边缘（Q1 - 1.5×IQR）    ●异常值`
```

## 三、概率分布

### 3.1 正态分布

正态分布是统计学中最重要的分布，也叫"高斯分布"。

特点**：
- • 呈钟形曲线
- • 均值、中位数、众数三者相等
- • 关于均值对称

审计应用**：

在审计中，很多财务数据（如_transaction amounts_）近似服从正态分布，这为异常检测提供了理论基础。

import numpy as npimport matplotlib.pyplot as plt# 模拟正态分布数据np.random.seed(42)data = np.random.normal(loc=100, scale=20, size=1000)# 绘制直方图plt.hist(data, bins=30, density=True, alpha=0.7, color='steelblue')plt.xlabel('金额')plt.ylabel('概率密度')plt.title('正态分布示例')plt.show()`
```

### 3.2 泊松分布

泊松分布用于描述单位时间内随机事件发生次数的分布。

审计应用**：
- • 每天发生的交易笔数
- • 每月发生的差错次数
- • 每年发现的违规次数

from scipy import stats# 假设每天平均发生10笔交易lambda_val = 10# 计算某天发生15笔交易的概率prob_15 = stats.poisson.pmf(15, lambda_val)print(f"某天发生15笔交易的概率：{prob_15:.4f}")# 计算某天发生少于5笔交易的概率prob_less_5 = stats.poisson.cdf(4, lambda_val)print(f"某天发生少于5笔交易的概率：{prob_less_5:.4f}")`
```

### 3.3 二项分布

二项分布用于描述n次独立试验中成功次数的分布。

审计应用**：
- • n笔交易中发现k笔错误的概率
- • 内部控制有效/无效的检验

## 四、异常检测方法

这是统计学的核心应用场景。

### 4.1 Z分数法（标准分数法）

原理**：计算每个数据点与均值的距离（以标准差为单位）

def z_score_analysis(data, threshold=2):    """    Z分数异常检测    threshold: 超过此阈值判定为异常（默认2倍标准差）    """    mean = np.mean(data)    std = np.std(data)    # 计算每个数据点的Z分数    z_scores = [(x - mean) / std for x in data]    # 标记异常值    anomalies = []    for i, z in enumerate(z_scores):        if abs(z) > threshold:            anomalies.append({                'index': i,                'value': data[i],                'z_score': z,                'severity': '高' if abs(z) > 3 else '中'            })    return anomalies# 示例：检测异常费用expenses = [100, 150, 120, 180, 200, 130, 160, 500, 140, 155]anomalies = z_score_analysis(expenses, threshold=2)print("异常费用：", anomalies)`
```

阈值选择**：
| **| Z分数阈值 | 异常比例（理论） | 实际应用建议 
| 2 | ~5% | 宽松标准，可能漏报 
| 2.5 | ~1.2% | 中等标准 
| 3 | ~0.3% | 严格标准，可能误报较少 

### 4.2 IQR法（四分位距法）

原理**：数据超出Q1-1.5×IQR或Q3+1.5×IQR即为异常

def iqr_anomaly_detection(data, multiplier=1.5):    """    IQR异常检测    multiplier: IQR的倍数（默认1.5）    """    q1 = np.percentile(data, 25)    q3 = np.percentile(data, 75)    iqr = q3 - q1    lower_bound = q1 - multiplier * iqr    upper_bound = q3 + multiplier * iqr    anomalies = []    for i, value in enumerate(data):        if value < lower_bound or value > upper_bound:            anomalies.append({                'index': i,                'value': value,                'bound': '低于下界' if value < lower_bound else '高于上界',                'bounds': (lower_bound, upper_bound)            })    return anomalies, (lower_bound, upper_bound)expenses = [100, 150, 120, 180, 200, 130, 160, 500, 140, 155]anomalies, bounds = iqr_anomaly_detection(expenses)print(f"异常边界：{bounds}")print("异常费用：", anomalies)`
```

两种方法的对比**：
| **| 方法 | 优点 | 缺点 | 适用场景 
| Z分数法 | 计算简单，结果直观 | 对极端值敏感 | 数据近似正态分布 
| IQR法 | 对极端值不敏感 | 可能漏检轻度异常 | 数据存在明显偏态 

### 4.3 Benford定律

Benford定律**：在自然产生的数据中，数字1-9作为首字母出现的概率是不同的。

import matplotlib.pyplot as pddef benford_expected():    """Benford定律预期分布"""    digits = range(1, 10)    expected = [np.log10(1 + 1/d) for d in digits]    return expecteddef benford_analysis(data):    """分析数据首位数字分布"""    # 提取首位数字    first_digits = []    for num in data:        if num > 0:            first_digit = int(str(num).lstrip('0').lstrip('.'))[0]            first_digits.append(first_digit)    # 计算分布    observed = [first_digits.count(d) for d in range(1, 10)]    total = len(first_digits)    observed_pct = [c / total * 100 for c in observed]    return observed_pct# 示例transactions = [1234, 5678, 9123, 3456, 7890, 2345, 6789, 123, 4567, 8901]observed = benford_analysis(transactions)expected = benford_expected()print("数字\t预期\t实际\t偏差")for i in range(9):    print(f"{i+1}\t{expected[i]:.2f}%\t{observed[i]:.2f}%\t{observed[i]-expected[i]:+.2f}%")`
```

审计应用场景**：
| **| 应用领域 | 说明 
| 收入造假检测 | 人为编造的数据往往不符合Benford定律 
| 费用虚增检测 | 员工可能虚报费用，金额分布异常 
| 银行流水分析 | 虚假交易难以完美模拟自然分布 

## 五、抽样方法

统计学在审计抽样中的应用同样重要。

### 5.1 随机抽样

每个样本被选中的概率相等。

import randomdef simple_random_sampling(population, sample_size):    """简单随机抽样"""    return random.sample(population, sample_size)# 示例：从1000笔交易中抽取50笔population = list(range(1, 1001))sample = simple_random_sampling(population, 50)print(f"抽中的交易编号：{sample}")`
```

### 5.2 分层抽样

将总体分成不同层次（层），在各层内分别抽样。

def stratified_sampling(data, stratify_col, sample_size):    """    分层抽样    data: DataFrame    stratify_col: 分层依据的列名    sample_size: 总样本量    """    strata = data.groupby(stratify_col)    total_size = len(data)    samples = []    for name, group in strata:        # 按各层占总体的比例分配样本量        stratum_size = int(len(group) / total_size * sample_size)        stratum_sample = group.sample(n=min(stratum_size, len(group)))        samples.append(stratum_sample)    return pd.concat(samples)# 示例：按部门分层抽样# sampled = stratified_sampling(expense_df, '部门', 50)`
```

### 5.3 货币单位抽样（PPS）

金额越大的项目被抽中的概率越高。

def pps_sampling(data, amount_col, sample_size):    """    货币单位抽样（Probability Proportional to Size）    金额大的项目更容易被抽中    """    total_amount = data[amount_col].sum()    data['抽中概率'] = data[amount_col] / total_amount    # 计算累计概率    data['累计概率'] = data['抽中概率'].cumsum()    # 随机选择    random_selections = [random.random() for _ in range(sample_size)]    selected = []    for rand_val in random_selections:        for idx, row in data.iterrows():            if row['累计概率'] >= rand_val:                selected.append(idx)                break    return data.loc[selected]# 示例：从交易中选择最可能发现错误的样本# high_value_sample = pps_sampling(transactions_df, '金额', 50)`
```

## 六、置信区间与假设检验

### 6.1 置信区间

置信区间是对总体参数的区间估计。

from scipy import statsdef confidence_interval(data, confidence=0.95):    """    计算均值的置信区间    confidence: 置信水平（默认95%）    """    n = len(data)    mean = np.mean(data)    std_err = stats.sem(data)  # 标准误差    # t分布（样本量小时使用）    ci = stats.t.interval(confidence, n-1, loc=mean, scale=std_err)    return ci# 示例：估计总体平均费用expenses = [100, 150, 120, 180, 200, 130, 160, 140, 155, 145]ci = confidence_interval(expenses, 0.95)print(f"95%置信区间：[{ci[0]:.2f}, {ci[1]:.2f}]")`
```

### 6.2 假设检验

假设检验用于判断样本数据是否支持某个假设。

场景**：审计人员怀疑某部门的平均费用高于公司平均水平（100元）

def one_sample_t_test(data, pop_mean):    """    单样本t检验    检验样本均值是否显著不同于总体均值    """    result = stats.ttest_1samp(data, pop_mean)    return result# 示例：检验部门平均费用是否显著高于100expenses = [110, 150, 120, 180, 105, 130, 160, 140, 155, 145]t_stat, p_value = one_sample_t_test(expenses, 100)print(f"t统计量：{t_stat:.4f}")print(f"p值：{p_value:.4f}")# 判断（通常以0.05为显著性水平）if p_value < 0.05:    print("结论：有统计显著证据表明该部门平均费用高于公司平均水平")else:    print("结论：没有足够证据表明该部门平均费用异常")`
```

## 七、实战案例

### 案例一：银行流水异常检测

import pandas as pdimport numpy as npfrom scipy import stats# 读取银行流水数据# df = pd.read_excel('银行流水_2024.xlsx')# 模拟数据np.random.seed(42)df = pd.DataFrame({    '交易日期': pd.date_range('2024-01-01', periods=1000),    '金额': np.random.normal(10000, 5000, 1000)})# 添加几笔异常值df.loc[100, '金额'] = 500000df.loc[200, '金额'] = -100000df.loc[300, '金额'] = 800000# 1. Z分数法检测df['Z分数'] = (df['金额'] - df['金额'].mean()) / df['金额'].std()df['异常标记_Z'] = abs(df['Z分数']) > 2# 2. IQR法检测Q1 = df['金额'].quantile(0.25)Q3 = df['金额'].quantile(0.75)IQR = Q3 - Q1lower = Q1 - 1.5 * IQRupper = Q3 + 1.5 * IQRdf['异常标记_IQR'] = (df['金额'] < lower) | (df['金额'] > upper)# 3. 合并结果df['异常标记'] = df['异常标记_Z'] | df['异常标记_IQR']# 查看异常记录anomalies = df[df['异常标记']]print(f"检测到 {len(anomalies)} 笔异常交易：")print(anomalies[['交易日期', '金额', 'Z分数']])`
```

### 案例二：收入真实性验证（Benford定律）

def benford_test(data):    """    使用Benford定律检验数据真实性    返回卡方检验结果    """    # 计算实际首位数字分布    first_digits = []    for num in data:        if num > 0:            first_digit = int(str(abs(num)).lstrip('0').lstrip('.'))[0]            first_digits.append(first_digit)    # 统计各数字出现次数    observed = [first_digits.count(d) for d in range(1, 10)]    total = len(first_digits)    # 计算预期频率（Benford定律）    expected = [(np.log10(1 + 1/d) * total) for d in range(1, 10)]    # 卡方检验    chi2, p_value = stats.chisquare(observed, expected)    return chi2, p_value, observed, expected# 示例：检验收入数据revenue = [123456, 78901, 23456, 345678, 45678, 567890, 6789, 78901]chi2, p_value, observed, expected = benford_test(revenue)print(f"卡方统计量：{chi2:.4f}")print(f"p值：{p_value:.4f}")if p_value < 0.05:    print("警告：数据分布显著偏离Benford定律，可能存在异常！")else:    print("数据分布符合Benford定律，未发现明显异常")`
```

### 案例三：费用趋势异常检测

import pandas as pdimport numpy as np# 模拟月度费用数据np.random.seed(42)expenses = pd.DataFrame({    '月份': pd.date_range('2024-01', periods=24, freq='M'),    '费用': [100, 102, 98, 105, 103, 101, 99, 104, 106, 102,             150, 200, 105, 103, 101, 104, 102, 99, 98, 105, 103, 101, 104, 102]  # 11-12月异常高})# 计算滚动均值和标准差expenses['滚动均值'] = expenses['费用'].rolling(window=6).mean()expenses['滚动标准差'] = expenses['费用'].rolling(window=6).std()# 计算Z分数expenses['Z分数'] = (expenses['费用'] - expenses['滚动均值']) / expenses['滚动标准差']# 标记异常expenses['异常'] = abs(expenses['Z分数']) > 2print("趋势分析结果：")print(expenses[['月份', '费用', '滚动均值', 'Z分数', '异常']])print("\n检测到的异常月份：")print(expenses[expenses['异常']][['月份', '费用', 'Z分数']])`
```

## 八、学习资源

| **| 资源类型 | 推荐 
| 书籍 | 《统计学，关乎数据解释的艺术》《深入浅出统计学》 
| 在线课程 | Khan Academy统计学基础 
| 工具 | Python (SciPy, StatsModels)、R语言 
| 实践 | 在实际审计项目中应用统计方法 

## 九、实践作业

- 1. 理解基本概念**：理解均值、中位数、标准差、置信区间的含义
- 2. Python练习**：

- • 使用NumPy和SciPy对一组模拟数据进行描述性统计分析
- • 实现Z分数法和IQR法进行异常检测

- 3. 应用实践**：

- • 找一份银行流水或费用数据
- • 应用至少两种统计方法进行异常检测
- • 分析检测结果的合理性

## 总结

今天我们学习了统计学基础知识：
| **| 知识点 | 说明 | 审计应用 
| 描述性统计 | 均值、中位数、标准差 | 数据概况分析 
| 概率分布 | 正态分布、泊松分布 | 建模基础 
| Z分数法 | 标准差距离法 | 异常值检测 
| IQR法 | 四分位距法 | 稳健异常检测 
| Benford定律 | 首位数字分布规律 | 数据真实性验证 
| 假设检验 | 统计显著性检验 | 审计结论验证 
| 抽样方法 | 随机、分层、PPS | 审计抽样 

统计学是审计人员从"经验驱动"走向"数据驱动"的关键桥梁。掌握基本的统计方法，你就能更科学、更客观地识别审计风险。

下期预告**：我们将学习数据架构与数据治理**——进阶篇的最后一站！了解企业数据的组织方式和管理框架，为高阶篇打下基础。敬请期待！

如果觉得有帮助，欢迎转发给需要的同事！
