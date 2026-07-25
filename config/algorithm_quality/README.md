# 融策审计算法质量保障体系 v1.0

> 基于六模型联合评审的17条改进清单，2026-07-22 实施

---

## 架构概览

```
                    ┌─────────────────────────────┐
                    │    第零道门：数据安全守卫      │
                    │  分级→脱敏→本地留存→安全审计   │
                    └──────────────┬──────────────┘
                                   │ 通过
                    ┌──────────────▼──────────────┐
                    │       四层防御体系            │
                    │                              │
                    │  第一层：金标准测试集（三轨制）   │
                    │  第二层：回归测试（基准保持）      │
                    │  第三层：双盲盲测（统计功效）      │
                    │  第四层：生产监控（MLSys）         │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │     Feedback Loop 闭环        │
                    │  人工复核→回流训练→更新基准集   │
                    └─────────────────────────────┘
```

## 17条改进清单 — 实施状态

| # | 改进项 | 优先级 | 状态 | 文件 |
|:--|:--|:--|:--:|:--|
| 1 | 拆开"统计异常"和"审计结论"两层 | P0 | 📋 设计 | README: 分层架构 |
| 2 | 多重比较FDR校正 | P0 | ✅ 已实现 | `scripts/algorithm_quality/fdr_correction.py` |
| 3 | 金标准测试集三轨制 | P0 | 📋 设计 | 合成注入+回溯+对抗验证 |
| 4 | 指标重构：AUC-PR/Precision@K/Expected Cost | P0 | ✅ 已实现 | `scripts/algorithm_quality/evaluation_metrics.py` |
| 5 | 第零道门：数据分级+脱敏前置 | P0 | ✅ 已实现 | `scripts/algorithm_quality/data_guard.py` |
| 6 | 算法可解释性+决策留痕 | P0 | 📋 规范 | `config/algorithm_quality/explainable_output_spec.md` |
| 7 | 模型风险分级（A/B/C三级） | P1 | ✅ 已配置 | `config/algorithm_quality/risk_tiers.json` |
| 8 | Feedback Loop闭环 | P1 | 📋 设计 | 人工复核→回流→更新基准集 |
| 9 | 国产LLM幻觉专项探针 | P1 | ✅ 已实现 | `scripts/algorithm_quality/hallucination_probes.py` |
| 10 | 模型版本化管理 | P1 | ✅ 已配置 | `config/algorithm_quality/version_registry.json` |
| 11 | 紧急通道+事后补跑机制 | P1 | 📋 设计 | 流程设计（见下方） |
| 12 | 数据治理层 | P1 | 📋 设计 | 血缘/完整性/对账 |
| 13 | 盲测统计功效计算 | P2 | ⏳ 待实施 | 交叉验证+Bootstrapping |
| 14 | MLSys生产监控 | P2 | ⏳ 待实施 | 数据漂移MMD+决策翻转率 |
| 15 | 等保2.0+信创适配 | P2 | ⏳ 待实施 | 昇腾910B+国密SM4 |
| 16 | 外部第三方年审 | P2 | ⏳ 待实施 | 年度高校专家评审 |
| 17 | 三年标准输出路线 | P2 | 📋 设计 | 地方标准→行业标准 |

> ✅ 已实现 = 代码已写 | 📋 设计 = 方案文档 | ⏳ 待实施 = 需更多资源

---

## 分层架构设计（P0-1）

### 阶段A：统计异常检测（EDA层）
```
输入：财务数据、合同、投标文件
输出：异常分数（anomaly scores），不做二分判断
评估指标：统计功效、效应量、异常覆盖率、FDR校正后显著性
```
**注意**：Benford/Z-score/Mann-Kendall/CUSUM/Apriori/PageRank 都属于此层。
它们的输出是"统计上不寻常"，不是"审计上违规"。必须走FDR校正。

