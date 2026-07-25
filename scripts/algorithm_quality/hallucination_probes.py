#!/usr/bin/env python3
"""
P1-9: 国产LLM幻觉专项探针
针对 DeepSeek/Kimi/GLM 各自不同的幻觉特征设计差异化测试
- DeepSeek: 法规文号编造检测
- Kimi: 长上下文串台检测
- GLM: 金额精度漂移检测
"""

import re, json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class ProbeResult:
    """探针检测结果"""
    test_name: str
    passed: bool
    detail: str
    evidence: str = ""
    severity: str = "INFO"  # INFO / WARNING / CRITICAL


class RegulationRefProbe:
    """
    法规文号验证探针（DeepSeek专项）
    
    检测LLM输出中是否包含虚构的法规文号
    如："财预〔2023〕XX号" → 检验格式+存在性
    """
    
    # 政府公文文号正则
    DOC_PATTERN = re.compile(
        r'(财[税预办发会国农][综]\s*〔?\s*\d{4}\s*〕?\s*\d+\s*号)'
        r'|(国发\s*〔?\s*\d{4}\s*〕?\s*\d+\s*号)'
        r'|(川财\s*〔?\s*\d{4}\s*〕?\s*\d+\s*号)'
        r'|(成财\s*〔?\s*\d{4}\s*〕?\s*\d+\s*号)'
    )
    
    # 常见虚假文号模式
    FAKE_PATTERNS = [
        r'〔\s*202[3-9]\s*〕\s*[0-9X]+\s*号',  # 未来年份
        r'XX号', r'xx号', r'〔0000〕',  # 占位符
    ]

    @classmethod
    def probe(cls, llm_output: str) -> List[ProbeResult]:
        """检测LLM输出中的法规文号"""
        results = []
        
        # 检测虚构文号
        for pattern in cls.FAKE_PATTERNS:
            matches = re.findall(pattern, llm_output, re.IGNORECASE)
            for m in matches:
                results.append(ProbeResult(
                    test_name="法规文号-虚构占位",
                    passed=False,
                    detail=f"发现疑似虚构文号: {m}",
                    evidence=m,
                    severity="CRITICAL"
                ))
        
        # 检测所有文号引用 → 格式校验
        doc_refs = cls.DOC_PATTERN.findall(llm_output)
        for ref in doc_refs:
            ref_str = ''.join(ref) if isinstance(ref, tuple) else ref
            if ref_str:
                # 基础格式校验
                year_match = re.search(r'〔?\s*(\d{4})\s*〕?', ref_str)
                if year_match:
                    year = int(year_match.group(1))
                    if year > 2026:
                        results.append(ProbeResult(
                            test_name="法规文号-未来年份",
                            passed=False,
                            detail=f"文号年份{year}超出当前范围: {ref_str}",
                            evidence=ref_str,
                            severity="CRITICAL"
                        ))
        
        if not results:
            results.append(ProbeResult(
                test_name="法规文号-通过",
                passed=True,
                detail="未发现虚构法规文号"
            ))
        
        return results


class LongContextProbe:
    """
    长上下文串台检测（Kimi专项）
    
    检测多文档场景下LLM是否将文档A的信息错误归因到文档B
    """
    
    @classmethod
    def probe(cls, llm_output: str, source_docs: List[Dict]) -> List[ProbeResult]:
        """检测信息串台"""
        results = []
        
        # 简化：检查输出中的金额/日期/实体是否与源文档匹配
        for doc in source_docs:
            doc_entities = cls._extract_entities(llm_output)
            source_entities = cls._extract_entities(doc.get('content', ''))
            # 检查交叉引用
            for entity, value in doc_entities.items():
                if entity in source_entities and value != source_entities[entity]:
                    results.append(ProbeResult(
                        test_name=f"长上下文-实体串台",
                        passed=False,
                        detail=f"实体[{entity}]在输出中={value}, 源文档={source_entities[entity]}",
                        evidence=f"output={value} vs source={source_entities[entity]}",
                        severity="WARNING"
                    ))
        
        if not results:
            results.append(ProbeResult(
                test_name="长上下文-通过",
                passed=True,
                detail="未发现跨文档串台"
            ))
        
        return results
    
    @classmethod
    def _extract_entities(cls, text: str) -> Dict[str, str]:
        """提取关键实体"""
        entities = {}
        # 金额
        amt_match = re.findall(r'[\d,]+\.?\d*\s*(万元|亿元|元)', text)
        if amt_match:
            entities['amounts'] = json.dumps(amt_match)
        # 日期
        date_match = re.findall(r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日号]', text)
        if date_match:
            entities['dates'] = json.dumps(date_match[:5])
        return entities


