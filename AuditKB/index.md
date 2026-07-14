# 审计知识库 - 目录索引

> 最后更新:2026-06-01
> 自动生成,每次 Ingest 后更新

## 案例索引

| 案例编号 | 项目名称 | 审计类型 | 行业 | 关键发现 |
|---------|---------|---------|------|---------|
| CASE-MED-ECA | 医疗机构经责审计全过程操作指南 | 经济责任审计 | 医疗 | 20环节全流程操作规范+12条M规则 |
| CASE-DATA-VOUCHER | 消费券审计三步法 | 专项资金/数据分析 | 财政/消费券 | 多维分析→Apriori→K-Means 挖出6亿消费券团伙作案 |
| 期刊指南 | 审计案例杂志2026年第1册 | 综合 | 多领域 | 21个案例目录索引,标注6篇优先深挖 |
| CASE-NONSTRUCT-226 | 非结构化数据处理批处理实战 | 招投标审计/数据技术 | 通用 | 226项目1.27TB数据→1天全覆盖筛查，发现围标串标 |
| CASE-BID-APRIORI | 招投标围标SQL实现Apriori | 招投标审计/围标串标 | 通用 | 5维检测+SQL实现Apriori抱团分析+评标专家异常 |
| CASE-LAW-BID | 串通投标法律责任认定与取证 | 法律框架/取证标准 | 通用 | 四要件法律框架+3种取证方式+举证责任倒置 |
| CASE-SPECFUND-4STEPS | 专项资金审计4步法 | 专项资金审计 | 通用 | 4核心目标+4步流程+四单匹配法 |
| CASE-FARMLAND-GIS | 永久基本农田GIS空间叠加审计 | 自然资源资产审计 | 农业/国土 | 5类GIS叠加分析+两方向五类型问题体系 |
| CASE-BID-SHIELD | 合规企业投标自保8条指南 | 招投标合规/企业自保 | 通用 | 5种数字指纹+8条自保指南（审计反向用=8个检测点） |
| CASE-BID-2026 | 串标识别2026升级版 | 招投标审计/串标识别 | 通用 | 4传统方法+3新利器（社保/资质/信用）+3趋势（跨省/AI/行为分析） |
| CASE-ECA-14Q | 行政事业单位经责典型问题及防范措施 | 经济责任审计 | 行政事业通用 | 6大方面14类典型问题+防范措施（无锡市审计局） |
| CASE-005 | 国企活牛贸易风险 | 国企审计/贸易审计 | 国企 | 短缺468头牛,无人机盘点+三重一大缺失 |
| CASE-006 | 国储林资金挪用 | 资源环境审计 | 林业 | 5.15亿贷款被挪用,GIS图斑比对 |
| CASE-007 | 湿地占补平衡审计 | 资源环境审计 | 林业/湿地 | GIS数据叠加分析查占补违规 |
| CASE-PROJ-75 | 工程项目审计全过程8方面75项必查重点 | 工程项目审计 | 工程/基建 | 8阶段75项必查违规点（立项→运维+财务） |

## 案例杂志索引

- [审计案例杂志2026年第1册](wiki/cases/journal_index_2026_01.md) — 21个案例全目录+优先级标注
- [审计案例杂志2026年第4册](wiki/cases/journal_index_2026_04.md) — 22个案例全目录+8篇优先深挖
- [审计案例杂志2026年第2册](wiki/cases/journal_index_2026_02.md) — 19个案例全目录+5篇优先深挖
- [审计案例杂志2025年第12册](wiki/cases/journal_index_2025_12.md) — 22个案例+5篇优先深挖
- [审计案例杂志2025年第11册](wiki/cases/journal_index_2025_11.md) — 24个案例+4篇优先深挖（资源环境审计专题）

## 规则索引

