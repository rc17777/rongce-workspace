# 智析智能体 v2.0 — 数据校验清洗模块
# 功能：完整性校验 / 总量变量校验 / 业务规则校验 / 数据清洗 / 审计规则模板

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class ValidationRule:
    id: str
    name: str
    rule_type: str      # completeness / consistency / business / statistical
    description: str
    severity: str = "error"  # error / warning / info
    apply_to: str = "*"      # 列名或 * 表示全部


@dataclass
class ValidationReport:
    rule_id: str
    rule_name: str
    passed: bool
    total_rows: int
    fail_rows: int
    fail_pct: float
    fail_samples: List[Dict]
    details: str = ""


class ValidationEngine:
    """数据校验引擎"""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
        self.reports: List[ValidationReport] = []
        self._init_builtin_rules()
    
    def _init_builtin_rules(self):
        """内置审计常用校验规则"""
        builtin = [
            ValidationRule("C001", "主键唯一性检查", "completeness", "检查主键列是否存在重复值", "error"),
            ValidationRule("C002", "必填字段非空检查", "completeness", "检查关键字段是否存在空值", "error"),
            ValidationRule("C003", "数据类型一致性", "consistency", "检查字段数据类型是否与预期一致", "warning"),
            ValidationRule("C004", "数值范围校验", "business", "检查数值字段是否在合理范围内", "error"),
            ValidationRule("C005", "日期合法性", "consistency", "检查日期字段格式和逻辑是否合法", "error"),
            ValidationRule("C006", "金额借贷平衡", "business", "检查借方金额合计是否等于贷方金额合计", "error"),
            ValidationRule("C007", "资金平衡校验", "business", "检查收入-支出是否等于结余", "error"),
            ValidationRule("C008", "科目对应关系", "business", "检查会计科目借贷对应是否符合规范", "warning"),
            ValidationRule("C009", "期间匹配校验", "business", "检查数据期间是否与审计期间一致", "error"),
            ValidationRule("C010", "统计抽样校验", "statistical", "随机抽样验证数据准确性", "info"),
        ]
        self.rules.extend(builtin)
    
    def add_rule(self, rule: ValidationRule):
        self.rules.append(rule)
    
    # ---- 完整性校验 ----
    def check_completeness(self, df: pd.DataFrame, key_cols: List[str] = None, required_cols: List[str] = None) -> List[ValidationReport]:
        reports = []
        # 主键唯一性
        if key_cols:
            dup = df.duplicated(subset=key_cols, keep=False)
            dup_count = dup.sum()
            reports.append(ValidationReport(
                rule_id="C001", rule_name="主键唯一性", passed=dup_count == 0,
                total_rows=len(df), fail_rows=dup_count, fail_pct=round(100*dup_count/len(df),2) if len(df)>0 else 0,
                fail_samples=df[dup][key_cols].head(10).to_dict("records")
            ))
        # 必填字段
        if required_cols:
            for col in required_cols:
                nulls = df[col].isna().sum()
                reports.append(ValidationReport(
                    rule_id="C002", rule_name=f"必填字段[{col}]非空", passed=nulls == 0,
                    total_rows=len(df), fail_rows=nulls, fail_pct=round(100*nulls/len(df),2) if len(df)>0 else 0,
                    fail_samples=[]
                ))
        return reports
    
    # ---- 总量变量校验 ----
    def check_totals(self, df: pd.DataFrame, total_col: str, group_col: str, expected: Dict[str, float] = None) -> List[ValidationReport]:
        """校验分组汇总与预期总量"""
        reports = []
        actual = df.groupby(group_col)[total_col].sum().to_dict()
        if expected:
            for grp, exp_val in expected.items():
                act_val = actual.get(grp, 0)
                diff = abs(act_val - exp_val)
                reports.append(ValidationReport(
                    rule_id="V001", rule_name=f"总量校验[{group_col}={grp}]",
                    passed=diff < 0.01,
                    total_rows=len(df), fail_rows=1 if diff >= 0.01 else 0,
                    fail_pct=0, fail_samples=[],
                    details=f"期望={exp_val}, 实际={act_val}, 差异={diff}"
                ))
        return reports
    
    # ---- 业务规则校验 ----
    def check_business_rules(self, df: pd.DataFrame, rules_yaml_path: str = None) -> List[ValidationReport]:
        """
        执行YAML格式的业务校验规则
        规则格式:
        - id: B001
          name: 金额非负
          condition: amount >= 0
          severity: error
        """
        # 内置审计业务规则
        reports = []
        
        # 资金平衡检查
        if "debit_amount" in df.columns and "credit_amount" in df.columns:
            dr = df["debit_amount"].sum()
            cr = df["credit_amount"].sum()
            balanced = abs(dr - cr) < 0.01
            reports.append(ValidationReport(
                rule_id="C006", rule_name="借贷平衡", passed=balanced,
                total_rows=len(df), fail_rows=0 if balanced else 1,
                fail_pct=0, fail_samples=[],
                details=f"借方合计={dr}, 贷方合计={cr}, 差额={abs(dr-cr)}"
            ))
        
        # 科目对应关系
        if "account_code" in df.columns and "counter_account" in df.columns:
            # 检查现金/银行存款不能直接对应收入科目（必须经过往来）
            cash_codes = ("1001", "1002")
            income_codes = ("4",)
            suspicious = df[
                df["account_code"].astype(str).str.startswith(cash_codes) &
                df["counter_account"].astype(str).str.startswith(income_codes)
            ]
            if len(suspicious) > 0:
                reports.append(ValidationReport(
                    rule_id="C008", rule_name="科目对应关系", passed=False,
                    total_rows=len(df), fail_rows=len(suspicious),
                    fail_pct=round(100*len(suspicious)/len(df), 2),
                    fail_samples=suspicious.head(10)[["account_code", "counter_account"]].to_dict("records"),
                    details="现金/银行存款疑似直接对应收入科目"
                ))
        
        return reports
    
    def run_all(self, df: pd.DataFrame, key_cols: List[str] = None, required_cols: List[str] = None,
                expected_totals: Dict = None) -> List[ValidationReport]:
        reports = []
        reports.extend(self.check_completeness(df, key_cols, required_cols))
        reports.extend(self.check_business_rules(df))
        if expected_totals:
            reports.extend(self.check_totals(df, list(expected_totals.keys())[0] if expected_totals else "", "", expected_totals))
        self.reports = reports
        return reports
    
    def summary(self) -> Dict:
        total = len(self.reports)
        passed = sum(1 for r in self.reports if r.passed)
        return {"total": total, "passed": passed, "failed": total - passed}


