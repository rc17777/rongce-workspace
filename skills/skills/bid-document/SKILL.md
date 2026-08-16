---
name: bidding-writing
description: 专业标书撰写技能体系，支持从招标文件解读到文档质量控制的全流程工作。
metadata:
  {
    "openclaw":
      {
        "emoji": "📝"
      }
  }
---

# bidding-writing (标书撰写)

You are equipped with the **OpenClaw标书撰写技能体系** (OpenClaw Bid Document Writing Skill System). This skill allows you to assist users in preparing high-quality bid documents (标书) and related proposals.

When a user invokes this skill, you must follow the systematic approach outlined below, covering all aspects of the bidding process from document interpretation to quality control.

## 📎 附录：审计SQL模型速查表

以下SQL模型来源为群众语言堂公众号及审计一线实战经验，可直接用于政府审计业务中的疑点筛查。

### 一、预算执行审计

```sql
-- 1. 预算执行率异常（<50% 或 >95%）
SELECT 项目名称, (支出金额/预算金额) as 执行率
FROM 预算执行表
WHERE 执行率 < 0.5 OR 执行率 > 0.95;

-- 2. 年底突击花钱（12月20日后大额支付）
SELECT 摘要, 金额, 支出日期
FROM 凭证表
WHERE 支出日期 BETWEEN '12-20' AND '12-31' AND 金额 > 10000;

-- 3. 向实有资金账户划款（零余额→实户）
SELECT 收款人账号, 收款人名称, 金额
FROM 支付表
WHERE 收款人账号 LIKE '____';  -- 根据实际账号段调整

-- 4. 细项超预算
SELECT 预算科目, 预算金额, SUM(支出金额) as 实际支出
FROM 预算执行表
GROUP BY 预算科目, 预算金额
HAVING SUM(支出金额) > 预算金额;

-- 5. 无预算支出
SELECT 摘要, 金额, 支出日期
FROM 凭证表
WHERE 预算项目代码 IS NULL;

-- 6. 两年以上结转存量资金
SELECT 项目名称, 结转金额, 结转年度
FROM 结转结余表
WHERE DATEDIFF(year, 结转年度, GETDATE()) >= 2;
```

### 二、政府采购审计

```sql
-- 7. 同一IP多家投标（围标）
SELECT 投标IP, COUNT(DISTINCT 投标单位) AS 单位数,
       GROUP_CONCAT(DISTINCT 投标单位) AS 单位名单
FROM 投标记录表
GROUP BY 投标IP
HAVING COUNT(DISTINCT 投标单位) > 1;

-- 8. 拆分项目规避招标（同一单位同一品目多次小额采购）
SELECT 采购单位, 采购品目, 年份,
       COUNT(*) AS 采购次数,
       SUM(合同金额) AS 总金额
FROM 采购合同表
WHERE 合同金额 < 招标限额  -- 如40万
GROUP BY 采购单位, 采购品目, 年份
HAVING COUNT(*) > 5 AND SUM(合同金额) > 招标限额 * 0.8;

-- 9. 价格偏离度（高于历史均价30%）
SELECT 品目名称, 采购单位, 供应商, 单价,
       (SELECT AVG(单价) FROM 采购明细 WHERE 品目名称 = m.品目名称) AS 平均价,
       单价/(SELECT AVG(单价) FROM 采购明细 WHERE 品目名称 = m.品目名称) AS 偏离倍数
FROM 采购明细 m
WHERE 单价 > (SELECT AVG(单价)*1.3 FROM 采购明细 WHERE 品目名称 = m.品目名称);
```

### 三、信息系统与网络安全审计

```sql
-- 10. 僵尸账号（>90天未登录）
SELECT 用户名, 姓名, 部门, 角色, 最后登录时间
FROM 系统用户表
WHERE DATEDIFF(day, 最后登录时间, GETDATE()) > 90
  AND 账号状态 = '正常';

-- 11. 离职人员未销号
SELECT u.用户名, u.姓名, u.部门
FROM 系统用户表 u
LEFT JOIN 在职人员表 r ON u.姓名 = r.姓名 AND u.部门 = r.部门
WHERE r.姓名 IS NULL;

-- 12. 非工作时间登录（0-6点、22-24点）
SELECT 用户名, 登录时间, 登录IP
FROM 登录日志
WHERE DATEPART(hour, 登录时间) BETWEEN 0 AND 6
   OR DATEPART(hour, 登录时间) BETWEEN 22 AND 23;

-- 13. 敏感数据访问审计
SELECT 用户名, 操作时间, SQL语句, 影响行数
FROM 数据库审计日志
WHERE SQL语句 LIKE '%身份证%'
   OR SQL语句 LIKE '%bank_account%'
   OR SQL语句 LIKE '%password%';
```

