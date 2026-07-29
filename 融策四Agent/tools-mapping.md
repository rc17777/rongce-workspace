# 现有工具 → Agent 分配矩阵

> 基于融策审计智析Agent v3-v12全栈工具资产
> 版本：v1.0 | 2026-07-11

---

## 工具清单全量

| # | 工具 | 文件 | 行数 | v版本 | 分配 |
|---|------|------|------|-------|------|
| 1 | text_hotword_analysis | tools/audit_text_analysis/ | ~300 | v4 | 审 |
| 2 | text_similarity_compare | tools/audit_text_analysis/ | ~350 | v4 | 审 |
| 3 | contract_field_extract | tools/audit_text_analysis/ | ~400 | v4 | 审 |
| 4 | personnel_profile_check | tools/audit_text_analysis/ | ~250 | v4 | 审 |
| 5 | budget_compliance_scan | tools/audit_text_analysis/ | ~350 | v4 | 审 |
| 6 | benford_analysis | tools/audit_text_analysis/benford.py | ~350 | v7 | 审 |
| 7 | supplier_fingerprint | tools/audit_text_analysis/supplier_fingerprint.py | ~420 | v7 | 审 |
| 8 | timeline_anomaly | tools/audit_text_analysis/timeline_anomaly.py | ~300 | v7 | 审 |
| 9 | contract_change_trajectory | tools/audit_text_analysis/contract_change_trajectory.py | ~500 | v7 | 审+工 |
| 10 | bid_rigging_detector | tools/ | ~600 | v9 | 审+工 |
| 11 | evidence_chain_graph | tools/ | ~540 | v9 | 审+工 |
| 12 | three_flow_checker | tools/ | ~330 | v11 | 审 |
| 13 | data_script_generator | tools/ | — | v6 | 审+工 |
| 14 | duplicate_claim_detector | tools/ | — | v8 | 审 |
| 15 | context_window_monitor | tools/ | — | v8 | 监 |
| 16 | human_review_rules | tools/ | — | v6 | 监 |
| 17 | throughput_benchmark | tools/ | — | v6 | 监 |
| 18 | flip_voucher (AP/AR/EXP/FA) | agent_config.py | — | v8 | 审 |
| 19 | 定性模板库 (5套) | agent_config.py | — | v11 | 审 |
| 20 | arithmetic_cross_checker (4场景) | — | — | v12 | 审+工 |

---

## 按Agent汇总

### 融策审计（11个专属 + 3个共享）

| 专属 | 共享 |
|------|------|
| text_hotword_analysis | contract_change_trajectory |
| text_similarity_compare | bid_rigging_detector |
| contract_field_extract | evidence_chain_graph |
| personnel_profile_check | data_script_generator |
| budget_compliance_scan | arithmetic_cross_checker (专项/绩效规则包) |
| benford_analysis | |
| supplier_fingerprint | |
| timeline_anomaly | |
| three_flow_checker | |
| duplicate_claim_detector | |
| flip_voucher (4场景) | |

### 融策工程咨询（0个专属 + 5个共享 + 待建）

| 共享 | 待建 |
|------|------|
| contract_change_trajectory (工程视角) | five_stage_comparison（五算对比引擎） |
| bid_rigging_detector (投标视角) | quantity_verification（工程量清单核对） |
| evidence_chain_graph | quota_validation（定额套用审查） |
| data_script_generator | material_price_adjustment（材料调差） |
| arithmetic_cross_checker (工程/年报规则包) | change_order_audit（变更签证审核） |
| | progress_payment_check（进度款核验） |
| | report_parser（鉴定意见书模板） |

### 融策知识（无工具，纯采集+归档+推送）

### 融策监督（3个专属）

- human_review_rules
- throughput_benchmark
- context_window_monitor

---

## 优先级

| 优先级 | 内容 | 工期 |
|--------|------|------|
| P0 | 工程咨询5个待建工具（五算对比/清单核对/定额审查/材料调差/变更签证） | 25天 |
| P0 | 进度款核验工具 | 5天 |
| P1 | 鉴定意见书模板生成器 | 3天 |
| P1 | 知识Agent自动采集流水线 | 10天 |
| P1 | 消息队列与Agent间通信基础设施 | 8天 |
| P2 | 融策监督L2独立评审模型微调 | 15天 |
| P2 | 全流程监控看板 | 5天 |

**待建总计：71天**
