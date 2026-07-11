# 融策审计智析Agent v5.0.0 — 快速上手指南

> 所有代码位于 `tools/audit_text_analysis/`
> 运行前提：`pip install scikit-learn jieba numpy`

---

## 一、三个层次的使用方式

| 层次 | 适合场景 | 入口 |
|---|---|---|
| 🔧 **直接调工具** | 快速分析少量数据 | 每个工具的独立函数 |
| 🔗 **走流水线** | 完整审计项目 | `AuditTextPipeline` |
| 🔌 **通过MCP** | LLM Agent调用 | `mcp_server.py` 或 JSON-RPC |

---

## 二、直接调工具 —— 最快上手

### 1. 会议纪要热词分析

```python
from audit_text_analysis import text_hotword_analysis

result = text_hotword_analysis(
    documents=["会议纪要文本1...", "会议纪要文本2..."],
    doc_type="meeting_minutes",
    top_n=10,
)

for hw in result["hotwords"]:
    flag = "⚠️" if hw["risk_signal"] else "  "
    print(f"{flag} {hw['word']}: {hw['weight']:.4f}")
# 输出示例：
#   ⚠️ 采购: 0.2152
#   ⚠️ 外包: 0.1850
#     工程: 0.2042
```

### 2. 合同字段提取 + 交叉比对

```python
from audit_text_analysis import ContractFieldExtractor

extractor = ContractFieldExtractor()
result = extractor.extract(
    contract_texts=[("合同.pdf", "合同文本内容...")],
    payment_records=[
        {"amount": 6200000, "date": "2024-12-01"},
    ],
)

for ct in result.contracts:
    print(f"提取字段: {list(ct.fields.keys())}")
    for rf in ct.risk_flags:
        print(f"[{rf['severity']}] {rf['detail']}")
# 输出示例:
# [high] 累计支付6200000元，超过合同金额5800000元（超付6.9%）
```

### 3. 预算合规扫描

```python
from audit_text_analysis import budget_compliance_scan

result = budget_compliance_scan(
    expense_texts=[
        "会所消费 ¥12,800元",
        "购物卡 ¥30,000元 节日慰问",
        "ETC充值 ¥5,000元",
    ],
)

print(result["summary"])
# 共扫描3条记录，发现3条违规（高危2条，中危1条，低危0条）
```

### 4. 人员身份比对

```python
from audit_text_analysis import personnel_profile_check

result = personnel_profile_check(
    applicants=[
        {"name": "张三", "subsidy_type": "惠农补贴", "amount": 5000},
        {"name": "李四", "subsidy_type": "低保补贴", "amount": 8000},
    ],
    reference_lists={
        "finance_staff": ["李四"],  # 财政供养人员名单
        "deceased": ["王五"],        # 死亡人员名单
    },
)

print(result["summary"])
# 共核查2人，发现1人存在违规，1人通过
for v in result["violations"]:
    print(f"  [{v['violation_type']}] {v['name']}: {v['evidence']}")
```

### 5. 相似度比对（药品串换/围标检测）

```python
from audit_text_analysis import text_similarity_compare

result = text_similarity_compare(
    reference_texts=["维生素C咀嚼片 100mg×60片"],
    check_texts=["维生素C片 100mg×60片"],
    threshold=0.7,
)

for m in result["matches"]:
    print(f"{m['ref_text']} ←→ {m['check_text']}: "
          f"{m['similarity']:.1%} [{m['risk_type']}]")
# 维生素C咀嚼片 ←→ 维生素C片: 84.6% [tweak]
```

---

## 三、走完整流水线 —— 端到端审计项目

```python
from audit_text_analysis import AuditTextPipeline

pipeline = AuditTextPipeline()

# 准备文件
files = [
    "会议纪要_第1次.txt",
    "会议纪要_第2次.txt",
    "合同_001.txt",
    "报销凭证_2024.txt",
]

# 一键运行4步流程
result = pipeline.run(
    source_files=files,
    project_name="2024年度经责审计",
    project_type="economic_responsibility",
    enable_simulator=True,     # 启用v5模拟器对偶推理
)

print(f"总疑点: {result['total_findings']}")
print(f"高危: {result['high_risk_count']}")
print(f"中危: {result['medium_risk_count']}")

# 获取人工复核任务
review_task = result['review_task']
for item in review_task['high_medium_risk_items']:
    print(f"[{item['severity']}] {item['source']}: "
          f"{item['risk_flags'][0]['detail'][:50]}")

# 提交人工反馈
pipeline.submit_human_feedback([
    {"index": 1, "decision": "confirmed", "note": "确认违规"},
    {"index": 2, "decision": "rejected", "note": "程序性瑕疵"},
])
```

