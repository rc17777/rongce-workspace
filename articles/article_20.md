# 七大核心方法玩转审计数据分析：从原理到落地

> **来源：** 数审派 微信公众号  
> **原文链接：** https://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483874&idx=1&sn=5b938bba0051ae53efdca561c3e725ff  
> **抓取时间：** 2026-05-06 20:05:01  
> **抓取方式：** curl + WeChat UA → HTML 提取

---

## 引言

如果说数据是审计的食材，那数据分析方法就是烹饪技术。同样一块鱼肉，煎炸炖煮味道各不相同；同样一堆数据，用不同方法分析也能得出截然不同的结论。

想象一下这个场景：**

某天，审计部小王拿到了一份看似正常的采购数据，Excel打开瞅了瞅——金额差不多、时间也挺规律、供应商也都是老熟人。完美！但小王总觉得哪里不对劲...

于是他掏出"数据分析神器"，对这份数据进行了多维度"解剖"：一查，发现那几家"老熟人"供应商的报价居然比其他供应商高出30%！二追，发现有好几笔大额采购都集中在周五下班后审批。三挖，发现某供应商跟采购经理竟是同一个老家的人...

原本"干干净净"的采购记录，一下子冒出来一堆问题线索。

这就是数据分析方法的威力——它能帮审计人员从表象看到本质，从常规中发现异常。

今天这篇文章，我将系统介绍七种审计工作中最常用的数据分析方法。每种方法都会配合具体的应用场景和代码示例，保证大家看完就能上手用。

## 一、描述性统计分析：先摸清"家底"

### 1.1 什么是描述性统计？

说白了，描述性统计就是给数据做"体检报告"。

你去医院体检，化验单上会写：身高、体重、血压、血糖...这些指标能快速让你知道自己身体的基本情况。描述性统计也是一样——它通过一组简单的数字，告诉你这堆数据长什么样。

主要包括三个"当家花旦"：
• **均值**（平均值）：把所有人的工资加一块再除以人数，就是"平均工资"
• **中位数**：把所有人的工资从低到高排，最中间那个就是中位数
• **众数**：出现次数最多的那个值

为什么要同时看这三个？因为它们组合起来，才能告诉你数据的真实面貌。

举个例子：某公司有100个员工，99个月薪5000元，1个高管月薪500万。这时候均值告诉你"平均月薪50万"，听起来大家都挺有钱；中位数告诉你"中间那位月薪5000"，这才是普通员工的真实收入水平。

### 1.2 集中趋势分析

前面提到的均值、中位数、众数，都是用来反映数据"集中趋势"的指标。它们能帮助审计人员快速了解：
• 公司的费用水平大概在什么区间？
• 某个供应商的报价是偏高还是偏低？
• 业务的整体表现是"正常"还是"异常"？

import pandas as pd**import numpy as np****def descriptive_statistics(df, column):**    """**    描述性统计分析函数**    一键生成数据体检报告**    """**    stats = {**        '样本数量': df[column].count(),**        '平均值': df[column].mean(),**        '中位数': df[column].median(),**        '众数': df[column].mode()[0] if not df[column].mode().empty else None,**        '标准差': df[column].std(),**        '最小值': df[column].min(),**        '最大值': df[column].max(),**        '数据范围': df[column].max() - df[column].min(),**        'Q1（25%分位）': df[column].quantile(0.25),**        'Q3（75%分位）': df[column].quantile(0.75),**        '四分位距IQR': df[column].quantile(0.75) - df[column].quantile(0.25),**        '偏度': df[column].skew(),**        '峰度': df[column].kurtosis()**    }****    return pd.DataFrame.from_dict(stats, orient='index', columns=['数值'])

**审计应用场景**：

在财务审计中，通过分析管理费用、销售费用等科目的均值、中位数，可以了解企业的费用水平；对比不同期间的数据，可以发现费用异常波动的线索。

