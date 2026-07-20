# OCR预处理管道设计 v1.0

> 2026-07-17 | 融策右护卫设计
> 核心问题：客户资料大量为扫描件/照片/图片，不先OCR，Agent全是盲人摸象

---

## 架构：OCR层嵌入Phase ①

```
Phase ① 资料导入与智能分类（重构后）

①a  文件入库     raw_data/ 接收所有文件
     │
①b  OCR预处理    ★新增★ 检测哪些文件需要OCR → 执行OCR → 结构化提取
     │
①c  智能分类     基于OCR文本+文件名+列名 的深度分类
     │
①d  归档同步     复制到Obsidian + 增量更新RAG
```

---

## ①b OCR预处理 — 分文档类型的差异化处理

### 文档类型自动识别

| 输入 | 检测方法 | 输出类型 |
|:--|:--|:--|
| PDF无文本层 | `pdfplumber` 检测文本量 < 50字 | → 扫描件PDF，需完整OCR |
| PDF有文本层 | `pdfplumber` 检测文本量 ≥ 50字 | → 直接提取文本，仅OCR图片 |
| .jpg/.png/.bmp | 文件扩展名 | → 图片OCR |
| .ofd | 文件扩展名 | → OFD解析（国产版式） |
| .docx/.xlsx | — | → 跳过OCR，直接读取 |
| .rar/.zip | 先解压 | → 递归处理内部文件 |

### 五类文档的OCR + 结构化提取

#### Type 1: 发票（增值税发票/普通发票/财政票据）

```
OCR → 结构化提取
├─ 发票代码/号码
├─ 开票日期
├─ 销售方名称/税号
├─ 购买方名称/税号
├─ 金额（不含税/税额/价税合计）
├─ 货物/服务名称
├─ 备注
└─ 输出: invoices.csv（可直接导入Excel分析）
```

**用途**：费用真实性验证、大额发票查重、关联方交易识别

#### Type 2: 合同/协议

```
OCR → 全文 → 关键信息提取
├─ 合同编号
├─ 甲方/乙方
├─ 签订日期
├─ 合同金额
├─ 付款方式（一次性/分期/进度款）
├─ 履约期限
├─ 违约责任条款
├─ 争议解决方式
└─ 输出: contracts.csv + 全文.md
```

**用途**：合同台账自动建表、条款合规审查、履约追踪

#### Type 3: 招投标文件

```
OCR → 全文 → 结构化提取
├─ 项目名称/编号
├─ 招标方式（公开/邀请/竞争性谈判/单一来源）
├─ 各投标人报价
├─ 技术/商务得分
├─ 中标候选人
├─ 招标文件与投标文件关键条款对比
└─ 输出: bids.csv + 全文.md
```

**用途**：围标串标检测（L1-L19）、评标公正性审查

#### Type 4: 银行单据/凭证

```
OCR → 结构化提取
├─ 银行名称/账号
├─ 交易日期
├─ 交易金额
├─ 对方户名/账号
├─ 摘要/用途
├─ 凭证号码
└─ 输出: bank_transactions.csv
```

**用途**：资金流水对账、大额异常交易检测、资金流向追踪

#### Type 5: 通用文档（报告/纪要/制度/其他）

```
OCR → 全文.md（保留格式优先）
└─ 不做结构化提取，保留全文供后续Agent分析
```

---

## 技术选型

| 环节 | 工具 | 理由 |
|:--|:--|:--|
| 通用OCR | PaddleOCR 2.7+ | 中文识别率最高，已有base环境 |
| 发票专用OCR | PaddleOCR + 模板匹配 | 发票格式固定，模板匹配比通用OCR准 |
| PDF文本检测 | pdfplumber | 判断是否有文字层，避免重复OCR |
| OFD解析 | ofdparser (pip) | 国产版式文件解析 |
| 合同关键信息提取 | qwen3.7-plus (OCR text → LLM提取) | 合同条款非结构化，需LLM理解 |
| 发票结构化 | qwen-vl-max (图片直接识别) | 发票图片直接交VL模型一次提取 |
| 批量调度 | Python multiprocessing | 充分利用多核 |

---

## 处理流程

```
文件入库
    │
    ├─ .docx/.xlsx/.csv ──────────→ 跳过OCR ──→ 直接给分类Agent
    ├─ .rar/.zip ─────────→ 解压 ──→ 递归处理
    │
    ├─ PDF ──→ pdfplumber检测文本层
    │           ├─ 有文本层 ──→ 直接提取文本
    │           └─ 无文本层 ──→ PaddleOCR整页识别
    │
    ├─ .jpg/.png/.bmp ──→ 检测内容类型
    │           ├─ 发票特征 ──→ qwen-vl-max 发票识别 → invoices.csv
    │           ├─ 合同特征 ──→ PaddleOCR → 全文 → qwen3.7提取字段 → contracts.csv
    │           ├─ 银行单据 ──→ PaddleOCR → bank_transactions.csv
    │           └─ 其他图片 ──→ PaddleOCR → 全文.md
    │
    └─ .ofd ──→ ofdparser ──→ 文本提取
```

---

## 输出物

执行OCR后，raw_data/ 下自动生成：

```
raw_data/
├── 原始文件（保持不变）
├── .ocr_cache/           # OCR结果缓存
│   ├── 发票/
│   │   ├── invoices.csv          # 所有发票的结构化数据
│   │   └── *.md                  # 每张发票全文
│   ├── 合同/
│   │   ├── contracts.csv         # 合同台账
│   │   └── *.md                  # 每份合同全文
│   ├── 招投标/
│   │   ├── bids.csv
│   │   └── *.md
│   ├── 银行/
│   │   ├── bank_transactions.csv
│   │   └── *.md
│   ├── 通用/
│   │   └── *.md                  # 通用文档全文
│   └── ocr_report.json           # OCR处理报告
│
├── .meta.json            # 分类结果（基于OCR文本深度分类）
└── .missing.json         # 对照DATA_SPEC的资料缺口清单
```

---

## 与后续Agent的对接

OCR后的结构化数据直接喂给Agent：

```
invoices.csv ──→ data_scout (费用分析、发票查重)
contracts.csv ──→ contract_hound (合同条款审查)
bids.csv ──→ bid_hunter (围标串标检测)
bank_transactions.csv ──→ data_scout (资金流水分析)
*.md 全文 ──→ law_inspector (法规匹配)
            ──→ report_writer (引用原文)
```

---

## 成本估算

| 场景 | OCR量 | 模型调用 | 预估Token |
|:--|:--|:--|:--|
| 小型项目（50页） | 全部PaddleOCR本地 | 发票/合同字段提取用LLM | ~5K tokens |
| 中型项目（200页） | PaddleOCR本地 | 同上 | ~15K tokens |
| 大型项目（500页+） | PaddleOCR本地 + 分批 | 同上 | ~30K tokens |

> PaddleOCR本地全免费，LLM仅用于结构化提取，成本可控。
