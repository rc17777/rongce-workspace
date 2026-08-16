"""
融策统一数据基座 (RongCe Unified Data Base)
============================================
基于SQLite的统一数据管理、数据目录、数据接入引擎。
支持：多源数据注册、标准数据字典、数据质量监控、数据血缘追踪。

使用方式：
  py rongce_data_base.py init          # 初始化数据库
  py rongce_data_base.py register      # 注册数据源
  py rongce_data_base.py import        # 导入数据
  py rongce_data_base.py query         # 查询
  py rongce_data_base.py quality       # 数据质量报告
  py rongce_data_base.py lineage       # 数据血缘追踪
"""

import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import sqlite3
import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

DB_DIR = Path(__file__).parent / ".." / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "rongce_core.db"

# ────────── Schema 初始化 ──────────

SCHEMA_SQL = """
-- ========== 核心元数据 ==========

-- 数据源注册表：所有接入的数据系统
CREATE TABLE IF NOT EXISTS data_sources (
    source_id      TEXT PRIMARY KEY,       -- DS001, DS002...
    name           TEXT NOT NULL,          -- 财政预算系统 / 国库支付系统 ...
    category       TEXT NOT NULL,          -- 财政 / 税务 / 工商 / 社保 / 采购 / 项目 / 内部
    description    TEXT,
    access_type    TEXT DEFAULT 'file',    -- database / api / file / manual
    access_config  TEXT,                   -- JSON: 连接串、API地址、文件路径
    update_freq    TEXT DEFAULT 'monthly', -- realtime / daily / weekly / monthly / adhoc
    status         TEXT DEFAULT 'active',  -- active / inactive / error
    created_at     TEXT DEFAULT (datetime('now','localtime')),
    updated_at     TEXT DEFAULT (datetime('now','localtime'))
);

-- 数据表册：每个数据源下的数据表
CREATE TABLE IF NOT EXISTS data_tables (
    table_id       TEXT PRIMARY KEY,
    source_id      TEXT NOT NULL REFERENCES data_sources(source_id),
    name           TEXT NOT NULL,          -- 业务表名，如 budget_execution
    display_name   TEXT NOT NULL,          -- 中文名：预算执行表
    description    TEXT,
    row_count      INTEGER DEFAULT 0,
    file_path      TEXT,                   -- 如果是文件导入，记录路径
    imported_at    TEXT,
    is_archived    INTEGER DEFAULT 0
);

-- 字段标准字典：统一字段定义
CREATE TABLE IF NOT EXISTS field_dictionary (
    field_id       TEXT PRIMARY KEY,
    table_id       TEXT NOT NULL REFERENCES data_tables(table_id),
    field_name     TEXT NOT NULL,          -- 列名
    display_name   TEXT,                    -- 中文名
    data_type      TEXT,                   -- TEXT / INTEGER / REAL / DATE / DECIMAL
    is_standard    INTEGER DEFAULT 1,      -- 是否已标准化
    original_type  TEXT,                   -- 原始系统中的类型
    unit           TEXT,                   -- 单位：元 / 万元 / %
    description    TEXT,
    is_key_field   INTEGER DEFAULT 0,      -- 是否主键
    is_foreign_key INTEGER DEFAULT 0       -- 是否外键
);

-- 数据质量日志
CREATE TABLE IF NOT EXISTS data_quality_logs (
    log_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id       TEXT NOT NULL REFERENCES data_tables(table_id),
    check_type     TEXT NOT NULL,          -- completeness / accuracy / consistency / timeliness
    status         TEXT NOT NULL,          -- pass / warn / fail
    detail         TEXT,                    -- JSON 详情
    affected_rows  INTEGER DEFAULT 0,
    checked_at     TEXT DEFAULT (datetime('now','localtime'))
);

-- 数据血缘记录：记录每张表的ETL来源
CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    target_table   TEXT NOT NULL,          -- 目标表
    source_table   TEXT NOT NULL,          -- 来源表
    source_fields  TEXT,                   -- JSON: 字段映射关系
    transform_log  TEXT,                   -- 转换过程描述
    created_at     TEXT DEFAULT (datetime('now','localtime'))
);

-- ========== 审计业务数据 ==========

-- 审计项目表
CREATE TABLE IF NOT EXISTS audit_projects (
    project_id      TEXT PRIMARY KEY,      -- PRJ001
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,         -- 预算执行 / 经济责任 / 专项资金 / 绩效 / 采购
    target_unit     TEXT,                   -- 被审计单位
    start_date      TEXT,
    end_date        TEXT,
    status          TEXT DEFAULT 'planning', -- planning / executing / reviewing / completed
    budget_amount   REAL,                   -- 审计预算
    risk_score      REAL,                   -- 审计风险评分
    data_sources    TEXT,                   -- JSON: 关联数据源列表
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 审计发现表
CREATE TABLE IF NOT EXISTS audit_findings (
    finding_id      TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES audit_projects(project_id),
    title           TEXT NOT NULL,
    category        TEXT NOT NULL,         -- 违规 / 内控缺陷 / 效率问题 / 制度缺失
    severity        TEXT DEFAULT 'medium',  -- high / medium / low
    description     TEXT,
    amount_involved REAL,                   -- 涉及金额
    law_reference   TEXT,                   -- 法规依据
    evidence        TEXT,                   -- JSON: 证据列表
    status          TEXT DEFAULT 'pending',  -- pending / confirmed / rejected / rectified
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 分析模型注册表
CREATE TABLE IF NOT EXISTS analysis_models (
    model_id        TEXT PRIMARY KEY,       -- M001
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,          -- 财务舞弊 / 预算执行 / 资金异常 / 关联交易 / 政府采购 / 风险排序
    description     TEXT,
    script_path     TEXT,                   -- 脚本文件路径
    params_schema   TEXT,                   -- JSON: 参数定义
    version         TEXT DEFAULT '1.0',
    status          TEXT DEFAULT 'active',  -- active / deprecated / draft
    last_run_at     TEXT,
    run_count       INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 模型运行记录
CREATE TABLE IF NOT EXISTS model_run_logs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id        TEXT NOT NULL REFERENCES analysis_models(model_id),
    project_id      TEXT REFERENCES audit_projects(project_id),
    params          TEXT,                   -- JSON: 运行参数
    result_summary  TEXT,                   -- 结果摘要
    anomalies_found INTEGER DEFAULT 0,     -- 发现的异常数
    risk_score      REAL,                   -- 综合风险评分
    duration_sec    REAL,
    status          TEXT DEFAULT 'success',  -- success / partial / error
    error_msg       TEXT,
    ran_at          TEXT DEFAULT (datetime('now','localtime'))
);

-- ========== 基础数据 ==========

-- 标准科目表
CREATE TABLE IF NOT EXISTS standard_accounts (
    account_code    TEXT PRIMARY KEY,
    account_name    TEXT NOT NULL,
    level           INTEGER,                -- 科目层级 1-4
    parent_code     TEXT,
    category        TEXT                    -- 资产 / 负债 / 净资产 / 收入 / 支出
);

-- 标准单位表
CREATE TABLE IF NOT EXISTS standard_units (
    unit_code       TEXT PRIMARY KEY,
    unit_name       TEXT NOT NULL,
    unit_type       TEXT,                   -- 行政单位 / 事业单位 / 企业
    superior_code   TEXT,                   -- 上级单位编码
    region          TEXT                    -- 所在区域
);

-- 风险规则库
CREATE TABLE IF NOT EXISTS risk_rules (
    rule_id         TEXT PRIMARY KEY,       -- R001
    rule_name       TEXT NOT NULL,
    category        TEXT NOT NULL,          -- 采购舞弊 / 预算偏差 / 资金异常 / 费用违规 / 关联交易
    detection_logic TEXT,                   -- 检测逻辑描述
    risk_level      TEXT DEFAULT 'medium',  -- 极高 / 高 / 中 / 低
    weight          REAL DEFAULT 10,        -- 评分权重
    script_ref      TEXT,                   -- 关联脚本
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);
"""

