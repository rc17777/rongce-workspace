"""
融策审计数据中台 - 数据服务API
提供RESTful API接口供上层应用调用
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'rongce'),
    'password': os.getenv('DB_PASSWORD', 'rongce123'),
    'database': os.getenv('DB_NAME', 'rongce_data_platform')
}

def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(**DB_CONFIG)

# ========== 项目数据服务 ==========

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """获取项目列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    project_type = request.args.get('type')
    status = request.args.get('status')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    sql = """
        SELECT p.*, c.client_name 
        FROM audit_data.dim_project p
        LEFT JOIN audit_data.dim_client c ON p.client_id = c.client_id
        WHERE 1=1
    """
    params = []
    
    if project_type:
        sql += " AND p.project_type = %s"
        params.append(project_type)
    
    if status:
        sql += " AND p.status = %s"
        params.append(status)
    
    sql += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, (page - 1) * page_size])
    
    cursor.execute(sql, params)
    projects = cursor.fetchall()
    
    # 获取总数
    cursor.execute("""
        SELECT COUNT(*) FROM audit_data.dim_project p WHERE 1=1
        """)
    total = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'code': 200,
        'data': {
            'items': projects,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project_detail(project_id):
    """获取项目详情"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT p.*, c.client_name, c.client_type
        FROM audit_data.dim_project p
        LEFT JOIN audit_data.dim_client c ON p.client_id = c.client_id
        WHERE p.project_id = %s
    """, (project_id,))
    
    project = cursor.fetchone()
    
    if not project:
        return jsonify({'code': 404, 'message': '项目不存在'}), 404
    
    # 获取项目阶段
    cursor.execute("""
        SELECT * FROM audit_data.fact_project_phase
        WHERE project_id = %s
        ORDER BY phase_order
    """, (project_id,))
    
    phases = cursor.fetchall()
    
    # 获取项目文档
    cursor.execute("""
        SELECT * FROM audit_data.fact_project_document
        WHERE project_id = %s
        ORDER BY upload_time DESC
    """, (project_id,))
    
    documents = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    project['phases'] = phases
    project['documents'] = documents
    
    return jsonify({
        'code': 200,
        'data': project
    })

# ========== 客户数据服务 ==========

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """获取客户列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    client_type = request.args.get('type')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    sql = "SELECT * FROM audit_data.dim_client WHERE 1=1"
    params = []
    
    if client_type:
        sql += " AND client_type = %s"
        params.append(client_type)
    
    sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([page_size, (page - 1) * page_size])
    
    cursor.execute(sql, params)
    clients = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM audit_data.dim_client")
    total = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'code': 200,
        'data': {
            'items': clients,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })

@app.route('/api/clients/<int:client_id>/projects', methods=['GET'])
def get_client_projects(client_id):
    """获取客户的项目列表"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT * FROM audit_data.dim_project
        WHERE client_id = %s
        ORDER BY start_date DESC
    """, (client_id,))
    
    projects = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'code': 200,
        'data': projects
    })

# ========== 政策法规服务 ==========

@app.route('/api/policies', methods=['GET'])
def get_policies():
    """获取政策法规列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword')
    policy_type = request.args.get('type')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    sql = """
        SELECT policy_id, policy_code, policy_name, policy_type, issue_org,
               issue_date, effective_date, status
        FROM audit_data.dim_policy
        WHERE status = '有效'
    """
    params = []
    
    if keyword:
        sql += " AND (policy_name LIKE %s OR content_abstract LIKE %s)"
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    if policy_type:
        sql += " AND policy_type = %s"
        params.append(policy_type)
    
    sql += " ORDER BY issue_date DESC LIMIT %s OFFSET %s"
    params.extend([page_size, (page - 1) * page_size])
    
    cursor.execute(sql, params)
    policies = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'code': 200,
        'data': {
            'items': policies,
            'page': page,
            'page_size': page_size
        }
    })

@app.route('/api/policies/<int:policy_id>', methods=['GET'])
def get_policy_detail(policy_id):
    """获取政策法规详情"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT * FROM audit_data.dim_policy
        WHERE policy_id = %s
    """, (policy_id,))
    
    policy = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not policy:
        return jsonify({'code': 404, 'message': '政策不存在'}), 404
    
    return jsonify({
        'code': 200,
        'data': policy
    })

# ========== 财务数据服务 ==========

