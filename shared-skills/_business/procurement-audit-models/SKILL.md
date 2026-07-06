---
name: "procurement-audit-models"
description: >
  采购审计模型库 — 围标串标识别+供应商关联挖掘。基于群众语言堂公众号《政府采购审计大数据技术超详细操作》及审计一线实战提炼。Triggers: '围标串标', '采购审计', '供应商关联', '投标IP相同', '报价规律', '标书比对', '政府采购'.
business_line: "招投标审计"
methods: "关联分析; 文本相似度; 图像哈希; 报价规律; FP-Growth"
difficulty: "高级"
keywords: "招投标, 围标串标, 供应商关联, TF-IDF, 同IP, 标书比对"
status: "stable"
---

# Procurement Audit Models — 采购审计模型库

## 概述

7个可独立运行的Python脚本，覆盖政府采购审计中围标串标识别+供应商风险分群+异常交易检测。依赖轻量，一行命令输出疑点清单 + 可视化网络图。

## 模型清单

| 模型 | 脚本 | 识别目标 | 输出 |
|:----|:-----|:---------|:-----|
| **趋势** | `00_window_func_trend.py` | 中标累计趋势+异常放量检测 | 放量预警 |
| **①-v2 STDDEV** | `01_v2_stddev_outlier.py` | Z-Score标准差异常报价+分组分析 | 异常报价清单 |
| ① 同一IP多单位投标 | `01_same_ip_bidding.py` | 多家投标单位使用同一IP | 疑点.xlsx |
| ② 报价规律性识别 | `02_price_pattern.py` | 报价呈等差数列/阶梯分布 | 疑点.xlsx |
| ③ 技术标雷同检测 | `03_tfidf_similarity.py` | 标书文本TF-IDF相似度≥90% | 相似度矩阵.xlsx |
| **③-v2 名称模糊匹配** | `03_v2_fuzzy_name_match.py` | 投标人名称相似度+聚类分组 | 关联企业簇 |
| ④ 供应商关联网络 | `04_supplier_network.py` | 同一股东控制多家供应商围标 | 关联集团.xlsx + 网络图.png |
| **④-v2 图分析** | `04_v2_graph_analysis.py` | **多层股权穿透+中心性+派系+社区发现** | **关键节点+围标集团** |
| **⑪-v2 FP-growth** | `11_v2_fpgrowth.py` | **频繁项集+关联规则→职业陪标团伙** | **陪标团伙清单** |
| ⑤ 采购价格偏离度 | `05_price_deviation.py` | Z值异常+政府价格监测比对 | 价格偏离疑点.xlsx |
| ⑥ 供应商聚类分群 | `06_supplier_clustering.py` | 按交易特征自动分群+风险标注 | 聚类结果.xlsx |
| ⑦ 采购异常交易检测 | `07_anomaly_purchase.py` | Isolation Forest异常交易 | 异常交易.xlsx |
| **⑧ 图片哈希比对** | `08_image_hash.py` | 跨投标人嵌入图片MD5/SHA256比对 | 重复图片清单 |
| **⑧-v2 感知哈希** | `08_image_hash_v2.py` | DCT+Hamming → 检测同图不同扫描版本 | 跨投标人视觉相似图片 |
| **⑨ PDF元数据交叉** | `09_metadata_cross.py` | Author/Creator/Producer/字体比对 | 同源检测报告 |
| **⑩ 文档结构比对** | `10_doc_structure.py` | 字体使用/页面布局/样式一致性 | 结构相似度报告 |
| **⑪ 跨项目伴随投标** | `11_cross_project_bidding.py` | Jaccard共现系数+中标集中度 | 跨项目围标疑点 |
| **⑫ 节资率+支持度/置信度** | `12_savings_rate.py` | 节资率箱线图+共现网络分析 | 竞争不足疑点表 (v3.2) |
| **⑬ 实体异常检测(L15-L19)** | `13_entity_anomalies.py` | 陪标专业户/保证金/经办人/硬件/专家违规 | 五维实体异常报告 (v3.3) |
| **通用·应有未有** | `should_have_but_dont.py` | LEFT JOIN+IS NULL 三场景 | 漏保/错保/盘亏清单 |
| **通用·三维验证** | `three_way_cross_validation.py` | 资格×行为×排除八态分类 | 交叉验证矩阵 |
| **通用·并行处理** | `parallel_data_split.py` | 多线程智能拆分+并行分析 | 分组批量结果 |
| **通用·隐性网络** | `implicit_network.py` | 隐性供应商网络+围标团伙发现 | 社区+团伙报告 |

