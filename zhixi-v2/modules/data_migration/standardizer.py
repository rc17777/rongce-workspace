# 智析智能体 v2.0 — 数据迁移标准化模块
# 功能：多数据库迁移 / 审计数据标准化 / 审计标准库管理

import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json


class DataMigrator:
    """多数据库间数据迁移"""
    
    @staticmethod
    def migrate_table(source_conn, target_conn, table_name: str, 
                      batch_size: int = 10000, where_clause: str = "",
                      incremental_col: str = None, last_value: Any = None) -> Dict:
        """全量/增量表迁移"""
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        if incremental_col and last_value:
            query += f" AND {incremental_col} > {last_value}"
        
        # 分批读取
        offset = 0
        total = 0
        while True:
            batch_query = query + f" LIMIT {batch_size} OFFSET {offset}"
            # df = pd.read_sql(batch_query, source_conn)  # 实际运行时需要连接
            offset += batch_size
            # if len(df) == 0: break
            # df.to_sql(table_name, target_conn, if_exists="append", index=False)
            # total += len(df)
            break  # 占位，实际运行时去掉
        
        return {"table": table_name, "total_rows": total, "status": "completed"}

    @staticmethod
    def schema_compare(source_conn, target_conn, table_name: str) -> Dict:
        """源库与目标库表结构对比"""
        # 实际运行时获取ddl
        return {
            "table": table_name,
            "source_columns": [],
            "target_columns": [],
            "missing_in_target": [],
            "type_mismatches": [],
        }


