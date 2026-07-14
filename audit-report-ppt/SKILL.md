---
name: audit-report-ppt
description: "审计报告/咨询报告PPT生成工作流。基于受众蒸馏+评审卡+页型映射三步法，自动生成可编辑的汇报级PPT。支持：审计发现汇报、整改报告、咨询方案展示、项目汇报。触发词：做PPT/生成PPT/汇报材料/审计报告PPT。"
---

# 审计报告PPT生成技能 (Audit Report PPT Generator)

## 一句话核心

先搞清"受众脑子怎么转"，再决定每页放什么。

## 适用场景

| 场景 | 受众 | 关键诉求 |
|------|------|---------|
| 审计发现汇报 | 被审单位领导层 | 问题定性+依据+整改方向 |
| 审计整改报告 | 上级领导/局领导 | 整改进度+成效+下一步 |
| 咨询方案汇报 | 客户决策层 | 价值+可行性+落地路径 |
| 项目进度汇报 | 甲方/管理层 | 成果+问题+计划 |
| 经责审计汇报 | 市委/区委领导 | 政绩评价+风险点 |

---

## 工作流程（5阶段）

### 阶段A：蒸馏受众（核心差异化）

**为什么要先蒸馏？** 审计报告不是写给自己看的，是写给"那个会决定结果的人"看的。

```
输入格式：
- 场景：审计发现汇报
- 受众：[具体人名/职务]，如"某区分管财务的副区长"
- 审计类型：经责审计/财务审计/专项审计
- 审计期间：20XX年X月-20XX年X月

女娲自动调度6个Agent并行：
1. 角色调研Agent → 该领导的决策风格、关注重点
2. 表达分析Agent → 该领导习惯的表达方式（数据型/定性型/折中型）
3. 审查偏好Agent → 该领导审阅报告时的常见关注点
4. 否决触发Agent → 什么会让领导直接质疑报告可信度
5. 注意力模型Agent → 领导看前3页时在想什么
6. 风险预判Agent → 报告中最容易引发追问的部分

输出：audience-card.md（受众卡）
```

**预设受众卡（快速开始，无需蒸馏）**

| 受众类型 | 预设为 | 核心特征 |
|----------|--------|----------|
| 地方政府领导 | 袁家军式 | 系统工程+数据闭环+可复制+不谈困难 |
| 被审单位一把手 | 问责防御型 | 关注责任边界+历史成因+整改可行性 |
| 上级审计机关 | 专业审慎型 | 法规依据充分+逻辑链条完整+证据闭环 |
| 被审计领导干部 | 自我保护型 | 关注表述措辞+定性程度+责任划分 |
| 企业管理层 | 效率优先型 | 问题+影响+解决方案，不谈过程 |

### 阶段B：蒸馏评审专家

**逻辑**：好的报告不是自己觉得好，而是过得了专家的审。

```
输入：
用女娲蒸馏一个"[评审角色]"，重点关注审查逻辑和否决习惯

预设评审专家：
- 被审单位一把手 → audit-leader-referee.skill
- 上级领导 → gov-leader-referee.skill
- 审计法规专家 → audit-law-referee.skill

输出：reviewer-card.md（评审卡）
```

**评审卡核心内容**
- 审查维度：从哪几个角度看报告
- 合格标准：每个维度什么水平算过关
- 否决触发器：什么情况会直接质疑
- 加分项：什么会赢得认可

### 阶段C：内容规划（PPT Director B阶段）

**核心公式**

```
受众关注什么（audience-card）
× 专家会怎么审（reviewer-card）
× 你有什么素材（审计数据/报告/取证记录）
= 每一页应该放什么、怎么放
```

**审计报告标准页型（17种中的核心9种）**

| 页型 | 代码 | 适用场景 | 审计报告示例 |
|------|------|----------|------------|
| 封面页 | T01 | 标题+副标题+汇报人 | 某区20XX年度财政收支审计报告 |
| 目录页 | T02 | 整体结构概览 | 审计范围/审计内容/主要发现 |
| 数字突出页 | T10 | 1-3个大数字 | 违规金额XXXX万 / 问题数量X个 |
| 对比页 | T06 | 改革前vs改革后 | 整改前后对比 / 制度执行前后 |
| 问题清单页 | T14 | 并列事项罗列 | 发现的X个问题分类汇总 |
| 时间轴页 | T16 | 里程碑/发展历程 | 审计时间线 / 违规行为时间线 |
| 证据链页 | T07 | 流程/步骤 | 资金流向/审批流程/操作链条 |
| 原因分析页 | T04 | 核心观点+要点 | 问题成因深度分析 |
| 整改建议页 | T17 | 结论+下一步 | 整改方向+责任单位+完成时限 |

**审计报告专属风格卡（蓝色汇报）**

```
颜色系统：
- primary: #003366（深蓝，标题和重点元素）
- secondary: #0066CC（科技蓝，图表和装饰）
- accent: #FF6600（橙色，问题高亮和警示）
- background: #F5F7FA（浅灰底色）
- warning: #CC0000（红色，严重问题标注）

字体系统：
- 标题：微软雅黑 Bold 28-32pt
- 副标题：微软雅黑 Regular 18-22pt
- 正文：微软雅黑 Regular 14-16pt
- 数据：DIN / Impact 48-72pt（大数字展示）

审计特定规则：
- 数字>100万用红色加粗
- 问题等级P0/P1/P2用对应颜色标注
- 法规依据用括号标注在具体问题后
- 每页文字不超过50字（审计报告尤忌堆砌）
```

