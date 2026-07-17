# 融策异常筛查规则引擎

> 基于《融策审计深度穿透方法论 V2.0》的5坐标系×6审计类型框架，实现E01-E24筛查规则的自动化脚本。

## 目录结构

```
scripts/anomaly_rules/
├── README.md                           # 本文件
├── run_all.py                          # 批量执行器
├── e01_door_access_vs_travel.py        # E01 门禁×出差时空矛盾
├── e05_bid_metadata_homology.py        # E05 投标元数据同源
├── e13_purchase_sales_inventory.py     # E13 进销存三向比对
├── e15_handler_payee_association.py    # E15 经办人×收款方关联
└── e23_year_end_spending.py            # E23 年末突击支出节奏
```

## 快速开始

### 单规则运行

```bash
# E01 门禁×出差时空矛盾
python scripts/anomaly_rules/e01_door_access_vs_travel.py 差旅报销.csv 门禁记录.csv

# E05 投标元数据同源
python scripts/anomaly_rules/e05_bid_metadata_homology.py 投标文件目录/

# E13 进销存三向比对
python scripts/anomaly_rules/e13_purchase_sales_inventory.py 进货.csv 销售.csv 库存.csv

# E15 经办人×收款方关联
python scripts/anomaly_rules/e15_handler_payee_association.py 报销台账.csv

# E15 带工商信息
python scripts/anomaly_rules/e15_handler_payee_association.py 报销台账.csv -b 工商信息.csv

# E23 年末突击支出
python scripts/anomaly_rules/e23_year_end_spending.py 月度支出.csv -y 2026
```

### 批量运行

```bash
# 列出所有规则
python scripts/anomaly_rules/run_all.py --list

# 运行全部规则（使用默认文件名）
python scripts/anomaly_rules/run_all.py --all --data-dir projects/某项目/data/

# 运行指定规则（自定义文件）
python scripts/anomaly_rules/run_all.py --e01 --e23 --travel 差旅.csv --access 门禁.csv --year 2025
```

## 输入格式

### E01 — 差旅报销表 (travel.csv)
```csv
姓名,出差日期,出差地点,报销金额,事由
张三,2026-06-15,成都,2500,项目现场审计
```

### E01 — 门禁记录 (access.csv)
```csv
姓名,日期,首次进门,末次出门
张三,2026-06-15,08:35,17:42
```

### E13 — 进货台账 (purchase.csv)
```csv
商品编码,商品名称,进货数量,进货日期,供应商
G001,XX设备,100,2026-01-15,XX供应商
```

### E13 — 销售台账 (sales.csv)
```csv
商品编码,商品名称,销售数量,销售日期,消费者,补贴金额
G001,XX设备,50,2026-02-20,消费者A,50000
```

### E13 — 库存台账 (inventory.csv)
```csv
商品编码,商品名称,期初库存,期末库存,盘点日期
G001,XX设备,20,70,2026-12-31
```

### E15 — 报销台账 (expense.csv)
```csv
经办人,收款方名称,金额,日期,事由
张三,XX供应商,15000,2026-03-10,会议费
```

### E15 — 工商信息（可选）(biz_info.csv)
```csv
企业名称,法人,股东,注册地址
XX供应商,李四,王五,成都市XX区
```

### E23 — 月度支出表 (monthly_spending.csv)

**格式A（宽表）**：
```csv
部门,年份,1月,2月,3月,4月,5月,6月,7月,8月,9月,10月,11月,12月
办公室,2026,50000,48000,52000,...
```

**格式B（长表）**：
```csv
日期,金额,部门
2026-01-15,50000,办公室
```

## 输出

每规则输出对应的 `anomalies_eXX.csv`，列包含异常说明、风险等级、建议动作。批量运行还生成 `anomaly_summary.json` 和 `anomaly_summary.md`。

## 已实现规则（第一梯队：立即可做）

| 编号 | 规则 | 坐标系 | 难度 |
|:--|:--|:--|:--:|
| E01 | 门禁×出差时空矛盾 | 时空 | ⭐ |
| E05 | 投标元数据同源 | 时空 | ⭐ |
| E13 | 进销存三向比对 | 物理 | ⭐ |
| E15 | 经办人×收款方关联 | 社会关系 | ⭐ |
| E23 | 年末突击支出节奏 | 时间序列 | ⭐ |

## 待实现（第二、三梯队）

| 编号 | 规则 | 优先级 |
|:--|:--|:--|
| E02 | 街景历史影像×验收照片 | 短期 |
| E03 | 受益对象GPS聚类 | 短期 |
| E09 | 纸张反推印刷量 | 短期 |
| E16 | 申报方×承接方股权穿透 | 短期 |
| E17 | 领导干部亲属工商图谱 | 短期 |
| E20 | 报价数学规律异常 | 短期 |
| ... | 其余E规则 | 中长期 |
