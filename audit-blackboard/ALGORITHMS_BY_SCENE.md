# 政府审计算法库 · 按业务场景目录（135 算法）

> 来源：`audit-blackboard/algorithm_registry.json`（v5.0） ｜ 生成：2026-08-06 ｜ 一级场景 14 类，二级细分 52 类

> 旗舰=P0（40） ｜ 骨架=P1（95） ｜ 一个算法可归属多个场景（主场景+附加场景）

---

## 全景统计

| 指标 | 数值 |
|:--|:--|
| 算法总数 | 135 |
| 旗舰 P0 | 40 |
| 骨架 P1 | 95 |
| 一级业务场景 | 14 类 |
| 二级细分 | 52 类 |

## 招投标与政府采购（21 个算法，旗舰 6）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| BID-PATTERN-005 | Apriori关联规则围标模式识别算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter | 围标串标 | 主 |
| MED-BIDRIG-001 | 医疗采购围标串标检测算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter,data_scout | 围标串标 | 主 |
| PROC-CONCEN-001 | 供应商采购集中度异常识别算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter,data_scout | 供应商审查 | 主 |
| PROC-FAKE-001 | 供应商虚假材料三查算法 | 旗舰 | P0 | L3 | 合规性 | contract_hound,bid_hunter | 供应商审查 | 主 |
| PROC-RELATED-001 | 关联方13维检测算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter | 供应商审查 | 主 |
| SUPV-WARNING-001 | 审计预警风险画像算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout | — | 附 |
| BID-DARKMARK-001 | 暗标技术标'隐形记号'检测（文档元数据/字体颜色/编号指纹/页眉页脚/EXIF） | 骨架 | P1 | L2 | 合规性 | data_classifier,bid_hunter | 围标串标 | 主 |
| BID-ROTATE-001 | 互惠型陪标轮庄识别（跨项目轮流中标闭环+陪标费资金轨迹） | 骨架 | P1 | L3 | 真实性 | bid_hunter,data_scout | 围标串标 | 主 |
| BUDGET-018 | 政府采购电子卖场价格偏离检测算法 | 骨架 | P1 | L3 | 异常性 | data_scout,budget_estimator | 电子卖场与价格 | 主 |
| BUDGET-019 | 投标单位跨年度虚假资料检测算法 | 骨架 | P1 | L3 | 真实性 | bid_hunter,budget_estimator | — | 主 |
| HOSP-PARAM-001 | 公立医院采购围标串标识别（排他性参数+保证金资金同源+隐性收益结算） | 骨架 | P1 | L3 | 合规性 | bid_hunter,data_scout | 围标串标 | 主 |
| INVEST-001 | 电子投标文件特征码围标串标检测算法 | 骨架 | P1 | L3 | 合规性 | bid_hunter | 围标串标 | 主 |
| INVEST2-001 | 电子标书特征码串标检测 | 骨架 | P1 | L3 | 合规性 | bid_hunter | 围标串标 | 主 |
| MED2-001 | 养老服务工单配置超限检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout | — | 主 |
| PERF2-002 | 咨询服务费-供应商资质分拆支付检测 | 骨架 | P1 | L3 | 真实性 | fiscal_reviewer,performance_evaluator | 供应商审查 | 主 |
| PROC2-001 | 跨年度投标资料重复套用识别（文本相似度+错别字位置比对） | 骨架 | P1 | L3 | 真实性 | contract_hound,bid_hunter | — | 主 |
| PROC2-002 | 产权交易“受控拍卖”识别（矿业权/资产二次拍卖参数突变比对） | 骨架 | P1 | L2 | 合规性 | bid_hunter,review_sentinel | — | 主 |
| PROC2-003 | 政府采购电子卖场商品价格偏离度跨平台比价 | 骨架 | P1 | L3 | 异常性 | bid_hunter,data_scout | 电子卖场与价格 | 主 |
| PROC2-004 | 无介质围标串标团伙识别（共同投标频次+杰卡德相似系数+图数据库） | 骨架 | P1 | L3 | 合规性 | bid_hunter,data_scout | 围标串标 | 主 |
| SOCIAL2-008 | 医疗器械供应商壳特征画像检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 围标串标 | 主 |
| VENDOR-VERIFY-001 | 供应商虚假检测报告/认证证书/合同业绩三查核验（官方平台比对+三查机制） | 骨架 | P1 | L2 | 真实性 | bid_hunter,contract_hound | 供应商审查 | 主 |