class AmountPrecisionProbe:
    """
    金额精度漂移检测（GLM专项）
    
    检测LLM在金额复算/格式转换时是否出现精度偏移
    如：1.5亿→1.5万、40728元→40700元
    """
    
    @classmethod
    def probe(cls, original_text: str, llm_output: str) -> List[ProbeResult]:
        """检测金额精度"""
        results = []
        
        # 提取原文和输出中的金额
        orig_amounts = cls._parse_amounts(original_text)
        out_amounts = cls._parse_amounts(llm_output)
        
        for oa in orig_amounts:
            # 查找最接近的对应金额
            closest = cls._find_closest(oa, out_amounts)
            if closest:
                diff_pct = abs(oa['value'] - closest['value']) / (oa['value'] + 1e-10)
                
                if diff_pct > 1.0:  # 数量级错误
                    results.append(ProbeResult(
                        test_name="金额精度-数量级漂移",
                        passed=False,
                        detail=f"原文{oa['raw']}({oa['value']})→输出{closest['raw']}({closest['value']})，差异{diff_pct:.0%}",
                        evidence=f"{oa['raw']} vs {closest['raw']}",
                        severity="CRITICAL"
                    ))
                elif diff_pct > 0.01:  # 1%以上偏差
                    results.append(ProbeResult(
                        test_name="金额精度-轻微偏差",
                        passed=False,
                        detail=f"原文{oa['raw']}→输出{closest['raw']}，差异{diff_pct:.1%}",
                        evidence=f"{oa['raw']} vs {closest['raw']}",
                        severity="WARNING"
                    ))
        
        if not results:
            results.append(ProbeResult(
                test_name="金额精度-通过",
                passed=True,
                detail="未发现金额精度漂移"
            ))
        
        return results
    
    @classmethod
    def _parse_amounts(cls, text: str) -> List[Dict]:
        """解析文本中的金额"""
        amounts = []
        # 匹配: 数字 + 可选逗号 + 可选小数 + 单位
        pattern = r'([\d,]+\.?\d*)\s*(万元|亿元|元|[万千百]元)'
        multipliers = {'万元': 10000, '亿元': 100000000, '元': 1, '万元': 10000}
        for m in re.finditer(pattern, text):
            raw = m.group(0)
            num = float(m.group(1).replace(',', ''))
            unit = m.group(2)
            value = num * multipliers.get(unit, 1)
            amounts.append({'raw': raw, 'value': value})
        return amounts
    
    @classmethod
    def _find_closest(cls, orig: Dict, candidates: List[Dict]) -> Optional[Dict]:
        """找到最接近的金额"""
        if not candidates:
            return None
        best = min(candidates, key=lambda c: abs(c['value'] - orig['value']))
        # 只匹配数量级差不多的
        if abs(best['value'] - orig['value']) / (orig['value'] + 1e-10) < 100:
            return best
        return None


class HallucinationProbeRunner:
    """
    幻觉探针总运行器
    
    使用：
    >>> runner = HallucinationProbeRunner()
    >>> results = runner.run_all(
    ...     model_name="deepseek",
    ...     llm_output="根据财预〔2023〕XX号文件...",
    ...     source_text="原合同金额4.07万元"
    ... )
    """
    
    @classmethod
    def run_all(cls, model_name: str, llm_output: str, 
                source_text: str = "", source_docs: List[Dict] = None) -> Dict:
        """运行全部探针"""
        all_results = {
            'model': model_name,
            'timestamp': '',
            'probes': [],
            'summary': {'total': 0, 'passed': 0, 'failed': 0, 'critical': 0}
        }
        
        # 法规文号探针（所有模型都跑）
        reg_results = RegulationRefProbe.probe(llm_output)
        all_results['probes'].append({
            'type': 'regulations',
            'results': [{'test': r.test_name, 'passed': r.passed, 'detail': r.detail, 'severity': r.severity} for r in reg_results]
        })
        
        # 金额精度探针（所有模型都跑）
        if source_text:
            amt_results = AmountPrecisionProbe.probe(source_text, llm_output)
            all_results['probes'].append({
                'type': 'amount_precision',
                'results': [{'test': r.test_name, 'passed': r.passed, 'detail': r.detail, 'severity': r.severity} for r in amt_results]
            })
        
        # Kimi专项：长上下文串台
        if model_name.lower() in ('kimi', 'kimi-k3') and source_docs:
            ctx_results = LongContextProbe.probe(llm_output, source_docs or [])
            all_results['probes'].append({
                'type': 'long_context',
                'results': [{'test': r.test_name, 'passed': r.passed, 'detail': r.detail, 'severity': r.severity} for r in ctx_results]
            })
        
        # 统计
        for probe_group in all_results['probes']:
            for r in probe_group['results']:
                all_results['summary']['total'] += 1
                if r['passed']:
                    all_results['summary']['passed'] += 1
                else:
                    all_results['summary']['failed'] += 1
                    if r['severity'] == 'CRITICAL':
                        all_results['summary']['critical'] += 1
        
        return all_results


# ===== CLI Demo =====
if __name__ == '__main__':
    print("=" * 60)
    print("  国产LLM幻觉探针演示")
    print("=" * 60)
    
    runner = HallucinationProbeRunner()
    
    # 测试1: DeepSeek编造法规文号
    fake_output = """
    根据《中华人民共和国预算法》及财预〔2024〕XX号文件规定...
    该笔支出违反了财预〔2025〕156号的要求...
    """
    r1 = runner.run_all("deepseek", fake_output)
    print("\n【DeepSeek 法规文号探针】")
    for g in r1['probes']:
        for r in g['results']:
            icon = '✅' if r['passed'] else '❌'
            print(f"  {icon} {r['test']}: {r['detail']}")
    
    # 测试2: GLM金额精度
    source = "该项目预算4.07万元，实际支出40728元。"
    wrong_output = "预算4.07亿元，支出4.07万元。共涉及资金200万元。"
    r2 = runner.run_all("glm", wrong_output, source_text=source)
    print("\n【GLM 金额精度探针】")
    for g in r2['probes']:
        for r in g['results']:
            icon = '✅' if r['passed'] else '❌'
            print(f"  {icon} {r['test']}: {r['detail']} [{r['severity']}]")
    
    # 总结
    print(f"\n探针通过率: {r1['summary']['passed']}/{r1['summary']['total']} + {r2['summary']['passed']}/{r2['summary']['total']}")