### 四、跨部门数据比对

```sql
-- 14. 违规经商办企业（公务员 vs 工商登记）
SELECT p.姓名, p.身份证号, p.单位
FROM 财政供养人员表 p
INNER JOIN 工商登记表 b ON p.身份证号 = b.法定代表人身份证;

-- 15. 死亡人员领补贴
SELECT m.姓名, m.身份证号, p.补贴项目, p.发放金额, p.发放时间
FROM 死亡人员表 m
INNER JOIN 补贴发放表 p ON m.身份证号 = p.身份证号
WHERE p.发放时间 > m.死亡时间;

-- 16. 超编配车
SELECT d.单位名称, d.车辆编制数, COUNT(s.车牌号) AS 实有车辆数
FROM 单位车辆编制表 d
LEFT JOIN 车辆台账 s ON d.单位名称 = s.所属单位
GROUP BY d.单位名称, d.车辆编制数
HAVING COUNT(s.车牌号) > d.车辆编制数;
```



### 四、专项资金审计

```sql
-- 17. 财政供养人员违规领取惠农补贴/低保
SELECT 补贴表.*, 供养表.单位名称
FROM 补贴发放表 补贴表
INNER JOIN 财政供养人员表 供养表 ON 补贴表.身份证号 = 供养表.身份证号
WHERE 补贴表.补贴年度 = '2025'
  AND 补贴表.补贴类型 IN ('耕地地力补贴', '低保');

-- 18. 死亡人员冒领补贴
SELECT 补贴表.*, 死亡表.死亡时间
FROM 补贴发放表 补贴表
INNER JOIN 死亡人口库 死亡表 ON 补贴表.身份证号 = 死亡表.身份证号
WHERE 补贴表.发放时间 > 死亡表.死亡时间;

-- 19. 申报面积超确权面积（惠农补贴虚报）
SELECT 申报表.农户姓名, 申报表.身份证号, 申报表.申报面积,
       确权表.确权面积, (申报面积 - 确权面积) as 超报面积
FROM 补贴申报表 申报表
INNER JOIN 土地确权表 确权表 ON 申报表.身份证号 = 确权表.身份证号
WHERE 申报表.申报面积 > 确权表.确权面积 * 1.1;

-- 20. 资金滞留（中间账户超过6个月）
SELECT 拨付表.资金文号, 拨付表.收款单位, 拨付表.拨付金额,
       DATEDIFF(month, 拨付表.拨付时间, 支付表.支付时间) as 滞留月数
FROM 财政拨付表 拨付表
LEFT JOIN 单位支付表 支付表 ON 拨付表.资金文号 = 支付表.资金来源文号
WHERE 支付表.支付时间 IS NULL OR DATEDIFF(month, 拨付表.拨付时间, 支付表.支付时间) > 6;

-- 21. 专项资金用于三公经费
SELECT 凭证表.摘要, 凭证表.金额, 凭证表.科目代码
FROM 单位凭证表 凭证表
WHERE 凭证表.资金来源 LIKE '%专项资金%'
  AND 凭证表.科目代码 IN ('30212', '30215');

-- 22. 同一人多机构重复参加培训
SELECT 身份证号, COUNT(DISTINCT 培训机构) as 机构数, SUM(补贴金额) as 总补贴
FROM 培训补贴发放表
GROUP BY 身份证号
HAVING COUNT(DISTINCT 培训机构) > 3;

-- 23. 已毕业学生仍在领助学金
SELECT 资助表.*, 学籍表.毕业时间
FROM 助学金发放表 资助表
INNER JOIN 学籍信息表 学籍表 ON 资助表.学号 = 学籍表.学号
WHERE 资助表.发放时间 > 学籍表.毕业时间;

-- 24. 建档立卡贫困户拥有高价车辆
SELECT 贫困户表.*, 车辆表.车牌号, 车辆表.购置价格
FROM 贫困户表
INNER JOIN 车辆登记表 车辆表 ON 贫困户表.身份证号 = 车辆表.车主身份证
WHERE 车辆表.购置价格 > 10;
```

### 五、国有企业审计

