---
name: "energy-audit"
description: >
  能源审计技能 — 融策12大业务线之「能源审计」（含碳中和审计/核查）。双模块：能耗单耗核查+碳排放核算。触发词：能源审计、碳排放、碳中和、节能、资源环境、能耗。
business_line: "能源审计"
methods: "比率分析; 基准对标; 碳排放核算"
difficulty: "中级"
keywords: "能源审计, 碳排放, 碳中和, 节能, 资源环境, 能耗"
status: "draft"
---

# energy-audit — 能源审计

> 融策12大业务线之「能源审计」（含碳中和审计/核查）
> 支撑资料：按类型/资源环境审计7篇 + 审计案例7篇 + 政监1篇=15篇
> 定位：🟡拓展业务，轻量级技能

## 触发条件
`能源审计` `碳排放` `碳中和` `节能` `资源环境` `能耗` `能源`

## 双模块

### dim1 — 能耗单耗核查
- **检测**: 单位产品能耗vs行业基准 / 能耗总量vs产能匹配 / 能耗数据波动
- **输入**: 能耗统计表.xlsx + 产量台账.xlsx
- **阈值**: 能耗偏离行业基准>20%🔴 / 同比波动>30%🟡
- **输出**: `energy_consumption_anomalies.xlsx`

### dim2 — 碳排放核查
- **检测**: 碳排放报告vs能耗推算 / 减排量真实性 / 碳配额盈余合理性
- **输入**: 碳排放报告.xlsx + 能耗统计表.xlsx
- **输出**: `carbon_emission_anomalies.xlsx`

## 使用方式

```bash
python dim1_energy_consumption.py -e 能耗统计.xlsx -p 产量台账.xlsx --sector 水泥
python dim2_carbon_emission.py -c 碳排放报告.xlsx -e 能耗统计.xlsx
```

## 行业基准（嵌入）

| 行业 | 综合能耗(kgce/单位) | 来源 |
|------|:---:|------|
| 水泥(熟料) | ≤117 kgce/t | GB16780-2021 |
| 钢铁(粗钢) | ≤560 kgce/t | GB21256 |
| 化工(合成氨) | ≤1420 kgce/t | GB21344 |
| 火电(供电) | ≤300 gce/kWh | GB21258 |
| 建筑(公建) | ≤80 kWh/m²·a | GB50189 |
