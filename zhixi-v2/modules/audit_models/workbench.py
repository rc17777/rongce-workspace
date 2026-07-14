# 智析智能体 v2.0 — 审计模型工作台
# 资产来源: bid-document 技能中31个审计SQL模型 + audit-data-analysis-methods 7大方法

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

# ============================================================
# 31个审计SQL模型（直接内嵌自 bid-document SKILL.md）
# ============================================================

AUDIT_SQL_MODELS = {
    # ---- 一、预算执行审计 ----
    "M001": {
        "name": "预算执行率异常",
        "category": "预算执行审计",
        "sql": "SELECT 项目名称, (支出金额/预算金额) as 执行率 FROM 预算执行表 WHERE 执行率 < 0.5 OR 执行率 > 0.95",
        "description": "识别预算执行率低于50%或高于95%的异常项目",
        "params": ["budget_table", "expense_col", "budget_col"],
    },
    "M002": {
        "name": "年底突击花钱",
        "category": "预算执行审计",
        "sql": "SELECT 摘要, 金额, 支出日期 FROM 凭证表 WHERE 支出日期 BETWEEN '12-20' AND '12-31' AND 金额 > 10000",
        "description": "识别12月20日后大额支出，发现年底突击花钱",
        "params": ["voucher_table", "date_col", "amount_col", "threshold"],
    },
    "M003": {
        "name": "向实有资金账户划款",
        "category": "预算执行审计",
        "sql": "SELECT 收款人账号, 收款人名称, 金额 FROM 支付表 WHERE 收款人账号 LIKE '____%'",
        "description": "识别零余额账户向实有资金账户划款",
        "params": ["payment_table", "account_col"],
    },
    "M004": {
        "name": "细项超预算",
        "category": "预算执行审计",
        "sql": "SELECT 预算科目, 预算金额, SUM(支出金额) as 实际支出 FROM 预算执行表 GROUP BY 预算科目, 预算金额 HAVING SUM(支出金额) > 预算金额",
        "description": "识别预算科目实际支出超预算",
        "params": ["budget_exec_table", "budget_item_col", "budget_col", "expense_col"],
    },
    "M005": {
        "name": "无预算支出",
        "category": "预算执行审计",
        "sql": "SELECT 摘要, 金额, 支出日期 FROM 凭证表 WHERE 预算项目代码 IS NULL",
        "description": "识别无预算项目的支出",
        "params": ["voucher_table", "budget_code_col"],
    },
    "M006": {
        "name": "两年以上结转存量资金",
        "category": "预算执行审计",
        "sql": "SELECT 项目名称, 结转金额, 结转年度 FROM 结转结余表 WHERE DATEDIFF(year, 结转年度, GETDATE()) >= 2",
        "description": "识别两年以上未使用的结转资金",
        "params": ["rollover_table", "year_col"],
    },
    
    # ---- 二、政府采购审计 ----
    "M007": {
        "name": "同一IP多家投标",
        "category": "政府采购审计",
        "sql": "SELECT 投标IP, COUNT(DISTINCT 投标单位) AS 单位数, GROUP_CONCAT(DISTINCT 投标单位) AS 单位名单 FROM 投标记录表 GROUP BY 投标IP HAVING COUNT(DISTINCT 投标单位) > 1",
        "description": "识别围标嫌疑：同一IP地址多家单位投标",
        "params": ["bid_record_table", "ip_col", "bidder_col"],
    },
    "M008": {
        "name": "拆分项目规避招标",
        "category": "政府采购审计",
        "sql": "SELECT 采购单位, 采购品目, 年份, COUNT(*) AS 采购次数, SUM(合同金额) AS 总金额 FROM 采购合同表 WHERE 合同金额 < 招标限额 GROUP BY 采购单位, 采购品目, 年份 HAVING COUNT(*) > 5 AND SUM(合同金额) > 招标限额 * 0.8",
        "description": "识别同一品目多次小额采购，总分超招标限额",
        "params": ["procurement_table", "department_col", "category_col", "amount_col", "limit_amount"],
    },
    "M009": {
        "name": "价格偏离度",
        "category": "政府采购审计",
        "sql": "SELECT 品目名称, 采购单位, 供应商, 单价, (SELECT AVG(单价) FROM 采购明细 WHERE 品目名称 = m.品目名称) AS 平均价, 单价/(SELECT AVG(单价) FROM 采购明细 WHERE 品目名称 = m.品目名称) AS 偏离倍数 FROM 采购明细 m WHERE 单价 > (SELECT AVG(单价)*1.3 FROM 采购明细 WHERE 品目名称 = m.品目名称)",
        "description": "识别采购单价偏离市场均价30%以上",
        "params": ["procurement_detail_table", "item_col", "price_col"],
    },
    
    # ---- 三、信息系统与网络安全审计 ----
    "M010": {"name": "僵尸账号(>90天未登录)", "category": "信息系统审计", "sql": "SELECT 用户名, 姓名, 部门, 角色, 最后登录时间 FROM 系统用户表 WHERE DATEDIFF(day, 最后登录时间, GETDATE()) > 90 AND 账号状态 = '正常'", "description": "识别长期未登录的活跃账号", "params": ["user_table", "last_login_col"]},
    "M011": {"name": "离职人员未销号", "category": "信息系统审计", "sql": "SELECT u.用户名, u.姓名, u.部门 FROM 系统用户表 u LEFT JOIN 在职人员表 r ON u.姓名 = r.姓名 AND u.部门 = r.部门 WHERE r.姓名 IS NULL", "description": "识别已离职但账号未注销的用户", "params": ["user_table", "employee_table"]},
    "M012": {"name": "非工作时间登录", "category": "信息系统审计", "sql": "SELECT 用户名, 登录时间, 登录IP FROM 登录日志 WHERE DATEPART(hour, 登录时间) BETWEEN 0 AND 6 OR DATEPART(hour, 登录时间) BETWEEN 22 AND 23", "description": "识别深夜登录异常行为", "params": ["login_log_table"]},
    "M013": {"name": "敏感数据访问审计", "category": "信息系统审计", "sql": "SELECT 用户名, 操作时间, SQL语句, 影响行数 FROM 数据库审计日志 WHERE SQL语句 LIKE '%身份证%' OR SQL语句 LIKE '%bank_account%' OR SQL语句 LIKE '%password%'", "description": "监控敏感数据访问行为", "params": ["db_audit_table"]},
    
    # ---- 四、跨部门数据比对 ----
    "M014": {"name": "违规经商办企业", "category": "跨部门比对", "sql": "SELECT p.姓名, p.身份证号, p.单位 FROM 财政供养人员表 p INNER JOIN 工商登记表 b ON p.身份证号 = b.法定代表人身份证", "description": "识别财政供养人员违规担任企业法人", "params": ["fiscal_staff_table", "business_reg_table"]},
    "M015": {"name": "死亡人员领补贴", "category": "跨部门比对", "sql": "SELECT m.姓名, m.身份证号, p.补贴项目, p.发放金额, p.发放时间 FROM 死亡人员表 m INNER JOIN 补贴发放表 p ON m.身份证号 = p.身份证号 WHERE p.发放时间 > m.死亡时间", "description": "识别死亡后继续领取补贴", "params": ["death_table", "subsidy_table"]},
    "M016": {"name": "超编配车", "category": "跨部门比对", "sql": "SELECT d.单位名称, d.车辆编制数, COUNT(s.车牌号) AS 实有车辆数 FROM 单位车辆编制表 d LEFT JOIN 车辆台账 s ON d.单位名称 = s.所属单位 GROUP BY d.单位名称, d.车辆编制数 HAVING COUNT(s.车牌号) > d.车辆编制数", "description": "识别超编制配备公务车辆", "params": ["car_quota_table", "car_ledger_table"]},
    
    # ---- 五、专项资金审计 ----
    "M017": {"name": "财政供养人员领惠农补贴", "category": "专项资金审计", "sql": "SELECT 补贴表.*, 供养表.单位名称 FROM 补贴发放表 补贴表 INNER JOIN 财政供养人员表 供养表 ON 补贴表.身份证号 = 供养表.身份证号 WHERE 补贴表.补贴年度 = '2025' AND 补贴表.补贴类型 IN ('耕地地力补贴', '低保')", "description": "识别财政供养人员违规领取惠农补贴/低保", "params": ["subsidy_table", "fiscal_staff_table", "year"]},
    "M018": {"name": "申报面积超确权面积", "category": "专项资金审计", "sql": "SELECT 申报表.农户姓名, 申报表.身份证号, 申报表.申报面积, 确权表.确权面积, (申报面积 - 确权面积) as 超报面积 FROM 补贴申报表 申报表 INNER JOIN 土地确权表 确权表 ON 申报表.身份证号 = 确权表.身份证号 WHERE 申报表.申报面积 > 确权表.确权面积 * 1.1", "description": "识别惠农补贴虚报面积", "params": ["application_table", "land_rights_table"]},
    "M019": {"name": "资金滞留(>6个月)", "category": "专项资金审计", "sql": "SELECT 拨付表.资金文号, 拨付表.收款单位, 拨付表.拨付金额, DATEDIFF(month, 拨付表.拨付时间, 支付表.支付时间) as 滞留月数 FROM 财政拨付表 拨付表 LEFT JOIN 单位支付表 支付表 ON 拨付表.资金文号 = 支付表.资金来源文号 WHERE 支付表.支付时间 IS NULL OR DATEDIFF(month, 拨付表.拨付时间, 支付表.支付时间) > 6", "description": "识别资金滞留超6个月未拨付", "params": ["fiscal_disbursement_table", "payment_table"]},
    "M020": {"name": "专项资金用于三公经费", "category": "专项资金审计", "sql": "SELECT 凭证表.摘要, 凭证表.金额, 凭证表.科目代码 FROM 单位凭证表 凭证表 WHERE 凭证表.资金来源 LIKE '%专项资金%' AND 凭证表.科目代码 IN ('30212', '30215')", "description": "识别专项资金挪用为三公经费", "params": ["voucher_table", "fund_source_col"]},
    
    # ---- 六、国有企业审计 ----
    "M021": {"name": "采购价格偏离监测", "category": "国企审计", "sql": "SELECT d.采购物料, d.采购单价, j.监测价格, (d.采购单价 - j.监测价格)/j.监测价格 AS 偏离率 FROM 采购明细 d INNER JOIN 政府价格监测 j ON d.物料名称 = j.物料名称 AND d.采购时间 = j.监测月份 WHERE ABS((d.采购单价 - j.监测价格)/j.监测价格) > 0.3", "description": "识别国企采购价格偏离市场价格30%以上", "params": ["procurement_detail", "price_monitor"]},
    "M022": {"name": "供应商法人代表为国企人员", "category": "国企审计", "sql": "SELECT g.姓名, g.工作单位, s.供应商名称, s.法定代表人 FROM 国企人员表 g INNER JOIN 供应商表 s ON g.身份证号 = s.法定代表人身份证", "description": "识别国企人员开办供应商利益输送", "params": ["soe_staff_table", "supplier_table"]},
    
    # ---- 七、经济责任审计 ----
    "M023": {"name": "科目年度增长率Z值异常", "category": "经济责任审计", "sql": "SELECT 年份, 科目名称, 金额, (金额 - LAG(金额) OVER(ORDER BY 年份)) / LAG(金额) OVER(ORDER BY 年份) AS 增长率 FROM 科目余额表 HAVING ABS(增长率) > 2", "description": "识别科目年度增长率异常（变通列支）", "params": ["account_balance_table"]},
    "M024": {"name": "银行存款活期占比过高", "category": "经济责任审计", "sql": "SELECT 公司名称, AVG(月末余额) AS 月均余额, SUM(CASE WHEN 存款类型='活期' THEN 月末余额 ELSE 0 END) / SUM(月末余额) AS 活期占比 FROM 银行存款明细账 GROUP BY 公司名称 HAVING 活期占比 > 0.7", "description": "识别资金闲置：活期存款占比超过70%", "params": ["bank_deposit_table"]},
    
    # ---- 八、自然资源与生态环境审计 ----
    "M025": {"name": "审批用地超出开发边界", "category": "自然资源审计", "sql": "SELECT 项目名称, 审批面积 FROM 用地审批表 WHERE 边界内面积 / 审批面积 < 0.9", "description": "识别审批用地超出城镇开发边界", "params": ["land_approval_table"]},
    "M026": {"name": "排放物超标", "category": "自然资源审计", "sql": "SELECT 企业名称, 排放物, 实际排放量, 许可排放量 FROM 企业排放监测表 WHERE 实际排放量 > 许可排放量", "description": "识别企业排放物超标", "params": ["emission_monitor_table"]},
    
    # ---- 九、医保基金审计 ----
    "M027": {"name": "死亡人员仍领医保待遇", "category": "医保审计", "sql": "SELECT a.person_id, a.name, a.hospital_name, a.settle_date, b.death_date, a.total_fee, a.fund_pay FROM settle_detail a LEFT JOIN police_death b ON a.id_card = b.id_card WHERE a.settle_date > b.death_date AND a.fund_pay > 0", "description": "识别死亡后仍在结算医保", "params": ["settle_table", "death_table"]},
    "M028": {"name": "单日多机构结算", "category": "医保审计", "sql": "SELECT id_card, name, COUNT(DISTINCT hospital_id) AS hospital_cnt, COUNT(*) AS settle_cnt, SUM(fund_pay) AS total_pay FROM settle_detail GROUP BY id_card, name HAVING COUNT(DISTINCT hospital_id) >= 3 OR COUNT(*) >= 20", "description": "识别同一人单日多机构就诊（骗保疑点）", "params": ["settle_table"]},
    "M029": {"name": "分解住院/挂床住院", "category": "医保审计", "sql": "SELECT patient_id, name, hospital_name, admit_date, discharge_date, DATEDIFF(day, LAG(discharge_date) OVER (PARTITION BY patient_id ORDER BY admit_date), admit_date) AS days_between FROM his_inpatient WHERE DATEDIFF(day, admit_date, discharge_date) < 3 OR DATEDIFF(day, LAG(discharge_date) OVER (PARTITION BY patient_id ORDER BY admit_date), admit_date) <= 7", "description": "识别住院<3天或出院7天内再入院", "params": ["inpatient_table"]},
    
    # ---- 十、审计方法分析模型（audit-data-analysis-methods） ----
    "M030": {"name": "Benford定律第一数字分布", "category": "审计分析方法", "sql": "SELECT LEFT(CAST(金额 AS VARCHAR), 1) AS 首数字, COUNT(*) AS 频次, COUNT(*)*100.0/SUM(COUNT(*)) OVER() AS 占比 FROM 财务数据表 WHERE 金额 > 0 GROUP BY LEFT(CAST(金额 AS VARCHAR), 1) ORDER BY 首数字", "description": "Benford定律检测数值伪造", "params": ["financial_table", "amount_col"]},
    "M031": {"name": "Z-Score异常值检测", "category": "审计分析方法", "sql": "SELECT *, (金额 - AVG(金额) OVER()) / STDEV(金额) OVER() AS Z值 FROM 财务数据表 HAVING ABS(Z值) > 3", "description": "Z-Score法检测数值异常", "params": ["table_name", "amount_col"]},
}


