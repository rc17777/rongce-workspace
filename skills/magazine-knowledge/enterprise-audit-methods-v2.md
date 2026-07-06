---
name: magazine-enterprise-audit
description: 企业审计方法库v2。从《审计案例》2026年3-5册企业审计文章提炼。触发：企业审计/国企审计/财务收支审计/SOE/国有资产/投资损失。
version: 2.0
source_articles:
  - "审计案例2026.3册：影子交易员——国企加油站利润流失之谜"
  - "审计案例2026.4册：不翼而飞的应收账款——以某集团收购上市公司造成重大损失为例"
  - "审计案例2026.4册：昂贵的数字摆设——投资2500万元的数字平台建成即废弃"
  - "审计案例2026.4册：高息融资现形记——国企融资成本审计"
  - "审计案例2026.5册：供应商管理存货背后隐藏的秘密——营收10亿利润1000万的异常"
---

# 企业审计方法库 v2

> 从《审计案例》2026年3-5册企业审计文章中提炼的可复用方法、SQL/Python模板、违规模式清单及融策业务匹配方案。

---

## 一、企业营收真实性审计

### 1.1 "影子交易员"——销售收入截留检测

**案例概要：** 某市属国企加油站，审计人员发现利润大幅低于行业均值，通过比对加油机原始数据与财务入账数据，揪出"影子交易员"——员工通过篡改系统数据将部分销售收入转入个人账户。

**核心方法：业务系统原始数据 vs 财务入账数据 全量比对**

```sql
-- 加油站业务-财务差异检测模板
WITH pump_raw AS (
    -- 加油机原始交易记录
    SELECT 
        station_id,
        pump_no,
        transaction_date,
        oil_type,
        SUM(liters) AS total_liters,
        SUM(amount) AS total_amount_raw,
        COUNT(*) AS transaction_count
    FROM pump_transaction_log
    WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'
    GROUP BY station_id, pump_no, transaction_date, oil_type
),
finance_booked AS (
    -- 财务入账收入
    SELECT 
        station_id,
        business_date,
        oil_type,
        SUM(revenue_amount) AS total_amount_booked,
        SUM(sales_volume) AS total_liters_booked
    FROM station_revenue_records
    WHERE business_date BETWEEN '2024-01-01' AND '2024-12-31'
    GROUP BY station_id, business_date, oil_type
)
SELECT 
    pr.station_id,
    pr.transaction_date,
    pr.oil_type,
    pr.total_amount_raw,
    COALESCE(fb.total_amount_booked, 0) AS total_amount_booked,
    pr.total_amount_raw - COALESCE(fb.total_amount_booked, 0) AS diff_amount,
    ROUND(
        (pr.total_amount_raw - COALESCE(fb.total_amount_booked, 0)) * 100.0 
        / NULLIF(pr.total_amount_raw, 0), 1
    ) AS diff_pct,
    pr.transaction_count,
    CASE 
        WHEN (pr.total_amount_raw - COALESCE(fb.total_amount_booked, 0)) 
             / NULLIF(pr.total_amount_raw, 0) > 0.03 
        THEN '⚠ 差异>3%需核查'
        WHEN (pr.total_amount_raw - COALESCE(fb.total_amount_booked, 0)) > 0
        THEN '存在差异'
        ELSE '一致'
    END AS alert_level
FROM pump_raw pr
LEFT JOIN finance_booked fb 
    ON pr.station_id = fb.station_id 
    AND pr.transaction_date = fb.business_date
    AND pr.oil_type = fb.oil_type
WHERE pr.total_amount_raw > 0
ORDER BY diff_amount DESC;
```

**异常模式识别清单：**

| 异常信号 | 现象 | 可能的舞弊手段 |
|---------|------|--------------|
| 单站利润骤降 | 某月利润率从15%降至3% | 收入被截留 |
| 系统日志缺失 | 特定时段无加油记录 | 系统被关闭或数据被删除 |
| 收款账户异常 | 频繁出现个人账户收款 | 公款私存 |
| 班次交接差异 | 交班金额与系统记录不符 | 当班人员截留 |
| 与非油品收入关联 | 便利店/洗车收入同时异常 | 系统性截留 |

