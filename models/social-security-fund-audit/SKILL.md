---
name: social-security-fund-audit
description: 社保基金审计模型 — 覆盖养老保险、医疗保险、工伤保险、失业保险、生育保险五大险种。五维穿透审计框架：基金筹集→待遇支出→业务经办→基金管理→制度执行。集成128数据分析模型+15领域飞检风险+审计署审计结果+预算绩效管理。
---

# 社保基金审计模型 v1.1

> 融策 | 基于8份资料综合构建：审计署2017-1号+泉州128模型+昆明特派办+飞检15领域+工伤保险案例+预算绩效管理+4篇学术论文+法发2024-6号刑事指导意见
> 新增v1.1：法规六层体系 + 刑事责任认定维度 + 知识图谱方法 + Hadoop大数据方案 + 5个新SQL模型(M21-M25)

## 适用场景

| 险种 | 审计重点 |
|:--|:--|
| 基本养老保险 | 基金收支缺口、重复参保、待遇重复领取、一次性补缴套利 |
| 基本医疗保险 | 骗保套取、虚记费用、串换药品、分解住院、DRG高编高套 |
| 工伤保险 | 工伤认定尺度不一、辅助器具配置异常、非工伤用药结算 |
| 失业保险 | 虚构失业骗取、稳岗补贴挪用、培训补贴虚报 |
| 生育保险 | 合并实施后基金混用、虚报生育医疗费 |

## 五维穿透审计框架

```
         ┌──────────────────────────────┐
         │     制度执行维度（顶层）       │
         │  政策衔接 · 信息共享 · 内控   │
         ├──────────────────────────────┤
         │  基金管理维度               │
         │  预决算 · 结余 · 保值增值    │
    ┌────┴────────────┬──────────────┴────┐
    │  基金筹集维度    │   待遇支出维度    │
    │  征缴·参保·补助 │   发放·结算·审核  │
    └────┬────────────┴──────────────┬────┘
         │     业务经办维度（底层）     │
         │  认定·鉴定·配置·协议管理   │
         └──────────────────────────────┘
```

## 维度一：基金筹集

### 1.1 参保管理
| 风险点 | 检测方法 | 数据源 |
|:--|:--|:--|
| 重复参保（跨险种/跨地区） | 身份证+姓名跨系统关联比对 | 职工医保+居民医保参保表 |
| 应参未参（用人单位漏保） | 社保参保清单 vs 税务个税申报清单 | 社保系统 + 税务系统 |
| 虚构参保（空壳公司参保） | 单位参保人数 vs 个税申报人数 vs 工商状态 | 社保+税务+工商 |
| 死亡/服刑人员继续参保 | 参保表 vs 民政殡葬/司法数据 | 社保+民政+司法 |

### 1.2 征缴管理
| 风险点 | 检测方法 | 阈值 |
|:--|:--|:--:|
| 少缴漏缴（缴费基数不实） | 缴费基数 vs 个税申报工资 | 差异>20% 🔴 |
| 欠费累积（长期拖欠） | 按单位统计欠费时长+金额 | >12个月 🔴 |
| 征收机构截留/延迟上缴 | 征收日期 vs 入库日期 | >5个工作日 🟡 |
| 一次性补缴套利 | 补缴金额+时间窗口异常聚类 | 临退休前集中补缴 🔴 |

### 1.3 财政补助
| 风险点 | 检测方法 |
|:--|:--|
| 财政补助未足额拨付 | 应补金额 vs 实拨金额，按年度对比 |
| 重复参保导致财政多补助 | 重复参保人数 × 人均补助标准 |
| 补助资金被挪用 | 财政专户流水追踪 |

## 维度二：待遇支出

### 2.1 医疗保险支出（重灾区 ★★★）
| 序号 | 风险点 | 检测方法 | 数据源 |
|:--:|:--|:--|:--|
| 1 | **分解住院** | 同一患者出院后N天内同病种再入院 | 住院记录自关联 |
| 2 | **挂床住院** | 住院期间门诊有就诊记录/床位费占比异常 | 住院+门诊时间线 |
| 3 | **虚记诊疗项目** | 结算项目 vs 医院HIS实际执行记录 | 医保结算+HIS |
| 4 | **串换药品/耗材** | 进销存品种 vs 结算品种 比对 | 进销存+结算明细 |
| 5 | **过度诊疗（供给侧诱导需求）** | 同病种费用标准差异常（>3σ） | 按DRG分组统计 |
| 6 | **高编高套（DRG/DIP）** | 主诊断与次要诊断/手术编码逻辑不一致 | DRG分组+病历 |
| 7 | **重复收费/超标准收费** | 项目单价 vs 物价部门核定标准 | 结算清单+价格目录 |
| 8 | **药品回流（职业开药人）** | 药品追溯码重复出现/同一人跨院高频取药 | 追溯码+取药记录 |
| 9 | **敛卡套刷** | 同一卡短时间内跨机构刷卡 | 刷卡时间+GPS/机构编码 |
| 10 | **冲顶消费** | 年度累计费用在封顶线附近异常集中 | 按人按年累计 |