@dataclass
class AuditModel:
    id: str
    name: str
    category: str
    sql_template: str
    description: str
    params: List[str]
    
class ModelWorkbench:
    """审计模型工作台"""
    
    def __init__(self):
        self.models: Dict[str, AuditModel] = {}
        self._load_builtin_models()
    
    def _load_builtin_models(self):
        for mid, m in AUDIT_SQL_MODELS.items():
            self.models[mid] = AuditModel(
                id=mid, name=m["name"], category=m["category"],
                sql_template=m["sql"], description=m["description"],
                params=m.get("params", [])
            )
    
    def list_models(self, category: str = None) -> List[Dict]:
        result = []
        for mid, m in self.models.items():
            if category and m.category != category:
                continue
            result.append({
                "id": mid, "name": m.name, "category": m.category,
                "description": m.description, "params": m.params
            })
        return result
    
    def list_categories(self) -> List[str]:
        return sorted(set(m.category for m in self.models.values()))
    
    def get_model(self, model_id: str) -> Optional[AuditModel]:
        return self.models.get(model_id)
    
    def build_sql(self, model_id: str, params: Dict[str, str] = None) -> str:
        """根据参数替换SQL模板"""
        model = self.get_model(model_id)
        if not model:
            raise ValueError(f"模型不存在: {model_id}")
        sql = model.sql_template
        if params:
            for k, v in params.items():
                sql = sql.replace(k, str(v))
        return sql
    
    def search(self, keyword: str) -> List[Dict]:
        kw = keyword.lower()
        result = []
        for mid, m in self.models.items():
            if kw in m.name.lower() or kw in m.description.lower() or kw in m.category.lower():
                result.append({
                    "id": mid, "name": m.name, "category": m.category, "description": m.description
                })
        return result