### 1.2 营收-利润背离检测（VMI存货模式）

**案例概要：** Q贸易公司年营收10亿，利润仅1000万（利润率1%），但存货+应收账款总额超10亿，近3年累计退货超5亿。

**核心方法：财务报表横向对比 + 业务逻辑检验**

```python
"""
企业营收-利润-存货-应收账款 四维背离检测
检测逻辑：正常企业营收增长时利润应同步增长，存货和应收不应远超营收
"""
import pandas as pd
import numpy as np

def revenue_profit_divergence(df: pd.DataFrame) -> pd.DataFrame:
    """
    检测营收-利润背离模式
    
    Parameters:
    df: DataFrame with columns [year, revenue, profit, inventory, ar, 
         industry_avg_margin, industry_avg_turnover]
    """
    df = df.copy()
    
    # 1. 利润率异常检测
    df['profit_margin'] = df['profit'] / df['revenue']
    df['margin_vs_industry'] = df['profit_margin'] - df['industry_avg_margin']
    
    # 2. 存货周转天数（正常应<90天）
    df['inventory_turnover_days'] = 365 / (df['revenue'] / df['inventory'])
    
    # 3. 应收账款周转天数（正常应<60天）
    df['ar_turnover_days'] = 365 / (df['revenue'] / df['ar'])
    
    # 4. (存货+应收)/营收 比率（正常应<50%）
    df['inv_ar_to_revenue'] = (df['inventory'] + df['ar']) / df['revenue']
    
    # 5. 综合风险评分
    df['risk_score'] = 0
    df.loc[df['profit_margin'] < 0.02, 'risk_score'] += 3  # 利润率<2%
    df.loc[df['profit_margin'] < df['industry_avg_margin'] * 0.5, 'risk_score'] += 2
    df.loc[df['inventory_turnover_days'] > 180, 'risk_score'] += 3  # 存货>6个月
    df.loc[df['ar_turnover_days'] > 120, 'risk_score'] += 3  # 应收>4个月
    df.loc[df['inv_ar_to_revenue'] > 1.0, 'risk_score'] += 4  # (存货+应收)>营收
    
    # 6. 判定
    conditions = [
        df['risk_score'] >= 8,
        df['risk_score'] >= 5,
        df['risk_score'] >= 3,
        df['risk_score'] < 3
    ]
    choices = ['极高风险', '高风险', '关注', '正常']
    df['risk_level'] = np.select(conditions, choices, default='正常')
    
    return df[['year', 'revenue', 'profit', 'profit_margin', 'margin_vs_industry',
               'inventory_turnover_days', 'ar_turnover_days', 'inv_ar_to_revenue',
               'risk_score', 'risk_level']]

# 使用示例
# data = pd.DataFrame({...})
# result = revenue_profit_divergence(data)
# result.to_excel('营收利润背离分析.xlsx')
```

**VMI存货舞弊模式特征：**

| 特征 | 正常企业 | Q贸易公司（异常） | 舞弊可能 |
|------|---------|----------------|---------|
| 利润率 | 5-15% | 1% | 虚假交易做大营收 |
| 存货周转 | 30-90天 | >365天 | 存货虚构/已灭失 |
| 退货率 | <5% | >16% (5亿/30亿) | 虚假销售后以退货冲销 |
| (存货+应收)/营收 | <50% | >100% | 资金被占用或虚构 |
| 存货地点 | 自管仓库 | 外地供应商仓 | 无法盘点核实 |

---

## 二、投资损失审计

### 2.1 M&A投资损失责任认定

**案例概要：** B市国有独资C集团收购上市公司后短期内形成重大损失。

**审计判断框架：正常投资损失 vs 违规决策/失职渎职**

