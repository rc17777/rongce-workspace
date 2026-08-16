# -*- coding: utf-8 -*-
"""
融策审计平台 - OpenClaw 技能入口
================================
注册所有分析模型到统一数据基座，提供统一的模型调用接口。
此脚本会被 SKILL.md 中定义的工作流触发。

使用：
  py index.py init              # 初始化数据基座+注册模型
  py index.py run 费用舞弊      # 运行指定模型（示例数据）
  py index.py run 全部          # 全部模型
  py index.py list              # 列出可用模型
  py index.py status            # 查看数据基座状态
"""

import sys
import io

# Windows 终端 GBK 编码修复：强制 stdout/stderr 使用 UTF-8，避免中文/emoji 乱码或崩溃
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import json
import importlib.util
from pathlib import Path

SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
DB_PATH = DATA_DIR / "rongce_core.db"

# 模型注册表
MODELS = [
    {
        "id": "M001", "name": "费用舞弊风险模型", "file": "expense_fraud_model.py",
        "function": "batch_score", "type": "财务舞弊",
        "desc": "基于8条风控规则的报销费用综合评分",
        "sample_args": {"with_pre_analysis": True},
        "sample_data_attr": "SAMPLE_DATA",
    },
    {
        "id": "M004", "name": "预算执行分析模型", "file": "budget_analysis.py",
        "function": "budget_analysis", "type": "预算执行",
        "desc": "预算执行率分析、年底突击花钱检测、季度波动检测",
        "sample_args": {"year": 2025},
        "sample_data_attr": "SAMPLE_DATA",
    },
    {
        "id": "M005", "name": "资金异常流动检测", "file": "fund_flow_model.py",
        "function": "detect_fund_flow_anomalies", "type": "资金异常",
        "desc": "资金回流、大额拆分、异常时段、跨区域检测",
        "sample_args": {"min_amount": 100000, "window_days": 30},
        "sample_data_attr": "SAMPLE_DATA",
    },
    {
        "id": "M101", "name": "出差×考勤时空验证", "file": "cross_coordinate_audit.py",
        "function": "detect_trip_attendance_conflict", "type": "跨坐标系",
        "desc": "报销出差日期 vs 门禁/打卡记录交叉验证",
        "sample_args": {},
        "sample_data_attr": "M101_SAMPLE",
    },
    {
        "id": "M102", "name": "受益对象重复检测", "file": "cross_coordinate_audit.py",
        "function": "detect_duplicate_beneficiaries", "type": "跨坐标系",
        "desc": "同身份证/同地址/同银行账号多次享受补贴",
        "sample_args": {},
        "sample_data_attr": "M102_SAMPLE",
    },
    {
        "id": "M103", "name": "进销存三向比对", "file": "cross_coordinate_audit.py",
        "function": "detect_inventory_sales_gap", "type": "跨坐标系",
        "desc": "期初+进货-期末 vs 申报销量，发现虚报",
        "sample_args": {},
        "sample_data_attr": "M103_SAMPLE",
    },
    {
        "id": "M104", "name": "报价行为模式分析", "file": "cross_coordinate_audit.py",
        "function": "detect_bidding_pattern", "type": "跨坐标系",
        "desc": "等差/等比报价、精准控价、报价区间过窄检测",
        "sample_args": {},
        "sample_data_attr": "M104_SAMPLE",
    },
    {
        "id": "M105", "name": "时间序列矛盾检测", "file": "cross_coordinate_audit.py",
        "function": "detect_time_sequence_conflicts", "type": "跨坐标系",
        "desc": "合同/公告/验收/付款的日期先后逻辑验证",
        "sample_args": {},
        "sample_data_attr": "M105_SAMPLE",
    },
    {
        "id": "M106", "name": "街景时空验证", "file": "cross_coordinate_audit.py",
        "function": "detect_street_view_conflicts", "type": "跨坐标系",
        "desc": "验收照片时间地点 x 百度街景历史影像比对",
        "sample_args": {},
        "sample_data_attr": "M106_SAMPLE",
    },
    {
        "id": "M107", "name": "卫星图进度验证", "file": "cross_coordinate_audit.py",
        "function": "detect_satellite_progress_conflicts", "type": "跨坐标系",
        "desc": "卫星/航拍历史影像 x 申报施工进度交叉验证",
        "sample_args": {},
        "sample_data_attr": "M107_SAMPLE",
    },
    {
        "id": "M108", "name": "工程量反推", "file": "cross_coordinate_audit.py",
        "function": "detect_quantity_reverse_conflict", "type": "跨坐标系",
        "desc": "8类建材用量反推工程量 vs 申报面积/体积比对",
        "sample_args": {},
        "sample_data_attr": "M108_SAMPLE",
    },
    {
        "id": "M109", "name": "OA登录IPx出差验证", "file": "cross_coordinate_audit.py",
        "function": "detect_oa_ip_trip_conflict", "type": "跨坐标系(替代)",
        "desc": "手机信令替代：内网IP登录操作 vs 出差日期交叉验证",
        "sample_args": {},
        "sample_data_attr": "M109_SAMPLE",
    },
    {
        "id": "M111", "name": "凭证制单行为分析", "file": "cross_coordinate_audit.py",
        "function": "detect_voucher_behavior_anomaly", "type": "跨坐标系(替代)",
        "desc": "审批画像替代：制单/审核/记账行为异常检测（一人多角色/深夜/秒批/月末）",
        "sample_args": {},
        "sample_data_attr": "M111_SAMPLE",
    },
    {
        "id": "M113", "name": "材料进场x施工日志", "file": "cross_coordinate_audit.py",
        "function": "detect_material_construction_mismatch", "type": "跨坐标系(替代)",
        "desc": "探地雷达替代：施工日志活动 vs 材料进场记录的物理支撑验证",
        "sample_args": {},
        "sample_data_attr": "M113_SAMPLE",
    },
    {
        "id": "M006", "name": "审计风险排序模型", "file": "audit_risk_ranking.py",
        "function": "rank_entities", "type": "风险排序",
        "desc": "7维加权综合评分，对审计对象进行风险优先级排序",
        "sample_args": {"top_n": 10},
        "sample_data_attr": "SAMPLE_ENTITIES",
    },
]


