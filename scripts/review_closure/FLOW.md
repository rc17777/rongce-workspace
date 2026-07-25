# 审盾闭环层 v1.0

> 复核意见自动流转 → 质控系统 + 每条结论带推演过程

## 核心理念

**你审查的不是结论，是推导过程。**

审计报告复核最怕什么？AI 说"这里有错"，但你不知道它为什么这么说。你敢直接信吗？

闭环层的答案是：**每条复核发现都带推理链**——从数据加载到规则匹配，从知识库查询到计算推演，从 AI 判断到误报抑制，每一步都留痕。

## 架构

```
报告提交
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Step 1: RAG增强复核（现有report_review_workflow）   │
│  Step 2: 快速复核（规则引擎）                        │
│  Step 3: 深度复核（15维框架）                        │
│  Step 4: 告警汇总                                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  闭环层：推理链构建器                                │
│  - 每条发现 → 自动包装推理链                         │
│  - 规则引用 + 数据来源 + RAG引用 + 计算过程 + FP检查  │
│  - 链式置信度累加                                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  质控管道（QC Pipeline）                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ 待审核队列 │ → │ 质控审核  │ → │ 归档归档  │      │
│  │ (queue/)  │    │ 确认/驳回 │    │(archive/)│      │
│  └──────────┘    └──────────┘    └──────────┘      │
└─────────────────────────────────────────────────────┘
```

## 数据模型

### 每个发现的推理链格式

```json
{
  "finding_id": "F-20260721-001",
  "dimension": "金额单位",
  "severity": "P1",
  "message": "报告同时使用万元和元为单位，建议统一",
  "trail": {
    "step_count": 4,
    "overall_confidence": 0.85,
    "data_sources": ["报告文本"],
    "rules_applied": ["R-001"],
    "rag_references": ["专项资金审计要点..."],
    "fp_checks": ["FP-11A检查通过"],
    "steps": [
      {
        "step_type": "数据加载",
        "description": "扫描报告全文，定位金额单位相关模式",
        "source_ref": "报告文本"
      },
      {
        "step_type": "规则匹配",
        "description": "应用R-001: 金额单位混用检查",
        "rule_ref": "R-001",
        "input_data": "万元和元同时出现",
        "output_data": "需要统一为单位"
      },
      {
        "step_type": "知识库查询",
        "description": "查专项资金审计常见金额问题",
        "source_ref": "RAG知识库"
      },
      {
        "step_type": "误报抑制",
        "description": "检查是否误报: 金额单位混用",
        "rule_ref": "FP-11A",
        "output_data": "检查通过，未触发抑制"
      }
    ]
  }
}
```

## 质控工作流

```
待审核 (PENDING) ──→ 审核中 (IN_REVIEW) ──→ 已确认 (ACCEPTED) ──→ 已归档
                  │                        └→ 已驳回 (REJECTED)   ──→ 已归档
                  │                        └→ 已修改 (MODIFIED)   ──→ 已归档
                  └→ 直接确认/驳回 (批量操作)
```

## 文件结构

```
scripts/review_closure/
├── __init__.py          # 模块入口
├── schema.py            # 数据模型
│   ├── ReasoningStep    # 推理步骤
│   ├── ReasoningTrail   # 推理链
│   ├── ReviewFinding    # 带推理链的发现
│   └── QCPipeline       # 质控管道
├── reasoning_trail.py   # 推理链构建器
│   ├── RULE_REGISTRY    # 规则索引(30+条)
│   ├── build_quick_review_trail()
│   ├── build_deep_review_trail()
│   ├── build_full_pipeline()
│   └── pipeline_to_markdown()
├── qc_pipeline.py       # 质控管道
│   ├── submit_to_qc()      # 提交到队列
│   ├── review_finding()    # 审核单条
│   ├── batch_review()      # 批量审核
│   └── get_qc_dashboard()  # 质控看板
├── cli.py               # 命令行审核工具
└── test_all.py          # 集成测试

output/qc_pipelines/
├── queue/               # 待审核队列
├── archive/             # 已归档
└── reports/             # 推理链报告(Markdown)
```

## 快速上手

### 1. 提交报告到质控管道

