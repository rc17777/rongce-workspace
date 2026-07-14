# 智析智能体 v2.0 — 数据采集模块
# 功能：多源数据采集 / 国产数据库适配 / API对接 / 财务账套解析

import pandas as pd
import requests
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class CollectTask:
    id: str
    name: str
    source_type: str      # database / api / file / platform
    source_config: Dict
    target_table: str
    schedule: str = "once"  # once / daily / weekly / monthly
    incremental: bool = False
    last_run: Optional[str] = None
    status: str = "pending"

class DatabaseAdapter:
    """多数据库适配器 - 支持 Oracle/SQL Server/MySQL/DB2/Sybase/达梦/神通/人大金仓"""
    
    CONNECTORS = {
        "mysql":      {"driver": "pymysql",    "port": 3306, "template": "mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"},
        "mssql":      {"driver": "pymssql",    "port": 1433, "template": "mssql+pymssql://{user}:{pwd}@{host}:{port}/{db}"},
        "oracle":     {"driver": "cx_Oracle",  "port": 1521, "template": "oracle+cx_oracle://{user}:{pwd}@{host}:{port}/?service_name={db}"},
        "postgresql": {"driver": "psycopg2",   "port": 5432, "template": "postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"},
        "db2":        {"driver": "pyodbc",     "port": 50000, "template": "db2+pyodbc://{user}:{pwd}@{host}:{port}/{db}"},
        "sybase":     {"driver": "pyodbc",     "port": 5000,  "template": "sybase+pyodbc://{user}:{pwd}@{host}:{port}/{db}"},
        "dm":         {"driver": "dmPython",   "port": 5236,  "template": "dm+dmPython://{user}:{pwd}@{host}:{port}/{db}"},  # 达梦
        "shentong":   {"driver": "pyodbc",     "port": 2003,  "template": "oscar+pyodbc://{user}:{pwd}@{host}:{port}/{db}"},  # 神通
        "kingbase":   {"driver": "psycopg2",   "port": 54321, "template": "postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"},  # 人大金仓
    }
    
    @classmethod
    def get_connection_string(cls, db_type: str, host: str, port: int, user: str, password: str, database: str) -> str:
        if db_type not in cls.CONNECTORS:
            raise ValueError(f"不支持的数据库类型: {db_type}。支持: {list(cls.CONNECTORS.keys())}")
        cfg = cls.CONNECTORS[db_type]
        p = port if port else cfg["port"]
        return cfg["template"].format(user=user, pwd=password, host=host, port=p, db=database)

    @classmethod
    def list_supported(cls) -> List[str]:
        return list(cls.CONNECTORS.keys())

    @classmethod
    def list_domestic(cls) -> List[str]:
        """国产数据库列表"""
        return ["dm", "shentong", "kingbase"]


class APIConnector:
    """政务共享平台 / 网络API数据采集"""
    
    @staticmethod
    def fetch_json(url: str, headers: Dict = None, params: Dict = None, auth: tuple = None) -> Dict:
        r = requests.get(url, headers=headers or {}, params=params or {}, auth=auth, timeout=30)
        r.raise_for_status()
        return r.json()
    
    @staticmethod
    def fetch_csv(url: str, **kwargs) -> pd.DataFrame:
        return pd.read_csv(url, **kwargs)
    
    @staticmethod
    def post_query(url: str, payload: Dict, headers: Dict = None) -> Dict:
        r = requests.post(url, json=payload, headers=headers or {}, timeout=60)
        r.raise_for_status()
        return r.json()


class FileImporter:
    """文件数据导入"""
    
    SUPPORTED = {
        ".xlsx":  lambda f: pd.read_excel(f),
        ".xls":   lambda f: pd.read_excel(f),
        ".csv":   lambda f: pd.read_csv(f, encoding="utf-8-sig"),
        ".json":   lambda f: pd.read_json(f),
        ".xml":   lambda f: pd.read_xml(f),
        ".parquet": lambda f: pd.read_parquet(f),
    }
    
    @classmethod
    def import_file(cls, path: str) -> pd.DataFrame:
        ext = os.path.splitext(path)[1].lower()
        if ext not in cls.SUPPORTED:
            raise ValueError(f"不支持的文件格式: {ext}。支持: {list(cls.SUPPORTED.keys())}")
        return cls.SUPPORTED[ext](path)


