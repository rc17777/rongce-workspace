"""
工具4：personnel_profile_check — 集合运算人员身份比对

场景：民生补贴/惠农补贴/低保核查中，
     筛查财政供养人员、死亡人员、重复申领等违规领取情况
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict

from .utils import normalize_name


@dataclass
class Violation:
    name: str
    id_card: str = ""
    violation_type: str = ""  # finance_staff | deceased | duplicate | policy_mismatch
    subsidy_type: str = ""
    subsidy_amount: float = 0.0
    evidence: str = ""
    severity: str = "high"
    reference_source: str = ""


@dataclass
class PersonnelResult:
    violations: List[Violation]
    total_applicants: int
    matched_count: int  # 命中违规的数量
    violation_by_type: Dict[str, int]
    clean_count: int


class PersonnelProfileChecker:
    """人员画像比对器"""

    def __init__(self):
        self._reference_lists: Dict[str, Set[str]] = {}

    def check(
        self,
        applicants: List[Dict[str, Any]],
        reference_lists: Dict[str, List[str]],
        check_rules: Optional[List[str]] = None,
        id_card_key: str = "id_card",
    ) -> PersonnelResult:
        """
        人员身份比对

        Args:
            applicants: 申报人列表 [{"name": "张三", "subsidy_type": "惠农补贴", "amount": 5000}, ...]
            reference_lists: 参照名单
                {"finance_staff": ["张三", ...], "deceased": ["李四", ...], ...}
            check_rules: 要执行的检查规则，None=全部
                ["duplicate_claim", "ineligible_identity", "policy_mismatch"]
            id_card_key: 身份证号的键名

        Returns:
            PersonnelResult
        """
        if check_rules is None:
            check_rules = ["duplicate_claim", "ineligible_identity", "policy_mismatch"]

        # 构建索引
        ref_sets = {}
        for list_name, names in reference_lists.items():
            ref_sets[list_name] = {
                normalize_name(n) for n in names if n
            }

        violations = []
        seen_names: Dict[str, int] = {}  # name → index（用于重复检测）

        for idx, applicant in enumerate(applicants):
            name = normalize_name(applicant.get("name", ""))
            if not name:
                continue

            subsidy_type = applicant.get("subsidy_type", "未知补贴")
            amount = float(applicant.get("amount", 0))
            id_card = applicant.get(id_card_key, "")

            # 规则1：重复申领检测
            if "duplicate_claim" in check_rules:
                if name in seen_names:
                    violations.append(Violation(
                        name=name,
                        id_card=id_card,
                        violation_type="duplicate_claim",
                        subsidy_type=subsidy_type,
                        subsidy_amount=amount,
                        evidence=f"{name}在第{seen_names[name]+1}行和第{idx+1}行重复出现",
                        severity="high",
                    ))
                seen_names[name] = idx

            # 规则2：不合格身份检测
            if "ineligible_identity" in check_rules:
                for ref_name, ref_set in ref_sets.items():
                    if name in ref_set:
                        violations.append(Violation(
                            name=name,
                            id_card=id_card,
                            violation_type=f"ineligible_{ref_name}",
                            subsidy_type=subsidy_type,
                            subsidy_amount=amount,
                            evidence=f"{name}出现在「{ref_name}」名单中",
                            severity="high",
                            reference_source=ref_name,
                        ))

            # 规则3：政策一致性检测
            if "policy_mismatch" in check_rules:
                pm_violations = self._check_policy_match(
                    name, applicant, id_card, subsidy_type, amount
                )
                violations.extend(pm_violations)

        # 统计
        violation_types: Dict[str, int] = {}
        for v in violations:
            key = v.violation_type
            violation_types[key] = violation_types.get(key, 0) + 1

        unique_violators = len({v.name for v in violations})

        return PersonnelResult(
            violations=violations,
            total_applicants=len(applicants),
            matched_count=unique_violators,
            violation_by_type=violation_types,
            clean_count=len(applicants) - unique_violators,
        )

    def _check_policy_match(
        self,
        name: str,
        applicant: Dict[str, Any],
        id_card: str,
        subsidy_type: str,
        amount: float,
    ) -> List[Violation]:
        """政策一致性检测"""
        violations = []

        # 年龄检查
        age = applicant.get("age")
        if age is not None:
            try:
                age = int(age)
            except (ValueError, TypeError):
                age = None

        # 惠农补贴通常针对农村户籍
        household = applicant.get("household_type", "")
        if subsidy_type in ("惠农补贴", "农业补贴") and household == "城镇":
            violations.append(Violation(
                name=name,
                id_card=id_card,
                violation_type="policy_mismatch",
                subsidy_type=subsidy_type,
                subsidy_amount=amount,
                evidence=f"{name}为城镇户籍，不符合{ subsidy_type}申领条件",
                severity="high",
            ))

        # 高龄补贴年龄检查
        if "高龄" in subsidy_type and age is not None and age < 80:
            violations.append(Violation(
                name=name,
                id_card=id_card,
                violation_type="policy_mismatch",
                subsidy_type=subsidy_type,
                subsidy_amount=amount,
                evidence=f"{name}年龄{age}岁，不满足{ subsidy_type}年龄要求",
                severity="medium",
            ))

        # 异常金额
        if amount > 100000:
            violations.append(Violation(
                name=name,
                id_card=id_card,
                violation_type="policy_mismatch",
                subsidy_type=subsidy_type,
                subsidy_amount=amount,
                evidence=f"{name}申领金额{amount:.0f}元，远超{ subsidy_type}正常标准",
                severity="medium",
            ))

        return violations


# ── MCP工具接口 ──────────────────────────────────────────────

def personnel_profile_check(
    applicants: List[Dict[str, Any]],
    reference_lists: Dict[str, List[str]],
    check_rules: Optional[List[str]] = None,
) -> dict:
    """MCP工具接口：personnel_profile_check"""
    checker = PersonnelProfileChecker()
    result = checker.check(
        applicants=applicants,
        reference_lists=reference_lists,
        check_rules=check_rules,
    )

    return {
        "violations": [asdict(v) for v in result.violations],
        "total_applicants": result.total_applicants,
        "matched_count": result.matched_count,
        "violation_by_type": result.violation_by_type,
        "clean_count": result.clean_count,
        "summary": (
            f"共核查{result.total_applicants}人，发现{result.matched_count}人存在违规"
            f"（{result.violation_by_type}），{result.clean_count}人通过"
        ),
    }
