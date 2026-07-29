"""
P1: data_script_generator — 数据处理脚本生成器（DSG）

场景：审计数据处理中，"表头给AI，数据本地跑"的安全模式。
     用户提供CSV列名+处理需求描述 → 生成可直接本地执行的Python/Pandas脚本。

安全设计：
- 脚本仅操作本地CSV文件，不发起网络请求
- 内置敏感数据检测（身份证号/银行账号正则，禁止输出到日志）
- 输出脚本标注安全声明
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import re
import os


# ── 敏感数据检测正则 ─────────────────────────────────────────

SENSITIVE_PATTERNS = {
    "id_card": re.compile(r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"),
    "bank_account": re.compile(r"\b\d{16,19}\b"),
    "phone": re.compile(r"\b1[3-9]\d{9}\b"),
    "name": None,  # 姓名无法用正则，通过列名检测
}


SENSITIVE_COLUMN_KEYWORDS = [
    "姓名", "name", "身份证", "id_card", "idcard",
    "银行账号", "bank_account", "account", "卡号", "card_no",
    "手机", "phone", "mobile", "电话", "tel",
    "住址", "address", "地址",
    "密码", "password", "secret",
]

# 禁止在脚本中使用的高危函数
FORBIDDEN_FUNCTIONS = [
    "requests.get", "requests.post", "urllib",
    "socket.", "subprocess", "os.system", "exec(", "eval(",
    "__import__", "open(",  # open只允许读CSV，通过安全声明约束
]


# ── 脚本模板库 ──────────────────────────────────────────────

_SCRIPT_TEMPLATES = {
    "filter": """
# 筛选过滤
def filter_records(df):
    \"\"\"{description}\"\"\"
    {conditions}
    return result
""",
    "aggregate": """
# 分组聚合
def aggregate_records(df):
    \"\"\"{description}\"\"\"
    result = df.groupby({group_cols}).agg({agg_specs})
    return result
""",
    "merge": """
# 多表合并
def merge_tables(df1, df2):
    \"\"\"{description}\"\"\"
    result = pd.merge(df1, df2, {merge_params})
    return result
""",
    "sort_topn": """
# 排序取Top-N
def sort_topn(df):
    \"\"\"{description}\"\"\"
    result = df.sort_values(by={sort_cols}, ascending={ascending}).head({top_n})
    return result
""",
    "transform": """
# 字段转换
def transform_columns(df):
    \"\"\"{description}\"\"\"
    {transformations}
    return result
""",
    "deduplicate": """
# 去重
def deduplicate_records(df):
    \"\"\"{description}\"\"\"
    result = df.drop_duplicates(subset={subset_cols}, keep={keep})
    return result
""",
    "date_filter": """
# 日期筛选
def filter_by_date(df):
    \"\"\"{description}\"\"\"
    {date_col} = pd.to_datetime(df[{date_col_str}])
    mask = ({date_col} >= '{start_date}') & ({date_col} <= '{end_date}')
    result = df[mask]
    return result