```
┌─────────────────────────────────────────────────────┐
│               投资损失责任认定四步法                     │
├─────────────────────────────────────────────────────┤
│  Step 1: 决策合规性                                   │
│  ├─ 是否经董事会/党委会集体决策？                       │
│  ├─ 是否进行了尽职调查（法律/财务/业务）？                │
│  ├─ 是否经上级主管部门审批/备案？                       │
│  └─ 是否存在"一言堂"或越权决策？                       │
├─────────────────────────────────────────────────────┤
│  Step 2: 交易公允性                                   │
│  ├─ 估值方法是否合理（收益法/市场法/资产基础法）？         │
│  ├─ 评估机构是否具备资质且独立？                        │
│  ├─ 交易价格 vs 评估值偏差是否在合理范围（±10%）？       │
│  └─ 是否存在抽屉协议或阴阳合同？                        │
├─────────────────────────────────────────────────────┤
│  Step 3: 尽调充分性                                   │
│  ├─ 标的公司财务数据是否经审计核实？                     │
│  ├─ 隐性负债（担保/诉讼/税务）是否充分揭示？              │
│  ├─ 核心技术/资产权属是否清晰？                         │
│  └─ 客户/供应商集中度是否评估？                         │
├─────────────────────────────────────────────────────┤
│  Step 4: 投后管理有效性                               │
│  ├─ 是否委派董事/监事/财务人员？                        │
│  ├─ 是否定期报告经营和财务状况？                        │
│  ├─ 业绩对赌条款是否触发并追偿？                        │
│  └─ 损失发现后是否及时止损？                            │
└─────────────────────────────────────────────────────┘
```

**SQL——投资损失追溯分析：**

```sql
-- 投资损失与决策责任人关联
WITH investment_loss AS (
    SELECT 
        i.investment_id,
        i.project_name,
        i.target_company,
        i.investment_amount,
        i.investment_date,
        i.current_value,
        i.current_value - i.investment_amount AS loss_amount,
        (i.current_value - i.investment_amount) / i.investment_amount AS loss_rate,
        i.decision_maker,
        i.approval_body
    FROM investments i
    WHERE i.status = '已退出' OR i.impairment_recognized = 1
),
decision_type AS (
    SELECT 
        investment_id,
        CASE 
            WHEN approval_body LIKE '%董事会%' AND committee_vote_passed = 1 
                 AND vote_against = 0 THEN '合规集体决策'
            WHEN approval_body NOT LIKE '%董事会%' AND approval_body NOT LIKE '%党委%' 
                 THEN '越权个人决策'
            WHEN committee_vote_passed = 0 THEN '集体否决仍执行'
            WHEN due_diligence_report IS NULL THEN '无尽职调查'
            WHEN third_party_valuation IS NULL THEN '无第三方评估'
            ELSE '程序瑕疵'
        END AS decision_type
    FROM investment_approval
)
SELECT 
    il.*,
    dt.decision_type,
    -- 金额分层
    CASE 
        WHEN il.loss_amount > 10000000 THEN '重大损失(>1000万)'
        WHEN il.loss_amount > 1000000 THEN '较大损失(>100万)'  
        WHEN il.loss_amount > 0 THEN '一般损失'
    END AS loss_level
FROM investment_loss il
LEFT JOIN decision_type dt ON il.investment_id = dt.investment_id
WHERE il.loss_amount > 0
ORDER BY il.loss_amount DESC;
```

### 2.2 数字化项目投资失败审计

**案例概要：** 某国企投资2500万元建设数字平台，建成后即废弃——虚假招投标、虚假列支工资、工程款套取。

**审计线索清单：**

| 阶段 | 应有标准 | 异常信号 | 审计取证方法 |
|------|---------|---------|------------|
| 立项 | 可研报告+专家评审 | 论证报告夸大前景、回避风险 | 对比同类项目投入产出 |
| 招标 | 公开招标/邀请招标 | 投标方均为关联企业、围标迹象 | 投标文件IP/MAC地址比对 |
| 开发 | 分阶段验收+里程碑付款 | 一次全额付款、验收走过场 | 验收报告 vs 实际系统功能 |
| 人员 | 实际到位技术人员 | 虚列开发人员工资 | 社保缴纳记录+个税申报 |
| 验收 | 第三方测试+用户试用 | 验收当天通过、无用户反馈 | 系统日志+访问量统计 |
| 运营 | 持续更新+用户增长 | 上线后再无更新、零用户 | 系统活跃度+内容更新记录 |