# ────────── 标准数据 ──────────

STANDARD_DATA = {
    "data_sources": [
        ("DS001", "财政预算系统", "财政", "预算编制、执行、调整数据", "database", '{}', "daily", "active", None, None),
        ("DS002", "国库支付系统", "财政", "资金拨付、支付流水", "database", '{}', "realtime", "active", None, None),
        ("DS003", "政府采购系统", "采购", "采购项目、中标信息、合同", "api", '{}', "daily", "active", None, None),
        ("DS004", "税务系统", "税务", "纳税申报、发票数据", "api", '{}', "weekly", "active", None, None),
        ("DS005", "工商登记系统", "工商", "企业注册、变更、股权结构", "api", '{}', "monthly", "active", None, None),
        ("DS006", "社保系统", "社保", "参保信息、缴费记录", "database", '{}', "monthly", "active", None, None),
        ("DS007", "项目管理系统", "项目", "重大项目立项、进度、资金", "api", '{}', "daily", "active", None, None),
        ("DS008", "非税收入系统", "财政", "行政事业性收费、罚没收入", "database", '{}', "daily", "active", None, None),
        ("DS009", "内部管理系统", "内部", "审计底稿、报告、台账", "file", '{}', "adhoc", "active", None, None),
    ],
    "risk_rules": [
        ("R001", "大额整数报销", "费用违规", "金额≥10000且为整数", "中", 10, "benford_analysis.py", 1),
        ("R002", "连号发票异常", "费用违规", "同一单位连号发票≥5张", "高", 20, "expense_fraud_model.py", 1),
        ("R003", "高频小额报销", "费用违规", "同一人月报销次数≥20次", "中", 10, "expense_fraud_model.py", 1),
        ("R004", "节假日报销", "费用违规", "发票日期为法定节假日", "高", 20, "expense_fraud_model.py", 1),
        ("R005", "超标准报销", "费用违规", "住宿/交通/餐费超标准", "高", 20, "anomaly_detection.py", 1),
        ("R006", "关联方报销", "关联交易", "收款方为关联企业/个人", "极高", 40, "fund_flow_model.py", 1),
        ("R007", "重复报销", "费用违规", "同一发票多次报销", "极高", 40, "expense_fraud_model.py", 1),
        ("R008", "预算执行不足", "预算偏差", "执行率<50%", "高", 15, "budget_analysis.py", 1),
        ("R009", "超预算执行", "预算偏差", "执行率>120%", "高", 20, "budget_analysis.py", 1),
        ("R010", "年底突击花钱", "预算偏差", "Q4执行占比>50%", "高", 25, "budget_analysis.py", 1),
        ("R011", "资金回流", "资金异常", "资金流向形成闭环", "极高", 40, "fund_flow_model.py", 1),
        ("R012", "跨区域大额交易", "资金异常", "交易地与注册地不符", "高", 20, "fund_flow_model.py", 1),
        ("R013", "围标串标-文件雷同", "采购舞弊", "投标文件相似度>85%", "极高", 40, "bid_collusion.py", 1),
        ("R014", "异常低价", "采购舞弊", "低于市场均价30%以上", "高", 25, "bid_collusion.py", 1),
        ("R015", "单一来源不达标", "采购舞弊", "应招未招、化整为零", "高", 20, "bid_collusion.py", 1),
    ],
    "analysis_models": [
        ("M001", "Benford定律异常检测", "财务舞弊", "检测财务数据首位数字是否偏离Benford分布", "benford_analysis.py", '{"data_field":"amount","p_threshold":0.05}', "1.0", "active"),
        ("M002", "费用舞弊识别模型", "财务舞弊", "基于8条风险规则的报销费用评分", "expense_fraud_model.py", '{"rules":"all","min_score":20}', "1.0", "active"),
        ("M003", "关联交易识别模型", "关联交易", "通过多维关联分析发现隐性关联关系", "fund_flow_model.py", '{"depth":3}', "1.0", "active"),
        ("M004", "预算执行分析模型", "预算执行", "预算编制、执行进度、偏差分析", "budget_analysis.py", '{"year":2025}', "1.0", "active"),
        ("M005", "资金异常流动检测", "资金异常", "资金回流、大额拆分、异常时段检测", "fund_flow_model.py", '{"min_amount":100000,"window_days":30}', "1.0", "active"),
        ("M006", "审计风险排序模型", "风险排序", "综合多维度评分，输出审计优先级", "audit_risk_ranking.py", '{"top_n":20}', "1.0", "active"),
        ("M007", "政府采购审计模型", "采购舞弊", "围标串标、异常低价、单一来源分析", "bid_collusion_analyze.py", '{}', "1.0", "active"),
    ]
}


