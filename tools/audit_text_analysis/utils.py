"""
共享工具函数 — 文本预处理、停用词管理、结果格式化
"""

import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ── 审计专用停用词表 ──────────────────────────────────────────

_AUDIT_STOPWORDS_BASE = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "所", "为", "所以", "因为", "但是", "然而", "不过", "并且", "或者",
    "以及", "虽然", "如果", "可以", "可能", "应该", "已经", "还是",
    "进行", "使用", "通过", "相关", "根据", "按照", "关于", "对于",
    "其中", "其他", "以上", "以下", "本次", "各项", "如下", "包括",
    "方面", "情况", "问题", "工作", "需要", "主要", "基本", "具体",
    "一般", "一定", "比较", "非常", "十分", "特别", "确实", "真的",
    "什么", "怎么", "怎样", "哪", "吗", "呢", "吧", "啊", "哦", "嗯",
    "会议", "同志", "大家", "各位", "指出", "强调", "要求",
}

_AUDIT_FOCUS_STOPWORDS = {
    "economic_responsibility": {
        "经责", "离任", "任期", "述职", "述廉",
    },
    "budget": {
        "预算", "决算", "收支", "拨款", "经费",
    },
    "project": {
        "工程", "项目", "施工", "招标", "投标",
    },
    "subsidy": {
        "补贴", "补助", "惠民", "扶贫", "低保",
    },
}


def load_stopwords(
    audit_focus: Optional[str] = None,
    custom_stopwords: Optional[List[str]] = None,
) -> set:
    """加载审计专用停用词表，可按审计重点增补"""
    sw = set(_AUDIT_STOPWORDS_BASE)
    if audit_focus and audit_focus in _AUDIT_FOCUS_STOPWORDS:
        sw.update(_AUDIT_FOCUS_STOPWORDS[audit_focus])
    if custom_stopwords:
        sw.update(custom_stopwords)
    return sw


# ── 中文文本清洗 ──────────────────────────────────────────────

def clean_text(text: str) -> str:
    """清洗文本：去标点、空白规范化、全角转半角"""
    text = text.strip()
    text = re.sub(r"[\s\u3000]+", " ", text)  # 统一空白
    # 去除中文标点和常见英文标点
    text = re.sub(r"[，。！？、；：""''（）【】《》…—]", " ", text)
    text = re.sub(r"[-.,!?;:\\\"'()\[\]{}]", " ", text)
    return text


def normalize_name(name: str) -> str:
    """规范化中文姓名：去空格、统一全角"""
    return name.strip().replace("\u3000", "").replace(" ", "")


def normalize_company(name: str) -> str:
    """规范化公司名称"""
    name = name.strip()
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"[（(].*?[）)]", "", name)  # 去括号内容（分公司/地址等）
    return name


# ── 结果数据结构 ──────────────────────────────────────────────

@dataclass
class RiskFlag:
    """风险标记"""
    type: str
    detail: str
    severity: str  # high | medium | low
    evidence: str = ""
    cross_refs: List[str] = field(default_factory=list)
    simulator_inference: Optional[Dict[str, Any]] = None  # v5: Why层推理


@dataclass
class AuditFinding:
    """审计疑点"""
    index: int
    finding_type: str
    source_file: str
    risk_flags: List[RiskFlag] = field(default_factory=list)
    severity: str = "medium"  # highest severity among flags
    human_review_status: str = "pending"  # pending | confirmed | rejected | modified
    human_review_note: str = ""


@dataclass
class CoverageReport:
    """数据归集覆盖率报告"""
    expected_count: int = 0
    actual_count: int = 0
    coverage_pct: float = 0.0
    missing_items: List[str] = field(default_factory=list)
    data_quality_issues: List[str] = field(default_factory=list)


def serialize_findings(findings: List[AuditFinding]) -> str:
    """序列化审计疑点列表为JSON"""
    result = []
    for f in findings:
        d = {
            "index": f.index,
            "finding_type": f.finding_type,
            "source_file": f.source_file,
            "severity": f.severity,
            "human_review_status": f.human_review_status,
            "human_review_note": f.human_review_note,
            "risk_flags": [
                {
                    "type": rf.type,
                    "detail": rf.detail,
                    "severity": rf.severity,
                    "evidence": rf.evidence,
                    "cross_refs": rf.cross_refs,
                    "simulator_inference": rf.simulator_inference,
                }
                for rf in f.risk_flags
            ],
        }
        result.append(d)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ── 审计类型推断 ──────────────────────────────────────────────

_AUDIT_TYPE_KEYWORDS = {
    "economic_responsibility": ["经责", "离任", "任期", "经济责任", "领导干部"],
    "medical_insurance": ["医保", "药品", "医疗", "诊疗", "处方"],
    "procurement": ["采购", "招标", "供应商", "投标"],
    "project": ["工程", "施工", "造价", "监理", "竣工验收"],
    "subsidy": ["补贴", "惠民", "扶贫", "低保", "救助", "保障性"],
    "budget": ["预算", "决算", "收支", "资金", "财政"],
}


def infer_audit_type(texts: List[str]) -> str:
    """根据文本内容推断审计类型"""
    full = " ".join(texts)
    scores = {}
    for atype, keywords in _AUDIT_TYPE_KEYWORDS.items():
        scores[atype] = sum(full.count(kw) for kw in keywords)
    if not scores:
        return "general"
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def infer_focus_areas(audit_type: str) -> List[str]:
    """根据审计类型推荐关注领域"""
    mapping = {
        "economic_responsibility": ["重大经济决策", "国有资产管理", "廉政建设", "内控制度执行"],
        "medical_insurance": ["药品采购", "诊疗收费", "基金使用", "定点机构管理"],
        "procurement": ["招标合规性", "供应商管理", "合同履行", "资金支付"],
        "project": ["工程变更", "签证审核", "材料价格", "竣工结算"],
        "subsidy": ["资格审核", "资金发放", "重复申领", "超范围发放"],
        "budget": ["预算编制", "支出合规性", "资金挪用", "三公经费"],
    }
    return mapping.get(audit_type, ["通用审计关注事项"])
