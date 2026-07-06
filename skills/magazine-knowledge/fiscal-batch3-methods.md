# 财政审计方法提取 — 第3批

> 来源：《中国审计》2026年第1期 / 《审计案例》2026年第1-2册
> 提取原则：只取可复用的方法步骤、SQL模板、违规模式。跳过政治表态与个人散文。

---

## 一、GIS+数据分析：院前急救资源配置审计

> 来源：运用地理信息和数据分析技术揭示院前急救资源配置不合理问题（中国审计 1期）

### 1.1 审计思路框架

| 阶段 | 步骤 | 数据来源 |
|------|------|----------|
| 需求分析 | 人口老龄化空间分布 → 急救需求热力图 | 卫健委人口数据、街道/乡镇人口结构 |
| 供给分析 | 急救站点/车辆空间分布 → 覆盖范围 | 急救中心站点坐标、车辆GPS数据 |
| 效率分析 | 接警→到达时间 → 响应达标率 | 120接警系统出车记录 |
| 缺口判定 | 需求 vs 供给叠加 → 盲区与过剩区 | GIS叠加分析图层 |

### 1.2 GIS分析关键指标

| 指标 | 计算方式 | 阈值参考 |
|------|----------|----------|
| 急救站点覆盖半径 | 以站点为圆心，计算覆盖人口 | 城区 ≤5km，郊区 ≤10km |
| 响应时间达标率 | 接警到到达 ≤15分钟的占比 | ≥95% |
| 万人救护车拥有量 | 救护车数 / 常住人口(万) | ≥1.5辆 |
| 盲区人口 | 未被任何站点5km覆盖的人口 | →0 |

### 1.3 可复用数据操作步骤

```
1. 获取急救站点经纬度（卫健委/急救中心）
2. 获取街道/乡镇人口数据（统计局）
3. GIS缓冲分析：以站点为圆心生成5km/10km缓冲区
4. 空间连接：缓冲区与人口网格叠加 → 覆盖人口
5. 计算各街道覆盖率 = 覆盖人口 / 总人口
6. 输出覆盖率 < 60% 的街道清单 → 审计疑点
```

### 1.4 典型违规模式

| 模式 | 表现 | 定性 |
|------|------|------|
| 资源分布失衡 | 城区站点密集、远郊空白 | 资源配置不合理 |
| 车辆闲置浪费 | 救护车采购后长期未投用 | 资产闲置 |
| 响应不达标 | 大量出车记录 >30分钟到达 | 服务效能低下 |
| 规划脱离需求 | 新建站点未考虑老龄化分布 | 规划决策不科学 |

---

## 二、多层次数据交叉验证：农商行快贷虚假资料审计

> 来源：运用多层次数据交叉验证技术审查农商行快贷业务虚假资料（中国审计 1期）

### 2.1 交叉验证层次模型

| 验证层 | 验证内容 | 数据源A | 数据源B | 验证逻辑 |
|--------|----------|---------|---------|----------|
| 第1层：身份真实性 | 借款人身份 | 贷款申请表(身份证号) | 公安户籍库 | 姓名-身份证号匹配 |
| 第2层：经营真实性 | 经营主体 | 贷款资料营业执照 | 市场监管局登记库 | 统一社会信用代码验证 |
| 第3层：经营状况 | 收入/流水 | 银行流水/财务报表 | 税务申报数据 | 收入-纳税匹配 |
| 第4层：关联关系 | 多人互保/共借 | 贷款关联人图谱 | 企业股权关系 | 关联方识别（一致行动人） |
| 第5层：资金用途 | 贷款资金去向 | 放款账户流水 | 受托支付对手方 | 资金是否回流/挪用 |

### 2.2 通用交叉验证矩阵（适用于各类审计）

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   验证维度    │   被审计方   │   第三方数据  │   差异判定    │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 主体资格      │ A单位申报材料 │ 工商/编办登记 │ 申报≠登记    │
│ 人员身份      │ A单位花名册   │ 社保/公积金   │ 在册≠参保    │
│ 资产权属      │ A单位资产台账 │ 不动产登记    │ 台账≠登记    │
│ 业务量        │ A单位业务系统 │ 行业监管平台  │ 系统≠平台    │
│ 资金量        │ A单位账簿     │ 银行对账单    │ 账簿≠银行    │
│ 纳税额        │ A单位纳税申报 │ 税务系统      │ 申报≠税务    │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### 2.3 快贷审计SQL模板

