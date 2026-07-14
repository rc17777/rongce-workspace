"""
融策审计数据中台 - 业务数据ETL
支持从工程管理系统、项目管理系统导入业务数据
"""

import os
import json
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, date
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'rongce'),
    'password': os.getenv('DB_PASSWORD', 'rongce123'),
    'database': os.getenv('DB_NAME', 'rongce_data_platform')
}

class BusinessDataETL:
    """业务数据ETL处理器"""
    
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def import_projects_from_excel(self, file_path, sheet_name=0):
        """
        从Excel导入项目数据
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称或索引
        """
        logger.info(f"开始导入项目数据: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 标准化列名映射
        column_mapping = {
            '项目编号': 'project_code',
            '项目名称': 'project_name',
            '项目类型': 'project_type',
            '客户编码': 'client_code',
            '合同金额': 'contract_amount',
            '开始日期': 'start_date',
            '结束日期': 'end_date',
            '项目经理': 'manager_name',
            '状态': 'status'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 获取客户编码到ID的映射
        self.cursor.execute("SELECT client_code, client_id FROM audit_data.dim_client")
        client_map = dict(self.cursor.fetchall())
        
        # 获取项目经理名称到ID的映射（简化处理，实际应从员工表获取）
        manager_map = {}
        
        # 数据清洗和转换
        records = []
        for _, row in df.iterrows():
            client_code = str(row.get('client_code', ''))
            client_id = client_map.get(client_code)
            
            if not client_id:
                logger.warning(f"客户编码 {client_code} 不存在，跳过项目 {row.get('project_code')}")
                continue
            
            # 日期处理
            start_date = self._parse_date(row.get('start_date'))
            end_date = self._parse_date(row.get('end_date'))
            
            records.append((
                str(row['project_code']),
                str(row['project_name']),
                str(row.get('project_type', '其他')),
                client_id,
                float(row.get('contract_amount', 0) or 0),
                start_date,
                end_date,
                str(row.get('status', '进行中'))
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO audit_data.dim_project 
            (project_code, project_name, project_type, client_id, contract_amount, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_code) DO UPDATE SET
                project_name = EXCLUDED.project_name,
                project_type = EXCLUDED.project_type,
                client_id = EXCLUDED.client_id,
                contract_amount = EXCLUDED.contract_amount,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP
        """, records)
        
        self.conn.commit()
        logger.info(f"成功导入/更新 {len(records)} 条项目数据")
        return len(records)
    
    def import_project_phases(self, file_path, sheet_name=0):
        """
        导入项目阶段数据
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称或索引
        """
        logger.info(f"开始导入项目阶段数据: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 标准化列名
        column_mapping = {
            '项目编号': 'project_code',
            '阶段名称': 'phase_name',
            '阶段顺序': 'phase_order',
            '计划开始': 'planned_start',
            '计划结束': 'planned_end',
            '实际开始': 'actual_start',
            '实际结束': 'actual_end',
            '状态': 'status',
            '进度': 'progress'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 获取项目编码到ID的映射
        self.cursor.execute("SELECT project_code, project_id FROM audit_data.dim_project")
        project_map = dict(self.cursor.fetchall())
        
        records = []
        for _, row in df.iterrows():
            project_code = str(row.get('project_code', ''))
            project_id = project_map.get(project_code)
            
            if not project_id:
                logger.warning(f"项目编号 {project_code} 不存在，跳过")
                continue
            
            records.append((
                project_id,
                str(row['phase_name']),
                int(row.get('phase_order', 1)),
                self._parse_date(row.get('planned_start')),
                self._parse_date(row.get('planned_end')),
                self._parse_date(row.get('actual_start')),
                self._parse_date(row.get('actual_end')),
                str(row.get('status', '未开始')),
                float(row.get('progress', 0) or 0)
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO audit_data.fact_project_phase 
            (project_id, phase_name, phase_order, planned_start, planned_end, 
             actual_start, actual_end, status, progress)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, records)
        
        self.conn.commit()
        logger.info(f"成功导入 {len(records)} 条项目阶段数据")
        return len(records)
    
    def import_contracts(self, file_path, sheet_name=0):
        """
        导入合同数据
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称或索引
        """
        logger.info(f"开始导入合同数据: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 标准化列名
        column_mapping = {
            '客户编码': 'client_code',
            '合同编号': 'contract_code',
            '合同名称': 'contract_name',
            '合同类型': 'contract_type',
            '合同金额': 'contract_amount',
            '签订日期': 'sign_date',
            '开始日期': 'start_date',
            '结束日期': 'end_date',
            '状态': 'status'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 获取客户编码到ID的映射
        self.cursor.execute("SELECT client_code, client_id FROM audit_data.dim_client")
        client_map = dict(self.cursor.fetchall())
        
        records = []
        for _, row in df.iterrows():
            client_code = str(row.get('client_code', ''))
            client_id = client_map.get(client_code)
            
            if not client_id:
                logger.warning(f"客户编码 {client_code} 不存在，跳过")
                continue
            
            # 解析付款条款JSON
            payment_terms = {}
            if '付款条款' in row:
                try:
                    payment_terms = json.loads(str(row['付款条款']))
                except:
                    payment_terms = {'terms': str(row.get('付款条款', ''))}
            
            records.append((
                client_id,
                str(row['contract_code']),
                str(row['contract_name']),
                str(row.get('contract_type', '')),
                float(row.get('contract_amount', 0) or 0),
                self._parse_date(row.get('sign_date')),
                self._parse_date(row.get('start_date')),
                self._parse_date(row.get('end_date')),
                json.dumps(payment_terms, ensure_ascii=False),
                str(row.get('status', '生效中'))
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO audit_data.fact_client_contract 
            (client_id, contract_code, contract_name, contract_type, contract_amount,
             sign_date, start_date, end_date, payment_terms, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, records)
        
        self.conn.commit()
        logger.info(f"成功导入 {len(records)} 条合同数据")
        return len(records)
    
    def import_clients(self, file_path, sheet_name=0):
        """
        导入客户数据
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称或索引
        """
        logger.info(f"开始导入客户数据: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 标准化列名
        column_mapping = {
            '客户编码': 'client_code',
            '客户名称': 'client_name',
            '客户简称': 'client_short_name',
            '客户类型': 'client_type',
            '所属行业': 'industry',
            '地区编码': 'region_code',
            '地区名称': 'region_name',
            '地址': 'address',
            '联系人': 'contact_name',
            '联系电话': 'contact_phone',
            '联系邮箱': 'contact_email',
            '信用等级': 'credit_level',
            '合作开始日期': 'cooperation_start'
        }
        
        df = df.rename(columns=column_mapping)
        
        records = []
        for _, row in df.iterrows():
            records.append((
                str(row['client_code']),
                str(row['client_name']),
                str(row.get('client_short_name', '')),
                str(row.get('client_type', '其他')),
                str(row.get('industry', '')),
                str(row.get('region_code', '')),
                str(row.get('region_name', '')),
                str(row.get('address', '')),
                str(row.get('contact_name', '')),
                str(row.get('contact_phone', '')),
                str(row.get('contact_email', '')),
                str(row.get('credit_level', '')),
                self._parse_date(row.get('cooperation_start'))
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO audit_data.dim_client 
            (client_code, client_name, client_short_name, client_type, industry,
             region_code, region_name, address, contact_name, contact_phone,
             contact_email, credit_level, cooperation_start)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (client_code) DO UPDATE SET
                client_name = EXCLUDED.client_name,
                client_short_name = EXCLUDED.client_short_name,
                client_type = EXCLUDED.client_type,
                industry = EXCLUDED.industry,
                region_code = EXCLUDED.region_code,
                region_name = EXCLUDED.region_name,
                address = EXCLUDED.address,
                contact_name = EXCLUDED.contact_name,
                contact_phone = EXCLUDED.contact_phone,
                contact_email = EXCLUDED.contact_email,
                credit_level = EXCLUDED.credit_level,
                cooperation_start = EXCLUDED.cooperation_start,
                updated_at = CURRENT_TIMESTAMP
        """, records)
        
        self.conn.commit()
        logger.info(f"成功导入/更新 {len(records)} 条客户数据")
        return len(records)
    
    def sync_project_progress(self):
        """
        同步项目进度
        根据阶段完成情况计算项目整体进度
        """
        logger.info("开始同步项目进度...")
        
        self.cursor.execute("""
            UPDATE audit_data.dim_project p
            SET status = CASE 
                WHEN all_completed THEN '已完成'
                WHEN has_in_progress THEN '进行中'
                ELSE status
            END
            FROM (
                SELECT 
                    project_id,
                    BOOL_AND(status = '已完成') as all_completed,
                    BOOL_OR(status = '进行中') as has_in_progress
                FROM audit_data.fact_project_phase
                GROUP BY project_id
            ) phase_summary
            WHERE p.project_id = phase_summary.project_id
        """)
        
        self.conn.commit()
        logger.info("项目进度同步完成")
    
    def generate_project_report(self, project_id=None):
        """
        生成项目统计报告
        
        Args:
            project_id: 项目ID，为None则生成所有项目的报告
        """
        logger.info("开始生成项目统计报告...")
        
        # 项目概览统计
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_projects,
                COUNT(CASE WHEN status = '进行中' THEN 1 END) as active_projects,
                COUNT(CASE WHEN status = '已完成' THEN 1 END) as completed_projects,
                SUM(contract_amount) as total_contract_amount,
                AVG(contract_amount) as avg_contract_amount
            FROM audit_data.dim_project
            WHERE (%s IS NULL OR project_id = %s)
        """, (project_id, project_id))
        
        overview = self.cursor.fetchone()
        
        # 项目类型分布
        self.cursor.execute("""
            SELECT project_type, COUNT(*) as count, SUM(contract_amount) as amount
            FROM audit_data.dim_project
            WHERE (%s IS NULL OR project_id = %s)
            GROUP BY project_type
        """, (project_id, project_id))
        
        type_distribution = self.cursor.fetchall()
        
        # 客户分布
        self.cursor.execute("""
            SELECT c.client_name, COUNT(p.project_id) as project_count, SUM(p.contract_amount) as total_amount
            FROM audit_data.dim_project p
            JOIN audit_data.dim_client c ON p.client_id = c.client_id
            WHERE (%s IS NULL OR p.project_id = %s)
            GROUP BY c.client_id, c.client_name
            ORDER BY total_amount DESC
        """, (project_id, project_id))
        
        client_distribution = self.cursor.fetchall()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'overview': {
                'total_projects': overview[0],
                'active_projects': overview[1],
                'completed_projects': overview[2],
                'total_contract_amount': float(overview[3] or 0),
                'avg_contract_amount': float(overview[4] or 0)
            },
            'type_distribution': [
                {'type': r[0], 'count': r[1], 'amount': float(r[2] or 0)} 
                for r in type_distribution
            ],
            'client_distribution': [
                {'client': r[0], 'count': r[1], 'amount': float(r[2] or 0)} 
                for r in client_distribution
            ]
        }
        
        return report
    
    def _parse_date(self, value):
        """解析日期值"""
        if pd.isna(value):
            return None
        if isinstance(value, (datetime, date)):
            return value
        try:
            return pd.to_datetime(value).date()
        except:
            return None

if __name__ == '__main__':
    etl = BusinessDataETL()
    
    # 示例：导入客户数据
    # etl.import_clients('data/clients.xlsx')
    
    # 示例：导入项目数据
    # etl.import_projects_from_excel('data/projects.xlsx')
    
    # 示例：生成项目报告
    # report = etl.generate_project_report()
    # print(json.dumps(report, ensure_ascii=False, indent=2))
