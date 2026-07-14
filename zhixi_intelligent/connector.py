"""
数据库自动连接器
==============
支持：MySQL, PostgreSQL, SQLite, SQL Server, Oracle, 达梦(DM), 神通(Oscar)

用于连接审计厅各类行业数据库，自动管理连接池。
"""
from datetime import datetime
from sqlalchemy import create_engine


class DatabaseConnector:
    """多数据库统一连接管理器"""

    # 连接字符串模板（SQLAlchemy格式）
    DIALECTS = {
        "mysql": "mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4",
        "postgresql": "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
        "sqlite": "sqlite:///{database}",   # database=文件路径
        "sqlserver": "mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes",
        "oracle": "oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={database}",
        "dameng": "dm+dmPython://{user}:{password}@{host}:{port}/{database}",
        "shengtong": "oscar+pyodbc://{user}:{password}@{host}:{port}/{database}",
    }

    # 数据库类型中文名
    DB_TYPE_NAMES = {
        "mysql": "MySQL/MariaDB",
        "postgresql": "PostgreSQL",
        "sqlite": "SQLite",
        "sqlserver": "SQL Server",
        "oracle": "Oracle",
        "dameng": "达梦(DM)",
        "shengtong": "神通(Oscar)",
    }

    def __init__(self):
        self.engines = {}  # {连接名: SQLAlchemy Engine}
        self.info = {}     # {连接名: 连接信息}

    def connect(self, name, db_type, host="", port=0, database="", user="", password=""):
        """
        连接数据库
        
        参数:
            name     - 给这个连接起的名字(如"审计厅财政库")
            db_type  - 数据库类型: mysql/postgresql/sqlite/sqlserver/oracle/dameng/shengtong
            host     - 主机地址
            port     - 端口号
            database - 数据库名/服务名(SQLite时填文件路径)
            user     - 用户名
            password - 密码
        
        返回:
            dict: {"status": "connected" / "error", ...}
        """
        template = self.DIALECTS.get(db_type)
        if not template:
            supported = ", ".join(self.DIALECTS.keys())
            return {"error": f"不支持的数据库类型: {db_type}。支持的类型: {supported}"}

        if db_type == "sqlite":
            conn_str = template.format(database=database)
        else:
            conn_str = template.format(
                user=user, password=password,
                host=host, port=port, database=database
            )

        try:
            engine = create_engine(conn_str, echo=False, pool_size=5,
                                   max_overflow=10, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(engine.dialect.statement_compiler(engine.dialect, None)._execution_options) if False else None
                # 测试连接
                pass  # connect() 本身就测试了

            self.engines[name] = engine
            self.info[name] = {
                "name": name, "db_type": db_type, "type_name": self.DB_TYPE_NAMES.get(db_type, db_type),
                "host": host, "port": port, "database": database,
                "dialect": engine.dialect.name,
                "connected_at": datetime.now().isoformat()
            }
            return {
                "status": "connected",
                "name": name,
                "type": self.DB_TYPE_NAMES.get(db_type, db_type),
                "dialect": engine.dialect.name,
                "time": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "failed", "error": str(e), "name": name, "db_type": db_type}

    def disconnect(self, name):
        """断开连接"""
        if name in self.engines:
            try:
                self.engines[name].dispose()
            except:
                pass
            del self.engines[name]
            del self.info[name]
            return {"status": "disconnected", "name": name}
        return {"error": f"未找到连接: {name}"}

    def get_engine(self, name):
        """获取指定连接的Engine对象"""
        return self.engines.get(name)

    def list_connections(self):
        """列出所有活动连接"""
        return list(self.engines.keys())

    def status(self):
        """
        查看所有连接状态（给用户看的友好格式）
        返回:
            dict: {"total": N, "connections": [...]}
        """
        connections = []
        for name, info in self.info.items():
            connections.append({
                "连接名": info["name"],
                "数据库类型": info["type_name"],
                "主机": info["host"],
                "端口": info["port"],
                "数据库": info["database"],
                "连接时间": info["connected_at"],
                "状态": "在线" if name in self.engines else "离线"
            })
        return {"total": len(connections), "connections": connections}

    def quick_connect(self, db_type, database, **kwargs):
        """
        快速连接（自动生成连接名）
        用于简单场景，如: connector.quick_connect("sqlite", "test.db")
        """
        name = f"{db_type}_{database}"
        return self.connect(name=name, db_type=db_type, database=database, **kwargs)