```sql
-- 模板1：身份证号逻辑校验
SELECT loan_id, borrower_name, id_number
FROM fast_loan_applications
WHERE LENGTH(id_number) != 18
   OR SUBSTR(id_number, 7, 4) NOT BETWEEN '1900' AND '2026'  -- 出生年份异常
   OR SUBSTR(id_number, 11, 2) NOT BETWEEN '01' AND '12'      -- 月份异常
   OR SUBSTR(id_number, 13, 2) NOT BETWEEN '01' AND '31';     -- 日期异常

-- 模板2：经营主体工商状态校验
SELECT a.loan_id, a.company_name, a.credit_code, b.status
FROM fast_loan_applications a
LEFT JOIN bureau_registry b ON a.credit_code = b.credit_code
WHERE b.credit_code IS NULL                    -- 工商不存在
   OR b.status IN ('吊销','注销','撤销');      -- 非正常状态

-- 模板3：流水与纳税收入交叉
SELECT a.loan_id, a.reported_income, b.tax_income,
       ROUND((a.reported_income - b.tax_income)/a.reported_income, 2) AS diff_pct
FROM fast_loan_applications a
JOIN tax_records b ON a.credit_code = b.credit_code
WHERE b.tax_year = YEAR(a.application_date)
  AND ABS(a.reported_income - b.tax_income) / a.reported_income > 0.3;  -- 偏离超过30%

-- 模板4：关联担保网络检测
SELECT a1.loan_id AS loan_1, a2.loan_id AS loan_2,
       a1.borrower_name, a2.guarantor_name, a2.borrower_name AS borrower_2
FROM fast_loan_applications a1
JOIN fast_loan_applications a2
  ON a1.borrower_name = a2.guarantor_name     -- A的借款人是B的担保人
WHERE a1.loan_id != a2.loan_id;
```

### 2.4 快贷虚假资料特征清单

| 特征类别 | 具体标志 | 风险等级 |
|----------|----------|----------|
| 身份异常 | 同一IP/设备提交多笔申请 | ★★★ |
| 收入虚高 | 流水收入与纳税收入偏离>50% | ★★★ |
| 经营存疑 | 营业执照注册时间<3个月 | ★★ |
| 关联密集 | 同一担保人为≥5人担保 | ★★★ |
| 资金回流 | 放款后资金返回借款人关联账户 | ★★★ |
| 集中用款 | 同一时段多笔贷款汇入同一账户 | ★★★ |
| 空壳嫌疑 | 注册地址与经营地址不一致 | ★★ |

---

## 三、经责审计发现方法：蹊跷签名引出的贪腐案

> 来源：蹊跷签名引出的贪腐案—民政局财务科长侵吞685万元（中国审计 1期）

### 3.1 审计发现路径（可复用步骤）

| 步骤 | 操作 | 本文对应手法 |
|------|------|-------------|
| 1. 初查凭证异常 | 抽查大额支出凭证，关注签字、附件 | 发现财务科长代签领导、审批不完整 |
| 2. 追踪资金去向 | 从付款凭证→银行流水→收款方 | 发现资金流向财务科长个人关联账户 |
| 3. 人员关系图谱 | 查收款方法人/股东与内部人员关系 | 发现收款企业为财务科长亲属控制 |
| 4. 核对业务真实性 | 付款事项→合同→验收→实物 | 虚构采购、虚假项目验收 |
| 5. 全周期穿透 | 扩面至全部年份、全部科目 | 累计查明侵吞685万元 |

### 3.2 经责审计"签字异常"检查清单

