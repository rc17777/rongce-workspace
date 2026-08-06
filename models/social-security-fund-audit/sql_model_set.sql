-- ============================================================
-- 社保基金审计 — 20核心SQL数据分析模型
-- 适用：MySQL/PostgreSQL（标注差异）
-- 基于：泉州128模型 + 审计署昆明特派办大数据审计实践
-- ============================================================

-- ==================== 维度一：基金筹集 ====================

-- M1: 重复参保检测（跨险种）
-- 检测同一人在不同险种系统中同时参保
SELECT 
    a.id_card,
    a.name,
    a.insurance_type AS type1,
    a.status AS status1,
    b.insurance_type AS type2,
    b.status AS status2
FROM insurance_participant a
INNER JOIN insurance_participant b 
    ON a.id_card = b.id_card 
    AND a.insurance_type < b.insurance_type  -- 避免自关联重复
WHERE a.status = '正常参保' 
  AND b.status = '正常参保';


-- M2: 应参未参检测（用人单位漏保）
-- 有税务个税申报但无社保参保记录
SELECT 
    t.company_id,
    t.company_name,
    t.employee_count AS tax_employee_count,
    COALESCE(s.employee_count, 0) AS insured_count,
    t.employee_count - COALESCE(s.employee_count, 0) AS uninsured_count,
    ROUND((t.employee_count - COALESCE(s.employee_count, 0)) * 1.0 / t.employee_count, 2) AS uninsured_rate
FROM tax_report_summary t
LEFT JOIN (
    SELECT company_id, COUNT(DISTINCT id_card) AS employee_count
    FROM insurance_participant
    WHERE status = '正常参保'
    GROUP BY company_id
) s ON t.company_id = s.company_id
WHERE t.employee_count - COALESCE(s.employee_count, 0) > 10  -- 差异>10人
  AND t.employee_count > 0
ORDER BY uninsured_count DESC;


-- M3: 缴费基数不实检测
-- 社保缴费基数 vs 税务申报工资对比
SELECT 
    ic.company_id,
    ic.company_name,
    ROUND(AVG(ic.payment_base), 2) AS avg_insurance_base,
    ROUND(AVG(tr.reported_salary), 2) AS avg_tax_salary,
    ROUND(ABS(AVG(ic.payment_base) - AVG(tr.reported_salary)) / AVG(tr.reported_salary), 3) AS deviation_rate,
    COUNT(DISTINCT ic.id_card) AS employee_count
FROM insurance_contributions ic
JOIN tax_records tr ON ic.id_card = tr.id_card 
    AND YEAR(ic.period) = YEAR(tr.period)
    AND MONTH(ic.period) = MONTH(tr.period)
WHERE ic.payment_base > 0 AND tr.reported_salary > 0
GROUP BY ic.company_id, ic.company_name
HAVING ABS(AVG(ic.payment_base) - AVG(tr.reported_salary)) / AVG(tr.reported_salary) > 0.2
ORDER BY deviation_rate DESC;


-- M4: 死亡/服刑人员继续参保
-- 参保表 vs 民政殡葬数据
SELECT 
    p.id_card,
    p.name,
    p.insurance_type,
    p.last_payment_date,
    d.death_date,
    DATEDIFF(p.last_payment_date, d.death_date) AS days_after_death
FROM insurance_participant p
INNER JOIN death_data d ON p.id_card = d.id_card
WHERE p.last_payment_date > d.death_date
  AND DATEDIFF(p.last_payment_date, d.death_date) > 30;


-- M5: 一次性补缴套利检测
-- 临退休前集中补缴
SELECT 
    id_card,
    name,
    company_id,
    payment_type,
    SUM(payment_amount) AS total_lump_sum,
    COUNT(*) AS payment_times,
    MIN(payment_date) AS first_date,
    MAX(payment_date) AS last_date
FROM insurance_contributions
WHERE payment_type = '一次性补缴'
GROUP BY id_card, name, company_id, payment_type
HAVING SUM(payment_amount) > 100000  -- 大额补缴
ORDER BY total_lump_sum DESC;


-- ==================== 维度二：待遇支出 ====================

