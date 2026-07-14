"""
融策审计数据中台 - 外部数据采集ETL
采集政策法规、招投标信息、工商信息等外部数据
"""

import os
import json
import time
import requests
import psycopg2
from psycopg2.extras import execute_batch
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

class ExternalDataCollector:
    """外部数据采集器"""
    
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def __del__(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def collect_policy_from_file(self, file_path):
        """
        从本地文件导入政策法规
        支持JSON、Excel格式
        
        Args:
            file_path: 文件路径
        """
        logger.info(f"开始导入政策法规: {file_path}")
        
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                policies = json.load(f)
        elif file_path.endswith(('.xlsx', '.xls')):
            import pandas as pd
            df = pd.read_excel(file_path)
            policies = df.to_dict('records')
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
        
        records = []
        for policy in policies:
            records.append((
                str(policy.get('policy_code', '')),
                str(policy.get('policy_name', '')),
                str(policy.get('policy_type', '其他')),
                str(policy.get('issue_org', '')),
                self._parse_date(policy.get('issue_date')),
                self._parse_date(policy.get('effective_date')),
                self._parse_date(policy.get('expire_date')),
                str(policy.get('industry_scope', '')),
                str(policy.get('content_abstract', '')),
                str(policy.get('full_text', '')),
                json.dumps(policy.get('keywords', []), ensure_ascii=False),
                str(policy.get('status', '有效')),
                str(policy.get('source_url', ''))
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO audit_data.dim_policy 
            (policy_code, policy_name, policy_type, issue_org, issue_date,
             effective_date, expire_date, industry_scope, content_abstract,
             full_text, keywords, status, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, records)
        
        self.conn.commit()
        logger.info(f"成功导入 {len(records)} 条政策法规")
        return len(records)
    
    def collect_policy_from_website(self, url_template, page_range, delay=1):
        """
        从网站采集政策法规（示例框架）
        
        Args:
            url_template: URL模板，如 'http://example.com/policies?page={page}'
            page_range: 页码范围，如 range(1, 11)
            delay: 请求间隔秒数
        """
        logger.info(f"开始从网站采集政策法规: {url_template}")
        
        all_policies = []
        
        for page in page_range:
            url = url_template.format(page=page)
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # 解析HTML（需要根据具体网站定制）
                # 这里使用简化的示例
                policies = self._parse_policy_html(response.text)
                all_policies.extend(policies)
                
                logger.info(f"第 {page} 页采集完成，获取 {len(policies)} 条数据")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"采集第 {page} 页失败: {e}")
                continue
        
        # 保存到数据库
        if all_policies:
            self.collect_policy_from_file(
                self._save_to_temp_json(all_policies)
            )
        
        return len(all_policies)
    
    def collect_bidding_info(self, keywords, days=30):
        """
        采集招投标信息（示例框架）
        
        Args:
            keywords: 关键词列表
            days: 最近多少天的数据
        """
        logger.info(f"开始采集招投标信息，关键词: {keywords}")
        
        # 这里应该对接实际的招投标API
        # 示例使用模拟数据
        bidding_data = []
        
        for keyword in keywords:
            # 模拟API调用
            logger.info(f"搜索关键词: {keyword}")
            # 实际实现需要对接具体的数据源
            pass
        
        return bidding_data
    
    def collect_company_info(self, company_names):
        """
        采集企业工商信息（示例框架）
        
        Args:
            company_names: 企业名称列表
        """
        logger.info(f"开始采集企业信息: {company_names}")
        
        # 这里应该对接天眼查/企查查等API
        # 示例框架
        company_data = []
        
        for name in company_names:
            logger.info(f"查询企业: {name}")
            # 实际实现需要对接具体的API
            pass
        
        return company_data
    
    def update_policy_status(self):
        """
        更新政策法规状态
        检查已过期或已废止的政策
        """
        logger.info("开始更新政策法规状态...")
        
        # 标记已过期的政策
        self.cursor.execute("""
            UPDATE audit_data.dim_policy
            SET status = '已废止'
            WHERE expire_date IS NOT NULL 
              AND expire_date < CURRENT_DATE
              AND status = '有效'
        """)
        
        expired_count = self.cursor.rowcount
        
        self.conn.commit()
        logger.info(f"已标记 {expired_count} 条过期政策")
        return expired_count
    
    def search_policies(self, keywords=None, policy_type=None, issue_org=None, 
                       start_date=None, end_date=None, status='有效'):
        """
        搜索政策法规
        
        Args:
            keywords: 关键词列表
            policy_type: 政策类型
            issue_org: 发布机关
            start_date: 开始日期
            end_date: 结束日期
            status: 状态
        """
        sql = """
            SELECT policy_id, policy_code, policy_name, policy_type, issue_org,
                   issue_date, effective_date, status, content_abstract
            FROM audit_data.dim_policy
            WHERE 1=1
        """
        params = []
        
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append("(policy_name LIKE %s OR content_abstract LIKE %s)")
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            sql += " AND (" + " OR ".join(keyword_conditions) + ")"
        
        if policy_type:
            sql += " AND policy_type = %s"
            params.append(policy_type)
        
        if issue_org:
            sql += " AND issue_org LIKE %s"
            params.append(f'%{issue_org}%')
        
        if start_date:
            sql += " AND issue_date >= %s"
            params.append(start_date)
        
        if end_date:
            sql += " AND issue_date <= %s"
            params.append(end_date)
        
        if status:
            sql += " AND status = %s"
            params.append(status)
        
        sql += " ORDER BY issue_date DESC LIMIT 100"
        
        self.cursor.execute(sql, params)
        
        columns = [desc[0] for desc in self.cursor.description]
        results = []
        
        for row in self.cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def get_policy_timeline(self, category=None, limit=50):
        """
        获取政策法规时间线
        
        Args:
            category: 分类
            limit: 返回数量
        """
        self.cursor.execute("""
            SELECT policy_name, issue_date, policy_type, status
            FROM audit_data.dim_policy
            WHERE (%s IS NULL OR policy_type = %s)
            ORDER BY issue_date DESC
            LIMIT %s
        """, (category, category, limit))
        
        return [
            {
                'policy_name': r[0],
                'issue_date': str(r[1]),
                'policy_type': r[2],
                'status': r[3]
            }
            for r in self.cursor.fetchall()
        ]
    
    def _parse_date(self, value):
        """解析日期"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        try:
            return datetime.strptime(str(value), '%Y-%m-%d').date()
        except:
            try:
                return datetime.strptime(str(value), '%Y/%m/%d').date()
            except:
                return None
    
    def _parse_policy_html(self, html):
        """解析政策HTML（需要根据具体网站实现）"""
        # 这里需要根据实际网站结构实现
        # 使用BeautifulSoup等库解析
        return []
    
    def _save_to_temp_json(self, data):
        """保存数据到临时JSON文件"""
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        return temp_file.name

if __name__ == '__main__':
    collector = ExternalDataCollector()
    
    # 示例：从文件导入政策
    # collector.collect_policy_from_file('data/policies.json')
    
    # 示例：搜索政策
    # results = collector.search_policies(keywords=['财政', '审计'])
    # print(json.dumps(results, ensure_ascii=False, indent=2))
    
    # 示例：更新政策状态
    # collector.update_policy_status()