| 检查项 | 方法 | 疑点标志 |
|--------|------|----------|
| 签名字迹一致性 | 同一人名下签名字迹比对 | 明显不一致 → 代签 |
| 签字顺序 | 审批日期 vs 付款日期 | 审批晚于付款 → 事后补签 |
| 审批权限 | 审批人职务 vs 金额权限 | 越权审批 |
| 签章组合 | 同一凭证多人签字风格 | 同一笔迹签多人 → 一人多签 |
| 关键岗位签批密度 | 某岗位签批量占比统计 | 某财务岗位异常集中签批 |

### 3.3 资金追踪SQL

```sql
-- 从大额支付追踪到个人关联方
-- step1: 提取大额异常支付
SELECT voucher_no, pay_date, amount, payee_name, bank_account, summary
FROM payment_records
WHERE dept = '民政局'
  AND amount > 50000                                    -- 单笔超5万
  AND payee_type = '企业'                                -- 对公支付
  AND (summary LIKE '%采购%' OR summary LIKE '%服务%');  -- 采购服务类

-- step2: 关联收款方法人/股东信息（需导入工商数据）
SELECT p.*, b.legal_person, b.shareholder_names
FROM payment_records p
JOIN business_register b ON p.payee_name = b.company_name
WHERE p.dept = '民政局' AND p.amount > 50000;

-- step3: 匹配内部人员及其亲属（需导入人员亲属关系表）
SELECT DISTINCT p.payee_name, b.legal_person, e.name AS internal_person, e.position
FROM payment_records p
JOIN business_register b ON p.payee_name = b.company_name
JOIN employee_relations e ON b.legal_person = e.relative_name
   OR b.shareholder_names LIKE CONCAT('%', e.relative_name, '%');
```

### 3.4 侵吞公款典型手法

| 手法 | 操作方式 | 审计突破口 |
|------|----------|-----------|
| 虚构采购 | 编造采购合同→发票→付款→资金回流 | 实物盘点 + 供应商背景核查 |
| 伪造签字 | 模仿/代签领导审批 | 原始签批件笔迹比对 |
| 关联交易 | 资金流向亲属控制的企业 | 工商股东穿透 + 亲属关系 |
| 阴阳合同 | 合同金额与实际执行不符 | 合同比对 + 市场询价 |
| 拆分支付 | 大额拆分为多笔小额规避审批 | 按收款方汇总分析 |

---

## 四、SQL数据模型：污水处理费收缴审计

> 来源：运用SQL技术揭示污水处理费收缴管理中存在的典型问题（中国审计 1期）

### 4.1 污水处理费征收完整数据模型

```
核心数据表设计：
┌─────────────────────────────────────────────────────────┐
│  water_usage（自来水用量表）                              │
│  user_id | user_name | user_type | water_qty | period   │
├─────────────────────────────────────────────────────────┤
│  sewage_fee（污水费征收表）                                │
│  user_id | fee_period | water_qty_billed | fee_amount   │
├─────────────────────────────────────────────────────────┤
│  self_well（自备水源表）                                   │
│  well_id | user_id | water_qty_metered | period         │
├─────────────────────────────────────────────────────────┤
│  exemption（减免表）                                       │
│  user_id | exempt_period | exempt_type | exempt_qty     │
├─────────────────────────────────────────────────────────┤
│  user_register（用户登记表）                                │
│  user_id | user_name | user_type | address | status     │
└─────────────────────────────────────────────────────────┘
```

### 4.2 五大典型问题及SQL定位

#### 问题1：应征未征—用水但未缴污水费

```sql
-- 在自来水用量表中存在，但污水费征收表中缺失的用户
SELECT w.user_id, w.user_name, w.user_type,
       SUM(w.water_qty) AS total_water,
       w.period
FROM water_usage w
LEFT JOIN sewage_fee s
  ON w.user_id = s.user_id AND w.period = s.fee_period
WHERE s.user_id IS NULL
  AND w.water_qty > 0
  AND w.user_type IN ('企业','商业','机关')  -- 非居民用户
GROUP BY w.user_id, w.user_name, w.user_type, w.period
ORDER BY total_water DESC;
```

#### 问题2：少征—污水费计费水量 < 实际用水量