| 规则编号 | 规则名称 | 审计领域 | 检测方法 | 参考案例 |
|---------|---------|---------|---------|---------|
| RULE-001 | 同一身份证号跨投标方 | 采购围标 | PDF元数据+文本匹配 | CASE-001 |
| RULE-002 | 同一PDF Author跨公司 | 采购围标 | PDF元数据 | CASE-001 |
| RULE-003 | 同乡联盟(身份证前6位) | 采购围标 | 身份证解析+聚类 | CASE-001 |
| RULE-004 | 报价阶梯式差异 | 采购围标 | 统计偏差 | CASE-001 |
| RULE-005 | 技术方案相似度异常 | 采购围标 | 文本相似度比对 | CASE-001 |
| RULE-006 | 投标日期协同 | 采购围标 | 时间戳聚类 | CASE-001 |
| RULE-007 | 关联方投标(同一法人/股东) | 采购围标 | 工商信息比对 | CASE-001 |
| RULE-008 | 历史中标率异常 | 采购围标 | 历史统计分析 | CASE-001 |
| RULE-101 | 分解住院检测 | 医保审计 | 入院-出院间隔≤3天 | CASE-002 |
| RULE-102 | 诊疗费虚高检测 | 医保审计 | 诊疗费/总费>80% | CASE-002 |
| RULE-103 | 进销存三向比对 | 医保/物资 | 销量vs入库量vsPOS | CASE-002 |
| RULE-104 | 跨区域大额异常 | 医保/资金 | 参保地≠消费地+大额 | CASE-002 |
| RULE-105 | 收报差额检测 | 医保/资金 | 收费vs结算差>30% | CASE-002 |
| RULE-106 | 操作权限异常 | 内控审计 | 单人多角色覆盖>80% | CASE-002 |
| RULE-107 | 价格波动异常 | 采购审计 | 最低价/最高价>200% | CASE-002 |
| RULE-108 | 非目录产品识别 | 合规审计 | 批准文号不含"国药准字" | CASE-002 |
| RULE-201 | 中标价vs控制价偏差 | 投资审计 | 偏差<85%或>100%标红 | - |
| RULE-202 | 结算价vs合同价超比例 | 投资审计 | 超10%标红 | - |
| RULE-203 | 同甲方同乙方频繁合作 | 投资审计 | 3年≥3次 → 关联嫌疑 | - |
| RULE-204 | 变更签证集中于竣工前 | 投资审计 | 距竣工<总工期10% | - |
| RULE-205 | 进度款超比例支付 | 投资审计 | 累计/合同>完工比×1.1 | - |
| RULE-206 | 材料采购价vs信息价偏离 | 投资审计 | 偏离>20%标红 | - |
| RULE-207 | 招标控制价编制依据不足 | 投资审计 | 缺项>20%标红 | - |
| RULE-208 | 软件项目功能点虚增 | 投资审计 | 申报/基准>1.3标红 | — |
| RULE-301 | 预算执行偏离度异常 | 经济责任 | 决算/预算>120%或<60%标红 | — |
| RULE-302 | 三公经费超标 | 经济责任 | 超预算批复比例标红 | — |
| RULE-303 | 国有资产处置程序缺失 | 经济责任 | 无审批/无评估/无公开交易 | — |
| RULE-304 | 重大决策未集体研究 | 经济责任 | 无会议纪要或纪要缺失 | — |
| RULE-305 | 往来款长期挂账 | 经济责任 | 挂账>3年且无清理动作 | — |
| RULE-306 | 专项资金挪用 | 经济责任 | 资金用途偏离批复范围 | — |
| RULE-401 | 个体工商户异常开票检测 | 发票审计 | 存续短+开票大+经办人集中+虚假地址 | CASE-004 |
| RULE-501 | 国企贸易决策缺失 | 国企审计 | 无可研+无会议+口头决策 | CASE-005 |
| RULE-502 | 供应商异常集中 | 国企审计 | 单一供应商占比>80% | CASE-005 |
| RULE-503 | 实物盘点差异检测 | 资产审计 | 账面vs实盘差异>10% | CASE-005 |
| RULE-M001 | 集采约定采购量未完成检测 | 医改政策执行 | 实际/合同完成率<80% | CASE-MED-ECA |
| RULE-M002 | 绩效工资超总量发放检测 | 薪酬福利管理 | 账面发放 vs 人社批复总量 | CASE-MED-ECA |
| RULE-M003 | 三重一大决策程序倒置检测 | 决策程序合规 | 合同/实施时间 vs 会议决策时间 | CASE-MED-ECA |
| RULE-M004 | 科研经费套取检测 | 科研经费管理 | 供应商关联分析+集中报销异常 | CASE-MED-ECA |
| RULE-M005 | 人员吃空饷检测 | 人员经费管理 | 花名册+考勤+工资三方交叉比对 | CASE-MED-ECA |
| RULE-M006 | DRG/DIP高套分组检测 | 医保基金管理 | 病历诊断/操作 vs 医保分组核对 | CASE-MED-ECA |
| RULE-M007 | 药品耗材采购价虚高检测 | 采购管理 | 采购价 vs 集采平台/兄弟医院价 | CASE-MED-ECA |
| RULE-M008 | 国有资产账实不符检测 | 资产管理 | 监盘结果 vs 账面差异率>5% | CASE-MED-ECA |
| RULE-M009 | 收入不入账/体外循环检测 | 收入管理 | HIS收费汇总 vs 财务账面月差异>1% | CASE-MED-ECA |
| RULE-M010 | 违规对外担保/抵押检测 | 对外担保管理 | 担保合同无上级批准文件 | CASE-MED-ECA |
| RULE-M011 | 违规变相举债检测 | 融资管理 | 固定回报/兜底回购条款未入负债 | CASE-MED-ECA |
| RULE-M012 | 决算数据不实检测 | 预算决算管理 | 决算报表 vs 总账/明细账差异>10万 | CASE-MED-ECA |
- **Q01-Q14**：行政事业单位经责典型问题14条（无锡市审计局）
| RULE-P001 | 虚假立项套取资金 | 立项决策 | 申报内容与实际建设不符 | CASE-PROJ-75 |
| RULE-P002 | 拆分项目规避审批 | 立项决策 | 单项投资压低至审批门槛以下 | CASE-PROJ-75 |
| RULE-P003 | 资金来源造假 | 立项决策 | 银行流水与到账凭证不符 | CASE-PROJ-75 |
| RULE-P004 | 低价中标后续变更获利 | 招投标 | 中标价远低于成本价+变更频繁 | CASE-PROJ-75 |
| RULE-P005 | 阴阳合同执行价偏离 | 招投标 | 备案合同价 vs 补充协议差异>10% | CASE-PROJ-75 |
| RULE-P006 | 围标串标联盟检测 | 招投标 | IP/MAC/制作机器码高度重合 | CASE-PROJ-75 |
| RULE-P007 | 虚报工程量套取结算 | 施工阶段 | 签证单 vs 实际 vs 结算三层差异>5% | CASE-PROJ-75 |
| RULE-P008 | 材料偷梁换柱 | 施工阶段 | 进场材料与合同不符 | CASE-PROJ-75 |
| RULE-P009 | 超付工程款 | 施工阶段 | 进度款支付比例>合同约定 | CASE-PROJ-75 |
| RULE-P010 | 资产转固滞后 | 财务管理 | 已使用资产挂账在建工程>12个月 | CASE-PROJ-75 |
| RULE-P011 | 质保金异常退还 | 竣工阶段 | 期满前提前退还或未扣维修费 | CASE-PROJ-75 |
- **压缩/Word/PDF/OCR批处理**：压缩包内存解压、Word限定词检测、PDF表格精准提取+Simhash趋同率、PaddleOCR图文识别

