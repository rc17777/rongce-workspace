#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
HUB = VAULT / '融策AI知识中枢.md'
NAV_DIR = VAULT / '融策AI知识中枢'
SCENE_DIR = NAV_DIR / '场景导航'

SCENES = {
    '工程审计': ['招投标链条拆解', '合同支付穿透', '现场踏勘', '工程量/变更签证核查'],
    '政策落实审计': ['政策链条对标', '资金直达核查', '部门协同验证', '整改回头看'],
    '医保卫健数据审计': ['医保结算比对', 'HIS诊疗明细核验', '死亡/年龄逻辑校验', 'SQL疑点筛查'],
    '国企审计': ['三重一大核查', '国资安全', '异常交易筛查', '内控测试'],
    '农业农村审计': ['涉农资金比对', '受益对象核验', '高标准农田现场核查', '乡村振兴绩效'],
    '绩效审计': ['绩效目标对标', '投入产出分析', '指标完成度分析', '整改闭环'],
}

HUB_CONTENT = f'''---
title: "融策AI知识中枢"
scene: 知识中枢
tags: [融策, AI知识中枢, Obsidian, RAG, LLM Wiki]
updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 融策AI知识中枢

> 总入口：从这里进入 Obsidian 案例库、融策标准作业体系 v2.0、LLM Wiki、RAG 本地检索和同步流程。

## 1. 今天能直接用什么

| 模块 | 入口 | 状态 |
|---|---|---|
| 场景案例库 | [[审计案例库-OCR]] | 已按场景同步，逐篇带“融策审计逻辑提炼” |
| 融策标准作业体系 v2.0 | [[审计案例库-OCR/融策标准作业体系 v2.0/00-覆盖率与同步机制说明|覆盖率与同步机制说明]] | 已覆盖真实案例/文章 |
| 全库训练清单 | [[审计案例库-OCR/融策标准作业体系 v2.0/01-训练清单/场景-审计逻辑-可复用方法训练清单 v2.0|训练清单 v2.0]] | 已全量覆盖 |
| 案例卡片 | [[审计案例库-OCR/融策标准作业体系 v2.0/02-案例卡片|精选案例卡片]] | 已生成精选卡片 |
| 项目模板包 | [[审计案例库-OCR/融策标准作业体系 v2.0/03-融策审计项目可直接套用模板包|项目模板包]] | 可直接改用 |
| 标准作业包 | [[审计案例库-OCR/融策标准作业体系 v2.0/04-融策标准作业包 v2.0|标准作业包 v2.0]] | 可作为公司作业骨架 |
| 实战试点包 | [[审计案例库-OCR/融策标准作业体系 v2.0/05-融策实战试点包 v2.0|实战试点包 v2.0]] | 工程/政策/信息系统/国企/农业农村 |
| RAG 查询 | [[融策AI知识中枢/RAG查询示例库|RAG查询示例库]] | 本地检索可用 |
| 同步流程 | [[融策AI知识中枢/新增资料同步SOP|新增资料同步SOP]] | 手动同步，暂不自动定时 |

## 2. 高频场景入口

- [[融策AI知识中枢/场景导航/工程审计导航|工程审计导航]]
- [[融策AI知识中枢/场景导航/政策落实审计导航|政策落实审计导航]]
- [[融策AI知识中枢/场景导航/医保卫健数据审计导航|医保卫健数据审计导航]]
- [[融策AI知识中枢/场景导航/国企审计导航|国企审计导航]]
- [[融策AI知识中枢/场景导航/农业农村审计导航|农业农村审计导航]]
- [[融策AI知识中枢/场景导航/绩效审计导航|绩效审计导航]]

## 3. 一句话使用法

- **要找案例**：进场景导航或训练清单。
- **要写方案**：进项目模板包或实战试点包。
- **要查知识**：用 RAG 查询示例。
- **要新增资料**：按同步 SOP 执行。
- **要培训团队**：从案例卡片 + 标准作业包开始。

## 4. 当前状态

- Obsidian 场景案例库：可用。
- 融策标准作业体系 v2.0：可用。
- RAG 本地检索：可用。
- LLM Wiki：基础可用，主题化重构进行中。
- 自动同步：按要求暂不启用。
'''