**Python——数字平台"建成即废弃"检测：**

```python
"""
数字化项目投资效益评估
检测指标：系统活跃度、内容更新频率、用户增长、运维投入合理性
"""
import pandas as pd
from datetime import datetime, timedelta

def assess_digital_platform_health(
    investment_amount: float,
    launch_date: str,
    system_logs: pd.DataFrame,
    user_data: pd.DataFrame,
    maintenance_costs: pd.DataFrame
) -> dict:
    """
    评估数字化平台投资效益
    
    返回：健康度评估报告
    """
    launch_dt = pd.to_datetime(launch_date)
    months_since_launch = (datetime.now() - launch_dt).days / 30
    
    # 1. 系统活跃度（从服务器日志）
    active_days = system_logs['log_date'].nunique()
    daily_avg_logins = system_logs.groupby('log_date')['user_id'].nunique().mean()
    content_updates = system_logs[system_logs['action'] == 'content_update']['log_date'].nunique()
    
    # 2. 用户增长
    if not user_data.empty:
        user_data['register_date'] = pd.to_datetime(user_data['register_date'])
        first_month_users = len(user_data[user_data['register_date'] <= launch_dt + timedelta(days=30)])
        latest_month_users = len(user_data[user_data['register_date'] >= datetime.now() - timedelta(days=30)])
        total_users = len(user_data)
        active_users_30d = len(user_data[user_data['last_login'] >= datetime.now() - timedelta(days=30)])
    else:
        first_month_users = latest_month_users = total_users = active_users_30d = 0
    
    # 3. 维护成本与投资额比值
    total_maintenance = maintenance_costs['cost_amount'].sum() if not maintenance_costs.empty else 0
    maintenance_to_investment = total_maintenance / investment_amount if investment_amount > 0 else 0
    
    # 4. 综合判定
    red_flags = []
    
    if daily_avg_logins < 5:
        red_flags.append(f'日均活跃用户仅{daily_avg_logins:.1f}人')
    if content_updates < months_since_launch * 0.5:
        red_flags.append('内容更新严重不足')
    if total_users < 100:
        red_flags.append(f'上线{months_since_launch:.0f}个月总用户仅{total_users}人')
    if active_users_30d == 0:
        red_flags.append('近30天零活跃用户')
    if maintenance_to_investment > 0.3:
        red_flags.append(f'运维投入占投资{maintenance_to_investment*100:.0f}%')
    
    # 投资每万元年均活跃用户
    annual_cost_per_active = (investment_amount / 10000) / max(active_users_30d, 1)
    
    return {
        'investment_amount': investment_amount,
        'months_since_launch': round(months_since_launch, 1),
        'daily_avg_logins': round(daily_avg_logins, 1),
        'content_updates_count': content_updates,
        'total_users': total_users,
        'active_users_30d': active_users_30d,
        'total_maintenance_cost': total_maintenance,
        'cost_per_active_user': round(annual_cost_per_active, 2),
        'health_status': '已废弃' if len(red_flags) >= 3 else (
            '濒临废弃' if len(red_flags) >= 2 else (
            '低效运行' if len(red_flags) >= 1 else '正常运行')),
        'red_flags': red_flags
    }
```

---

## 三、融资成本审计

### 3.1 高息融资检测方法

**案例概要：** 国企融资中存在的超基准利率融资、非正规渠道融资、融资顾问费异常等问题。

**SQL——融资成本偏离检测：**

