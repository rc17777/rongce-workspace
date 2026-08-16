---
name: rongce-platform
description: >
  融策统一审计平台，提供数据基座管理 + 9个核心分析模型。
  当用户需要：运行审计分析模型、查看数据基座状态、初始化审计数据平台、费用舞弊分析、
  预算执行分析、资金异常检测、审计风险排序、跨坐标系交叉验证时使用。
  触发词：数据基座、审计模型、费用舞弊、预算执行、资金异常、风险排序、平台初始化、
  出差考勤比对、受益对象重复、进销存比对、报价分析。
---

# 融策统一审计平台

## 概述

基于《数据基座与审计模型》规划实现的审计分析平台，包含：

1. **统一数据基座** — SQLite 数据库（9个数据源 + 39条风控规则 + 18个模型定义）
2. **15个模型脚本** — 4个基础模型 + 8个跨坐标系模型 + 3个替代方案模型（2026-07新增）
3. **数据基座管理** — 初始化、质量报告、数据注册

## 使用方式

```bash
# 初始化数据基座
py skills/rongce-platform/index.py init

# 运行原有模型（示例数据）
py skills/rongce-platform/index.py run 费用舞弊
py skills/rongce-platform/index.py run 预算执行
py skills/rongce-platform/index.py run 资金异常
py skills/rongce-platform/index.py run 风险排序
py skills/rongce-platform/index.py run 全部

# 运行跨坐标系模型（示例数据）
py skills/rongce-platform/cross_coordinate_audit.py sample

# 或通过 index.py 统一调用
py skills/rongce-platform/index.py run 出差
py skills/rongce-platform/index.py run 受益
py skills/rongce-platform/index.py run 进销存
py skills/rongce-platform/index.py run 报价
py skills/rongce-platform/index.py run 时间序列

# 真实数据
py skills/rongce-platform/cross_coordinate_audit.py M101 --file 报销门禁数据.csv
py skills/rongce-platform/cross_coordinate_audit.py M103 --file 进销存数据.csv

# 列出模型
py skills/rongce-platform/index.py list

# 数据基座状态
py skills/rongce-platform/index.py status
```

## 模型详解

### M001 费用舞弊风险模型 (`expense_fraud_model.py`)
- 8条规则：大额整数、连号发票、高频小额、节假日、超标准、关联方、异常时间、重复报销
- 三级风险：极高(>=60分) / 高(>=40分) / 中(>=20分) / 低
- 支持 CSV 批量导入评分，输出 JSON 报告

### M004 预算执行分析模型 (`budget_analysis.py`)
- 执行率偏差检测：<50%执行不足、>120%超预算、=0%完全未执行
- 年底突击花钱检测：Q4占比>50% 或 Q4>Q1x3
- 季度波动异常检测：变异系数>0.8
- 支持按年份过滤

### M005 资金异常流动检测 (`fund_flow_model.py`)
- 资金回流检测（A-B-A两步闭环）
- 大额拆分检测（同日多笔累加）
- 异常时段交易（22:00-06:00大额）
- 高频交易对检测
- 跨区域异常检测

### M006 审计风险排序模型 (`audit_risk_ranking.py`)
- 7维评分：财务舞弊(25%) + 预算偏差(20%) + 内控(15%) + 历史问题(15%) + 资金规模(10%) + 社会关注(10%) + 整改(5%)
- 自定义权重支持
- 自动排序生成审计优先级清单

### 🆕 M101 出差x考勤时空验证 (`cross_coordinate_audit.py`)
- **坐标系**：时空
- **功能**：报销出差日期 x 门禁/打卡记录交叉比对
- **输出**：出差期间在本单位打卡的冲突天数、具体记录、风险等级
- **适用**：预算执行审计、经济责任审计

### 🆕 M102 受益对象重复检测 (`cross_coordinate_audit.py`)
- **坐标系**：时空x社会关系
- **功能**：同身份证/同地址/同银行账号多次享受补贴检测
- **输出**：按重复维度（身份证/银行账号/地址）分组的异常清单
- **适用**：专项资金审计、两新补贴审计

