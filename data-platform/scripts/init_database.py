"""
融策审计数据中台 - 数据库初始化脚本
创建所有数据标准定义的数据表
"""

import os
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'rongce'),
    'password': os.getenv('DB_PASSWORD', 'rongce123'),
    'database': os.getenv('DB_NAME', 'rongce_data_platform')
}

def create_database():
    """创建数据库"""
    conn = psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # 检查数据库是否存在
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_CONFIG['database']}'")
    if not cursor.fetchone():
        cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']} ENCODING 'UTF8' LC_COLLATE 'zh_CN.UTF-8'")
        print(f"数据库 {DB_CONFIG['database']} 创建成功")
    else:
        print(f"数据库 {DB_CONFIG['database']} 已存在")
    
    cursor.close()
    conn.close()

def create_tables():
    """创建数据表"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 启用UUID扩展
    cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    
    # 创建schema
    cursor.execute("CREATE SCHEMA IF NOT EXISTS audit_data")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS data_quality")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS metadata")
    
    # ========== 审计项目数据 ==========
    
    # 项目主数据
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.dim_project (
            project_id BIGSERIAL PRIMARY KEY,
            project_code VARCHAR(50) UNIQUE NOT NULL,
            project_name VARCHAR(200) NOT NULL,
            project_type VARCHAR(50) NOT NULL CHECK (project_type IN ('绩效评价', '资产清查', '专项债', '监督检查', '其他')),
            client_id BIGINT,
            contract_amount DECIMAL(18,2),
            start_date DATE,
            end_date DATE,
            status VARCHAR(20) DEFAULT '进行中' CHECK (status IN ('进行中', '已完成', '已终止')),
            manager_id BIGINT,
            team_members JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 项目阶段跟踪
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.fact_project_phase (
            phase_id BIGSERIAL PRIMARY KEY,
            project_id BIGINT NOT NULL REFERENCES audit_data.dim_project(project_id),
            phase_name VARCHAR(50) NOT NULL,
            phase_order INTEGER NOT NULL,
            planned_start DATE,
            planned_end DATE,
            actual_start DATE,
            actual_end DATE,
            status VARCHAR(20) DEFAULT '未开始' CHECK (status IN ('未开始', '进行中', '已完成', '已延期')),
            progress DECIMAL(5,2) DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 项目文档
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.fact_project_document (
            document_id BIGSERIAL PRIMARY KEY,
            project_id BIGINT NOT NULL REFERENCES audit_data.dim_project(project_id),
            document_type VARCHAR(50) NOT NULL,
            document_name VARCHAR(200) NOT NULL,
            file_path VARCHAR(500),
            file_size BIGINT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploader_id BIGINT
        )
    """)
    
    # ========== 客户主数据 ==========
    
    # 客户主数据
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.dim_client (
            client_id BIGSERIAL PRIMARY KEY,
            client_code VARCHAR(50) UNIQUE NOT NULL,
            client_name VARCHAR(200) NOT NULL,
            client_short_name VARCHAR(50),
            client_type VARCHAR(50) CHECK (client_type IN ('政府机关', '事业单位', '国企', '民企', '其他')),
            industry VARCHAR(50),
            region_code VARCHAR(20),
            region_name VARCHAR(100),
            address VARCHAR(500),
            contact_name VARCHAR(100),
            contact_phone VARCHAR(50),
            contact_email VARCHAR(100),
            credit_level VARCHAR(20),
            cooperation_start DATE,
            status VARCHAR(20) DEFAULT '活跃' CHECK (status IN ('活跃', '暂停', '终止')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 客户合同
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.fact_client_contract (
            contract_id BIGSERIAL PRIMARY KEY,
            client_id BIGINT NOT NULL REFERENCES audit_data.dim_client(client_id),
            contract_code VARCHAR(50) NOT NULL,
            contract_name VARCHAR(200) NOT NULL,
            contract_type VARCHAR(50),
            contract_amount DECIMAL(18,2),
            sign_date DATE,
            start_date DATE,
            end_date DATE,
            payment_terms JSONB DEFAULT '{}',
            status VARCHAR(20) DEFAULT '生效中' CHECK (status IN ('生效中', '已履行', '已终止'))
        )
    """)
    
    # ========== 政策法规数据 ==========
    
    # 政策分类
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.dim_policy_category (
            category_id BIGSERIAL PRIMARY KEY,
            category_code VARCHAR(50) NOT NULL,
            category_name VARCHAR(100) NOT NULL,
            parent_id BIGINT REFERENCES audit_data.dim_policy_category(category_id),
            level INTEGER DEFAULT 1,
            description VARCHAR(500)
        )
    """)
    
    # 政策法规
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.dim_policy (
            policy_id BIGSERIAL PRIMARY KEY,
            policy_code VARCHAR(50),
            policy_name VARCHAR(500) NOT NULL,
            policy_type VARCHAR(50) CHECK (policy_type IN ('法律', '法规', '规章', '规范性文件', '其他')),
            issue_org VARCHAR(200),
            issue_date DATE,
            effective_date DATE,
            expire_date DATE,
            industry_scope VARCHAR(200),
            content_abstract TEXT,
            full_text TEXT,
            keywords JSONB DEFAULT '[]',
            status VARCHAR(20) DEFAULT '有效' CHECK (status IN ('有效', '已废止', '已修订')),
            source_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ========== 财务数据 ==========
    
    # 会计科目
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.dim_account_subject (
            subject_id BIGSERIAL PRIMARY KEY,
            subject_code VARCHAR(50) NOT NULL,
            subject_name VARCHAR(200) NOT NULL,
            subject_type VARCHAR(50) CHECK (subject_type IN ('资产', '负债', '权益', '收入', '费用')),
            parent_code VARCHAR(50),
            level INTEGER DEFAULT 1,
            balance_direction VARCHAR(10) CHECK (balance_direction IN ('借', '贷'))
        )
    """)
    
    # 会计凭证
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.fact_voucher (
            voucher_id BIGSERIAL PRIMARY KEY,
            voucher_no VARCHAR(50) NOT NULL,
            voucher_date DATE NOT NULL,
            accounting_period VARCHAR(20) NOT NULL,
            project_id BIGINT REFERENCES audit_data.dim_project(project_id),
            client_id BIGINT REFERENCES audit_data.dim_client(client_id),
            total_amount DECIMAL(18,2) NOT NULL,
            preparer VARCHAR(100),
            reviewer VARCHAR(100),
            bookkeeper VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 凭证分录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_data.fact_voucher_entry (
            entry_id BIGSERIAL PRIMARY KEY,
            voucher_id BIGINT NOT NULL REFERENCES audit_data.fact_voucher(voucher_id),
            entry_no INTEGER NOT NULL,
            subject_code VARCHAR(50) NOT NULL,
            subject_name VARCHAR(200),
            debit_amount DECIMAL(18,2) DEFAULT 0,
            credit_amount DECIMAL(18,2) DEFAULT 0,
            summary VARCHAR(500),
            auxiliary_info JSONB DEFAULT '{}'
        )
    """)
    
    # ========== 数据质量监控表 ==========
    
    # 数据质量规则
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_quality.quality_rules (
            rule_id BIGSERIAL PRIMARY KEY,
            rule_name VARCHAR(200) NOT NULL,
            rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('完整性', '准确性', '一致性', '时效性')),
            target_table VARCHAR(100) NOT NULL,
            target_column VARCHAR(100),
            rule_sql TEXT NOT NULL,
            threshold DECIMAL(5,2) DEFAULT 100.00,
            severity VARCHAR(20) DEFAULT '警告' CHECK (severity IN ('提示', '警告', '严重')),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 数据质量检查结果
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_quality.quality_check_results (
            result_id BIGSERIAL PRIMARY KEY,
            rule_id BIGINT NOT NULL REFERENCES data_quality.quality_rules(rule_id),
            check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_records BIGINT,
            failed_records BIGINT,
            pass_rate DECIMAL(5,2),
            status VARCHAR(20) CHECK (status IN ('通过', '失败')),
            error_details JSONB DEFAULT '[]',
            duration_ms INTEGER
        )
    """)
    
    # ========== 元数据管理表 ==========
    
    # 数据资产目录
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata.data_assets (
            asset_id BIGSERIAL PRIMARY KEY,
            asset_name VARCHAR(200) NOT NULL,
            asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('表', '视图', '字段', '报表')),
            schema_name VARCHAR(50),
            table_name VARCHAR(100),
            column_name VARCHAR(100),
            description TEXT,
            owner VARCHAR(100),
            sensitivity_level VARCHAR(20) DEFAULT '内部' CHECK (sensitivity_level IN ('公开', '内部', '机密', '绝密')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 数据血缘关系
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata.data_lineage (
            lineage_id BIGSERIAL PRIMARY KEY,
            source_asset_id BIGINT REFERENCES metadata.data_assets(asset_id),
            target_asset_id BIGINT REFERENCES metadata.data_assets(asset_id),
            transformation_logic TEXT,
            etl_job_name VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_client ON audit_data.dim_project(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_status ON audit_data.dim_project(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_type ON audit_data.dim_project(project_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_voucher_date ON audit_data.fact_voucher(voucher_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_voucher_project ON audit_data.fact_voucher(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_type ON audit_data.dim_policy(policy_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_status ON audit_data.dim_policy(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_type ON audit_data.dim_client(client_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_rule_type ON data_quality.quality_rules(rule_type)")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("所有数据表创建完成")

def init_sample_data():
    """初始化示例数据"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 初始化客户数据
    cursor.execute("""
        INSERT INTO audit_data.dim_client (client_code, client_name, client_short_name, client_type, industry, region_name, status)
        VALUES 
            ('C001', '成都市财政局', '成都财政', '政府机关', '财政', '成都市', '活跃'),
            ('C002', '四川省教育厅', '省教育厅', '政府机关', '教育', '成都市', '活跃'),
            ('C003', '四川某国有企业', '某国企', '国企', '建筑', '成都市', '活跃')
        ON CONFLICT (client_code) DO NOTHING
    """)
    
    # 初始化项目数据
    cursor.execute("""
        INSERT INTO audit_data.dim_project (project_code, project_name, project_type, client_id, contract_amount, start_date, end_date, status)
        VALUES 
            ('P2024001', '2024年度绩效评价项目', '绩效评价', 1, 500000, '2024-01-01', '2024-06-30', '已完成'),
            ('P2024002', '国有资产清查项目', '资产清查', 2, 300000, '2024-03-01', '2024-09-30', '进行中')
        ON CONFLICT (project_code) DO NOTHING
    """)
    
    # 初始化政策分类
    cursor.execute("""
        INSERT INTO audit_data.dim_policy_category (category_code, category_name, level, description)
        VALUES 
            ('CAT001', '财政法规', 1, '财政相关法律法规'),
            ('CAT002', '审计准则', 1, '审计相关准则规范'),
            ('CAT003', '工程法规', 1, '工程建设相关法规')
        ON CONFLICT DO NOTHING
    """)
    
    # 初始化会计科目
    cursor.execute("""
        INSERT INTO audit_data.dim_account_subject (subject_code, subject_name, subject_type, level, balance_direction)
        VALUES 
            ('1001', '库存现金', '资产', 1, '借'),
            ('1002', '银行存款', '资产', 1, '借'),
            ('1122', '应收账款', '资产', 1, '借'),
            ('2202', '应付账款', '负债', 1, '贷'),
            ('6001', '主营业务收入', '收入', 1, '贷'),
            ('6401', '主营业务成本', '费用', 1, '借')
        ON CONFLICT DO NOTHING
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("示例数据初始化完成")

if __name__ == '__main__':
    print(f"[{datetime.now()}] 开始初始化数据库...")
    create_database()
    create_tables()
    init_sample_data()
    print(f"[{datetime.now()}] 数据库初始化完成")