```sql
-- 融资成本异常检测
WITH benchmark_rates AS (
    -- 同期LPR基准利率
    SELECT 
        rate_period,
        loan_term_type,
        lpr_1y,
        lpr_5y
    FROM lpr_benchmark
),
financing_detail AS (
    SELECT 
        f.financing_id,
        f.company_name,
        f.financing_type,       -- 银行贷款/信托/融资租赁/发债
        f.principal_amount,
        f.annual_rate,
        f.start_date,
        f.end_date,
        f.lender_name,
        f.intermediary_fee,     -- 融资顾问费/手续费
        f.actual_received,      -- 实际到账金额
        f.term_months,
        -- 计算实际年化成本（含费用）
        CASE 
            WHEN f.term_months > 0 AND f.actual_received > 0 
            THEN (f.principal_amount * f.annual_rate / 100 * f.term_months / 12 
                  + f.intermediary_fee) / f.actual_received * 12 / f.term_months * 100
            ELSE NULL
        END AS effective_annual_rate,
        -- 融资顾问费率
        f.intermediary_fee * 100.0 / NULLIF(f.principal_amount, 0) AS advisory_fee_pct
    FROM financing_records f
)
SELECT 
    fd.*,
    br.lpr_1y,
    br.lpr_5y,
    -- 与LPR偏离度
    CASE 
        WHEN fd.term_months <= 12 THEN fd.annual_rate - br.lpr_1y
        ELSE fd.annual_rate - br.lpr_5y
    END AS rate_spread,
    -- 综合判定
    CASE
        WHEN fd.effective_annual_rate > 
            (CASE WHEN fd.term_months <= 12 THEN br.lpr_1y ELSE br.lpr_5y END) * 2
            THEN '⚠ 实际成本超LPR 2倍'
        WHEN fd.advisory_fee_pct > 2 
            THEN '⚠ 顾问费率超2%'
        WHEN fd.actual_received < fd.principal_amount * 0.95
            THEN '⚠ 实际到账不足95%（砍头息）'
        ELSE '正常'
    END AS alert
FROM financing_detail fd
LEFT JOIN benchmark_rates br 
    ON fd.start_date BETWEEN br.rate_period - INTERVAL 3 MONTH AND br.rate_period + INTERVAL 3 MONTH
WHERE fd.effective_annual_rate IS NOT NULL
ORDER BY fd.effective_annual_rate DESC;
```

**高息融资典型违规模式：**

| 模式 | 表现 | 审计切入点 |
|------|------|-----------|
| 砍头息 | 借款1000万，实际到账950万 | 合同金额 vs 银行到账金额 |
| 融资顾问费 | 通过第三方咨询公司收取2-5%费用 | 顾问公司背景调查（是否关联/空壳） |
| 非标融资 | 融资租赁/信托利率远超银行贷款 | 是否有银行贷款渠道却不使用 |
| 存单质押 | 先用存款作质押再贷款，实质为担保 | 存单+贷款时间线比对 |
| 资金过桥 | 民间借贷高息过桥，再以银行贷款置换 | 还款资金来源追踪 |

---

## 四、违规模式分类清单

### 4.1 企业审计高频违规模式

| 编号 | 违规模式 | 表现特征 | 涉案金额级 | 审计切入点 |
|------|---------|---------|----------|-----------|
| QY-01 | 收入截留 | 业务系统数据与财务数据存在系统性差异 | 百万-千万 | 业务原始记录 vs 财务入账 |
| QY-02 | 虚假交易做大营收 | 营收高、利润低、退货多、存货应收高 | 亿级 | 四维背离分析 |
| QY-03 | VMI存货造假 | 存货存放在供应商仓库、无法盘点 | 亿级 | 函证+实地盘点 |
| QY-04 | 投资决策草率 | 无量可研/无评介/无集体决策 | 千万-亿 | 决策程序复核 |
| QY-05 | 虚假招投标 | 投标IP相同、围标串标、先定后招 | 百万-千万 | 投标文件技术分析 |
| QY-06 | 资金套取 | 虚假列支人员工资、虚增工程量 | 百万级 | 工资社保比对+现场核查 |
| QY-07 | 数字项目"晒太阳" | 建成即闲置、零用户、无更新 | 千万级 | 系统活跃度+访问日志 |
| QY-08 | 高息融资 | 实际融资成本超LPR 2倍+ | 百万-千万 | 有效利率计算+顾问公司审查 |
| QY-09 | 应收账款造假 | 大额应收长期挂账突然核销 | 亿级 | 账龄分析+客户函证 |
| QY-10 | 关联交易利益输送 | 与关联方交易价格明显偏离市场 | 百万-亿 | 关联方识别+公允价格比对 |