> ⚠️ **NODE.JS版本为参考框架**。实战分析推荐Python脚本（PyMuPDF+openpyxl）直接操作PDF。
> 
> ⚠️ **2026-05-27教训**：L5(元数据)是围标检测中最高证据价值层之一。**不论是否仅有PDF，L4/L5/L6必须做**——PyMuPDF完全可提取嵌入图片、元数据、字体。本次急救实训室项目的串标铁证即来自L5 PDF Author字段交叉比对。

## 技术底座文档

> ⚠️ **必读**：完整的15层+检测体系、项目分类策略、标准作业程序(SOP)、决策树、经验教训 → 详见 [TECHNICAL-FOUNDATION.md](./TECHNICAL-FOUNDATION.md)
>
> 基于四个实战项目（校服采购/急救实训室/艺术团采购/宿舍监理）的系统化方法论沉淀，v3.3版本。

## 快速使用

```bash
cd scripts/

# Node.js版本（推荐，本机可用，无需额外依赖）
node 01_same_ip_bidding.js --input 投标记录.xlsx
node 02_price_pattern.js --input 投标报价.xlsx
node 03_tfidf_similarity.js --input 投标文件清单.xlsx --dir ./标书文件
node 04_supplier_network.js --input 供应商股东表.xlsx
node 05_price_deviation.js --input 采购明细.xlsx
node 06_supplier_clustering.js --input 供应商表.xlsx --clusters 4
node 07_anomaly_purchase.js --input 采购明细.xlsx

# Python版本（需安装依赖）
pip install pandas openpyxl scikit-learn networkx matplotlib
python 01_same_ip_bidding.py --i 投标记录.xlsx --o 疑点清单.xlsx
```

## 输入数据格式

### 模型1 — `投标记录.xlsx`
| 投标IP | 投标单位 | 项目名称 | 投标时间 |
|--------|---------|---------|---------|
| 192.168.1.1 | 甲公司 | XX项目 | 2025-03-01 |
| 192.168.1.1 | 乙公司 | XX项目 | 2025-03-01 |

### 模型2 — `投标报价.xlsx`
| 项目名称 | 投标单位 | 投标报价 |
|---------|---------|---------|
| XX项目 | 甲公司 | 1000000 |
| XX项目 | 乙公司 | 1050000 |
| XX项目 | 丙公司 | 1100000 |

### 模型3 — `投标文件清单.xlsx`
| 投标单位 | 文件路径 |
|---------|---------|
| 甲公司 | C:\标书\甲公司_技术标.docx |
| 乙公司 | C:\标书\乙公司_技术标.docx |

### 模型4 — `供应商股东表.xlsx`
| 供应商 | 股东姓名 | 持股比例 |
|--------|---------|---------|
| 甲公司 | 张三 | 60% |
| 乙公司 | 张三 | 40% |
| 丙公司 | 李四 | 100% |

## 使用场景

1. **政府采购审计**: 落地一个项目，跑4个模型，快速输出《采购疑点清单》
2. **招投标监督**: 评标前跑模型1+2，辅助筛查风险投标
3. **专项审计调查**: 对历年采购数据批量跑模型4，发现长期隐藏的关联集团

## 参考

基于群众语言堂公众号《审计人必看：政府采购审计大数据技术超详细操作》及《七大核心方法玩转审计数据分析》提炼，融策工程咨询公司实战适用。
