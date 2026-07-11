# 融策审计标准与工具库

> audit-blackboard/standards/  
> 存放审计数据标准、脱敏规范、检测模型等通用组件

---

## 已完成的组件

### 1. 数据脱敏规范

| 文件 | 说明 |
|:---|:---|
| `数据脱敏规范v1.0.md` | 四级分级标准、脱敏字段清单、操作原则、违规处理 |
| `脱敏操作手册.md` | 3分钟快速上手、场景要点、质量检查清单、常见问题 |
| `scripts/desensitize_excel.py` | 脱敏脚本（Excel/CSV/JSON），自动识别10类字段 |
| `scripts/generate_test_data.py` | 测试数据生成器 |

**脱敏能力**：
- 姓名、身份证号、手机号、银行卡号、地址、金额、企业名称、信用代码、邮箱
- 金额区间化（5万以下/5-10万/10-50万/.../1亿以上）
- 自动列名识别 + 自定义规则
- Excel多Sheet支持

**用法**：
```bash
python scripts/desensitize_excel.py \
  -i "原始数据.xlsx" \
  -o "脱敏数据_脱敏.xlsx"
```

---

### 2. 评标专家偏离度检测模型

| 文件 | 说明 |
|:---|:---|
| `scripts/expert_bias_detection.py` | 偏离度检测模型，6种检测方法 |

**检测方法**：

| 方法 | 原理 | 检出异常类型 |
|:---|:---|:---|
| **Kendall W协调系数** | 专家评分一致性检验 | 整体一致性差（W<0.5） |
| **Z-score偏离** | (评分-均值)/标准差 | 单个专家对某投标人显著偏离 |
| **IQR异常值** | 四分位距法 | 超出正常范围的极端评分 |
| **变异系数CV** | 标准差/均值 | 专家评分波动异常（忽高忽低） |
| **聚类孤立** | 层次聚类 | 评分模式与大多数专家不同的孤立专家 |
| **极端打分模式** | 规则匹配 | 全打满分/全打低分/压线集中/完全一致 |

**输出**：
- Excel报告（4个Sheet：检测摘要/异常记录/评分矩阵/专家统计）
- JSON格式（兼容audit-blackboard finding_schema）

**用法**：
```bash
python scripts/expert_bias_detection.py \
  -i "评标打分表.xlsx" \
  -o "偏离度分析报告.xlsx" \
  --score-col "总分" \
  --threshold-z 2.0
```

---

## 与audit-blackboard的集成

### 在orchestrate.py中调用

```python
# 在prepare阶段加入脱敏检查
from standards.scripts.desensitize_excel import desensitize_excel

def prepare_agent_tasks(...):
    # ... 现有代码 ...
    
    # 脱敏检查
    raw_data = proj_dir / 'raw_data'
    for f in raw_data.glob('*.xlsx'):
        if '_脱敏' not in f.name:
            desensitize_excel(f, f.parent / f'{f.stem}_脱敏{f.suffix}')
            
    # ... 继续生成Agent任务 ...
```

### 作为新Agent加入

在`agent_specs/`中可新增：
- `expert_bias_detector.json`：评标偏离度检测Agent
- `data_desensitizer.json`：数据脱敏Agent

---

## 待完成（需硬件/业务配合）

| 组件 | 状态 | 依赖 |
|:---|:---|:---|
| Ollama+Qwen本地部署 | ⏸️ 暂停 | 新电脑到位 |
| Dify工作流平台 | ⏸️ 暂停 | 新电脑到位 |
| 944篇案例RAG化 | 🔄 网页端进行中 | 向量数据库 |
| 项目风险图谱（三流合一） | ⏸️ 暂停 | 业务专家配合设计勾稽关系 |

---

## 测试验证

评标偏离度模型已用模拟数据验证，检出：
- ✅ Kendall W = 0.25（严重不一致）
- ✅ Z-score偏离 2条（专家C、F）
- ✅ IQR异常值 1条（专家F）
- ✅ 极端打分模式：专家D全部一致（90分）
- ✅ 报告已导出Excel+JSON

---

*最后更新：2026-06-24*
