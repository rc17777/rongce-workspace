# Batch 4 审计算法提取总结

## 概览

- **轮次**：第 4 轮（前 3 轮累积 114 个算法）
- **新增算法**：**21 个**
- **输出**：`batch_algorithms_batch4.json`
- **日期**：2026-08-06

---

## 知识源与产出

### 源 1：2026 年 财政监督杂志 PDF（OCR 文本）

路径：`D:\杂志资料\财政监督\articles\`（196 篇 OCR 转 MD）

从中提取 **12 个算法**：

| SN | 名称 | 领域 | 来源期数 |
|:--|:--|:--|:--|
| EINV-CROSS-001 | 电子发票多源融合稽核 | 财务收支 | 2026.1 |
| EXPSTD-CHECK-001 | 经费类支出标准符合性评审 | 预算评审 | 2026.1 |
| HOSP-PARAM-001 | 公立医院采购围标串标识别 | 医疗采购 | 2026.9 |
| BID-ROTATE-001 | 互惠型陪标轮庄识别 | 招投标 | 2026.11 |
| CONCESS-DEBT-001 | 特许经营项目化债风险穿透 | 政府债务 | 2026.2 |
| TAX-ESCAPE-001 | 逃逸式注销+非交易过户税源追征 | 税务 | 2026.5 |
| WAT-CONSTR-001 | 水利项目资金归集挪用监管 | 基建 | 2026.9 |
| WHISTLE-FLOW-001 | 财会监督举报受理闭环 | 财会监督 | 2026.7 |
| COUNTY-RISK-001 | 县域财政风险预警指标体系 | 财政监督 | 2026.2 |
| PERF-COST-001 | 运转类项目成本预算绩效分析 | 绩效评价 | 2026.5 |
| CONCESS-FEE-001 | 特许经营费用测算四维框架 | 特许经营 | 2026.10 |
| INV-APPROVAL-001 | 政府投资规避审批与概算约束识别 | 投资 | 2026.11 |

### 源 2：政策法规入库文件（_incoming）

路径：`C:\Users\scrccpa\.openclaw\workspace\knowledge\laws\_incoming\`（11 篇审计方法 MD）

从中提取 **9 个算法**：

| SN | 名称 | 领域 |
|:--|:--|:--|
| LOSS-PENETRATE-001 | 亏损项目六步穿透法 | 国企审计 |
| VENDOR-VERIFY-001 | 供应商虚假材料三查核验 | 招投标 |
| HR-EATEMPTY-001 | 吃空饷五对照核查 | 经责审计 |
| TRAVEL-SIGNAL-001 | 差旅费四信号自动筛查 | 收支审计 |
| BID-DARKMARK-001 | 暗标技术标隐形记号检测 | 电子招投标 |
| WATER-SQL-001 | 水费征收SQL三查 | 公用事业 |
| EMPLOY-SUB-001 | 就业补助资金九项疑点SQL筛查 | 民生审计 |
| NATRES-AUDIT-001 | 自然资源资产离任审计五维问题清单 | 资源环境 |
| ASSET-REVIVE-001 | 闲置资产盘活效益评估 | 国有资产 |

### 源 3：书籍

路径：`C:\Users\scrccpa\Documents\My eBooks\My Bookcase`

**无内容**（目录为空），未产出算法。

---

## 复杂度分布

| 复杂度 | 数量 | 说明 |
|:--|:--|:--|
| L2（规则/统计） | 9 | 标准比对、信号筛查、SQL 查询 |
| L3（多源交叉） | 10 | 跨系统交叉比对、资金穿透、GIS 叠加 |
| L4（模型/算法） | 2 | 化债风险穿透、六步穿透法 |

---

## 与前 3 轮的差异化

- **全新场景**：电子发票稽核（EINV-CROSS）、暗标隐形记号检测（BID-DARKMARK）、逃逸式注销追征（TAX-ESCAPE）、水利资金归集（WAT-CONSTR）、就业补助 SQL 筛查（EMPLOY-SUB）
- **方法创新**：特许经营"化债+费用测算"双卡（CONCESS-DEBT + CONCESS-FEE）、投资审批 2026 新规"规避识别+概算约束+终身负责"（INV-APPROVAL）、亏损项目"真假亏损三把尺子"（LOSS-PENETRATE）
- **SQL 模板**：水费征收（WATER-SQL）和就业补助（EMPLOY-SUB）含可直接执行的 SQL 审计逻辑

---

## 已避免的重复

以下领域已有的 SN 已避开，或在 novelty 字段说明与已有算法的互补关系：

- **医疗采购**：HOSP-PARAM-001 与 MED-BIDRIG-001 互补（本卡聚焦"排他性参数+资金同源+隐性回补"三段式）
- **陪标**：BID-ROTATE-001 与 BID-PATTERN-005 互补（本卡聚焦"跨项目轮流中网闭环"）
- **差旅费**：TRAVEL-SIGNAL-001 与 SUPV-TRAVEL-001 互补（本卡给出四条可 SQL 化硬信号）
- **供应商材料**：VENDOR-VERIFY-001 与 PROC-FAKE-001 互补（本卡固化三平台核验渠道）
- **税务**：TAX-ESCAPE-001 与 TAX-001 互补（本卡聚焦"注销-过户"两步链路）

---

## 累计统计

| 轮次 | 数量 | 文件 |
|:--|:--|:--|
| Batch 1 | ~30 | batch_algorithms_batch1.json |
| Batch 2 | ~39 | batch_algorithms_batch2.json |
| Batch 3 | 15 | batch_algorithms_batch3.json |
| **Batch 4** | **21** | batch_algorithms_batch4.json |
| **合计** | **~135** | — |