## 农业农村审计（14 个算法，旗舰 2）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| AGR-INSFAKE-001 | 农业保险虚增面积骗补检测算法 | 旗舰 | P0 | L3 | 合规性 | data_scout | 涉农补贴与保险 | 主 |
| FIN-INSFAKE-001 | 政策性农业保险虚假投保理赔检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 涉农补贴与保险 | 主 |
| AGRI2-001 | 涉农合资公司国资流失检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,contract_hound | 乡村振兴产业 | 主 |
| AGRI3-001 | 消费补贴资金回流闭环检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 涉农补贴与保险 | 主 |
| AGRI3-002 | 补贴农机短期过户-新设主体检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 涉农补贴与保险 | 主 |
| AGRI3-003 | 关联企业重复获补检测 | 骨架 | P1 | L3 | 异常性 | data_scout | 涉农补贴与保险 | 主 |
| AGRI3-004 | 物资运输单据时空合理性校验 | 骨架 | P1 | L3 | 真实性 | data_scout | — | 主 |
| AGRI3-005 | 无实物交付资产入账检测 | 骨架 | P1 | L2 | 真实性 | adjustment_scribe,data_scout | 乡村振兴产业 | 主 |
| AGRI3-006 | 农业保险全出险-无养殖事实检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 涉农补贴与保险 | 主 |
| BUDGET-013 | 以工代赈项目虚假用工检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 乡村振兴产业 | 主 |
| BUDGET-017 | 村级财务'白条'入账检测算法 | 骨架 | P1 | L2 | 真实性 | workpaper_crafter,budget_estimator | 村级财务 | 主 |
| FIN3-001 | 政策性保险投保-理赔交叉校验 | 骨架 | P1 | L3 | 真实性 | data_scout | 涉农补贴与保险 | 主 |
| GRAIN-001 | 储备粮轮换运输真实性核验（过磅单+运输轨迹+费用条款三角验证） | 骨架 | P1 | L2 | 真实性 | data_scout,settlement_auditor | 粮食储备 | 主 |
| PERF2-004 | 储备粮损耗率超限检测 | 骨架 | P1 | L3 | 真实性 | data_scout,performance_evaluator | 粮食储备 | 主 |

## 民生与社保医保（27 个算法，旗舰 8）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| BIGDATA-SERVICE-001 | 服务工单时空验证算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 养老与救助 | 主 |
| FUND-FRAUD-001 | FP-Growth关联规则骗保/骗补模式识别算法 | 旗舰 | P0 | L3 | 合规性 | data_scout,performance_evaluator | 社保基金 | 主 |
| MED-BIDRIG-001 | 医疗采购围标串标检测算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter,data_scout | — | 附 |
| SOCIAL-INS-001 | 社保基金多源数据比对检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 社保基金 | 主 |
| SOCIAL-MAT-001 | 医保生育津贴多维骗保检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 社保基金 | 主 |
| SOCIAL-WELFARE-001 | 惠民补贴应享未享与虚报冒领检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 养老与救助 | 主 |
| SOCIAL-WORK-001 | 工伤保险基金安全多信号检测算法 | 旗舰 | P0 | L3 | 合规性 | data_scout | 社保基金 | 主 |
| TRANSFER-TRACE-001 | 转移支付资金全链路追踪算法 | 旗舰 | P0 | L3 | 完整性 | budget_estimator,fiscal_reviewer | 社保基金 | 主 |
| AGRI3-001 | 消费补贴资金回流闭环检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 就业与消费补贴 | 附 |
| ASSET-REVIVE-001 | 闲置校舍等沉没资产盘活效益评估（转型投入-收益-替代-民生四维测算） | 骨架 | P1 | L2 | 完整性 | data_scout,budget_estimator | 养老与救助 | 主 |
| BUDGET-008 | 补贴对象重复与身份异常申报检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 就业与消费补贴 | 主 |
| BUDGET-009 | 民生补贴顶格申报异常检测算法 | 骨架 | P1 | L2 | 真实性 | data_scout,budget_estimator | 养老与救助 | 主 |
| BUDGET-010 | 惠企减租补贴真实性核验算法 | 骨架 | P1 | L2 | 真实性 | contract_hound,budget_estimator | 就业与消费补贴 | 主 |
| DATA3-001 | 上门服务工单时空冲突检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 养老与救助 | 主 |
| EMPLOY-SUB-001 | 就业补助资金九项疑点SQL筛查（重复领取/死亡冒领/多头申报/虚假劳动合同） | 骨架 | P1 | L3 | 真实性 | data_scout,review_sentinel | 社保基金 | 主 |
| FUND2-001 | 消费品以旧换新补贴“人货单钱”四维防线 | 骨架 | P1 | L3 | 真实性 | data_scout,bid_hunter | 就业与消费补贴 | 主 |
| HOSP-PARAM-001 | 公立医院采购围标串标识别（排他性参数+保证金资金同源+隐性收益结算） | 骨架 | P1 | L3 | 合规性 | bid_hunter,data_scout | 医保基金 | 附 |
| MED2-001 | 养老服务工单配置超限检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout | 养老与救助 | 附 |
| POLICY-001 | 转移支付资金闭环监管指标算法 | 骨架 | P1 | L2 | 真实性 | budget_estimator,fiscal_reviewer | 社保基金 | 主 |
| SOCIAL2-001 | 医用耗材领用-结算量偏差检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 医保基金 | 主 |
| SOCIAL2-002 | 社保高申领率-即停保壳公司检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 社保基金 | 主 |
| SOCIAL2-003 | 燃气补贴多部门数据一致性校验 | 骨架 | P1 | L3 | 真实性 | data_scout | — | 主 |
| SOCIAL2-004 | DRG病组套码高付费检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 医保基金 | 主 |
| SOCIAL2-006 | 消费券代发核销-真实交易交叉校验 | 骨架 | P1 | L3 | 真实性 | data_scout | 就业与消费补贴 | 主 |
| SOCIAL2-007 | 工伤辅助器具高频更换检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 工伤保障 | 主 |
| SOCIAL2-008 | 医疗器械供应商壳特征画像检测 | 骨架 | P1 | L3 | 真实性 | data_scout | — | 附 |
| SOCIAL3-001 | 居家养老上门服务工单真实性（时空重叠+穿越+工单限额+人员资质四规则） | 骨架 | P1 | L3 | 合规性 | data_scout,review_sentinel | 养老与救助 | 主 |