```bash
# 从文件提交
python -m scripts.review_closure.cli submit --file 审计报告.docx

# 直接贴文本
python -m scripts.review_closure.cli submit --text "报告全文..." --name "XX项目审计报告"
```

### 2. 查看质控队列

```bash
python -m scripts.review_closure.cli list
python -m scripts.review_closure.cli dashboard
```

### 3. 查看管道详情

```bash
python -m scripts.review_closure.cli show --pipeline_id QC-20260721-143056-abc123
```

### 4. 查看推理链（推演过程）

```bash
# 查看所有推理链摘要
python -m scripts.review_closure.cli trail --pipeline_id QC-20260721-143056-abc123

# 查看单条完整推理链
python -m scripts.review_closure.cli trail --pipeline_id QC-20260721-143056-abc123 --finding_id F-20260721-001
```

### 5. 审核发现

```bash
# 确认发现
python -m scripts.review_closure.cli review --pipeline_id QC-xxx --finding_id F-20260721-001 accept --reviewer "张三" --comment "金额已核实，确认发现"

# 驳回（误报）
python -m scripts.review_closure.cli review --pipeline_id QC-xxx --finding_id F-20260721-002 reject --reviewer "张三" --comment "日期格式正确，无需修改"

# 批量确认所有P0
python -m scripts.review_closure.cli batch --pipeline_id QC-xxx accept --severity P0 --reviewer "张三"
```

### 6. 导出报告

```bash
# 导出Markdown报告（含推理链）
python -m scripts.review_closure.cli export --pipeline_id QC-xxx --format md

# 导出JSON
python -m scripts.review_closure.cli export --pipeline_id QC-xxx --format json
```

## 规则索引

| 编号 | 规则 | 用途 |
|:----|:-----|:-----|
| R-001 | 金额单位混用 | 检测万元/元并用 |
| R-002 | 金额单位升档 | ≥1亿建议用"亿" |
| R-003 | 日期格式 | 统一YYYY年MM月DD日 |
| R-004 | 金额大小写一致性 | 中文大写vs数字 |
| R-005~013 | 错别字 | 帐/账/做出/截止/涉及等 |
| R-014 | 连续标点 | 禁止重复标点 |
| R-015 | 空括号 | 遗漏内容标记 |
| R-016 | 数字合计校验 | 编号项金额汇总 |
| R-017 | 百分数合计 | 结构占比检查 |
| R-018 | 法规引用完整性 | 书名号匹配 |
| R-101~115 | 15维深度复核 | 逻辑/定性/证据链等 |
| FP-G1~G2 | 通用误报抑制 | 尾差/低置信度 |
| FP-1A~1B | 经责FP | 定性词白名单 |
| FP-3A~3B | 预算FP | 基本完成/超预算 |
| FP-6A | 采购FP | 围标串标交叉确认 |
| FP-11A~11D | 绩效FP | 专业表述白名单 |

## 与现有系统集成

### 与 report_review_workflow.py 集成

```python
from scripts.review_closure.reasoning_trail import build_full_pipeline, save_pipeline

# 运行现有复核
result = run_full_workflow(file_path="报告.docx")

# 构建质控管道
pipeline = build_full_pipeline(
    report_name="XX项目",
    step2_result=result['step2_quick'],
    step3_framework=result['step3_deep_framework'],
    step1_result=result['step1_rag'],
    report_text=report_text,
)

# 提交到质控队列
from scripts.review_closure.qc_pipeline import submit_to_qc
submit_to_qc(pipeline)
```

## 你问的"推演过程"长什么样？

拿你的测试报告举例：

**发现：** "截止2023年12月31日，部分资金未拨付到位" 中的"截止"应为"截至"

**推理链：**
1. 📄 **数据加载** → 扫描报告全文，定位错别字模式
2. ⚙️ **规则匹配** → 应用 R-007: "截止"不接宾语，"截至"可接宾语
   - 输入: "截止2023年12月31日"
   - 输出: "截止"后直接接时间宾语，判定为误用
3. ✅ **误报抑制** → 检查 FP-3A: 非预算语境，不触发
4. 📊 **置信度**: 0.85（规则匹配确定性高）

**质控员收到的信息：**
- 发现本身（1行）
- 推理链（4步，可展开）
- 规则引用（R-007，可查原文）
- 置信度（85%）
- 误报检查记录