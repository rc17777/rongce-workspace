# 融策AI知识中枢 - OpenClaw 使用说明

## Obsidian 首页

打开：

```text
C:\Users\scrccpa\Documents\Obsidian Vault\融策AI知识中枢.md
```

## 常用 RAG 查询

```powershell
python scripts\rag_query.py "工程审计 招投标 审计逻辑"
python scripts\rag_query.py "医保 卫健 数据审计 老年人健康管理 造假"
python scripts\rag_query.py "政策落实审计 两重 两新 审理"
```

## 新增资料后的手动同步流程

```powershell
python scripts\build_catalog.py
python scripts\enrich_and_sync_scene_cases.py
python scripts\rongce_v2_sync.py
python scripts\audit_v2_coverage.py
python scripts\rag_rebuild.py
```

## 当前状态

- Obsidian 场景案例库：可用
- 融策标准作业体系 v2.0：可用
- RAG 本地检索：可用
- LLM Wiki：基础可用，待主题化重构
- 自动同步：暂不启用
