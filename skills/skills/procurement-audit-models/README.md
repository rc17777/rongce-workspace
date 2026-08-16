# 采购审计模型库 — 围标串標识别 + 关联关系挖掘

本目录包含4个可独立运行的审计分析脚本，用于政府采购审计中的围标串标疑点筛查。

## 脚本清单

| 文件名 | 模型 | 输入 | 输出 |
|:------|:-----|:-----|:-----|
| `01_same_ip_bidding.py` | 同一IP多家投标 | 投标记录表 (xlsx) | 疑点清单 (xlsx) |
| `02_price_pattern.py` | 报价规律性（等差数列） | 投标报价表 (xlsx) | 疑点清单 (xlsx) |
| `03_tfidf_similarity.py` | 技术标文本相似度 | 投标文件清单 (xlsx) + 文件目录 | 相似度矩阵 (xlsx) |
| `04_supplier_network.py` | 供应商关联网络 | 供应商股东表 (xlsx) | 关联集团列表 + 网络图 (png) |
| `05_price_deviation.py` | 采购价格偏离度 | 采购明细 (xlsx) + 可选监测数据 | Z值异常 + 价格偏离清单 (xlsx) |
| `06_supplier_clustering.py` | 供应商聚类分群 | 供应商交易特征表 | 聚类结果 + 风险标注 |
| `07_anomaly_purchase.py` | 采购异常交易检测 | 采购明细 (xlsx) | Isolation Forest异常交易 |

## 使用方法

```bash
# 安装依赖
pip install pandas openpyxl scikit-learn networkx matplotlib

# 运行模型（示例）
python 01_same_ip_bidding.py --input 投标记录.xlsx --output 疑点清单.xlsx
python 02_price_pattern.py --input 投标报价.xlsx --output 报价疑点.xlsx
python 03_tfidf_similarity.py --input 投标文件清单.xlsx --dir ./标书文件 --output 相似度结果.xlsx
python 04_supplier_network.py --input 供应商股东表.xlsx --output ./output/
```

## 数据格式要求

见各脚本文件头部的 Input Schema 说明。