RAG_EXAMPLES = '''---
title: "RAG查询示例库"
scene: 知识中枢
tags: [融策, RAG, 查询示例]
---

# RAG 查询示例库

## 工程审计

```powershell
python scripts\rag_query.py "工程审计 招投标 审计逻辑"
python scripts\rag_query.py "围标串标 投标文件 雷同 数据分析"
python scripts\rag_query.py "工程变更签证 审计疑点 取证路径"
```

## 政策落实审计

```powershell
python scripts\rag_query.py "政策落实审计 两重 两新 审理"
python scripts\rag_query.py "重大政策落实 资金直达 整改闭环"
python scripts\rag_query.py "京津冀协同 审计逻辑 政策链条"
```

## 医保卫健数据审计

```powershell
python scripts\rag_query.py "医保 卫健 数据审计 老年人健康管理 造假"
python scripts\rag_query.py "医院 串换诊疗项目 过度诊疗 数据分析"
python scripts\rag_query.py "死亡人员 体检记录 SQL 疑点筛查"
```

## 国企审计

```powershell
python scripts\rag_query.py "国企审计 三重一大 投资决策 内控"
python scripts\rag_query.py "高新技术企业 奖补资金 虚假申报 相似度算法"
```

## 农业农村审计

```powershell
python scripts\rag_query.py "乡村振兴 审计 涉农资金 高标准农田"
python scripts\rag_query.py "农业农村 补贴资金 受益对象 核验"
```

## 重建索引

```powershell
python scripts\rag_rebuild.py
```
'''

SYNC_SOP = '''---
title: "新增资料同步SOP"
scene: 知识中枢
tags: [融策, 同步SOP, Obsidian]
---

# 新增资料同步 SOP

> 当前不启用每日自动同步。新增一批案例、文章、政策法规后，手动执行以下步骤。

## 1. 入库要求

- PDF/Word/Markdown 先放入 Obsidian 对应资料目录。
- OCR 后 Markdown 至少要有 `scene` 字段。
- 推荐 YAML 字段：`title`、`scene`、`tags`、`keywords`、`findings`、`recommendations`。

## 2. 执行命令

在 OpenClaw workspace：

```powershell
python scripts\build_catalog.py
python scripts\enrich_and_sync_scene_cases.py
python scripts\rongce_v2_sync.py
python scripts\audit_v2_coverage.py
python scripts\rag_rebuild.py
```

## 3. 验证标准

- `审计资料清单.json` 更新。
- 新资料有 `融策审计逻辑提炼` 模块。
- 新资料同步到对应 `审计案例库-OCR/<审计场景>/`。
- `audit_v2_coverage.py` 输出 `TRAINING_MISSED 0`。
- RAG 查询能搜到新增资料。

## 4. 注意事项

- 场景库会产生副本，总条目数会增加，不能把总条目数等同于原始案例数。
- 执行 `enrich_and_sync_scene_cases.py` 会批量写原文，确认需要同步后再跑。
'''


def main():
    NAV_DIR.mkdir(parents=True, exist_ok=True)
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    HUB.write_text(HUB_CONTENT, encoding='utf-8')
    (NAV_DIR / 'RAG查询示例库.md').write_text(RAG_EXAMPLES, encoding='utf-8')
    (NAV_DIR / '新增资料同步SOP.md').write_text(SYNC_SOP, encoding='utf-8')
    for scene, methods in SCENES.items():
        content = f'''---
title: "{scene}导航"
scene: 知识中枢
tags: [融策, 场景导航, {scene}]
---

# {scene}导航

## 1. 场景案例库

- [[审计案例库-OCR/{scene}|{scene}案例库]]

## 2. v2.0 标准作业入口

- [[审计案例库-OCR/融策标准作业体系 v2.0/01-训练清单/场景-审计逻辑-可复用方法训练清单 v2.0|全库训练清单 v2.0]]
- [[审计案例库-OCR/融策标准作业体系 v2.0/02-案例卡片|案例卡片]]
- [[审计案例库-OCR/融策标准作业体系 v2.0/03-融策审计项目可直接套用模板包|项目模板包]]
- [[审计案例库-OCR/融策标准作业体系 v2.0/05-融策实战试点包 v2.0|实战试点包]]

## 3. 常用方法

{chr(10).join('- ' + m for m in methods)}

## 4. 推荐动作

1. 先查同类案例。
2. 再套项目模板。
3. 最后用 RAG 查询补充政策、方法和案例。
'''
        (SCENE_DIR / f'{scene}导航.md').write_text(content, encoding='utf-8')
    print('WROTE_HUB', HUB)

if __name__ == '__main__':
    main()
