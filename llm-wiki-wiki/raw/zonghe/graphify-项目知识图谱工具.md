# graphify — 项目代码知识图谱工具

> 来源：公众号「AI智沐笔记」| 入库：2026-07-19
> GitHub: https://github.com/Graphify-Labs/graphify (85.2万星)
> 安装：`uv tool install graphifyy` 或 `pipx install graphifyy`
> PyPI包名：graphifyy（双y），命令：graphify

---

## 功能

把整个项目（代码/文档/PDF/图像/视频）映射为可查询的知识图谱。

### 核心特性

- **本地AST解析**：用 tree-sitter 做确定性代码抽取，无上传
- **边有出处**：EXTRACTED（源码写明的） / INFERRED（推断的）
- **非向量库**：真正可遍历的图，无embedding

### 输出

```
graphify-out/
├── graph.html       ← 浏览器可视化（点节点、搜索、按社区过滤）
├── GRAPH_REPORT.md  ← 高亮摘要（God nodes、意外连接、建议提问）
└── graph.json       ← 完整图谱数据
```

---

## 三招核心用法

| 命令 | 功能 | 场景 |
|:--|:--|:--|
| `graphify explain "APIRouter"` | 解释节点（位置/社区/连接度/上下游） | 接手陌生项目 |
| `graphify path "FastAPI" "ModelField"` | 查两点间路径（最短跳数+每跳关系） | 改需求前确认影响链 |
| `graphify query "what connects auth to database?"` | 自然语言查询子图 | 理解模块关系 |

---

## GRAPH_REPORT 三个看点

1. **God Nodes** — 连接度最高的枢纽节点（改bug前先扫）
2. **Surprising Connections** — 跨文件的意外连接（隐藏耦合入口）
3. **Communities** — Leiden算法拓扑聚类（颜色块≈模块边界）

---

## 融策适用场景

| 场景 | 用途 |
|:--|:--|
| 接手一个复杂审计脚本项目 | 先 `graphify .` 出图，再按社区消化 |
| 审计工具链代码审查 | 检查模块间依赖是否合理 |
| 审计数据分析脚本维护 | 改代码前 `graphify path` 确认影响范围 |

> ⚠️ 这是代码开发工具，非审计业务工具。如果融策不自行开发审计分析脚本，此工具优先级较低。