**泉州128模型核心方法**：
- `utl_match()` 模糊匹配药品名称 → 找出相似名称药品（串换线索）
- `OVER / PARTITION BY` 窗口函数 → 逐层累计分析
- `STDDEV` 标准差 → 同病种费用异常检测
- `INNER JOIN` 自连接 → 分解住院检测
- 移动加权平均价 → 药品价格异常

### 2.2 养老保险支出
| 风险点 | 检测方法 |
|:--|:--|
| 重复领取待遇 | 职工养老+居民养老待遇表跨系统关联 |
| 死亡冒领 | 待遇发放表 vs 殡葬数据 |
| 服刑期间领取 | 待遇表 vs 司法数据 |
| 提前退休骗领 | 退休审批年龄 vs 身份证年龄 |
| 待遇调整计算错误 | 自动重算比对 |

### 2.3 工伤保险支出
| 风险点 | 检测方法 |
|:--|:--|
| 工伤认定尺度不一致 | 同类情形不同区认定结果横向对比 |
| 非工伤疾病用药 | 外伤诊断 vs 慢性病/呼吸道用药 关联 |
| 辅助器具异常配置 | 刚满最低使用年限即按最高限价更换 |
| 辅助器具闲置 | 配置数量 vs 实际发放/使用记录 |
| 工伤医疗机构监管缺失 | 协议履行情况检查记录 |

### 2.4 失业保险支出
| 风险点 | 检测方法 |
|:--|:--|
| 虚构失业骗取 | 领取失业金期间有个税/社保缴纳记录 |
| 已就业继续领取 | 失业金表 vs 个税申报/新单位参保 |
| 稳岗补贴挪用 | 补贴用途 vs 实际资金去向 |

## 维度三：业务经办

### 3.1 定点医药机构协议管理
| 检查项 | 方法 |
|:--|:--|
| 准入合规性 | 定点机构资质审查文件完整性 |
| 协议履行监督 | 近年监督检查记录、处罚记录 |
| 退出机制执行 | 违规机构是否按规定退出 |
| 费用审核质量 | 经办机构审核拦截率、人工抽审比例 |

### 3.2 工伤认定/劳动能力鉴定
| 检查项 | 方法 |
|:--|:--|
| 认定口径一致性 | 同类型案件跨区/跨期认定结果对比 |
| 鉴定机构资质 | 鉴定机构、人员资质有效性 |
| 认定时限合规 | 从申请到认定的工作时限 |

### 3.3 待遇核定与支付
| 检查项 | 方法 |
|:--|:--|
| 待遇计算准确性 | 系统参数 vs 政策规定 |
| 支付时效 | 从核定到支付的时长 |
| 大额支付审批 | 大额/异常支付是否经多级审批 |

## 维度四：基金管理

### 4.1 预决算管理
| 风险点 | 检测方法 |
|:--|:--|
| 预算编制科学性不足 | 预算数 vs 实际执行数偏差率分析 |
| 预算执行约束力不足 | 各险种预算执行率横向对比 |
| 收支缺口持续扩大 | 近3-5年收支趋势分析 |
| 跨险种资金混用 | 各险种专户资金流水隔离性检查 |

### 4.2 基金结余与保值增值
| 风险点 | 检测方法 |
|:--|:--|
| 基金被挪用/侵占 | 基金专户银行流水追踪 |
| 结余资金闲置 | 活期占比过高→测算利息损失 |
| 保值增值方式违规 | 投资范围合规性检查（禁止股市/房地产等） |

### 4.3 基金安全
| 风险点 | 检测方法 |
|:--|:--|
| 经办机构违规收取费用 | 网络维护费/手续费等收入科目 |
| 个人账户资金违规提取 | 个人账户大额/频繁提取记录 |
| 药店套现/日用品刷卡 | 结算明细+药店铺货清单比对 |

## 维度五：制度执行

### 5.1 政策衔接
| 风险点 | 检测方法 |
|:--|:--|
| 跨地区转移接续障碍 | 转入转出数据比对 |
| 制度间重复保障 | 同一人享多种制度保障 |
| 封闭运行资金未整合 | 企业封闭运行动态排查 |

### 5.2 信息共享
| 风险点 | 检测方法 |
|:--|:--|
| 跨险种信息不共享 | 各险种系统数据互通测试 |
| 跨部门数据壁垒 | 社保/税务/民政/司法数据关联测试 |
| 系统数据质量 | 必填字段完整率、数据格式一致性 |