## 行业知识索引

| 行业 | 典型风险点 | 参考案例 |
|------|-----------|---------|
| 教育 | 课程采购拆分、教师招聘围标、科研经费挪用 | CASE-001 |
| 医疗 | 分解住院、过度诊疗、药品回扣、医保套现、DRG/DIP违规、集采规避、绩效超发 | CASE-002 + CASE-MED-ECA |
| 投资审计 | 招投标串标、评标专家失职、结算虚报、施工质量 | 参见"智慧审计平台架构.md" |
| 信息化审计 | 软件造价虚高、政务系统不合规、网络安全漏洞 | 参见"智慧审计平台架构.md" |
| 物业 | 租赁合同阴阳、能耗虚报、停车场收入截留 | CASE-003 |
| 经济责任审计 | 预算执行偏离、三公经费超标、国有资产流失、决策程序违规 | 参见"智慧审计平台架构.md"+eco-responsibility-audit/digital-eca.md |
| 银行/金融 | 票据兑付异常、贷款资金流向、监管指标偏离、内部人控制 | 参见rongce-gov-audit/references/bank-digital-audit.md |
| 国企审计 | 三重一大决策缺失、实物盘点差异、供应商集中风险、贸易模式异常 | CASE-005 |
| 财政/消费券 | 商户核销异常、团伙套现、手机号归属地异动、门槛差额集中在1元附近 | CASE-DATA-VOUCHER |
| 工程项目/基建 | 立项虚假/拆分规避/围标串标/低价中标/阴阳合同/虚报工程量/超付工程款/资产转固滞后 | CASE-PROJ-75 |
| 行政事业单位通用 | 三重一大流于形式、预算约束不强、违规收费、串通投标、合同管理、资产账实不符 | CASE-ECA-14Q |
| 审计技术方法 | OCR+批处理+Simhash/SQL实现Apriori/五维围标检测/NLP大模型定性 | CASE-NONSTRUCT-226 + CASE-BID-APRIORI + 非结构化数据处理深度分析 |