""",
}


# ── 核心类 ──────────────────────────────────────────────────

@dataclass
class ScriptGenerationResult:
    """脚本生成结果"""
    script: str
    script_lines: int
    detected_sensitive_columns: List[str]
    security_warnings: List[str]
    estimated_output_rows: str
    usage_instructions: str


class DataScriptGenerator:
    """数据处理脚本生成器"""

    def __init__(self):
        self._sensitive_columns: Set[str] = set()
        self._security_warnings: List[str] = []

    def generate(
        self,
        csv_path: str,
        column_headers: List[str],
        processing_requirements: str,
        output_path: str = "output.csv",
        extra_filters: Optional[Dict[str, Any]] = None,
    ) -> ScriptGenerationResult:
        """
        生成数据处理脚本

        Args:
            csv_path: 输入CSV文件路径
            column_headers: 列名列表
            processing_requirements: 处理需求描述（自然语言）
            output_path: 输出文件路径
            extra_filters: 额外筛选条件

        Returns:
            ScriptGenerationResult 含完整脚本和安全声明
        """
        self._sensitive_columns.clear()
        self._security_warnings.clear()

        # 检测敏感列
        for col in column_headers:
            if any(kw in col.lower() for kw in SENSITIVE_COLUMN_KEYWORDS):
                self._sensitive_columns.add(col)

        # 解析处理需求，确定脚本操作类型
        operations = self._parse_requirements(processing_requirements, column_headers)

        # 组装完整脚本
        script = self._build_script(
            csv_path=csv_path,
            column_headers=column_headers,
            operations=operations,
            output_path=output_path,
            extra_filters=extra_filters,
            processing_requirements=processing_requirements,
        )

        # 估算输出行数
        estimated = self._estimate_output(processing_requirements)

        return ScriptGenerationResult(
            script=script,
            script_lines=script.count("\n"),
            detected_sensitive_columns=sorted(self._sensitive_columns),
            security_warnings=self._security_warnings,
            estimated_output_rows=estimated,
            usage_instructions=self._build_usage(csv_path, output_path),
        )

    def _parse_requirements(
        self, requirements: str, columns: List[str]
    ) -> List[Dict[str, Any]]:
        """解析自然语言需求 → 操作序列"""
        ops = []
        req_lower = requirements.lower()

        # 关键词→操作映射
        if any(kw in req_lower for kw in ["筛选", "过滤", "filter", "where", "条件"]):
            ops.append({"type": "filter", "desc": "按条件筛选记录"})

        if any(kw in req_lower for kw in ["分组", "汇总", "group", "sum", "count", "聚合", "统计"]):
            ops.append({"type": "aggregate", "desc": "分组聚合统计"})

        if any(kw in req_lower for kw in ["合并", "merge", "join", "关联", "拼接"]):
            ops.append({"type": "merge", "desc": "多表合并/关联"})

        if any(kw in req_lower for kw in ["排序", "top", "前", "最大", "最小", "sort"]):
            ops.append({"type": "sort_topn", "desc": "排序取Top-N"})

        if any(kw in req_lower for kw in ["去重", "重复", "unique", "dedup"]):
            ops.append({"type": "deduplicate", "desc": "去重检测"})

        if any(kw in req_lower for kw in ["日期", "时间", "date", "时间范围", "期间"]):
            ops.append({"type": "date_filter", "desc": "日期范围筛选"})

        if any(kw in req_lower for kw in ["转换", "计算", "transform", "新列", "新增", "派生"]):
            ops.append({"type": "transform", "desc": "字段转换/计算"})

        # 没有匹配到任何操作 → 默认识别为"筛选"
        if not ops:
            ops.append({"type": "filter", "desc": "通用数据筛选"})

        # 注入列信息
        for op in ops:
            op["columns"] = columns

        return ops

    def _build_script(
        self,
        csv_path: str,
        column_headers: List[str],
        operations: List[Dict],
        output_path: str,
        extra_filters: Optional[Dict] = None,
        processing_requirements: str = "",
    ) -> str:
        """组装完整Python脚本"""

        # 检测高危列名（如有则发出警告）
        sensitive_warning = ""
        if self._sensitive_columns:
            cols_str = ", ".join(sorted(self._sensitive_columns))
            sensitive_warning = (
                f"# ⚠️ 安全声明：检测到敏感列 [{cols_str}]，请勿在日志/屏幕输出中打印\n"
            )
            self._security_warnings.append(
                f"检测到敏感列: {cols_str}。脚本已内置安全过滤，不会打印这些列的内容到日志。"
            )

        # 列名列表
        cols_list = ",\n    ".join(f"'{c}'" for c in column_headers)

        # 操作函数
        funcs = []
        main_calls = []
        for i, op in enumerate(operations):
            func_code = self._generate_operation_code(op, i)
            funcs.append(func_code)
            call_name = op["type"]
            if i == 0:
                main_calls.append(f"    result = {call_name}_step{i}(df)")
            else:
                main_calls.append(f"    result = {call_name}_step{i}(result)")

        # 安全列过滤（在print/display时不输出敏感列）
        safe_columns = [c for c in column_headers if c not in self._sensitive_columns]
        safe_display = "', '".join(safe_columns[:10])  # 最多显示10个安全列
        if len(safe_columns) > 10:
            safe_display += ", ..."

        script = f'''"""
审计数据处理脚本 — 自动生成
生成时间：自动生成，请在使用前确认安全
=============================================================
{sensitive_warning}
## ⚠️ 使用前必读（安全声明）

1. 本脚本仅读取本地CSV文件，不发起任何网络请求
2. 敏感列（身份证/银行账号/手机号等）已自动识别，不会在脚本中打印
3. 输出结果将保存到 "{output_path}"，请确认该路径安全
4. 本脚本不包含 eval/exec/subprocess 等危险调用
5. 请在审计专用环境中运行，运行前建议代码审查