-- M6: 分解住院检测（★核心模型）
-- 同一患者出院后7天内同病种再入院
SELECT 
    a.patient_id,
    a.patient_name,
    a.admission_date AS first_admission,
    a.discharge_date AS first_discharge,
    b.admission_date AS second_admission,
    DATEDIFF(b.admission_date, a.discharge_date) AS gap_days,
    a.primary_diagnosis,
    a.total_cost AS first_cost,
    b.total_cost AS second_cost,
    a.institution_name
FROM inpatient_record a
INNER JOIN inpatient_record b 
    ON a.patient_id = b.patient_id 
    AND a.discharge_date < b.admission_date
    AND DATEDIFF(b.admission_date, a.discharge_date) BETWEEN 0 AND 7
WHERE a.primary_diagnosis = b.primary_diagnosis
ORDER BY a.patient_id, a.discharge_date;


-- M7: 挂床住院检测
-- 住院期间在门诊有就诊记录
SELECT 
    ip.patient_id,
    ip.patient_name,
    ip.admission_date,
    ip.discharge_date,
    op.visit_date,
    op.department AS outpatient_dept,
    ip.department AS inpatient_dept,
    ip.total_cost
FROM inpatient_record ip
INNER JOIN outpatient_record op 
    ON ip.patient_id = op.patient_id
    AND op.visit_date BETWEEN ip.admission_date AND ip.discharge_date
WHERE ip.discharge_date > ip.admission_date  -- 正常住院
ORDER BY ip.institution_name, ip.patient_id;


-- M8: 同病种费用异常检测（STDDEV窗口函数 ★泉州模型）
SELECT 
    drg_code,
    patient_id,
    patient_name,
    institution_name,
    total_cost,
    ROUND(avg_cost, 2) AS drg_avg_cost,
    ROUND(std_cost, 2) AS drg_std_cost,
    ROUND((total_cost - avg_cost) / NULLIF(std_cost, 0), 2) AS z_score,
    CASE 
        WHEN std_cost > 0 AND (total_cost - avg_cost) / std_cost > 3 THEN 'HIGH_OUTLIER'
        WHEN std_cost > 0 AND (total_cost - avg_cost) / std_cost > 2 THEN 'ELEVATED'
        ELSE 'NORMAL'
    END AS anomaly_level
FROM (
    SELECT 
        drg_code,
        patient_id,
        patient_name,
        institution_name,
        total_cost,
        AVG(total_cost) OVER (PARTITION BY drg_code) AS avg_cost,
        STDDEV(total_cost) OVER (PARTITION BY drg_code) AS std_cost
    FROM medical_claims
    WHERE drg_code IS NOT NULL AND total_cost > 0
) sub
WHERE std_cost > 0 
  AND (total_cost - avg_cost) / NULLIF(std_cost, 0) > 2
ORDER BY z_score DESC;


-- M9: 药品串换检测（模糊匹配 ★泉州模型核心技术）
-- 结算药品名称 vs 进销存药品名称模糊匹配
-- MySQL: 使用 SOUNDEX + LEVENSHTEIN；PostgreSQL: pg_trgm + levenshtein()
-- 以下为简化版（精确名称对比 + 拼音编码近似）
SELECT 
    s.drug_name AS settled_drug_name,
    s.drug_code AS settled_code,
    i.drug_name AS inventory_drug_name,
    i.drug_code AS inventory_code,
    s.institution_name,
    SUM(s.quantity) AS total_quantity_settled,
    SUM(s.total_amount) AS total_amount,
    -- PostgreSQL: similarity(s.drug_name, i.drug_name) AS sim_score
    SOUNDEX(s.drug_name) AS settled_soundex,
    SOUNDEX(i.drug_name) AS inventory_soundex
FROM medical_settlement_detail s
LEFT JOIN drug_inventory i 
    ON s.institution_code = i.institution_code 
    AND s.drug_code = i.drug_code
    AND i.period = s.period
WHERE i.drug_name IS NULL  -- 结算药品在进销存中不存在
   OR s.drug_name <> i.drug_name  -- 名称不一致
GROUP BY s.drug_name, s.drug_code, i.drug_name, i.drug_code, s.institution_name,
         SOUNDEX(s.drug_name), SOUNDEX(i.drug_name)