class AuditStandardizer:
    """审计数据标准化引擎"""
    
    # 审计行业数据规划 - 标准字段映射
    AUDIT_STANDARDS = {
        # 财务数据标准
        "financial": {
            "account_code":    {"name": "科目编码", "type": "str", "max_len": 20, "required": True},
            "account_name":    {"name": "科目名称", "type": "str", "max_len": 100, "required": True},
            "debit_amount":    {"name": "借方金额", "type": "float", "precision": 2, "required": True},
            "credit_amount":   {"name": "贷方金额", "type": "float", "precision": 2, "required": True},
            "voucher_date":    {"name": "凭证日期", "type": "date", "format": "YYYY-MM-DD", "required": True},
            "voucher_no":      {"name": "凭证号", "type": "str", "max_len": 30, "required": True},
            "summary":         {"name": "摘要", "type": "str", "max_len": 500},
            "voucher_type":    {"name": "凭证类型", "type": "str", "max_len": 10},
        },
        # 预算数据标准
        "budget": {
            "budget_item_code":   {"name": "预算项目编码", "type": "str", "max_len": 30, "required": True},
            "budget_item_name":   {"name": "预算项目名称", "type": "str", "max_len": 100, "required": True},
            "budget_amount":      {"name": "预算金额", "type": "float", "precision": 2, "required": True},
            "exec_amount":        {"name": "执行金额", "type": "float", "precision": 2},
            "fiscal_year":        {"name": "财政年度", "type": "int", "required": True},
            "department":         {"name": "部门名称", "type": "str", "max_len": 100},
        },
        # 采购数据标准
        "procurement": {
            "project_name":     {"name": "项目名称", "type": "str", "max_len": 200, "required": True},
            "proc_method":      {"name": "采购方式", "type": "str", "max_len": 20, "required": True},
            "budget_amount":    {"name": "预算金额", "type": "float", "precision": 2, "required": True},
            "contract_amount":  {"name": "合同金额", "type": "float", "precision": 2},
            "winner":           {"name": "中标单位", "type": "str", "max_len": 200},
            "bid_date":         {"name": "开标日期", "type": "date", "format": "YYYY-MM-DD"},
        },
        # 社保数据标准
        "social_security": {
            "id_card":         {"name": "身份证号", "type": "str", "max_len": 18, "required": True},
            "name":            {"name": "姓名", "type": "str", "max_len": 50, "required": True},
            "insurance_type":  {"name": "险种", "type": "str", "max_len": 20, "required": True},
            "pay_amount":      {"name": "缴费金额", "type": "float", "precision": 2},
            "pay_month":       {"name": "缴费月份", "type": "str", "max_len": 7, "required": True},
        },
        # 资产数据标准
        "asset": {
            "asset_code":      {"name": "资产编码", "type": "str", "max_len": 30, "required": True},
            "asset_name":      {"name": "资产名称", "type": "str", "max_len": 100, "required": True},
            "asset_type":      {"name": "资产类别", "type": "str", "max_len": 20},
            "original_value":  {"name": "原值", "type": "float", "precision": 2},
            "purchase_date":   {"name": "购置日期", "type": "date"},
            "department":      {"name": "使用部门", "type": "str", "max_len": 100},
        },
    }
    
    # 编码标准化映射
    CODE_MAPPINGS = {
        "sex":           {"男": "M", "女": "F", "男性": "M", "女性": "F"},
        "procurement_method": {"公开招标": "GKZB", "邀请招标": "YQZB", "竞争性谈判": "JZTP",
                                "竞争性磋商": "JZXS", "询价": "XJ", "单一来源": "DYLY"},
        "voucher_type":  {"记": "JZ", "收": "SK", "付": "FK", "转": "ZZ"},
    }
    
    @classmethod
    def get_standard_schema(cls, domain: str) -> Dict:
        """获取某个审计领域的标准字段定义"""
        return cls.AUDIT_STANDARDS.get(domain, {})
    
    @classmethod
    def list_domains(cls) -> List[str]:
        return list(cls.AUDIT_STANDARDS.keys())
    
    @classmethod
    def map_fields(cls, df: pd.DataFrame, mapping: Dict[str, str], domain: str) -> pd.DataFrame:
        """字段映射：将原始字段名映射到标准字段名"""
        result = df.rename(columns=mapping)
        standard = cls.get_standard_schema(domain)
        # 只保留标准字段
        cols = [c for c in standard.keys() if c in result.columns]
        return result[cols]
    
    @classmethod
    def apply_code_mapping(cls, df: pd.DataFrame, col: str, mapping_name: str) -> pd.DataFrame:
        """应用编码标准化映射"""
        if mapping_name in cls.CODE_MAPPINGS:
            result = df.copy()
            result[col] = result[col].astype(str).map(cls.CODE_MAPPINGS[mapping_name]).fillna(result[col])
            return result
        return df
    
    @classmethod
    def validate_standard(cls, df: pd.DataFrame, domain: str) -> Dict:
        """验证DataFrame是否符合审计数据标准"""
        standard = cls.get_standard_schema(domain)
        issues = []
        
        for field, spec in standard.items():
            if spec.get("required") and field not in df.columns:
                issues.append({"field": field, "issue": "缺少必填字段"})
                continue
            if field in df.columns:
                # 类型检查
                col_type = str(df[field].dtype)
                if spec["type"] == "str" and "object" not in col_type and "str" not in col_type:
                    issues.append({"field": field, "issue": f"类型不匹配: 期望{spec['type']}, 实际{col_type}"})
                # 长度检查
                if "max_len" in spec and spec["type"] == "str":
                    max_actual = df[field].astype(str).str.len().max()
                    if max_actual > spec["max_len"]:
                        issues.append({"field": field, "issue": f"超长: 最大{max_actual}, 限制{spec['max_len']}"})
        
        return {"domain": domain, "valid": len(issues) == 0, "issues": issues}


class StandardLibrary:
    """审计数据标准库管理"""
    
    def __init__(self):
        self.datasets: Dict[str, Dict] = {}  # {table_name: {schema, meta, stats}}
    
    def register_table(self, name: str, domain: str, description: str, columns: List[Dict]):
        self.datasets[name] = {
            "domain": domain,
            "description": description,
            "columns": columns,
            "row_count": 0,
            "last_update": datetime.now().isoformat(),
            "quality_score": 0,
        }
    
    def update_stats(self, name: str, row_count: int, quality_score: float):
        if name in self.datasets:
            self.datasets[name]["row_count"] = row_count
            self.datasets[name]["quality_score"] = quality_score
            self.datasets[name]["last_update"] = datetime.now().isoformat()
    
    def list_by_domain(self, domain: str) -> List[Dict]:
        return [{"name": k, **v} for k, v in self.datasets.items() if v["domain"] == domain]
    
    def to_catalog(self) -> List[Dict]:
        """生成数据资源目录"""
        return [
            {
                "table_name": k,
                "domain": v["domain"],
                "description": v["description"],
                "columns": len(v["columns"]),
                "rows": v["row_count"],
                "quality": v["quality_score"],
                "updated": v["last_update"],
            }
            for k, v in self.datasets.items()
        ]