# 审计应用示例：分析管理费用月度波动**management_fees = df[df['account_code'] == '6602']['amount']****stats_df = descriptive_statistics(management_fees, 'amount')**print("管理费用描述性统计：")**print(stats_df)****# 识别异常月份（偏离均值2个标准差以上）**mean_fee = management_fees.mean()**std_fee = management_fees.std()**threshold = 2****anomalous_months = df[**    (df['account_code'] == '6602') &**    (np.abs(df['amount'] - mean_fee) > threshold * std_fee)**][['period', 'amount']]****print(f"\n异常波动月份（偏离均值超过{threshold}个标准差）：")**print(anomalous_months)

**实战小贴士**：

审计老司机通常会用"均值±2倍标准差"作为异常判定的经验值。数据落在这个区间之外的，要么是大牛人，要么就是有问题。

### 1.3 分布分析：数据也有"性格"

分布分析能帮我们看清数据的"性格"——它是正态分布（规规矩矩中间多）？还是双峰分布（两个山头）？或者是严重右偏（少数几个大鳄拖后腿）？

看分布图就像看人的性格一样，有时候比看具体数字更有价值。

def distribution_analysis(df, column, bins=20):**    """**    分布分析**    看看数据的"身材"如何**    """**    # 计算频数分布**    hist, bin_edges = np.histogram(df[column], bins=bins)****    # 计算累计分布**    sorted_data = np.sort(df[column])**    cumulative = np.arange(1, len(sorted_data) + 1) / len(sorted_data)****    # 输出分布特征**    distribution_summary = pd.DataFrame({**        '区间起始': bin_edges[:-1],**        '区间结束': bin_edges[1:],**        '频数': hist,**        '频率': hist / len(df[column])**    })****    return distribution_summary

**审计应用场景**：

在收入审计中，通过分析销售收入的分布，可以识别是否存在虚假交易；在费用审计中，通过分析费用金额分布，可以发现异常的费用报销模式。

# 审计应用示例：分析销售收入的金额分布**sales_data = df[df['transaction_type'] == 'SALE']['amount']****print("销售收入分布分析：")**dist_df = distribution_analysis(sales_data, 'amount', bins=50)****# 识别小额交易异常（通常虚假交易金额较小且整数值较多）**small_sales = df[**    (df['transaction_type'] == 'SALE') &**    (df['amount'] < 100) &**    (df['amount'] == df['amount'].astype(int))**]****print(f"\n小额整数销售记录数：{len(small_sales)}")**print(f"涉及金额：{small_sales['amount'].sum()}")

**有意思的发现**：

虚假交易往往有几个特点：金额小、整数多、日期集中、审批流程简化。通过分布分析，这些"不自然"的模式会像夜空中的星星一样凸显出来。

## 二、相关性分析：寻找"朋友圈"

### 2.1 相关性是什么？

通俗来说，相关性就是研究"谁跟谁是一伙的"。

举个例子：夏天冰棍销量增加，溺水人数也会增加——这两者有相关性。但冰棍卖得好并不会导致溺水，问题在于它们背后都有同一个原因：夏天天气热。

这个例子告诉我们：相关性不等于因果关系。但它能帮我们发现潜在的联系。

在审计中，相关性分析有什么用呢？
• 成本和产量应该是正相关的，如果产量下降成本却上升——有问题
• 销售额和广告投入应该是正相关的，如果广告砸了钱销售却不动——有猫腻
• 员工数量和办公面积应该是正相关的，如果人少办公室却越来越大——不对劲

### 2.2 相关系数计算

相关系数是一个介于-1和1之间的数字：
• 接近1：强正相关（手牵手一起走）
• 接近-1：强负相关（你往东我往西）
• 接近0：没什么关系（各走各的路）

def correlation_analysis(df, columns):**    """**    相关性分析**    找出数据之间的"朋友圈"**    """**    # Pearson相关系数（适用于线性关系）**    pearson_corr = df[columns].corr(method='pearson')****    # Spearman相关系数（适用于非线性关系，更稳健）**    spearman_corr = df[columns].corr(method='spearman')****    return pearson_corr, spearman_corr****def find_high_correlations(df, threshold=0.8):**    """**    找出高相关性变量对**    也就是"铁哥们"**    """**    corr_matrix = df.corr()****    high_corr_pairs = []**    for i in range(len(corr_matrix.columns)):**        for j in range(i+1, len(corr_matrix.columns)):**            if abs(corr_matrix.iloc[i, j]) > threshold:**                high_corr_pairs.append({**                    '变量1': corr_matrix.columns[i],**                    '变量2': corr_matrix.columns[j],**                    '相关系数': corr_matrix.iloc[i, j]**                })****    return pd.DataFrame(high_corr_pairs)