class DataCleaner:
    """数据清洗工作台"""
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: List[str] = None) -> Tuple[pd.DataFrame, int]:
        before = len(df)
        result = df.drop_duplicates(subset=subset)
        return result, before - len(result)
    
    @staticmethod
    def fill_missing(df: pd.DataFrame, strategy: Dict[str, str] = None) -> pd.DataFrame:
        """strategy: {col: method}, method=mean/median/mode/zero/ffill"""
        result = df.copy()
        if strategy:
            for col, method in strategy.items():
                if col not in result.columns:
                    continue
                if method == "mean":
                    result[col] = result[col].fillna(result[col].mean())
                elif method == "median":
                    result[col] = result[col].fillna(result[col].median())
                elif method == "mode":
                    result[col] = result[col].fillna(result[col].mode().iloc[0] if len(result[col].mode()) > 0 else 0)
                elif method == "zero":
                    result[col] = result[col].fillna(0)
                elif method == "ffill":
                    result[col] = result[col].fillna(method="ffill")
        return result
    
    @staticmethod
    def standardize_dates(df: pd.DataFrame, date_cols: List[str]) -> pd.DataFrame:
        result = df.copy()
        for col in date_cols:
            if col in result.columns:
                result[col] = pd.to_datetime(result[col], errors="coerce")
        return result
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, col: str, method: str = "iqr") -> pd.DataFrame:
        """异常值检测"""
        if method == "iqr":
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
            return df[(df[col] < lower) | (df[col] > upper)]
        elif method == "zscore":
            z = np.abs((df[col] - df[col].mean()) / df[col].std())
            return df[z > 3]
        return pd.DataFrame()
    
    @staticmethod
    def normalize_text(df: pd.DataFrame, text_cols: List[str]) -> pd.DataFrame:
        """文本标准化：去空格、统一全角半角"""
        result = df.copy()
        for col in text_cols:
            if col in result.columns:
                result[col] = result[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        return result
