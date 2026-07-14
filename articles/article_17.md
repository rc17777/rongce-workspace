# 审计人员数字技能修炼手册 | 高阶篇（二）：自然语言处理——合同文本分析

> **来源：** 数审派 微信公众号  
> **原文链接：** https://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483858&idx=1&sn=a42f38c2a5010f96fb4e475d2364af68  
> **抓取时间：** 2026-05-06 20:05:00  
> **抓取方式：** curl + WeChat UA → HTML 提取

---

各位审计同仁，大家好！

上期我们完成了机器学习基础的学习。今天我们继续高阶篇第二站——**自然语言处理（NLP）**。

审计工作中，除了数字数据，还有大量的文本数据需要处理：合同、协议、审计报告、法规文件等。NLP技术可以帮助审计人员自动从这些文本中提取关键信息、识别风险点。

## 一、认识自然语言处理

### 1.1 什么是NLP？

自然语言处理（Natural Language Processing，NLP）是人工智能的一个分支，研究如何让计算机理解和生成人类语言。

### 1.2 NLP在审计中的应用

应用场景
具体内容**合同分析**
提取关键条款、识别风险点**审计报告分析**
自动分类审计意见**法规解读**
提取适用条款、判断合规性**文本分类**
将合同/单据分类**实体识别**
提取合同中的金额、日期、主体**智能问答**
自动回答审计问题**情感分析**
分析客户反馈、舆情监控

### 1.3 NLP处理流程

文本数据**   ↓**文本预处理（清洗、分词、去停用词）**   ↓**特征提取（词袋模型、TF-IDF、词嵌入）**   ↓**建模与分析（分类、实体识别、情感分析）**   ↓**结果输出（结构化数据、报告）

## 二、文本预处理基础

### 2.1 安装必要的库

pip install jieba snownlp thulac sklearn

### 2.2 中文分词

中文文本需要先分词才能进行分析。

import jieba****# 基础分词**text = "本合同的标的物为甲方所有的商品房一套"**words = jieba.lcut(text)**print(words)**# 输出：['本合同', '的', '标的物', '为', '甲方', '所有', '的', '商品房', '一套']****# 添加自定义词汇**jieba.add_word('标的物')**jieba.add_word('甲方')**jieba.add_word('乙方')****words = jieba.lcut(text)**print(words)

### 2.3 文本清洗

import re****def clean_text(text):**    """文本清洗"""**    # 去除特殊字符**    text = re.sub(r'[^\w\s]', '', text)**    # 去除数字（保留金额中的数字，后续单独处理）**    # text = re.sub(r'\d+', '', text)**    # 去除多余空格**    text = re.sub(r'\s+', ' ', text)**    # 转小写（英文文本时）**    # text = text.lower()**    return text.strip()****text = "本合同签署日期为2024年1月1日，甲乙双方经友好协商，达成如下协议："**cleaned = clean_text(text)**print(cleaned)

### 2.4 停用词处理

# 常见停用词**stopwords = set([**    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',**    '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',**    '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '但'**])****def remove_stopwords(words):**    """去除停用词"""**    return [w for w in words if w not in stopwords and len(w) > 1]****text = "本合同的标的物为甲方所有的商品房一套"**words = jieba.lcut(text)**filtered = remove_stopwords(words)**print(filtered)

## 三、关键词提取

### 3.1 TF-IDF关键词提取

TF-IDF是一种用于信息检索的权重计算方法。

from sklearn.feature_extraction.text import TfidfVectorizer****# 示例文档**documents = [**    "本合同规定了双方的权利和义务",**    "甲方应按期支付货款",**    "乙方应按时交付货物",**    "违约方应承担违约责任",**    "本合同一式两份，甲乙双方各执一份"**]****# 创建TF-IDF向量化器**tfidf = TfidfVectorizer(max_features=10)**tfidf_matrix = tfidf.fit_transform(documents)****# 获取特征词**feature_names = tfidf.get_feature_names_out()**print("关键词：", feature_names)****# 查看每篇文档的关键词权重**for i, doc in enumerate(documents):**    scores = tfidf_matrix[i].toarray()[0]**    top_indices = scores.argsort()[-3:][::-1]  # 取前3个关键词**    print(f"\n文档{i+1}: {doc}")**    print(f"关键词: {[feature_names[idx] for idx in top_indices]}")

### 3.2 使用jieba的关键词提取

import jieba.analyse****text = """**本合同甲方委托乙方进行软件开发工作，双方经友好协商，达成如下协议：****一、委托内容**甲方委托乙方开发XXX系统，包括需求分析、系统设计、编码实现、测试验收等工作。****二、开发费用**本项目总费用为人民币100万元整，分阶段支付。****三、交付时间**乙方应于2024年12月31日前完成系统开发并交付甲方使用。****四、违约责任**如一方违约，应向守约方支付合同总金额20%的违约金。**"""****# 提取关键词**keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=True)**print("关键词提取结果：")**for word, weight in keywords:**    print(f"  {word}: {weight:.4f}")