**审计应用场景**：

在成本审计中，通过分析产量与成本的相关性，可以识别虚增成本的问题；在收入审计中，通过分析销售数量与销售收入的相关系数，可以验证收入的完整性。

# 审计应用示例：分析成本与产量的相关性**# 正常情况下，成本与产量应呈正相关**cost_production_corr = df[['production_volume', 'cost_amount']].corr()**print("成本与产量相关性分析：")**print(cost_production_corr)****# 识别异常相关：产量下降但成本上升**abnormal_cost = df[**    (df['production_volume'].pct_change() < -0.1) &  # 产量下降超过10%**    (df['cost_amount'].pct_change() > 0.1)  # 成本上升超过10%**]****print(f"\n产量下降但成本上升的月份数：{len(abnormal_cost)}")

### 2.3 偏相关分析

有时候两个变量之间的关系会受到第三个变量的"干扰"。偏相关分析就是在控制其他变量影响的情况下，单独看两个变量的真实关系。

from scipy import stats****def partial_correlation(df, var1, var2, control_vars):**    """**    偏相关分析**    排除"第三者干扰"，看真实的二人世界**    """**    # 计算var1和var2的相关系数**    r_xy = df[var1].corr(df[var2])****    # 计算var1与控制变量的相关系数**    r_xz = df[var1].corr(df[control_vars])****    # 计算var2与控制变量的相关系数**    r_yz = df[var2].corr(df[control_vars])****    # 计算偏相关系数**    r_xy_z = (r_xy - r_xz * r_yz) / np.sqrt((1 - r_xz**2) * (1 - r_yz**2))****    return r_xy_z

**生活中的例子**：

收入和学历通常是正相关的。但如果我们控制"专业"这个变量，会发现同一专业内，收入和学历的关系可能就没那么明显了——因为有些专业天生就是比别的专业赚钱。

## 三、回归分析：预测未来

### 3.1 回归分析是什么？

如果说相关性分析回答的是"有没有关系"，那回归分析回答的就是"有什么关系、有什么关系"。

回归分析可以帮我们建立数学模型，用一个或多个变量来预测另一个变量。

举个例子：审计人员想知道维修费用跟哪些因素有关。通过回归分析，可能会发现：
• 维修费用 = 0.5 × 设备年龄 + 2.3 × 维修次数 + 1000

这意味着：设备每老1年，维修费用平均多0.5元；每多修一次，费用多2.3元；基础费用是1000元。

这个公式有什么用？一方面可以验证业务逻辑是否合理，另一方面可以预测未来的费用水平——如果实际值长期大幅偏离预测值，就要警惕了。

### 3.2 线性回归分析

from sklearn.linear_model import LinearRegression**from sklearn.model_selection import train_test_split**from sklearn.metrics import r2_score, mean_squared_error****def linear_regression_analysis(df, target_var, feature_vars):**    """**    线性回归分析**    建立预测模型，看透变量之间的关系**    """**    X = df[feature_vars]**    y = df[target_var]****    # 划分训练集和测试集（用来验证模型准不准）**    X_train, X_test, y_train, y_test = train_test_split(**        X, y, test_size=0.2, random_state=42**    )****    # 建立模型**    model = LinearRegression()**    model.fit(X_train, y_train)****    # 预测和评估**    y_pred = model.predict(X_test)****    results = {**        '回归系数': dict(zip(feature_vars, model.coef_)),**        '截距': model.intercept_,**        'R²分数': r2_score(y_test, y_pred),**        'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),**        '预测值': y_pred,**        '实际值': y_test**    }****    return results

**审计应用场景**：

在费用审计中，可以通过回归分析建立费用预测模型，将实际费用与预测费用进行对比，识别异常偏高或偏低的情况。