### 5.3 内控制度
| 检查项 | 方法 |
|:--|:--|
| 不相容岗位分离 | 审核/支付/记账是否分离 |
| 系统权限管理 | 超级管理员账号/敏感操作日志审查 |
| 风险预警机制 | 是否有事前提醒+事中审核+事后监管三道防线 |

---

## 数据分析模型集（20核心模型）

### M1: 重复参保检测
```sql
SELECT a.id_card, a.name, a.insurance_type AS type1, b.insurance_type AS type2
FROM insurance_a a
INNER JOIN insurance_b b ON a.id_card = b.id_card
WHERE a.insurance_type <> b.insurance_type;
```

### M2: 分解住院检测
```sql
SELECT a.patient_id, a.discharge_date, b.admission_date,
       b.admission_date - a.discharge_date AS gap_days
FROM inpatient a
INNER JOIN inpatient b ON a.patient_id = b.patient_id
WHERE a.discharge_date < b.admission_date
  AND b.admission_date - a.discharge_date <= 7
  AND a.primary_diagnosis = b.primary_diagnosis;
```

### M3: 死亡冒领检测
```sql
SELECT p.id_card, p.name, p.last_payment_date, d.death_date
FROM pension_payment p
INNER JOIN death_data d ON p.id_card = d.id_card
WHERE p.last_payment_date > d.death_date;
```

### M4: 同病种费用异常检测（STDDEV）
```sql
SELECT drg_code, patient_id, total_cost,
       AVG(total_cost) OVER (PARTITION BY drg_code) AS avg_cost,
       STDDEV(total_cost) OVER (PARTITION BY drg_code) AS std_cost
FROM medical_claims
WHERE total_cost > AVG(total_cost) OVER (PARTITION BY drg_code)
                 + 3 * STDDEV(total_cost) OVER (PARTITION BY drg_code);
```

### M5: 药品串换检测（模糊匹配）
```sql
SELECT a.drug_name AS settled_name, b.drug_name AS actual_name,
       UTL_MATCH.jaro_winkler(a.drug_name, b.drug_name) AS similarity
FROM settlement_detail a
CROSS JOIN pharmacy_inventory b
WHERE UTL_MATCH.jaro_winkler(a.drug_name, b.drug_name) > 0.85
  AND a.drug_name <> b.drug_name;
```

### M6: 敛卡套刷检测
```sql
SELECT card_id, institution_code, swipe_time,
       LAG(institution_code) OVER (PARTITION BY card_id ORDER BY swipe_time) AS prev_inst,
       LAG(swipe_time) OVER (PARTITION BY card_id ORDER BY swipe_time) AS prev_time,
       (swipe_time - LAG(swipe_time) OVER (PARTITION BY card_id ORDER BY swipe_time)) * 24 * 60 AS gap_minutes
FROM swipe_records
WHERE (swipe_time - LAG(swipe_time) OVER (PARTITION BY card_id ORDER BY swipe_time)) * 24 * 60 < 30
  AND institution_code <> LAG(institution_code) OVER (PARTITION BY card_id ORDER BY swipe_time);
```

### M7: 辅助器具异常配置
```sql
SELECT person_id, device_type, config_date, price,
       LAG(config_date) OVER (PARTITION BY person_id ORDER BY config_date) AS prev_date,
       (config_date - LAG(config_date) OVER (PARTITION BY person_id ORDER BY config_date)) AS days_gap,
       CASE WHEN (config_date - LAG(config_date) OVER (PARTITION BY person_id ORDER BY config_date)) <= 1826 -- 5年+1天
             AND price = (SELECT MAX(price) FROM device_prices WHERE type = device_type)
            THEN 'EXACT_MIN_YEAR_MAX_PRICE' ELSE 'NORMAL' END AS anomaly_flag
FROM assistive_device_records;
```

### M8: 单位缴费基数异常
```sql
SELECT company_id, insurance_base, tax_salary_base,
       ABS(insurance_base - tax_salary_base) / tax_salary_base AS deviation_rate
FROM (
    SELECT company_id, AVG(insurance_payment_base) AS insurance_base
    FROM insurance_contributions GROUP BY company_id
) a
JOIN (
    SELECT company_id, AVG(reported_salary) AS tax_salary_base
    FROM tax_records GROUP BY company_id
) b ON a.company_id = b.company_id
WHERE ABS(insurance_base - tax_salary_base) / tax_salary_base > 0.2;
```

### M9: 非工伤用药检测
```sql
SELECT w.person_id, w.injury_type, m.drug_name, m.drug_category, m.cost
FROM work_injury_info w
JOIN medical_settlement m ON w.person_id = m.person_id
WHERE w.injury_type LIKE '%外伤%'
  AND m.drug_category IN ('慢性病用药', '呼吸道用药')
  AND m.drug_name IN ('肺力咳合剂','蓝芩口服液','苏黄止咳胶囊','盐酸二甲双胍片','磷酸西格列汀片','硝苯地平控释片');
```

