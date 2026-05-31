---
name: arch-diagrammer
description: "Generate production-ready architecture diagrams, flowcharts, timelines, and infographics from structured illustration requirements (JSON from illustration-analysis or direct spec). Outputs SVG and PNG. Triggers: '生成配图', '画流程图', '画架构图', '出图', 'render diagram', '产出示意图'."
---

# Arch-Diagrammer Skill

## Overview

Receives structured illustration requirements (from `illustration-analysis` or direct user input) and renders them as deliverable SVG/PNG graphics. The "how to draw" counterpart of `illustration-analysis`.

## Supported Output Types

| Type ID | Description | Tool |
|---------|:-----------|:----:|
| `heatmap` | 风险热力图矩阵 | draw_chart.js |
| `bar_chart` / `bar` | 柱状图、分组对比柱状图 | draw_chart.js |
| `pie_chart` / `pie` | 饼图/环形图 | draw_chart.js |
| `line_chart` / `line` | 折线图/多系列趋势图 | draw_chart.js |
| `colored_table` / `table` | 带红绿灯标注的彩色表格 | draw_chart.js |
| `flowchart` | SVG流程图（Mermaid或Canvas） | draw_chart.js / Mermaid |
| `timeline` | 时间轴/甘特图 | draw_chart.js / Mermaid |
| `org_chart` / `hierarchy` | 组织架构/层级结构图 | draw_chart.js |
| `cycle` | 循环图/闭环图 | draw_chart.js |
| `map` | 地理标注图 | 备选：video_generate |

## Core Workflow

### Step 1: Parse Requirement

Input is a JSON requirement object from `illustration-analysis`:

```json
{
  "id": "ill-001",
  "type": "flowchart",
  "title": "审计程序流程图",
  "logic": "从接收委托到出具报告共4个阶段11个步骤，涉及审计组、被审计单位、质量复核人三方",
  "dataNeeded": [
    {"key": "stages", "desc": "阶段名称列表"},
    {"key": "steps", "desc": "每阶段的步骤明细"},
    {"key": "actors", "desc": "参与角色"}
  ],
  "dimensions": "1000x800"
}
```

If data is missing, ask the user or derive from the document.

### Step 2: Render Graphic

#### 统计图表类（heatmap/bar/pie/line/table）

```bash
# Write data to temp JSON, then run
node scripts/draw_chart.js --type heatmap --data "path/to/data.json" --output "output/ill-001.png"
```

The `draw_chart.js` script accepts these types directly:
- `heatmap` — 风险矩阵
- `bar` — 柱状图（分组=values传二维数组+group_names）
- `pie` — 环形饼图（donut:true）
- `line` — 折线图（values传二维数组=多系列）
- `colored_table` — 带状态着色的表格（status_column指定状态列）

#### 流程图/阶段图类（flowchart/timeline/cycle）

Use Node Canvas to draw SVG-style diagrams with `scripts/draw_chart.js` extended calls, or fallback to programmatic SVG generation.

For Mermaid-compatible diagrams, create `.mmd` file and render to SVG:

```bash
npx @mermaid-js/mermaid-cli mmdc -i diagram.mmd -o diagram.png -w 1000
```

If mermaid-cli is unavailable, render via Node Canvas drawing primitives.

#### 概念图/装饰配图

Use `video_generate` tool for high-quality AI-generated illustrations:

```
video_generate with prompt: "professional audit risk heatmap, corporate blue theme..."
```

### Step 3: Quality Check

Before delivery, verify:
- ✅ 分辨率 ≥200dpi or ≥800px width
- ✅ 标题完整（含项目名+图号）
- ✅ 中文字体正常（微软雅黑）
- ✅ 配色符合审计调性（深蓝+灰+红）
- ✅ 图例/坐标轴标签完整
- ✅ 数据标注清晰

### Step 4: Delivery

Output:
1. **独立图片文件** → `output/ill-001.png` 等
2. 告知用户每张图的文件名和位置

## Script Reference

See `scripts/draw_chart.js` for the core chart engine.

**Available chart types and their data schemas:**
```
node scripts/draw_chart.js --type [type] --data [json_file|json_string] --output [file.png]
```

For data format details of each type, see `references/chart-specs.md`.

For flowcharts and diagrams beyond the script's capabilities, draw programmatically using `@napi-rs/canvas` primitives (rect, arc, text, line, bezierCurveTo).