## 金融审计（12 个算法，旗舰 5）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| AGR-INSFAKE-001 | 农业保险虚增面积骗补检测算法 | 旗舰 | P0 | L3 | 合规性 | data_scout | 保险基金 | 附 |
| FIN-INSFAKE-001 | 政策性农业保险虚假投保理赔检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 保险基金 | 附 |
| FIN-SHELL-001 | 空壳公司信贷欺诈检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 信贷与银行 | 主 |
| SOCIAL-INS-001 | 社保基金多源数据比对检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 保险基金 | 附 |
| SOCIAL-WORK-001 | 工伤保险基金安全多信号检测算法 | 旗舰 | P0 | L3 | 合规性 | data_scout | 保险基金 | 附 |
| AGRI3-006 | 农业保险全出险-无养殖事实检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 保险基金 | 附 |
| DATA3-002 | 员工-客户资金往来关联检测 | 骨架 | P1 | L3 | 穿透性 | data_scout | 信贷与银行 | 主 |
| FIN2-001 | 银行费用支出资金回流检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout | 信贷与银行 | 主 |
| FIN3-001 | 政策性保险投保-理赔交叉校验 | 骨架 | P1 | L3 | 真实性 | data_scout | 保险基金 | 附 |
| FIN3-002 | 资管产品估值平滑-刚性兑付检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 资管与基金投资 | 主 |
| FIN3-003 | 农商行快贷虚假资料多层交叉验证（客户经理行为+业务集中度+三址合一） | 骨架 | P1 | L3 | 真实性 | data_scout,law_inspector | 信贷与银行 | 主 |
| SOCIAL2-007 | 工伤辅助器具高频更换检测 | 骨架 | P1 | L3 | 真实性 | data_scout | 保险基金 | 附 |

## 工程与投资审计（22 个算法，旗舰 7）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| BID-PATTERN-005 | Apriori关联规则围标模式识别算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter | — | 附 |
| CHK-RECON-001 | 多源数据勾稽核对通用算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,review_sentinel | — | 附 |
| ENG-FINAL-001 | 工程竣工财务决算AI复核算法 | 旗舰 | P0 | L3 | 真实性 | settlement_auditor,review_sentinel | 竣工决算与结算 | 主 |
| ENG-RATIO-001 | 工程支出合理性比例检测算法 | 旗舰 | P0 | L3 | 效益性 | settlement_auditor,budget_estimator | 政府投资项目 | 主 |
| ENG-SAMPLE-001 | LightGBM工程结算自动抽样复审算法 | 旗舰 | P0 | L3 | 效益性 | settlement_auditor | 竣工决算与结算 | 主 |
| ENG-SCORE-001 | LightGBM一审审计质量自动评分算法 | 旗舰 | P0 | L3 | 管理性 | settlement_auditor,fiscal_reviewer | 竣工决算与结算 | 主 |
| PROC-CONCEN-001 | 供应商采购集中度异常识别算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter,data_scout | — | 附 |
| AGRI3-004 | 物资运输单据时空合理性校验 | 骨架 | P1 | L3 | 真实性 | data_scout | — | 附 |
| BUDGET-002 | 政府投资基金资金循环回流检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,bid_hunter | 政府投资项目 | 主 |
| BUDGET-012 | 政府投资基金'画皮'项目识别算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 政府投资项目 | 主 |
| CONCESS-DEBT-001 | 特许经营项目化债风险穿透审计（明股实债/支出责任固化/使用者付费真实性） | 骨架 | P1 | L4 | 真实性 | contract_hound,data_scout | — | 主 |
| ENG2-001 | 土方挖运工程量GIS真实性核验（变化检测+挖填平衡+弃土量三维测算） | 骨架 | P1 | L3 | 真实性 | settlement_auditor,data_scout | 工程量与造价 | 主 |
| EXPSTD-CHECK-001 | 经费类支出标准符合性评审（29项支出定额比对） | 骨架 | P1 | L2 | 合规性 | budget_estimator,fiscal_reviewer | 信息化项目 | 主 |
| HOSP-PARAM-001 | 公立医院采购围标串标识别（排他性参数+保证金资金同源+隐性收益结算） | 骨架 | P1 | L3 | 合规性 | bid_hunter,data_scout | 竣工决算与结算 | 附 |
| INV-APPROVAL-001 | 政府投资项目规避审批与概算约束识别（国企代报规避审批+超概算追责） | 骨架 | P1 | L3 | 合规性 | budget_estimator,contract_hound | 政府投资项目 | 主 |
| INVEST-001 | 电子投标文件特征码围标串标检测算法 | 骨架 | P1 | L3 | 合规性 | bid_hunter | — | 附 |
| INVEST2-001 | 电子标书特征码串标检测 | 骨架 | P1 | L3 | 合规性 | bid_hunter | — | 附 |
| INVEST2-002 | 征拆补偿图斑-影像面积比对 | 骨架 | P1 | L3 | 真实性 | data_scout | 征地拆迁 | 主 |
| INVEST2-003 | 工程量签证单虚增检测 | 骨架 | P1 | L2 | 真实性 | settlement_auditor | 竣工决算与结算 | 主 |
| ITCOST-001 | 信息化项目软件造价审计（功能点分析+三类费用界定） | 骨架 | P1 | L3 | 真实性 | settlement_auditor,contract_hound | 工程量与造价 | 主 |
| PROC2-004 | 无介质围标串标团伙识别（共同投标频次+杰卡德相似系数+图数据库） | 骨架 | P1 | L3 | 合规性 | bid_hunter,data_scout | — | 附 |
| WAT-CONSTR-001 | 水利项目建设资金归集挪用与专款专用核查（资金外借/归集/转移轨迹） | 骨架 | P1 | L3 | 真实性 | data_scout,settlement_auditor | 政府投资项目 | 主 |

