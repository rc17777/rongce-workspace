"""
工具3：contract_field_extract — 正则+NER合同八大字段拆解

场景：工程审计中，自动提取合同核心字段，
     与财务支付数据、项目台账交叉比对，识别付款违规、履约超期
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

from .utils import normalize_company, normalize_name


# ── 合同八字段正则规则库 ──────────────────────────────────────

_FIELD_PATTERNS = {
    "party": [
        # 甲方
        r"甲\s*方[：:]\s*([^\n。；;]{2,50})",
        r"发包人[：:]\s*([^\n。；;]{2,50})",
        r"采购人[：:]\s*([^\n。；;]{2,50})",
        # 乙方
        r"乙\s*方[：:]\s*([^\n。；;]{2,50})",
        r"承包人[：:]\s*([^\n。；;]{2,50})",
        r"供应商[：:]\s*([^\n。；;]{2,50})",
        r"中标人[：:]\s*([^\n。；;]{2,50})",
    ],
    "amount": [
        # 跳过中文大写数字，找到 ¥/￥ 标记后的阿拉伯数字
        r"(?:合同|总)?金额[：:为].*?[¥￥]\s*([\d,，.]+)\s*(?:元|万元?)",
        r"(?:中标|成交)?价[：:为]?.*?[¥￥]\s*([\d,，.]+)\s*(?:元|万元?)",
        r"合同价款[：:].*?[¥￥]?\s*([\d,，.]+)\s*(?:元|万元?)",
        r"暂定(?:合同)?总价[：:为]?.*?[¥￥]?\s*([\d,，.]+)\s*(?:元|万元?)",
        # 兜底：直接匹配 ¥xxx元
        r"[¥￥]\s*([\d,，.]+)\s*(?:元|万元?)",
    ],
    "sign_date": [
        r"(?:签订|签署|签订合同)?日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
        r"(?:签订|签署)(?:于|时间)[：:]?\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
        r"(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)\s*(?:签订|签署)",
    ],
    "period": [
        r"(?:工期|履行期限|合同期限|服务期限)[：:]\s*([^\n。；;]{5,50})",
        r"(?:自|从)(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)\s*(?:起|至|到)\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
        r"计划(?:开工|开始)日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
        r"计划(?:竣工|完成|结束)日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
    ],
    "payment_terms": [
        r"(?:付款|支付)(?:方式|条件|条款|约定)[：:]\s*([^\n。；;]{5,100})",
        r"(?:预付款|进度款|结算款)[：:]\s*([^\n。；;]{5,100})",
        r"质保金[：:为]?\s*[¥￥]?([\d,，.%％]+)",
    ],
    "penalty": [
        r"(?:违约|违约(?:责任|条款|约定))[：:]\s*([^\n。；;]{5,100})",
        r"(?:逾期|延误)(?:违约金|罚款)[：:为]?\s*[¥￥]?([\d,，.%％/天日]+)",
        r"质量(?:违约|不合格).*?(?:违约金|罚款|赔偿)[：:为]?\s*([^\n。；;]{5,50})",
    ],
    "amendments": [
        r"(?:变更|补充协议|合同变更)[：:]\s*([^\n。；;]{5,100})",
        r"变更(?:内容|范围|方式)[：:]\s*([^\n。；;]{5,100})",
        r"合同价款(?:调整|变更)[：:]\s*([^\n。；;]{5,50})",
    ],
    "qualification": [
        r"(?:资质|资格)(?:要求|等级|条件)[：:]\s*([^\n。；;]{5,50})",
        r"(?:承包|施工|设计)资质[：:为]?\s*([一二三甲乙丙丁特]级|[^\n。；;]{3,30})",
        r"营业执照.*?(?:编号|号)[：:]?\s*([\dA-Za-z-]{10,30})",
    ],
}

# 单位转换
_UNIT_MULTIPLIER = {
    "万元": 10000,
    "元": 1,
}


@dataclass
class ContractInfo:
    file: str
    fields: Dict[str, Any]  # 提取的字段
    risk_flags: List[Dict[str, Any]] = field(default_factory=list)
    raw_match_positions: Dict[str, List[Tuple[int, int]]] = field(
        default_factory=dict
    )


@dataclass
class ContractResult:
    contracts: List[ContractInfo]
    total_files: int
    extracted_fields_count: Dict[str, int]
    risk_summary: Dict[str, int]


class ContractFieldExtractor:
    """合同字段提取器"""

    def extract(
        self,
        contract_texts: List[Tuple[str, str]],  # (文件名, 文本内容)
        extract_fields: Optional[List[str]] = None,
        payment_records: Optional[List[Dict]] = None,
        project_ledger: Optional[List[Dict]] = None,
    ) -> ContractResult:
        """
        合同字段提取

        Args:
            contract_texts: [(文件名, 文本内容), ...]
            extract_fields: 要提取的字段名列表，None=全部
            payment_records: 财务支付记录（用于交叉比对）
            project_ledger: 项目台账（用于交叉比对）

        Returns:
            ContractResult
        """
        if extract_fields is None:
            extract_fields = list(_FIELD_PATTERNS.keys())

        contracts = []
        filed_counts = {f: 0 for f in extract_fields}

        for filename, text in contract_texts:
            fields = {}
            positions = {}

            for field_name in extract_fields:
                if field_name not in _FIELD_PATTERNS:
                    continue
                patterns = _FIELD_PATTERNS[field_name]
                matches = []
                for pat in patterns:
                    for m in re.finditer(pat, text):
                        value = m.group(1).strip()
                        if value and len(value) >= 2:
                            matches.append(value)
                            positions.setdefault(field_name, []).append(
                                (m.start(), m.end())
                            )
                if matches:
                    # 去重取最完整的匹配
                    fields[field_name] = max(matches, key=len)
                    filed_counts[field_name] += 1

            # 金额标准化
            if "amount" in fields:
                fields["amount_normalized"] = self._normalize_amount(
                    fields["amount"]
                )

            contract = ContractInfo(
                file=filename,
                fields=fields,
                raw_match_positions=positions,
            )

            # 交叉比对
            if payment_records or project_ledger:
                self._cross_check(contract, payment_records, project_ledger)

            contracts.append(contract)

        # 风险统计
        risk_summary = {"high": 0, "medium": 0, "low": 0}
        for c in contracts:
            for rf in c.risk_flags:
                risk_summary[rf.get("severity", "low")] += 1

        return ContractResult(
            contracts=contracts,
            total_files=len(contract_texts),
            extracted_fields_count=filed_counts,
            risk_summary=risk_summary,
        )

    def _normalize_amount(self, amount_str: str) -> float:
        """标准化金额字符串为浮点数（元）"""
        s = amount_str.replace(",", "").replace("，", "").replace(" ", "")
        s = s.lstrip("¥￥")

        # 抽取数值和单位
        match = re.match(r"([\d.]+)\s*(万元?|元)?", s)
        if not match:
            return 0.0

        value = float(match.group(1))
        unit = match.group(2) or "元"

        if "万" in unit:
            value *= 10000

        return round(value, 2)

    def _cross_check(
        self,
        contract: ContractInfo,
        payment_records: Optional[List[Dict]],
        project_ledger: Optional[List[Dict]],
    ):
        """合同字段与财务/项目数据交叉比对"""
        # 金额比对
        if payment_records and "amount_normalized" in contract.fields:
            contract_amount = contract.fields["amount_normalized"]
            for pr in payment_records:
                paid = float(pr.get("amount", 0))
                if paid > contract_amount * 1.05:
                    contract.risk_flags.append({
                        "type": "over_payment",
                        "detail": (
                            f"累计支付{paid:.2f}元，超过合同金额"
                            f"{contract_amount:.2f}元（超付{(paid/contract_amount-1)*100:.1f}%）"
                        ),
                        "severity": "high",
                    })
                elif paid > contract_amount * 0.9 and paid <= contract_amount * 1.05:
                    # 接近全额支付，检查是否满足付款条件
                    if "payment_terms" not in contract.fields:
                        contract.risk_flags.append({
                            "type": "early_payment",
                            "detail": (
                                f"已支付{paid:.2f}元（合同{contract_amount:.2f}元），"
                                f"但未提取到付款条件，需人工确认"
                            ),
                            "severity": "medium",
                        })

        # 日期比对
        if project_ledger and "period" in contract.fields:
            for pj in project_ledger:
                actual_end = pj.get("actual_end_date", "")
                # 简单检查工期是否包含"逾期"关键词
                if "逾期" in str(contract.fields.get("penalty", "")):
                    contract.risk_flags.append({
                        "type": "delay",
                        "detail": "合同包含逾期违约条款，需核实是否发生逾期",
                        "severity": "medium",
                    })

    def extract_from_file(
        self, filepath: str, extract_fields: Optional[List[str]] = None
    ) -> ContractInfo:
        """从文件读取合同文本并提取字段"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            try:
                with open(filepath, "r", encoding="gbk") as f:
                    text = f.read()
            except Exception as e:
                raise ValueError(f"无法读取文件 {filepath}: {e}")

        import os
        filename = os.path.basename(filepath)
        result = self.extract([(filename, text)], extract_fields)
        return result.contracts[0] if result.contracts else ContractInfo(
            file=filename, fields={}
        )


# ── MCP工具接口 ──────────────────────────────────────────────

def contract_field_extract(
    contract_files: List[str],
    extract_fields: Optional[List[str]] = None,
    payment_records: Optional[List[Dict]] = None,
    project_ledger: Optional[List[Dict]] = None,
) -> dict:
    """MCP工具接口：contract_field_extract"""
    import os

    extractor = ContractFieldExtractor()
    contract_texts = []
    for filepath in contract_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, FileNotFoundError) as e:
            text = f"[读取失败: {e}]"
        contract_texts.append((os.path.basename(filepath), text))

    result = extractor.extract(
        contract_texts=contract_texts,
        extract_fields=extract_fields,
        payment_records=payment_records,
        project_ledger=project_ledger,
    )

    contracts_data = []
    for c in result.contracts:
        contracts_data.append({
            "file": c.file,
            "fields": c.fields,
            "risk_flags": c.risk_flags,
        })

    return {
        "contracts": contracts_data,
        "total_files": result.total_files,
        "extracted_fields_count": result.extracted_fields_count,
        "risk_summary": result.risk_summary,
    }
