import os, sys
sys.stdout.reconfigure(encoding='utf-8')

md = r'C:\Users\Admin\.openclaw\workspace\skills\audit-sql-patterns\SKILL.md'
with open(md, 'r', encoding='utf-8') as f:
    c = f.read()

section = """

---

## 实战案例库

### 案例1：基层法院经责审计SQL分析

> 来源：黄发斌、曾晶、洪云（湖北省荆州市审计局）
> 《基层法院领导干部经济责任审计数据分析方法》

#### 数据来源
- 综合信息管理平台 → 诉讼结案案件明细表
- 执行案件流程信息管理平台 → 执行结案案件明细表
- 法务综合管理平台 → 诉讼/执行案件收退费明细表

#### 分析1：无依据收取诉讼案件受理费
```sql
-- 筛选不应收费的案件类别
SELECT * FROM 诉讼结案案件明细
WHERE 案件文号 LIKE '%民申%'
   OR 案件文号 LIKE '%民监%'
   OR 案件文号 LIKE '%民特%'
   OR 结案方式 IN ('不予受理', '驳回起诉', '驳回上诉');

-- 关联收退费表，查出实际已收费的
SELECT a.*, b.确认的案件受理费
FROM 诉讼结案案件明细 a
LEFT JOIN 诉讼案件收退费明细 b ON a.案件文号 = b.案件文号
WHERE (a.案件文号 LIKE '%民申%' OR a.案件文号 LIKE '%民监%')
  AND b.确认的案件受理费 > 0;
```

#### 分析2：诉讼案件受理费收退费合理性
```sql
-- 按案由分类计算应收费用，与法官确认费用比对
-- 先分类：财产类/离婚类/侵权类
SELECT 案件文号, 立案标的, 案由,
  CASE
    WHEN 案由分类 = '财产类' AND 立案标的 <= 10000 THEN 50
    WHEN 案由分类 = '财产类' AND 立案标的 > 10000 AND 立案标的 <= 100000 THEN 立案标的 * 0.025 - 200
    WHEN 案由分类 = '财产类' AND 立案标的 > 100000 AND 立案标的 <= 200000 THEN 立案标的 * 0.02 + 300
    -- 其他金额区间省略...
    ELSE 0
  END AS 实际应交纳的案件受理费
INTO #审计中间表
FROM 诉讼结案案件明细;

-- 简易程序/调解/撤诉减半
UPDATE #审计中间表
SET 实际应交纳的案件受理费 = 实际应交纳的案件受理费 / 2
WHERE 适用程序 = '简易程序'
   OR 结案方式 IN ('调解', '申请撤诉');

-- 比对差异
SELECT a.*, b.确认的案件受理费,
  a.实际应交纳的案件受理费 - b.确认的案件受理费 AS 差异金额
FROM #审计中间表 a
JOIN 诉讼案件收退费明细 b ON a.案件文号 = b.案件文号
WHERE abs(a.实际应交纳的案件受理费 - b.确认的案件受理费) > 0.01;
```

#### 分析3：申请执行费应收未收/多收
```sql
-- 按执行到位标的计算应收申请执行费
SELECT 案件文号, 执行到位标的,
  CASE
    WHEN 执行到位标的 <= 10000 THEN 50
    WHEN 执行到位标的 > 10000 AND 执行到位标的 <= 500000 THEN 执行到位标的 * 0.015 - 100
    WHEN 执行到位标的 > 500000 THEN 执行到位标的 * 0.01 + 2400
    ELSE 0
  END AS 实际应交纳的申请执行费
INTO #执行费中间表
FROM 执行结案案件明细
WHERE 结案方式 IN ('执行完毕', '自动履行完毕');

-- 比对已收金额
SELECT a.*, b.已收的申请执行费,
  a.实际应交纳的申请执行费 - b.已收的申请执行费 AS 差异金额
FROM #执行费中间表 a
JOIN 执行案件收退费明细 b ON a.案件文号 = b.案件文号
WHERE abs(a.实际应交纳的申请执行费 - b.已收的申请执行费) > 0.01;
```

#### 分析4：审理/执行期限超期
```sql
-- 诉讼案件审理期限超期检测
SELECT 案件文号, 立案日期, 结案日期,
  DATEDIFF(day, 立案日期, 结案日期) AS 实际审理期限,
  CASE
    WHEN 案件文号 LIKE '%民初%' AND 适用程序 = '普通程序' THEN 180
    WHEN 案件文号 LIKE '%民初%' AND 适用程序 = '简易程序' THEN 90
    WHEN 案件文号 LIKE '%刑初%' AND 适用程序 = '普通程序' THEN 30
    WHEN 案件文号 LIKE '%刑初%' AND 适用程序 = '简易程序' THEN 15
    WHEN 案件文号 LIKE '%民特%' THEN 30
    ELSE 180
  END AS 法定审理期限
FROM 诉讼结案案件明细
WHERE DATEDIFF(day, 立案日期, 结案日期) >
  CASE
    WHEN 案件文号 LIKE '%民初%' AND 适用程序 = '普通程序' THEN 180
    WHEN 案件文号 LIKE '%民初%' AND 适用程序 = '简易程序' THEN 90
    WHEN 案件文号 LIKE '%刑初%' AND 适用程序 = '普通程序' THEN 30
    WHEN 案件文号 LIKE '%刑初%' AND 适用程序 = '简易程序' THEN 15
    WHEN 案件文号 LIKE '%民特%' THEN 30
    ELSE 180
  END;
```

#### 分析5：刑事案件罚没收入超期未执行
```sql
-- 查判决超过180天仍未执行到位的罚金
SELECT *, DATEDIFF(day, 结案日期, GETDATE()) AS 结案至今天数,
  (应收金额 - 实收金额) AS 未执行到位金额
FROM 刑事案件收费明细
WHERE 收取方式 = '本院依法收缴'
  AND 应收金额 > 实收金额
  AND DATEDIFF(day, 结案日期, GETDATE()) > 180;
```

#### 审计成效
- 替代传统翻阅案卷方式
- 快速精准发现法院在履行审判职能中的薄弱环节
- 实现以审促改，完善规章制度
"""

with open(md, 'w', encoding='utf-8') as f:
    f.write(c + section)

print(f'Done: {os.path.getsize(md)} chars')
