# OpenClaw 6个PPT/海报Skill推荐

> 来源：OpenClaw腾讯云社区（微信公众号）
> 抓取时间：2026-06-26
> 原文：https://mp.weixin.qq.com/s/hQpQd28wZi7MUAFQkWNTVQ

---

## 1. ppt-maker — 本地生成，零API费用

- **特点**：完全本地运行，不需要API Key，生成标准.pptx文件，可用PowerPoint/WPS打开编辑
- **速度**：1分钟生成完整PPT（封面、目录、内容页、数据图表）
- **6种风格主题**：

| 主题名 | 风格 | 适合场景 |
|-------|------|---------|
| ocean | 蓝色海洋 | 科技/专业汇报 |
| sunset | 橙红日落 | 温暖/创意分享 |
| purple | 紫罗兰 | 设计感演示 |
| luxury | 黑金奢华 | 高端/产品提案 |
| midnight | 深夜暗色 | 震撼感发布 |
| classic | 经典绿 | 商务/正式报告 |

- **数据图表**：饼图、柱状图、折线图都能正确渲染，数据来自用户描述
- **安装**：`clawhub install ppt-maker`

---

## 2. powerpoint-pptx — 功能最全的专业级PPT Skill

- **核心能力**：
  - 支持套用现有.pptx模板
  - 自动插入图表、表格、讲者备注
  - 视觉检查（对齐/重叠/裁切/对比度）
  - 批量处理：合并、提取文本、导出PDF
  - 跨平台兼容（Windows/Mac/LibreOffice）
- **安装**：`clawhub install powerpoint-pptx` + `pip install python-pptx`

---

## 3. Skywork PPT — 深度研究逻辑，直接可演示

- **特点**：先做内容梳理再排版，逻辑结构更完整，不是简单文字堆砌
- **适用**：定期产出周报/月报PPT，配置一次模板后可定时自动生成
- **安装**：`clawhub install skywork-ppt`

---

## 4. claw-poster — 营销海报设计

- **适用场景**：电商促销横幅、小红书/公众号封面、活动通知、品牌宣传物料
- **安装**：`clawhub install claw-poster`（需要API Key）

---

## 5. seedance-image — 中文图像生成首选

- **特点**：对中文提示词支持最佳，无需翻译英文
- **适用**：插画风配图、治愈系小清新、科技感展示、公众号文章配图
- **安装**：`openclaw skills install seedance-image`（需要即梦API Key）

---

## 快速安装指南

| Skill | 主要用途 | 安装命令 | 需要API Key |
|-------|---------|---------|------------|
| ppt-maker | PPT本地生成 | `clawhub install ppt-maker` | 否 |
| powerpoint-pptx | 专业级PPT | `clawhub install powerpoint-pptx` | 否 |
| skywork-ppt | 智能内容PPT | `clawhub install skywork-ppt` | 否 |
| claw-poster | 营销海报 | `clawhub install claw-poster` | 是 |
| seedance-image | 中文图像生成 | `openclaw skills install seedance-image` | 是（即梦） |

---

## 对融策的启发

- **ppt-maker**（本地、零费用、.pptx输出）非常适合我们的审计报告PPT/标书PPT场景，不需要额外API成本
- **powerpoint-pptx**（套模板、批量处理）适合需要统一融策模板、批量合并多份PPT的场景
- **skywork-ppt**（内容梳理+定时生成）适合定期周报/月报自动化
- **seedance-image** 可作为公众号文章配图、审计宣传物料的辅助工具

---

## 相关资源

- ClawHub: https://clawhub.ai
- OpenClaw官方文档: https://docs.openclaw.ai/zh-CN
