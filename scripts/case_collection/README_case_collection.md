# 审计案例采集系统使用指南

## 系统概述

每周自动采集财政部政策和5省审计厅案例，经用户确认后按12业务线归档到本地和Obsidian。

## 工作流程

```
1. 每周运行采集器
   ↓
2. 生成待确认清单（JSON）
   ↓
3. 用户审核确认
   ↓
4. AI自动分类到12业务线
   ↓
5. 归档到本地+Obsidian
   ↓
6. 更新审计资料清单.json
```

## 使用步骤

### 1. 首次采集（测试）

```bash
python scripts/case_collector.py
```

输出：
- `logs/case_collection/pending/pending_YYYYMMDD_HHMMSS.json`
- 终端显示前10条预览

### 2. 查看待确认清单

打开生成的 JSON 文件，结构如下：

```json
{
  "collected_at": "2026-07-03T08:52:00",
  "total": 15,
  "items": [
    {
      "title": "关于加强预算绩效管理的通知",
      "url": "http://...",
      "source": "财政部预算司-绩效管理",
      "type": "policy",
      "hash": "abc123...",
      "collected_at": "2026-07-03T08:52:00"
    },
    ...
  ]
}
```

### 3. 确认要提取的案例

编辑 JSON 文件，添加确认标记：

```json
{
  "collected_at": "2026-07-03T08:52:00",
  "total": 15,
  "confirmed": true,
  "confirmed_items": [
    {
      "title": "关于加强预算绩效管理的通知",
      "url": "http://...",
      "source": "财政部预算司-绩效管理",
      "type": "policy",
      "hash": "abc123...",
      "collected_at": "2026-07-03T08:52:00"
    }
  ],
  "rejected_items": [...]
}
```

或者直接告诉我："确认提取第 1、3、5、8-12 条"，我帮你生成确认文件。

### 4. AI自动分类

```bash
python scripts/case_classifier.py logs/case_collection/pending/pending_20260703_085200.json
```

输出：
- `pending_20260703_085200_classified.json`
- 终端显示按12业务线分类结果

### 5. 归档到本地+Obsidian

```bash
python scripts/case_archiver.py logs/case_collection/pending/pending_20260703_085200_classified.json
```

效果：
- 按场景存到 `knowledge/cases/{场景}/`
- 按场景存到 `Obsidian Vault/审计案例库-OCR/{场景}/`
- 更新 `审计资料清单.json`

## 配置说明

### `config/case_sources.json`

```json
{
  "sources": {
    "mof_policies": {
      "enabled": true,  // 是否启用财政部采集
      "sites": [...]
    },
    "provincial_audit": {
      "enabled": true,  // 是否启用省级审计厅采集
      "sites": [...]
    }
  },
  "filters": {
    "exclude_keywords": ["通知", "公告", "会议"],  // 排除关键词
    "must_contain_any": ["审计", "检查", "评价"]   // 必须包含关键词
  }
}
```

### 12业务线映射

- 经济责任审计
- 收支审计
- 预算执行审计
- 专项资金审计
- 往来款清理
- 招投标审计
- 国企审计
- 成本效益审计
- 能源审计
- 工程竣工决算财务审计
- 预算绩效管理
- 政府补贴审计

## 定时任务

在 `HEARTBEAT.md` 中配置每周运行：

```markdown
### 上午检查（约9:00-10:00）
- [ ] 审计案例采集：运行 `python scripts/case_collector.py`，有新案例时推送
```

## 注意事项

1. **政府网站抓取不稳定**：部分网站采用 JS 渲染，简单抓取可能失败
2. **需要手动确认**：所有案例必须经过你确认才会归档
3. **文件名去重**：同一URL不会重复采集
4. **编码问题**：政府网站可能是 GBK，脚本会自动尝试多种编码

## 下一步优化

- [ ] 增加浏览器引擎支持（处理 JS 渲染页面）
- [ ] 增加全文抓取和摘要提取
- [ ] 增加审计逻辑自动提取
- [ ] 增加关键词、方法、发现类型标注

## 故障排查

```bash
# 查看采集历史
cat logs/case_collection/history.json

# 查看待确认清单
ls logs/case_collection/pending/

# 手动测试单个URL
python -c "from scripts.case_collector import fetch_page; print(fetch_page('http://...')[:1000])"
```