## 资源环境审计（12 个算法，旗舰 2）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| ENV-CHECKLIST-001 | 自然资源经责审计清单对照算法 | 旗舰 | P0 | L3 | 真实性 | law_inspector,performance_evaluator | 自然资源资产 | 主 |
| ENV-RS-001 | 遥感变化图斑穿透检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,law_inspector | 自然资源资产 | 主 |
| BUDGET-007 | 代征非税收入上缴及时足额性检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | — | 主 |
| CHK2-001 | 污水处理费征缴稽核（差别费率+用水性质+自备水源+代征上缴四模型） | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | — | 主 |
| ENV3-001 | 超许可深度采矿检测 | 骨架 | P1 | L3 | 合规性 | data_scout,law_inspector | 矿业与土地 | 主 |
| ENV3-002 | 地表异常变化时序检测 | 骨架 | P1 | L3 | 异常性 | data_scout,law_inspector | — | 主 |
| ENV3-003 | 矿业权转让异常溢价检测 | 骨架 | P1 | L3 | 合规性 | contract_hound,law_inspector | 矿业与土地 | 主 |
| ENV4-001 | 工业用地“退二进三”违规识别（地址模糊匹配+缓冲区空间相交） | 骨架 | P1 | L3 | 真实性 | data_scout,fiscal_reviewer | 矿业与土地 | 主 |
| ENV4-002 | 公益林侵占NDVI遥感识别（植被指数+栅格矢量化+图斑相交） | 骨架 | P1 | L3 | 完整性 | data_scout,fiscal_reviewer | 自然资源资产 | 主 |
| INVEST2-002 | 征拆补偿图斑-影像面积比对 | 骨架 | P1 | L3 | 真实性 | data_scout | 遥感与地理信息 | 附 |
| NATRES-AUDIT-001 | 自然资源资产离任审计五维问题清单（政策执行/法规遵守/重大决策/目标完成/监督责任） | 骨架 | P1 | L3 | 合规性 | data_scout,law_inspector | 自然资源资产 | 主 |
| PROC2-002 | 产权交易“受控拍卖”识别（矿业权/资产二次拍卖参数突变比对） | 骨架 | P1 | L2 | 合规性 | bid_hunter,review_sentinel | 矿业与土地 | 附 |

## 国企审计（25 个算法，旗舰 14）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| ASSET-MATCH-001 | 账实核对资产状态异常检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 主 |
| CHK-LOSS-001 | 亏损项目六步穿透检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout,contract_hound | 亏损与投资损失 | 主 |
| CHK-RD-001 | 研发支出三程序穿透算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,law_inspector | 研发与人力 | 主 |
| CHK-RECON-001 | 多源数据勾稽核对通用算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,review_sentinel | — | 附 |
| FIN-SHELL-001 | 空壳公司信贷欺诈检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 附 |
| HR-RF-001 | 随机森林虚列培训费检测算法 | 旗舰 | P0 | L3 | 合规性 | data_scout | 研发与人力 | 主 |
| HR-RF-002 | 随机森林在职不在岗人员检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout | 研发与人力 | 主 |
| PROC-CONCEN-001 | 供应商采购集中度异常识别算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter,data_scout | — | 附 |
| PROC-RELATED-001 | 关联方13维检测算法 | 旗舰 | P0 | L3 | 廉洁性 | bid_hunter | — | 附 |
| SOE-MIDMAN-001 | 中间人异常交易检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout,contract_hound | 供应链与中间人 | 主 |
| SUPV-ANOMALY-001 | Benford定律财务数据异常检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 主 |
| SUPV-POCKET-001 | 小金库四信号检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout,contract_hound | — | 主 |
| SUPV-TRAVEL-001 | 差旅费四信号真实性检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 主 |
| SUPV-WARNING-001 | 审计预警风险画像算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout | — | 附 |
| AGRI2-001 | 涉农合资公司国资流失检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,contract_hound | 国资运营 | 附 |
| BUDGET-002 | 政府投资基金资金循环回流检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,bid_hunter | — | 附 |
| BUDGET-006 | 国有资产出租收入完整性检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 国资运营 | 主 |
| FIN3-003 | 农商行快贷虚假资料多层交叉验证（客户经理行为+业务集中度+三址合一） | 骨架 | P1 | L3 | 真实性 | data_scout,law_inspector | — | 附 |
| INV-APPROVAL-001 | 政府投资项目规避审批与概算约束识别（国企代报规避审批+超概算追责） | 骨架 | P1 | L3 | 合规性 | budget_estimator,contract_hound | — | 附 |
| LOSS-PENETRATE-001 | 亏损项目'六步穿透法'（决策起点-资金流向-程序合规-真假亏损判别） | 骨架 | P1 | L4 | 真实性 | data_scout,contract_hound | 亏损与投资损失 | 主 |
| PERF2-001 | 异常贸易-交易对手风险检测 | 骨架 | P1 | L3 | 异常性 | performance_evaluator | 供应链与中间人 | 主 |
| SOE3-001 | 集团内业务绕道中间人-无期限合同检测 | 骨架 | P1 | L3 | 合规性 | contract_hound | 供应链与中间人 | 主 |
| SOE3-002 | 高息融资突击还款检测 | 骨架 | P1 | L3 | 异常性 | data_scout,contract_hound | — | 主 |
| SOE3-003 | 虚假研发团队工资套取检测 | 骨架 | P1 | L3 | 真实性 | data_scout,contract_hound | 研发与人力 | 主 |
| WAT-CONSTR-001 | 水利项目建设资金归集挪用与专款专用核查（资金外借/归集/转移轨迹） | 骨架 | P1 | L3 | 真实性 | data_scout,settlement_auditor | — | 附 |