```sql
-- 计费水量与实际用水量差异
SELECT w.user_id, w.user_name,
       SUM(w.water_qty) AS actual_water,
       SUM(COALESCE(s.water_qty_billed, 0)) AS billed_water,
       SUM(w.water_qty) - SUM(COALESCE(s.water_qty_billed, 0)) AS diff,
       ROUND((SUM(w.water_qty) - SUM(COALESCE(s.water_qty_billed, 0))) / SUM(w.water_qty) * 100, 1) AS diff_pct
FROM water_usage w
LEFT JOIN sewage_fee s ON w.user_id = s.user_id AND w.period = s.fee_period
WHERE w.water_qty > 0
GROUP BY w.user_id, w.user_name
HAVING diff > 1000  -- 差异超1000吨
   AND diff_pct > 10  -- 差异超过10%
ORDER BY diff DESC;
```

#### 问题3：漏征—自备水源用户未纳入征收

```sql
-- 有自备井用水记录但无水费征收记录
SELECT w.user_id, w.user_name, SUM(w.water_qty_metered) AS well_water,
       COALESCE(s.total_fee, 0) AS sewage_fee_paid
FROM self_well w
LEFT JOIN (
    SELECT user_id, SUM(fee_amount) AS total_fee
    FROM sewage_fee
    GROUP BY user_id
) s ON w.user_id = s.user_id
WHERE s.user_id IS NULL OR s.total_fee = 0
GROUP BY w.user_id, w.user_name
ORDER BY well_water DESC;
```

#### 问题4：违规减免—不符合条件的用户享受减免

```sql
-- 减免用户类型分析
SELECT e.user_id, e.user_name, u.user_type,
       SUM(e.exempt_qty) AS exempt_water,
       SUM(e.exempt_qty * f.unit_price) AS exempt_amount
FROM exemption e
JOIN user_register u ON e.user_id = u.user_id
JOIN fee_standard f ON u.user_type = f.user_type
WHERE e.exempt_type != '政策减免'  -- 非政策性减免
   OR (e.exempt_type = '政策减免' AND u.user_type NOT IN ('低保户','社会福利'))
GROUP BY e.user_id, e.user_name, u.user_type
HAVING SUM(e.exempt_qty * f.unit_price) > 5000  -- 减免金额超5000
ORDER BY exempt_amount DESC;
```

#### 问题5：征收标准错误—单价执行有误

```sql
-- 实际征收单价与标准单价比对
SELECT s.user_id, u.user_name, u.user_type,
       s.fee_amount / NULLIF(s.water_qty_billed, 0) AS actual_price,
       f.unit_price AS standard_price,
       (s.fee_amount / NULLIF(s.water_qty_billed, 0) - f.unit_price) * s.water_qty_billed AS price_diff_amount
FROM sewage_fee s
JOIN user_register u ON s.user_id = u.user_id
JOIN fee_standard f ON u.user_type = f.user_type
WHERE ABS(s.fee_amount / NULLIF(s.water_qty_billed, 0) - f.unit_price) > 0.01
  AND s.water_qty_billed > 0
ORDER BY price_diff_amount DESC;
```

### 4.3 跨部门数据集合运算总表

| 审计目标 | 数据源1 | 数据源2 | 集合运算 | SQL关键操作 |
|----------|---------|---------|----------|-----------|
| 应征未征 | 自来水公司用水台账 | 污水费征收台账 | A - B（差集） | LEFT JOIN IS NULL |
| 少征漏征 | 用水量 | 计费水量 | 量差 > 阈值 | SUM差值 + HAVING |
| 自备水源遗漏 | 水利局取水许可 | 污水费征收台账 | A - B | LEFT JOIN IS NULL |
| 违规减免 | 减免台账 | 用户类型 | 资格交叉验证 | WHERE类型不符 |
| 标准差错 | 实际征收单价 | 物价核定标准 | 单价差 | 算术比较 |

---

## 五、粮食安全审计方法

> 来源：突出治理效能 保障粮食安全—F粮食储备公司资产负债损益审计（中国审计 1期）

### 5.1 粮食企业审计核心逻辑

```
"购销存"三环联动审计模型：

采购端 ────────→ 库存端 ────────→ 销售端
 ↓                  ↓               ↓
采购数量          账面库存         销售收入
采购价格          实物库存         轮换价差
采购来源          质量等级         出库流向
 │                  │               │
 └────── 三端交叉验证 ─────────────┘
     采购量 ≈ 销量 + 期末库存 - 期初库存
```

