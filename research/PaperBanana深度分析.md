# PaperBanana 深度技术分析与集成方案

> 来源：[GitHub dwzhu-pku/PaperBanana](https://github.com/dwzhu-pku/PaperBanana) | Apache 2.0 | 源自 Google Research PaperVizAgent
> 分析时间：2026-05-27

---

## 一、核心架构

### 1.1 五Agent流水线

```
用户输入(论文方法段+图注)
    ↓
Retriever Agent  → 从PaperBananaBench检索Top10相似参考插图
    ↓
Planner Agent    → Few-shot In-Context Learning：模仿参考图的描述风格，产出Detailed Description
    ↓
Stylist Agent    → 对齐学术审美规范，优化配色/字体/布局描述
    ↓
Visualizer Agent → 调用图片生成API（Gemini/GPT-Image/OpenRouter）生成像素图
    ↓  ↑
Critic Agent     → 闭环迭代(最多3轮)：审查→提出修改意见→Visualizer重新生成
    ↓
最终输出 → PNG/JPEG + Base64编码
```

### 1.2 6种运行模式（Experiment Modes）

| 模式 | Agent链 | 说明 |
|------|---------|------|
| `vanilla` | Visualizer only | 直接文本→图，无规划无审查 |
| `dev_planner` | Retriever→Planner→Visualizer | 有规划无审查 |
| `dev_planner_stylist` | Retriever→Planner→Stylist→Visualizer | 加美学优化 |
| `dev_planner_critic` | R→P→V→Critic loop | 审查循环，无Stylist |
| `dev_full` | 全部5个Agent | 完整流水线 |
| `demo_*` | 同上但不做评估 | 交互式Demo用 |

### 1.3 项目结构

```
agents/          ← 5个Agent + Vanilla + Polish
  base_agent.py      ← 抽象基类
  retriever_agent.py ← 检索参考图（基于描述embedding匹配）
  planner_agent.py   ← Few-shot生成详细描述
  stylist_agent.py   ← 美学规范对齐
  visualizer_agent.py← 核心：调用图片生成API（diagram）或matplotlib代码执行（plot）
  critic_agent.py    ← 审查+迭代优化
  polish_agent.py    ← 图片后期精修（2K/4K放大）
utils/
  paperviz_processor.py ← 流水线编排器（Orchestrator）
  generation_utils.py   ← 多Provider统一API（Gemini/Anthropic/OpenAI/OpenRouter）
  eval_toolkits.py      ← 4维度评估（Faithfulness/Conciseness/Readability/Aesthetics）
prompts/
  diagram_eval_prompts.py ← 4维度评估Prompt（含Veto Rules）
style_guides/          ← 自动合成的学术风格指南
configs/               ← YAML配置
```

---

## 二、关键技术细节

### 2.1 Visualizer：并非SVG，是图片生成API

**微信公众号文章的不准确之处**：文章说"调用代码去生成SVG矢量图"，但实际源码中：

- **Diagram（学术架构图）**：直接调用 Gemini/GPT-Image/OpenRouter 等图片生成API，输出**PNG像素图**，不是SVG
  ```python
  # visualizer_agent.py 第74-77行
  self.task_config = {
      "task_name": "diagram",
      "use_image_generation": True,  # 直接图片生成，不是代码
  }
  ```
- **Plot（统计图）**：走代码生成路径，LLM写matplotlib代码 → `exec()`执行 → 输出JPEG
  ```python
  # visualizer_agent.py 第65-69行
  self.task_config = {
      "task_name": "plot",
      "use_image_generation": False,  # 用代码生成
  }
  ```

**结论**：PaperBanana的架构图和我们的 drawio/arch-diagrammer 走的是不同路径：
- PaperBanana：文本描述 → 图片生成API → 像素图
- 我们（drawio/arch-diagrammer）：文本描述 → 代码/Mermaid → SVG/Draw.io XML → 矢量图

### 2.2 Critic Agent：核心差异化能力

```python
# critic_agent.py — 审查维度
1. Content（内容）
   - Fidelity & Alignment: 图是否忠实反映方法论和图注
   - Text QA: 拼写/语法/标签清晰度
   - Validation of Examples: 示例数据准确性
   - Caption Exclusion: 图中不应包含图注文字

2. Presentation（呈现）
   - Clarity & Readability: 流程清晰度、布局合理性
   - Legend Management: 去除冗余图例
```

**Critic的输入**：
1. Target Diagram（当前生成的图，base64）
2. Detailed Description（当前图的文字描述）
3. Methodology Section（原始方法论文本）
4. Figure Caption（原始图注）

**Critic的输出**（JSON）：
```json
{
  "critic_suggestions": "具体修改建议...",
  "revised_description": "修改后的详细描述..."
}
```

**迭代终止条件**：
- Critic返回"No changes needed."
- 或达到max_critic_rounds（默认3轮）
- 或Visualizer生成失败（回退到上一轮最佳结果）

### 2.3 Planner：Few-shot In-Context Learning

Planner的核心技巧是**参考驱动**：
1. Retriever从PaperBananaBench中找到与当前任务最相似的10张参考图
2. 将参考图的（方法论文本 + 图注 + 图片）作为few-shot examples喂给Planner
3. Planner模仿参考图的描述风格，为目标图生成Detailed Description

```python
# planner_agent.py 第54-65行
for idx, item in enumerate(examples):
    user_prompt += f"Example {idx+1}:\n"
    user_prompt += f"Methodology Section: {item['content']}\n"
    user_prompt += f"Diagram Caption: {item['visual_intent']}\n"
    user_prompt += f"Reference Diagram: "
    content_list.append({"type": "text", "text": user_prompt})
    content_list.append({"type": "image", ...})  # 参考图base64
```

### 2.4 评估体系：4维度 + Veto Rules

| 维度 | 定义 | 否决规则 |
|------|------|----------|
| **Faithfulness** | 技术对齐度（内容正确性） | 幻觉/逻辑矛盾/范围违规/乱码 |
| **Conciseness** | 视觉信噪比（抽象程度） | 文字超载/照抄原文/公式堆砌 |
| **Readability** | 可读性（排版清晰度） | 视觉噪声/遮挡/混乱连线/字号过小/低对比度/布局低效/黑底 |
| **Aesthetics** | 美学品质 | 低质量伪影/配色冲突/业余风格/字体不一致/黑底 |

每个维度都设置了严格的Veto Rules（否决红线），确保评估不是主观打分而是规则驱动。

### 2.5 与ClawHub的关系

PaperBanana已发布为ClawHub Skill（`clawhub install paperbanana`），说明其设计理念与OpenClaw生态兼容。

---

## 三、与融策现有技能体系对比

### 3.1 现有绘图技能

| 技能 | 方式 | 输出 | 可编辑 | Critic循环 |
|------|------|------|--------|------------|
| **arch-diagrammer** | LLM→SVG/PNG | 矢量/像素 | 部分 | ❌ 无 |
| **drawio** | LLM→Draw.io XML | 原生XML | ✅ 完全 | ❌ 无 |
| **deepseek-charting** | LLM→Mermaid/ECharts | 代码→图 | ✅ 代码级 | ❌ 无 |
| **PaperBanana** | 多Agent→图片生成API | PNG像素 | ❌ 不可编辑 | ✅ 3轮迭代 |

### 3.2 能力互补矩阵

```
             矢量可编辑  多Agent   Critic审查   专业领域
drawio          ✅         ❌         ❌        通用
arch-diagrammer ⚠️半      ❌         ❌        软件架构
deepseek-chart  ✅         ❌         ❌        数据图表
PaperBanana      ❌         ✅         ✅        学术科研
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
我们需要的       ✅         ✅         ✅        政府审计
```

### 3.3 核心差距

1. **缺少Critic审查循环**：我们现有的3个绘图技能都是一次生成，没有"审查→修改"迭代
2. **缺少参考驱动**：我们没有Few-shot in-context learning机制
3. **缺少审计领域风格规范**：PaperBanana有style_guides，我们没有审计图表的美学规范库
4. **中文文本准确性**：PaperBanana的Critic有Text QA，但对中文的检查不够

---

## 四、集成方案

### 方案A：轻量级——给drawio加Critic循环（推荐优先实施）

**思路**：不改变底层生成器，在现有drawio/arch-diagrammer外层包一个Critic。

```
用户需求（审计场景）
    ↓
drawio/arch-diagrammer → 生成初始Draw.io XML
    ↓
渲染为PNG截图
    ↓
Audit Diagram Critic → 审查（内容准确性/标签完整性/布局合理性/中文正确性）
    ↓ 需要修改
返回修改指令 → drawio/arch-diagrammer重新生成
    ↓ 通过
最终 .drawio 文件 + PNG预览
```

**技术要点**：
- Critic接收：原始需求 + 当前PNG截图 + 当前description
- Critic输出：具体修改点 + Revised Description
- 迭代上限：2-3轮
- 可复用PaperBanana的Critic Prompt结构，改造为审计场景

**优势**：
- 最小改动，不破坏现有技能
- draw.io文件保持可编辑
- Critic Prompt可以针对审计场景定制（资金流方向、组织关系正确性等）

### 方案B：中量级——审计图表风格指南 + Reference库

**思路**：参考PaperBanana的style_guides和PaperBananaBench，建立审计领域的参考库。

**需要建立**：
1. **审计图表风格指南**（style_guides/audit/）
   - 配色规范（政府审计报告常用色）
   - 字体规范（中文标签要求）
   - 布局规范（流程图/组织图/资金流图/问题树图）
   - 连接线规范（箭头语义：资金流/审批流/数据流）

2. **审计图表参考库**（data/audit-bench/）
   - 收集20-30张高质量政府审计图表作为few-shot参考
   - 每张图配：场景描述 + 图注 + 图片
   - 覆盖类型：组织架构图、资金流程图、问题关系图、时序甘特图、数据对比图

**优势**：
- Few-shot学习可以大幅提升生成质量
- 积累的参考库可复用
- 为后续审计Agent提供知识基础

### 方案C：重量级——AuditBanana：审计图表多Agent生成器

**思路**：借鉴PaperBanana完整架构，构建审计专用版。

```
审计文档(实施方案/审计报告片段)
    ↓
Retriever Agent    → 从审计参考库检索相似图表
    ↓
Planner Agent      → 生成审计图表的详细描述
    ↓
Stylist Agent      → 对齐政府审计报告规范
    ↓
Visualizer Agent   → 调用drawio技能生成XML
    ↓  ↑
Audit Critic Agent → 迭代审查（3轮）
    ↓
审计图表 + 审计底稿引用标注
```

**Critic的审计专属检查项**：
1. 资金流向正确性（来源→路径→去向）
2. 组织层级准确性（上下级关系不颠倒）
3. 时间顺序逻辑（流程先后不矛盾）
4. 法规条款引用准确性（图中引用的法规编号正确）
5. 数据一致性（图中数字与底稿一致）
6. 涉密信息检查（不应出现的敏感数据）
7. 中文本地化（无乱码、无英文残留、术语统一）

**优势**：
- 完整的审计专用能力
- 可集成到audit-plugin的Finding → Recommendation → Report流程中
- 积累的参考库和Critic Prompt可持续优化

### 方案D：利用ClawHub直接安装

PaperBanana已发布为ClawHub Skill，可以直接安装使用：
```bash
clawhub install paperbanana
```

但需要：
1. Google API Key 或 OpenRouter API Key
2. Python 3.12 + uv环境
3. PaperBananaBench数据集（可选）

**局限**：PaperBanana的Visualizer用的是图片生成API，输出像素图不可编辑，不适合审计报告的迭代修改需求。

---

## 五、推荐实施路线

### Phase 1：Critic Prompt先行（1-2天）

**目标**：先让现有drawio/arch-diagrammer具备审查能力。

- [ ] 编写 `AuditDiagramCritic` 系统提示词（中英文双语）
- [ ] 建立审查检查清单（资金流/层级/时序/法规/数据/涉密/中文）
- [ ] 在drawio技能上测试Critic循环（手动触发）

### Phase 2：建立审计参考库（3-5天）

**目标**：积累审计领域的Few-shot参考素材。

- [ ] 从融策历史项目中收集20+张高质量审计图表
- [ ] 每张图标注：场景类型、描述文本、图注
- [ ] 建立 `data/audit-bench/` 目录结构
- [ ] 编写审计图表风格指南

### Phase 3：集成到drawio技能（3-5天）

**目标**：drawio生成 → Critic审查 → 自动迭代修改。

- [ ] 扩展现有drawio技能，添加`--critic`模式和`--max-rounds`参数
- [ ] 在drawio SKILL.md中声明Critic工作流
- [ ] 端到端测试：审计场景输入 → 审查循环 → 最终可编辑图表

### Phase 4：独立AuditBanana技能（按需）

**目标**：完整的审计图表多Agent生成框架。

- [ ] 新建 `skills/audit-banana/SKILL.md`
- [ ] 实现5个Agent（Retriever/Planner/Stylist/Visualizer/Critic）
- [ ] 集成drawio作为Visualizer底层
- [ ] 集成到audit-plugin的report-writer流程

---

## 六、关键代码参考

### Critic Agent核心Prompt结构（可直接改造）

PaperBanana的Critic Prompt有清晰的 **Role → Task → Rules → Input → Output** 结构，可以直接fork改造为审计版：

```yaml
ROLE: 政府审计图表审查专家
TASK: 检查审计图表的内容准确性、布局合理性和规范合规性
RULES:
  1. Content:
     - 资金流向: 来源→路径→去向必须完整闭合
     - 组织层级: 上下级关系不得颠倒
     - 数据一致性: 图中数字必须与审计底稿一致
     - 法规引用: 条款编号必须正确
  2. Presentation:
     - 中文标签无错别字
     - 箭头方向语义明确（资金流/审批流/数据流用不同线型）
     - 配色符合政府审计报告规范（建议色板）
     - 涉密信息不得出现在可分发版本中
INPUT:
  - Target Diagram: [PNG截图]
  - Detailed Description: [当前图描述]
  - Audit Context: [审计场景说明]
  - Figure Caption: [图注]
OUTPUT: JSON {critic_suggestions, revised_description}
```

### Orchestrator模式

PaperVizProcessor的核心是 **async pipeline + semaphore并发控制**：

```python
# 关键模式
semaphore = asyncio.Semaphore(max_concurrent)
async def process_with_semaphore(doc):
    async with semaphore:
        return await self.process_single_query(doc)
```

这个模式可以直接复用到audit-plugin的批量审计底稿处理中。

---

## 七、总结

| 维度 | PaperBanana | 融策现状 | 差距/机会 |
|------|-------------|----------|-----------|
| 多Agent架构 | ✅ 5个 | ✅ audit-plugin多skill | 可借鉴编排模式 |
| Critic审查循环 | ✅ 3轮迭代 | ❌ 一次生成 | **最大差距，优先弥补** |
| Few-shot参考驱动 | ✅ PaperBananaBench | ❌ 无参考库 | 建立审计参考库 |
| 风格指南 | ✅ 自动合成 | ❌ 无审计规范库 | 编写政府审计风格指南 |
| 矢量可编辑 | ❌ 像素图 | ✅ drawio XML | **我们的优势，保持** |
| 中文支持 | ⚠️ 有限 | ✅ 完整 | 需要中文本地化改造 |

**核心判断**：PaperBanana最有价值的部分不是它的图片生成能力（我们已有更好的drawio），而是 **Critic审查循环 + Few-shot参考驱动 + 4维度评估体系**。将这3个设计模式嫁接到我们的drawio/arch-diagrammer上，可以在保持矢量可编辑优势的同时，获得多轮迭代的质量提升。