## 财政与政府债务（20 个算法，旗舰 6）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| BOND-PENETRATE-001 | 专项债资金穿透式监测算法 | 旗舰 | P0 | L3 | 真实性 | budget_estimator,fiscal_reviewer | 专项债 | 主 |
| FIN-INSFAKE-001 | 政策性农业保险虚假投保理赔检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 附 |
| SOCIAL-INS-001 | 社保基金多源数据比对检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 附 |
| SOCIAL-MAT-001 | 医保生育津贴多维骗保检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 附 |
| SOCIAL-WORK-001 | 工伤保险基金安全多信号检测算法 | 旗舰 | P0 | L3 | 合规性 | data_scout | — | 附 |
| TRANSFER-TRACE-001 | 转移支付资金全链路追踪算法 | 旗舰 | P0 | L3 | 完整性 | budget_estimator,fiscal_reviewer | 转移支付 | 附 |
| BUDGET-001 | 专项债券资金支出进度真实性核验算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 专项债 | 主 |
| BUDGET-002 | 政府投资基金资金循环回流检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,bid_hunter | — | 附 |
| BUDGET-011 | 招商引资补贴项目存活异常检测算法 | 骨架 | P1 | L2 | 真实性 | data_scout,settlement_auditor | — | 主 |
| BUDGET-012 | 政府投资基金'画皮'项目识别算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | — | 附 |
| BUDGET-014 | 超长期特别国债资金投向合规检测算法 | 骨架 | P1 | L2 | 合规性 | budget_estimator | — | 主 |
| BUDGET-015 | 专项债收益自平衡真实性评估算法 | 骨架 | P1 | L2 | 效率性 | budget_estimator | 专项债 | 主 |
| CONCESS-DEBT-001 | 特许经营项目化债风险穿透审计（明股实债/支出责任固化/使用者付费真实性） | 骨架 | P1 | L4 | 真实性 | contract_hound,data_scout | 债务风险与化债 | 附 |
| CONCESS-FEE-001 | 特许经营公共服务项目费用测算四维框架（成本-收入-风险-绩效+全生命周期） | 骨架 | P1 | L3 | 效率性 | performance_evaluator,budget_estimator | 特许经营 | 主 |
| COUNTY-RISK-001 | 县域财政风险预警指标体系（债务率/库款保障/支出刚性/财源结构四维） | 骨架 | P1 | L2 | 真实性 | data_scout,budget_estimator | 债务风险与化债 | 主 |
| POLICY-001 | 转移支付资金闭环监管指标算法 | 骨架 | P1 | L2 | 真实性 | budget_estimator,fiscal_reviewer | 转移支付 | 附 |
| SOCIAL2-001 | 医用耗材领用-结算量偏差检测 | 骨架 | P1 | L3 | 真实性 | data_scout | — | 附 |
| SOCIAL2-004 | DRG病组套码高付费检测 | 骨架 | P1 | L3 | 真实性 | data_scout | — | 附 |
| SOCIAL2-007 | 工伤辅助器具高频更换检测 | 骨架 | P1 | L3 | 真实性 | data_scout | — | 附 |
| WAT-CONSTR-001 | 水利项目建设资金归集挪用与专款专用核查（资金外借/归集/转移轨迹） | 骨架 | P1 | L3 | 真实性 | data_scout,settlement_auditor | — | 附 |