## 四、文本分类

### 4.1 合同风险分类

from sklearn.feature_extraction.text import TfidfVectorizer**from sklearn.naive_bayes import MultinomialNB**from sklearn.linear_model import LogisticRegression**from sklearn.model_selection import train_test_split**from sklearn.metrics import classification_report****# 模拟合同数据**contracts = [**    ("房屋租赁合同", "租赁", "低风险"),**    ("软件开发合同", "技术合同", "中风险"),**    ("采购合同", "采购", "低风险"),**    ("借款合同", "借贷", "高风险"),**    ("担保合同", "担保", "高风险"),**    ("咨询服务合同", "服务", "低风险"),**    ("投资协议", "投资", "高风险"),**    ("保密协议", "协议", "中风险"),**    ("竞业禁止协议", "协议", "中风险"),**    ("股权转让合同", "转让", "高风险"),**]****# 更多训练数据...**train_data = contracts * 10  # 扩充数据****# 准备数据**X_text = [item[0] for item in train_data]**y_labels = [item[2] for item in train_data]****# 特征提取**vectorizer = TfidfVectorizer()**X = vectorizer.fit_transform(X_text)****# 划分训练集和测试集**X_train, X_test, y_train, y_test = train_test_split(**    X, y_labels, test_size=0.2, random_state=42**)****# 训练模型**model = LogisticRegression()**model.fit(X_train, y_train)****# 预测**y_pred = model.predict(X_test)****print("分类报告：")**print(classification_report(y_test, y_pred))

### 4.2 审计意见分类

# 模拟审计意见数据**audit_opinions = [**    ("财务报表在所有重大方面按照企业会计准则的规定编制，公允反映了公司财务状况。", "标准无保留意见"),**    ("除形成保留意见基础段所述事项的影响外，财务报表在所有重大方面公允反映。", "保留意见"),**    ("公司持续经营能力存在重大不确定性，可能无法在正常经营过程中变现资产。", "无法表示意见"),**    ("财务报表存在重大错报，会计处理不符合企业会计准则的要求。", "否定意见"),**]****# 使用关键词匹配进行简单分类**def classify_opinion(text):**    if "公允" in text and "重大方面" in text and "保留" not in text:**        return "标准无保留意见"**    elif "保留意见" in text or "保留" in text:**        return "保留意见"**    elif "无法表示" in text or "持续经营" in text:**        return "无法表示意见"**    elif "否定" in text or "重大错报" in text:**        return "否定意见"**    else:**        return "其他"****# 测试分类**for opinion, expected in audit_opinions:**    result = classify_opinion(opinion)**    print(f"预期: {expected}, 分类: {result}")

## 五、命名实体识别（NER）

从文本中提取关键实体：人名、地名、组织名、金额、日期等。

### 5.1 使用jieba进行词性标注

import jieba.posseg as pseg****text = "北京科技有限公司与上海贸易公司在2024年1月15日签订了一份金额为500万元的采购合同。"****words = pseg.cut(text)**print("词性标注结果：")**for word, flag in words:**    print(f"  {word}: {flag}")

词性标记说明：
• nr: 人名
• ns: 地名
• nt: 机构名
• t: 时间
• m: 数量词

### 5.2 正则表达式提取实体

import re****contract_text = """**合同编号：HT-2024-001**甲方（委托方）：北京科技有限公司**乙方（受托方）：上海软件开发有限公司**签订日期：2024年1月15日**项目金额：人民币500万元（¥5,000,000）**履约地点：北京市朝阳区**履约期间：2024年2月1日至2024年12月31日**"""****# 提取金额**amounts = re.findall(r'[¥￥]?\s*([\d,]+)\s*(?:万元|元)', contract_text)**print("提取的金额：", amounts)****# 提取日期**dates = re.findall(r'(\d{4}年\d{1,2}月\d{1,2}日)', contract_text)**print("提取的日期：", dates)****# 提取公司名称**companies = re.findall(r'（委托方|受托方）：(.+?)$', contract_text, re.MULTILINE)**print("提取的公司：", [c[1] for c in companies])****# 提取合同编号**contract_id = re.search(r'合同编号[：:]\s*(\S+)', contract_text)**if contract_id:**    print("合同编号：", contract_id.group(1))

## 六、实战案例

### 案例一：合同关键条款提取