### 5.2 储备粮审计检查表

| 审计环节 | 检查项 | 方法 | 违规典型 |
|----------|--------|------|----------|
| **数量真实** | 账实是否相符 | 逐仓丈量 + 容重测算 | 粮仓空置、以少充多 |
| **质量良好** | 等级是否符合储备标准 | 抽样送检（水分/杂质/霉变） | 以次充好、陈粮充新粮 |
| **轮换规范** | 轮换时间/数量/价差 | 购销合同+入库单+出库单三单比对 | 虚假轮换、空转套利 |
| **资金安全** | 收购资金是否专款专用 | 农发行贷款→收购凭证逐笔追踪 | 挪用购粮款 |
| **费用真实** | 保管费用是否虚列 | 人员工资↔花名册↔考勤 | 虚列保管人员吃空饷 |

### 5.3 粮库实物核查速算公式

```
理论库存量(t) = 仓房体积(m³) × 容重(t/m³) × 装粮高度系数
                ↓
实际库存量(t) = Σ(逐仓测量体积 × 实测容重)
                ↓
差额 = 实际库存量 - 账面库存量
      差额 > 3% → 严重问题

注：
- 小麦容重 0.75-0.79 t/m³
- 稻谷容重 0.55-0.60 t/m³
- 玉米容重 0.70-0.75 t/m³
- 装粮高度系数 = 实际装粮高度 / 仓房设计高度
```

### 5.4 粮食审计SQL关键查询

```sql
-- 1. 购销存平衡验证
SELECT grain_type,
       SUM(purchase_qty) AS total_in,
       SUM(sales_qty) AS total_out,
       (SUM(purchase_qty) - SUM(sales_qty)) AS theoretical_stock,
       MAX(ending_stock) AS book_stock,
       (SUM(purchase_qty) - SUM(sales_qty)) - MAX(ending_stock) AS gap
FROM grain_transactions
WHERE trans_year BETWEEN 2006 AND 2021
GROUP BY grain_type
HAVING ABS(gap) > 100;  -- 差异超100吨

-- 2. 轮换价差异常检测
SELECT grain_type, rotation_batch,
       purchase_date, purchase_price,
       sales_date, sales_price,
       (sales_price - purchase_price) AS spread,
       (sales_price - purchase_price) / purchase_price AS spread_pct
FROM grain_rotations
WHERE ABS((sales_price - purchase_price) / purchase_price) > 0.15;  -- 价差超15%

-- 3. 保管费用异常
SELECT year_month, warehouse_id,
       COUNT(DISTINCT staff_id) AS staff_count,
       SUM(salary_amount) AS total_salary,
       SUM(storage_fee) AS total_storage_fee,
       SUM(storage_fee) / NULLIF(SUM(book_inventory_qty), 0) AS fee_per_ton
FROM grain_storage_costs
GROUP BY year_month, warehouse_id
HAVING fee_per_ton > (SELECT AVG(fee_per_ton) * 2 FROM ...);  -- 超均值2倍
```

### 5.5 "空库"与"转圈粮"识别方法

| 违规类型 | 操作手法 | 识别方法 |
|----------|----------|----------|
| **空库** | 账面有粮、仓内无粮 | ①突击实物盘点 ②查看粮温监测（空仓无粮温数据）③粮情测控系统日志 |
| **转圈粮** | 同一批粮反复出入库充轮换 | ①出库→入库时间间隔<15天 ②出库车辆与入库车辆GPS轨迹重合 ③出入库质检报告关键指标（容重/水分）一致 |
| **以陈顶新** | 旧粮当新粮入库 | ①脂肪酸值/KOH值检测 ②入库时间与粮情曲线匹配（新粮入仓应有升温期） |
| **虚假收购** | 伪造收购凭证套取资金 | ①售粮人身份证号查重 ②磅单与入库单时间逻辑矛盾 ③售粮人电话回访 |

---

## 六、补充：SQL+Python固定资产投资审计模型

