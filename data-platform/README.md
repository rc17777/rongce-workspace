# 融策审计数据中台 - 部署指南

## 环境要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (可选，用于缓存)
- MinIO (可选，用于文件存储)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `.env` 文件：

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=rongce
DB_PASSWORD=rongce123
DB_NAME=rongce_data_platform
```

### 3. 初始化数据库

```bash
python scripts/init_database.py
```

### 4. 初始化数据质量规则

```bash
python -c "from quality.data_quality_monitor import DataQualityMonitor; m = DataQualityMonitor(); m.init_default_rules()"
```

### 5. 启动API服务

```bash
python api/data_service_api.py
```

服务将在 http://localhost:5000 启动

## 目录结构

```
data-platform/
├── config/                 # 配置文件
│   └── data_standards.json # 数据标准
├── docs/                   # 文档
│   └── architecture.md     # 架构设计
├── scripts/                # 脚本工具
│   └── init_database.py    # 数据库初始化
├── etl/                    # ETL脚本
│   ├── financial_data_etl.py    # 财务数据ETL
│   ├── business_data_etl.py     # 业务数据ETL
│   └── external_data_collector.py # 外部数据采集
├── quality/                # 数据质量
│   └── data_quality_monitor.py  # 质量监控
├── api/                    # 数据服务API
│   └── data_service_api.py      # RESTful API
├── tests/                  # 测试用例
├── requirements.txt        # Python依赖
└── README.md              # 本文件
```

## 使用示例

### 导入财务数据

```python
from etl.financial_data_etl import FinancialDataETL

etl = FinancialDataETL()

# 导入会计科目
etl.import_subject_from_excel('data/subjects.xlsx')

# 导入凭证
etl.import_voucher_from_excel('data/vouchers.xlsx', project_id=1, client_id=1)

# 验证数据
results = etl.validate_financial_data()
```

### 执行业务数据ETL

```python
from etl.business_data_etl import BusinessDataETL

etl = BusinessDataETL()

# 导入客户
etl.import_clients('data/clients.xlsx')

# 导入项目
etl.import_projects_from_excel('data/projects.xlsx')

# 生成报告
report = etl.generate_project_report()
```

### 数据质量检查

```python
from quality.data_quality_monitor import DataQualityMonitor

monitor = DataQualityMonitor()

# 执行检查
results = monitor.run_quality_check()

# 生成报告
report = monitor.get_quality_report()
```

## API接口

### 项目相关

- `GET /api/projects` - 项目列表
- `GET /api/projects/<id>` - 项目详情

### 客户相关

- `GET /api/clients` - 客户列表
- `GET /api/clients/<id>/projects` - 客户项目

### 政策法规

- `GET /api/policies` - 政策列表
- `GET /api/policies/<id>` - 政策详情

### 财务数据

- `GET /api/financial/vouchers` - 凭证列表
- `GET /api/financial/subject-balance` - 科目余额

### 数据质量

- `POST /api/quality/check` - 执行检查
- `GET /api/quality/report` - 质量报告

### 统计分析

- `GET /api/statistics/project-overview` - 项目概览
- `GET /api/statistics/client-analysis` - 客户分析

## 数据标准

详见 `config/data_standards.json`，包含：

- 命名规范
- 数据类型定义
- 审计项目数据模型
- 客户主数据模型
- 政策法规数据模型
- 财务数据模型

## 数据质量规则

### 完整性
- 关键字段非空检查
- 必填字段完整性

### 准确性
- 数值范围检查
- 日期合理性检查
- 金额精度检查

### 一致性
- 外键关联检查
- 借贷平衡检查
- 状态一致性检查

### 时效性
- 数据更新频率检查
- 业务时效性检查

## 扩展开发

### 添加新的ETL脚本

1. 在 `etl/` 目录创建新的ETL类
2. 继承基础ETL类或独立实现
3. 实现数据清洗、转换、加载逻辑

### 添加新的质量规则

1. 在 `data_quality_monitor.py` 中添加规则定义
2. 或使用SQL直接插入 `quality_rules` 表

### 添加新的API接口

1. 在 `api/data_service_api.py` 中添加路由
2. 实现业务逻辑
3. 返回标准JSON格式

## 注意事项

1. 生产环境请修改默认密码
2. 定期备份数据库
3. 监控数据质量检查结果
4. 及时更新政策法规数据

## 联系方式

四川融策会计师事务所/工程咨询公司