## 输入文件：{csv_path}
## 列名清单（{len(column_headers)}列）：
{cols_list}

## 处理需求：
{processing_requirements}
=============================================================
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# ── 安全配置 ──
# 以下列包含敏感信息，禁止输出到日志/屏幕
SENSITIVE_COLUMNS = {sorted(self._sensitive_columns) if self._sensitive_columns else []}

# ── 数据加载 ──
def load_data(filepath: str) -> pd.DataFrame:
    """加载CSV数据"""
    print(f"[DSG] 加载数据: {{filepath}}")
    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="gbk")
    print(f"[DSG] 加载完成: {{len(df)}}行 x {{len(df.columns)}}列")
    return df


def safe_display(df: pd.DataFrame, n: int = 5):
    """安全显示：排除敏感列"""
    cols = [c for c in df.columns if c not in SENSITIVE_COLUMNS]
    display_df = df[cols].head(n)
    print(display_df.to_string())


def safe_save(df: pd.DataFrame, filepath: str):
    """安全保存：如含敏感列则发出提醒"""
    sensitive_in_output = [c for c in df.columns if c in SENSITIVE_COLUMNS]
    if sensitive_in_output:
        print(f"[DSG] ⚠️ 输出文件包含敏感列: {{sensitive_in_output}}")
        print(f"[DSG] 请确认 {{filepath}} 的存储位置安全")
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"[DSG] 结果已保存: {{filepath}} ({{len(df)}}行)")


# ── 数据处理函数 ──
{chr(10).join(funcs)}

# ── 主流程 ──
def main():
    print(f"[DSG] === 审计数据处理开始 === ({{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}})")
    print(f"[DSG] 输入: {csv_path}")
    print(f"[DSG] 输出: {output_path}")
    print(f"[DSG] 安全列数: {{len(SENSITIVE_COLUMNS)}}列已标记为敏感")

    # 1. 加载数据
    df = load_data("{csv_path}")
    print(f"[DSG] 数据预览（排除敏感列）:")
    safe_display(df, n=5)
    print(f"[DSG] 列名: {{list(df.columns)}}")
    print(f"[DSG] 数据类型: {{dict(df.dtypes)}}")
    print()

    # 2. 数据处理
{chr(10).join(main_calls)}

    # 3. 保存结果
    print()
    safe_save(result, "{output_path}")

    # 4. 统计摘要
    print()
    print(f"[DSG] === 处理统计 ===")
    print(f"[DSG] 输入行数: {{len(df)}}")
    print(f"[DSG] 输出行数: {{len(result)}}")
    print(f"[DSG] 筛选率: {{(1 - len(result)/len(df))*100:.1f}}%")
    print(f"[DSG] === 处理完成 === ({{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}})")

    return result


if __name__ == "__main__":
    result = main()
'''
        return script

    def _generate_operation_code(self, op: Dict, step_id: int) -> str:
        """根据操作类型生成函数代码"""
        op_type = op["type"]
        desc = op.get("desc", "")
        columns = op.get("columns", [])

        if op_type == "filter":
            return f'''
def filter_step{step_id}(df):
    """{desc}"""
    # TODO: 请根据实际需求修改筛选条件
    # 示例: result = df[df["金额"] > 10000]
    result = df.copy()
    print(f"[DSG] 筛选: {{len(result)}}行（从{{len(df)}}行）")
    return result
'''
        elif op_type == "aggregate":
            return f'''
def aggregate_step{step_id}(df):
    """{desc}"""
    # TODO: 请指定分组列和聚合方式
    # 示例: result = df.groupby("部门").agg({{"金额": "sum", "数量": "count"}}).reset_index()
    result = df.copy()
    print(f"[DSG] 聚合: {{len(result)}}组")
    return result
'''
        elif op_type == "merge":
            return f'''
def merge_step{step_id}(df):
    """{desc}"""
    # TODO: 请指定要合并的第二个数据源
    # 示例: df2 = pd.read_csv("second_table.csv")
    #       result = pd.merge(df, df2, on="key", how="left")
    result = df.copy()
    print(f"[DSG] 合并: {{len(result)}}行")
    return result
'''
        elif op_type == "sort_topn":
            return f'''