# 审计应用示例：建立销售费用预测模型**# 假设销售费用与销售收入、市场推广投入、员工数量相关****feature_vars = ['revenue', 'marketing_expense', 'employee_count']**target_var = 'sales_expense'****results = linear_regression_analysis(df, target_var, feature_vars)****print("销售费用回归分析结果：")**print(f"R² 分数：{results['R²分数']:.4f}")**print(f"RMSE：{results['RMSE']:.2f}")**print("\n回归系数（解读：每增加1单位对应变量，销售费用增加多少）：")**for var, coef in results['回归系数'].items():**    print(f"  {var}: {coef:.4f}")****# 识别异常：实际值与预测值差异超过2个RMSE**df['predicted_sales_expense'] = results['截距'] + sum(**    df[var] * results['回归系数'][var] for var in feature_vars**)**df['残差'] = df['sales_expense'] - df['predicted_sales_expense']****abnormal_expense = df[np.abs(df['残差']) > 2 * results['RMSE']]**print(f"\n异常费用记录数：{len(abnormal_expense)}")

**R²分数解读**：

R²取值范围0-1，越接近1说明模型预测越准。通常：
• R² > 0.8：模型效果不错
• 0.5 < R² < 0.8：勉强能用，需要改进
• R² < 0.5：模型质量堪忧，可能漏掉了重要变量

### 3.3 风险评分模型

回归分析还有个高级玩法——风险评分模型。通过给不同的风险因素分配权重，计算出每个审计对象的"风险得分"。

from sklearn.preprocessing import StandardScaler**from sklearn.linear_model import LogisticRegression****def risk_scoring_model(df, risk_factors, known_risk_cases):**    """**    风险评分模型**    给风险打打分，高的要重点关注**    """**    X = df[risk_factors]**    y = known_risk_cases****    # 标准化（消除量纲影响）**    scaler = StandardScaler()**    X_scaled = scaler.fit_transform(X)****    # 建立逻辑回归模型**    model = LogisticRegression(random_state=42)**    model.fit(X_scaled, y)****    # 计算风险分数（0-1之间，越接近1越危险）**    df['risk_score'] = model.predict_proba(X_scaled)[:, 1]****    return model, df****def calculate_risk_score_weights(model, risk_factors):**    """**    计算各风险因素的权重**    看看谁是"风险之王"**    """**    coefficients = model.coef_[0]**    weights = pd.DataFrame({**        '风险因素': risk_factors,**        '回归系数': coefficients,**        '绝对值': np.abs(coefficients)**    }).sort_values('绝对值', ascending=False)****    return weights

**实战应用**：

银行放贷款要评估违约风险，审计也可以借鉴这个思路。通过对供应商、客户、员工建立风险评分模型，把有限审计资源集中在高风险领域。

## 四、聚类分析：物以类聚

### 4.1 聚类是什么？

"物以类聚，人以群分"——聚类分析就是干这个的。

它能帮我们把相似的数据点自动归为一组，让你一眼看出"谁跟谁是一伙的"。

审计中的应用场景：
• 把供应商分分类：哪些是价格高的、哪些是交货慢的、哪些是质量差的
• 把员工分分类：哪些人报销金额异常高、哪些人审批速度异常快
• 把客户分分类：哪些是贡献大但回款差的、哪些是稳定但增长慢的

### 4.2 K-Means聚类

K-Means是最经典的聚类算法，原理很简单：
1. 先指定要分成几类（K值）
2. 随机选K个点作为"种子"
3. 把每个数据点归到最近的"种子"那一类
4. 重新计算每类的中心点
5. 重复3-4步，直到收敛

from sklearn.cluster import KMeans**from sklearn.preprocessing import StandardScaler****def kmeans_clustering(df, features, n_clusters=5):**    """**    K-Means聚类分析**    自动给数据"分班"**    """**    X = df[features]****    # 标准化（让不同量纲的指标可以比较）**    scaler = StandardScaler()**    X_scaled = scaler.fit_transform(X)****    # 确定最优聚类数（肘部法则）**    inertias = []**    K_range = range(2, 10)**    for k in K_range:**        kmeans = KMeans(n_clusters=k, random_state=42)**        kmeans.fit(X_scaled)**        inertias.append(kmeans.inertia_)****    # 执行聚类**    kmeans = KMeans(n_clusters=n_clusters, random_state=42)**    df['cluster'] = kmeans.fit_predict(X_scaled)****    # 计算聚类特征（每类长什么样）**    cluster_summary = df.groupby('cluster')[features].mean()****    return df, cluster_summary, inertias