### 阶段D：代码生成（python-pptx）

```bash
# 标准生成
python -m pptxgenjs --input delivery-doc.md --style audit-blue --output audit-report.pptx

# 快速生成（已有素材）
python -m pptxgenjs --material your-audit-report.txt --slides 10 --output presentation.pptx
```

**python-pptx核心代码模板**

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RgbColor
from pptx.enum.text import PP_ALIGN

# 创建16:9演示文稿
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_title_slide(prs, title, subtitle):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # 标题
    title_shape = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(12.333), Inches(1.5))
    tf = title_shape.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = RgbColor(0, 51, 102)  # #003366
    # 副标题
    sub_shape = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(12.333), Inches(0.8))
    tf2 = sub_shape.text_frame
    tf2.paragraphs[0].text = subtitle
    tf2.paragraphs[0].font.size = Pt(20)
    tf2.paragraphs[0].font.color.rgb = RgbColor(102, 102, 102)

def add_data_slide(prs, title, data_points):
    """数字突出页 T10"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # 标题
    title_shape = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    title_shape.text_frame.paragraphs[0].text = title
    title_shape.text_frame.paragraphs[0].font.size = Pt(32)
    title_shape.text_frame.paragraphs[0].font.bold = True
    # 数据点
    for i, (num, label, color) in enumerate(data_points):
        x = Inches(1 + i*4)
        num_shape = slide.shapes.add_textbox(x, Inches(2), Inches(3.5), Inches(1.5))
        num_shape.text_frame.paragraphs[0].text = num
        num_shape.text_frame.paragraphs[0].font.size = Pt(60)
        num_shape.text_frame.paragraphs[0].font.bold = True
        num_shape.text_frame.paragraphs[0].font.color.rgb = color
        label_shape = slide.shapes.add_textbox(x, Inches(3.5), Inches(3.5), Inches(0.8))
        label_shape.text_frame.paragraphs[0].text = label
        label_shape.text_frame.paragraphs[0].font.size = Pt(16)
```

### 阶段E：评审验证

**评审三检查**

```
对当前PPT执行评审三检查，按P0/P1/P2优先级输出修改清单：

P0（必须修改，否则汇报有风险）：
- 法规依据是否充分？领导可能质疑定性
- 数据来源是否标注？数字是否前后一致
- 问题表述是否留有余地？不能把话说死

P1（建议修改，改了明显更好）：
- 前3页是否抓住注意力？审计汇报第1页必须看到核心数字
- 每页是否超过50字？审计报告尤忌堆砌
- 页型是否与内容匹配？数字页不要放太多文字

P2（可优化）：
- 视觉是否有优化空间？
- 是否有遗漏的重要发现？
```

---

## 快速开始（3种路径）

### 路径1：政府审计汇报（最常用）

```
输入：
场景：审计发现汇报
受众：某区副区长（分管财政）
审计类型：财政收支审计
审计期间：2025年1月-12月
素材：[粘贴审计报告/取证记录]

执行步骤：
1. 用受众卡快速开始（无需蒸馏，省15分钟）
2. 用审计法规专家评审卡验证
3. 生成15页标准汇报PPT
4. 执行评审三检查
5. 按P0修改后重新生成
预计耗时：20-35分钟
```

### 路径2：被审单位整改汇报

```
输入：
场景：审计整改汇报
受众：被审单位一把手
审计问题：X个问题，Y个已整改，Z个整改中
整改成效：[量化数据]

执行步骤：
1. 蒸馏被审单位领导受众卡（关注责任边界）
2. 重点展示整改进度和成效
3. 生成整改报告PPT
预计耗时：15-25分钟
```

### 路径3：咨询方案汇报

```
输入：
场景：咨询方案汇报
受众：客户决策层
项目：[项目名称]
方案：[方案要点]

执行步骤：
1. 蒸馏客户决策层受众卡
2. 方案结构按"价值→可行性→落地路径"三段式
3. 生成咨询方案PPT
预计耗时：25-40分钟
```

---

## 受众蒸馏模板

当用户需要蒸馏特定受众时，使用以下标准模板：

```
用女娲蒸馏一个"[角色/职务]"，同时生成：
1. audience-card.md（作为受众想听什么）
2. reviewer-card.md（作为评审会挑什么毛病）

重点关注：
- 决策框架：什么因素决定他的判断
- 否决触发器：什么会让报告可信度打折扣
- 表达偏好：数据型/定性型/折中型
- 注意力分配：前3页他最关心什么

输出格式：.skill.md 格式，供PPT Director直接调用
```

---

## 禁止事项

- 不要在审计报告PPT中出现未经确认的数据
- 不要使用模糊定性（如"可能""大概"），审计报告必须明确
- 不要在政府汇报中混入被审单位的辩解内容
- 不要省略法规依据页（P0必须）
- 不要超过20页（政府汇报标准上限）

---

## 参考资料

- references/yuan-jiajun-audit-style.md（政府领导汇报风格）
- references/audit-report-page-types.md（审计报告页型详解）
- references/audit-blue-style-card.md（蓝色汇报风格卡）