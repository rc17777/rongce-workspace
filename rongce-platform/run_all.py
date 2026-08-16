"""
融策审计平台 — 一键运行入口
============================
支持：初始化数据基座 + 运行4个审计模型 + 查看质量报告

使用方式：
  py run_all.py                    # 初始化 + 全部模型示例运行
  py run_all.py --init-only        # 只初始化数据基座
  py run_all.py --model 费用舞弊    # 只运行指定模型
  py run_all.py --quality          # 只看数据质量报告

可选模型: 费用舞弊 / 预算执行 / 资金异常 / 风险排序 / 全部
"""

import sys
import os
import json
import time
from pathlib import Path

BASE = Path(__file__).parent
DATA_BASE = BASE / "data-base"
MODELS = BASE / "models"
HR = "=" * 60


def run_init():
    """初始化统一数据基座"""
    print(f"\n{HR}")
    print("  [1/5] 初始化统一数据基座")
    print(HR)
    import subprocess
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(DATA_BASE / "rongce_data_base.py"), "init"],
        capture_output=True, text=True, cwd=str(BASE)
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def run_model(name, script, args):
    """运行单个模型"""
    print(f"\n{HR}")
    print(f"  [运行模型] {name}")
    print(HR)
    import subprocess
    cmd = [sys.executable, "-X", "utf8", str(MODELS / script)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE))
    print(result.stdout)
    if result.stderr:
        # 只打印非emoji相关的错误
        err = result.stderr.strip()
        if err and "illegal multibyte" not in err:
            print(f"[ERROR] {err}")


def run_all_models():
    """依次运行所有模型"""
    models = [
        ("费用舞弊风险模型", "expense_fraud_model.py", ["--sample"]),
        ("预算执行分析模型", "budget_analysis.py", ["--sample"]),
        ("资金异常流动检测", "fund_flow_model.py", ["--sample"]),
        ("审计风险排序模型", "audit_risk_ranking.py", ["--sample", "--top", "10"]),
    ]
    for name, script, args in models:
        run_model(name, script, args)


def run_quality():
    """查看数据质量报告"""
    print(f"\n{HR}")
    print("  查看数据质量报告")
    print(HR)
    import subprocess
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(DATA_BASE / "rongce_data_base.py"), "quality"],
        capture_output=True, text=True, cwd=str(BASE)
    )
    print(result.stdout)


def show_menu():
    """显示操作菜单"""
    print(HR)
    print("  融策审计平台 — 操作菜单")
    print(HR)
    print("  [1] 初始化数据基座 + 运行全部模型")
    print("  [2] 只初始化数据基座")
    print("  [3] 运行费用舞弊风险模型")
    print("  [4] 运行预算执行分析模型")
    print("  [5] 运行资金异常流动检测")
    print("  [6] 运行审计风险排序模型")
    print("  [7] 查看数据质量报告")
    print("  [8] 运行全部模型")
    print("  [0] 退出")
    print(HR)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行模式
        if "--init-only" in sys.argv:
            run_init()
        elif "--quality" in sys.argv:
            run_quality()
        elif "--model" in sys.argv:
            idx = sys.argv.index("--model")
            model_name = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "全部"
            if "费用舞弊" in model_name or "expense" in model_name.lower():
                run_model("费用舞弊风险模型", "expense_fraud_model.py", ["--sample"])
            elif "预算" in model_name or "budget" in model_name.lower():
                run_model("预算执行分析模型", "budget_analysis.py", ["--sample"])
            elif "资金" in model_name or "fund" in model_name.lower():
                run_model("资金异常流动检测", "fund_flow_model.py", ["--sample"])
            elif "风险排序" in model_name or "risk" in model_name.lower():
                run_model("审计风险排序模型", "audit_risk_ranking.py", ["--sample", "--top", "10"])
            else:
                run_all_models()
        else:
            run_init()
            run_all_models()
        sys.exit(0)

    # 交互模式
    while True:
        show_menu()
        choice = input("  请选择 [1-8 / 0 退出]: ").strip()

        if choice == "0":
            print("  再见！")
            break
        elif choice == "1":
            run_init()
            run_all_models()
        elif choice == "2":
            run_init()
        elif choice == "3":
            run_model("费用舞弊风险模型", "expense_fraud_model.py", ["--sample"])
        elif choice == "4":
            run_model("预算执行分析模型", "budget_analysis.py", ["--sample"])
        elif choice == "5":
            run_model("资金异常流动检测", "fund_flow_model.py", ["--sample"])
        elif choice == "6":
            run_model("审计风险排序模型", "audit_risk_ranking.py", ["--sample", "--top", "10"])
        elif choice == "7":
            run_quality()
        elif choice == "8":
            run_all_models()
        else:
            print("  无效选择，请重新输入")

        input("\n  按回车继续..." if choice != "7" else "\n  按回车返回主菜单...")
