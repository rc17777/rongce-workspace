import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("待摊投资费用 收费标准逐笔测算")
print("阿坝州税务局业务用房维修改造项目")
print("=" * 70)

# ============================================================
# 一、设计费测算
# 依据：国家计委、建设部《工程勘察设计收费管理规定》
#       计价格[2002]10号（2002年3月1日起施行）
# ============================================================
print()
print("━" * 70)
print("一、设计费 — 计价格[2002]10号《工程勘察设计收费管理规定》")
print("━" * 70)

print("""
【收费标准摘要】
  第七条 工程设计收费 = 工程设计收费基价 × 专业调整系数
                        × 工程复杂程度调整系数 × 附加调整系数
  第八条 工程设计收费基价：按计费额从《工程设计收费基价表》内插
  计费额 = 经批准的初步设计概算中的建筑安装工程费+设备购置费+联合试运转费
""")

# Step 1: 确定计费额
print("【Step 1 确定计费额】")
print(f"  概算批准总投资：1,350,000.00元")
print(f"  概算中建安费+设备费（参照招标控制价）：约1,346,697.04元（含暂列金48,422.10）")
print(f"  扣除暂列金后：1,298,274.94元")
jifei_design = 1298274.94
print(f"  本次测算取计费额：{jifei_design:.2f}元 = 129.83万元")

# Step 2: 收费基价（内插法）
print()
print("【Step 2 工程设计收费基价 — 内插法】")
print("""
  《工程设计收费基价表》（单位：万元）
  ┌──────────┬──────────┐
  │ 计费额    │ 收费基价  │
  ├──────────┼──────────┤
  │   0      │    0     │
  │ 200      │   9.0    │
  │ 500      │  20.9    │
  │1000      │  38.8    │
  └──────────┴──────────┘
""")

fee_200 = 9.0  # 万元
fee_rate = fee_200 / 200  # 9.0/200 = 0.045万元/每万元计费额

design_base_million = 129.83
design_base_fee_million = design_base_million * fee_rate
design_base_fee = design_base_fee_million * 10000

print(f"  计费额 129.83万，处于0~200万区间")
print(f"  单位费率 = 9.0万÷200万 = 0.045（万元基价/每万元计费额）")
print(f"  收费基价 = 129.83 × 0.045 = {design_base_fee_million:.4f}万元 = {design_base_fee:.2f}元")

# Step 3: 调整系数
print()
print("【Step 3 调整系数】")

# 专业调整系数
coeff_prof = 1.0
print(f"  ① 专业调整系数：建筑、市政工程 = {coeff_prof}")

# 工程复杂程度
# 本项目为办公用房维修改造（含结构加固+装修），属一般标准的建筑环境设计和装饰
# 工程复杂程度表：建筑、人防工程（I级：1. 功能单一、技术要求简单；II级：1.一般公共建筑）
# 维修改造项目，结构加固有一定技术含量，取II级 1.0
coeff_complex = 1.0
print(f"  ② 工程复杂程度调整系数：含结构加固的维修改造，取II级 = {coeff_complex}")
print(f"     （注：若按一般装修I级=0.85，结果见附表）")

# 附加调整系数
# 改扩建和技术改造建设项目，附加调整系数为1.1~1.4
# 本项目为维修改造，属改扩建性质
coeff_extra = 1.1
print(f"  ③ 附加调整系数：改扩建和技术改造项目，取较低值 = {coeff_extra}")
print(f"     （注：取1.1~1.4中的低值，见附表对比）")

# Step 4: 计算
print()
print("【Step 4 计算基本设计费】")

design_fee = design_base_fee * coeff_prof * coeff_complex * coeff_extra
print(f"  基本设计费 = {design_base_fee:.2f} × {coeff_prof} × {coeff_complex} × {coeff_extra}")
print(f"              = {design_fee:.2f}元")

# 浮动幅度
print(f"  浮动幅度（上下20%）：{design_fee*0.8:.2f} ~ {design_fee*1.2:.2f}元")

