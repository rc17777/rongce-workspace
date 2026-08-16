---
name: reflection
description: "Structured self-reflection and review. Learns when to stop and self-critique before delivering work. Also reviews recent work sessions to capture what went well, what went wrong, and what to improve. Triggers: '反思', 'review', '复盘', '回顾总结', '自我检查', '反省', 'what could I have done better', '事后复盘'."
---

# Reflection Skill

## Two Modes

### Mode 1: Pre-Delivery Self-Critique

Before delivering any non-trivial output, the system should pause and self-check:

1. **完整性检查**
   - 用户的所有需求是否都覆盖到了？
   - 有没有遗漏什么细节假设？
   - 有没有"我以为"但实际没做对的地方？

2. **准确性检查**
   - 数据引用是否正确？
   - 有没有编造不存在的数据或事实？
   - 分析逻辑有没有漏洞？

3. **清晰度检查**
   - 结论是否在开头？
   - 有没有不必要的废话/重复？
   - 用词是否精确（数据精确到小数点，不用模糊词）？

4. **可行性检查**
   - 交付物的接收方能否直接使用？
   - 是否需要额外步骤/工具才能用？
   - 有没有给出下一步行动建议？

**Output if issues found:**
```
⚠️ 自我检查发现3个问题：
1. [问题描述] → 修改/补充/说明
2. ...
```

### Mode 2: Session Review (Post-Work)

Use for end-of-work or end-of-day retrospective:

```markdown
## 📋 工作复盘

### 做了什么
- 任务A: [简述]
- 任务B: [简述]

### 做得好
- [具体] — 因为...下次继续保持
- [具体] — 因为...

### 能更好
- [具体] — 下次改为...
- [具体] — 下次改为...

### 学到的东西
- [知识点/经验]
- [之前踩过的坑不再踩]

### 下一步
- 待办事项
- 需要用户确认的
```

### Reflection Prompts

| 场景 | 提示问题 |
|:----|:---------|
| 交付前 | "用户拿到这个，第一反应会是什么？能直接用吗？" |
| 数据交付 | "数据源完整吗？有没有遗漏？格式用户能打开吗？" |
| 方案建议 | "我有没有站在用户的实际业务场景想，还是只给了通用方案？" |
| 客户沟通 | "语气合适吗？有没有太技术化？有没有该解释的没解释？" |