## 工具技能索引

| 技能 | 功能 | 触发词 |
|------|------|--------|
| **audit-report-ppt** | 审计报告PPT生成（受众蒸馏+页型映射） | 做PPT/生成PPT/汇报材料 |
| audit-report-writer | 审计报告写作辅助 | 写报告/报告润色 |
| audit-report-structured | 标准审计报告结构化生成 | 生成报告 |
| audit-data-analyst | 数据分析+异常检测 | 数据分析/异常检测 |
| audit-sql-patterns | SQL模板+4大案例 | SQL审计/查询模板 |
| audit-capa-tracker | 整改问题跟踪 | 整改跟踪 |
| rongce-gov-audit | 政府审计核心技能（90个之首） | 政府审计/经责审计 |
| audit-watchdog | 审计红线快速判断 | 红线判断/违规判断 |
| bid-collusion-audit | 串标围标审计 | 串标/围标/招投标 |
| audit-evidence-three-point | 审计证据三核对 | 证据充分/取证 |
| audit-law-check | 法规合规检查 | 法规检查/合法性 |
| audit-policy-monitor | 政策变化监控 | 政策变化/法规更新 |
| audit-pricing-monitor | 两新补贴价格审计 | 价格检查/补贴审计 |

详细索引：[工具技能索引](wiki/tools/index.md)

## Generated
<!-- openclaw:wiki:index:start -->
- Render mode: `obsidian`
- Total pages: 13
- Claims: 0
- Sources: 0
- Entities: 0
- Concepts: 0
- Syntheses: 0
- Reports: 9

### Sources
- No sources yet.

### Entities
- No entities yet.

### Concepts
- No concepts yet.

### Syntheses
- No syntheses yet.

### Reports
- [[reports/claim-health|Claim Health]]
- [[reports/contradictions|Contradictions]]
- [[reports/low-confidence|Low Confidence]]
- [[reports/open-questions|Open Questions]]
- [[reports/person-agent-directory|Person Agent Directory]]
- [[reports/privacy-review|Privacy Review]]
- [[reports/provenance-coverage|Provenance Coverage]]
- [[reports/relationship-graph|Relationship Graph]]
- [[reports/stale-pages|Stale Pages]]
<!-- openclaw:wiki:index:end -->