def init():
    """初始化：建表+注册模型"""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(SKILL_DIR / "rongce_data_base.py"), "init"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(SKILL_DIR)
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def load_module(filepath):
    """动态加载模型模块"""
    name = Path(filepath).stem
    spec = importlib.util.spec_from_file_location(name, str(filepath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_model(model_name):
    """运行指定模型"""
    matches = [m for m in MODELS if model_name in m["name"] or model_name in m["id"]]
    if not matches:
        print("未找到模型: %s。可用: %s" % (model_name, ", ".join(m["name"] for m in MODELS)))
        return

    for m in matches:
        print("=" * 60)
        print("  运行: %s (%s)" % (m["name"], m["type"]))
        print("  %s" % m["desc"])
        print("=" * 60)

        try:
            mod = load_module(SKILL_DIR / m["file"])
            func = getattr(mod, m["function"])
            args = m["sample_args"]

            # 获取示例数据
            sample_data = getattr(mod, m["sample_data_attr"])
            result = func(sample_data, **args)
            mod.print_report(result)

            # 记录运行日志到数据基座
            try:
                import subprocess as sp
                log_cmd = [sys.executable, "-X", "utf8", "-c",
                    "import sys; sys.path.insert(0, r'%s'); "
                    "from rongce_data_base import get_connection; "
                    "conn = get_connection(); "
                    "conn.execute('INSERT INTO model_run_logs (model_id, project_id, params, result_summary, status) VALUES (?,?,?,?,?)', "
                    "('%s', None, '%s', 'Ran with sample data', 'success')); "
                    "conn.execute('UPDATE analysis_models SET last_run_at=datetime(\\\"now\\\",\\\"localtime\\\"), run_count=run_count+1 WHERE model_id=?', ('%s',)); "
                    "conn.commit(); conn.close()" % (
                        str(SKILL_DIR).replace("\\", "\\\\"),
                        m["id"],
                        json.dumps(args, ensure_ascii=False),
                        m["id"]
                    )]
                sp.run(log_cmd, capture_output=True, cwd=str(SKILL_DIR))
            except Exception:
                pass

        except Exception as e:
            print("运行失败: %s" % e)
            import traceback
            traceback.print_exc()


def run_all():
    """运行全部模型"""
    for m in MODELS:
        run_model(m["name"])
    print("\n" + "=" * 60)
    print("  [OK] 全部模型运行完成")
    print("=" * 60)


def list_models():
    """列出所有可用模型"""
    print("=" * 60)
    print("  融策审计平台 - 可用模型")
    print("=" * 60)
    for m in MODELS:
        print("\n  %s %s" % (m["id"], m["name"]))
        print("     类型: %s" % m["type"])
        print("     描述: %s" % m["desc"])
    print("\n  总计: %d 个模型" % len(MODELS))


def show_status():
    """查看数据基座状态"""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(SKILL_DIR / "rongce_data_base.py"), "quality"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(SKILL_DIR)
    )
    print(result.stdout)
    if result.stderr:
        err = result.stderr.strip()
        if err and "illegal multibyte" not in err:
            print("ERROR: %s" % err)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  py index.py init              # 初始化")
        print("  py index.py run <模型名/全部>   # 运行模型")
        print("  py index.py list              # 列出模型")
        print("  py index.py status            # 数据基座状态")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "init":
        init()
    elif cmd == "run":
        model = sys.argv[2] if len(sys.argv) > 2 else "全部"
        if model == "全部":
            run_all()
        else:
            run_model(model)
    elif cmd == "list":
        list_models()
    elif cmd == "status":
        show_status()
    else:
        print("未知命令: %s" % cmd)