### M10: 冲顶消费检测
```sql
SELECT person_id, annual_total, cap_line,
       annual_total / cap_line AS usage_rate
FROM (
    SELECT person_id, SUM(cost) AS annual_total, 500000 AS cap_line
    FROM medical_claims
    WHERE YEAR(settlement_date) = 2025
    GROUP BY person_id
)
WHERE annual_total / cap_line > 0.95;
```

---

## 飞行检查15领域风险矩阵（★最新2026）

| 序号 | 领域 | 核心风险 | 高值特征 |
|:--:|:--|:--|:--|
| 1 | 骨科 | 脊柱手术耗材虚记、假体串换 | 耗材数万-十几万 |
| 2 | 心内科 | 支架/球囊/导管/起搏器虚记 | 高值耗材重灾区 |
| 3 | 血透 | 虚记透析次数、病人去世后仍收费 | 费用稳定可预期→易做手脚 |
| 4 | 口腔 | 种植牙串换、义齿超标准 | 自费转医保 |
| 5 | 眼科 | 白内障手术耗材串换 | 高值晶体 |
| 6 | 精神医学 | 挂床住院、虚记治疗项目 | 长期住院 |
| 7 | 康复医学 | 过度治疗、虚记康复次数 | 按次计费 |
| 8 | 肿瘤科 | 靶向药超适应症、超量开药 | 高值药品 |
| 9 | 检验检查 | 打包收费、虚记检查 | 大型设备 |
| 10 | 影像学 | AI辅助阅片实为人工、第三方无资质 | 服务外包 |
| 11 | 中医理疗 | 虚记针灸/推拿次数 | 按次计费 |
| 12 | 血液制品 | 白蛋白等滥用、串换 | 高值药品 |
| 13-15 | 定点药店(3类) | 刷卡套现、日用品串换、处方药无方销售 | 高频小额 |

---

## 审计发现分类与定性依据

### 违法违规类
| 问题类型 | 定性依据 | 处罚 |
|:--|:--|:--|
| 骗取医保基金 | 《医疗保障基金使用监督管理条例》第20条 | 退回+2-5倍罚款 |
| 分解住院/挂床住院 | 同条例第15条、第38条 | 退回+1-2倍罚款 |
| 过度诊疗/串换药品 | 同条例第15条、第38条 | 退回+1-2倍罚款 |
| 挪用社保基金 | 《社会保险法》第91条 | 追回+处分/刑责 |
| 重复参保套取 | 《社会保险法》+审计署2017-1号 | 退回+整改 |

### 管理不规范类
| 问题类型 | 表现 |
|:--|:--|
| 预算编制不科学 | 偏差率>20%，主要依赖主观估算 |
| 征缴不到位 | 欠费率>5%，缴费基数与实际不符 |
| 信息共享不畅 | 跨险种/跨部门数据壁垒 |
| 内控缺失 | 不相容岗位未分离，无三道防线 |

---

## 审计程序

### 第一阶段：数据采集与准备
1. 获取各险种参保/征缴/待遇支付全量数据
2. 获取定点医药机构协议及监督记录
3. 获取基金预决算报告及财务报表
4. 获取外部比对数据（税务/民政/司法/殡葬）
5. 数据清洗、标准化、关联建表

### 第二阶段：总体分析与疑点生成（大数据）
1. 运行20核心SQL模型 → 生成疑点清单
2. 按基金支出金额排序锁定Top 20机构
3. 按疑点类型分级（P0/P1/P2）
4. 绘制关系网络图（患者-医生-机构-药品）

### 第三阶段：现场核查
1. 飞检式突击检查（高值耗材科室优先）
2. 进销存实物盘点 vs 系统数据比对
3. 病历审阅（重点关注DRG高编高套）
4. 患者电话回访核实（住院真实性）

### 第四阶段：问题定性与报告
1. 疑点核实确认 → 问题归类
2. 法律法规条款匹配
3. 金额核算（直接损失+间接影响）
4. 整改建议（制度修复优先）

---

## 绩效导向（预算绩效管理视角）

| 绩效维度 | 指标 | 检测方法 |
|:--|:--|:--|
| 预算编制科学性 | 预算偏差率 | (决算-预算)/预算 |
| 征缴效率 | 征缴率 | 实缴/应缴 |
| 待遇发放及时性 | 平均审核天数 | 申请到支付间隔 |
| 基金可持续性 | 可支付月数 | 累计结余/月均支出 |
| 监管有效性 | 违规发生率 | 违规金额/总支出 |
| 信息共享覆盖度 | 系统互通率 | 已互通系统/应互通系统 |

---

## 输出物