# ============================================================
# 7大数据分析方法模板（audit-data-analysis-methods）
# ============================================================

ANALYSIS_METHODS = {
    "descriptive": {
        "name": "描述性统计",
        "description": "对审计数据进行汇总统计，了解数据分布特征",
        "techniques": ["均值/中位数/众数", "标准差/方差", "频次分布", "百分位数", "偏度/峰度"],
        "audit_use": "快速了解资金规模、支出结构、异常分布",
        "tools": ["pd.DataFrame.describe()", "pd.DataFrame.value_counts()", "numpy.percentile()"],
    },
    "correlation": {
        "name": "相关性分析",
        "description": "分析变量之间的关联关系，发现隐藏的业务逻辑",
        "techniques": ["Pearson相关系数", "Spearman秩相关", "交叉表分析"],
        "audit_use": "发现指标间异常关系（如收入增长但税收下降）",
        "tools": ["pd.DataFrame.corr()", "pd.crosstab()", "scipy.stats"],
    },
    "regression": {
        "name": "回归分析",
        "description": "建立变量间定量关系模型，预测和发现偏离",
        "techniques": ["线性回归", "多元回归", "残差分析"],
        "audit_use": "建立支出预测模型，发现超出预期的支出项",
    },
    "clustering": {
        "name": "聚类分析",
        "description": "将相似对象分组，发现数据内在结构",
        "techniques": ["K-Means", "DBSCAN", "层次聚类"],
        "audit_use": "对供应商/项目/单位分类，识别离群群体",
    },
    "anomaly_detection": {
        "name": "异常检测",
        "description": "识别偏离正常模式的数据点",
        "techniques": ["Z-Score", "IQR", "Isolation Forest", "LOF"],
        "audit_use": "自动识别异常交易、虚报、错误数据",
    },
    "association": {
        "name": "关联规则与网络分析",
        "description": "发现数据项之间的关联模式和网络关系",
        "techniques": ["Apriori算法", "FP-Growth", "网络中心性分析"],
        "audit_use": "围标串标识别、供应商关系图谱、利益输送链条",
    },
    "time_series": {
        "name": "时间序列分析",
        "description": "分析时序数据的趋势、周期和异常",
        "techniques": ["移动平均", "同比/环比", "季节性分解", "断点检测"],
        "audit_use": "资金使用节奏分析、收入趋势异常、年底突击花钱检测",
    },
}