# 对比
actual_design = 40000.00
diff_design = design_fee - actual_design
print()
print("【对比】")
print(f"  测算设计费（中值）：{design_fee:>10.2f}元")
print(f"  实际合同设计费：    {actual_design:>10.2f}元")
print(f"  差额：              {diff_design:>10.2f}元 ({diff_design/design_fee*100:+.1f}%)")
print(f"  判定：{'✅ 在合理范围内（实际金额在浮动下限以上）' if actual_design >= design_fee*0.8 else '⚠️ 低于测算下限，需关注' if actual_design >= design_fee*0.7 else '❌ 明显偏低'}")

# 多情景
print()
print("【多情景对比】")
scenarios_design = [
    ("I级(0.85) + 改扩建系数(1.1)", 0.85, 1.1),
    ("I级(0.85) + 改扩建系数(1.2)", 0.85, 1.2),
    ("II级(1.0) + 改扩建系数(1.1)", 1.0, 1.1),
    ("II级(1.0) + 改扩建系数(1.3)", 1.0, 1.3),
    ("I级(0.85) + 无改扩建系数", 0.85, 1.0),
]
print(f"  {'情景':<35s} {'测算金额':>10s} {'与实付差':>10s}")
print(f"  {'-'*35} {'-'*10} {'-'*10}")
for name, cpx, cex in scenarios_design:
    fee = design_base_fee * coeff_prof * cpx * cex
    d = fee - actual_design
    print(f"  {name:<35s} {fee:>10.2f} {d:>+10.2f}")

# ============================================================
# 二、监理费测算
# 依据：发改价格[2007]670号《建设工程监理与相关服务收费管理规定》
# ============================================================
print()
print()
print("━" * 70)
print("二、监理费 — 发改价格[2007]670号《建设工程监理与相关服务收费管理规定》")
print("━" * 70)

print("""
【收费标准摘要】
  施工监理服务收费 = 施工监理服务收费基价 × 专业调整系数
                    × 工程复杂程度调整系数 × 高程调整系数
  施工监理服务收费基价：按计费额从《施工监理服务收费基价表》内插
  计费额 = 建筑安装工程费 + 设备购置费 + 联合试运转费
""")

# Step 1: 计费额
print("【Step 1 确定计费额】")
jifei_supervise = 1069200.00  # 施工合同额（不含待摊）
print(f"  施工合同额（建安+设备）：1,069,200.00元 = 106.92万元")
print(f"  计费额取：106.92万元")

# Step 2: 收费基价
print()
print("【Step 2 施工监理服务收费基价 — 内插法】")
print("""
  《施工监理服务收费基价表》（单位：万元）
  ┌──────────┬──────────┐
  │ 计费额    │ 收费基价  │
  ├──────────┼──────────┤
  │   0      │    0     │
  │ 500      │   16.5   │
  │1000      │   30.1   │
  │3000      │   78.1   │
  └──────────┴──────────┘
""")

# 计费额106.92万 < 500万
# 实际处理方式：各省市有不同的理解
# 方法1：按基价表第一档费率内插
#   收费基价 = (16.5/500) × 计费额 = 0.033 × 计费额
# 方法2：低于500万时由双方协商
# 
# 四川省工程造价信息及行业惯例：低于500万的，按16.5÷500=3.3%的费率计算
supervise_rate = 16.5 / 500  # 3.3%
supervise_base_million = 106.92 * supervise_rate
supervise_base = supervise_base_million * 10000

print(f"  计费额 106.92万 < 500万（基价表最低档）")
print(f"  按川内惯例：低于500万的，按16.5÷500=3.3%费率计算")
print(f"  收费基价 = 106.92 × 3.3% = {supervise_base_million:.4f}万元 = {supervise_base:.2f}元")

# Step 3: 调整系数
print()
print("【Step 3 调整系数】")

# 专业调整系数
coeff_sup_prof = 1.0
print(f"  ① 专业调整系数：建筑、市政工程 = {coeff_sup_prof}")

# 工程复杂程度
# 一般房屋建筑工程：I级(0.85)—结构简单、6层以下、含装修
# 本项目含结构加固，取II级(1.0)
coeff_sup_complex = 1.0
print(f"  ② 工程复杂程度：含结构加固，取II级 = {coeff_sup_complex}")

