"""
工具5：budget_compliance_scan — 关键词+规则预算合规校验

场景：预算执行审计、三公经费审计、专项资金审计中，
     全量扫描报销文本，识别超标接待、私车公养、违规采购等
"""

import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field, asdict

from .utils import clean_text


# ── 内置审计合规规则库 ────────────────────────────────────────

_DEFAULT_RULES = {
    "keywords": [
        # 三公经费
        {"keyword": "超标接待", "severity": "high",
         "description": "接待费超过规定标准"},
        {"keyword": "违规接待", "severity": "high",
         "description": "违反公务接待管理规定"},
        {"keyword": "高档烟酒", "severity": "high",
         "description": "购买高档烟酒可能违反八项规定"},
        {"keyword": "会所", "severity": "high",
         "description": "在私人会所消费"},
        {"keyword": "高消费", "severity": "high",
         "description": "高消费场所开支"},
        # 车辆
        {"keyword": "私车公养", "severity": "high",
         "description": "私人车辆费用公款报销"},
        {"keyword": "油卡", "severity": "medium",
         "description": "加油卡管理不规范"},
        {"keyword": "ETC充值", "severity": "medium",
         "description": "ETC大额充值需关注使用情况"},
        {"keyword": "维修", "severity": "low",
         "description": "车辆维修费关注合理性和审批"},
        # 采购
        {"keyword": "拆分采购", "severity": "high",
         "description": "拆分采购规避招标"},
        {"keyword": "围标", "severity": "high",
         "description": "围标串标行为"},
        {"keyword": "单一来源", "severity": "medium",
         "description": "单一来源采购需审批"},
        {"keyword": "礼品", "severity": "high",
         "description": "公款购买礼品"},
        {"keyword": "购物卡", "severity": "high",
         "description": "公款购买购物卡/预付卡"},
        # 资金
        {"keyword": "挪用", "severity": "high",
         "description": "挪用专项资金"},
        {"keyword": "套取", "severity": "high",
         "description": "虚构交易套取资金"},
        {"keyword": "白条", "severity": "medium",
         "description": "白条抵账/无正式发票"},
        {"keyword": "现金支付", "severity": "medium",
         "description": "大额现金支付不规范"},
        {"keyword": "预付", "severity": "medium",
         "description": "大额预付款关注资金安全和审批"},
        # 差旅
        {"keyword": "超标准住宿", "severity": "medium",
         "description": "住宿费超过差旅标准"},
        {"keyword": "绕道", "severity": "medium",
         "description": "差旅绕道可能涉及公款旅游"},
        # 会议/培训
        {"keyword": "以会代训", "severity": "medium",
         "description": "变相公款旅游"},
        {"keyword": "培训班", "severity": "low",
         "description": "培训班关注必要性和费用合理性"},
    ],
    "patterns": [
        # 正则模式
        {"pattern": r"[¥￥](\d{5,})\s*[元]?", "severity": "medium",
         "description": "单笔5万元以上大额支出"},
        {"pattern": r"(?:餐饮|招待|宴请).*?[¥￥](\d{4,})", "severity": "high",
         "description": "餐饮/招待单笔超千元"},
        {"pattern": r"(?:预付|预付款).*?[¥￥](\d{5,})", "severity": "high",
         "description": "大额预付款"},
        {"pattern": r"无(?:合同|发票|审批)", "severity": "high",
         "description": "无合同/发票/审批的支出"},
        {"pattern": r"(?:连号|连续).*?(?:发票|票据)", "severity": "medium",
         "description": "连号发票可能涉及拆分报销"},
        {"pattern": r"(?:周末|节假日|休息日).*?(?:出差|差旅)", "severity": "low",
         "description": "休息日出差需关注真实性"},
    ],
    "limits": {
        # 限额规则
        "差旅费": {"per_day": 800, "severity_override": "medium"},
        "办公耗材": {"per_transaction": 5000, "severity_override": "low"},
        "会议费": {"per_person_day": 500, "severity_override": "medium"},
        "培训费": {"per_person_day": 400, "severity_override": "medium"},
    },
}


@dataclass
class BudgetViolation:
    index: int
    violation_type: str  # keyword_hit | pattern_match | limit_exceeded | custom
    rule_description: str
    original_text: str
    severity: str
    matched_pattern: str = ""
    amount: Optional[float] = None


@dataclass
class BudgetResult:
    violations: List[BudgetViolation]
    total_expenses: int
    violation_count: int
    violation_by_severity: Dict[str, int]
    violation_by_type: Dict[str, int]