import re**import jieba****class ContractAnalyzer:**    def __init__(self, text):**        self.text = text**        self.results = {}****    def extract_amount(self):**        """提取合同金额"""**        # 匹配各种格式的金额**        patterns = [**            r'总[金费用]额[为是：:\s]*([\d,，.]+)\s*(?:万元|万)',**            r'[金费用]额[为是：:\s]*[¥￥]?\s*([\d,]+)\s*(?:万元|万|元)',**            r'¥\s*([\d,]+)',**        ]**        for pattern in patterns:**            match = re.search(pattern, self.text)**            if match:**                amount_str = match.group(1).replace(',', '')**                try:**                    amount = float(amount_str)**                    if '万' in self.text[match.start():match.end()]:**                        amount *= 10000**                    self.results['金额'] = amount**                    return amount**                except:**                    pass**        return None****    def extract_parties(self):**        """提取合同双方"""**        parties = {}**        # 提取甲方**       甲方_match = re.search(r'甲[方方]?[（(]?[^\s）)]+[）)]?\s*[:：]\s*([^\n，。]+)', self.text)**        if 甲方_match:**            parties['甲方'] = 甲方_match.group(1).strip()****        # 提取乙方**        乙方_match = re.search(r'乙[方方]?[（(]?[^\s）)]+[）)]?\s*[:：]\s*([^\n，。]+)', self.text)**        if 乙方_match:**            parties['乙方'] = 乙方_match.group(1).strip()****        self.results['合同主体'] = parties**        return parties****    def extract_dates(self):**        """提取关键日期"""**        dates = {}**        # 签订日期**        sign_date = re.search(r'签订[日期之日][为是：:\s]*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)', self.text)**        if sign_date:**            dates['签订日期'] = sign_date.group(1)****        # 履行期限**        period = re.search(r'履行[期限][为是：:\s]*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?).*?(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)', self.text)**        if period:**            dates['开始日期'] = period.group(1)**            dates['结束日期'] = period.group(2)****        self.results['日期'] = dates**        return dates****    def extract_penalty(self):**        """提取违约条款"""**        penalty = {}**        # 违约金比例**        ratio_match = re.search(r'违约金[为是]?\s*([\d]+)\s*%', self.text)**        if ratio_match:**            penalty['违约金比例'] = ratio_match.group(1) + '%'****        # 违约责任**        liability_match = re.search(r'违约[方任][应应]当?[承担支付]([^\n。]+)', self.text)**        if liability_match:**            penalty['违约责任'] = liability_match.group(1).strip()****        self.results['违约条款'] = penalty**        return penalty****    def analyze(self):**        """执行完整分析"""**        print("=" * 60)**        print("合同分析报告")**        print("=" * 60)****        self.extract_amount()**        self.extract_parties()**        self.extract_dates()**        self.extract_penalty()****        for key, value in self.results.items():**            print(f"\n{key}：")**            if isinstance(value, dict):**                for k, v in value.items():**                    print(f"  {k}: {v}")**            else:**                print(f"  {value}")****        return self.results******# 使用示例**contract_text = """**采购合同****甲方（委托方）：北京科技有限公司**乙方（受托方）：上海贸易有限公司****一、合同标的**乙方向甲方供应XXX设备一批。****二、合同金额**本合同总金额为人民币500万元整（¥5,000,000），含税价格。****三、履行期限**本合同履行期限为2024年2月1日至2024年12月31日。****四、违约责任**如一方违约，违约方应向守约方支付合同总金额20%的违约金。****签订日期：2024年1月15日**"""****analyzer = ContractAnalyzer(contract_text)**results = analyzer.analyze()

### 案例二：合同风险点识别

