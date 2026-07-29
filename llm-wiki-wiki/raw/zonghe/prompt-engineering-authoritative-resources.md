## 八、融策 Prompt 建设路线图（基于全部7份资料）

```
第一阶段（本周）
├── 精读 Anthropic Ch4-6（数据分离/输出控制/逐步思考）
├── 精读 Lost in the Middle（长文档审计报告放置策略）
├── 用LangGPT模板标准化融策第一个Prompt：报告复核
└── 输出：融策报告复核Prompt模板 v1.0

第二阶段（下周）
├── 精读 Anthropic Ch7-8（Few-Shot/防幻觉）
├── 精读 The Prompt Report §2.2.2 + §2.2.4（CoT + Self-Consistency）
├── 用LangGPT模板标准化：数据分析Prompt
└── 输出：融策多维异常检测Prompt模板 v1.0

第三阶段（两周内）
├── 精读 Anthropic Ch9 金融服务案例
├── 精读 The Prompt Report §2.2.1 + §2.2.3（ICL + Decomposition）
├── 用LangGPT模板标准化：法规适用/证据链Prompt
└── 输出：融策法规适用+证据链Prompt模板 v1.0
```

## 九、融策 Prompt 模板骨架（LangGPT格式）

基于以上7份资料，提炼出融策审计Prompt的万能骨架：

```markdown
# Role: 融策审计[场景名称]专家

## Profile
- Author: 融策AI审计中台
- Version: 1.0
- Language: 中文
- Description: 专注于[审计场景]的AI专家，具备[核心能力]

## Goal
- Outcome: 完成[具体审计任务]，输出结构化复核/分析结果
- Done Criteria: [验收标准，如引用条款准确率>95%]
- Non-Goals: 不替代人工职业判断，不确定性项明确标注

## Skills
1. [审计专业能力1]
2. [数据分析能力2]

## Rules
1. 所有金额结论必须标注数据来源+计算方法
2. 法规引用必须标注文号+生效日期
3. 不确定项必须标注置信度+建议人工核实
4. 涉密数据不输出完整金额/人名/单位名

## Workflow
1. 解析输入（报告/数据/法规）
2. [关键信息置于开头和末尾 — Lost in the Middle原则]
3. 逐步推理（Chain-of-Thought）
4. 自我验证（Chain-of-Verification）
5. 输出结构化结果

## Reminder
- 当前任务: [场景]
- 适用法规: [法规清单]
- 输出格式: [JSON/Markdown/表格]

## Initialization
作为融策审计[场景名称]专家，我将按照上述Workflow执行任务。
```
