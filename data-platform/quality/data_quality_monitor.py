"""
融策审计数据中台 - 数据质量监控
实现完整性、准确性、一致性、时效性检查
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
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

class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
    
    def __del__(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def init_default_rules(self):
        """初始化默认数据质量规则"""
        logger.info("初始化默认数据质量规则...")
        
        rules = [
            # ========== 完整性规则 ==========
            {
                'rule_name': '项目编号不能为空',
                'rule_type': '完整性',
                'target_table': 'audit_data.dim_project',
                'target_column': 'project_code',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.dim_project WHERE project_code IS NULL OR project_code = ''",
                'threshold': 100.00,
                'severity': '严重'
            },
            {
                'rule_name': '项目名称不能为空',
                'rule_type': '完整性',
                'target_table': 'audit_data.dim_project',
                'target_column': 'project_name',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.dim_project WHERE project_name IS NULL OR project_name = ''",
                'threshold': 100.00,
                'severity': '严重'
            },
            {
                'rule_name': '客户名称不能为空',
                'rule_type': '完整性',
                'target_table': 'audit_data.dim_client',
                'target_column': 'client_name',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.dim_client WHERE client_name IS NULL OR client_name = ''",
                'threshold': 100.00,
                'severity': '严重'
            },
            {
                'rule_name': '凭证日期不能为空',
                'rule_type': '完整性',
                'target_table': 'audit_data.fact_voucher',
                'target_column': 'voucher_date',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.fact_voucher WHERE voucher_date IS NULL",
                'threshold': 100.00,
                'severity': '严重'
            },
            {
                'rule_name': '凭证分录科目编码不能为空',
                'rule_type': '完整性',
                'target_table': 'audit_data.fact_voucher_entry',
                'target_column': 'subject_code',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.fact_voucher_entry WHERE subject_code IS NULL OR subject_code = ''",
                'threshold': 100.00,
                'severity': '严重'
            },
            
            # ========== 准确性规则 ==========
            {
                'rule_name': '合同金额必须大于0',
                'rule_type': '准确性',
                'target_table': 'audit_data.dim_project',
                'target_column': 'contract_amount',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.dim_project WHERE contract_amount IS NOT NULL AND contract_amount <= 0",
                'threshold': 100.00,
                'severity': '警告'
            },
            {
                'rule_name': '凭证借贷金额必须非负',
                'rule_type': '准确性',
                'target_table': 'audit_data.fact_voucher_entry',
                'target_column': 'debit_amount,credit_amount',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.fact_voucher_entry WHERE debit_amount < 0 OR credit_amount < 0",
                'threshold': 100.00,
                'severity': '严重'
            },
            {
                'rule_name': '项目结束日期不能早于开始日期',
                'rule_type': '准确性',
                'target_table': 'audit_data.dim_project',
                'target_column': 'start_date,end_date',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.dim_project WHERE end_date IS NOT NULL AND start_date IS NOT NULL AND end_date < start_date",
                'threshold': 100.00,
                'severity': '警告'
            },
            {
                'rule_name': '凭证金额必须精确到分',
                'rule_type': '准确性',
                'target_table': 'audit_data.fact_voucher',
                'target_column': 'total_amount',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.fact_voucher WHERE total_amount != ROUND(total_amount, 2)",
                'threshold': 100.00,
                'severity': '提示'
            },
            
            # ========== 一致性规则 ==========
            {
                'rule_name': '项目客户ID必须在客户表中存在',
                'rule_type': '一致性',
                'target_table': 'audit_data.dim_project',
                'target_column': 'client_id',
                'rule_sql': """
                    SELECT COUNT(*) FROM audit_data.dim_project p
                    LEFT JOIN audit_data.dim_client c ON p.client_id = c.client_id
                    WHERE p.client_id IS NOT NULL AND c.client_id IS NULL
                """,
                'threshold': 100.00,
                'severity': '严重'
            },
            {
                'rule_name': '凭证分录的科目编码必须在科目表中存在',
                'rule_type': '一致性',
                'target_table': 'audit_data.fact_voucher_entry',
                'target_column': 'subject_code',
                'rule_sql': """
                    SELECT COUNT(DISTINCT ve.subject_code) FROM audit_data.fact_voucher_entry ve
                    LEFT JOIN audit_data.dim_account_subject s ON ve.subject_code = s.subject_code
                    WHERE s.subject_code IS NULL AND ve.subject_code IS NOT NULL
                """,
                'threshold': 100.00,
                'severity': '严重'
            },
            {
                'rule_name': '凭证借贷必须平衡',
                'rule_type': '一致性',
                'target_table': 'audit_data.fact_voucher',
                'target_column': 'total_amount',
                'rule_sql': """
                    SELECT COUNT(*) FROM audit_data.fact_voucher v
                    WHERE EXISTS (
                        SELECT 1 FROM audit_data.fact_voucher_entry ve
                        WHERE ve.voucher_id = v.voucher_id
                        GROUP BY ve.voucher_id
                        HAVING ABS(SUM(ve.debit_amount) - SUM(ve.credit_amount)) > 0.01
                    )
                """,
                'threshold': 100.00,
                'severity': '严重'
            },
            {
                'rule_name': '项目状态与阶段状态一致',
                'rule_type': '一致性',
                'target_table': 'audit_data.dim_project',
                'target_column': 'status',
                'rule_sql': """
                    SELECT COUNT(*) FROM audit_data.dim_project p
                    WHERE p.status = '已完成'
                    AND EXISTS (
                        SELECT 1 FROM audit_data.fact_project_phase ph
                        WHERE ph.project_id = p.project_id AND ph.status != '已完成'
                    )
                """,
                'threshold': 100.00,
                'severity': '警告'
            },
            
            # ========== 时效性规则 ==========
            {
                'rule_name': '项目数据更新不能超过30天',
                'rule_type': '时效性',
                'target_table': 'audit_data.dim_project',
                'target_column': 'updated_at',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.dim_project WHERE updated_at < CURRENT_DATE - INTERVAL '30 days'",
                'threshold': 95.00,
                'severity': '警告'
            },
            {
                'rule_name': '凭证数据不能超过业务日期7天',
                'rule_type': '时效性',
                'target_table': 'audit_data.fact_voucher',
                'target_column': 'voucher_date',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.fact_voucher WHERE created_at > voucher_date + INTERVAL '7 days'",
                'threshold': 95.00,
                'severity': '提示'
            },
            {
                'rule_name': '政策法规数据需要定期更新',
                'rule_type': '时效性',
                'target_table': 'audit_data.dim_policy',
                'target_column': 'created_at',
                'rule_sql': "SELECT COUNT(*) FROM audit_data.dim_policy WHERE created_at < CURRENT_DATE - INTERVAL '90 days'",
                'threshold': 80.00,
                'severity': '提示'
            }
        ]
        
        # 插入规则
        for rule in rules:
            self.cursor.execute("""
                INSERT INTO data_quality.quality_rules 
                (rule_name, rule_type, target_table, target_column, rule_sql, threshold, severity)
                VALUES (%(rule_name)s, %(rule_type)s, %(target_table)s, %(target_column)s, 
                        %(rule_sql)s, %(threshold)s, %(severity)s)
                ON CONFLICT DO NOTHING
            """, rule)
        
        self.conn.commit()
        logger.info(f"已初始化 {len(rules)} 条数据质量规则")
    
    def run_quality_check(self, rule_id=None, rule_type=None):
        """
        执行数据质量检查
        
        Args:
            rule_id: 指定规则ID，为None则检查所有规则
            rule_type: 指定规则类型，为None则检查所有类型
        """
        logger.info("开始执行数据质量检查...")
        
        # 获取需要执行的规则
        if rule_id:
            self.cursor.execute("""
                SELECT * FROM data_quality.quality_rules 
                WHERE rule_id = %s AND is_active = TRUE
            """, (rule_id,))
        elif rule_type:
            self.cursor.execute("""
                SELECT * FROM data_quality.quality_rules 
                WHERE rule_type = %s AND is_active = TRUE
            """, (rule_type,))
        else:
            self.cursor.execute("""
                SELECT * FROM data_quality.quality_rules WHERE is_active = TRUE
            """)
        
        rules = self.cursor.fetchall()
        results = []
        
        for rule in rules:
            start_time = datetime.now()
            
            try:
                # 获取总记录数
                self.cursor.execute(f"""
                    SELECT COUNT(*) FROM {rule['target_table']}
                """)
                total_records = self.cursor.fetchone()['count']
                
                # 执行质量检查SQL
                self.cursor.execute(rule['rule_sql'])
                failed_records = self.cursor.fetchone()['count']
                
                # 计算通过率
                if total_records > 0:
                    pass_rate = ((total_records - failed_records) / total_records) * 100
                else:
                    pass_rate = 100.0
                
                # 判断是否通过
                status = '通过' if pass_rate >= rule['threshold'] else '失败'
                
                # 记录结果
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                self.cursor.execute("""
                    INSERT INTO data_quality.quality_check_results 
                    (rule_id, check_date, total_records, failed_records, pass_rate, status, duration_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (rule['rule_id'], datetime.now(), total_records, failed_records, 
                      pass_rate, status, int(duration)))
                
                self.conn.commit()
                
                results.append({
                    'rule_id': rule['rule_id'],
                    'rule_name': rule['rule_name'],
                    'rule_type': rule['rule_type'],
                    'status': status,
                    'total_records': total_records,
                    'failed_records': failed_records,
                    'pass_rate': pass_rate,
                    'threshold': rule['threshold'],
                    'duration_ms': int(duration)
                })
                
                logger.info(f"规则 [{rule['rule_name']}] 检查完成: {status} (通过率: {pass_rate:.2f}%)")
                
            except Exception as e:
                logger.error(f"规则 [{rule['rule_name']}] 检查失败: {e}")
                results.append({
                    'rule_id': rule['rule_id'],
                    'rule_name': rule['rule_name'],
                    'rule_type': rule['rule_type'],
                    'status': '错误',
                    'error': str(e)
                })
        
        return results
    
    def get_quality_report(self, start_date=None, end_date=None):
        """
        生成数据质量报告
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # 总体统计
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_checks,
                COUNT(CASE WHEN status = '通过' THEN 1 END) as passed_checks,
                COUNT(CASE WHEN status = '失败' THEN 1 END) as failed_checks,
                AVG(pass_rate) as avg_pass_rate
            FROM data_quality.quality_check_results
            WHERE check_date BETWEEN %s AND %s
        """, (start_date, end_date))
        
        overview = self.cursor.fetchone()
        
        # 按规则类型统计
        self.cursor.execute("""
            SELECT 
                qr.rule_type,
                COUNT(*) as check_count,
                COUNT(CASE WHEN qcr.status = '通过' THEN 1 END) as pass_count,
                AVG(qcr.pass_rate) as avg_pass_rate
            FROM data_quality.quality_check_results qcr
            JOIN data_quality.quality_rules qr ON qcr.rule_id = qr.rule_id
            WHERE qcr.check_date BETWEEN %s AND %s
            GROUP BY qr.rule_type
        """, (start_date, end_date))
        
        type_stats = self.cursor.fetchall()
        
        # 失败的检查详情
        self.cursor.execute("""
            SELECT 
                qr.rule_name,
                qr.rule_type,
                qr.severity,
                qcr.check_date,
                qcr.pass_rate,
                qcr.failed_records
            FROM data_quality.quality_check_results qcr
            JOIN data_quality.quality_rules qr ON qcr.rule_id = qr.rule_id
            WHERE qcr.status = '失败'
            AND qcr.check_date BETWEEN %s AND %s
            ORDER BY qcr.check_date DESC
            LIMIT 20
        """, (start_date, end_date))
        
        failed_details = self.cursor.fetchall()
        
        report = {
            'report_period': {
                'start': str(start_date),
                'end': str(end_date)
            },
            'overview': {
                'total_checks': overview['total_checks'],
                'passed_checks': overview['passed_checks'],
                'failed_checks': overview['failed_checks'],
                'avg_pass_rate': float(overview['avg_pass_rate'] or 0)
            },
            'type_statistics': [
                {
                    'rule_type': r['rule_type'],
                    'check_count': r['check_count'],
                    'pass_count': r['pass_count'],
                    'avg_pass_rate': float(r['avg_pass_rate'] or 0)
                }
                for r in type_stats
            ],
            'failed_details': [
                {
                    'rule_name': r['rule_name'],
                    'rule_type': r['rule_type'],
                    'severity': r['severity'],
                    'check_date': str(r['check_date']),
                    'pass_rate': float(r['pass_rate']),
                    'failed_records': r['failed_records']
                }
                for r in failed_details
            ]
        }
        
        return report
    
    def get_rule_history(self, rule_id, limit=30):
        """
        获取规则历史检查结果
        
        Args:
            rule_id: 规则ID
            limit: 返回记录数
        """
        self.cursor.execute("""
            SELECT check_date, total_records, failed_records, pass_rate, status, duration_ms
            FROM data_quality.quality_check_results
            WHERE rule_id = %s
            ORDER BY check_date DESC
            LIMIT %s
        """, (rule_id, limit))
        
        return [
            {
                'check_date': str(r['check_date']),
                'total_records': r['total_records'],
                'failed_records': r['failed_records'],
                'pass_rate': float(r['pass_rate']),
                'status': r['status'],
                'duration_ms': r['duration_ms']
            }
            for r in self.cursor.fetchall()
        ]

if __name__ == '__main__':
    monitor = DataQualityMonitor()
    
    # 初始化默认规则
    monitor.init_default_rules()
    
    # 执行质量检查
    results = monitor.run_quality_check()
    
    # 生成报告
    report = monitor.get_quality_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