| 文件 | 内容 |
|:--|:--|
| `社保基金审计模型_v1.md` | 本文件 |
| `sql_model_set.sql` | 20核心SQL模型 |
| `risk_matrix.xlsx` | 风险矩阵（概率×影响） |
| `疑点清单_自动生成.xlsx` | 自动生成的疑点清单 |
| `audit_procedures.py` | Python自动化分析脚本 |

---

## 维度六：刑事责任认定（★v1.1新增 — 法发2024-6号）

> 来源：最高人民法院 最高人民检察院 公安部《关于办理医保骗保刑事案件若干问题的指导意见》（法发〔2024〕6号，2024.2.28）

### 6.1 定罪标准矩阵

| 主体 | 行为类型 | 罪名 | 条文 |
|:--|:--|:--|:--|
| **定点医药机构** | ①诱导冒名就医 ②伪造变造资料 ③虚构服务 ④分解住院/挂床 ⑤重复收费/串换 ⑥串换药品 ⑦目录外纳入结算 | **诈骗罪** | 刑法第266条 |
| **个人** | ①伪造变造资料 ②冒名就医购药 ③虚构服务 ④重复享受待遇 ⑤转卖药品套现 ⑥其他 | **诈骗罪** | 刑法第266条 |
| **医保经办人员** | 利用职务便利骗取基金 | **贪污罪** | 刑法第382条 |
| **倒卖药品者** | 明知骗保购买药品而收购销售 | **掩饰隐瞒犯罪所得罪** | 刑法第312条 |
| **组织者/职业骗保人** | 组织指挥犯罪团伙 | **从重处罚** | 法发2024-6号第10条 |

### 6.2 四类从重情节（第10条）
1. 组织、指挥犯罪团伙骗取医保基金
2. 曾因医保骗保犯罪受过刑事追究
3. 拒不退赃退赔或者转移财产
4. 造成其他严重后果或恶劣社会影响

### 6.3 审计→刑事衔接关键条款

| 条款 | 内容 | 审计实践意义 |
|:--|:--|:--|
| **第15条** | 全面收集处方/病历等原始证据+核心证据材料 | 审计取证标准直接对标刑事证据要求 |
| **第18条** | 医保行政部门监督检查中收集的证据可直接作为定案根据 | **行政取证→刑事证据通道打通** |
| **第19条** | 可用银行流水/审计报告/医保系统数据等综合认定诈骗数额 | 审计报告可直接作为刑事证据 |
| **第12条** | 认罪认罚的医务人员可从宽处理 | 取证时可做政策宣讲，促进配合 |

### 6.4 全链条打击（第11条）
- 同步审查洗钱、侵犯公民个人信息等其他犯罪线索
- 深挖医保骗保犯罪背后的腐败和"保护伞"
- 结合扫黑除恶，识别骗保团伙中的黑恶势力

---

## 维度七：法规政策体系（六层法规范）

> 来源：融策知识库法规梳理

```
第一层：法律 — 《社会保险法》（2010/2018修正）
  ├─ 第78条：审计机关法定监督职责
  ├─ 第87条：机构骗保2-5倍罚款+吊销执业
  └─ 第94条：构成犯罪→刑事责任

第二层：行政法规 — 735号令《医保基金使用监管条例》（2021.5.1）
  ├─ 第15条：11项定点机构行为禁区
  ├─ 第38条：一般违规→退回+1-2倍罚款
  ├─ 第40条：骗保→退回+2-5倍罚款+暂停6-12月+解除协议
  └─ 第27条：可聘请会计师事务所协助检查（融策参与法定依据）

第三层：部门规章 — 医保局2号令/3号令（2021.2.1）
  ├─ 2号令：定点医疗机构准入6条件/考核/退出
  └─ 3号令：定点零售药店准入7条件/执业药师/信息对接

第四层：规范性文件
  ├─ 国办发〔2021〕2号：药品集采常态化（量价挂钩/医保预付30%）
  └─ 医保发〔2021〕48号：DRG/DIP三年行动计划（2024全覆盖）

第五层：刑事司法解释 — 法发〔2024〕6号
  └─ 医保骗保入刑操作手册（14类行为→刑法第266条/第382条/第312条）

第六层：审计实践 — 审计署2017-1号公告
  └─ 全国28省抽查3433亿/查实违规15.78亿/移送421起
```

---

## 新增数据分析模型（M21-M25）★v1.1

