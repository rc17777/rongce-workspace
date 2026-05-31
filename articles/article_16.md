# 审计人员数字技能修炼手册 | 高阶篇（一）：机器学习基础——异常检测算法

> **来源：** 数审派 微信公众号  
> **原文链接：** https://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483853&idx=1&sn=96ad54a6f895863cc7fc2839abdd5da2  
> **抓取时间：** 2026-05-06 20:05:00  
> **抓取方式：** curl + WeChat UA → HTML 提取

---

各位审计同仁，大家好！

经过入门篇和进阶篇的学习，相信大家已经建立了扎实的数据分析基础。从今天开始，我们进入**高阶篇**的学习。

高阶篇将带你进入人工智能和智能化审计的领域。第一站，我们来学习**机器学习基础——异常检测算法**。

## 一、机器学习概述

### 1.1 什么是机器学习？

机器学习是人工智能的一个分支，它让计算机能够"从数据中学习"，而不需要明确编程。

**传统编程 vs 机器学习**：

传统编程：**  输入数据 + 规则 → 输出结果****机器学习：**  输入数据 + 结果 → 学习规则

### 1.2 机器学习的三种类型

类型
说明
审计应用场景**监督学习**
有标签的学习（输入有正确答案）
发票分类、欺诈识别**无监督学习**
无标签的学习（自行发现模式）
异常检测、客户分群**半监督学习**
部分有标签
大量无标签数据 + 少量标注数据

### 1.3 审计中的机器学习应用

应用领域
具体场景
异常检测
自动识别异常交易
欺诈检测
识别可能的舞弊行为
文本分类
合同风险分类、审计意见判断
预测分析
财务风险预测

## 二、异常检测基础

### 2.1 什么是异常？

异常（Anomaly）是指与大多数数据显著不同的数据点。

**异常的三种类型**：

类型
说明
审计示例**点异常**
单个数据点异常
某笔100万的餐费**上下文异常**
在特定上下文下异常
周末发生的巨额转账**集合异常**
一组数据点共同构成异常
连续多笔略低于审批权限的交易

### 2.2 异常检测方法分类

异常检测方法**├── 传统统计方法**│   ├── Z分数法**│   ├── IQR法**│   └── Benford定律**├── 机器学习方法**│   ├── 孤立森林 (Isolation Forest)**│   ├── One-Class SVM**│   ├── Local Outlier Factor (LOF)**│   └── DBSCAN聚类**└── 深度学习方法**    ├── 自编码器 (Autoencoder)**    └── 变分自编码器 (VAE)

## 三、scikit-learn入门

scikit-learn是Python最流行的机器学习库。

### 3.1 安装

pip install scikit-learn

### 3.2 基本使用流程

# 1. 导入**from sklearn.ensemble import IsolationForest**from sklearn.preprocessing import StandardScaler****# 2. 准备数据**# X = ... # 你的特征数据****# 3. 训练模型**model = IsolationForest(n_estimators=100, contamination=0.01)**model.fit(X)****# 4. 预测**# -1 表示异常，1 表示正常**predictions = model.predict(X)****# 5. 获取异常分数**scores = model.decision_function(X)

## 四、核心异常检测算法

### 4.1 孤立森林（Isolation Forest）

**原理**：异常点通常更容易被"孤立"（即随机切分时很快被分离出来）。

**优点**：
• 无需设置距离度量
• 对高维数据效果好
• 训练速度快

**审计应用场景**：
• 大量交易数据中的异常检测
• 高维特征（多指标）的异常识别

import numpy as np**import pandas as pd**from sklearn.ensemble import IsolationForest****# 模拟审计数据：科目余额表**np.random.seed(42)****# 正常数据：正态分布**normal_data = np.random.normal(loc=100, scale=20, size=(500, 4))**normal_labels = ['正常'] * 500****# 异常数据：添加一些异常值**anomaly_data = np.array([**    [500, 120, 80, 200],   # 第一列异常高**    [100, 800, 95, 150],   # 第二列异常高**    [110, 130, 500, 180],  # 第三列异常高**    [105, 115, 105, 900],  # 第四列异常高**])**anomaly_labels = ['异常'] * 4****# 合并数据**X = np.vstack([normal_data, anomaly_data])****# 训练孤立森林模型**model = IsolationForest(**    n_estimators=100,      # 树的数量**    contamination=0.01,    # 预期的异常比例（约1%）**    random_state=42**)**model.fit(X)****# 预测**predictions = model.predict(X)**scores = model.decision_function(X)****# 查看结果**results = pd.DataFrame({**    '金额1': X[:, 0],**    '金额2': X[:, 1],**    '金额3': X[:, 2],**    '金额4': X[:, 3],**    '预测结果': ['异常' if p == -1 else '正常' for p in predictions],**    '异常分数': scores**})****print("检测结果：")**print(results[results['预测结果'] == '异常'])****# 按异常分数排序，查看最异常的数据点**print("\n异常程度排名（前10）：")**print(results.sort_values('异常分数').head(10))