### 4.2 国有企业必查清单

**经营真实性：**
- [ ] 主营业务收入确认是否符合会计准则
- [ ] 是否存在虚构交易循环（贸易性融资）
- [ ] 存货盘点与账面是否一致（尤其异地存放存货）
- [ ] 应收账款账龄+坏账计提是否充分
- [ ] 大额退货/折让的合理性

**投资合规性：**
- [ ] 重大投资是否经"三重一大"决策程序
- [ ] 是否进行了尽职调查和第三方评估
- [ ] 投资后是否形成有效管控
- [ ] 投资损失是否追究责任

**融资审慎性：**
- [ ] 融资成本是否处于合理区间
- [ ] 是否通过非银行渠道高息融资
- [ ] 是否存在存单质押变相担保
- [ ] 融资中介费/顾问费的合理性

**资产安全性：**
- [ ] 固定资产权属是否清晰
- [ ] 无形资产（土地/专利/品牌）价值是否真实
- [ ] 对外担保是否失控
- [ ] 是否存在账外资产/小金库

**信息化项目效益：**
- [ ] 信息化投资是否达到预期效果
- [ ] 系统是否实际投入使用
- [ ] 运维投入与系统价值是否匹配

---

## 五、融策业务匹配方案

### 5.1 现有业务直接匹配

| 方法/模板 | 融策业务场景 | 应用建议 |
|----------|------------|---------|
| 业务-财务数据比对 | 国企审计/财务收支审计 | 适用于加油站、水务、公交等有业务系统的企业 |
| 四维背离分析 | 企业财务审计/尽职调查 | 快速识别虚假交易/营收造假 |
| 投资损失追溯 | 国企经责审计/资产清查 | 为责任认定提供量化依据 |
| 数字化项目效益评估 | 绩效评价/经责审计 | 信息化项目投资成效评价 |
| 融资成本偏离检测 | 国企审计/专项债审计 | 识别不合理融资成本 |
| VMI存货核查 | 企业审计/供应链审计 | 异地存货实质性程序 |

### 5.2 拓展业务方向

| 当前能力 | 可拓展业务 | 市场价值 |
|---------|----------|---------|
| 业务-财务比对模式 | 各类有业务系统的国企审计 | 差异化竞争力 |
| 数字化项目后评估 | 政府信息化项目绩效评价 | 新兴市场，竞争少 |
| 投资决策合规审计 | 国企投资决策专项审计 | 政企合规刚需 |
| 融资成本审计 | 城投/国企融资合规审计 | 高风险领域，收费可观 |

### 5.3 技术能力建设建议

1. **数据采集能力**——能对接加油站管理系统、ERP、OA、融资台账等各类企业系统
2. **Python数据分析能力**——掌握pandas+numpy进行财务异常检测
3. **系统日志分析能力**——从服务器日志/数据库日志还原业务真相
4. **函证+盘点流程**——针对VMI存货和应收账款的实质性程序

---

## 六、企业审计技术工具箱

### 6.1 数据比对类