### M21: 药品购销闭环检测（知识图谱法）
```sql
-- 基于樊世昊知识图谱方法：构建"参保人→药品→药店→医师"闭环
-- 检测"职业开药人"模式：同一参保人→多机构→同药品→大量购买
SELECT 
    p.person_id,
    p.person_name,
    p.drug_name,
    COUNT(DISTINCT p.institution_code) AS institution_count,
    COUNT(DISTINCT p.doctor_id) AS doctor_count,
    SUM(p.quantity) AS total_quantity,
    SUM(p.cost) AS total_cost,
    -- 知识图谱关系密度指标
    COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT p.institution_code), 0) AS kg_density_score
FROM medical_settlement_detail p
WHERE p.drug_category IN ('慢性病用药', '靶向药', '抗肿瘤药')
  AND p.settlement_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
GROUP BY p.person_id, p.person_name, p.drug_name
HAVING COUNT(DISTINCT p.institution_code) >= 3  -- 跨≥3家机构
   AND SUM(p.quantity) > 60  -- 超量购买
ORDER BY kg_density_score DESC;
```

### M22: 医患合谋检测（供给方+需求方联动）
```sql
-- 基于李文艳方案：医生→患者→药店三方联动
-- 同一医师开出的处方→同一药店→高价药集中
SELECT 
    m.doctor_id,
    m.doctor_name,
    p.pharmacy_name,
    m.drug_name,
    COUNT(DISTINCT m.patient_id) AS patient_count,
    SUM(m.cost) AS total_cost,
    AVG(m.unit_price) AS avg_price,
    -- 检测该医师是否倾向于开高价药到特定药店
    PERCENT_RANK() OVER (PARTITION BY m.doctor_id ORDER BY AVG(m.unit_price)) AS price_percentile
FROM medical_settlement_detail m
JOIN pharmacy_transactions p ON m.patient_id = p.patient_id 
    AND m.drug_name = p.drug_name
    AND p.transaction_date BETWEEN m.settlement_date AND DATE_ADD(m.settlement_date, INTERVAL 1 DAY)
GROUP BY m.doctor_id, m.doctor_name, p.pharmacy_name, m.drug_name
HAVING COUNT(DISTINCT m.patient_id) >= 10
   AND AVG(m.unit_price) > (SELECT AVG(unit_price) * 1.5 FROM medical_settlement_detail WHERE drug_name = m.drug_name)
ORDER BY total_cost DESC;
```

### M23: 异地就医异常检测
```sql
-- 基于湖北大数据方案：跨地区就医反常模式
SELECT 
    person_id,
    person_name,
    registered_city,
    treatment_city,
    COUNT(*) AS visit_count,
    SUM(total_cost) AS total_cost,
    -- 异地就医频繁度 = 异地次数/总次数
    COUNT(*) * 1.0 / (
        SELECT COUNT(*) FROM medical_settlement_detail m2 
        WHERE m2.person_id = m.person_id
    ) AS remote_ratio
FROM medical_settlement_detail m
WHERE registered_city <> treatment_city
GROUP BY person_id, person_name, registered_city, treatment_city
HAVING COUNT(*) >= 5  -- 频繁异地
   AND SUM(total_cost) > 50000  -- 大额
ORDER BY remote_ratio DESC;
```

### M24: 药品价格异常波动（移动加权平均+集采对比）
```sql
-- 基于泉州模型移动加权平均法 + 集采价格基线
WITH weighted_avg AS (
    SELECT 
        drug_name,
        institution_code,
        settlement_date,
        unit_price,
        AVG(unit_price) OVER (
            PARTITION BY drug_name, institution_code 
            ORDER BY settlement_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS moving_avg_price
    FROM medical_settlement_detail
)
SELECT 
    drug_name,
    institution_code,
    settlement_date,
    unit_price,
    moving_avg_price,
    (unit_price - moving_avg_price) / NULLIF(moving_avg_price, 0) AS price_spike_pct,
    CASE 
        WHEN (unit_price - moving_avg_price) / NULLIF(moving_avg_price, 0) > 0.5 THEN '价格异常飙升'
        WHEN unit_price < moving_avg_price * 0.5 THEN '价格异常骤降（串换低价药）'
        ELSE '正常'
    END AS flag
FROM weighted_avg
WHERE moving_avg_price > 0
  AND ABS((unit_price - moving_avg_price) / moving_avg_price) > 0.3
ORDER BY price_spike_pct DESC;
```

### M25: 三医联动关联检测（医疗机构+医保+医药）
```sql
-- 跨部门数据关联：就诊记录↔医保结算↔药品进销存
SELECT 
    h.institution_name,
    h.doctor_name,
    COUNT(DISTINCT h.patient_id) AS patients,
    SUM(s.total_cost) AS billed_amount,
    SUM(i.purchase_cost) AS inventory_cost,
    -- 进销存金额 vs 结算金额 差额 = 虚记金额
    SUM(s.total_cost) - COALESCE(SUM(i.purchase_cost), 0) AS delta_amount,
    CASE 
        WHEN SUM(s.total_cost) > COALESCE(SUM(i.purchase_cost), 0) * 1.5 
        THEN '结算远超进销存→疑似虚记'
        ELSE '正常'
    END AS risk_flag
FROM his_execution_record h
JOIN medical_settlement_detail s ON h.patient_id = s.person_id 
    AND h.doctor_name = s.doctor_name
    AND h.execution_date = s.settlement_date
LEFT JOIN drug_inventory i ON h.institution_code = i.institution_code 
    AND s.drug_name = i.drug_name
    AND i.period = DATE_FORMAT(s.settlement_date, '%Y%m')
GROUP BY h.institution_name, h.doctor_name
HAVING SUM(s.total_cost) > COALESCE(SUM(i.purchase_cost), 0) * 1.5
ORDER BY delta_amount DESC;
```

