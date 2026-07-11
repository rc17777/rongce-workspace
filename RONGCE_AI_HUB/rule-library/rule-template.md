# 审计规则库标准模板

## 一、单条规则标准颗粒度

每条规则必须小到可以执行、复核、记录效果，不能写成“检查合同风险”“关注资金问题”这种泛化描述。

## 二、规则字段

| 字段 | 是否必填 | 说明 |
|---|---:|---|
| rule_id | 是 | 规则编号，如 JZ-HYJY-001 |
| rule_name | 是 | 规则名称，如“先实施后补议事项识别” |
| module | 是 | 所属模块：M1/M2/M3/M4/M5 |
| audit_type | 是 | 审计类型：经责、预算执行、专项资金、工程、采购、绩效等 |
| risk_topic | 是 | 风险主题：决策程序、资金用途、合同履约、人员资格、围标串标等 |
| rule_level | 是 | A底稿级/B疑点级/C提示级 |
| case_source | 是 | 案例来源、Obsidian 文件、报告、底稿或法规依据 |
| case_summary | 是 | 案例摘要，说明该规则从什么问题抽象而来 |
| problem_pattern | 是 | 问题表现，审计人员看到的异常状态 |
| trigger_terms | 否 | 关键词、短语、异常表达、文本模式 |
| required_data | 是 | 必需资料，如会议纪要、付款台账、合同、人员名单 |
| optional_data | 否 | 辅助资料，如制度、审批单、访谈记录、工商数据 |
| data_fields | 是 | 需要的字段，如日期、金额、供应商、身份证号、摘要 |
| detection_logic | 是 | 可执行判断逻辑 |
| risk_level | 是 | P0/P1/P2/P3 |
| evidence_chain | 是 | 形成底稿或报告所需证据链 |
| audit_action | 是 | 建议核查动作 |
| output_wording | 是 | 疑点输出表述 |
| report_wording | 否 | 可进入报告的问题表述模板 |
| false_positive_note | 否 | 常见误报场景 |
| validation_method | 是 | 如何验证规则有效性 |
| status | 是 | 草稿/试运行/有效/高误报/停用 |
| owner | 否 | 规则维护人 |
| version | 是 | 版本号 |
| last_updated | 是 | 最后更新时间 |

## 三、规则编号规范

```text
<模块>-<场景>-<序号>
```

示例：

| 编号 | 含义 |
|---|---|
| JZ-HYJY-001 | 经责审计-会议纪要-第1条 |
| GC-HT-001 | 工程审计-合同-第1条 |
| YS-PZ-001 | 预算执行-凭证-第1条 |
| BT-RY-001 | 补贴审计-人员-第1条 |
| CG-LT-001 | 采购审计-雷同-第1条 |

## 四、规则模板

```yaml
rule_id: ""
rule_name: ""
module: ""
audit_type: ""
risk_topic: ""
rule_level: ""
case_source: ""
case_summary: ""
problem_pattern: ""
trigger_terms: []
required_data: []
optional_data: []
data_fields: []
detection_logic: ""
risk_level: ""
evidence_chain: []
audit_action: []
output_wording: ""
report_wording: ""
false_positive_note: ""
validation_method: ""
status: "草稿"
owner: ""
version: "v0.1"
last_updated: ""
```

## 五、完整示例

```yaml
rule_id: "GC-HT-001"
rule_name: "验收前提前付款识别"
module: "M2 合同条款抽取与付款异常比对"
audit_type: "工程项目审计/采购审计/专项资金审计"
risk_topic: "合同付款与履约管理"
rule_level: "A底稿级"
case_source: "待绑定：Obsidian案例/历史底稿/法规依据"
case_summary: "案例中合同约定竣工验收合格后付款，但实际付款日期早于验收日期，形成提前付款问题。"
problem_pattern: "合同约定验收后付款，实际在验收前支付全部或部分款项。"
trigger_terms:
  - "验收合格后付款"
  - "竣工验收后支付"
  - "成果交付并验收后"
required_data:
  - "合同文本"
  - "付款台账"
  - "验收报告或验收单"
optional_data:
  - "付款审批单"
  - "项目进度资料"
  - "补充协议"
data_fields:
  - "合同编号"
  - "合同金额"
  - "合同乙方"
  - "付款日期"
  - "付款金额"
  - "验收日期"
detection_logic: "抽取合同付款条件，若合同包含验收后付款表达，且付款日期早于验收日期，则输出疑点；若累计提前付款金额较大，风险等级提高。"
risk_level: "P0/P1，按金额和政策刚性确定"
evidence_chain:
  - "合同付款条款原文"
  - "付款凭证或付款台账"
  - "验收报告/验收单"
  - "付款审批资料"
audit_action:
  - "核实付款审批依据"
  - "核实项目实际履约进度"
  - "访谈项目负责人或财务经办人"
output_wording: "合同约定验收后付款，但系统识别到付款日期早于验收日期，疑似存在提前付款风险。"
report_wording: "XX项目合同约定在验收合格后支付款项，但实际于XX年XX月XX日支付XX万元，早于验收时间XX年XX月XX日，付款管理不符合合同约定。"
false_positive_note: "若存在合法预付款条款、阶段性验收、补充协议调整付款节点，应排除或降级。"
validation_method: "人工核对合同、付款凭证、验收资料，确认时间顺序和付款依据。"
status: "草稿"
owner: ""
version: "v0.1"
last_updated: "2026-07-03"
```

## 六、质量门槛

一条规则进入“有效”状态前，至少满足：

1. 有明确案例来源或法规依据。
2. 所需资料和字段说得清。
3. 检测逻辑能被人工复核。
4. 输出结果能定位到原文或台账记录。
5. 误报场景有说明。
6. 至少经过 1 个项目试运行。