## 预算执行与财政管理（24 个算法，旗舰 6）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| BUD-CHECKLIST-001 | 预算执行60条违规清单对照算法 | 旗舰 | P0 | L3 | 合规性 | budget_estimator,review_sentinel | 预算执行 | 主 |
| CHK-RECON-001 | 多源数据勾稽核对通用算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,review_sentinel | 预算执行 | 附 |
| PERF-DEVIATION-001 | 绩效指标偏离度多维检测算法 | 旗舰 | P0 | L3 | 真实性 | performance_evaluator | — | 主 |
| PERF-OUTLIER-001 | K-Means聚类孤立点异常检测算法 | 旗舰 | P0 | L3 | 异常性 | data_scout,performance_evaluator | 预算执行 | 主 |
| REV-PREDICT-001 | 线性回归收入与用户合理性预测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,budget_estimator | 预算执行 | 主 |
| SOCIAL-WELFARE-001 | 惠民补贴应享未享与虚报冒领检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 附 |
| BUDGET-003 | 公用经费预算申报偏差检测算法 | 骨架 | P1 | L2 | 异常性 | budget_estimator | 预算执行 | 主 |
| BUDGET-004 | 往来科目隐匿资金检测算法 | 骨架 | P1 | L2 | 真实性 | workpaper_crafter,budget_estimator | — | 主 |
| BUDGET-005 | 公务车辆运行费用异常检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 公用经费与三公 | 主 |
| BUDGET-006 | 国有资产出租收入完整性检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 非税收入 | 附 |
| BUDGET-007 | 代征非税收入上缴及时足额性检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 非税收入 | 附 |
| BUDGET-016 | 财政收支异常波动检测算法（局部加权线性回归） | 骨架 | P1 | L3-ML | 异常性 | data_scout,budget_estimator | 预算执行 | 主 |
| BUDGET-019 | 投标单位跨年度虚假资料检测算法 | 骨架 | P1 | L3 | 真实性 | bid_hunter,budget_estimator | 预算执行 | 附 |
| BUDGET-020 | 公用经费通信费用支出异常检测算法 | 骨架 | P1 | L2 | 真实性 | data_scout,budget_estimator | 公用经费与三公 | 主 |
| CHK2-001 | 污水处理费征缴稽核（差别费率+用水性质+自备水源+代征上缴四模型） | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 非税收入 | 附 |
| CONCESS-FEE-001 | 特许经营公共服务项目费用测算四维框架（成本-收入-风险-绩效+全生命周期） | 骨架 | P1 | L3 | 效率性 | performance_evaluator,budget_estimator | — | 附 |
| ECONRESP-001 | 公务用车平台数据异常检测算法 | 骨架 | P1 | L3 | 合规性 | data_scout,fiscal_reviewer | 公用经费与三公 | 主 |
| ECONRESP2-003 | 公车超编-里程异常检测 | 骨架 | P1 | L3 | 合规性 | data_scout,fiscal_reviewer | 公用经费与三公 | 主 |
| EXPSTD-CHECK-001 | 经费类支出标准符合性评审（29项支出定额比对） | 骨架 | P1 | L2 | 合规性 | budget_estimator,fiscal_reviewer | 预算编制与评审 | 附 |
| PERF-COST-001 | 运转类项目成本预算绩效分析六步法（定类型-拆运行-核成本-评绩效-出标准-促管理） | 骨架 | P1 | L3 | 合规性 | performance_evaluator,budget_estimator | 公用经费与三公 | 主 |
| PERF2-003 | 预算项目最小单元重复申报识别 | 骨架 | P1 | L3 | 异常性 | budget_estimator,performance_evaluator | 预算编制与评审 | 主 |
| PROC2-001 | 跨年度投标资料重复套用识别（文本相似度+错别字位置比对） | 骨架 | P1 | L3 | 真实性 | contract_hound,bid_hunter | 预算执行 | 附 |
| SOCIAL2-003 | 燃气补贴多部门数据一致性校验 | 骨架 | P1 | L3 | 真实性 | data_scout | 非税收入 | 附 |
| WATER-SQL-001 | 水费征收SQL三查（违约金未收/阶梯水价未执行/少收水量） | 骨架 | P1 | L2 | 完整性 | data_scout,settlement_auditor | 非税收入 | 主 |

## 绩效评价（13 个算法，旗舰 5）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| CHK-LOSS-001 | 亏损项目六步穿透检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout,contract_hound | 成本效益 | 附 |
| CHK-RD-001 | 研发支出三程序穿透算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,law_inspector | 成本效益 | 附 |
| ENG-RATIO-001 | 工程支出合理性比例检测算法 | 旗舰 | P0 | L3 | 效益性 | settlement_auditor,budget_estimator | 绩效指标 | 附 |
| PERF-DEVIATION-001 | 绩效指标偏离度多维检测算法 | 旗舰 | P0 | L3 | 真实性 | performance_evaluator | 绩效指标 | 附 |
| PERF-OUTLIER-001 | K-Means聚类孤立点异常检测算法 | 旗舰 | P0 | L3 | 异常性 | data_scout,performance_evaluator | 绩效指标 | 附 |
| ASSET-REVIVE-001 | 闲置校舍等沉没资产盘活效益评估（转型投入-收益-替代-民生四维测算） | 骨架 | P1 | L2 | 完整性 | data_scout,budget_estimator | — | 附 |
| BUDGET-016 | 财政收支异常波动检测算法（局部加权线性回归） | 骨架 | P1 | L3-ML | 异常性 | data_scout,budget_estimator | — | 附 |
| CONCESS-FEE-001 | 特许经营公共服务项目费用测算四维框架（成本-收入-风险-绩效+全生命周期） | 骨架 | P1 | L3 | 效率性 | performance_evaluator,budget_estimator | 绩效指标 | 附 |
| PERF-COST-001 | 运转类项目成本预算绩效分析六步法（定类型-拆运行-核成本-评绩效-出标准-促管理） | 骨架 | P1 | L3 | 合规性 | performance_evaluator,budget_estimator | 绩效指标 | 附 |
| PERF2-001 | 异常贸易-交易对手风险检测 | 骨架 | P1 | L3 | 异常性 | performance_evaluator | 绩效指标 | 附 |
| PERF2-003 | 预算项目最小单元重复申报识别 | 骨架 | P1 | L3 | 异常性 | budget_estimator,performance_evaluator | 绩效指标 | 附 |
| PERF2-004 | 储备粮损耗率超限检测 | 骨架 | P1 | L3 | 真实性 | data_scout,performance_evaluator | 绩效指标 | 附 |
| PROC2-003 | 政府采购电子卖场商品价格偏离度跨平台比价 | 骨架 | P1 | L3 | 异常性 | bid_hunter,data_scout | 绩效指标 | 附 |