### 阶段B：审计风险评估（ML分类层）
```
输入：阶段A的异常分数 + 领域特征
输出：风险概率 + 风险等级（高/中/低）
评估指标：AUC-PR、Precision@K、Recall@Budget、Expected Cost
```

### 阶段C：人工复核（Human-in-the-Loop）
```
输入：阶段B的高风险项 + 可解释性报告
输出：审计判断（确认违规/排除/需进一步取证）
反馈：复核结论回流 → 更新基准集、模型迭代
```

---

## 风险分级（P1-7）

| 等级 | 定义 | 算法示例 | 管控要求 |
|:--|:--|:--|:--|
| **A级**（直接影响审计结论） | 串标检测、资金流向异常、签字/盖章真伪 | L3文本雷同、L4图片哈希、L8工商关联 | 必须过Gate1+Gate2+Gate3，审计师逐条核实，可解释性≥4.0 |
| **B级**（辅助审计判断） | Benford分析、Z-score异常、文本聚类、合同比较 | Benford、DBSCAN、Sentence-BERT | 过Gate1+Gate3，项目组抽样核实，可解释性≥3.0 |
| **C级**（提供参考信息） | 趋势分析、关键词提取、数据分类 | Mann-Kendall、NER、数据分类 | 过Gate1即可，不强制核实 |

---

## 紧急通道机制（P1-11）

```
正常流程：Gate1(测试集) → Gate2(盲测) → Gate3(试跑) → 上线
紧急流程：Gate1(测试集) → 项目经理签字 → 上线 ⚡
         └─ 项目结束后7天内 → 补跑Gate2+Gate3 → 不合格 → 回滚
```

**限制**：
- 紧急通道使用次数：≤2次/季度
- 仅限A级以下（非直接影响结论）算法
- 使用记录单独存档，质控部门每季度复盘

---

## 使用指南

### 日常使用
```bash
# 跑统计算法前必跑FDR校正
python scripts/algorithm_quality/fdr_correction.py

# API调用前必跑数据守卫
python scripts/algorithm_quality/data_guard.py

# LLM输出后必跑幻觉探针
python scripts/algorithm_quality/hallucination_probes.py

# 评估算法性能
python scripts/algorithm_quality/evaluation_metrics.py
```

### 测试集构建规范
```
测试集目录结构：
knowledge/algorithm-test-sets/
├── synthetic/     # 合成数据注入（已知问题人工注入）
├── closed_cases/  # 已结案项目回溯
├── adversarial/   # 对抗验证用例
└── probes/        # 幻觉探针用例
    ├── regulation_fakes.txt      # 虚构法规文号
    ├── amount_drift.txt          # 金额精度漂移
    └── long_context_cross.txt    # 长上下文串台
```

### 标注规范（最低要求）
- **双人标注**：2名审计师独立标注
- **Cohen's Kappa ≥ 0.75**：不合格则第三名专家仲裁
- **最小样本量**：统计≥500案例，NLP≥1000文本段，多模型≥200场景
- **多样性要求**：覆盖≥5行业、≥3审计类型、≥2异常模式

---

## 下一步行动

### 本周（7月22-27日）
1. [ ] 跑通 FDR校正+评估指标+数据守卫 三个模块的单元测试
2. [ ] 从"红光街道绩效评价"项目回溯10条测试案例加入测试集
3. [ ] 用幻觉探针测一次 DeepSeek/Kimi 当前版本的输出

### 下周（7月28日-8月3日）
4. [ ] 完成可解释性输出规范文档
5. [ ] 建 Feedback Loop 追踪表（Excel→后续自动化）
6. [ ] 为5个核心算法建最小测试集（50-100条/算法）

### 8月
7. [ ] 跑通一次完整的 Gate1→Gate2→Gate3 流程（选1个项目）
8. [ ] 给项目经理培训一次"算法质量分级"概念
9. [ ] 试点第零道门（选2个API调用场景）

---

*最后更新: 2026-07-22 | 六模型评审会议*