**审计应用场景**：

在供应商审计中，可以对供应商进行聚类分析，识别交易特征异常的供应商群体；在员工审计中，可以对员工的行为数据进行聚类，发现可疑的行为模式。

# 审计应用示例：供应商聚类分析**# 基于交易金额、交易频率、价格偏差等维度对供应商进行聚类****vendor_features = ['total_transaction_amount', 'transaction_count',**                   'avg_price_deviation', 'payment_delay_days']****df_clustered, cluster_summary, inertias = kmeans_clustering(**    vendor_df, vendor_features, n_clusters=4**)****print("供应商聚类分析结果：")**print(cluster_summary)****# 分析各聚类的风险特征**for cluster_id in range(4):**    cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]**    print(f"\n聚类 {cluster_id} 供应商数：{len(cluster_data)}")**    print(f"  平均交易金额：{cluster_data['total_transaction_amount'].mean():.2f}")**    print(f"  平均价格偏差：{cluster_data['avg_price_deviation'].mean():.2f}%")****    # 标记高风险聚类**    if cluster_data['avg_price_deviation'].mean() > 15:**        high_risk_vendors = cluster_data[cluster_data['total_transaction_amount'] > 1000000]**        print(f"  高风险供应商数：{len(high_risk_vendors)}")

### 4.3 层次聚类

跟K-Means不同，层次聚类不需要预先指定分几类。它会画一个"族谱图"（树状图），让你看到数据之间从远到近的亲疏关系。

from scipy.cluster.hierarchy import dendrogram, linkage, fcluster****def hierarchical_clustering(df, features, method='ward'):**    """**    层次聚类分析**    画个族谱图，看看谁跟谁最亲近**    """**    X = df[features]****    # 标准化**    scaler = StandardScaler()**    X_scaled = scaler.fit_transform(X)****    # 计算层次聚类**    Z = linkage(X_scaled, method=method)****    # 绘制树状图**    plt.figure(figsize=(12, 8))**    dendrogram(Z, labels=df.index.tolist(), leaf_rotation=90)**    plt.title('供应商层次聚类树状图')**    plt.xlabel('供应商编号')**    plt.ylabel('距离')**    plt.show()****    # 切割树状图获取聚类结果**    clusters = fcluster(Z, t=5, criterion='maxclust')****    return Z, clusters

**什么时候用层次聚类**：
• 数据量不大（几百到几千）
• 想要看到聚类形成的"过程"
• 需要一个直观的可视化展示

## 五、异常检测：火眼金睛识"妖怪"

### 5.1 什么是异常检测？

前面几种分析方法都是在"找规律"，异常检测则是专门"找反常"。

在审计中，异常检测的意义重大：大部分交易都是正常的，但偏偏就是那些少数异常交易，往往隐藏着最大的风险。

常见的"妖怪"类型：
• **点异常**：单笔交易本身就不正常（比如单笔金额特别大）
• **上下文异常**：单独看某笔交易没问题，但放到特定时间或背景下就露馅了（比如月末集中报销）
• **集体异常**：单独看每笔都正常，但它们集体出现就有问题（比如同一个供应商的多笔交易都恰好卡在审批权限边界）

### 5.2 基于统计的异常检测

最简单的方法：用统计学原理找出"不正常"的数据点。
• IQR法：数据落在Q1-1.5×IQR到Q3+1.5×IQR之外，就算异常
• Z分数法：数据偏离均值超过2-3个标准差，就算异常