import re****class ContractRiskAnalyzer:**    def __init__(self):**        # 风险关键词及其风险等级**        self.risk_keywords = {**            '高风险': [**                (r'无限连带', '无限连带责任'),**                (r'抵押[^\s]{0,5}[房车土]', '不动产抵押担保'),**                (r'质押[^\s]{0,5}[股知]', '股权/知识产权质押'),**                (r'回购[^\s]{0,10}义务', '强制回购义务'),**                (r'不竞争', '竞业禁止条款'),**            ],**            '中风险': [**                (r'优先[购选]', '优先购买/选择权'),**                (r'最惠国', '最惠国待遇条款'),**                (r'排他性', '排他性条款'),**                (r'价格调整', '价格调整机制'),**                (r'自动续约', '自动续约条款'),**            ],**            '低风险': [**                (r'争议解决', '争议解决条款'),**                (r'不可抗力', '不可抗力条款'),**                (r'保密', '保密条款'),**                (r'知识产权归属', '知识产权归属'),**            ]**        }****    def analyze_risk(self, text):**        """分析合同风险点"""**        risks = {'高风险': [], '中风险': [], '低风险': []}****        for risk_level, keywords in self.risk_keywords.items():**            for pattern, description in keywords:**                matches = re.findall(pattern, text)**                if matches:**                    for match in matches:**                        risks[risk_level].append({**                            '条款': description,**                            '匹配内容': match if isinstance(match, str) else match[0] if match else '',**                        })****        return risks****    def generate_report(self, text):**        """生成风险分析报告"""**        risks = self.analyze_risk(text)****        print("=" * 60)**        print("合同风险分析报告")**        print("=" * 60)****        total_risks = sum(len(v) for v in risks.values())**        print(f"\n发现 {total_risks} 个风险点：")****        for level in ['高风险', '中风险', '低风险']:**            if risks[level]:**                print(f"\n【{level}】({len(risks[level])}个)")**                for i, risk in enumerate(risks[level], 1):**                    print(f"  {i}. {risk['条款']}")**                    if risk['匹配内容']:**                        print(f"     匹配内容：...{risk['匹配内容']}...")****        if total_risks == 0:**            print("\n未发现明显风险条款")****        # 风险等级建议**        if risks['高风险']:**            print("\n⚠️ 风险评估：高风险，建议法务重点审核")**        elif risks['中风险']:**            print("\n⚠️ 风险评估：中风险，建议关注相关条款")**        else:**            print("\n✓ 风险评估：低风险，条款基本可控")******# 使用示例**contract_text = """**投资协议****甲方（投资者）：XX股权投资基金管理有限公司**乙方（被投资方）：北京科技有限公司****一、投资条款**1. 甲方以现金方式向乙方投资人民币2000万元，占乙方注册资本的10%。**2. 乙方承诺在投资完成后3年内实现IPO，否则甲方有权要求乙方回购甲方持有的全部股份。****二、担保条款**乙方创始人以其持有的全部股权作为质押，为乙方在本协议项下的义务提供担保。****三、竞业禁止**乙方创始人及核心团队成员在投资期间及退出后2年内，不得从事与乙方业务竞争的业务。****四、优先购买权**在乙方进行下一轮融资时，甲方享有优先购买权。****签订日期：2024年1月1日**"""****analyzer = ContractRiskAnalyzer()**analyzer.generate_report(contract_text)

### 案例三：合同相似度比较

from sklearn.feature_extraction.text import TfidfVectorizer**from sklearn.metrics.pairwise import cosine_similarity**import numpy as np****def calculate_similarity(text1, text2):**    """计算两份合同的相似度"""**    # 分词**    import jieba**    text1_seg = ' '.join(jieba.lcut(text1))**    text2_seg = ' '.join(jieba.lcut(text2))****    # TF-IDF向量化**    vectorizer = TfidfVectorizer()**    tfidf_matrix = vectorizer.fit_transform([text1_seg, text2_seg])****    # 计算余弦相似度**    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]****    return similarity****# 示例：比较两份采购合同**contract1 = """**采购合同**甲方：北京科技有限公司**乙方：上海贸易有限公司**采购内容：A产品1000台**合同金额：100万元**履行期限：2024年内**"""****contract2 = """**采购合同**甲方：北京科技有限公司**乙方：深圳贸易有限公司**采购内容：B产品500台**合同金额：80万元**履行期限：2025年内**"""****contract3 = """**租赁合同**甲方：北京物业公司**乙方：XX科技有限公司**租赁内容：办公室500平米**租金：50万元/年**租期：3年**"""****sim_1_2 = calculate_similarity(contract1, contract2)**sim_1_3 = calculate_similarity(contract1, contract3)****print(f"合同1与合同2的相似度：{sim_1_2:.2%}")**print(f"合同1与合同3的相似度：{sim_1_3:.2%}")****if sim_1_2 > 0.5:**    print("\n⚠️ 合同1与合同2相似度较高，建议检查是否存在重复采购或其他关联关系")

## 七、实战作业

1. **环境准备**：
• 安装jieba等NLP库
• 准备几份合同文本进行练习
2. **基础练习**：
• 对合同文本进行分词和词性标注
• 使用正则表达式提取合同中的金额、日期、主体
3. **进阶实践**：
• 实现完整的合同关键条款提取
• 构建合同风险点识别系统
• 对多份合同进行相似度比较

## 总结

今天我们学习了自然语言处理在审计中的应用：

技术
说明
审计应用
分词
将文本切分成词语
文本预处理
TF-IDF
关键词提取
提取合同核心内容
文本分类
自动分类文档
合同分类、审计意见分类
命名实体识别
提取关键实体
提取金额、日期、当事人
风险识别
识别风险关键词
合同风险点识别
文本相似度
计算文本相似程度
发现异常相似合同

NLP技术让审计人员能够处理海量的文本数据，从中发现规律、识别风险。这大大提高了审计效率和覆盖面。

**下期预告**：我们将学习**AI与大模型**——审计智能化新时代。大模型如何帮助审计人员提升效率？有哪些具体应用场景？敬请期待！

如果觉得有帮助，欢迎转发给需要的同事！