class AccountingParser:
    """财务账套解析 - 用友/金蝶/浪潮/新中大"""
    
    ACCOUNTING_SOFTWARE = {
        "yonyou_nc":   {"desc": "用友NC",   "acc_table": "GL_ACCOUPLEDGER",  "voucher_table": "GL_VOUCHER"},
        "yonyou_u8":   {"desc": "用友U8",   "acc_table": "GL_accvouch",      "voucher_table": "GL_accvouch"},
        "kingdee_eas": {"desc": "金蝶EAS",  "acc_table": "T_GL_ACCOUNT",     "voucher_table": "T_GL_VOUCHER"},
        "kingdee_k3":  {"desc": "金蝶K3",   "acc_table": "t_Account",        "voucher_table": "t_Voucher"},
        "inspur_gs":   {"desc": "浪潮GS",   "acc_table": "CW_KJKM",          "voucher_table": "CW_PZ"},
        "newgrand":    {"desc": "新中大",    "acc_table": "ACCOUNT",          "voucher_table": "VOUCHER"},
    }
    
    @staticmethod
    def parse_account_ledger(software: str, conn_string: str, year: int) -> pd.DataFrame:
        """解析科目余额表"""
        if software not in AccountingParser.ACCOUNTING_SOFTWARE:
            raise ValueError(f"不支持的财务软件: {software}")
        cfg = AccountingParser.ACCOUNTING_SOFTWARE[software]
        # 这里实际运行时需要数据库连接
        return pd.DataFrame()
    
    @staticmethod
    def parse_vouchers(software: str, conn_string: str, year: int, month: int = None) -> pd.DataFrame:
        """解析会计凭证"""
        cfg = AccountingParser.ACCOUNTING_SOFTWARE[software]
        return pd.DataFrame()


class CollectorManager:
    """采集管理器 - 统一调度"""
    
    def __init__(self):
        self.tasks: List[CollectTask] = []
        self.logs: List[Dict] = []
    
    def add_task(self, task: CollectTask):
        self.tasks.append(task)
    
    def run_task(self, task_id: str) -> Dict:
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            return {"error": f"任务不存在: {task_id}"}
        
        task.status = "running"
        log = {"task_id": task_id, "start": datetime.now().isoformat(), "records": 0, "errors": []}
        
        try:
            if task.source_type == "database":
                df = self._collect_database(task.source_config)
            elif task.source_type == "api":
                df = self._collect_api(task.source_config)
            elif task.source_type == "file":
                df = self._collect_file(task.source_config)
            else:
                raise ValueError(f"未知数据源类型: {task.source_type}")
            
            log["records"] = len(df)
            task.status = "completed"
            task.last_run = datetime.now().isoformat()
        except Exception as e:
            log["errors"].append(str(e))
            task.status = "failed"
        
        log["end"] = datetime.now().isoformat()
        self.logs.append(log)
        return log
    
    def _collect_database(self, config: Dict) -> pd.DataFrame:
        conn_str = DatabaseAdapter.get_connection_string(**config)
        # 实际连接逻辑
        return pd.DataFrame()
    
    def _collect_api(self, config: Dict) -> pd.DataFrame:
        data = APIConnector.fetch_json(config["url"], headers=config.get("headers"))
        return pd.DataFrame(data.get("data", data))
    
    def _collect_file(self, config: Dict) -> pd.DataFrame:
        return FileImporter.import_file(config["path"])
    
    def get_status(self) -> List[Dict]:
        return [{"id": t.id, "name": t.name, "status": t.status, "last_run": t.last_run} for t in self.tasks]
