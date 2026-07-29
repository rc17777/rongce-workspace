"""
v5增强：模拟器对偶 — 每个工具的"Why"层因果推理

对5个文本分析工具的输出进行二次分析，不回答"模式是什么"，
而是回答"模式为什么存在"——通过信任方/质疑方辩论引擎自动触发。

设计原则：
- 每个工具的输出增加 simulator_inference 字段
- 信任方给出优化解（操作失误/正常业务 → 低风险）
- 质疑方给出恶意解（舞弊/蓄意规避 → 高风险）
- 仲裁Agent综合裁定倾向
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class InferenceTilt(Enum):
    BENIGN = "benign"       # 偏良性解释
    SUSPICIOUS = "suspicious"  # 偏恶性解释
    INCONCLUSIVE = "inconclusive"  # 无法判断


@dataclass
class SimulatorInference:
    """模拟器推理结果"""
    tool_name: str
    original_finding: str     # 原始工具发现摘要
    trust_view: str            # 信任方观点（良性解释）
    trust_evidence: str        # 信任方证据
    challenge_view: str        # 质疑方观点（恶意解释）
    challenge_evidence: str    # 质疑方证据
    arbitration_tilt: InferenceTilt  # 仲裁倾向
    arbitration_reason: str    # 仲裁理由
    confidence: float          # 仲裁置信度 0-1
    recommended_action: str    # 建议行动


class SimulatorDualityEngine:
    """
    模拟器对偶引擎

    为每个文本分析工具的发现生成因果推理。
    不替代工具，而是给工具的输出添加深度解读层。
    """

    def infer_hotword(
        self, hotword: Dict[str, Any], audit_type: str
    ) -> SimulatorInference:
        """热词分析 → 业务语义解释"""
        word = hotword.get("word", "")
        weight = hotword.get("weight", 0)
        is_risk = hotword.get("risk_signal", False)

        if not is_risk:
            return SimulatorInference(
                tool_name="text_hotword_analysis",
                original_finding=f"「{word}」为高频词（权重{weight:.4f}）",
                trust_view=f"「{word}」可能是该单位正常业务关键词，"
                          f"反映了当前工作重点",
                trust_evidence=f"高频但不属于风险词库，在其他同类审计项目中也常见",
                challenge_view=f"即使是正常高频词，也可能掩盖异常——比如过于聚焦"
                              f"「{word}」而忽视其他风险领域",
                challenge_evidence="业务聚焦度过高本身就是治理风险信号",
                arbitration_tilt=InferenceTilt.BENIGN,
                arbitration_reason="非风险信号词，建议关注但无需优先排查",
                confidence=0.75,
                recommended_action=f"在后续审计中关注「{word}」相关业务的资金流向",
            )

        # 风险信号词的深度推理
        benign_explanations = {
            "外包": "可能是正常的业务外包，按程序进行了招标",
            "采购": "采购频率高是因为年度集中采购时点",
            "处置": "资产处置可能是正常的报废更新",
            "变更": "工程变更是客观条件变化导致的正常调整",
            "预付": "预付款是行业惯例，有保函保障",
            "借款": "可能是正常内部调拨，有完整的审批手续",
            "转包": "可能是合法的专业分包",
            "围标": "高频讨论围标问题可能是加强监管的表现，而非参与围标",
            "挪用": "可能指的是正常资金调度，用词不准确",
            "套取": "可能指正常费用报销，描述存在歧义",
            "冒领": "可能是重复录入导致的系统问题",
            "截留": "可能指正常留存，非恶意截留",
            "超标": "可能是物价上涨导致的客观超标",
            "违规": "可能是程序性瑕疵而非实质性违规",
            "虚列": "可能是科目归属不准确，非恶意虚列",
        }

        malicious_explanations = {
            "外包": "可能通过外包规避招标或关联交易输送利益",
            "采购": "高频采购可能隐藏化整为零、规避招标",
            "处置": "资产处置可能未经评估，低价转让造成国有资产流失",
            "变更": "频繁变更可能是围标后追加利润的手段",
            "预付": "大额预付款可能被挪用或形成坏账",
            "借款": "可能是违规对外借款，存在利益输送",
            "转包": "违法转包，实际施工方不具资质",
            "围标": "直接参与围标串标，涉嫌违法犯罪",
            "挪用": "专项资金被挪用于其他用途",
            "套取": "虚构交易套取财政资金",
            "冒领": "蓄意冒领补贴资金的舞弊行为",
            "截留": "截留应上缴的财政资金",
            "超标": "奢侈浪费，违反八项规定精神",
            "违规": "明知故犯的严重违规行为",
            "虚列": "设立账外资金小金库",
        }

        trust_ev = benign_explanations.get(word, f"「{word}」存在合理解释可能")
        challenge_ev = malicious_explanations.get(word, f"「{word}」可能是重大风险信号")

        return SimulatorInference(
            tool_name="text_hotword_analysis",
            original_finding=f"「{word}」为风险信号词（权重{weight:.4f}）",
            trust_view=trust_ev,
            trust_evidence="审计实践中此类关键词有较高误报率",
            challenge_view=challenge_ev,
            challenge_evidence=f"「{word}」在{audit_type}审计中是经典违规特征",
            arbitration_tilt=InferenceTilt.SUSPICIOUS,
            arbitration_reason=f"作为风险信号词，「{word}」在{audit_type}"
                              f"审计中有明确的风险关联，建议优先核查",
            confidence=0.8,
            recommended_action=f"将「{word}」列入重点核查清单，"
                             f"调取相关凭证和审批记录",
        )

    def infer_similarity(
        self, match: Dict[str, Any]
    ) -> SimulatorInference:
        """相似度比对 → 串换原因推断"""
        similarity = match.get("similarity", 0)
        ref = match.get("ref_text", "")
        check = match.get("check_text", "")
        risk_type = match.get("risk_type", "")

        if risk_type == "duplicate":
            return SimulatorInference(
                tool_name="text_similarity_compare",
                original_finding=f"「{ref}」与「{check}」"
                                f"完全重复（相似度{similarity:.2%}）",
                trust_view="可能为同一事项的多份独立记录，非恶意",
                trust_evidence="同一采购分批到货、同一工程分标段等情况正常",
                challenge_view=f"「{ref}」疑似通过拆分为「{check}」"
                              f"规避招标限额",
                challenge_evidence="拆分采购是规避招标的经典手法",
                arbitration_tilt=InferenceTilt.SUSPICIOUS,
                arbitration_reason=f"完全重复({similarity:.2%})"
                                  f"需排除拆分规避嫌疑",
                confidence=0.85,
                recommended_action="核实是否属于同一项目拆分，"
                                 "索取拆分依据和审批文件",
            )

        if similarity >= 0.85:
            return SimulatorInference(
                tool_name="text_similarity_compare",
                original_finding=f"「{ref}」与「{check}」"
                                f"高度相似（{similarity:.2%}）",
                trust_view="名称微调可能是品牌升级、规范名称变更",
                trust_evidence="供应商更名、药品名称规范等有官方依据",
                challenge_view="名称微调是串换的典型手法——"
                              "替换个别字逃避筛查",
                challenge_evidence="医保审计中品名串换极为常见",
                arbitration_tilt=InferenceTilt.SUSPICIOUS,
                arbitration_reason="高相似度+风险场景，建议从严",
                confidence=0.78,
                recommended_action="比对供应商工商注册信息和变更记录",
            )

        return SimulatorInference(
            tool_name="text_similarity_compare",
            original_finding=f"「{ref}」与「{check}」"
                            f"中等相似（{similarity:.2%}）",
            trust_view="偶发性匹配，不太可能有组织性串换",
            trust_evidence="阈值接近临界值，可能是偶然",
            challenge_view="即使是中等相似，在集中时间段出现的多个中等相似"
                          "也可能是组织性串换",
            challenge_evidence="有组织的串换会刻意控制相似度",
            arbitration_tilt=InferenceTilt.INCONCLUSIVE,
            arbitration_reason="中等相似度需结合时间分布和金额判断",
            confidence=0.5,
            recommended_action="扩大时间范围检查，关注是否集中出现",
        )

    def infer_contract_risk(
        self, risk_flag: Dict[str, Any]
    ) -> SimulatorInference:
        """合同风险 → 根因分析"""
        risk_type = risk_flag.get("type", "")
        detail = risk_flag.get("detail", "")

        inferences = {
            "over_payment": SimulatorInference(
                tool_name="contract_field_extract",
                original_finding=detail,
                trust_view="超合同付款可能是正常的补充协议金额累积",
                trust_evidence="因工程变更/价格上涨导致的正常追加",
                challenge_view="超合同付款可能是利益输送——"
                              "通过超额支付向供应商输送利益",
                challenge_evidence="无对应补充协议的超额支付是腐败的常见形式",
                arbitration_tilt=InferenceTilt.SUSPICIOUS,
                arbitration_reason="超额支付需有完整审批链，否则视为高风险",
                confidence=0.82,
                recommended_action="核查是否有对应补充协议和变更审批单",
            ),
            "early_payment": SimulatorInference(
                tool_name="contract_field_extract",
                original_finding=detail,
                trust_view="提前付款可能因对方资金困难而特殊批准",
                trust_evidence="有完整的提前付款审批流程",
                challenge_view="提前付款可能为关联方输送利益——"
                              "牺牲本方资金时间价值",
                challenge_evidence="无合理理由的提前付款是资金占用的信号",
                arbitration_tilt=InferenceTilt.INCONCLUSIVE,
                arbitration_reason="需结合具体付款条件判断",
                confidence=0.55,
                recommended_action="核查付款申请单和审批记录中的提前付款理由",
            ),
            "delay": SimulatorInference(
                tool_name="contract_field_extract",
                original_finding=detail,
                trust_view="工期延误可能是不可抗力或甲方原因",
                trust_evidence="不可抗力/设计变更/甲方供应不及时等客观原因",
                challenge_view="工期延误可能是串通行为——"
                              "故意延误创造变更索赔机会",
                challenge_evidence="无合理原因的延误配合大量变更索赔是典型手法",
                arbitration_tilt=InferenceTilt.INCONCLUSIVE,
                arbitration_reason="需核对工期延误原因和责任归属",
                confidence=0.5,
                recommended_action="调取工期延期审批单，核实延误原因",
            ),
        }

        return inferences.get(
            risk_type,
            SimulatorInference(
                tool_name="contract_field_extract",
                original_finding=detail,
                trust_view="可能存在合理的解释",
                trust_evidence="需进一步核查",
                challenge_view="需警惕这是系统性问题的一部分",
                challenge_evidence="综合其他疑点判断",
                arbitration_tilt=InferenceTilt.INCONCLUSIVE,
                arbitration_reason="信息不足，无法判断",
                confidence=0.3,
                recommended_action="收集更多相关证据再判断",
            ),
        )

    def infer_personnel_violation(
        self, violation: Dict[str, Any]
    ) -> SimulatorInference:
        """人员违规 → 意图分类"""
        vtype = violation.get("violation_type", "")
        name = violation.get("name", "")

        if "duplicate" in vtype:
            return SimulatorInference(
                tool_name="personnel_profile_check",
                original_finding=f"{name}存在重复申领",
                trust_view="可能是系统录入错误导致的重复记录",
                trust_evidence="基层信息录入人员常见操作错误",
                challenge_view="蓄意重复申领骗取双份补贴",
                challenge_evidence="使用不同身份信息或跨地区重复申领是常见舞弊手法",
                arbitration_tilt=InferenceTilt.SUSPICIOUS,
                arbitration_reason="重复申领是民生资金审计的经典问题，"
                                  "需排除蓄意可能",
                confidence=0.72,
                recommended_action=f"核实{name}的两份申领记录中"
                                 f"身份证号、银行账号是否一致",
            )

        if "ineligible" in vtype:
            return SimulatorInference(
                tool_name="personnel_profile_check",
                original_finding=f"{name}不符合申领资格",
                trust_view="可能是基层审核不严的程序疏漏",
                trust_evidence="基层工作量大人少，审核难免有遗漏",
                challenge_view="有组织的不合格申领——有人专门收集不合格人员"
                              "信息套取补贴",
                challenge_evidence="有组织的骗补往往涉及多人且金额巨大",
                arbitration_tilt=InferenceTilt.SUSPICIOUS,
                arbitration_reason=f"{name}出现在禁止名单中，客观违规事实清晰",
                confidence=0.88,
                recommended_action=f"追查{name}的申领经办人，"
                                 f"检查是否有更多不合格申领",
            )

        if "policy_mismatch" in vtype:
            return SimulatorInference(
                tool_name="personnel_profile_check",
                original_finding=f"{name}申领与政策不一致",
                trust_view="可能是政策理解偏差或信息更新不及时",
                trust_evidence="补贴政策经常调整，一线人员可能不知晓",
                challenge_view="明知不符合条件但仍申领，利用信息差套利",
                challenge_evidence="政策公示后仍申领，属于明知故犯",
                arbitration_tilt=InferenceTilt.INCONCLUSIVE,
                arbitration_reason="需结合申领时间和政策发布时间判断",
                confidence=0.55,
                recommended_action="核实政策发布时间与申领时间的关系",
            )

        return SimulatorInference(
            tool_name="personnel_profile_check",
            original_finding=str(violation),
            trust_view="需进一步核查确认",
            trust_evidence="信息有限",
            challenge_view="不能排除蓄意违规",
            challenge_evidence="人员身份违规索赔是常见问题",
            arbitration_tilt=InferenceTilt.INCONCLUSIVE,
            arbitration_reason="建议人工核实",
            confidence=0.4,
            recommended_action="收集更多信息后重新评估",
        )

    def infer_budget_violation(
        self, violation: Dict[str, Any]
    ) -> SimulatorInference:
        """预算违规 → 根因分析"""
        vtype = violation.get("violation_type", "")
        severity = violation.get("severity", "medium")
        desc = violation.get("rule_description", "")

        if severity == "high":
            return SimulatorInference(
                tool_name="budget_compliance_scan",
                original_finding=desc,
                trust_view="高危标记可能是政策理解偏差或程序性瑕疵",
                trust_evidence="部分高危关键词（如'现金支付'）有可能只是用词不当",
                challenge_view=f"「{desc}」属于蓄意违规，"
                              f"刻意规避监管",
                challenge_evidence="高危违规在实践中极少是偶发的程序性错误",
                arbitration_tilt=InferenceTilt.SUSPICIOUS,
                arbitration_reason="高危标记通常对应明确违规行为，优先核查",
                confidence=0.85,
                recommended_action="列为优先核查项，调取原始凭证和相关审批",
            )

        if severity == "medium":
            return SimulatorInference(
                tool_name="budget_compliance_scan",
                original_finding=desc,
                trust_view="可能是不规范操作而非恶意违规",
                trust_evidence="基层财务管理水平参差不齐，不规范操作常见",
                challenge_view="不规范操作的累积效应可能构成系统性风险",
                challenge_evidence="多处中危在总体风险上可能超出单个高危",
                arbitration_tilt=InferenceTilt.INCONCLUSIVE,
                arbitration_reason=f"「{desc}」需结合完整支出流判断",
                confidence=0.55,
                recommended_action="结合该笔支出的全流程审批链评估",
            )

        return SimulatorInference(
            tool_name="budget_compliance_scan",
            original_finding=desc,
            trust_view="低危标记，可能为偶发性问题",
            trust_evidence="低危标记有较高误报率",
            challenge_view="即使是低危，大量累积也构成风险",
            challenge_evidence="系统性低危问题反映内控薄弱",
            arbitration_tilt=InferenceTilt.BENIGN,
            arbitration_reason=f"「{desc}」建议纳入后续关注但非当期重点",
            confidence=0.65,
            recommended_action="记录但不作为当期优先核查项",
        )


# ── 便捷函数：批量推理 ─────────────────────────────────────

def generate_simulator_inferences(
    tool_name: str,
    findings: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    为一批工具发现批量生成模拟器推理

    Args:
        tool_name: 工具名
        findings: 工具发现列表
        context: 上下文（如audit_type）

    Returns:
        带 simulator_inference 字段的发现列表
    """
    engine = SimulatorDualityEngine()

    for finding in findings:
        inference = None

        if tool_name == "text_hotword_analysis":
            inference = engine.infer_hotword(
                finding, context.get("audit_type", "general") if context else "general"
            )
        elif tool_name == "text_similarity_compare":
            inference = engine.infer_similarity(finding)
        elif tool_name == "contract_field_extract":
            inference = engine.infer_contract_risk(finding)
        elif tool_name == "personnel_profile_check":
            inference = engine.infer_personnel_violation(finding)
        elif tool_name == "budget_compliance_scan":
            inference = engine.infer_budget_violation(finding)

        if inference:
            finding["simulator_inference"] = asdict(inference)

    return findings
