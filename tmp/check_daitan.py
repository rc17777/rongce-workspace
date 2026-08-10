import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("1. DaTan contract-audit-payment per item")
print("=" * 60)
items = [
    ("Design fee", "Chengdu Yipinwei", 40000.00, 40000.00, 40000.00),
    ("Supervision", "Zhonghong Shamei", 27000.00, 27000.00, 27000.00),
]
for name, unit, contract, audited, paid in items:
    d1 = contract - audited
    d2 = audited - paid
    flag = "OK" if (d1 == 0 and d2 == 0) else "FAIL"
    print(f"[{flag}] {name:15s} contract={contract:>10.2f} audit={audited:>10.2f} paid={paid:>10.2f} cut={d1:>6.2f} unpaid={d2:>6.2f}")
print(f"Total: 67000.00 = 67000.00 = 67000.00  [OK]")

print()
print("=" * 60)
print("2. DaTan allocation to JianAn vs SheBei")
print("=" * 60)
jianan = 863684.35
shebei = 192985.07
daitan = 67000.00
total_cost = jianan + shebei  # 1056669.42

rj = jianan / total_cost
rs = shebei / total_cost
calc_j = round(daitan * rj, 2)
calc_s = round(daitan * rs, 2)

print(f"JianAn: {jianan:>12.2f}  ratio = {rj*100:.6f}%")
print(f"SheBei: {shebei:>12.2f}  ratio = {rs*100:.6f}%")
print()
print(f"Computed allocation:")
print(f"  JianAn = {daitan} x {rj*100:.6f}% = {calc_j:.2f}")
print(f"  SheBei = {daitan} x {rs*100:.6f}% = {calc_s:.2f}")
print(f"  Sum = {calc_j + calc_s:.2f}")

actual_j = 54763.44
actual_s = 12236.56
print()
print(f"Report allocation:")
print(f"  JianAn = {actual_j:.2f}")
print(f"  SheBei = {actual_s:.2f}")
print()

# High precision
precise_j = daitan * rj
precise_s = daitan * rs
print(f"High precision: J={precise_j:.10f} S={precise_s:.10f}")
print(f"Rounded:        J={round(precise_j,2)} S={round(precise_s,2)}")
print(f"Report:         J={actual_j} S={actual_s}")

diff_j = actual_j - round(precise_j, 2)
diff_s = actual_s - round(precise_s, 2)
print(f"Diff: J={diff_j:.2f} S={diff_s:.2f}")

if diff_j == 0 and diff_s == 0:
    print("Result: MATCH [OK]")
else:
    print("Result: MISMATCH! Differ by >0.01 after rounding")

# Try raw excel values
print()
print("=" * 60)
print("3. Raw Excel check")
print("=" * 60)
raw_jianan_daitan = 54763.4391179788  # 918447.7891179788 - 863684.35
raw_shebei_daitan = 12236.5608820212  # 205221.6308820212 - 192985.07
print(f"Raw Excel: J={raw_jianan_daitan:.10f} S={raw_shebei_daitan:.10f}")
print(f"Sum: {raw_jianan_daitan + raw_shebei_daitan:.10f}")
print(f"Rounded: J={round(raw_jianan_daitan,2)} S={round(raw_shebei_daitan,2)}")

# Check: what if they allocated by a slightly different method?
# Some accountants pick one item to bear the rounding difference
print()
print("=" * 60)
print("4. Alternative allocation methods")
print("=" * 60)
# Method A: Proportion, then adjust SheBei as remainder
method_a_j = calc_j
method_a_s = daitan - method_a_j
print(f"Method A (J proportional, S=remainder): J={method_a_j:.2f} S={method_a_s:.2f}")
print(f"  vs Report: J={actual_j} S={actual_s}")

# Method B: Proportion, then adjust JianAn as remainder
method_b_s = calc_s
method_b_j = daitan - method_b_s
print(f"Method B (S proportional, J=remainder): J={method_b_j:.2f} S={method_b_s:.2f}")
print(f"  vs Report: J={actual_j} S={actual_s}")

# Check cost ratios more carefully
print()
print("=" * 60)
print("5. Missing DaTan items check")
print("=" * 60)
print("Report has: design=40000, supervision=27000")
print("Typical DaTan items for renovation projects:")
typical = [
    "proj management fee",
    "feasibility study fee", 
    "survey/geotech fee",
    "design fee",
    "construction drawing review fee",
    "bidding agent fee",
    "supervision fee",
    "settlement audit fee",
    "financial audit fee (this report)",
]
for t in typical:
    has = any(kw in t.lower() for kw in ['design', 'supervision'])
    print(f"  {'[HAVE]' if has else '[MISS]'} {t}")

print()
print("Note: Financial audit fee for THIS review would be post-completion and")
print("is typically separate; settlement audit fee handled by different firm.")
print("Project is small (135wan), some items like feasibility study may have been")
print("processed separately or waived. But project management fee is notably absent.")
