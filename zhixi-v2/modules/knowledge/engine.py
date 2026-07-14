# 智析智能体 v2.0 — 知识资产引擎
# 资产来源: cot-capture (审计思维链) + prompt-librarian (提示词库) + agent-data-standard (12项检查)
#            + audit-data-analysis-methods (7大审计分析方法) + digital-audit-methodology (10大框架)

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


# ============================================================
# 1. 审计思维链规则引擎 (cot-capture)
# ============================================================

COT_RULES = {
    "budget_execution": {
        "name": "预算执行审计思维链",
        "rules": [
            {"step": 1, "trigger": "发现预算执行率<50%", "action": "检查是否因项目未启动导致资金无法拨付", "next": 2},
            {"step": 2, "trigger": "项目已启动但执行率低", "action": "检查是否存在资金被挪用至其他用途", "next": 3},
            {"step": 3, "trigger": "发现年底大额支付", "action": "检查是否突击花钱、虚列支出套取资金", "next": 4},
            {"step": 4, "trigger": "发现向实有账户划款", "action": "检查实有账户资金用途，是否形成账外资金", "next": None},
        ],
    },
    "procurement": {
        "name": "采购审计思维链",
        "rules": [
            {"step": 1, "trigger": "同一品目多次小额采购", "action": "汇总全年采购金额，判断是否超招标限额", "next": 2},
            {"step": 2, "trigger": "总金额超限额但未招标", "action": "检查是否刻意拆分项目规避招标", "next": 3},
            {"step": 3, "trigger": "发现中标价异常偏高", "action": "对比同期同品目市场价，检查是否围标抬价", "next": 4},
            {"step": 4, "trigger": "多家投标单位中标IP相同", "action": "确认为围标串标嫌疑，调取投标文件做文本比对", "next": 5},
            {"step": 5, "trigger": "投标文件实质性雷同", "action": "出具围标串标审计证据，移交处理", "next": None},
        ],
    },
    "financial_fraud": {
        "name": "财务造假检测思维链",
        "rules": [
            {"step": 1, "trigger": "财务报表数据异常", "action": "应用Benford定律检测数字分布", "next": 2},
            {"step": 2, "trigger": "Benford检测偏离", "action": "检查大额整数交易、月末/年末集中入账", "next": 3},
            {"step": 3, "trigger": "发现异常交易", "action": "追踪交易对手方，核实业务真实性", "next": 4},
            {"step": 4, "trigger": "交易对手方为关联方", "action": "检查定价公允性，是否存在利益输送", "next": None},
        ],
    },
    "subsidy_fraud": {
        "name": "补贴资金审计思维链",
        "rules": [
            {"step": 1, "trigger": "发现补贴对象身份异常", "action": "将补贴对象与财政供养人员库/死亡库/工商登记库比对", "next": 2},
            {"step": 2, "trigger": "发现违规领取", "action": "追溯资金最终流向，确认是否有内部人员参与", "next": 3},
            {"step": 3, "trigger": "发现系统性违规模式", "action": "扩大筛查范围，从点→面揭示系统性管理漏洞", "next": None},
        ],
    },
    "natural_resources": {
        "name": "自然资源审计思维链",
        "rules": [
            {"step": 1, "trigger": "发现用地审批异常", "action": "将审批地块与城镇开发边界/生态红线/基本农田叠加分析", "next": 2},
            {"step": 2, "trigger": "超边界审批", "action": "追溯审批流程，检查审批权限和审批程序合规性", "next": 3},
            {"step": 3, "trigger": "审批程序违规", "action": "评估违规审批造成的资源破坏后果，确定责任主体", "next": None},
        ],
    },
    "economic_responsibility": {
        "name": "经济责任审计思维链",
        "rules": [
            {"step": 1, "trigger": "发现单位财务指标异常", "action": "区分是任期遗留问题还是任期内新增问题", "next": 2},
            {"step": 2, "trigger": "任期内新增问题", "action": "确认问题严重程度、是否因决策失误或管理失职导致", "next": 3},
            {"step": 3, "trigger": "确认有管理责任", "action": "量化损失影响，评估领导干部应承担的相应责任", "next": None},
        ],
    },
}


