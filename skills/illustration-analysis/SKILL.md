---
name: illustration-analysis
description: "Analyze Chinese audit/finance/project documents (方案/报告/标书) and identify where illustrations, charts, and diagrams are needed. Output a structured illustration requirement list with position, type, and content logic for each figure. Triggers: '方案配图', '插图需求', '哪里需要插图', '图文拆解', '文本可视化分析'."
---

# Illustration Analysis Skill

## Overview

Read a document and decompose it into structured illustration requirements. The output feeds directly into `arch-diagrammer` to produce the actual graphics.

## Workflow

### Step 1: Document Structure Scan

Read the full document and identify:
- 文档类型（审计方案 / 复盘报告 / 预算方案 / 项目规划）
- 章节层级（章→节→小节）
- 每个章节的核心内容（2~3句话概括）

### Step 2: Illustration Requirement Recognition

For each section, apply these rules:

#### 必须配图的场景

| 文本特征 | 插图类型 | 配图理由 |
|---------|:-------:|---------|
| 步骤描述（"先...再...最后"） | `flowchart` 流程图 | 流程靠文字5分钟看不明白，图一秒钟 |
| 对比描述（"相比...增长了"） | `bar_chart` 对比柱状图 | 差异可视化 |
| 占比/比例（"占XX%"） | `pie_chart` 饼图/环形图 | 结构一目了然 |
| 趋势描述（"逐年上升"） | `line_chart` 折线图 | 趋势可见 |
| 风险分级（"高风险/中风险/低风险"） | `heatmap` 热力图 | 颜色区分比文字高效10倍 |
| 层级结构（"包括A、B、C三个方面"） | `hierarchy` 层级图/金字塔 | 归属关系可视 |
| 时间安排（"阶段一→阶段二→阶段三"） | `timeline` 时间轴 | 里程碑可视化 |
| 审批/业务流程 | `flowchart` 泳道图 | 清晰体现角色流转 |
| 组织/人员分工 | `org_chart` 组织架构图 | 层级和权责一目了然 |
| 闭环/循环（"PDCA循环"） | `cycle` 循环图 | 闭环关系 |
| 地理/区位 | `map` 地图标注 | 位置关系 |
| 问题清单/校验结果 | `colored_table` 彩色表格 | 红绿灯标注高下立判 |

#### 不建议配图的场景
- 纯法律条款引用
- 简单列举（少于3项）
- 纯定义性文字

### Step 3: Output Structured Requirement

Output a clean array of requirement objects:

```json
[
  {
    "id": "ill-001",
    "section": "3.1 审计重点",
    "position": "第3章末尾，紧接3.2节之前",
    "type": "heatmap",
    "title": "天府广场审计重点风险评估",
    "logic": "10个重点审计方向 × 3个维度(可能性/影响程度/综合风险)，按风险等级着色",
    "dataSource": "方案原文3.1节的表格数据",
    "dataNeeded": [
      {"key": "rows", "desc": "审计方向名称", "source": "原文列出"},
      {"key": "values", "desc": "每个方向在每个维度的评分(1-5)", "source": "需整理"}
    ],
    "priority": "high",
    "dimensions": "900x600"
  },
  ...
]
```

**字段说明：**
- `id`: 唯一编号 `ill-001` ~ `ill-N`
- `section`: 所属节号
- `position`: 在文档中的插入位置
- `type`: 插图类型（对照Step 2图表类型）
- `title`: 插图标题
- `logic`: 插图要表达的内容逻辑（1~2句话，供arch-diagrammer理解）
- `dataSource`: 数据在原文中的位置
- `dataNeeded`: 画图需要的数据清单
- `priority`: high / medium / low
- `dimensions`: 建议尺寸（宽x高）

### Step 4: Final Output Format

```markdown
## 📋 方案配图清单

| 编号 | 章节位置 | 插图类型 | 优先级 | 内容逻辑 |
|:---:|:--------:|:--------:|:------:|---------|
| ill-001 | §3.1 审计重点 | 🔴 风险热力图 | 🔥高 | 10项风险×3维分级 |
| ill-002 | §4.2 审计程序 | 🔵 流程图 | 🔥高 | 4阶段11步审批流程 |
| ill-003 | §5.3 预算对比 | 📊 对比柱状图 | 中 | 预算vs实际vs差异 |

### 详细需求

**ill-001: 天府广场审计重点风险评估**
- 🎯 **位置**: 第3章末尾，§3.2正文前
- 📐 **尺寸**: 900×600px
- 🔗 **数据**: rows=["资产租赁","停车场管理","合同管理","能耗管理"…]
              values=[[3,4,3],[5,5,5],[2,3,2]…]
```

## Integration with arch-diagrammer

The output of this skill feeds directly into `arch-diagrammer`:

```bash
# Save requirement as JSON
node -e "fs.writeFileSync('ill-001.json', JSON.stringify(requirement))"

# Pass to arch-diagrammer
# (arch-diagrammer will pick up the requirement JSON and render the graphic)
```