### 4.2 Local Outlier Factor (LOF)

**原理**：比较每个点与其邻域的密度，如果一个点的密度显著低于其邻居，则为异常。

**优点**：
• 对局部异常敏感
• 适合不同密度的数据集

**审计应用场景**：
• 识别局部异常（如某部门费用明显高于相似部门）
• 发现簇边缘的异常点

from sklearn.neighbors import LocalOutlierFactor****# 准备数据**# X = ... # 特征矩阵****# 训练LOF模型**lof = LocalOutlierFactor(**    n_neighbors=20,        # 邻居数量**    contamination=0.01,    # 异常比例**    novelty=False          # 用于预测新数据时设为True**)****# 拟合和预测**predictions = lof.fit_predict(X)**negative_outlier_factor = lof.negative_outlier_factor_****print(f"发现 {(predictions == -1).sum()} 个异常点")

### 4.3 One-Class SVM

**原理**：学习一个边界，边界内的数据被视为"正常"，边界外的为异常。

**适用场景**：
• 当正常数据远多于异常数据时
• 边界不规则的情况

from sklearn.svm import OneClassSVM****# 数据标准化（One-Class SVM对尺度敏感）**scaler = StandardScaler()**X_scaled = scaler.fit_transform(X)****# 训练模型**ocsvm = OneClassSVM(**    kernel='rbf',          # 核函数**    gamma='auto',**    nu=0.01                # 异常比例的上限**)**ocsvm.fit(X_scaled)****# 预测**predictions = ocsvm.predict(X_scaled)**anomaly_scores = ocsvm.decision_function(X_scaled)****print(f"发现 {(predictions == -1).sum()} 个异常点")

### 4.4 DBSCAN聚类

**原理**：基于密度的聚类算法，不属于任何簇的点被视为异常。

**优点**：
• 自动确定簇的数量
• 能识别任意形状的簇

**审计应用场景**：
• 客户分群分析
• 交易行为模式识别

from sklearn.cluster import DBSCAN****# 训练DBSCAN**dbscan = DBSCAN(**    eps=15,                # 邻域半径**    min_samples=5          # 最小样本数**)**clusters = dbscan.fit_predict(X)****# -1 表示噪声点（异常）**anomalies = X[clusters == -1]**print(f"发现 {len(anomalies)} 个异常点")**print("异常点：", anomalies)

## 五、实战案例

### 案例一：银行交易异常检测

import numpy as np**import pandas as pd**from sklearn.ensemble import IsolationForest**from sklearn.preprocessing import StandardScaler, LabelEncoder****# 1. 模拟银行交易数据**np.random.seed(42)****n_normal = 1000**transactions = pd.DataFrame({**    '交易ID': range(1, n_normal + 4),**    '交易金额': np.random.lognormal(8, 1.5, n_normal),**    '交易类型': np.random.choice(['转账', '取现', '消费', '还款'], n_normal),**    '交易时间': np.random.choice(['工作日', '周末'], n_normal),**    '对方账户类型': np.random.choice(['个人', '企业', '境外'], n_normal),**    '金额Log': np.log(np.random.lognormal(8, 1.5, n_normal))**})****# 添加几笔异常交易**anomalies = pd.DataFrame({**    '交易ID': [9991, 9992, 9993, 9994],**    '交易金额': [5000000, 3000000, 8000000, 2000000],  # 异常大额**    '交易类型': ['转账', '转账', '取现', '转账'],**    '交易时间': ['周末', '周末', '工作日', '周末'],**    '对方账户类型': ['境外', '境外', '个人', '境外'],**    '金额Log': [np.log(5000000), np.log(3000000), np.log(8000000), np.log(2000000)]**})****transactions = pd.concat([transactions, anomalies], ignore_index=True)****# 2. 特征工程**le_type = LabelEncoder()**le_time = LabelEncoder()**le_account = LabelEncoder()****transactions['交易类型编码'] = le_type.fit_transform(transactions['交易类型'])**transactions['时间编码'] = le_time.fit_transform(transactions['交易时间'])**transactions['账户类型编码'] = le_account.fit_transform(transactions['对方账户类型'])****# 特征矩阵**features = ['交易金额', '交易类型编码', '时间编码', '账户类型编码', '金额Log']**X = transactions[features].values****# 标准化**scaler = StandardScaler()**X_scaled = scaler.fit_transform(X)****# 3. 训练孤立森林**model = IsolationForest(**    n_estimators=100,**    contamination=0.005,**    random_state=42**)**model.fit(X_scaled)****# 4. 预测**transactions['异常预测'] = model.predict(X_scaled)**transactions['异常分数'] = model.decision_function(X_scaled)**transactions['风险等级'] = pd.qcut(transactions['异常分数'], q=3, labels=['低', '中', '高'])****# 5. 查看结果**print("=" * 60)**print("银行交易异常检测报告")**print("=" * 60)**print(f"总交易笔数：{len(transactions)}")**print(f"检测到异常笔数：{(transactions['异常预测'] == -1).sum()}")**print("\n异常交易明细：")**print(transactions[transactions['异常预测'] == -1][['交易ID', '交易金额', '交易类型', '交易时间', '对方账户类型', '异常分数']])****print("\n风险分布：")**print(transactions['风险等级'].value_counts())