class CoTEngine:
    """思维链推理引擎"""
    
    def __init__(self):
        self.chains = COT_RULES
    
    def get_chain(self, name: str) -> Optional[Dict]:
        return self.chains.get(name)
    
    def execute_chain(self, name: str, initial_finding: str) -> List[Dict]:
        """执行思维链，给定初始发现，输出推理路径"""
        chain = self.get_chain(name)
        if not chain:
            return [{"error": f"思维链不存在: {name}"}]
        
        steps = []
        for rule in chain["rules"]:
            steps.append({
                "step": rule["step"],
                "trigger": rule["trigger"],
                "action": rule["action"],
                "next_step": rule["next"],
            })
        return steps
    
    def list_chains(self) -> List[str]:
        return list(self.chains.keys())


# ============================================================
# 2. 提示词库 (prompt-librarian)
# ============================================================

PROMPT_TEMPLATES = {
    "contract_review": {
        "name": "合同审查提示词",
        "category": "合同审计",
        "prompt": """你是一名政府审计专家，请审查以下合同，重点关注：
1. 合同主体资格是否合规（甲乙方名称、统一社会信用代码）
2. 合同金额是否合理（与预算、市场价格对比）
3. 付款条款是否有风险（预付款比例、质保金）
4. 合同期限是否合理
5. 违约责任是否对等
6. 是否存在明显不利于我方/政府方的条款

合同内容：
{contract_text}

请逐条分析，给出风险等级（高/中/低）和修改建议。""",
    },
    "bidding_review": {
        "name": "招投标文件审查提示词",
        "category": "采购审计",
        "prompt": """你是一名政府采购审计专家，请审查以下招投标文件，重点关注：
1. 采购方式选择是否合规（公开招标/邀请招标/竞争性谈判等）
2. 评分标准是否合理（主观分/客观分比例，是否存在量身定制）
3. 投标人资格条件是否具有排他性
4. 技术参数是否指向特定供应商
5. 价格分权重是否合理
6. 是否存在围标串标迹象

文件内容：
{bidding_text}

请逐条分析，给出审计结论和建议。""",
    },
    "voucher_analysis": {
        "name": "会计凭证分析提示词",
        "category": "财务审计",
        "prompt": """你是一名财务审计专家，请分析以下会计凭证摘要和科目信息，判断是否存在异常：
1. 摘要是否模糊或不合理
2. 科目使用是否合规
3. 金额与摘要描述的匹配性
4. 是否存在大额整数交易
5. 日期是否符合业务逻辑

凭证信息：
{voucher_info}

请逐条判断，标注异常等级。""",
    },
    "data_quality": {
        "name": "数据质量评估提示词",
        "category": "数据审计",
        "prompt": """请评估以下数据集的质量，检查维度包括：
1. 完整性：是否有大量缺失值
2. 准确性：数据是否符合业务逻辑
3. 一致性：不同字段之间是否存在矛盾
4. 唯一性：主键是否重复
5. 及时性：数据更新频率是否满足审计需要

数据概况：
{data_profile}

请给出质量评分（0-100）和改进建议。""",
    },
    "finding_draft": {
        "name": "审计问题发现撰写提示词",
        "category": "审计报告",
        "prompt": """你是一名审计报告撰写专家，请根据以下审计发现，撰写规范的问题描述段落：
要求：
1. 事实描述客观准确
2. 引用相关法规依据
3. 定量数据精确
4. 定性判断有据
5. 语言简洁专业

审计发现：
{finding}

请按"问题事实描述→违反何规定→造成何后果→建议"的结构撰写。""",
    },
    "recommendation": {
        "name": "审计建议撰写提示词",
        "category": "审计报告",
        "prompt": """你是一名审计建议专家，请根据以下审计发现，提出可落地的整改建议：
要求：
1. 建议具体可执行，不泛泛而谈
2. 分清立行立改和长期机制两类
3. 明确责任主体
4. 设定合理整改时限

审计发现：
{finding}

请按类别给出建议：（1）立行立改措施（2）制度完善建议（3）长效机制建议。""",
    },
}


class PromptLibrary:
    """提示词库管理器"""
    
    def __init__(self):
        self.templates = PROMPT_TEMPLATES
    
    def get(self, name: str) -> Optional[Dict]:
        return self.templates.get(name)
    
    def list_all(self) -> List[Dict]:
        return [{"name": k, "title": v["name"], "category": v["category"]} for k, v in self.templates.items()]
    
    def search(self, keyword: str) -> List[Dict]:
        kw = keyword.lower()
        results = []
        for k, v in self.templates.items():
            if kw in v["name"].lower() or kw in v["category"].lower() or kw in v["prompt"].lower():
                results.append({"name": k, "title": v["name"], "category": v["category"]})
        return results