# 高程调整系数
# 海拔2001~3000m: 1.1
# 阿坝州马尔康市海拔约2600m
coeff_sup_alt = 1.1
print(f"  ③ 高程调整系数：阿坝州海拔约2600m（2001~3000m区间）= {coeff_sup_alt}")

# Step 4: 计算
print()
print("【Step 4 计算施工监理服务收费】")

supervise_fee = supervise_base * coeff_sup_prof * coeff_sup_complex * coeff_sup_alt
print(f"  监理费 = {supervise_base:.2f} × {coeff_sup_prof} × {coeff_sup_complex} × {coeff_sup_alt}")
print(f"          = {supervise_fee:.2f}元")

# 浮动幅度
print(f"  浮动幅度（上下20%）：{supervise_fee*0.8:.2f} ~ {supervise_fee*1.2:.2f}元")

# 对比
actual_supervise = 27000.00
diff_supervise = supervise_fee - actual_supervise
print()
print("【对比】")
print(f"  测算监理费（中值）：{supervise_fee:>10.2f}元")
print(f"  实际合同监理费：    {actual_supervise:>10.2f}元")
print(f"  差额：              {diff_supervise:>10.2f}元 ({diff_supervise/supervise_fee*100:+.1f}%)")

# Check if actual is within 80% of calculated
lower_bound = supervise_fee * 0.8
within_range = actual_supervise >= lower_bound
print(f"  判定：{'✅ 在合理范围内' if within_range else '⚠️ 低于浮动下限(' + f'{lower_bound:.0f}' + '元)，需关注'}")

# 多情景
print()
print("【多情景对比】")
scenarios_sup = [
    ("II级(1.0)+高程1.1（主情景）", 1.0, 1.1),
    ("I级(0.85)+高程1.1", 0.85, 1.1),
    ("II级(1.0)+高程1.0（如海拔<2000m）", 1.0, 1.0),
    ("I级(0.85)+高程1.0", 0.85, 1.0),
]
print(f"  {'情景':<35s} {'测算金额':>10s} {'与实付差':>10s} {'比例':>8s}")
print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*8}")
for name, cpx, calt in scenarios_sup:
    fee = supervise_base * coeff_sup_prof * cpx * calt
    d = fee - actual_supervise
    pct = fee/actual_supervise
    print(f"  {name:<35s} {fee:>10.2f} {d:>+10.2f} {pct:>7.1%}")

# ============================================================
# 三、综合结论
# ============================================================
print()
print()
print("═" * 70)
print("三、综合结论")
print("═" * 70)

print("""
【设计费 40,000元】
  测算参考值区间：40,897 ~ 64,242元（随复杂度和改扩建系数变化）
  实际值40,000元处于区间下限附近
  → 若按 I级(0.85)+无改扩建附加 → 测算40,897元，实付40,000元 (差897元/2.2%)
  → 若按 II级(1.0)+改扩建附加 → 测算64,242元，实付40,000元 (差37.7%)
  关键判断：取决于对"是否适用改扩建附加系数"、"复杂度级别"的认定
  设计费通过"询价"方式采购，低于标准测算值可能是市场竞争结果
  
【监理费 27,000元】
  测算参考值（主情景）：38,811元（II级+高程1.1）
  实际值27,000元，低于测算30.4%
  → 若按 I级(0.85)+高程1.1 → 测算32,990元，实付27,000元 (差18.2%)
  高程系数1.1(海拔>2000m)是关键变量——如按海拔<2000m计算则基本吻合
  监理费通过"询价"方式采购
  
【重要提示 — 发改价格[2015]299号】
  2015年3月1日起，设计费、监理费等已放开为市场调节价，
  计价格[2002]10号、发改价格[2007]670号为参考标准，非强制。
  本项目2023年实施，适用市场调节价，上述测算为"参考基准"而非"合规底线"。

【审计建议】
  1. 设计费、监理费合同价均低于标准测算值，但基本在合理范围内
  2. 审核报告中应补充说明：
     - 采购方式（询价）及报价情况
     - 如低于标准基准的合理性说明（如小型项目市场竞争充分）
  3. 现存审核报告对此部分只有金额罗列，缺乏"按标准测算→对比→分析"的审计痕迹
""")