def statistical_outlier_detection(df, column, method='iqr', threshold=1.5):**    """**    基于统计的异常值检测**    用统计学原理找出"害群之马"**    """**    if method == 'iqr':**        Q1 = df[column].quantile(0.25)**        Q3 = df[column].quantile(0.75)**        IQR = Q3 - Q1**        lower_bound = Q1 - threshold * IQR**        upper_bound = Q3 + threshold * IQR****        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)].copy()**        outliers['异常原因'] = outliers[column].apply(**            lambda x: '低于下限' if x < lower_bound else '高于上限'**        )**        outliers['边界值'] = outliers[column].apply(**            lambda x: lower_bound if x < lower_bound else upper_bound**        )**        outliers['偏离比例'] = abs(outliers[column] - outliers['边界值']) / IQR****    elif method == 'zscore':**        mean = df[column].mean()**        std = df[column].std()**        z_scores = np.abs((df[column] - mean) / std)****        outliers = df[z_scores > threshold].copy()**        outliers['Z分数'] = z_scores[z_scores > threshold]**        outliers['异常原因'] = 'Z分数超过阈值'**        outliers['偏离比例'] = outliers['Z分数']****    return outliers, lower_bound, upper_bound

### 5.3 基于机器学习的异常检测

当数据维度高、关系复杂的时候，传统统计方法就不够用了。这时候可以请出机器学习算法。

**Isolation Forest（隔离森林）**：它的原理很巧妙——既然异常点"不正常"，那它们应该更容易被"隔离"出来。算法随机选择特征和切分点，看多久能把一个点隔离掉。隔离所需次数越少，越可能是异常。

**Local Outlier Factor（LOF）**：它的思路是看一个点跟邻居的"疏远程度"。如果某个点跟周围的邻居都格格不入，它就很可能是异常。

from sklearn.ensemble import IsolationForest**from sklearn.neighbors import LocalOutlierFactor****def isolation_forest_detection(df, features, contamination=0.1):**    """**    Isolation Forest异常检测**    用"隔离法"找出异类**    """**    X = df[features]****    # 标准化**    scaler = StandardScaler()**    X_scaled = scaler.fit_transform(X)****    # 建立Isolation Forest模型**    model = IsolationForest(**        contamination=contamination,  # 假设10%的数据是异常的**        random_state=42,**        n_estimators=100**    )****    # 预测：-1表示异常，1表示正常**    df['anomaly_label'] = model.fit_predict(X_scaled)**    df['anomaly_score'] = model.decision_function(X_scaled)****    # 筛选异常记录**    anomalies = df[df['anomaly_label'] == -1].copy()****    return anomalies, model****def lof_detection(df, features, n_neighbors=20, contamination=0.1):**    """**    Local Outlier Factor异常检测**    看谁跟邻居最疏远**    """**    X = df[features]****    # 标准化**    scaler = StandardScaler()**    X_scaled = scaler.fit_transform(X)****    # 建立LOF模型**    model = LocalOutlierFactor(**        n_neighbors=n_neighbors,**        contamination=contamination**    )****    df['anomaly_label'] = model.fit_predict(X_scaled)**    df['lof_score'] = model.negative_outlier_factor_****    anomalies = df[df['anomaly_label'] == -1].copy()****    return anomalies, model

**审计应用示例**：

# 审计应用示例：采购异常交易 Detection**# 基于交易金额、价格偏差、交易时间等维度检测异常****purchase_features = ['transaction_amount', 'price_deviation_pct',**                     'is_weekend', 'payment_delay_days']****anomalies, model = isolation_forest_detection(purchase_df, purchase_features, contamination=0.05)****print(f"检测到 {len(anomalies)} 笔异常采购交易")**print("\n异常交易详情：")**print(anomalies[['transaction_date', 'vendor_name', 'transaction_amount',**                 'price_deviation_pct', 'anomaly_score']].sort_values('anomaly_score'))****# 按供应商统计异常交易**vendor_anomaly_summary = anomalies.groupby('vendor_name').agg({**    'transaction_amount': ['count', 'sum'],**    'anomaly_score': 'mean'**}).round(4)****vendor_anomaly_summary.columns = ['异常交易数', '异常交易金额', '平均异常分数']**vendor_anomaly_summary = vendor_anomaly_summary.sort_values('异常交易金额', ascending=False)****print("\n供应商异常交易排名：")**print(vendor_anomaly_summary.head(10))

