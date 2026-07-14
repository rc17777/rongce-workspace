"""生成 Benford 检验用演示财务数据

生成 500 条混合数据:
  - 300 条正常数据（Benford 分布）
  - 200 条人工构造数据（首位数字集中在 5-9，圆整交易多）

用法: python generate_demo.py
输出: demo_ledger.csv
"""

import csv
import random
import numpy as np

random.seed(42)
np.random.seed(42)

records = []
voucher_id = 1

# ── 300 条正常数据: 遵循 Benford 分布 ──
benford_probs = [np.log10(1 + 1 / d) for d in range(1, 10)]
categories_normal = ['办公用品', '差旅费', '邮电费', '维修费', '印刷费', '咨询费', '会议费', '培训费', '租赁费']
departments = ['财务部', '行政部', '市场部', '技术部', '人事部', '总经办', '采购部', '销售部']

for _ in range(300):
    # 按 Benford 分布选首位数字
    first_digit = np.random.choice(range(1, 10), p=benford_probs)
    # 生成该首位数字范围内的金额
    magnitude = 10 ** random.randint(1, 4)
    low = first_digit * magnitude
    high = (first_digit + 1) * magnitude - 0.01
    amount = round(random.uniform(low, high), 2)

    records.append({
        '凭证号': f'PZ-{voucher_id:05d}',
        '日期': f'2026-{random.randint(1,6):02d}-{random.randint(1,28):02d}',
        '摘要': f'{random.choice(categories_normal)}采购',
        '科目': f'{random.randint(5501,5510)}',
        '金额': amount,
        '部门': random.choice(departments),
        '经办人': f'员工{random.randint(1,30):02d}',
        '支付方式': random.choice(['银行转账', '现金', '公务卡']),
        '数据来源': '正常',
    })
    voucher_id += 1

# ── 200 条人造数据: 避开 Benford 分布 ──
# 首位数字集中在 5-9（人为伪造的典型特征）
categories_fake = ['咨询费', '会议费', '印刷费', '办公费', '劳务费']
manipulated_first = [5, 6, 7, 8, 9]
manipulated_weights = [0.1, 0.15, 0.2, 0.25, 0.3]  # 偏向大数字

for _ in range(200):
    first_digit = random.choices(manipulated_first, weights=manipulated_weights)[0]
    magnitude = 10 ** random.randint(2, 4)  # 金额稍大

    # 一半是圆整交易
    if random.random() < 0.5:
        amount = round(random.uniform(first_digit, first_digit + 1) * magnitude, -2)  # 百元整数
    else:
        amount = round(random.uniform(first_digit, first_digit + 1) * magnitude, 2)

    # 约 30% 是整数（千元倍数）—— 圆整交易特征
    if random.random() < 0.3:
        amount = round(amount / 1000) * 1000

    records.append({
        '凭证号': f'PZ-{voucher_id:05d}',
        '日期': f'2026-{random.randint(1,6):02d}-{random.randint(1,28):02d}',
        '摘要': f'{random.choice(categories_fake)}费用',
        '科目': f'{random.randint(5501,5510)}',
        '金额': amount,
        '部门': random.choice(departments),
        '经办人': f'员工{random.randint(1,30):02d}',
        '支付方式': random.choice(['银行转账', '现金']),
        '数据来源': '人造',
    })
    voucher_id += 1

# ── 打乱顺序 ──
random.shuffle(records)

# ── 写入 CSV ──
output_path = 'demo_ledger.csv'
with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=records[0].keys())
    writer.writeheader()
    writer.writerows(records)

# ── 统计信息 ──
normal = [r for r in records if r['数据来源'] == '正常']
fake = [r for r in records if r['数据来源'] == '人造']
print(f'✅ 已生成 {output_path}')
print(f'   {len(records)} 条记录 (正常 {len(normal)} + 人造 {len(fake)})')
print(f'   总金额: ¥{sum(r["金额"] for r in records):,.2f}')
print(f'   正常金额: ¥{sum(r["金额"] for r in normal):,.2f}')
print(f'   人造金额: ¥{sum(r["金额"] for r in fake):,.2f}')

# 人造数据的特征
round_count = sum(1 for r in fake if r['金额'] % 1000 == 0)
print(f'   人造数据圆整交易: {round_count} 条 ({round_count/len(fake)*100:.0f}%)')

print(f'\n💡 运行检测:')
print(f'   python benford_test.py --input {output_path} --amount-col 金额')