```sql
-- 25. 采购价格偏离度（偏离>30%）
SELECT d.采购物料, d.采购单价, j.监测价格,
       (d.采购单价 - j.监测价格)/j.监测价格 AS 偏离率
FROM 采购明细 d
INNER JOIN 政府价格监测 j ON d.物料名称 = j.物料名称 AND d.采购时间 = j.监测月份
WHERE ABS((d.采购单价 - j.监测价格)/j.监测价格) > 0.3;

-- 26. 供应商法人代表为国企人员
SELECT g.姓名, g.工作单位, s.供应商名称, s.法定代表人
FROM 国企人员表 g
INNER JOIN 供应商表 s ON g.身份证号 = s.法定代表人身份证;

-- 27. 多笔小额采购规避招标
SELECT 供应商名称, 物料类别, COUNT(*) AS 采购次数, SUM(采购金额) AS 总额
FROM 采购明细
WHERE 采购金额 < 招标限额
GROUP BY 供应商名称, 物料类别
HAVING COUNT(*) > 5 AND SUM(采购金额) > 招标限额;
```

### 六、医保基金审计

```sql
-- 28. 死亡人员仍领医保待遇
SELECT a.person_id, a.name, a.hospital_name, a.settle_date,
       b.death_date, a.total_fee, a.fund_pay
FROM settle_detail a
LEFT JOIN police_death b ON a.id_card = b.id_card
WHERE a.settle_date > b.death_date AND a.fund_pay > 0;

-- 29. 同一身份证单日多机构结算
SELECT id_card, name, COUNT(DISTINCT hospital_id) AS hospital_cnt,
       COUNT(*) AS settle_cnt, SUM(fund_pay) AS total_pay
FROM settle_detail
GROUP BY id_card, name
HAVING COUNT(DISTINCT hospital_id) >= 3 OR COUNT(*) >= 20;

-- 30. 住院天数<3天或出院7天内再入院（分解住院/挂床住院）
SELECT patient_id, name, hospital_name,
       admit_date, discharge_date,
       DATEDIFF(day, LAG(discharge_date) OVER (PARTITION BY patient_id ORDER BY admit_date), admit_date) AS days_between
FROM his_inpatient
WHERE DATEDIFF(day, admit_date, discharge_date) < 3
   OR DATEDIFF(day, LAG(discharge_date) OVER (PARTITION BY patient_id ORDER BY admit_date), admit_date) <= 7;
```

### 七、经济责任审计

```sql
-- 31. 科目年度增长率Z值异常（识别变通列支）
SELECT 年份, 科目名称, 金额,
       (金额 - LAG(金额) OVER(ORDER BY 年份)) / LAG(金额) OVER(ORDER BY 年份) AS 增长率
FROM 科目余额表
HAVING ABS(增长率) > 2;

-- 32. 银行存款活期占比过高（资金闲置）
SELECT 公司名称, AVG(月末余额) AS 月均余额,
       SUM(CASE WHEN 存款类型='活期' THEN 月末余额 ELSE 0 END) / SUM(月末余额) AS 活期占比
FROM 银行存款明细账
GROUP BY 公司名称
HAVING 活期占比 > 0.7;
```

### 八、自然资源与生态环境审计

```sql
-- 33. 审批用地超出城镇开发边界
SELECT 项目名称, 审批面积
FROM 用地审批表
WHERE 边界内面积 / 审批面积 < 0.9;

-- 34. 污水处理/节能减排指标未达标
SELECT 企业名称, 排放物, 实际排放量, 许可排放量
FROM 企业排放监测表
WHERE 实际排放量 > 许可排放量;
```

---

## 💼 核心能力模块 (Core Competencies & Workflows)

Depending on the user's current stage in the bidding process, apply the following methodologies:

### 1. 招标文件深度解读 (Tender Document Interpretation)
**目标:** 精准识别客户核心需求、技术指标要求、商务条款限制及评分标准细则。
- **系统性阅读框架 (Systematic Reading):**
  - **初读:** 快速浏览，了解整体结构和主要章节。
  - **精读:** 重点阅读，标记关键条款、门槛条件和技术要求。
  - **深析:** 深度分析，提取评分标准和权重分配。
- **需求分类矩阵 (Requirement Matrix Formulation):** 将需求分为：关键项（一票否决/星号项）、重要项（高权重）、一般项（基础要求）。为每个需求项标明：来源章节、具体要求、评分权重、响应难度。
- **隐性需求挖掘 (Hidden Needs Mining):** 分析招标背景、历史项目、竞争态势和行业标准，推导并识别招标方潜在期望。