---

## 四、业务本体论查询 —— 智能规则匹配

```python
from audit_text_analysis import get_ontology

onto = get_ontology()  # 懒加载，含200条规则

# 按审计类型查规则
rules = onto.get_rules_by_category("procurement")
for r in rules:
    print(f"[{r.risk_level}] {r.name}")

# 条件匹配：我有这些数据，有哪些规则会触发？
matched = onto.match_rules(
    category="procurement",
    conditions={
        "same_supplier": True,
        "amount_min": 1000000,
        "has_competition": False,
    },
)
for r in matched:
    print(f"触发: {r.name} → {r.recommended_action}")

# 注入到Agent Prompt
prompt_text = onto.inject_to_prompt("budget", max_rules=5)
# 可追加到LLM的系统提示中
```

---

## 五、L1底稿评分

```python
from audit_text_analysis import WorkpaperScorer

scorer = WorkpaperScorer()

report = scorer.score(
    content="你的审计底稿文本...",
    workpaper_id="WP-ARR-001",
    workpaper_title="应收账款存在性测试",
    previous_year_content="上年度同项目底稿...",  # 可选，启用照抄检测
)

print(f"得分: {report.final_score}/100 [{report.grade[:8]}]")
print(f"四维: A={report.score_a} B={report.score_b} "
      f"C={report.score_c} D={report.score_d}")
print(f"扣分: E={report.penalty_e} F={report.penalty_f} "
      f"G={report.penalty_g}")

if not report.passed:
    print("改进建议:")
    for item in report.improvement_checklist:
        print(f"  - {item}")

# 批量评分
reports = scorer.batch_score([
    ("WP-001", "A底稿", content1),
    ("WP-002", "B底稿", content2),
])
summary = scorer.summary(reports)
print(f"通过率: {summary['pass_rate']}, 平均分: {summary['avg_score']}")
```

---

## 六、索引子系统

```python
from audit_text_analysis import AuditIndexSystem

idx = AuditIndexSystem("2024年度经责审计")

# 添加索引
wp = idx.add_entry("WP", "ARR", "应收账款底稿")
ev = idx.add_entry("EV", "ARR", "回函证据", 
                   file_path="/evidence/fx-001.pdf")
ct = idx.add_entry("CT", "PUR", "采购合同-设备")

# 建立交叉引用
idx.add_ref(wp, ev)
idx.add_ref(wp, ct)

# 追踪引用链
for chain in idx.get_ref_chain(wp):
    print(" → ".join(chain))
# WP-ARR-001 → EV-ARR-001

# 校验完整性
validation = idx.validate()
print(f"完整性: {validation.completeness:.0%}")
print(f"断链: {validation.broken_refs}")
print(f"孤岛: {validation.orphan_entries}")

# 生成索引表和可视化
print(idx.to_table())    # Markdown表格
print(idx.to_mermaid())  # Mermaid流程图
```

---

## 七、通过MCP Server（供LLM Agent调用）

```bash
# 启动MCP服务（stdin/stdout模式）
python -m audit_text_analysis.mcp_server

# 或交互模式
python -m audit_text_analysis.mcp_server --interactive
```

在LLM Agent中使用（MCP协议）：

```json
// 列出所有工具
{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

// 调用工具
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "text_hotword_analysis",
    "arguments": {
      "documents": ["会议纪要文本..."],
      "top_n": 10
    }
  }
}
```

可注册的7个MCP工具：
- `text_hotword_analysis`
- `text_similarity_compare`
- `contract_field_extract`
- `personnel_profile_check`
- `budget_compliance_scan`
- `audit_text_pipeline_run`
- `simulator_inference_generate`

---

## 八、典型工作流速查

| 场景 | 使用方式 |
|---|---|
| 领导说"看看这几份会议纪要有啥问题" | 调 `text_hotword_analysis` |
| 发现药品名称有点怪，疑似串换 | 调 `text_similarity_compare` |
| 拿到一堆合同，要提取关键信息 | 调 `contract_field_extract` |
| 补贴名单要核查有没有不合格的 | 调 `personnel_profile_check` |
| 报销凭证要扫一遍违规 | 调 `budget_compliance_scan` |
| 正式审计项目，端到端走 | 用 `AuditTextPipeline.run()` |
| 生成的底稿质量怎么样 | 用 `WorkpaperScorer.score()` |
| 有上年底稿，怕今年是照抄的 | 给 scorer 传 `previous_year_content` |
| Agent需要自动调用 | 接 `mcp_server` |
| 想让Agent更聪明 | 用 `get_ontology().inject_to_prompt()` |
| 管理底稿索引和引用关系 | 用 `AuditIndexSystem` |
