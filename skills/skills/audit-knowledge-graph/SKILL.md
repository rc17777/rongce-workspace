---
name: audit-knowledge-graph
description: "审计知识图谱构建与分析 — 基于Neo4j图数据库的审计关系网络分析。涵盖关系建模、图数据可视化、知识图谱构建、隐蔽关联发现。适用于围标串标识别、关联交易发现、股权穿透等审计场景。Triggers: '知识图谱', 'Neo4j', '关系网络', '图数据库', '关联分析', '网络分析', '股权穿透', '小团伙'."
---

# 审计知识图谱构建与分析

## 概述

关系分析是审计最核心的能力之一。图数据库（Neo4j）专为处理关系设计，是审计场景中"发现隐蔽关联"的利器。本技能基于「数据化审计」公众号知识图谱系列（#38/#9/#11/#2/#6/#12/#26）。

## 适用场景

| 审计场景 | 图分析应用 |
|---------|-----------|
| **围标串标识别** | 投标人→法人→股东→地址多跳关系 |
| **关联交易发现** | 交易双方→控股关系→利益输送路径 |
| **股权穿透** | N层股权穿透发现实际控制人 |
| **担保圈分析** | 互保连环圈→系统风险识别 |
| **资金流向追踪** | 资金链路→最终流向分析 |
| **供应商围猎** | 供应商→员工→亲属关系网络 |
| **骗取补贴** | 受益人→地址→电话→法人多重关联 |

## Neo4j基础

### 安装
- 下载：https://neo4j.com/download/
- 社区版免费，桌面版带可视化浏览器
- 默认端口：7474（HTTP）/ 7687（Bolt）

### 核心概念

| 概念 | 说明 | 审计示例 |
|------|------|---------|
| **节点(Node)** | 实体 | 公司、个人、银行账户、项目 |
| **关系(Relationship)** | 节点之间的连接 | 控股、担任、交易、担保、同一地址 |
| **属性(Property)** | 节点/关系的键值对 | 公司名称、注册资本、交易金额 |
| **标签(Label)** | 节点的类型标记 | :Company, :Person, :Account |
| **路径(Path)** | 多跳关系链 | 公司A→法人B→控制公司C |

### Cypher查询语言示例

```cypher
// 创建公司节点
CREATE (c:Company {name: 'A公司', reg_capital: 1000})

// 创建控股关系
MATCH (a:Company {name: 'A公司'}), (b:Company {name: 'B公司'})
CREATE (a)-[:控股 {ratio: 0.51}]->(b)

// N度关系查询：找出两个公司之间所有路径
MATCH path = (a:Company {name: 'A公司'})-[*1..5]-(b:Company {name: '目标公司'})
RETURN path

// 发现"小团伙"：互相关联紧密的子图
MATCH (a:Company)-[r:投标于]->(p:Project)
WHERE p.name IN ['项目X', '项目Y', '项目Z']
WITH a, count(DISTINCT p) as projects
WHERE projects > 1
RETURN a.name, projects
ORDER BY projects DESC
```

## 审计知识图谱构建流程

### 步骤1：数据建模
定义实体类型和关系类型：

```
实体：Company, Person, Project, Account, Address, Phone
关系：控股, 担任(法人/董事/监事), 投标, 中标, 交易, 同地址, 同电话
```

### 步骤2：数据提取
从多源数据中提取实体和关系：
- **工商数据**：天眼查/企查查 → 股权结构、高管
- **招投标数据**：招标公告/中标公告 → 投标人和项目关系
- **财务数据**：科目余额表/序时账 → 交易关系
- **发票数据**：购销双方 → 交易网络
- **合同数据**：签署方 → 合同关系网

### 步骤3：数据导入
```cypher
// 批量导入CSV
LOAD CSV WITH HEADERS FROM 'file:///companies.csv' AS row
CREATE (:Company {
  name: row.name,
  reg_no: row.reg_no,
  reg_capital: toInteger(row.reg_capital)
});

// 批量导入关系
LOAD CSV WITH HEADERS FROM 'file:///holdings.csv' AS row
MATCH (a:Company {name: row.from}), (b:Company {name: row.to})
CREATE (a)-[:控股 {ratio: toFloat(row.ratio)}]->(b);
```

### 步骤4：图分析
关键分析模式：

#### 中心度分析：找出网络中最重要的节点
```cypher
// 按交易关系数排序 → 找出最活跃的交易对手
MATCH (a:Company)-[r:交易]->(b:Company)
RETURN a.name, count(r) as trade_count
ORDER BY trade_count DESC LIMIT 20
```

#### 社区发现：找出关系紧密的群体
```cypher
// Louvain算法（需安装GDS插件）
CALL gds.louvain.stream('myGraph')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name, communityId
```

#### 最短路径：发现隐蔽关联
```cypher
// 投标人和评标专家之间有没有间接联系？
MATCH path = shortestPath(
  (bidder:Company {name: '投标人A'})-[*..5]-(expert:Person {name: '评标专家B'})
)
RETURN path
```

## 与关系网络分析的互操作

### 使用Pajek进行社交网络分析
```python
# 将Neo4j结果导出为Pajek格式
# Pajek (.net) 格式用于专业社会网络分析
# 可以计算：度中心性、中介中心性、接近中心性、聚类系数
```

### Excel → Pajek
参见文章 #26：将Excel数据转为Pajek可用的关系数据

## 非结构化数据中的关系提取

参见文章 #6：如何解析非结构化文档文本中的隐蔽关系

关键思路：从合同、会议纪要、邮件等文档中提取人名/公司名 → 构建关系对 → 导入图数据库。

## 审计知识图谱的构建（文章 #38）

知识图谱在审计中有三重价值：
1. **知识检索**：用图结构组织审计法规、案例、方法知识库
2. **关联发现**：实体间的隐蔽关系自动浮现
3. **推理辅助**：基于图谱规则推导新的审计线索

### 构建路线
```
政策法规文本 → NLP实体抽取 → 实体+关系三元组 → 知识图谱
审计案例     → 结构化标注   → 案例特征+结论  → 图谱节点
业务数据     → ETL + 映射   → 实体关系       → 图谱边
```

## 与融策业务的结合

1. **围标串标识别（融合procurement-audit-models）**：投标人→法人→股东→地址→电话五跳关系图谱
2. **专项债项目穿透**：项目→实施单位→负责人→关联公司关系链
3. **绩效评价**：资金流向→最终受益人图谱
4. **资产清查**：资产→使用人→部门→关联方关系网

## 参考

- Neo4j官网：https://neo4j.com/
- Neo4j Graph Data Science (GDS)：https://neo4j.com/docs/graph-data-science/
- Pajek：http://mrvar.fdv.uni-lj.si/pajek/
- 知识库：`knowledge/数据化审计/`（#38 审计知识图谱、#9/#11 Neo4j系列）
- 关联技能：`procurement-audit-models`、`audit-data-analysis-methods`（关联规则 #06）
