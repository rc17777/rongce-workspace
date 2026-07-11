---
name: "special-fund-audit"
description: >
  政府资金专项审计技能 — 融策12大业务线之「政府资金专项审计」。四类资金检测：社保资金/教育专项资金/民政救济资金/保障性住房资金。触发词：专项审计、专项资金、社保审计、教育审计、民政资金、保障性住房。
business_line: "专项资金审计"
methods: "核对法; 数据分析; 实地核查; 抽样审计"
difficulty: "中级"
keywords: "专项审计, 社保资金, 教育审计, 民政资金, 保障性住房, 惠农资金"
status: "reviewed"
---

# special-fund-audit — 政府资金专项审计

> 融策12大业务线之「政府资金专项审计」
> 支撑资料：按类型/民生审计28篇 + 审计案例17篇 + 审计案例专项17篇
> 覆盖：社保资金 / 教育专项 / 民政救济 / 保障性住房 / 医疗资金

## 触发条件
`专项审计` `专项资金` `社保审计` `教育审计` `民政资金` `保障性住房` `惠农资金`

## 四类资金检测

```
社保资金 ──→ 教育专项资金 ──→ 民政救济资金 ──→ 保障性住房资金
(dim1)       (dim2)            (dim3)            (dim4)
```

## 模块

### dim1 — 社保资金审计
- **检测**: 参保资格重复/死亡人员继续领取/缴费基数异常/待遇发放集中度
- **输入**: 参保清册.xlsx + 待遇发放表.xlsx
- **输出**: `social_security_anomalies.xlsx`

### dim2 — 教育专项资金
- **检测**: 营养餐(供应商集中/价格偏离)/助学补贴(申请人重复)/校建资金(进度vs拨付)
- **输入**: 教育专项资金台账.xlsx
- **输出**: `education_fund_anomalies.xlsx`

### dim3 — 民政救济资金
- **检测**: 低保(收入超标/车辆房产)/特困供养(资格不符)/临时救助(重复申请)
- **输入**: 民政救济发放表.xlsx + 车辆/房产/工商交叉数据
- **输出**: `civil_relief_anomalies.xlsx`

### dim4 — 保障性住房资金
- **检测**: 申请人资格(已有房产)/租金补贴(应缴vs实缴)/空置率
- **输入**: 保障房申请清册.xlsx + 房产登记交叉数据
- **输出**: `housing_fund_anomalies.xlsx`

## 使用方式

```bash
python dim1_social_security.py -i 参保清册.xlsx
python dim2_education.py -i 教育资金台账.xlsx
python dim3_civil_relief.py -r 救济发放表.xlsx -x 车辆数据.xlsx
python dim4_housing.py -i 保障房申请.xlsx -p 房产数据.xlsx
python run_all.py --data ./审计数据/
```