## 六、关联规则分析：顺藤摸瓜

### 6.1 关联规则是什么？

"啤酒和尿布"的故事你可能听过——美国超市发现，买尿布的顾客往往也会买啤酒。这就是关联规则的经典案例。

在审计中，关联规则可以帮我们发现一些"打包出现"的风险模式。比如：
• 周末审批 + 大额采购 + 指定供应商 → 高风险
• 新供应商 + 首次交易 + 现金付款 → 可疑
• 员工转账 + 供应商账户 + 备注"借款" → 违规

通过关联规则分析，我们能把这些隐藏的风险组合挖出来。

### 6.2 Apriori算法

Apriori算法是挖掘关联规则的经典方法。它的核心思想是：如果一个事务包含某个item集合，那它的超集也可能包含关联规则。

翻译成人话：如果"周末"和"大额采购"经常一起出现，那包含"周末"的交易也可能包含"大额采购"。

from mlxtend.frequent_patterns import apriori, association_rules**from mlxtend.preprocessing import TransactionEncoder****def apriori_analysis(df, itemsets, min_support=0.1):**    """**    Apriori关联规则分析**    找出"经常一起出现"的事物**    """**    # 编码为one-hot格式**    te = TransactionEncoder()**    te_ary = te.fit(itemsets).transform(itemsets)**    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)****    # 挖掘频繁项集**    frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)****    # 生成关联规则**    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)****    return frequent_itemsets, rules****def prepare_transaction_data(df, transaction_col, item_cols):**    """**    准备事务数据用于关联规则挖掘**    把数据整理成"购物篮"格式**    """**    transactions = []**    for _, row in df.iterrows():**        transaction = []**        for col in item_cols:**            if pd.notna(row[col]) and row[col] != '':**                transaction.append(str(row[col]))**        if transaction:**            transactions.append(transaction)****    return transactions

**审计应用场景**：

在舞弊审计中，关联规则可以发现同时出现的风险因素组合，如"同一审批人+周末审批+金额超过阈值"。

# 审计应用示例：发现异常审批模式**# 准备事务数据：每笔采购构成一个事务，包含审批人、时间、金额区间等****df['approval_hour'] = df['approval_time'].dt.hour**df['is_high_amount'] = df['amount'] > df['amount'].quantile(0.9)**df['is_weekend'] = df['approval_time'].dt.dayofweek.isin([5, 6])****item_cols = ['approver_id', 'approval_hour_bucket', 'amount_bucket',**             'is_high_amount', 'is_weekend', 'vendor_category']****df['approval_hour_bucket'] = pd.cut(df['approval_hour'],**                                      bins=[0, 9, 12, 18, 24],**                                      labels=['morning', 'noon', 'afternoon', 'evening'])**df['amount_bucket'] = pd.cut(df['amount'],**                             bins=[0, 10000, 50000, 100000, float('inf')],**                             labels=['small', 'medium', 'large', 'very_large'])****transactions = prepare_transaction_data(df, 'transaction_id', item_cols)****frequent_itemsets, rules = apriori_analysis(df, transactions, min_support=0.05)****# 筛选高风险规则**high_risk_rules = rules[**    (rules['confidence'] > 0.7) &**    (rules['lift'] > 2)**].sort_values('lift', ascending=False)****print("高风险关联规则：")**print(high_risk_rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']])

**关联规则三个指标解读**：
• **Support（支持度）**：这个组合在所有交易中出现的频率。越高说明越普遍
• **Confidence（置信度）**：出现A的时候，B也出现的概率。越高说明关联越强
• **Lift（提升度）**：A和B同时出现的概率，比它们独立出现概率高多少。超过1才有意义，越大说明关联越强

## 七、时间序列分析：让数据"动"起来

### 7.1 时间序列是什么？

时间序列就是按时间顺序排列的数据。比如：
• 每月收入变化
• 每日活跃用户数
• 每季度利润走势

分析时间序列，就是分析数据随时间变化的规律——趋势、季节性、周期性、突发事件影响等。

### 7.2 趋势分析

趋势分析帮我们看清数据长期是上涨、下跌还是平稳。