HAVING SUM(s.total_amount) > 10000
ORDER BY total_amount DESC;


-- M10: 虚记诊疗项目检测
-- 结算项目 vs HIS实际执行记录比对
SELECT 
    s.institution_name,
    s.patient_id,
    s.item_code,
    s.item_name,
    SUM(s.quantity) AS settled_quantity,
    SUM(s.total_amount) AS settled_amount,
    COUNT(DISTINCT h.execution_id) AS his_execution_count
FROM medical_settlement_detail s
LEFT JOIN his_execution_record h 
    ON s.patient_id = h.patient_id 
    AND s.item_code = h.item_code
    AND h.execution_date = s.settlement_date
WHERE s.item_category IN ('检查', '检验', '治疗', '手术')
GROUP BY s.institution_name, s.patient_id, s.item_code, s.item_name
HAVING SUM(s.quantity) > COUNT(DISTINCT h.execution_id) * 1.5  -- 结算量远超HIS记录
ORDER BY settled_amount DESC;


-- M11: 死亡冒领养老金
SELECT 
    pp.id_card,
    pp.name,
    pp.last_payment_date,
    pp.monthly_amount,
    dd.death_date,
    TIMESTAMPDIFF(MONTH, dd.death_date, pp.last_payment_date) AS months_after_death,
    pp.monthly_amount * TIMESTAMPDIFF(MONTH, dd.death_date, pp.last_payment_date) AS estimated_overpayment
FROM pension_payment pp
INNER JOIN death_data dd ON pp.id_card = dd.id_card
WHERE pp.last_payment_date > dd.death_date
  AND TIMESTAMPDIFF(MONTH, dd.death_date, pp.last_payment_date) > 0
ORDER BY estimated_overpayment DESC;


-- M12: 重复领取养老金
SELECT 
    a.id_card,
    a.name,
    a.pension_type AS type1,
    a.monthly_amount AS amount1,
    b.pension_type AS type2,
    b.monthly_amount AS amount2,
    a.monthly_amount + b.monthly_amount AS total_monthly
FROM pension_payment a
INNER JOIN pension_payment b 
    ON a.id_card = b.id_card 
    AND a.pension_type < b.pension_type
WHERE a.last_payment_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
  AND b.last_payment_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH);


-- M13: 失业保险骗取检测（就业后继续领取）
SELECT 
    ub.id_card,
    ub.name,
    ub.benefit_start_date,
    ub.benefit_end_date,
    ub.monthly_amount,
    ic.company_name AS new_employer,
    ic.payment_date AS new_insurance_date
FROM unemployment_benefit ub
INNER JOIN insurance_contributions ic 
    ON ub.id_card = ic.id_card
    AND ic.payment_date BETWEEN ub.benefit_start_date AND ub.benefit_end_date
WHERE ic.payment_type = '正常缴纳'
ORDER BY ub.benefit_start_date DESC;


-- M14: 非工伤用药检测（工伤保险案例）
SELECT 
    wi.person_id,
    wi.name,
    wi.injury_type,
    wi.injury_date,
    ms.settlement_date,
    ms.drug_name,
    ms.drug_category,
    ms.quantity,
    ms.cost,
    ms.institution_name
FROM work_injury_info wi
INNER JOIN medical_settlement_detail ms 
    ON wi.person_id = ms.person_id
WHERE wi.injury_type LIKE '%外伤%'
  AND ms.drug_category IN ('慢性病用药', '呼吸系统用药', '感冒用药', '降压药', '降糖药')
  AND ms.drug_name IN (
      '肺力咳合剂', '蓝芩口服液', '苏黄止咳胶囊', '感冒清热颗粒',
      '盐酸二甲双胍片', '磷酸西格列汀片', '硝苯地平控释片',
      '氨氯地平片', '阿卡波糖片', '厄贝沙坦片'
  )
ORDER BY ms.cost DESC;