@app.route('/api/financial/vouchers', methods=['GET'])
def get_vouchers():
    """获取凭证列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    project_id = request.args.get('project_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    sql = """
        SELECT v.*, p.project_name
        FROM audit_data.fact_voucher v
        LEFT JOIN audit_data.dim_project p ON v.project_id = p.project_id
        WHERE 1=1
    """
    params = []
    
    if project_id:
        sql += " AND v.project_id = %s"
        params.append(project_id)
    
    if start_date:
        sql += " AND v.voucher_date >= %s"
        params.append(start_date)
    
    if end_date:
        sql += " AND v.voucher_date <= %s"
        params.append(end_date)
    
    sql += " ORDER BY v.voucher_date DESC LIMIT %s OFFSET %s"
    params.extend([page_size, (page - 1) * page_size])
    
    cursor.execute(sql, params)
    vouchers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'code': 200,
        'data': {
            'items': vouchers,
            'page': page,
            'page_size': page_size
        }
    })

@app.route('/api/financial/subject-balance', methods=['GET'])
def get_subject_balance():
    """获取科目余额表"""
    project_id = request.args.get('project_id', type=int)
    period = request.args.get('period')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 计算各科目借贷发生额和余额
    cursor.execute("""
        SELECT 
            s.subject_code,
            s.subject_name,
            s.subject_type,
            s.balance_direction,
            COALESCE(SUM(ve.debit_amount), 0) as total_debit,
            COALESCE(SUM(ve.credit_amount), 0) as total_credit,
            CASE 
                WHEN s.balance_direction = '借' THEN COALESCE(SUM(ve.debit_amount), 0) - COALESCE(SUM(ve.credit_amount), 0)
                ELSE COALESCE(SUM(ve.credit_amount), 0) - COALESCE(SUM(ve.debit_amount), 0)
            END as balance
        FROM audit_data.dim_account_subject s
        LEFT JOIN audit_data.fact_voucher_entry ve ON s.subject_code = ve.subject_code
        LEFT JOIN audit_data.fact_voucher v ON ve.voucher_id = v.voucher_id
        WHERE (%s IS NULL OR v.project_id = %s)
          AND (%s IS NULL OR v.accounting_period = %s)
        GROUP BY s.subject_id, s.subject_code, s.subject_name, s.subject_type, s.balance_direction
        ORDER BY s.subject_code
    """, (project_id, project_id, period, period))
    
    balances = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'code': 200,
        'data': balances
    })

# ========== 数据质量服务 ==========

@app.route('/api/quality/check', methods=['POST'])
def run_quality_check():
    """执行数据质量检查"""
    from quality.data_quality_monitor import DataQualityMonitor
    
    monitor = DataQualityMonitor()
    results = monitor.run_quality_check()
    
    return jsonify({
        'code': 200,
        'data': results
    })

@app.route('/api/quality/report', methods=['GET'])
def get_quality_report():
    """获取数据质量报告"""
    from quality.data_quality_monitor import DataQualityMonitor
    
    monitor = DataQualityMonitor()
    report = monitor.get_quality_report()
    
    return jsonify({
        'code': 200,
        'data': report
    })

# ========== 统计分析服务 ==========

@app.route('/api/statistics/project-overview', methods=['GET'])
def get_project_overview():
    """获取项目概览统计"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 总体统计
    cursor.execute("""
        SELECT 
            COUNT(*) as total_projects,
            COUNT(CASE WHEN status = '进行中' THEN 1 END) as active_projects,
            COUNT(CASE WHEN status = '已完成' THEN 1 END) as completed_projects,
            SUM(contract_amount) as total_amount,
            AVG(contract_amount) as avg_amount
        FROM audit_data.dim_project
    """)
    
    overview = cursor.fetchone()
    
    # 按类型统计
    cursor.execute("""
        SELECT project_type, COUNT(*) as count, SUM(contract_amount) as amount
        FROM audit_data.dim_project
        GROUP BY project_type
    """)
    
    type_stats = cursor.fetchall()
    
    # 按月统计
    cursor.execute("""
        SELECT 
            DATE_TRUNC('month', start_date) as month,
            COUNT(*) as count,
            SUM(contract_amount) as amount
        FROM audit_data.dim_project
        WHERE start_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', start_date)
        ORDER BY month
    """)
    
    monthly_stats = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'code': 200,
        'data': {
            'overview': overview,
            'type_statistics': type_stats,
            'monthly_statistics': monthly_stats
        }
    })

@app.route('/api/statistics/client-analysis', methods=['GET'])
def get_client_analysis():
    """获取客户分析"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            c.client_name,
            c.client_type,
            COUNT(p.project_id) as project_count,
            SUM(p.contract_amount) as total_amount,
            MAX(p.end_date) as last_project_date
        FROM audit_data.dim_client c
        LEFT JOIN audit_data.dim_project p ON c.client_id = p.client_id
        GROUP BY c.client_id, c.client_name, c.client_type
        ORDER BY total_amount DESC
    """)
    
    clients = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'code': 200,
        'data': clients
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