def trend_analysis(df, date_col, value_col, window=12):**    """**    时间序列趋势分析**    看看数据是"蒸蒸日上"还是"日落西山"**    """**    df = df.copy()**    df = df.sort_values(date_col)****    # 计算移动平均（平滑短期波动，看清长期趋势）**    df['rolling_mean'] = df[value_col].rolling(window=window, min_periods=1).mean()****    # 计算趋势斜率（线性回归）**    df['time_index'] = range(len(df))**    X = df[['time_index']]**    y = df[value_col]****    model = LinearRegression()**    model.fit(X, y)****    trend_slope = model.coef_[0]****    # 识别趋势转折点**    df['trend_change'] = df['rolling_mean'].diff()**    trend_turns = df[abs(df['trend_change']) > 2 * df['trend_change'].std()]****    return df, trend_slope, trend_turns

### 7.3 季节性分析

很多业务都有季节性规律：空调旺季在夏天、年终奖集中在年底、礼品卡在节日前热销...季节性分析帮我们识别这些周期性波动。

def seasonal_analysis(df, date_col, value_col):**    """**    季节性分析**    看看数据是不是"看天吃饭"**    """**    df = df.copy()**    df['year'] = df[date_col].dt.year**    df['month'] = df[date_col].dt.month****    # 按月份汇总**    monthly_avg = df.groupby('month')[value_col].mean()****    # 计算季节指数（该月是平均水平的多少倍）**    overall_avg = df[value_col].mean()**    seasonal_index = monthly_avg / overall_avg****    # 识别异常季节波动**    seasonal_anomalies = df[**        df['month'].isin(seasonal_index[seasonal_index < 0.7].index) |**        df['month'].isin(seasonal_index[seasonal_index > 1.3].index)**    ]****    return seasonal_index, seasonal_anomalies

**审计应用示例**：

# 审计应用示例：收入趋势与季节性分析**# 分析营业收入的趋势变化和季节性模式****monthly_revenue = df.groupby('invoice_month')['revenue'].sum().reset_index()**monthly_revenue['invoice_month'] = pd.to_datetime(monthly_revenue['invoice_month'])****analyzed_df, trend_slope, trend_turns = trend_analysis(**    monthly_revenue, 'invoice_month', 'revenue', window=3**)****print(f"收入月均增长：{trend_slope:.2f}")****# 季节性分析**seasonal_index, seasonal_anomalies = seasonal_analysis(**    monthly_revenue, 'invoice_month', 'revenue'**)****print("\n季节指数（1.0表示平均水平）：")**print(seasonal_index)****# 识别异常月份**monthly_revenue['expected_revenue'] = monthly_revenue['invoice_month'].dt.month.map(**    seasonal_index * overall_avg**)**monthly_revenue['variance_pct'] = (**    (monthly_revenue['revenue'] - monthly_revenue['expected_revenue']) /**    monthly_revenue['expected_revenue']**)****abnormal_months = monthly_revenue[abs(monthly_revenue['variance_pct']) > 0.2]**print(f"\n收入异常月份（偏差超过20%）：")**print(abnormal_months)

## 总结：七把利剑，审计无忧

今天这篇文章给大家介绍了审计数据分析的七种核心方法：

方法类别
核心价值
一句话总结
描述性统计
数据特征刻画
先看看数据长什么样
相关性分析
关系识别与验证
找找谁跟谁是一伙的
回归分析
因果关系与预测
建立模型，预测未来
聚类分析
群体划分与发现
物以类聚，人以群分
异常检测
异常识别
找出那个"害群之马"
关联规则
模式发现
顺藤摸瓜，一网打尽
时间序列
趋势与周期分析
看数据如何"动"起来

这些方法不是孤立的，高级的审计分析往往需要综合运用多种技术：

比如要做供应商风险评估，可能先用聚类分析把供应商分群，再用异常检测找出高风险供应商，最后用关联规则发现哪些风险因素经常"结伴出现"。

**关注不迷路**：**

如果你觉得这篇文章对你有帮助，欢迎转发给身边的审计同行！

有任何问题或建议，欢迎在评论区留言交流~