class BudgetComplianceScanner:
    """预算合规扫描器"""

    def scan(
        self,
        expense_texts: List[str],
        rule_set: Optional[Dict[str, Any]] = None,
        custom_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> BudgetResult:
        """
        预算合规扫描

        Args:
            expense_texts: 报销备注/凭证文本数组
            rule_set: 自定义规则集，不传则使用内置默认规则
            custom_rules: 额外自定义规则，合并到规则集中

        Returns:
            BudgetResult
        """
        rules = self._load_rules(rule_set, custom_rules)
        violations = []

        for idx, text in enumerate(expense_texts):
            cleaned = clean_text(text)

            # 关键词扫描
            for kw_rule in rules.get("keywords", []):
                if kw_rule["keyword"] in cleaned:
                    violations.append(BudgetViolation(
                        index=idx,
                        violation_type="keyword_hit",
                        rule_description=kw_rule["description"],
                        original_text=text,
                        severity=kw_rule["severity"],
                        matched_pattern=kw_rule["keyword"],
                    ))

            # 正则模式扫描
            for pat_rule in rules.get("patterns", []):
                match = re.search(pat_rule["pattern"], cleaned)
                if match:
                    amount = None
                    try:
                        amount = float(match.group(1))
                    except (IndexError, ValueError):
                        pass

                    violations.append(BudgetViolation(
                        index=idx,
                        violation_type="pattern_match",
                        rule_description=pat_rule["description"],
                        original_text=text,
                        severity=pat_rule["severity"],
                        matched_pattern=pat_rule["pattern"],
                        amount=amount,
                    ))

            # 限额规则扫描
            for limit_name, limit_rule in rules.get("limits", {}).items():
                if limit_name in cleaned:
                    amount = self._extract_amount(cleaned)
                    if amount is not None:
                        per_day = limit_rule.get("per_day")
                        per_transaction = limit_rule.get("per_transaction")
                        per_person_day = limit_rule.get("per_person_day")

                        exceeded = False
                        if per_day and amount > per_day:
                            exceeded = True
                        if per_transaction and amount > per_transaction:
                            exceeded = True
                        if per_person_day and amount > per_person_day:
                            exceeded = True

                        if exceeded:
                            violations.append(BudgetViolation(
                                index=idx,
                                violation_type="limit_exceeded",
                                rule_description=f"{limit_name}超过限额",
                                original_text=text,
                                severity=limit_rule.get(
                                    "severity_override", "medium"
                                ),
                                amount=amount,
                            ))

        # 去重同一文本的多重命中，保留最高严重级别
        violations = self._deduplicate(violations)

        # 统计
        severity_count = {"high": 0, "medium": 0, "low": 0}
        type_count: Dict[str, int] = {}
        for v in violations:
            severity_count[v.severity] = severity_count.get(v.severity, 0) + 1
            type_count[v.violation_type] = type_count.get(v.violation_type, 0) + 1

        return BudgetResult(
            violations=sorted(violations, key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x.severity],
                x.index,
            )),
            total_expenses=len(expense_texts),
            violation_count=len(violations),
            violation_by_severity=severity_count,
            violation_by_type=type_count,
        )

    def _load_rules(
        self,
        rule_set: Optional[Dict],
        custom_rules: Optional[List[Dict]],
    ) -> Dict:
        """加载/合并规则集"""
        import copy
        rules = copy.deepcopy(_DEFAULT_RULES)

        if rule_set:
            rules["keywords"] = rule_set.get("keywords", rules["keywords"])
            rules["patterns"] = rule_set.get("patterns", rules["patterns"])
            rules["limits"] = rule_set.get("limits", rules["limits"])

        if custom_rules:
            rules["keywords"] = rules.get("keywords", []) + [
                r for r in custom_rules
                if r.get("type") == "keyword"
            ]
            rules["patterns"] = rules.get("patterns", []) + [
                r for r in custom_rules
                if r.get("type") == "pattern"
            ]

        return rules

    def _extract_amount(self, text: str) -> Optional[float]:
        """从文本中提取金额"""
        match = re.search(r"[¥￥]?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:元|万元?)?", text)
        if match:
            s = match.group(1).replace(",", "")
            try:
                return float(s)
            except ValueError:
                pass
        return None

    def _deduplicate(
        self, violations: List[BudgetViolation]
    ) -> List[BudgetViolation]:
        """去重：同一文本只保留最高严重级别的违规"""
        seen: Dict[int, BudgetViolation] = {}
        severity_order = {"high": 0, "medium": 1, "low": 2}

        for v in violations:
            if v.index not in seen:
                seen[v.index] = v
            else:
                existing = seen[v.index]
                if severity_order[v.severity] < severity_order[existing.severity]:
                    seen[v.index] = v

        return list(seen.values())


# ── MCP工具接口 ──────────────────────────────────────────────

def budget_compliance_scan(
    expense_texts: List[str],
    rule_set: Optional[Dict[str, Any]] = None,
    custom_rules: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """MCP工具接口：budget_compliance_scan"""
    scanner = BudgetComplianceScanner()
    result = scanner.scan(
        expense_texts=expense_texts,
        rule_set=rule_set,
        custom_rules=custom_rules,
    )

    return {
        "violations": [asdict(v) for v in result.violations],
        "total_expenses": result.total_expenses,
        "violation_count": result.violation_count,
        "violation_rate": (
            f"{result.violation_count/result.total_expenses*100:.1f}%"
            if result.total_expenses > 0 else "0%"
        ),
        "violation_by_severity": result.violation_by_severity,
        "violation_by_type": result.violation_by_type,
        "summary": (
            f"共扫描{result.total_expenses}条记录，发现{result.violation_count}条违规"
            f"（高危{result.violation_by_severity.get('high', 0)}条，"
            f"中危{result.violation_by_severity.get('medium', 0)}条，"
            f"低危{result.violation_by_severity.get('low', 0)}条）"
        ),
    }