### 案例二：费用报销异常检测

import numpy as np**import pandas as pd**from sklearn.ensemble import IsolationForest**from sklearn.preprocessing import StandardScaler****# 1. 模拟费用报销数据**np.random.seed(42)****# 正常报销数据**n = 500**expenses = pd.DataFrame({**    '员工ID': np.random.randint(1, 50, n),**    '部门': np.random.choice(['销售部', '市场部', '技术部', '财务部'], n),**    '费用类型': np.random.choice(['差旅', '招待', '办公', '交通'], n),**    '金额': np.random.lognormal(5, 1, n),  # 金额呈对数正态分布**    '天数': np.random.randint(1, 15, n),**    '每天均值': 0  # 稍后计算**})****# 计算每天均值**expenses['每天均值'] = expenses['金额'] / expenses['天数']****# 添加异常报销**anomalies = pd.DataFrame({**    '员工ID': [101, 102, 103, 104],**    '部门': ['销售部', '技术部', '财务部', '市场部'],**    '费用类型': ['招待', '差旅', '办公', '交通'],**    '金额': [50000, 80000, 30000, 60000],  # 异常高**    '天数': [1, 1, 5, 1],**    '每天均值': [50000, 80000, 6000, 60000]  # 每天均值也异常**})****expenses = pd.concat([expenses, anomalies], ignore_index=True)****# 2. 特征工程**expenses_encoded = pd.get_dummies(expenses[['部门', '费用类型']])**features = pd.concat([expenses[['金额', '天数', '每天均值']], expenses_encoded], axis=1)****X = features.values**scaler = StandardScaler()**X_scaled = scaler.fit_transform(X)****# 3. 训练多个模型进行集成**models = [**    ('IsolationForest', IsolationForest(n_estimators=100, contamination=0.01, random_state=42)),**]****results = []**for name, model in models:**    model.fit(X_scaled)**    pred = model.predict(X_scaled)**    score = model.decision_function(X_scaled)**    results.append({**        'model': name,**        'predictions': pred,**        'scores': score**    })****# 4. 汇总结果**expenses['异常预测'] = results[0]['predictions']**expenses['异常分数'] = results[0]['scores']****print("=" * 60)**print("费用报销异常检测报告")**print("=" * 60)**print("\n检测到的异常报销：")**print(expenses[expenses['异常预测'] == -1][['员工ID', '部门', '费用类型', '金额', '天数', '每天均值', '异常分数']])****# 按风险分数排序**print("\n高风险报销（前10）：")**print(expenses.sort_values('异常分数').head(10)[['员工ID', '部门', '费用类型', '金额', '异常分数']])

### 案例三：多指标综合异常检测