---

## 知识图谱分析方法（★v1.1新增）

> 来源：樊世昊《基于知识图谱的审计方法研究——以医保审计为例》（南京审计大学硕士论文，2018）

### 图谱实体类型
| 实体 | 属性 | 关系连接 |
|:--|:--|:--|
| 参保人 | 身份证/姓名/参保类型/缴费基数 | →就诊→ 医疗机构 |
| 医疗机构 | 名称/等级/定点类型/协议状态 | →雇佣→ 医师 / →结算→ 医保基金 |
| 医师 | 姓名/科室/执业编号 | →处方→ 药品 / →诊疗→ 参保人 |
| 药品 | 名称/规格/集采类型/医保目录 | →被处方于→ 参保人 |
| 疾病 | ICD编码/DRG分组/名称 | →诊断为→ 参保人 |
| 费用 | 金额/类别/支付方式 | →关联→ 参保人+机构+药品 |

### 三大图谱检测场景

| 场景 | 图谱关系链 | 检测逻辑 | 对应SQL |
|:--|:--|:--|:--:|
| **应保未保** | 用人单位→应参保人员 | 个税申报人数 vs 社保参保人数关联 | M2 |
| **重复参保** | 参保人→职工医保+居民医保 | 同一实体同时连接两个保险节点 | M1 |
| **不合理用药** | 参保人→外伤诊断→慢性病用药 | 诊断类型与用药类型不匹配 | M14 |
| **职业开药人** | 参保人→多机构→同药品→大量 | 高密度多对多关系 | M21 |
| **医患合谋** | 医师→高价药→特定药店→患者 | 三方闭环关系 | M22 |

---

## Hadoop大数据技术方案（★v1.1新增）

> 来源：湖北省审计学会课题组《大数据技术在审计全覆盖中的应用研究——以湖北省医保审计实践为例》（《审计研究》2018年1期）

### 技术架构

| 层级 | 技术 | 用途 | 适用场景 |
|:--|:--|:--|:--|
| 基础设施 | **Hadoop集群** | 6台512G服务器集群化，处理能力3TB级 | 全量医保数据（6TB+） |
| 分布式存储 | **HDFS** | 104个地区数据分布式存储+多副本容错 | 多县市数据汇总 |
| 数据仓库 | **Hive + 达梦数据库** | ETL+SQL分析（Hive离线/达梦实时） | 23张标准表建库 |
| 计算引擎 | **MapReduce + 分布式SQL引擎** | 白天交互查询+夜间批量计算 | 95审计组并行分析 |
| 辅助工具 | 数据校验+表名翻译+结果切分 | 质量校验/中文SQL转换/一键分发 | 全流程提速 |

### 23张标准表设计

| 部门 | 标准表数 | 关键表 |
|:--|:--:|:--|
| 人社 | 12 | 参保人员/单位参保/职工征缴/居民缴费/医疗结算/工伤认定/生育待遇… |
| 卫计 | 5 | 住院记录/门诊记录/疾病诊断/手术记录/处方明细 |
| 民政 | 4 | 低保人员/殡葬登记/婚姻登记/残疾人员 |
| 公积金 | 2 | 缴存记录/提取记录 |

### 三类跨行业关联分析方法

| 方法 | 关联数据 | 检测目标 |
|:--|:--|:--|
| **跨部门关联** | 医保结算 + 殡葬数据 | 死亡后继续报销 |
| **跨行业关联** | 医保结算 + 地税个税 | 缴费基数不实 |
| **跨区域关联** | A市参保 + B市就医 | 异地就医骗保 |

---

## 大数据欺诈检测五步法（★v1.1新增）

> 来源：李文艳《基于大数据的医保欺诈行为审计方案设计》（《审计观察》2022年第13期）

### 五步审计流程