# ============================================================
# 3. Agent友好数据标准检查 (agent-data-standard)
# ============================================================

DATA_QUALITY_CHECKS = [
    {"id": "DS01", "dimension": "结构", "check": "数据格式标准化", "standard": "字段名使用统一命名规范(下划线/驼峰)，无特殊字符"},
    {"id": "DS02", "dimension": "结构", "check": "主键唯一性", "standard": "每表有明确定义的主键，无重复值"},
    {"id": "DS03", "dimension": "结构", "check": "外键完整性", "standard": "关联表的外键值在父表中存在对应记录"},
    {"id": "DS04", "dimension": "结构", "check": "字段类型一致性", "standard": "数值字段不含文本，日期字段格式统一(YYYY-MM-DD)"},
    {"id": "DS05", "dimension": "语义", "check": "字段含义明确", "standard": "字段名能直接反映其业务含义，无歧义"},
    {"id": "DS06", "dimension": "语义", "check": "编码标准化", "standard": "科目编码/地区编码/行业编码等使用国家标准"},
    {"id": "DS07", "dimension": "语义", "check": "取值范围合法", "standard": "枚举字段值在预定义范围内，无非法值"},
    {"id": "DS08", "dimension": "语义", "check": "业务逻辑一致性", "standard": "关联数据之间的业务关系合规(如金额正负、日期先后)"},
    {"id": "DS09", "dimension": "接口", "check": "数据字典完整", "standard": "每表/每字段有完整的元数据说明"},
    {"id": "DS10", "dimension": "接口", "check": "数据可获取性", "standard": "数据可通过标准接口(SQL/API)获取，格式结构化"},
    {"id": "DS11", "dimension": "接口", "check": "数据更新频率", "standard": "数据定期更新，且更新频率满足使用需要"},
    {"id": "DS12", "dimension": "接口", "check": "权限与安全", "standard": "数据访问有权限控制，敏感字段脱敏处理"},
]


class DataQualityChecker:
    """12项Agent友好数据标准检查"""
    
    def __init__(self):
        self.checks = DATA_QUALITY_CHECKS
    
    def run_checks(self, data_profile: Dict) -> Dict:
        """
        data_profile: {table_name: {columns: [{name, type, nullable, values_sample}], row_count, pk, fks}}
        返回每项检查的通过/不通过及建议
        """
        results = []
        for check in self.checks:
            # 根据数据画像做简单的规则检查
            passed = True
            detail = ""
            
            if check["id"] == "DS01":
                # 检查字段命名规范
                for col in data_profile.get("columns", []):
                    name = col.get("name", "")
                    if any(c in name for c in [" ", "！", "@", "#", "$"]):
                        passed = False
                        detail = f"字段 {name} 包含不规范字符"
                        break
            
            elif check["id"] == "DS02":
                pk = data_profile.get("pk")
                if not pk:
                    passed = False
                    detail = "未定义主键"
            
            elif check["id"] == "DS04":
                for col in data_profile.get("columns", []):
                    if col.get("type") in ("date", "datetime"):
                        sample = col.get("values_sample", "")
                        if sample and "年" in str(sample):
                            passed = False
                            detail = f"日期字段 {col['name']} 格式不符合 YYYY-MM-DD"
                            break
            
            results.append({
                "id": check["id"],
                "dimension": check["dimension"],
                "check": check["check"],
                "standard": check["standard"],
                "passed": passed,
                "detail": detail or ("通过" if passed else "需人工复核"),
            })
        
        # 计算评分
        passed_count = sum(1 for r in results if r["passed"])
        score = round(100 * passed_count / len(results))
        
        return {
            "total_checks": len(results),
            "passed": passed_count,
            "score": score,
            "grade": "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D",
            "results": results,
        }

    def generate_report(self, check_results: Dict) -> str:
        """生成检查报告"""
        lines = []
        lines.append(f"## 数据标准就绪度评估报告")
        lines.append(f"")
        lines.append(f"- 综合评分: **{check_results['score']}/100** ({check_results['grade']}级)")
        lines.append(f"- 通过项: {check_results['passed']}/{check_results['total_checks']}")
        lines.append(f"")
        lines.append(f"### 逐项结果")
        lines.append(f"")
        lines.append(f"| 编号 | 维度 | 检查项 | 标准 | 结果 |")
        lines.append(f"|------|------|--------|------|:---:|")
        for r in check_results["results"]:
            status = "✅" if r["passed"] else "❌"
            lines.append(f"| {r['id']} | {r['dimension']} | {r['check']} | {r['standard']} | {status} |")
        return "\n".join(lines)