## 经济责任审计（19 个算法，旗舰 7）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| CHK-LOSS-001 | 亏损项目六步穿透检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout,contract_hound | 经责核查 | 附 |
| ENV-CHECKLIST-001 | 自然资源经责审计清单对照算法 | 旗舰 | P0 | L3 | 真实性 | law_inspector,performance_evaluator | 经责核查 | 附 |
| ENV-RS-001 | 遥感变化图斑穿透检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,law_inspector | 经责核查 | 附 |
| FUND-SIPHON-001 | 套取资金三分类检测算法（含五对照法） | 旗舰 | P0 | L3 | 真实性 | data_scout,workpaper_crafter | 经责核查 | 主 |
| SOE-MIDMAN-001 | 中间人异常交易检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout,contract_hound | 经责核查 | 附 |
| SUPV-POCKET-001 | 小金库四信号检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout,contract_hound | 经责核查 | 附 |
| SUPV-WARNING-001 | 审计预警风险画像算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout | 经责核查 | 附 |
| BUDGET-005 | 公务车辆运行费用异常检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | — | 附 |
| BUDGET-012 | 政府投资基金'画皮'项目识别算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 经责核查 | 附 |
| BUDGET-017 | 村级财务'白条'入账检测算法 | 骨架 | P1 | L2 | 真实性 | workpaper_crafter,budget_estimator | 经责核查 | 附 |
| ECONRESP-001 | 公务用车平台数据异常检测算法 | 骨架 | P1 | L3 | 合规性 | data_scout,fiscal_reviewer | 经责核查 | 附 |
| ECONRESP2-001 | 未履约全额结算检测 | 骨架 | P1 | L2 | 合规性 | contract_hound,fiscal_reviewer | 经责核查 | 主 |
| ECONRESP2-002 | 收费票据-台账-缴款三账比对 | 骨架 | P1 | L2 | 真实性 | data_scout,fiscal_reviewer | 经责核查 | 主 |
| ECONRESP2-003 | 公车超编-里程异常检测 | 骨架 | P1 | L3 | 合规性 | data_scout,fiscal_reviewer | 经责核查 | 附 |
| ENV4-002 | 公益林侵占NDVI遥感识别（植被指数+栅格矢量化+图斑相交） | 骨架 | P1 | L3 | 完整性 | data_scout,fiscal_reviewer | 离任审计 | 附 |
| HR-EATEMPTY-001 | 吃空饷'五对照'核查（编制-岗位-任务-考勤-群众言论） | 骨架 | P1 | L2 | 真实性 | data_scout,review_sentinel | 经责核查 | 主 |
| LOSS-PENETRATE-001 | 亏损项目'六步穿透法'（决策起点-资金流向-程序合规-真假亏损判别） | 骨架 | P1 | L4 | 真实性 | data_scout,contract_hound | 经责核查 | 附 |
| NATRES-AUDIT-001 | 自然资源资产离任审计五维问题清单（政策执行/法规遵守/重大决策/目标完成/监督责任） | 骨架 | P1 | L3 | 合规性 | data_scout,law_inspector | 离任审计 | 附 |
| WATER-SQL-001 | 水费征收SQL三查（违约金未收/阶梯水价未执行/少收水量） | 骨架 | P1 | L2 | 完整性 | data_scout,settlement_auditor | 经责核查 | 附 |

