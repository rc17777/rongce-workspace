# 智析智能 · 数据采集模块 SKILL

## 触发条件
当用户提及以下关键词时，读取并按照本SKILL使用 `zhixi_intelligent` 模块：
- "连接数据库" / "连数据库" / "数据库连接"
- "扫描表结构" / "元数据" / "有哪些表" / "看看表"
- "采集进度" / "看板" / "dashboard" / "进度报告"
- "数之联" / "审计厅合同" / "数据采集三件套"
- "登记采集" / "采集了XX数据"

## 模块位置
```
D:\openclaw-workspace\zhixi_intelligent\
  ├─ __init__.py
  ├─ connector.py   # 数据库连接器
  ├─ scanner.py     # 元数据扫描器
  ├─ dashboard.py   # 采集进度看板
  ├─ reports/       # JSON报告输出
  └─ dashboards/    # HTML看板输出
```

## 导入方式（必须用这个）
```python
import sys
sys.path.insert(0, r"D:\openclaw-workspace")
from zhixi_intelligent import DatabaseConnector, MetadataScanner, CollectionDashboard
```

## 核心API

### 1. 数据库连接器 DatabaseConnector

```python
connector = DatabaseConnector()

# 连接数据库
connector.connect(
    name="连接名",       # 如"省财政厅"
    db_type="mysql",     # mysql/postgresql/sqlite/sqlserver/oracle/dameng/shengtong
    host="10.x.x.x",     # 主机地址
    port=3306,           # 端口
    database="库名",     # 数据库名
    user="用户名",
    password="密码"
)

# SQLite快速连接
connector.quick_connect("sqlite", "D:/path/to/file.db")

# 查看所有连接
connector.list_connections()   # → ["省财政厅", "省社保局"]
connector.status()             # → {"total": 2, "connections": [...]}

# 断开
connector.disconnect("连接名")
```

### 2. 元数据扫描器 MetadataScanner

```python
scanner = MetadataScanner(connector)

# 全量扫描
scanner.scan("连接名")  # → dict(完整元数据)

# 摘要（给用户看）
scanner.scan_summary("连接名")  # → {"数据表": "68张", "表清单": [...]}

# 按模式过滤
scanner.scan("连接名", table_filter="fiscal_%")

# 导出JSON
scanner.export_to_json("连接名", "D:/output/metadata.json")
```

### 3. 采集进度看板 CollectionDashboard

```python
dashboard = CollectionDashboard()

# 登记一次采集
dashboard.register(
    industry="财政财务",      # 13行业之一
    data_source="省财政厅",   # 来源
    table_count=68,           # 表数
    row_count=8500000,        # 行数
    size_gb=320.0,            # 大小GB
    status="completed",       # completed/in_progress/pending/failed
    note="备注"
)

# 生成报告
report = dashboard.generate_report()  # → dict

# 保存
dashboard.save_report("zhixi_intelligent/reports/xxx.json")
dashboard.save_html("zhixi_intelligent/dashboards/xxx.html")

# 从真实数据库扫描结果自动更新（高级用法）
dashboard.bind_scanner(connector, scanner)
dashboard.auto_update_from_scan("连接名", {"fiscal": "财政财务", "edu": "教科文卫"})
```

## 数据库类型映射

| 用户说 | db_type参数 |
|--------|------------|
| MySQL | "mysql" |
| PostgreSQL / pg | "postgresql" |
| SQL Server / mssql | "sqlserver" |
| Oracle | "oracle" |
| SQLite / 本地文件 | "sqlite" |
| 达梦 / DM | "dameng" |
| 神通 / Oscar | "shengtong" |

## 操作模板

### 场景A：用户要连接数据库
1. 确认数据库类型
2. 确认连接参数（主机/端口/库名/用户名/密码）
3. 调用 `connector.connect()` 连接
4. 返回结果给用户
5. 如果失败，告知错误原因和排查建议（网络/防火墙/驱动/密码/权限）

### 场景B：用户要扫描数据库
1. `connector.list_connections()` 获取可用连接
2. 只有一个 → 直接扫描；多个 → 让用户选
3. `scanner.scan_summary("连接名")` 获取摘要
4. 展示表清单和字段预览给用户

### 场景C：用户要生成看板
1. 用 `dashboard.render_html()` 生成HTML
2. 保存到 `zhixi_intelligent/dashboards/`
3. 用 `start` 命令在浏览器打开
4. 同时保存JSON报告到 `zhixi_intelligent/reports/`

### 场景D：用户要登记采集进度
1. 确认：行业/来源/表数/行数/数据量/状态
2. `dashboard.register(...)` 登记
3. 询问是否要生成看板预览

## 13个行业清单（来自合同）
工商、财政财务、民生民政、教科文卫、社保医保、公积金、企业及金融机构、重大投资项目、公共资源交易、农业、高校、医院、其他

## 注意事项
- 密码等敏感信息不写入 MEMORY.md
- 连接失败时给排查建议，不要只说"连不上"
- 扫描结果表太多（>50张）时只展示前10张，后面让用户说"展开全部"
- 每次使用前确认模块可导入
