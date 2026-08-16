---
name: drawio
description: Always use when user asks to create, generate, draw, or design a diagram, flowchart, architecture diagram, ER diagram, sequence diagram, class diagram, network diagram, mockup, wireframe, or UI sketch, or mentions draw.io, drawio, drawoi, .drawio files, or diagram export to PNG/SVG/PDF.
---

# Draw.io Diagram Skill

Generate draw.io diagrams as native `.drawio` files. Optionally export to PNG, SVG, or PDF with the diagram XML embedded (so the exported file remains editable in draw.io).

## How to create a diagram

**For政府审计场景（资金流/流程/组织/问题/绩效/资产）**：自动启用下方的 **Critic Mode** 审查循环。

1. **Generate draw.io XML** in mxGraphModel format for the requested diagram
2. **Write the XML** to a `.drawio` file in the current working directory using the Write tool
3. **If the user requested an export format** (png, svg, pdf), locate the draw.io CLI (see below), export with `--embed-diagram`, then delete the source `.drawio` file. If the CLI is not found, keep the `.drawio` file and tell the user they can install the draw.io desktop app to enable export, or open the `.drawio` file directly
4. **Open the result** — the exported file if exported, or the `.drawio` file otherwise. If the open command fails, print the file path so the user can open it manually

## Choosing the output format

Check the user's request for a format preference. Examples:

- `/drawio create a flowchart` → `flowchart.drawio`
- `/drawio png flowchart for login` → `login-flow.drawio.png`
- `/drawio svg: ER diagram` → `er-diagram.drawio.svg`
- `/drawio pdf architecture overview` → `architecture-overview.drawio.pdf`

If no format is mentioned, just write the `.drawio` file and open it in draw.io. The user can always ask to export later.

### Supported export formats

| Format | Embed XML | Notes |
|--------|-----------|-------|
| `png` | Yes (`-e`) | Viewable everywhere, editable in draw.io |
| `svg` | Yes (`-e`) | Scalable, editable in draw.io |
| `pdf` | Yes (`-e`) | Printable, editable in draw.io |
| `jpg` | No | Lossy, no embedded XML support |

PNG, SVG, and PDF all support `--embed-diagram` — the exported file contains the full diagram XML, so opening it in draw.io recovers the editable diagram.

## draw.io CLI

The draw.io desktop app includes a command-line interface for exporting.

### Locating the CLI

First, detect the environment, then locate the CLI accordingly:

#### WSL2 (Windows Subsystem for Linux)

WSL2 is detected when `/proc/version` contains `microsoft` or `WSL`:

```bash
grep -qi microsoft /proc/version 2>/dev/null && echo "WSL2"
```

On WSL2, use the Windows draw.io Desktop executable via `/mnt/c/...`:

```bash
DRAWIO_CMD=`/mnt/c/Program Files/draw.io/draw.io.exe`
```

The backtick quoting is required to handle the space in `Program Files` in bash.

If draw.io is installed in a non-default location, check common alternatives:

```bash
# Default install path
`/mnt/c/Program Files/draw.io/draw.io.exe`

# Per-user install (if the above does not exist)
`/mnt/c/Users/$WIN_USER/AppData/Local/Programs/draw.io/draw.io.exe`
```

#### macOS

```bash
/Applications/draw.io.app/Contents/MacOS/draw.io
```

#### Linux (native)

```bash
drawio   # typically on PATH via snap/apt/flatpak
```

#### Windows (native, non-WSL2)

```
"C:\Program Files\draw.io\draw.io.exe"
```

Use `which drawio` (or `where drawio` on Windows) to check if it's on PATH before falling back to the platform-specific path.

### Export command

```bash
drawio -x -f <format> -e -b 10 -o <output> <input.drawio>
```

**WSL2 example:**

```bash
`/mnt/c/Program Files/draw.io/draw.io.exe` -x -f png -e -b 10 -o diagram.drawio.png diagram.drawio
```

