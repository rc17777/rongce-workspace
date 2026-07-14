"""
融策审计数据中台 - 配置文件
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    user: str = os.getenv('DB_USER', 'rongce')
    password: str = os.getenv('DB_PASSWORD', 'rongce123')
    database: str = os.getenv('DB_NAME', 'rongce_data_platform')
    
    def to_dict(self):
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database
        }

@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    password: Optional[str] = os.getenv('REDIS_PASSWORD')
    db: int = int(os.getenv('REDIS_DB', '0'))

@dataclass
class MinIOConfig:
    """MinIO配置"""
    endpoint: str = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    access_key: str = os.getenv('MINIO_ACCESS_KEY', 'rongce')
    secret_key: str = os.getenv('MINIO_SECRET_KEY', 'rongce123')
    bucket: str = os.getenv('MINIO_BUCKET', 'rongce-data')
    secure: bool = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

@dataclass
class APIConfig:
    """API服务配置"""
    host: str = os.getenv('API_HOST', '0.0.0.0')
    port: int = int(os.getenv('API_PORT', '5000'))
    debug: bool = os.getenv('API_DEBUG', 'false').lower() == 'true'

# 全局配置实例
db_config = DatabaseConfig()
redis_config = RedisConfig()
minio_config = MinIOConfig()
api_config = APIConfig()