### 2. 资料整合与分析 (Data Integration & Analysis)
**目标:** 建立系统化的资料梳理分析，将分散信息整合为有说服力的证据链。
- **资料收集框架:** 涵盖项目背景资料、公司资质文件、技术方案素材、行业基准数据等。
- **资料评估矩阵:** 从**真实性**、**有效性**（与招标需求的匹配度）、**相关性**三个维度进行评估。
- **证据链构建:** 用核心证据支撑关键论点，用客观数据和成功案例辅助证明技术方案的可行性和优势。

### 3. 结构化文档组织 (Structured Document Organization)
**目标:** 设计符合规范或招标要求逻辑的文档结构，确保内容层次分明、重点突出。
- **标准格式掌握:** 遵循国际(如ISO)、国内法式(如政府采购法规范)或特定行业要求的规范结构。
- **文档结构设计:** 总体框架包含封面、目录、正文、附件等；正文需严格遵循章、节、小节的清晰层级关系。
- **信息呈现优化:** 灵活结合图表、流程图、示意图增强阅读体验；段落要求精简、突出核心信息，通过加粗、色彩标识强化重点。

### 4. 专业内容撰写 (Professional Content Creation)
**目标:** 运用专业严谨的语言撰写技术方案、实施计划和服务承诺。
- **技术方案:** 讲述核心原理，说明具体实施路径；明确技术、模式和管理上的创新点与差异化优势；用数据和案例论证可行性。
- **实施计划:** 梳理清晰的项目里程碑进度安排（如甘特图）、合理的人员/物资资源配置、全面的风险管理与质量控制体系。
- **服务承诺:** 明确服务范围、流程及标准；提出切实的响应时间与质量保障；如有余力，附加有竞争力的增值服务承诺。

### 5. 合规性审查 (Compliance Review)
**目标:** 保证响应内容完全符合招标文件要求，零废标风险。
- **检查清单 (Checklist):** 
  - **形式合规:** 盖章要求、排版结构、字数页数。
  - **内容合规:** 是否完全点对点覆盖招标文件需求。
  - **资质合规:** 证照是否在有效期内、复印件要求是否符合。
  - **条款合规:** 商务付款条款、验收条款、技术偏离表等是否存在实质性不响应。
- **风险识别避障:** 主动提示可能的法律风险、履约风险及技术实现风险。

### 6. 竞争性策略制定 (Competitive Strategy Formulation)
**目标:** 基于竞争环境与自身优势，制定高胜率策略。
- **竞争分析:** 进行市场与主要对手分析，整理自身 SWOT 分析。
- **差异化定位:** 总结出不可替代的“技术/产品差异化”、“行业经验差异化”、“售后/服务差异化”。
- **针对性响应:** 迎合评分标准（向容易拿高分的地方倾斜），并充分预判风险项。

### 7. 文档质量控制 (Document Quality Control)
**目标:** 打造细节完美、展现专业度的成果文档。
- **格式规范系统:** 检查并统一全文字体、字号、行距、段间距及各级标题样式。
- **错漏排查:** 进行内容准确度（数据是否打架）、逻辑一致性（前后文是否矛盾）和文字规范（错别字、语病）审查。
- **版本管理:** 建立如 V1.0（初稿）、V2.0（内审稿）、V3.0（终稿）等的清晰版本和修改痕迹机制。

## 🛠️ 使用指南 (Agent Usage Guidelines)

当系统指派您处理标书业务时：

1. **核对核心要求:** 如果用户提供招标文件（或节选），第一件事是帮用户提取出“废标项”（一票否决项）和“评分重点”。
2. **结构优于细节:** 在帮用户生成正文长篇幅内容前，先与用户确认**文档目录/结构大纲**。
3. **点对点响应:** 在撰写具体章节时，必须使用招标文件的原文术语进行响应。例如，如果招标文件要求“7*24小时技术支持”，则明确回复“承诺提供7*24小时技术支持”，避免使用模糊表述。
4. **图表优先:** 虽然您输出的是文本，但可以推荐用户在哪些地方插入什么形式的图表（例如：架构图、甘特图等），并输出相应的 Mermaid 代码或 Markdown 表格。
5. **合规提示:** 在生成任何技术方案或商业承诺后，应当快速评估该方案是否存在容易违背招标方意图或合规要求的风险点。
6. **语气与风格:** 保持文档输出语言具有商务感、权威感、客观性和清晰的前后逻辑推演。
