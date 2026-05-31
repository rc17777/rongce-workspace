---
name: audit-data-analysis-methods
description: "7大审计数据分析方法 — 从描述性统计到时间序列分析的完整Python工具库。基于群众语言堂公众号《七大核心方法玩转审计数据分析》。Triggers: '数据分析方法', '描述性统计', '相关性分析', '回归分析', '聚类', '异常检测', '关联规则', '时间序列'."
---

# Audit Data Analysis — 7大审计数据分析方法

## 概述

7种核心数据分析方法，每种均配有Python代码和直接可用的审计场景。来源为公众号"群众语言堂"《七大核心方法玩转审计数据分析》。

## 方法一览

| 编号 | 方法 | 脚本 | 审计价值 |
|:---:|:----|:-----|:---------|
| 01 | 描述性统计 | `index.js 01` | 快速摸清数据特征、发现异常区间 |
| 02 | 相关性分析 | `index.js 02` | 验证变量间关系是否合逻辑 |
| 03 | 回归分析 | `index.js 03` | 建立预测模型，识别异常偏离 |
| 04 | 聚类分析 | `index.js 04` | 供应商/客户自动分群定位高风险 |
| 05 | 异常检测 | `index.js 05` | IQR/Z分法找出害群之马 |
| 06 | 关联规则 | `index.js 06` | 发现高频风险组合模式 |
| 07 | 时间序列 | `index.js 07` | 趋势和季节分析，发现异常波动 |

## 环境

**Node.js版本**（推荐，本机可用）:
```bash
cd scripts/
npm install
# 依赖: csv-parse + exceljs，已安装
```

**Python版本**（在正常Python 3.9~3.12环境可用）:
```bash
pip install pandas numpy openpyxl scikit-learn scipy matplotlib
```

## 核心逻辑图

```
原始数据
    │
    ▼
Describe ───→ 平均值/中位数/标准差 → 费用水平是否正常
    │
    ▼
Correlate ──→ 成本vs产量是否正相关
    │
    ▼
Regress ────→ 建立预测模型 → 实际偏离>2倍RMSE即为疑点
    │
    ▼
Cluster ────→ 供应商分群 → 高风险群自动标注
    │
    ▼
Detect ─────→ IQR/Z分法 → 异常交易清单
    │
    ▼
Associate ──→ 找出"周末+大额+指定供方"等打包风险
    │
    ▼
Forecast ───→ 月度收入季节指数 → 偏离>20%的月份
```

## 快速使用

```bash
cd scripts/

# 描述性统计：分析费用数据
node index.js 01 --input 费用表.xlsx --column 金额

# 聚类分析：供应商风险分群（K-Means）
node index.js 04 --input 供应商表.xlsx --clusters 4

# 异常检测：Z分法找出异常采购
node index.js 05 --input 采购明细.xlsx --column 金额 --method zscore

# 关联规则：审批异常模式挖掘
node index.js 06 --input 采购审批.xlsx --columns 审批人,时间,金额区间

# 时间序列：收入趋势和季节性
node index.js 07 --input 月度收入.xlsx --date-col 月份 --value-col 收入
```

**Python版**（通用环境）:
```bash
python 01_descriptive_stats.py --input 费用表.xlsx --column 金额
python 05_anomaly_detection.py --input 采购明细.xlsx --method isolation_forest
```

## SCQA报告框架（数据分析报告撰写指南）

来源：群众语言堂《数据分析报告撰写：让数据从「好看」到「有用」》(2026-04-17)

### SCQA四步法

| 步骤 | 含义 | 审计报告对应写法 |
|:----|:-----|:----------------|
| **S**ituation 情境 | 业务背景，1-2段 | "按照审计计划，我们对XX单位XXXX年度XX资金进行了专项审计" |
| **C**omplication 冲突 | 问题痛点，数据支撑 | "发现违规金额XXX万元。其中XX方面XX万元，同比上升XX%" |
| **Q**uestion 问题 | 报告要回答的核心 | "资金被挪用到了哪里？内控制度是否存在漏洞？" |
| **A**nswer 答案 | 数据发现+行动建议 | 具体问题清单 + 可量化的整改建议 |

### 审计报告三段论

1. **发生了什么** → 数据描述（预算执行率/资金流向/异常比例）
2. **为什么会这样** → 原因分析（回款慢/项目拖期/内控缺位）
3. **该怎么做** → 整改建议（具体可量化，如"建议建立XX机制，预计减少XX损失"）

### 数据可视化原则

- **一图一意**：一张图表只表达一个核心观点
- **标题即结论**：不写"XX单位预算执行情况"，写"预算执行率仅65%，系项目推进缓慢所致"
- **删减不必要元素**：去掉背景色/网格线/三维效果，保留的每个元素都服务于信息传达
- **配色**：主色调3-4种（企业蓝+警示橙+异常红），避免红绿搭配
|:----|:-----|:----------------|
| **S**ituation 情境 | 业务背景，简洁交代 | 
