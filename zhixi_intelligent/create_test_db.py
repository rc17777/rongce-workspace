"""创建测试用SQLite数据库——模拟审计厅数据采集场景"""
import sqlite3
import os
import random
from datetime import datetime, timedelta

db_path = r"D:\openclaw-workspace\zhixi_intelligent\collected_data\test_audit_demo.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# ========== 1. 财政预算表 ==========
c.execute("""CREATE TABLE fiscal_budget (
    id INTEGER PRIMARY KEY,
    dept_code TEXT, dept_name TEXT, budget_year INTEGER,
    initial_amount REAL, adjusted_amount REAL, final_amount REAL,
    func_class TEXT, eco_class TEXT, fund_source TEXT
)""")
depts = [("001", "教育局"), ("002", "卫健委"), ("003", "交通局"), ("004", "住建局"),
         ("005", "农业农村局"), ("006", "人社局"), ("007", "民政局"), ("008", "科技局")]
funcs = ["205-教育", "210-卫生健康", "214-交通运输", "212-城乡社区",
         "213-农林水", "208-社会保障", "208-民政", "206-科学技术"]
for i in range(200):
    d = random.choice(depts)
    c.execute("INSERT INTO fiscal_budget VALUES (?,?,?,?,?,?,?,?,?,?)", (
        i+1, d[0], d[1], 2025,
        round(random.uniform(100, 5000), 2),
        round(random.uniform(90, 5200), 2),
        round(random.uniform(95, 5100), 2),
        random.choice(funcs), random.choice(["301-工资", "302-商品服务", "309-资本性支出"]),
        random.choice(["一般公共预算", "政府性基金", "专项转移支付"])
    ))

# ========== 2. 政府采购表 ==========
c.execute("""CREATE TABLE procurement (
    id INTEGER PRIMARY KEY, project_name TEXT, proc_method TEXT,
    budget_amount REAL, bid_amount REAL, contract_amount REAL,
    winner TEXT, bidder_count INTEGER, bid_date TEXT, sign_date TEXT,
    dept_name TEXT, category TEXT
)""")
methods = ["公开招标", "邀请招标", "竞争性磋商", "竞争性谈判", "询价", "单一来源"]
bidders = ["A建设集团", "B工程技术公司", "C项目管理公司", "D市政工程公司", "E建筑安装公司"]
categories = ["工程", "货物", "服务"]
projects = ["校舍维修工程", "道路改造项目", "设备采购项目", "信息化平台建设", "办公家具采购",
            "物业服务招标", "公务用车采购", "污水处理工程", "智慧校园项目", "医疗设备采购"]
for i in range(50):
    budget = round(random.uniform(10, 500), 2)
    bid = round(budget * random.uniform(0.85, 0.99), 2)
    contract = round(bid * random.uniform(0.95, 1.0), 2)
    c.execute("INSERT INTO procurement VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
        i+1, random.choice(projects), random.choice(methods),
        budget, bid, contract,
        random.choice(bidders), random.randint(2, 8),
        f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        random.choice(depts)[1], random.choice(categories)
    ))

# ========== 3. 社保发放表 ==========
c.execute("""CREATE TABLE social_security (
    id INTEGER PRIMARY KEY, id_card TEXT, name TEXT, gender TEXT,
    birth_date TEXT, pension_type TEXT, monthly_amount REAL,
    pay_status TEXT, pay_month TEXT, bank_account TEXT
)""")
pension_types = ["城镇职工养老保险", "城乡居民养老保险", "机关事业单位养老保险"]
genders = ["男", "女"]
names_pool = ["张伟", "王芳", "李娜", "刘洋", "陈静", "杨帆", "赵敏", "黄磊",
              "周杰", "吴鑫", "徐明", "孙丽", "马超", "朱红", "胡兵", "林雪"]
for i in range(500):
    birth = f"{random.randint(1945,2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    c.execute("INSERT INTO social_security VALUES (?,?,?,?,?,?,?,?,?,?)", (
        i+1,
        f"5101{random.randint(1900,2020)}{random.randint(1,12):02d}{random.randint(1,28):02d}{random.randint(1000,9999)}",
        random.choice(names_pool), random.choice(genders),
        birth, random.choice(pension_types),
        round(random.uniform(800, 8000), 2),
        random.choice(["已发放", "已发放", "已发放", "已发放", "未发放", "暂停"]),
        f"2025-{random.randint(1,6):02d}",
        f"6222{random.randint(100000000000,999999999999)}"
    ))