import numpy as np**import pandas as pd**from sklearn.ensemble import IsolationForest**from sklearn.preprocessing import StandardScaler****# 模拟财务报表数据**np.random.seed(42)****companies = pd.DataFrame({**    '公司代码': [f'C{str(i).zfill(3)}' for i in range(1, 101)],**    '营业收入': np.random.normal(10000, 2000, 100),**    '营业成本': np.random.normal(7000, 1500, 100),**    '管理费用': np.random.normal(1000, 300, 100),**    '销售费用': np.random.normal(800, 200, 100),**    '净利润': np.random.normal(800, 200, 100),**    '资产总额': np.random.normal(50000, 10000, 100),**    '负债总额': np.random.normal(25000, 5000, 100),**})****# 添加异常公司**anomaly_companies = pd.DataFrame({**    '公司代码': ['A001', 'A002', 'A003'],**    '营业收入': [10000, 10000, 5000],**    '营业成本': [8000, 15000, 8000],  # A002成本异常高**    '管理费用': [5000, 1000, 8000],   # A001和A003费用异常**    '销售费用': [800, 200, 5000],     # A003销售费用异常**    '净利润': [500, -5000, -3000],    # A002和A003亏损**    '资产总额': [50000, 50000, 20000],**    '负债总额': [45000, 50000, 25000], # A001负债率过高**})****companies = pd.concat([companies, anomaly_companies], ignore_index=True)****# 计算财务比率**companies['毛利率'] = (companies['营业收入'] - companies['营业成本']) / companies['营业收入']**companies['费用率'] = (companies['管理费用'] + companies['销售费用']) / companies['营业收入']**companies['资产负债率'] = companies['负债总额'] / companies['资产总额']**companies['净利润率'] = companies['净利润'] / companies['营业收入']****# 选择特征**features = ['营业收入', '营业成本', '管理费用', '销售费用',**            '毛利率', '费用率', '资产负债率', '净利润率']****X = companies[features].values**scaler = StandardScaler()**X_scaled = scaler.fit_transform(X)****# 训练孤立森林**model = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)**model.fit(X_scaled)****companies['异常预测'] = model.predict(X_scaled)**companies['异常分数'] = model.decision_function(X_scaled)****print("=" * 60)**print("财务数据综合异常检测报告")**print("=" * 60)**print("\n异常公司：")**print(companies[companies['异常预测'] == -1][['公司代码', '营业收入', '毛利率', '费用率', '净利润率', '异常分数']])****print("\n财务指标异常分析：")**for idx, row in companies[companies['异常预测'] == -1].iterrows():**    print(f"\n{row['公司代码']}:")**    if row['毛利率'] < companies['毛利率'].mean() - 2 * companies['毛利率'].std():**        print("  - 毛利率异常低")**    if row['费用率'] > companies['费用率'].mean() + 2 * companies['费用率'].std():**        print("  - 费用率异常高")**    if row['净利润率'] < 0:**        print("  - 净利润为负")**    if row['资产负债率'] > 0.7:**        print("  - 资产负债率过高")

## 六、模型评估与优化

### 6.1 评估指标

from sklearn.metrics import classification_report, confusion_matrix****# 假设我们有一些标记好的数据（用于评估）**# y_true: 真实标签（1=正常，-1=异常）**# y_pred: 预测标签****y_true = np.array([1, 1, 1, -1, 1, -1, 1, 1])**y_pred = np.array([1, 1, -1, -1, 1, 1, 1, -1])****print("混淆矩阵：")**print(confusion_matrix(y_true, y_pred))****print("\n评估报告：")**print(classification_report(y_true, y_pred, target_names=['正常', '异常']))

### 6.2 参数调优

from sklearn.model_selection import GridSearchCV****# 孤立森林参数调优**param_grid = {**    'n_estimators': [50, 100, 200],**    'contamination': [0.01, 0.02, 0.05],**    'max_samples': [100, 200, 'auto']**}****model = IsolationForest(random_state=42)**grid_search = GridSearchCV(**    model,**    param_grid,**    cv=5,  # 5折交叉验证**    scoring='recall'  # 以召回率为评估指标**)**grid_search.fit(X)****print("最优参数：", grid_search.best_params_)**print("最优得分：", grid_search.best_score_)

## 七、实战作业

1. **环境准备**：
• 安装scikit-learn库
• 准备一组审计数据（可以是模拟数据）
2. **模型练习**：
• 使用孤立森林、LOF、One-Class SVM三种方法对数据进行异常检测
• 比较不同方法的结果差异
3. **综合实践**：
• 选择一个实际的审计分析场景
• 进行完整的特征工程
• 训练和评估模型
• 解读分析结果

## 总结

今天我们学习了机器学习基础和异常检测算法：

算法
原理
适用场景
孤立森林
异常点更容易被孤立
大数据量、高维特征
LOF
比较局部密度差异
局部异常检测
One-Class SVM
学习正常数据边界
小样本、高维数据
DBSCAN
基于密度的聚类
自动发现异常簇

机器学习让异常检测从"设定规则"转变为"自动学习"。这是智能化审计的重要基础。

**下期预告**：我们将学习**自然语言处理（NLP）**——用于合同文本分析，帮助你从海量文本中提取有价值的信息。敬请期待！

如果觉得有帮助，欢迎转发给需要的同事！
