# AgentDebugX：LLM Agent调试框架

> 来源：AI猩哥（微信公众号） | 2026-07-22
> 原文：https://mp.weixin.qq.com/s/oTjoZMpBghDr88mxvYEyRg
> 入库：2026-07-23 | 标签：AI Agent, 调试工具, 多智能体, 根因分析, AgentDebugX

## 摘要

来自伊利诺伊大学厄巴纳-香槟分校、斯坦福大学、Google、多伦多大学的研究团队发布的开源工具包 AgentDebugX，面向LLM Agent的本地化调试框架。核心流程：Detect（检测）→ Attribute（归因）→ Recover（修复）→ Rerun（重跑），把调试从"人工翻日志猜原因"变成结构化的闭环诊断流程。

## 为什么AI Agent调试难

- 错误暴露的位置往往不是错误发生的位置（第10步报错，根因可能在第3步）
- 传统可观测性工具只能重放trace，没有归因和修复
- 自我修正方法不知道错在哪，效果有限

## AgentDebugX 核心机制

### 四步闭环

1. **Detect（检测）**：确定性规则包（格式错误/无进展循环/无效输出/过早成功声明）+ LLM裁判模式
2. **Attribute（归因）**：多种策略——all-at-once / step-by-step / binary search / 反事实归因 / DeepDebug
3. **Recover（修复）**：自动生成带证据的修复建议（Reflexion/CRITIC/Self-Refine/AutoManual）
4. **Rerun（重跑）**：从检查点重新执行，保留原始+修复分支对比，失败则重新进入调试循环

### DeepDebug：复杂故障深度诊断

三步骤：
1. 全局轨迹读取
2. 结构引导探查（多Agent追踪交接点，单Agent用二分法）
3. 交叉验证 → 输出可审计报告（责任Agent+步骤+证据+修复方案）

## 实测数据

- **归因准确率**：DeepDebug（qwen3.5-9b）达到28.8%严格Agent+步骤准确率，单轮基线21.7%
- **修复成功率（GAIA基准）**：73个失败任务中修复13个（基线4-6个），整体准确率55.8%→63.6%
- 结论：先精准定位根因再修复 >> 盲目自我修正

## 其他亮点

- 框架无关的统一trace格式（LangGraph/CrewAI/OpenAI Agents SDK/OpenTelemetry）
- Error Hub 错误共享库（脱敏后可做CI回归测试用例、调试记忆）
- 本地化优先（trace留在本地，共享可选）
- 多种使用方式：Python库/CLI/Web控制台/Agent技能

## 快速上手

```bash
pip install agentdebugx          # 基础安装
pip install "agentdebugx[all]"   # 含UI和框架适配器
```

```python
from agentdebug import AgentDebug, EventType
debugger = AgentDebug()
with debugger.trace(goal="预订机票", framework="my-agent") as trace:
    trace.record(EventType.PLAN, agent_name="planner", step_index=1, output="搜索票价")
    # ...
    report = trace.analyze()
    print(report.summary)
```

## 对融策的启示

融策多Agent审计平台v3.0有22个Agent，当前handover_protocol v1.0只解决状态交接，缺乏系统化的调试和根因分析工具。AgentDebugX的四步闭环可以直接参考：
- 用确定性规则检测审计Agent常见失败模式（格式错误/循环/过早结论）
- 用DeepDebug思路定位多Agent协作中的错误交接点
- Error Hub可积累审计Agent失败案例作为回归测试

## 资源链接

- 论文：待补充
- GitHub：待补充
- 安装：`pip install agentdebugx`