# ========== 4. 公积金缴存表 ==========
c.execute("""CREATE TABLE housing_fund (
    id INTEGER PRIMARY KEY, unit_name TEXT, employee_name TEXT,
    id_card TEXT, base_salary REAL, person_rate REAL, unit_rate REAL,
    monthly_amount REAL, balance REAL, pay_month TEXT
)""")
units = ["教育局", "卫健委", "交通局", "住建局", "某国企集团", "某医院", "某高校"]
for i in range(300):
    base = random.uniform(3000, 25000)
    p_rate = random.choice([0.05, 0.07, 0.08, 0.10, 0.12])
    u_rate = random.choice([0.05, 0.07, 0.08, 0.10, 0.12])
    monthly = round(base * (p_rate + u_rate), 2)
    balance = round(monthly * random.randint(12, 180), 2)
    c.execute("INSERT INTO housing_fund VALUES (?,?,?,?,?,?,?,?,?,?)", (
        i+1, random.choice(units), random.choice(names_pool),
        f"5101{random.randint(1900,2020)}{random.randint(1,12):02d}{random.randint(1,28):02d}{random.randint(1000,9999)}",
        round(base, 2), p_rate, u_rate, monthly, balance,
        f"2025-{random.randint(1,6):02d}"
    ))

# ========== 5. 重大项目表 ==========
c.execute("""CREATE TABLE major_projects (
    id INTEGER PRIMARY KEY, project_code TEXT, project_name TEXT,
    total_invest REAL, year_invest REAL, progress_pct REAL,
    start_date TEXT, end_date TEXT, responsible_dept TEXT,
    category TEXT, status TEXT, approval_no TEXT
)""")
proj_names = ["XX高速公路", "YY水库工程", "ZZ医院新院区", "AA体育中心",
              "BB棚户区改造", "CC产业园区", "DD铁路专线", "EE污水处理厂"]
statuses = ["在建", "在建", "在建", "已竣工", "停工", "前期准备"]
for i in range(30):
    total = round(random.uniform(1000, 500000), 2)
    year = round(total * random.uniform(0.05, 0.3), 2)
    c.execute("INSERT INTO major_projects VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
        i+1,
        f"XM-2025-{i+1:04d}",
        random.choice(proj_names) + f"（{random.choice(['一期','二期','改扩建'])}）",
        total, year,
        round(random.uniform(0, 100), 1),
        f"202{random.randint(2,5)}-{random.randint(1,12):02d}",
        f"202{random.randint(6,8)}-{random.randint(1,12):02d}",
        random.choice(depts)[1],
        random.choice(["交通", "水利", "卫生", "体育", "保障房", "产业园区", "铁路", "环保"]),
        random.choice(statuses),
        f"川发改审批[{2024+random.randint(0,2)}]{random.randint(100,999)}号"
    ))

# ========== 6. 公务卡消费表 ==========
c.execute("""CREATE TABLE official_card (
    id INTEGER PRIMARY KEY, card_no TEXT, holder_name TEXT,
    dept_name TEXT, trans_date TEXT, amount REAL,
    merchant TEXT, category TEXT, purpose TEXT
)""")
merchants = ["某酒店", "某餐饮公司", "某加油站", "某办公用品店", "某旅行社",
             "某会议中心", "某汽车维修厂", "某广告公司", "某印刷厂"]
purposes = ["差旅住宿", "公务接待", "车辆加油", "办公用品", "会议费",
            "培训费", "车辆维修", "宣传费", "印刷费"]
for i in range(1000):
    c.execute("INSERT INTO official_card VALUES (?,?,?,?,?,?,?,?,?)", (
        i+1,
        f"6282{random.randint(100000000000,999999999999)}",
        random.choice(names_pool),
        random.choice(depts)[1],
        f"2025-{random.randint(1,6):02d}-{random.randint(1,28):02d}",
        round(random.uniform(50, 15000), 2),
        random.choice(merchants),
        random.choice(purposes),
        random.choice(purposes)
    ))

# ========== 7. 部门决算表 ==========
c.execute("""CREATE TABLE dept_final_accounts (
    id INTEGER PRIMARY KEY, dept_code TEXT, dept_name TEXT, year INTEGER,
    budget_revenue REAL, actual_revenue REAL, budget_expense REAL,
    actual_expense REAL, surplus REAL
)""")
for d in depts:
    for year in [2023, 2024]:
        b_rev = round(random.uniform(500, 8000), 2)
        b_exp = round(random.uniform(500, 8000), 2)
        c.execute("INSERT INTO dept_final_accounts VALUES (?,?,?,?,?,?,?,?,?)", (
            (depts.index(d)*2 + (1 if year==2023 else 2)), d[0], d[1], year,
            b_rev, round(b_rev * random.uniform(0.9, 1.05), 2),
            b_exp, round(b_exp * random.uniform(0.88, 1.02), 2),
            round(b_rev * random.uniform(-0.05, 0.05), 2)
        ))

conn.commit()

# 统计
tables = ["fiscal_budget", "procurement", "social_security", "housing_fund",
          "major_projects", "official_card", "dept_final_accounts"]
total_rows = 0
for t in tables:
    count = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    total_rows += count
    print(f"  [{t}] {count:,} 行")

conn.close()
print(f"\n  总计: {len(tables)} 张表, {total_rows:,} 行数据")
print(f"  数据库: {db_path}")