-- M15: 辅助器具异常配置（工伤保险案例）
SELECT 
    person_id,
    person_name,
    device_type,
    device_model,
    config_date,
    price,
    max_price,
    LAG(config_date) OVER (PARTITION BY person_id ORDER BY config_date) AS prev_config_date,
    DATEDIFF(config_date, LAG(config_date) OVER (PARTITION BY person_id ORDER BY config_date)) AS days_since_last,
    CASE 
        WHEN DATEDIFF(config_date, LAG(config_date) OVER (PARTITION BY person_id ORDER BY config_date)) <= 1830  -- 5年
         AND price = max_price
        THEN 'EXACT_MIN_YEAR_MAX_PRICE'
        WHEN DATEDIFF(config_date, LAG(config_date) OVER (PARTITION BY person_id ORDER BY config_date)) <= 1830
        THEN 'MIN_YEAR_TRIGGERED'
        ELSE 'NORMAL'
    END AS anomaly_flag
FROM (
    SELECT 
        a.person_id,
        a.person_name,
        a.device_type,
        a.device_model,
        a.config_date,
        a.price,
        b.max_price
    FROM assistive_device_records a
    JOIN (
        SELECT device_type, MAX(price) AS max_price
        FROM assistive_device_records
        GROUP BY device_type
    ) b ON a.device_type = b.device_type
) sub
ORDER BY anomaly_flag DESC, person_id, config_date;


-- M16: 冲顶消费检测
SELECT 
    person_id,
    person_name,
    insurance_type,
    SUM(total_cost) AS annual_total,
    cap_line,
    ROUND(SUM(total_cost) / cap_line * 100, 1) AS usage_pct,
    COUNT(DISTINCT institution_code) AS institution_count
FROM medical_claims
CROSS JOIN (
    SELECT 
        CASE 
            WHEN insurance_type = '职工医保' THEN 500000
            WHEN insurance_type = '居民医保' THEN 300000
            ELSE 500000
        END AS cap_line
    FROM DUAL
) caps
WHERE YEAR(settlement_date) = YEAR(CURDATE())
GROUP BY person_id, person_name, insurance_type, cap_line
HAVING SUM(total_cost) / cap_line > 0.9
ORDER BY usage_pct DESC;


-- M17: 敛卡套刷检测
-- 同一卡30分钟内跨机构刷卡
SELECT 
    card_id,
    institution_code,
    swipe_time,
    LAG(institution_code) OVER w AS prev_institution,
    LAG(swipe_time) OVER w AS prev_swipe_time,
    TIMESTAMPDIFF(MINUTE, LAG(swipe_time) OVER w, swipe_time) AS gap_minutes,
    amount
FROM swipe_records
WINDOW w AS (PARTITION BY card_id ORDER BY swipe_time)
WHERE TIMESTAMPDIFF(MINUTE, LAG(swipe_time) OVER w, swipe_time) < 30
  AND LAG(institution_code) OVER w IS NOT NULL
  AND institution_code <> LAG(institution_code) OVER w
ORDER BY card_id, swipe_time;


-- M18: 药店套现/日用品串换
-- 高频大额个人账户消费
SELECT 
    card_id,
    person_name,
    pharmacy_name,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount,
    AVG(amount) AS avg_amount,
    MAX(amount) AS max_single_amount
FROM pharmacy_transactions
WHERE transaction_type = '个人账户支付'
  AND settlement_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
GROUP BY card_id, person_name, pharmacy_name
HAVING COUNT(*) > 50  -- 高频
    OR AVG(amount) > 500  -- 大额
    OR MAX(amount) > 2000  -- 单笔超大
ORDER BY total_amount DESC;


-- ==================== 维度四：基金管理 ====================

-- M19: 基金可支付月数趋势
SELECT 
    period_year,
    period_month,
    insurance_type,
    cumulative_balance,
    monthly_expenditure,
    ROUND(cumulative_balance / NULLIF(monthly_expenditure, 0), 1) AS payable_months,
    LAG(ROUND(cumulative_balance / NULLIF(monthly_expenditure, 0), 1)) 
        OVER (PARTITION BY insurance_type ORDER BY period_year, period_month) AS prev_month_payable,
    ROUND(cumulative_balance / NULLIF(monthly_expenditure, 0), 1) - 
    LAG(ROUND(cumulative_balance / NULLIF(monthly_expenditure, 0), 1)) 
        OVER (PARTITION BY insurance_type ORDER BY period_year, period_month) AS change