```python
"""
通用业务-财务数据比对框架
适用场景：任何有独立业务系统的企业（加油站/水务/公交/物业/仓储）
"""
import pandas as pd

def biz_finance_reconciliation(
    biz_data: pd.DataFrame,
    finance_data: pd.DataFrame,
    biz_key_cols: list,
    finance_key_cols: list,
    biz_amount_col: str,
    finance_amount_col: str,
    tolerance_pct: float = 0.03
) -> pd.DataFrame:
    """
    业务系统与财务系统数据全量比对
    
    返回：差异明细表
    """
    # 按相同维度汇总
    biz_agg = biz_data.groupby(biz_key_cols)[biz_amount_col].sum().reset_index()
    fin_agg = finance_data.groupby(finance_key_cols)[finance_amount_col].sum().reset_index()
    
    # 全外连接
    merged = biz_agg.merge(
        fin_agg,
        left_on=biz_key_cols,
        right_on=finance_key_cols,
        how='outer',
        suffixes=('_biz', '_fin'),
        indicator=True
    )
    
    # 计算差异
    merged['biz_amount'] = merged[biz_amount_col + '_biz'].fillna(0)
    merged['fin_amount'] = merged[finance_amount_col + '_fin'].fillna(0)
    merged['diff'] = merged['biz_amount'] - merged['fin_amount']
    merged['diff_pct'] = (merged['diff'] / merged['biz_amount'].replace(0, np.nan) * 100).round(2)
    
    # 标记异常
    merged['alert'] = '正常'
    merged.loc[merged['_merge'] == 'left_only', 'alert'] = '⚠ 财务无记录（业务有）'
    merged.loc[merged['_merge'] == 'right_only', 'alert'] = '⚠ 业务无记录（财务有）'
    merged.loc[merged['diff_pct'].abs() > tolerance_pct * 100, 'alert'] = '⚠ 差异超阈值'
    
    return merged.sort_values('diff', key=abs, ascending=False)
```

### 6.2 供应商/客户集中度分析

```sql
-- 供应商/客户集中度及关联方识别
WITH supplier_stats AS (
    SELECT 
        company_name,
        supplier_name,
        SUM(purchase_amount) AS total_purchase,
        COUNT(*) AS transaction_count,
        AVG(purchase_amount) AS avg_transaction,
        -- 赫芬达尔指数（HHI）用于衡量集中度
        SUM(purchase_amount) * SUM(purchase_amount) / 
            (SELECT SUM(purchase_amount) FROM purchases p2 
             WHERE p2.company_name = p1.company_name) / 10000 AS supplier_HHI
    FROM purchases p1
    WHERE purchase_year = 2023
    GROUP BY company_name, supplier_name
),
company_totals AS (
    SELECT company_name, SUM(total_purchase) AS grand_total
    FROM supplier_stats
    GROUP BY company_name
)
SELECT 
    ss.company_name,
    ss.supplier_name,
    ss.total_purchase,
    ROUND(ss.total_purchase * 100.0 / ct.grand_total, 1) AS purchase_pct,
    ss.transaction_count,
    ss.avg_transaction,
    -- 单一供应商占比>50%为异常集中
    CASE 
        WHEN ss.total_purchase * 100.0 / ct.grand_total > 50 
        THEN '⚠ 单一供应商占比>50%'
        WHEN ss.total_purchase * 100.0 / ct.grand_total > 30 
        THEN '关注：占比>30%'
        ELSE '正常'
    END AS concentration_alert,
    -- 关联方检查（如供应商注册地址与被审计单位一致/相近）
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM related_parties rp 
            WHERE rp.company_name = ss.supplier_name
        ) THEN '⚠ 关联供应商'
        ELSE ''
    END AS related_party_flag
FROM supplier_stats ss
JOIN company_totals ct ON ss.company_name = ct.company_name
ORDER BY ss.total_purchase DESC;
```

---

## 附录：适用法规速查

| 法规 | 关键条款 | 适用场景 |
|------|---------|---------|
| 《企业国有资产法》 | 第30-38条（重大事项决策） | 投资/融资/处置决策 |
| 《企业国有产权转让管理暂行办法》 | 评估、进场交易 | 股权/资产转让 |
| 《关于进一步推进国有企业贯彻落实"三重一大"决策制度的意见》 | 决策范围+程序 | 决策合规性审计 |
| 《企业会计准则第8号——资产减值》 | 减值测试 | 投资损失确认 |
| 《政府采购法实施条例》第20条 | 以不合理条件限制供应商 | 招标合规 |
| LPR利率公告 | 贷款市场报价利率 | 融资成本基准 |