### 🆕 M103 进销存三向比对 (`cross_coordinate_audit.py`)
- **坐标系**：物理
- **功能**：期初+进货-期末=理论最大可销量 vs 申报销量
- **输出**：缺口数量、缺口百分比、风险等级、核查建议
- **适用**：两新补贴审计、专项资金审计

### 🆕 M104 报价行为模式分析 (`cross_coordinate_audit.py`)
- **坐标系**：行为
- **功能**：等差/等比报价检测、精准控价检测、报价区间过窄检测
- **输出**：每个项目的行为异常信号及组合风险
- **适用**：政府采购审计、招投标审计

### 🆕 M105 时间序列矛盾检测 (`cross_coordinate_audit.py`)
- **坐标系**：时间序列
- **功能**：合同/公告/验收/付款日期的先后顺序逻辑验证
- **输出**：日期矛盾点、法定时限检测、异常节奏信号
- **适用**：政府采购审计、投资审计

### 🆕 M106 街景时空验证 (`cross_coordinate_audit.py`)
- **坐标系**：时空
- **功能**：验收照片时间地点 × 百度街景历史影像比对
- **输出**：风险预判信号 + 一键街景查询链接 + 人工比对操作清单
- **适用**：投资审计、政府采购验收审计

### 🆕 M107 卫星图进度验证 (`cross_coordinate_audit.py`)
- **坐标系**：时空
- **功能**：卫星/航拍历史影像 × 申报施工进度交叉验证
- **输出**：付款vs进度偏差 + Google Earth/Sentinel/天地图查询指引
- **适用**：投资审计、专项资金绩效审计

### 🆕 M108 工程量反推 (`cross_coordinate_audit.py`)
- **坐标系**：物理
- **功能**：8类建材（混凝土/钢筋/水泥/砂石/沥青/苗木等）用量反推工程量
- **输出**：每种材料的反推值 vs 申报值、差距百分比、交叉印证
- **适用**：投资审计、工程结算审计

### 🆕 M109 OA登录IP×出差验证 (`cross_coordinate_audit.py`) — 替代方案
- **坐标系**：时空（手机信令的零成本替代）
- **功能**：出差期间从内网IP登录OA/财务系统操作检测
- **输出**：冲突天数、操作明细（区分OA浏览/审批/财务制单的敏感度分级）
- **适用**：预算执行审计、经济责任审计

### 🆕 M111 凭证制单行为分析 (`cross_coordinate_audit.py`) — 替代方案
- **坐标系**：行为（审批行为画像的零成本替代）
- **功能**：一人多角色/深夜制单/审核秒批/大额单人操作/月末突击
- **输出**：异常凭证清单 + 制单人行为画像（自审率/金额集中度）
- **适用**：所有审计类型通用

### 🆕 M113 材料进场×施工日志 (`cross_coordinate_audit.py`) — 替代方案
- **坐标系**：物理（探地雷达的零成本替代第一层）
- **功能**：施工日志的工程活动 vs 材料进场记录的物理支撑验证
- **输出**：混凝土/钢筋进场量缺口、实际 vs 施工日志使用量差异
- **适用**：投资审计、工程审计

## 数据基座表结构

| 表 | 用途 |
|----|------|
| data_sources | 数据源注册（9个预装） |
| data_tables | 数据表册 |
| field_dictionary | 字段标准字典 |
| data_quality_logs | 数据质量日志 |
| data_lineage | 数据血缘 |
| audit_projects | 审计项目 |
| audit_findings | 审计发现 |
| analysis_models | 分析模型注册（12个预装） |
| model_run_logs | 模型运行记录 |
| risk_rules | 风险规则库（39条：15条原有+24条E系列） |
| standard_accounts | 标准科目 |
| standard_units | 标准单位 |

## 关联

- **rongce-gov-audit** — 政府审计主技能，调用本平台的模型进行风险分析
- **audit-data-analyst** — 审计数据分析，与本平台共用数据基座
- **bid-collusion-audit** — 串标围标审计，扩展本平台的政府采购模型
- **cross-coordinate-audit-methods** — 跨坐标系方法论文档，本平台 M101-M105 的可执行实现
- **case-quality-criteria** — 案例质量标准，本平台输出的高价值发现经5标准筛选后入库
