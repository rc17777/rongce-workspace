---
name: "financial-fraud-detection"
description: >
  财务造假检测工具 — Benford定律数字分布检验 + 异常交易模式识别。用于国企审计、专项资金审计、政府采购审计中的凭证/流水/发票金额异常检测。Triggers: '财务造假', 'Benford', 'Benford定律', '本福特定律', '虚假发票', '虚列支出', '人为操纵'.
business_line: "通用审计方法"
methods: "Benford定律; 异常交易检测; 数字分布分析"
difficulty: "高级"
keywords: "财务造假, Benford, 虚假发票, 虚列支出, 人为操纵"
status: "stable"
---

# Financial Fraud Detection — 财务造假筛查

## 概述

基于Benford定律（本福特定律）的财务数据金额分布检验工具。适用于国企审计、政府采购审计、专项资金审计中的大额凭证抽查。

## 使用

**Node.js版本**（推荐，本机可用）:
```bash
cd scripts/
node benford_detector.js --input 凭证明细.xlsx
node anomaly_patterns.js --input 采购明细.xlsx --method zscore
```

**Python版本**（通用环境）:
```bash
pip install pandas numpy openpyxl scipy
python benford_detector.py --input 凭证明细.xlsx --output ./result/
python benford_detector.py --input 差旅费.xlsx --amount-col 报销金额
```

## 核心检测方法

### ① Benford首位数字分布（主检测）

对比凭证金额首位数字分布 vs Benford理论分布，卡方检验p<0.05即为**可能存在人为操纵**。

| 首位数字 | Benford理论% | 正常数据% | 人为伪造数据% |
|:--------:|:-----------:|:---------:|:-------------|
| 1 | 30.1% | ~28-32% | ~11-15% |
| 2 | 17.6% | ~16-19% | ~10-12% |
| ... | ... | ... | ... |
| 9 | 4.6% | ~3-6% | ~8-12% |

### ② 圆整交易检测

金额为千元整数的交易（10,000/20,000/500,000等）。自然发生的交易很少恰好是整数，大量圆整交易往往意味着**人为构造**。

### ③ 末位数字分布

正常数据末位数字应接近均匀分布（~10%）。金额末位大量出现0或5，属于人为构造痕迹。

## 脚本列表

| 脚本 | 用途 |
|:----|:-----|
| `benford_detector.py` | Benford首位数字分布 + 圆整交易 + 末位分布 |
| `anomaly_patterns.py` | 异常交易模式检测（IQR/Z分/Isolation Forest）+ 时间模式 + 临近限额 |

## 输出

- `Benford分布分析.xlsx` — 9个数字的分布对比表
- `疑点_圆整交易.xlsx` — 千元倍数的圆整交易清单
- `分析_金额末位分布.xlsx` — 末位数字分布表
- `疑点_金额异常.xlsx` — IQR/Z分/Isolation Forest检测的异常金额
- `疑点_交易模式.xlsx` — 周末交易/深夜交易/临近限额交易等模式

## 适用审计场景

1. **国企审计**: 差旅费/办公费/会议费凭证全面筛查
2. **政府采购**: 大额采购发票与支付金额分布检测
3. **专项资金**: 惠农补贴/扶贫资金支付金额异常检测
4. **医保基金**: 医疗机构结算数据是否存在虚假报销
5. **预算执行**: 年底突击花钱等异常支出模式识别

## 参考

群众语言堂公众号《国有企业审计大数据技术超详细操作》
