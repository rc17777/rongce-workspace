"""
融策审计数据中台 - 财务数据ETL
支持从Excel/CSV导入财务数据
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
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

class FinancialDataETL:
    """财务数据ETL处理器"""
    
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def import_subject_from_excel(self, file_path, sheet_name=0):
        """
        从Excel导入会计科目
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称或索引
        """
        logger.info(f"开始导入会计科目: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 标准化列名
        column_mapping = {
            '科目编码': 'subject_code',
            '科目名称': 'subject_name',
            '科目类型': 'subject_type',
            '父科目编码': 'parent_code',
            '层级': 'level',
            '余额方向': 'balance_direction'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 数据清洗
        df['subject_code'] = df['subject_code'].astype(str).str.strip()
        df['subject_name'] = df['subject_name'].astype(str).str.strip()
        df['subject_type'] = df['subject_type'].map({
            '资产': '资产', '负债': '负债', '权益': '权益',
            '收入': '收入', '费用': '费用', '成本': '费用'
        }).fillna('资产')
        
        # 批量插入
        records = []
        for _, row in df.iterrows():
            records.append((
                row['subject_code'],
                row['subject_name'],
                row['subject_type'],
                row.get('parent_code'),
                row.get('level', 1),
                row.get('balance_direction', '借')
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO audit_data.dim_account_subject 
            (subject_code, subject_name, subject_type, parent_code, level, balance_direction)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (subject_code) DO UPDATE SET
                subject_name = EXCLUDED.subject_name,
                subject_type = EXCLUDED.subject_type,
                parent_code = EXCLUDED.parent_code,
                level = EXCLUDED.level,
                balance_direction = EXCLUDED.balance_direction
        """, records)
        
        self.conn.commit()
        logger.info(f"成功导入 {len(records)} 条会计科目")
        return len(records)
    
    def import_voucher_from_excel(self, file_path, project_id=None, client_id=None, sheet_name=0):
        """
        从Excel导入会计凭证
        
        Args:
            file_path: Excel文件路径
            project_id: 关联项目ID
            client_id: 关联客户ID
            sheet_name: 工作表名称或索引
        """
        logger.info(f"开始导入会计凭证: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 标准化列名
        column_mapping = {
            '凭证号': 'voucher_no',
            '凭证日期': 'voucher_date',
            '会计期间': 'accounting_period',
            '合计金额': 'total_amount',
            '制单人': 'preparer',
            '审核人': 'reviewer',
            '记账人': 'bookkeeper'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 数据清洗
        df['voucher_date'] = pd.to_datetime(df['voucher_date']).dt.date
        df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)
        
        # 插入凭证主表
        voucher_records = []
        for _, row in df.iterrows():
            voucher_records.append((
                str(row['voucher_no']),
                row['voucher_date'],
                str(row.get('accounting_period', '')),
                project_id,
                client_id,
                float(row['total_amount']),
                str(row.get('preparer', '')),
                str(row.get('reviewer', '')),
                str(row.get('bookkeeper', ''))
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO audit_data.fact_voucher 
            (voucher_no, voucher_date, accounting_period, project_id, client_id, 
             total_amount, preparer, reviewer, bookkeeper)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING voucher_id
        """, voucher_records)
        
        self.conn.commit()
        logger.info(f"成功导入 {len(voucher_records)} 条凭证")
        return len(voucher_records)
    
    def import_voucher_entries(self, file_path, sheet_name=0):
        """
        从Excel导入凭证分录
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称或索引
        """
        logger.info(f"开始导入凭证分录: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 标准化列名
        column_mapping = {
            '凭证号': 'voucher_no',
            '分录序号': 'entry_no',
            '科目编码': 'subject_code',
            '科目名称': 'subject_name',
            '借方金额': 'debit_amount',
            '贷方金额': 'credit_amount',
            '摘要': 'summary'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 数据清洗
        df['debit_amount'] = pd.to_numeric(df['debit_amount'], errors='coerce').fillna(0)
        df['credit_amount'] = pd.to_numeric(df['credit_amount'], errors='coerce').fillna(0)
        
        # 获取凭证号到ID的映射
        self.cursor.execute("SELECT voucher_no, voucher_id FROM audit_data.fact_voucher")
        voucher_map = dict(self.cursor.fetchall())
        
        # 插入分录
        entry_records = []
        for _, row in df.iterrows():
            voucher_no = str(row['voucher_no'])
            if voucher_no in voucher_map:
                entry_records.append((
                    voucher_map[voucher_no],
                    int(row['entry_no']),
                    str(row['subject_code']),
                    str(row.get('subject_name', '')),
                    float(row['debit_amount']),
                    float(row['credit_amount']),
                    str(row.get('summary', ''))
                ))
        
        execute_batch(self.cursor, """
            INSERT INTO audit_data.fact_voucher_entry 
            (voucher_id, entry_no, subject_code, subject_name, debit_amount, credit_amount, summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, entry_records)
        
        self.conn.commit()
        logger.info(f"成功导入 {len(entry_records)} 条凭证分录")
        return len(entry_records)
    
    def import_balance_sheet(self, file_path, project_id=None, period=None, sheet_name=0):
        """
        导入资产负债表数据
        
        Args:
            file_path: Excel文件路径
            project_id: 项目ID
            period: 会计期间
            sheet_name: 工作表名称或索引
        """
        logger.info(f"开始导入资产负债表: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 创建临时表存储余额数据
        self.cursor.execute("""
            CREATE TEMP TABLE IF NOT EXISTS temp_balance (
                subject_code VARCHAR(50),
                subject_name VARCHAR(200),
                opening_balance DECIMAL(18,2),
                closing_balance DECIMAL(18,2),
                period VARCHAR(20)
            )
        """)
        
        # 清空临时表
        self.cursor.execute("TRUNCATE temp_balance")
        
        # 插入数据到临时表
        records = []
        for _, row in df.iterrows():
            records.append((
                str(row.get('科目编码', '')),
                str(row.get('科目名称', '')),
                float(row.get('期初余额', 0) or 0),
                float(row.get('期末余额', 0) or 0),
                period or str(row.get('会计期间', ''))
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO temp_balance (subject_code, subject_name, opening_balance, closing_balance, period)
            VALUES (%s, %s, %s, %s, %s)
        """, records)
        
        self.conn.commit()
        logger.info(f"成功导入 {len(records)} 条余额数据")
        return len(records)
    
    def validate_financial_data(self, project_id=None):
        """
        验证财务数据完整性
        
        Args:
            project_id: 项目ID，为None则验证所有数据
        """
        logger.info("开始验证财务数据...")
        
        checks = []
        
        # 检查1: 凭证借贷平衡
        self.cursor.execute("""
            SELECT v.voucher_no, v.total_amount,
                   COALESCE(SUM(ve.debit_amount), 0) as total_debit,
                   COALESCE(SUM(ve.credit_amount), 0) as total_credit
            FROM audit_data.fact_voucher v
            LEFT JOIN audit_data.fact_voucher_entry ve ON v.voucher_id = ve.voucher_id
            WHERE (%s IS NULL OR v.project_id = %s)
            GROUP BY v.voucher_id, v.voucher_no, v.total_amount
            HAVING ABS(COALESCE(SUM(ve.debit_amount), 0) - COALESCE(SUM(ve.credit_amount), 0)) > 0.01
        """, (project_id, project_id))
        
        unbalanced = self.cursor.fetchall()
        if unbalanced:
            checks.append({
                'check': '借贷平衡检查',
                'status': '失败',
                'details': f'发现 {len(unbalanced)} 条借贷不平衡的凭证',
                'records': [{'voucher_no': r[0], 'total': float(r[1]), 'debit': float(r[2]), 'credit': float(r[3])} for r in unbalanced[:5]]
            })
        else:
            checks.append({
                'check': '借贷平衡检查',
                'status': '通过',
                'details': '所有凭证借贷平衡'
            })
        
        # 检查2: 科目编码有效性
        self.cursor.execute("""
            SELECT DISTINCT ve.subject_code
            FROM audit_data.fact_voucher_entry ve
            WHERE NOT EXISTS (
                SELECT 1 FROM audit_data.dim_account_subject s 
                WHERE s.subject_code = ve.subject_code
            )
        """)
        
        invalid_subjects = self.cursor.fetchall()
        if invalid_subjects:
            checks.append({
                'check': '科目编码有效性',
                'status': '失败',
                'details': f'发现 {len(invalid_subjects)} 个无效科目编码',
                'records': [{'subject_code': r[0]} for r in invalid_subjects]
            })
        else:
            checks.append({
                'check': '科目编码有效性',
                'status': '通过',
                'details': '所有科目编码有效'
            })
        
        # 检查3: 凭证日期合理性
        self.cursor.execute("""
            SELECT voucher_no, voucher_date
            FROM audit_data.fact_voucher
            WHERE voucher_date > CURRENT_DATE
               OR voucher_date < '2000-01-01'
        """)
        
        invalid_dates = self.cursor.fetchall()
        if invalid_dates:
            checks.append({
                'check': '凭证日期合理性',
                'status': '警告',
                'details': f'发现 {len(invalid_dates)} 条日期异常的凭证',
                'records': [{'voucher_no': r[0], 'date': str(r[1])} for r in invalid_dates[:5]]
            })
        else:
            checks.append({
                'check': '凭证日期合理性',
                'status': '通过',
                'details': '所有凭证日期合理'
            })
        
        return checks

if __name__ == '__main__':
    etl = FinancialDataETL()
    
    # 示例：导入会计科目
    # etl.import_subject_from_excel('data/subjects.xlsx')
    
    # 示例：导入凭证
    # etl.import_voucher_from_excel('data/vouchers.xlsx', project_id=1, client_id=1)
    
    # 示例：验证数据
    results = etl.validate_financial_data()
    for result in results:
        print(f"{result['check']}: {result['status']} - {result['details']}")