# ────────── 接口函数 ──────────

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database():
    """初始化数据库：建表 + 灌标准数据"""
    conn = get_connection()
    cur = conn.cursor()

    # 执行建表SQL
    for statement in SCHEMA_SQL.split(";"):
        stmt = statement.strip()
        if stmt:
            try:
                cur.execute(stmt)
            except Exception as e:
                print(f"[WARN] Schema statement skipped: {e}")

    # 灌标准数据（仅首次）
    for table, rows in STANDARD_DATA.items():
        if not rows:
            continue
        # 获取实际列数
        col_count = len(conn.execute(f'PRAGMA table_info({table})').fetchall())
        placeholders = ",".join("?" * col_count)
        stmt = f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})"
        for row in rows:
            try:
                # 补足缺失列
                padded = list(row) + [None] * (col_count - len(row))
                cur.execute(stmt, padded[:col_count])
            except Exception as e:
                print(f"[WARN] Insert into {table} failed: {e}")

    conn.commit()
    conn.close()

    # 打印报表
    conn = get_connection()
    cur = conn.cursor()
    tables = ["data_sources", "data_tables", "field_dictionary", "risk_rules", "analysis_models",
              "audit_projects", "audit_findings", "data_quality_logs", "data_lineage",
              "standard_accounts", "standard_units", "model_run_logs"]
    print("=" * 56)
    print("  融策统一数据基座 — 初始化完成")
    print(f"  数据库路径: {DB_PATH}")
    print(f"  数据库大小: {DB_PATH.stat().st_size / 1024:.1f} KB")
    print("=" * 56)
    for t in tables:
        try:
            cnt = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            icon = "✅" if cnt > 0 else "⬜"
            print(f"  {icon} {t}: {cnt} 条记录")
        except Exception:
            pass
    conn.close()
    print("=" * 56)