> 来源：运用SQL、Python技术构建固定资产投资项目管理数据分析模型（中国审计 1期）

### 6.1 项目全生命周期数据表结构

```
项目库表（project_base）
├── project_id, project_name, invest_type, total_budget
├── plan_start, plan_end, dept, district

预算执行表（budget_exec）
├── project_id, budget_year, budget_amount, actual_pay

招标采购表（bidding）
├── project_id, bid_section, bid_type, win_company, win_amount

合同表（contracts）
├── contract_id, project_id, contractor, contract_amount, sign_date

支付表（payments）
├── pay_id, contract_id, amount, pay_date, payee

竣工验收表（completion）
├── project_id, actual_complete_date, final_account_amount
```

### 6.2 关键联查SQL

```sql
-- 1. 预算执行偏离度
SELECT p.project_id, p.project_name, p.total_budget,
       COALESCE(SUM(b.actual_pay), 0) AS total_paid,
       ROUND(COALESCE(SUM(b.actual_pay), 0) / p.total_budget * 100, 1) AS exec_rate
FROM project_base p
LEFT JOIN budget_exec b ON p.project_id = b.project_id
WHERE p.plan_end < CURRENT_DATE
GROUP BY p.project_id, p.project_name, p.total_budget
HAVING exec_rate < 30 OR exec_rate > 120  -- 执行率异常
ORDER BY exec_rate;

-- 2. 未招标先施工
SELECT p.project_id, p.project_name, b.bid_date, c.sign_date
FROM project_base p
JOIN bidding b ON p.project_id = b.project_id
JOIN contracts c ON b.project_id = c.project_id
WHERE c.sign_date < b.bid_date
   OR (b.bid_date IS NULL AND c.sign_date IS NOT NULL);

-- 3. 超概严重
SELECT p.project_id, p.project_name, p.total_budget,
       SUM(c.contract_amount) AS total_contract,
       SUM(c.contract_amount) / p.total_budget - 1 AS overrun_pct
FROM project_base p
JOIN contracts c ON p.project_id = c.project_id
GROUP BY p.project_id, p.project_name, p.total_budget
HAVING SUM(c.contract_amount) / p.total_budget > 1.3;  -- 超概30%以上
```

---

## 七、综合适用场景

| 方法模块 | 融策适用业务 | 匹配度 |
|----------|-------------|--------|
| GIS空间分析 | 绩效评价（公共服务配置）、资产清查（分布合理性） | ★★★★★ |
| 多层次交叉验证 | 经责审计、预算执行审计、专项审计调查 | ★★★★★ |
| 经责签字/资金追踪 | 经责审计、财务收支审计 | ★★★★★ |
| 污水处理费SQL模型 | 专项审计调查、绩效评价（专项资金） | ★★★★ |
| 粮食审计方法 | 资产清查、经责审计（国企） | ★★★★ |
| 固定资产投资SQL | 工程结算、财政评审、全过程咨询 | ★★★★★ |

---

## 八、通用审计数据采集清单（可直接用于审计通知书附件）

| 序号 | 数据项 | 来源部门 | 数据格式 | 适用方法 |
|------|--------|----------|----------|----------|
| 1 | 被审计单位在职人员名册 | 被审计单位 | Excel/CSV | 交叉验证 |
| 2 | 财政国库集中支付明细 | 财政局国库科 | CSV | SQL分析 |
| 3 | 工商登记信息（含股东） | 市场监管局 | Excel | 关联关系穿透 |
| 4 | 社保缴纳记录 | 人社局 | CSV | 人员真实性验证 |
| 5 | 税务申报数据 | 税务局 | CSV | 收入真实性验证 |
| 6 | 自然资源/地理信息数据 | 自然资源局 | Shapefile | GIS分析 |
| 7 | 银行账户流水 | 被审计单位开户行 | CSV | 资金追踪 |
| 8 | 招投标平台数据 | 公共资源交易中心 | Excel/CSV | 采购合规审查 |
| 9 | 业务系统导出台账 | 被审计单位 | Excel/CSV | 主数据源 |
| 10 | 身份证户籍信息 | 公安局（限申请） | CSV | 身份核验 |