```
Step 1: 数据采集
  ├─ 结构化数据：参保/征缴/结算（SQL数据库）
  ├─ 半结构化：电子病历/处方（XML/JSON）
  └─ 非结构化：影像报告/发票图片（OCR处理）
       ↓
Step 2: 数据清洗
  ├─ 统一数据格式 → 标准化
  ├─ 去重/去噪/空值处理
  └─ 建立表索引→提高查询效率
       ↓
Step 3: 数据存储
  ├─ 小数据(<1TB)→关系数据库
  ├─ 大数据(≥1TB)→Hadoop HDFS
  └─ 保存存储过程→实现SQL复用与共享
       ↓
Step 4: 数据挖掘
  ├─ 聚类分析→发现异常群体
  ├─ 判别分析→分类欺诈/正常
  ├─ 主成分分析→降维找关键变量
  ├─ 频繁模式挖掘→发现高频欺诈组合
  └─ 信息熵量化→购药行为异常度
       ↓
Step 5: 疑点分发与跟踪
  ├─ 疑点分级分类（P0/P1/P2）
  ├─ 一键切分下发至各审计组
  └─ 建立疑点核实反馈→优化分析模型
```

### 三方欺诈行为矩阵

| 欺诈方 | 典型行为 | 检测算法 |
|:--|:--|:--|
| **医疗机构** | 重复收费、串换项目、过度服务、编造就诊记录 | 聚类+关联规则 |
| **参保人** | 一卡多用、过度消费、冒名就医 | 信息熵+频率分析 |
| **医患合谋** | 以物串药、人情处方、虚假住院 | 关系网络分析 |

---

## 若尔盖医保资金审计实战架构（★v1.1新增）

> 来源：融策审计黑板 `audit-blackboard/projects/若尔盖医保资金审计/`

### 7 Agent分工体系

| Agent | 职责 | 分析方法 |
|:--|:--|:--|
| **数据侦察兵** | 财务数据全量扫描：科目余额异常/长期挂账/凭证断号 | clean_journal + map_accounts |
| **合同猎犬** | 合同12项风险规则检测：缺验收条款/先付款后签合同 | contract_review |
| **招投标猎手** | 围标串标检测L1-L11：报价规律/文本雷同/图片哈希/元数据 | 投标文件.DOCX解压分析 |
| **法规检察官** | 法规对照+违规程度判定+具体条款号匹配 | 政策法规知识库检索 |
| **底稿工匠** | 汇总发现→取证单+工作底稿+问题汇总 | workpaper_archive |
| **报告笔杆子** | 15维度质量自检→审计报告初稿 | 交叉碰撞线索标★ |
| **复核哨兵** | 证据链穿通测试：报告→底稿→取证单→原始发现→原始数据 | 15维度交叉比对 |

### 审计规模参照（基于若尔盖）

| 指标 | 若尔盖估算 | 全国参照 |
|:--|:--|:--|
| 参保人口 | ~7万人 | - |
| 年医保支出 | ~5000万元 | - |
| 预期违规率 | 0.46% | 审计署2017全国基准 |
| 预估问题金额 | ~23万元 | - |
| 预期重复参保 | <385人 | 重复参保率0.55% |

---

## 参考资料

### 法规政策类
1. 《社会保险法》（2010/2018修正）— 第78条(审计监督)/87条(骗保处罚)/94条(刑事责任)
2. 《医疗保障基金使用监督管理条例》（国务院令第735号，2021.5.1）
3. 医保局2号令《医疗机构医疗保障定点管理暂行办法》
4. 医保局3号令《零售药店医疗保障定点管理暂行办法》
5. 国办发〔2021〕2号：药品集中带量采购常态化
6. 医保发〔2021〕48号：DRG/DIP支付方式改革三年行动计划
7. **法发〔2024〕6号**：两高+公安部《关于办理医保骗保刑事案件若干问题的指导意见》— ★v1.1新增

### 审计实践类
8. 审计署2017年第1号公告《医疗保险基金审计结果》（含若尔盖分析参照）
9. 泉州/晋江审计局《医疗保险基金使用风险隐患审计数据分析方法》（128模型）
10. 审计署昆明特派办《新时代大数据审计实践研究——以医疗保障基金审计为例》
11. 湖北省审计学会课题组《大数据技术在审计全覆盖中的应用研究——以湖北省医保审计实践为例》— ★v1.1新增

### 学术方法类
12. 樊世昊《基于知识图谱的审计方法研究——以医保审计为例》（南京审计大学，2018）— ★v1.1新增
13. 李文艳《基于大数据的医保欺诈行为审计方案设计》（《审计观察》2022年第13期）— ★v1.1新增

### 案例与制度分析类
14. 林朴真《医保基金飞行检查：15个重点领域背后的"薅羊毛"生态》
15. 董竞飞《工伤保险业务背后的基金安全风险》
16. 周莉萍等《以预算绩效管理为抓手优化社保基金管理路径探索》
17. 《医疗保障基金监督检查五年行动计划（2026—2030年）》

### 融策内部
18. 若尔盖医保资金审计7 Agent部署方案（audit-blackboard）
19. 医保审计法规政策体系梳理（knowledge/policies/医保/）