Key flags:
- `-x` / `--export`: export mode
- `-f` / `--format`: output format (png, svg, pdf, jpg)
- `-e` / `--embed-diagram`: embed diagram XML in the output (PNG, SVG, PDF only)
- `-o` / `--output`: output file path
- `-b` / `--border`: border width around diagram (default: 0)
- `-t` / `--transparent`: transparent background (PNG only)
- `-s` / `--scale`: scale the diagram size
- `--width` / `--height`: fit into specified dimensions (preserves aspect ratio)
- `-a` / `--all-pages`: export all pages (PDF only)
- `-p` / `--page-index`: select a specific page (1-based)

### Opening the result

| Environment | Command |
|-------------|---------|
| macOS | `open <file>` |
| Linux (native) | `xdg-open <file>` |
| WSL2 | `cmd.exe /c start "" "$(wslpath -w <file>)"` |
| Windows | `start <file>` |

**WSL2 notes:**
- `wslpath -w <file>` converts a WSL2 path (e.g. `/home/user/diagram.drawio`) to a Windows path (e.g. `C:\Users\...`). This is required because `cmd.exe` cannot resolve `/mnt/c/...` style paths.
- The empty string `""` after `start` is required to prevent `start` from interpreting the filename as a window title.

**WSL2 example:**

```bash
cmd.exe /c start "" "$(wslpath -w diagram.drawio)"
```

## File naming

- Use a descriptive filename based on the diagram content (e.g., `login-flow`, `database-schema`)
- Use lowercase with hyphens for multi-word names
- For export, use double extensions: `name.drawio.png`, `name.drawio.svg`, `name.drawio.pdf` — this signals the file contains embedded diagram XML
- After a successful export, delete the intermediate `.drawio` file — the exported file contains the full diagram

## XML format

A `.drawio` file is native mxGraphModel XML. Always generate XML directly — Mermaid and CSV formats require server-side conversion and cannot be saved as native files.

### Basic structure

Every diagram must have this structure:

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- Diagram cells go here with parent="1" -->
  </root>
</mxGraphModel>
```

- Cell `id="0"` is the root layer
- Cell `id="1"` is the default parent layer
- All diagram elements use `parent="1"` unless using multiple layers

## XML reference

For the complete draw.io XML reference including common styles, edge routing, containers, layers, tags, metadata, dark mode colors, and XML well-formedness rules, fetch and follow the instructions at:
https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/xml-reference.md

## Critic Mode — 审计图表审查循环

> 基于 PaperBanana Multi-Agent Critic 模式 | 依赖 `audit-diagram-critic/` 子技能 | 2026-05-27

当用户请求生成**政府审计/财政/绩效评价/资产清查**等领域的图表时，自动启用Critic模式。用户也可以显式触发：`/drawio critic` 或 "审查这张图"。

### Critic Mode 工作流

```
用户需求 + 审计场景描述(source_context)
    ↓
[Step 1] 参考库匹配 — 根据图表类型从 audit-bench 加载 2-3 张相似参考图
    ↓
[Step 2] Few-shot 生成 — 以参考图为样本，生成 .drawio 初始版本
    ↓
[Step 3] 导出 PNG — 调用 draw.io CLI 导出预览图
    ↓
[Step 4] Critic 审查 — 按 7 维度审查 XML 内容 + 逻辑 + 呈现 + 合规
    ↓
[Step 5] 决策 — severity=critical/high 且 round < max_rounds → 修改 → 返回 Step 2
           severity=medium/low → 标记建议，不阻塞通过
           "No changes needed." → 审查通过
    ↓
