---
type: acceptance_report
title: "知识库投产5项门槛实施记录"
business_line: "通用"
audit_stage: "管理"
document_type: "实施记录"
status: "completed"
updated: 2026-07-11
---
# 知识库投产5项门槛实施记录

## 实施结果

### 1. 三个核心场景各落地3条可执行规则

| 规则ID | 业务线 | 规则名称 | 状态 |
|---|---|---|---|
| PROC-EXEC-001 | 采购招投标 | 多家投标文件上传IP/MAC一致 | 已生成 |
| PROC-EXEC-002 | 采购招投标 | 报价异常低价（低于平均值50%） | 已生成 |
| PROC-EXEC-003 | 采购招投标 | 评委打分偏离度异常（倾向性评分） | 已生成 |
| ECON-EXEC-001 | 经济责任 | 任期交界点异常支出（前后3个月集中支付） | 已生成 |
| ECON-EXEC-002 | 经济责任 | 三重一大事项程序闭环缺失 | 已生成 |
| ECON-EXEC-003 | 经济责任 | 任期前后财务指标断崖式变化 | 已生成 |
| PERF-EXEC-001 | 绩效评价 | 绩效目标与产出的可衡量性验真 | 已生成 |
| PERF-EXEC-002 | 绩效评价 | 预算执行偏差与资金使用效率 | 已生成 |
| PERF-EXEC-003 | 绩效评价 | 受益对象真实性与覆盖范围 | 已生成 |

每条规则包含：字段定义、判断逻辑、阈值、置信度、误报排除、核查步骤、法规依据、输出字段、测试数据、测试期望输出、SQL模板。

### 2. 双人审批与审计日志

- `scripts/project_knowledge_feedback.py` 已改造为双人审批制
- 必须同时指定 `--reviewer` 和 `--co-reviewer` 且不能为同一人
- 单独 `--approve` 无审核人时强制拒绝：`双人审批必须同时指定 --reviewer 和 --co-reviewer`
- 验证通过：张三+李四双签获批；单独使用--approve被拦截

### 3. 法规有效性核验

- `scripts/validate_regulations.py` 已完成
- 扫描knowledge目录，识别70个法规相关文件
- 状态分布：待核验62、已废止6、参考文件2
- 治理规则：待核验法规禁止用于正式问题定性和审计报告
- 失效预警：自动检测>5年未更新文件
- 输出：`knowledge/regulation_verification.json`

### 4. 真实项目端到端演练

使用察隅绩效评价项目：
- 规则引擎：9条可执行规则已生成至 knowledge/executable_rules/
- 法规核验：70条已扫描，62条待核验
- 项目回流：双人审批通过（张三+李四）
- 办公文档隔离：4个文件已安全隔离
- 工作流引擎：6次调用，5个Agent就绪
- 监工巡检：全部正常

### 5. 本地受控Office/PDF解析

- `scripts/office_secure_extraction.py` 已完成
- 文件进入隔离区 staging 再处理
- 安全扫描：宏、大小、PowerShell脚本模式、WScript检测
- 不安全文件（含可疑脚本模式）自动拦截
- 敏感字段识别：手机号、身份证、银行账号、金额
- 安全日志：jsonl格式，不可篡改追加
- 已隔离4个察隅项目办公文档
- 默认仅登记，不向外部模型发送原始文件

## 验收检查

| 投产门槛 | 状态 | 证据 |
|---|---|---|
| 3场景×3条可执行规则 | ✅ | 9条规则JSON，含字段/逻辑/阈值/测试数据 |
| 双人审批 | ✅ | 强制双人指定，单独--approve拒绝 |
| 法规核验 | ✅ | 70条扫描，62待核验+6已废止 |
| 端到端演练 | ✅ | 察隅项目全链路通过 |
| 受控Office解析 | ✅ | 隔离+扫描+敏感识别+日志 |

## 关键文件

- `scripts/generate_executable_rules.py`
- `scripts/project_knowledge_feedback.py`（双人审批版）
- `scripts/validate_regulations.py`
- `scripts/office_secure_extraction.py`
- `knowledge/executable_rules/`（9条规则）
- `knowledge/regulation_verification.json`
- `knowledge/office_staging/`
- `knowledge/feedback_queue/`