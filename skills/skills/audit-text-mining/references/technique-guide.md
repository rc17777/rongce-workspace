# 审计文本挖掘技术详解

> 来源：《中国审计》2023年第20期
> 作者：安徽省怀宁县审计局 何红兵

## 场景背景

某国家级经济技术开发区领导干部经济责任审计：
- 体量庞大，区属二级机构和国有企业众多
- 审计时间跨度大（多年）
- 资料类型复杂：合同文档、会议纪要、工作报告、财务报表等

**审计准备阶段三大难点**：
1. 看不清审计对象（资料太多，不知道被审计单位到底在做什么）
2. 抓不住审计重点（不知道应该关注哪些事项）
3. 找不到审计疑点（无法从海量文档中定位风险线索）

## 技术方案

### 技术栈

| 库 | 用途 | 安装 |
|----|------|------|
| `win32com` | .doc → .docx 格式转换 | `pip install pywin32` |
| `python-docx` | 读取.docx段落文本 | `pip install python-docx` |
| `jieba` | 中文分词 | `pip install jieba` |
| `re` | 正则表达式匹配 | Python内置 |
| `pandas` | 数据结构化+Excel导出 | `pip install pandas` |
| `wordcloud` | 词云可视化 | `pip install wordcloud` |
| `matplotlib` | 词云渲染 | `pip install matplotlib` |
| `openpyxl` | Excel写入 | `pip install openpyxl` |
| `glob` | 目录遍历 | Python内置 |

### 格式转换

部分Word文档为旧版 .doc 格式，python-docx 只能处理 .docx。需要用 win32com 批量转换。

关键代码：
```python
import win32com.client as win32
word = win32.Dispatch("Word.Application")
doc = word.Documents.Open(doc_path)
doc.SaveAs2(new_path, FileFormat=16)  # 16 = wdFormatXMLDocument
doc.Close()
```

> ⚠️ win32com 依赖本机安装 Microsoft Word。如无 Word，可考虑用 LibreOffice 命令行替代。

### 分词与词频统计

```python
import jieba
words = jieba.cut(text)
# 过滤：长度>1、非纯数字、非停用词
filtered = [w for w in words if len(w)>1 and w not in stopwords]
```

### 多关键词批量定位

核心思路：
1. 用正则 `|` 连接多个关键词
2. 遍历每个文档的每个段落
3. 匹配关键词前后各取N个字作为上下文
4. 汇总导出Excel

```python
pattern = re.compile("|".join(re.escape(kw) for kw in keywords))
for match in pattern.finditer(paragraph_text):
    start = max(0, match.start() - context_chars)
    end = min(len(text), match.end() + context_chars)
    context = text[start:end]
```

## 审计发现

通过词云锁定关键词后批量定位，揭示了该开发区五大问题：

1. **对外出借财政资金** → 关键词"借款"
2. **以奖励形式返还税收** → 关键词"奖励"+"税收"
3. **未按规定程序改变规划** → 关键词"规划"
4. **违规调整土地用途** → 关键词"土地"
5. **拆迁安置严重滞后** → 关键词"安置"

## 与传统方法的对比

| 维度 | Word查找功能 | Python方案 |
|------|------------|-----------|
| 多关键词 | 一次只能查一个 | 一次查多个 |
| 跨文档 | 逐文件打开查找 | 批量自动处理 |
| 上下文 | 需手动查看 | 自动提取前后N字 |
| 结果导出 | 需手动复制 | 一键导出Excel |
| 词频统计 | 不支持 | 支持，可出词云 |

## 实施建议

1. **先看词云，再定位**：词云帮助识别方向，避免盲目搜索
2. **停用词要不断迭代**：首次分析后把无价值的词加入停用词，第二次分析更精准
3. **上下文长度可调**：默认50字适合快速浏览，如需深入判断可设100-200字
4. **结合业务知识解读词云**：高频词不代表都是问题，需要审计人员的专业判断
