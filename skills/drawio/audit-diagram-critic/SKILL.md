# Audit Diagram Critic — 审计图表审查循环

> 基于 PaperBanana Critic Agent 模式 | 适配融策政府审计场景 | 2026-05-27
> **需配合 drawio 技能使用** | 审查维度：内容准确性 + 逻辑流程 + 呈现质量 + 合规性

## 触发条件

- 用户要求"审查这张图""审核图表质量""检查流程图"
- 生成审计图表后自动触发审查（drawio生成→Critic审查→回修改）
- 批处理模式下对批量图表做质量门禁

## 核心工作流

```
用户需求（审计场景）
    ↓
[Step 1] drawio 生成初始图表 → .drawio 文件 + PNG导出
    ↓
[Step 2] 审计图表Critic审查 (本轮) → 问题清单 + 修改描述
    ├── severity=critical/high → 必须修改
    ├── severity=medium → 建议修改
    ├── severity=low → 可选修改
    └── "No changes needed." → 审查通过
    ↓ (需要修改，且未达最大轮次)
[Step 3] drawio 根据 revised_description 重新生成 → 返回 Step 2
    ↓ (审查通过 或 达到最大轮次)
最终输出: .drawio 文件 + PNG预览 + 审查记录
```

## 审查维度（7大维度）

| # | 维度 | 检查内容 | 来源 |
|---|------|----------|------|
| A | **信息一致性** | 实体/流程/数据与原始描述一致，不凭空捏造 | Content Fidelity |
| B | **标签完整性** | 所有节点有标签，所有连线有语义标注 | Content Fidelity |
| C | **层级正确性** | 组织层级、资金流向方向正确 | Content Fidelity |
| D | **逻辑合理性** | 时序/因果关系正确，流程无矛盾 | Logic & Flow |
| E | **呈现质量** | 无遮挡/混乱/字小/配色违规 | Presentation |
| F | **中文质量** | 无错别字/语法错误/用语不规范 | Content Fidelity |
| G | **合规性** | 无涉密信息，术语规范 | Compliance |

## Veto Rules（一票否决）

以下任一命中，图表直接判定不合格：
1. **严重失实**：核心实体/流程/关系与原始描述矛盾
2. **逻辑颠倒**：流程方向与原文相反
3. **遗漏关键要素**：3个以上关键步骤/实体缺失
4. **涉密泄露**：出现源文档中未提及的涉密信息
5. **乱码/不可读**：标签乱码或字号过小完全无法阅读

## 使用方式

### 模式1：生成后自动审查（推荐）

```
用户: 画一张XX项目资金流向图，包含拨付、使用、结余三个环节...
    ↓
[AI] 调用drawio技能生成初始图 → 导出PNG
    ↓
[AI] 调用Critic审查 → 发现问题 → 输出修改版描述
    ↓
[AI] 调用drawio重新生成 → 导出PNG
    ↓
[AI] 再次审查 → 通过
    ↓
最终输出: .drawio + PNG + "审查通过：共2轮迭代，第2轮合格"
```

### 模式2：独立审查已有图表

```
用户: 审查这张流程图 output/审核流程图.drawio
    ↓
[AI] 导出PNG → 读取原始需求或source_context
    ↓
[AI] 调用Critic审查 → 输出审查报告
    ↓
输出: 审查报告（问题清单 + 严重程度 + 修改建议）
```

### 模式3：批量质量门禁

对一个目录下的所有.drawio文件做批量审查，输出汇总报告。

## 审查输出格式

审查报告包含以下部分：

```markdown
## 审计图表审查报告

**图表**: [图表名称]
**审查时间**: [时间戳]
**审查轮次**: Round N/M

### 总体评估
- 严重程度: low | medium | high | critical
- Veto是否触发: 是 | 否
- 审查结论: 通过 | 需修改(第N轮)

### 问题清单
| # | 类别 | 位置 | 问题 | 修正建议 |
|---|------|------|------|----------|
| 1 | content | 节点"XX" | 标签与原文不一致 | 修正为"YY" |
| 2 | logic | 连线A→B | 方向错误 | 改为B→A |

### 修改后的详细描述
[修改后的完整描述，用于驱动下一轮drawio生成]
```

## 审计场景重点检查项

按图表类型不同，审查重点不同：

| 图表类型 | 重点检查 |
|----------|----------|
| **资金流向图** | 来源→去向闭合、金额标注、有无截留/挪用风险点 |
| **组织架构图** | 层级关系正确、部门名称准确、隶属关系不颠倒 |
| **审计流程图** | 时序正确、角色标识清晰、决策分支完备 |
| **问题关系图** | 因果链正确、问题严重等级标注、整改状态 |
| **资产分布图** | 数据一致性、资产类别完整、占比标注 |
| **整改甘特图** | 时间节点合理、责任人标注、进度状态区分 |
| **制度框架图** | 制度层级正确、覆盖范围完整、发文文号标注 |

## drawio风格速查（审查时对照）

审查时，对照以下drawio属性检查合规性：

| 审计要求 | drawio style属性 | 合规值 |
|----------|-----------------|--------|
| 白底 | 默认(无fillColor或#FFFFFF) | ✅ 默认合规 |
| 深蓝主色 | `fillColor=#1A5276` `fontColor=#FFFFFF` | ✅ 标题栏/关键节点 |
| 问题标记红 | `strokeColor=#E74C3C` `strokeWidth=2` | ✅ 风险节点边框 |
| 圆角矩形 | `rounded=1` | ✅ 流程节点 |
| 菱形决策 | `rhombus` | ✅ 决策节点 |
| 箭头标注 | `value="拨付"` on edge | ✅ 资金流标注 |

## 迭代参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_rounds` | 3 | 最大审查轮次 |
| `severity_threshold` | `high` | 强制重新生成的最低严重度 |
| `preserve_structure` | `true` | 修改时保留原图结构，只改问题部分 |

## 与其他技能的集成

| 集成目标 | 方式 |
|----------|------|
| **drawio** | drawio生成→导出PNG→Critic审查→返回修改描述→drawio重新生成 |
| **arch-diagrammer** | 同理，SVG/PNG输出后走Critic审查 |
| **audit-plugin report-writer** | 图表插入报告前过Critic质量门禁 |
| **workflow-embedder** | 嵌入"图表生成后"事件触发器，自动启动Critic |

## 文件结构

```
skills/drawio/audit-diagram-critic/
├── SKILL.md              ← 本文件
├── critic_prompts.py     ← 系统提示词 + 检查清单 + Veto Rules
├── style_guide.py        ← 审计图表风格指南
└── references/           ← 审计图表参考库（待建设）
```

## 相关参考

- PaperBanana Critic Agent: `research/PaperBanana深度分析.md`
- drawio SKILL.md: `skills/drawio/SKILL.md`
- 审计图表风格指南: `skills/drawio/audit-diagram-critic/style_guide.py`