## 监督检查与经费舞弊（17 个算法，旗舰 8）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| BUD-CHECKLIST-001 | 预算执行60条违规清单对照算法 | 旗舰 | P0 | L3 | 合规性 | budget_estimator,review_sentinel | — | 附 |
| FUND-SIPHON-001 | 套取资金三分类检测算法（含五对照法） | 旗舰 | P0 | L3 | 真实性 | data_scout,workpaper_crafter | 小金库与资金套取 | 附 |
| HR-RF-001 | 随机森林虚列培训费检测算法 | 旗舰 | P0 | L3 | 合规性 | data_scout | — | 附 |
| PERF-DEVIATION-001 | 绩效指标偏离度多维检测算法 | 旗舰 | P0 | L3 | 真实性 | performance_evaluator | — | 附 |
| SUPV-ANOMALY-001 | Benford定律财务数据异常检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | — | 附 |
| SUPV-POCKET-001 | 小金库四信号检测算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout,contract_hound | 小金库与资金套取 | 附 |
| SUPV-TRAVEL-001 | 差旅费四信号真实性检测算法 | 旗舰 | P0 | L3 | 真实性 | data_scout | 差旅与报销 | 附 |
| SUPV-WARNING-001 | 审计预警风险画像算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout | — | 附 |
| BUDGET-017 | 村级财务'白条'入账检测算法 | 骨架 | P1 | L2 | 真实性 | workpaper_crafter,budget_estimator | — | 附 |
| COUNTY-RISK-001 | 县域财政风险预警指标体系（债务率/库款保障/支出刚性/财源结构四维） | 骨架 | P1 | L2 | 真实性 | data_scout,budget_estimator | — | 附 |
| EINV-CROSS-001 | 电子发票多源融合智能稽核（重复报销/超范围开票/发票状态异常） | 骨架 | P1 | L3 | 合规性 | data_scout,review_sentinel | 差旅与报销 | 主 |
| ENV4-001 | 工业用地“退二进三”违规识别（地址模糊匹配+缓冲区空间相交） | 骨架 | P1 | L3 | 真实性 | data_scout,fiscal_reviewer | — | 附 |
| EXPSTD-CHECK-001 | 经费类支出标准符合性评审（29项支出定额比对） | 骨架 | P1 | L2 | 合规性 | budget_estimator,fiscal_reviewer | — | 附 |
| HR-EATEMPTY-001 | 吃空饷'五对照'核查（编制-岗位-任务-考勤-群众言论） | 骨架 | P1 | L2 | 真实性 | data_scout,review_sentinel | 小金库与资金套取 | 附 |
| NATRES-AUDIT-001 | 自然资源资产离任审计五维问题清单（政策执行/法规遵守/重大决策/目标完成/监督责任） | 骨架 | P1 | L3 | 合规性 | data_scout,law_inspector | — | 附 |
| TRAVEL-SIGNAL-001 | 差旅费报销四信号自动筛查（非工作日/整百金额/多人同额/住宿尾数异常） | 骨架 | P1 | L2 | 真实性 | data_scout,review_sentinel | 差旅与报销 | 主 |
| WHISTLE-FLOW-001 | 财会监督举报受理闭环机制评估（受理-查处-跟踪-整改四环节+运行指标） | 骨架 | P1 | L2 | 有效性 | meeting_minutes_analyzer,review_sentinel | 小金库与资金套取 | 主 |

## 税务审计（6 个算法，旗舰 0）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| BUDGET-006 | 国有资产出租收入完整性检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 发票与税收 | 附 |
| BUDGET-007 | 代征非税收入上缴及时足额性检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 发票与税收 | 附 |
| CHK2-001 | 污水处理费征缴稽核（差别费率+用水性质+自备水源+代征上缴四模型） | 骨架 | P1 | L3 | 真实性 | data_scout,budget_estimator | 发票与税收 | 附 |
| FIN2-001 | 银行费用支出资金回流检测算法 | 骨架 | P1 | L3 | 真实性 | data_scout | 发票与税收 | 附 |
| TAX-001 | 网络货运平台虚开发票识别（开票集中度+运单时空矛盾+税收返还套利） | 骨架 | P1 | L3 | 真实性 | data_scout,law_inspector | 发票与税收 | 主 |
| TAX-ESCAPE-001 | 逃逸式注销与非交易过户税源追征核查（虚假清算报告+隐匿资产识别） | 骨架 | P1 | L3 | 真实性 | data_scout,law_inspector | 发票与税收 | 主 |

## 全场景通用（5 个算法，旗舰 4）

| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| BIGDATA-SQL-001 | SQL审计范式模板库算法 | 旗舰 | P0 | L3 | 异常性 | data_scout | SQL审计范式 | 主 |
| CHK-RECON-001 | 多源数据勾稽核对通用算法 | 旗舰 | P0 | L3 | 真实性 | data_scout,review_sentinel | 数据勾稽与核对 | 主 |
| RULE-MATCH-001 | 语义相似度审计规则智能匹配算法 | 旗舰 | P0 | L3 | 管理性 | data_scout,law_inspector | 规则匹配 | 主 |
| SUPV-WARNING-001 | 审计预警风险画像算法 | 旗舰 | P0 | L3 | 廉洁性 | data_scout | 风险画像与预警 | 主 |
| CHK2-002 | 跨部门同一业务补贴数据勾稽差异识别（双台账一致性校验） | 骨架 | P1 | L2 | 真实性 | data_scout,review_sentinel | 数据勾稽与核对 | 主 |

---

## 使用说明

- **归属列**：`主`=该算法在此场景的主场景，`附`=附加适用场景（一个算法可有多个附加场景）

- 程序化查询：`python -X utf8 -c "from algorithm_loader import list_algorithms_by_scene; import json; print(json.dumps(list_algorithms_by_scene('社保审计'), ensure_ascii=False, indent=1))"`

- 场景体系定义：`scene_taxonomy.json` ｜ 场景→算法映射：`algorithms_by_scene.json`

- 重建本文档：`python -X utf8 build_scene_catalog.py`（读取 algorithm_registry.json 重新生成）
