---
name: "engineering-audit"
description: >
  工程竣工决算财务审计技能 — 融策12大业务线之「工程竣工决算财务审计」，对接融策工程咨询公司。四维检测：变更签证合理性/造价偏差分析/进度款匹配/项目合规性。触发词：工程审计、竣工决算、工程结算、造价审计、变更签证。
business_line: "工程竣工决算财务审计"
methods: "核对法; 造价分析; 合规审查; 进度匹配"
difficulty: "高级"
keywords: "工程审计, 竣工决算, 变更签证, 造价审计, 工程财务"
status: "reviewed"
---

# engineering-audit — 工程竣工决算财务审计

> 融策12大业务线之「工程竣工决算财务审计」
> 支撑资料：按类型/投资审计8篇 + 审计案例8篇 + 政监8篇 + 中国审计1篇=25篇
> 对接：融策工程咨询公司（预算编制/财政评审/全过程工程咨询/工程结算）

## 触发条件
`工程审计` `竣工决算` `工程结算` `造价审计` `变更签证` `工程财务`

## 四维检测

```
变更签证合理性 ──→ 造价偏差分析 ──→ 进度款匹配 ──→ 项目合规性
(dim1)           (dim2)           (dim3)          (dim4)
```

## 模块

### dim1 — 变更签证合理性
- **检测**: 变更频率(同一标段>/中标金额比例>/变更原因聚类)
- **输入**: 变更签证台账.xlsx + 中标合同.xlsx
- **输出**: `change_order_anomalies.xlsx`

### dim2 — 造价偏差分析
- **检测**: 清单项单价偏离(市场价vs中标价)/工程量偏差/材料价差
- **输入**: 工程量清单.xlsx + 市场价参考.xlsx + 结算书.xlsx
- **输出**: `cost_deviation_anomalies.xlsx`

### dim3 — 进度款vs形象进度匹配
- **检测**: 支付比例vs监理确认进度/超付/预付款未扣回
- **输入**: 进度款支付表.xlsx + 监理月报进度
- **输出**: `progress_payment_anomalies.xlsx`

### dim4 — 项目合规性
- **检测**: 超概算/未招标先施工/合同签订滞后/履约保函缺失/分包违规
- **输入**: 项目基本信息表.xlsx + 招标文件.xlsx + 合同台账.xlsx
- **输出**: `compliance_anomalies.xlsx`

## 使用方式

```bash
python dim1_change_order.py -c 变更台账.xlsx -b 中标合同.xlsx
python dim2_cost_deviation.py -b 清单.xlsx -m 市场价.xlsx -s 结算书.xlsx
python dim3_progress_payment.py -p 进度款.xlsx -r 监理月报.xlsx
python dim4_compliance.py -i 项目基本信息.xlsx -w 招标文件.xlsx
python run_all.py --data ./审计数据/
```