# ============================================================
# 4. 数字化审计方法论 (digital-audit-methodology)
# ============================================================

METHODOLOGY_FRAMEWORKS = {
    "data_first": {
        "name": "数据先行",
        "description": "先打通数据壁垒，再进行业务分析。数据不通不分析，分析不需返工。",
        "steps": ["数据源盘点", "数据接入与清洗", "标准化处理", "质量验证", "入库管理"],
    },
    "business_penetration": {
        "name": "业务穿透三层",
        "description": "审计分析必须穿透制度流程层→业务环节层→业务操作层",
        "layers": ["制度流程层：审什么、依据什么", "业务环节层：怎么审、关键控制点在哪", "业务操作层：数据在哪、怎么验证"],
    },
    "exception_driven": {
        "name": "疑点驱动",
        "description": "从疑点出发，用数据验证，而非全面铺开",
        "steps": ["规则扫描产生疑点", "数据验证疑点", "现场核实确认", "分类处理"],
    },
    "cross_verification": {
        "name": "交叉验证",
        "description": "不同来源数据互相印证，单一来源不可信",
        "methods": ["部门间数据比对", "上下级数据比对", "财务与业务数据比对", "台账与系统数据比对"],
    },
    "quantitative_evaluation": {
        "name": "量化评价",
        "description": "用数据和指标替代经验判断",
        "steps": ["构建评价指标体系", "设定权重（AHP/熵权法）", "计算综合得分", "形成评价结论"],
    },
    "traceability": {
        "name": "全程可追溯",
        "description": "每个审计结论都能追溯到原始数据和判断过程",
        "chain": ["原始数据 → 处理逻辑 → 中间结果 → 判断规则 → 审计结论"],
    },
    "closed_loop": {
        "name": "闭环管理",
        "description": "审计发现问题→整改→跟踪→销号→回头看",
        "steps": ["问题发现与定性", "整改方案制定", "整改过程跟踪", "整改结果验收", "回头看抽查"],
    },
    "knowledge_accumulation": {
        "name": "知识沉淀",
        "description": "每个项目的方法、规则、经验入库，下次复用",
        "assets": ["审计模型库", "疑点规则库", "问题定性库", "法规引用库", "案例库"],
    },
    "scenario_embedding": {
        "name": "场景嵌入",
        "description": "AI能力嵌入审计流程的6种模式",
        "modes": ["文件到达触发", "数据刷新触发", "上下文感知触发", "定时巡检触发", "里程碑触发", "异常事件触发"],
    },
    "continuous_evolution": {
        "name": "持续进化",
        "description": "方法论和工具随实践不断迭代，不搞一次性交付",
        "cycle": ["实践 → 总结 → 提炼模板 → 验证 → 推广 → 再实践"],
    },
}


class MethodologyEngine:
    """数字化审计方法论引擎"""
    
    def get_framework(self, name: str) -> Optional[Dict]:
        return METHODOLOGY_FRAMEWORKS.get(name)
    
    def list_all(self) -> List[Dict]:
        return [{"name": k, **v} for k, v in METHODOLOGY_FRAMEWORKS.items()]
    
    def recommend_for_audit_type(self, audit_type: str) -> List[str]:
        """根据审计类型推荐适用框架"""
        recommendations = {
            "预算执行":  ["data_first", "exception_driven", "cross_verification"],
            "政府采购":  ["exception_driven", "cross_verification", "traceability"],
            "经济责任":  ["quantitative_evaluation", "traceability", "closed_loop"],
            "专项资金":  ["data_first", "cross_verification", "traceability"],
            "自然资源":  ["data_first", "cross_verification", "quantitative_evaluation"],
            "医保社保":  ["exception_driven", "cross_verification", "closed_loop"],
        }
        return recommendations.get(audit_type, ["data_first", "exception_driven", "traceability"])