def register_source(name, category, description, access_type="file", update_freq="monthly"):
    """注册新数据源"""
    conn = get_connection()
    source_id = f"DS{conn.execute('SELECT COUNT(*) FROM data_sources').fetchone()[0] + 1:03d}"
    conn.execute(
        "INSERT INTO data_sources (source_id, name, category, description, access_type, update_freq) VALUES (?,?,?,?,?,?)",
        (source_id, name, category, description, access_type, update_freq)
    )
    conn.commit()
    conn.close()
    return source_id


def register_table(source_id, name, display_name, description, file_path=None):
    """注册数据表"""
    conn = get_connection()
    cnt = conn.execute("SELECT COUNT(*) FROM data_tables").fetchone()[0]
    table_id = f"T{cnt + 1:04d}"
    conn.execute(
        "INSERT INTO data_tables (table_id, source_id, name, display_name, description, file_path) VALUES (?,?,?,?,?,?)",
        (table_id, source_id, name, display_name, description, file_path)
    )
    conn.commit()
    conn.close()
    return table_id


def log_quality(table_id, check_type, status, detail, affected_rows=0):
    """记录数据质量检查结果"""
    conn = get_connection()
    conn.execute(
        "INSERT INTO data_quality_logs (table_id, check_type, status, detail, affected_rows) VALUES (?,?,?,?,?)",
        (table_id, check_type, status, json.dumps(detail, ensure_ascii=False), affected_rows)
    )
    conn.commit()
    conn.close()


