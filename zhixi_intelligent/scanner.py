"""
元数据自动扫描器
==============
连接数据库后，自动扫描表结构、字段信息、主外键关系、数据量统计。

扫描结果可直接用于：
- 数据资源目录生成
- 审计数据规划匹配
- 标准化脚本生成
"""
import json
from datetime import datetime
from sqlalchemy import inspect, text


class MetadataScanner:
    """数据库全量元数据扫描"""

    def __init__(self, connector):
        """
        参数:
            connector: DatabaseConnector 实例
        """
        self.connector = connector
        self.results = {}  # {连接名: 扫描结果}

    def scan(self, connection_name, table_filter=None):
        """
        扫描指定数据库的全部表和视图
        
        参数:
            connection_name: 连接名
            table_filter    : 可选，只扫描匹配的表名(支持模糊匹配)
                             如 "fiscal_%" 只扫描财政相关表
        
        返回:
            dict: 完整元数据报告
        """
        engine = self.connector.get_engine(connection_name)
        if not engine:
            return {"error": f"未找到连接: {connection_name}，请先用 connector.connect() 连接"}

        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        all_views = inspector.get_view_names()

        # 表名过滤
        if table_filter:
            filter_pattern = table_filter.replace("%", ".*")
            import re
            pattern = re.compile(filter_pattern, re.IGNORECASE)
            tables = [t for t in all_tables if pattern.search(t)]
            views = [v for v in all_views if pattern.search(v)]
        else:
            tables = all_tables
            views = all_views

        result = {
            "connection": connection_name,
            "dialect": engine.dialect.name,
            "scan_time": datetime.now().isoformat(),
            "total_tables": len(tables),
            "total_views": len(views),
            "total_columns": 0,
            "estimated_rows": 0,
            "tables": []
        }

        with engine.connect() as conn:
            # 扫描每张表
            for table_name in tables + views:
                is_view = table_name in views
                columns = inspector.get_columns(table_name)

                if not is_view:
                    pk = inspector.get_pk_constraint(table_name)
                    fks = inspector.get_foreign_keys(table_name)
                else:
                    pk = {"constrained_columns": []}
                    fks = []

                # 行数统计(适配不同数据库的SQL方言)
                row_count, row_error = self._count_rows(conn, engine, table_name, is_view)

                # 汇总
                result["total_columns"] += len(columns)
                if row_count:
                    result["estimated_rows"] += row_count

                table_info = {
                    "table_name": table_name,
                    "type": "view" if is_view else "table",
                    "row_count": row_count,
                    "row_count_error": row_error,
                    "column_count": len(columns),
                    "primary_key": pk.get("constrained_columns", []),
                    "foreign_keys": [
                        {
                            "from_columns": fk["constrained_columns"],
                            "to_table": fk["referred_table"],
                            "to_columns": fk["referred_columns"]
                        }
                        for fk in fks
                    ],
                    "columns": [
                        {
                            "name": c["name"],
                            "type": str(c["type"]),
                            "nullable": c.get("nullable", True),
                            "default": str(c.get("default")) if c.get("default") else None,
                            "is_pk": c["name"] in pk.get("constrained_columns", []),
                            "comment": c.get("comment", "")  # 字段注释(MySQL等支持)
                        }
                        for c in columns
                    ]
                }
                result["tables"].append(table_info)

        # 保存结果
        self.results[connection_name] = result
        return result

    def _count_rows(self, conn, engine, table_name, is_view):
        """跨数据库行数统计"""
        try:
            dialect = engine.dialect.name
            if dialect == "sqlite":
                sql = f'SELECT COUNT(*) FROM [{table_name}]'
            elif dialect == "mysql":
                sql = f'SELECT COUNT(*) FROM `{table_name}`'
            elif dialect in ("postgresql",):
                sql = f'SELECT COUNT(*) FROM "{table_name}"'
            elif dialect in ("mssql",):
                sql = f'SELECT COUNT(*) FROM [{table_name}]'
            else:
                sql = f'SELECT COUNT(*) FROM {table_name}'

            count = conn.execute(text(sql)).scalar()
            return count, None
        except Exception as e:
            return None, str(e)

    def scan_summary(self, connection_name):
        """获取简明的扫描摘要（给用户看的友好格式）"""
        result = self.results.get(connection_name)
        if not result:
            engine = self.connector.get_engine(connection_name)
            if not engine:
                return {"error": f"尚未扫描连接 '{connection_name}'，请先调用 scan()"}
            # 尝试自动扫描
            result = self.scan(connection_name)

        if "error" in result:
            return result

        tables = [t for t in result["tables"] if t["type"] == "table"]
        views = [t for t in result["tables"] if t["type"] == "view"]

        summary = {
            "数据库类型": result["dialect"],
            "扫描时间": result["scan_time"],
            "数据表": f"{len(tables)} 张",
            "视图": f"{len(views)} 个",
            "总字段数": result["total_columns"],
            "估计总行数": result["estimated_rows"],
            "表清单": []
        }

        for t in result["tables"]:
            cols_preview = ", ".join(
                f"{c['name']}{'(PK)' if c['is_pk'] else ''}"
                for c in t["columns"][:5]
            )
            if len(t["columns"]) > 5:
                cols_preview += f" ...共{len(t['columns'])}个字段"

            summary["表清单"].append({
                "表名": t["table_name"],
                "类型": t["type"],
                "行数": t["row_count"],
                "字段数": t["column_count"],
                "主键": t["primary_key"],
                "字段预览": cols_preview
            })

        return summary

    def export_to_json(self, connection_name, filepath):
        """导出扫描结果到JSON文件"""
        result = self.results.get(connection_name)
        if not result:
            result = self.scan(connection_name)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return {"status": "saved", "path": filepath}

    def quick_connect_and_scan(self, db_type, database, **kwargs):
        """快捷方式：连接并扫描（一步完成）"""
        conn_result = self.connector.quick_connect(db_type, database, **kwargs)
        if conn_result.get("status") != "connected":
            return {"error": f"连接失败: {conn_result.get('error')}"}
        name = list(self.connector.engines.keys())[-1]
        return self.scan(name)