[Step 6] 最终输出 — .drawio + PNG + 审查报告
```

### 7 大审查维度

每次生成后，必须逐维度审查。审查基于 drawio XML 内容进行**逻辑审查**（不依赖视觉模型）：

| # | 维度 | XML审查要点 |
|---|------|------------|
| A | **信息一致性** | mxCell的value内容是否与source_context一致；有无凭空捏造的节点 |
| B | **标签完整性** | 每个vertex mxCell的value非空；每个edge的value有语义标注 |
| C | **层级/方向正确** | 组织图上下级id关系；资金流source→target方向；流程时序 |
| D | **逻辑合理性** | 箭头方向是否符合语义；不同性质的流是否用了不同样式 |
| E | **呈现质量** | fillColor合规(无黑底/霓虹色)；strokeWidth适中；有无冗余图例 |
| F | **中文质量** | 所有value中的中文无错别字；术语符合政府审计规范 |
| G | **合规性** | 无涉密信息；"下达"vs"拨付"等术语使用正确 |

### Veto Rules（一票否决）

以下任一命中，本轮直接判定不合格，必须重生成：
1. **严重失实** — 核心实体/流程与source_context矛盾
2. **逻辑颠倒** — 流程方向与原文相反
3. **遗漏关键要素** — 3个以上关键步骤/实体缺失
4. **涉密泄露** — 出现source_context未提及的涉密信息
5. **乱码/不可读** — 标签出现乱码或大量错别字

### 参考库匹配（Few-shot In-Context Learning）

在生成前，根据图表类型从 `data/audit-bench/` 加载参考图：

| 用户需求关键词 | 匹配类型 | 加载参考图（2-3张） |
|--------------|----------|-------------------|
| 资金流/拨付/专项 | **fund_flow** | fund-flow-three-level + fund-flow-bond |
| 组织架构/部门/层级 | **org_chart** | org-auditee + org-audit-team |
| 审计流程/程序/步骤 | **audit_flow** | audit-flow-performance + audit-flow-econ |
| 问题/因果/整改 | **issue_relation** | issue-causal-chain + issue-rectification-track |
| 甘特/时间/进度 | **gantt** | gantt-rectification-plan + gantt-project-progress |
| 制度/法规/框架 | **framework** | framework-internal-control + framework-procurement-law |
| 绩效/指标/评价 | **performance** | perf-indicator-tree + perf-radar-mapping |
| 资产/分类/生命周期 | **asset** | asset-classification + asset-lifecycle |

**操作方式**：从 `data/audit-bench/index.json` 读取匹配类型的条目，然后读取对应 `data/audit-bench/diagrams/{id}.drawio` 文件。将其内容作为 Few-shot 参考样本，模仿其结构、配色、标注风格生成新图。

### 审查报告格式

```markdown
## 🔍 审计图表审查报告（Round N/3）

| # | 维度 | 位置 | 问题 | 严重度 | 修正 |
|---|------|------|------|--------|------|
| 1 | content | 节点X | ... | high | ... |

**结论**: [通过 / 需修改]
**Veto触发**: [是/否]
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_rounds` | 3 | 最大审查迭代轮次 |
| `severity_threshold` | `high` | 强制重新生成的最低严重度 |
| `reference_count` | 2-3 | Few-shot参考图数量 |

### 参考文件

- 审查系统提示词 & 检查清单: `skills/drawio/audit-diagram-critic/critic_prompts.py`
- 审计图表风格指南: `skills/drawio/audit-diagram-critic/style_guide.py`
- 参考库索引: `data/audit-bench/index.json`

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| draw.io CLI not found | Desktop app not installed or not on PATH | Keep the `.drawio` file and tell the user to install the draw.io desktop app, or open the file manually |
| Export produces empty/corrupt file | Invalid XML (e.g. double hyphens in comments, unescaped special characters) | Validate XML well-formedness before writing; see the XML well-formedness section below |
| Diagram opens but looks blank | Missing root cells `id="0"` and `id="1"` | Ensure the basic mxGraphModel structure is complete |
| Edges not rendering | Edge mxCell is self-closing (no child mxGeometry element) | Every edge must have `<mxGeometry relative="1" as="geometry" />` as a child element |
| File won't open after export | Incorrect file path or missing file association | Print the absolute file path so the user can open it manually |

## CRITICAL: XML well-formedness

- **NEVER include ANY XML comments (`<!-- -->`) in the output.** XML comments are strictly forbidden — they waste tokens, can cause parse errors, and serve no purpose in diagram XML.
- Escape special characters in attribute values: `&amp;`, `&lt;`, `&gt;`, `&quot;`
- Always use unique `id` values for each `mxCell`
