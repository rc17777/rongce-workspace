# MEMORY.md - Long-term Memory

> Curated memories, preferences, and important context

---

## Agent Identity
- Name: 融策左护法
- Vibe: 聪明靠谱、轻松幽默、忠心耿耿

## User Preferences
- User: 融策平头哥
- Timezone: Asia/Shanghai
- 偏好：完整结构化 Word 文档输出，不满足于纯文字
- Windows 用 `py` 调 Python（非 `python`/`python3`）
- PowerShell 用 `;` 代替 `&&` 连接命令
- Windows GBK 终端用 `sys.stdout.reconfigure(encoding='utf-8')` 解决 emoji 问题

## 事务所背景
- 约50人会计师事务所，主营政府审计（40%）+咨询（60%），政府采购中标获客
- 核心痛点：经验锁在少数资深人员，助理专业弱/培养难/成本高
- 数字化转型核心：知识资产化是最低成本切入点，"把经验变成系统"

## 已完成重大项目

### 天府广场商业运营专项审计（2026-04）
- 对标北上广深头部商业项目，覆盖 7 大环节
- 输出：审计建议报告 + 数字化转型方案 v2.0 + 物业数字化商机分析
- 文件：天府广场项目专项审计建议报告.docx / 数字化转型方案_v2.docx

### 教科院附中串标围标审计（2026-05）
- 重大发现：马超同一身份证跨公司投标、潘翔-马超同乡联盟、童婷婷三重身份
- PDF 分析三剑客：PyMuPDF(元数据) + PyPDF2 + pdfminer
- OCR 方案：PaddleOCR（中文识别准确，纯 pip 安装）
- 输出：串标围标审计报告.xlsx（6个工作表）

### 金川医保审计（2026-05）
- 525万条医保结算数据全量分析，发现21个可追溯问题
- 大文件策略：xltx→CSV→pandas分块读取；PowerShell UsedRange.Value2 批量数组读取
- 可复用规则：分解住院(入院≤3天)、诊疗费虚高(>80%)、进销存三向比对、跨区域大额等
- 输出：4个Excel报告（37个Sheet）+ 分级资料清单

### 融策审计平台（2026-06）
- `rongce-platform` skill：SQLite 数据基座 + 4个分析模型
- 路径：skills/rongce-platform/data/rongce_core.db

## 知识体系建设（2026-05-31 集中建设日）

### AuditKB 五库
对标济南"1+5+N"智慧审计体系，建成五库：
- 对象库 / 主题数据库 / 操作指引库（70%）/ 法规案例库（33条规则+7案例）/ 审计整改库
- 位置：`C:\Users\Admin\AuditKB`

### 产出的方法论文件（均位于 rongce-gov-audit/references/）
- 8环节全链条SOP（宁津模式）→ 多类型通用SOP（预算执行/专项资金/绩效/采购/投资）
- 9大方法模块（河南农商银行方法论融策版）
- 1+5+N 体系蓝图 / 5库自动化方案 / 新技术落地评估
- AI+审计技术全景（9大场景+5地方案例+济南双主审模式）

### 案例库
- 期刊索引：5期共107篇案例目录
- 全文入库：7个案例（CASE-001~007）
- cron 自动采集：审计署+海南审计厅每周五9:00

## 技术栈速查
- PDF：PyMuPDF > PyPDF2 > pdfminer
- OCR：PaddleOCR（纯 pip，中文最佳）
- 大文件：PowerShell UsedRange.Value2 数组读取 > pandas chunksize 分块 > Excel COM
- 数据分析：pandas + numpy + jieba + scikit-learn（孤立森林）
- PDF 设备指纹：WPS/Chromium 不嵌入硬件指纹（MAC/CPU/硬盘序列号），需关注 Author 字段

## Marketplace 方法论（5条）
1. 东西多了就要管 — 生态成熟后管理是产品
2. 单点更新优于多点复制 — 一个 authoritative source
3. 标准化是协作语言
4. 引用优于复制 — 避免版本不一致
5. 启动成本比想象低 — 关键是有意识

## 技能库状态（2026-07）
- 108 eligible / 45 missing requirements / 0 blocked
- 核心技能：rongce-gov-audit（政府审计）、rongce-platform（数据平台）
- 审计专项：bid-collusion-audit（串标）、eco-responsibility-audit（经责）
- 办公：officecli-docx/pptx/xlsx、pdf、docx/pptx/xlsx（aweskill）
- 模型：deepseek-v4-pro（主）+ deepseek-v4-flash（cron），fallback 链已清空