def log_model_run(model_id, project_id, params, result_summary, anomalies, risk_score, duration, status="success", error_msg=None):
    """记录模型运行日志"""
    conn = get_connection()
    conn.execute("""
        INSERT INTO model_run_logs (model_id, project_id, params, result_summary, anomalies_found, risk_score, duration_sec, status, error_msg)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (model_id, project_id, json.dumps(params, ensure_ascii=False),
          json.dumps(result_summary, ensure_ascii=False) if result_summary else None,
          anomalies, risk_score, duration, status, error_msg))
    conn.execute("UPDATE analysis_models SET last_run_at=datetime('now','localtime'), run_count=run_count+1 WHERE model_id=?", (model_id,))
    conn.commit()
    conn.close()


def quality_report():
    """生成数据质量总报告"""
    conn = get_connection()
    print("\n" + "=" * 56)
    print("  融策数据质量报告")
    print("=" * 56)

    rows = conn.execute("""
        SELECT q.check_type, q.status, COUNT(*) as cnt
        FROM data_quality_logs q
        GROUP BY q.check_type, q.status
        ORDER BY q.check_type
    """).fetchall()
    for r in rows:
        print(f"  {r['check_type']:15s} | {r['status']:6s} | {r['cnt']}次")

    # 风险规则用量统计
    print("\n  --- 风险规则库 ---")
    rules = conn.execute("SELECT rule_id, rule_name, risk_level, weight FROM risk_rules WHERE is_active=1 ORDER BY risk_level, weight DESC").fetchall()
    for r in rules:
        icon = "🔴" if r['risk_level'] == "极高" else ("🟡" if r['risk_level'] == "高" else "🟢")
        print(f"  {icon} {r['rule_id']} {r['rule_name']} [{r['risk_level']}, 权重:{r['weight']}]")

    # 模型状态
    print("\n  --- 分析模型 ---")
    models = conn.execute("SELECT model_id, name, type, status, run_count, last_run_at FROM analysis_models ORDER BY model_id").fetchall()
    for m in models:
        last_run = m['last_run_at'] or "未运行"
        print(f"  {m['model_id']} {m['name']:15s} | {m['type']:8s} | {m['status']:8s} | 运行{m['run_count']}次 | 最近:{last_run}")

    conn.close()
    print("=" * 56)


def query_data(tablename, limit=10):
    """查询表中数据"""
    conn = get_connection()
    try:
        rows = conn.execute(f"SELECT * FROM {tablename} LIMIT ?", (limit,)).fetchall()
        cols = [d[0] for d in conn.execute(f"PRAGMA table_info({tablename})").fetchall()]
        print(f"表: {tablename} | 列: {', '.join(cols)} | 显示 {len(rows)}/{limit} 行")
        for r in rows:
            d = dict(r)
            print(json.dumps(d, ensure_ascii=False, default=str))
    except Exception as e:
        print(f"查询失败: {e}")
    conn.close()


def export_data(tablename, output_path):
    """导出表数据为JSON"""
    conn = get_connection()
    rows = conn.execute(f"SELECT * FROM {tablename}").fetchall()
    data = [dict(r) for r in rows]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"导出 {len(data)} 条记录到 {output_path}")
    conn.close()


# ────────── CLI ──────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: py rongce_data_base.py <命令> [参数...]")
        print("   init          — 初始化数据库")
        print("   quality       — 数据质量报告")
        print("   query <表名> [行数]  — 查询表数据")
        print("   export <表名> <文件> — 导出为JSON")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init_database()
    elif cmd == "quality":
        quality_report()
    elif cmd == "query":
        table = sys.argv[2] if len(sys.argv) > 2 else "risk_rules"
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        query_data(table, limit)
    elif cmd == "export":
        table = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 else f"{table}.json"
        export_data(table, out)
    else:
        print(f"未知命令: {cmd}")
