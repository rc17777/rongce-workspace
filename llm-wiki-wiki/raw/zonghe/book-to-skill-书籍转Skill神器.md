---
title: 夯爆了！这个开源神器把任意书籍转成 Skill，轻松打造专业的随身顾问
source: 微信公众号「极客之家」
url: https://mp.weixin.qq.com/s/6haAPXdwN38rOWx5mnsbIg
date: 2026-06-14
tags: [skill, 知识管理, book-to-skill, 开源工具, token优化]
---

# book-to-skill：把书编译成 Agent Skill

GitHub: https://github.com/virgiliojr94/book-to-skill （5.3k⭐）

## 核心机制

不是 PDF 阅读器，是**编译管线**：书/文档 → 完整 Agent Skill，输出到 `~/.claude/skills/<slug>/`：

- **SKILL.md**：核心心智模型 + 章节索引（~4000 token）
- **chapters/**：每章一个文件（800-1200 token），**按需加载**——不问第五章，第五章不占 token
- **glossary.md**：术语表（按字母排，标章节出处）
- **patterns.md**：技术模式/算法/设计模式
- **cheatsheet.md**：决策表和速查规则

## 支持格式

PDF、EPUB、DOCX、TXT、MD、RST、AsciiDoc、HTML、RTF、MOBI/AZW3。

智能选提取器：技术书（代码/表格/公式）走 **Docling**（1.5秒/页，保表格代码块）；纯文本走 **pdftotext**（秒出），fallback PyPDF2 → pdfminer.six。

基准（103页技术书）：pdftotext 0.1s/27K token/丢全部表格代码 vs Docling 164s/保住48表格+36代码块。

## 质量原则

- 密度优先于完整：1000 token 摘要 > 10000 token 摘录
- 实践者口吻：「用X当Y」，不是「本书解释了X」
- 永不复制原文：始终合成、总结、提取信号

## 成本

用 Claude Sonnet 4.5 转换，一本书 ¥5-10 一次性：

| 书 | 页数 | Token | 花费 |
|:--|:--|:--|:--|
| Think Python 2 | 244 | 119K | $0.88 |
| Working Backwards | 371 | 175K | $0.96 |
| Pro Git | 501 | 229K | $1.23 |

## vs 直接灌PDF vs RAG

- **vs 灌PDF**：400页PDF≈200K token 每轮重复烧；skill 一次编译后每次查询只加载 4K核心+1K章节。500页 Pro Git 差 **51倍**。且避免「lost in the middle」精度丢失。
- **vs RAG**：RAG 查询时工作（切块→嵌入→相似检索），擅长「找到提到X的那段」；book-to-skill 编译时工作（深度分析提取作者框架），回答「作者的12个框架是什么、何时用哪个」。**几十本书浅层搜索用 RAG，一两本书深度应用用 skill，互补。**
- Discovery Loop Tax 实测：比灌PDF省 24-51倍 token，比 Agent 自己翻书省 2.4-15.6倍。

## 用法

```bash
git clone https://github.com/virgiliojr94/book-to-skill.git ~/.claude/skills/book-to-skill
# 或会话内：Install book-to-skill: https://raw.githubusercontent.com/virgiliojr94/book-to-skill/master/SKILL.md

/book-to-skill ~/book.pdf              # slug 自动生成
/book-to-skill ~/book.epub my-slug     # 指定 slug
/book-to-skill file1.pdf file2.txt merged-skill  # 多文件合并
/book-to-skill ~/docs/ project-knowledge          # 整个文件夹
/book-to-skill new.pdf ~/.claude/skills/existing  # 增量更新（活的skill）
```

查询：`/slug` 加载核心、`/slug 主题`、`/slug ch05`、`/slug "what chapters?"`

依赖检查：`python3 scripts/extract.py --check`

## 限制

- 章节自动检测依赖标准格式（"Chapter N"/"第N章"），罗马数字/纯标题分段需手动指定
- 转换烧 token（一本书 119K-301K），用便宜模型跑

## 不止于书

docs/ 文件夹、品牌规范、论文集群+笔记、RFC、API合约、合规文档——凡是「反复打开同一个文档、每次都想记住」的东西都适合做 skill。