FROM fund_balance_sheet
ORDER BY insurance_type, period_year, period_month;


-- M20: 预算执行偏差率
SELECT 
    insurance_type,
    budget_year,
    budget_amount,
    actual_amount,
    ROUND((actual_amount - budget_amount) / NULLIF(budget_amount, 0) * 100, 2) AS deviation_pct,
    CASE 
        WHEN ABS((actual_amount - budget_amount) / NULLIF(budget_amount, 0)) > 0.3 THEN '严重偏差'
        WHEN ABS((actual_amount - budget_amount) / NULLIF(budget_amount, 0)) > 0.15 THEN '较大偏差'
        WHEN ABS((actual_amount - budget_amount) / NULLIF(budget_amount, 0)) > 0.05 THEN '一般偏差'
        ELSE '正常'
    END AS deviation_level
FROM fund_budget_execution
ORDER BY ABS(deviation_pct) DESC;


-- ==================== ★v1.1新增模型 M21-M25 ====================

-- M21: 药品购销闭环检测（知识图谱法 — 樊世昊2018）
-- 检测"职业开药人"模式：跨多机构大量购买同种药品
SELECT 
    person_id,
    person_name,
    drug_name,
    COUNT(DISTINCT institution_code) AS institution_count,
    COUNT(DISTINCT doctor_id) AS doctor_count,
    SUM(quantity) AS total_quantity,
    SUM(cost) AS total_cost,
    COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT institution_code), 0) AS kg_density_score
FROM medical_settlement_detail
WHERE drug_category IN ('慢性病用药', '靶向药', '抗肿瘤药')
  AND settlement_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
GROUP BY person_id, person_name, drug_name
HAVING COUNT(DISTINCT institution_code) >= 3
   AND SUM(quantity) > 60
ORDER BY kg_density_score DESC;


-- M22: 医患合谋检测（供给方+需求方联动 — 李文艳2022）
-- 同一医师→高价药→特定药店→大量患者
SELECT 
    m.doctor_id,
    m.doctor_name,
    p.pharmacy_name,
    m.drug_name,
    COUNT(DISTINCT m.patient_id) AS patient_count,
    SUM(m.cost) AS total_cost,
    AVG(m.unit_price) AS avg_price,
    PERCENT_RANK() OVER (PARTITION BY m.doctor_id ORDER BY AVG(m.unit_price)) AS price_percentile
FROM medical_settlement_detail m
JOIN pharmacy_transactions p ON m.patient_id = p.patient_id 
    AND m.drug_name = p.drug_name
    AND p.transaction_date BETWEEN m.settlement_date AND DATE_ADD(m.settlement_date, INTERVAL 1 DAY)
GROUP BY m.doctor_id, m.doctor_name, p.pharmacy_name, m.drug_name
HAVING COUNT(DISTINCT m.patient_id) >= 10
   AND AVG(m.unit_price) > (
       SELECT AVG(unit_price) * 1.5 FROM medical_settlement_detail WHERE drug_name = m.drug_name
   )
ORDER BY total_cost DESC;


-- M23: 异地就医异常检测（湖北大数据方案 — 湖北省审计学会2018）
SELECT 
    person_id,
    person_name,
    registered_city,
    treatment_city,
    COUNT(*) AS visit_count,
    SUM(total_cost) AS total_cost,
    COUNT(*) * 1.0 / (
        SELECT COUNT(*) FROM medical_settlement_detail m2 
        WHERE m2.person_id = m.person_id
    ) AS remote_ratio
FROM medical_settlement_detail m
WHERE registered_city <> treatment_city
GROUP BY person_id, person_name, registered_city, treatment_city
HAVING COUNT(*) >= 5
   AND SUM(total_cost) > 50000
ORDER BY remote_ratio DESC;


-- M24: 药品价格异常波动（移动加权平均+集采对比 — 泉州模型扩展）
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


-- M25: 三医联动关联检测（医疗机构+医保+医药 — 湖北跨行业关联方法）
SELECT 
    h.institution_name,
    h.doctor_name,
    COUNT(DISTINCT h.patient_id) AS patients,
    SUM(s.total_cost) AS billed_amount,
    SUM(i.purchase_cost) AS inventory_cost,
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