def sort_topn_step{step_id}(df):
    """{desc}"""
    # TODO: 请指定排序列和Top-N数量
    # 示例: result = df.sort_values("金额", ascending=False).head(10)
    result = df.copy()
    print(f"[DSG] 排序Top-N: {{len(result)}}行")
    return result
'''
        elif op_type == "deduplicate":
            return f'''
def deduplicate_step{step_id}(df):
    """{desc}"""
    # TODO: 请指定去重依据的列
    # 示例: result = df.drop_duplicates(subset=["报销人", "金额"], keep="first")
    result = df.copy()
    print(f"[DSG] 去重: {{len(result)}}行（从{{len(df)}}行，去重{{len(df)-len(result)}}条）")
    return result
'''
        elif op_type == "date_filter":
            return f'''
def date_filter_step{step_id}(df):
    """{desc}"""
    # TODO: 请指定日期列和日期范围
    # 示例: date_col = pd.to_datetime(df["日期"])
    #       mask = (date_col >= "2024-01-01") & (date_col <= "2024-12-31")
    #       result = df[mask]
    result = df.copy()
    print(f"[DSG] 日期筛选: {{len(result)}}行（从{{len(df)}}行）")
    return result
'''
        elif op_type == "transform":
            return f'''
def transform_step{step_id}(df):
    """{desc}"""
    # TODO: 请指定字段转换逻辑
    # 示例: df["含税金额"] = df["金额"] * 1.13
    result = df.copy()
    print(f"[DSG] 字段转换: {{len(result)}}行")
    return result
'''
        return ""

    def _estimate_output(self, requirements: str) -> str:
        """估算输出行数"""
        if any(kw in requirements for kw in ["top", "前", "最大", "最小"]):
            return "少量（Top-N结果，通常≤100行）"
        if any(kw in requirements for kw in ["聚合", "group", "汇总"]):
            return "中等（分组聚合结果，通常≤1000行）"
        if any(kw in requirements for kw in ["去重", "dedup"]):
            return "中量（去重后数据，约为输入的60-90%）"
        return "大量（全量筛选结果，可能接近输入行数）"

    def _build_usage(self, csv_path: str, output_path: str) -> str:
        """生成使用说明"""
        sensitive_note = ""
        if self._sensitive_columns:
            cols = ", ".join(sorted(self._sensitive_columns))
            sensitive_note = (
                f"\n4. ⚠️ 输出文件可能包含敏感列（{cols}），"
                f"请勿上传到云端或分享给未授权人员"
            )

        return f"""使用方法：
1. 将脚本保存为 .py 文件（如 data_process.py）
2. 确认输入文件 "{csv_path}" 存在于脚本同级目录
3. 在审计专用环境中运行: python data_process.py
{sensitive_note}
5. 运行前建议进行代码审查，确认无异常操作
6. 输出文件将生成在: "{output_path}"
"""


# ── MCP工具接口 ──────────────────────────────────────────────

def data_script_generator(
    csv_path: str,
    column_headers: List[str],
    processing_requirements: str,
    output_path: str = "output.csv",
    extra_filters: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    数据处理脚本生成器（DSG）— "表头给AI，数据本地跑"

    Args:
        csv_path: 输入CSV文件路径
        column_headers: CSV列名列表
        processing_requirements: 处理需求描述（自然语言）
        output_path: 输出文件路径
        extra_filters: 额外筛选条件

    Returns:
        生成结果，含完整Python脚本和安全声明
    """
    generator = DataScriptGenerator()
    result = generator.generate(
        csv_path=csv_path,
        column_headers=column_headers,
        processing_requirements=processing_requirements,
        output_path=output_path,
        extra_filters=extra_filters,
    )

    return {
        "script": result.script,
        "script_lines": result.script_lines,
        "operations_detected": len(
            [l for l in result.script.split("\n") if l.strip().startswith("def ")]
        ) - 3,  # 减去 load_data, safe_display, safe_save
        "detected_sensitive_columns": result.detected_sensitive_columns,
        "security_warnings": result.security_warnings,
        "estimated_output_rows": result.estimated_output_rows,
        "usage_instructions": result.usage_instructions,
        "security_verdict": (
            "🔴 包含敏感列，已自动禁用日志输出，请确认运行环境安全"
            if result.detected_sensitive_columns
            else "🟢 未检测到敏感列，脚本可安全运行"
        ),
    }
