"""
工具2：text_similarity_compare — Jaccard相似度串换筛查

场景：医保以药易物、品名串换、项目名称微调套取资金
     采购审计中供应商名称微调、围标陪标识别
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class SimilarityMatch:
    ref_text: str
    check_text: str
    similarity: float
    risk: str = ""
    risk_type: str = ""  # substitution | tweak | duplicate
    matched_chars: List[str] = field(default_factory=list)
    diff_chars: List[str] = field(default_factory=list)


@dataclass
class SimilarityResult:
    matches: List[SimilarityMatch]
    mode: str  # global | local
    threshold: float
    total_comparisons: int
    high_risk_count: int


class TextSimilarityComparator:
    """Jaccard文本相似度比对"""

    def compare(
        self,
        reference_texts: List[str],
        check_texts: List[str],
        mode: str = "global",
        threshold: float = 0.7,
        audit_type: str = "general",
        min_char_len: int = 2,
    ) -> SimilarityResult:
        """
        Jaccard相似度比对

        Args:
            reference_texts: 标准/合规文本数组
            check_texts: 待核查文本数组
            mode: global（整体匹配）| local（字符级微调检测）
            threshold: 相似度阈值，超过即标记
            audit_type: 审计类型
            min_char_len: 最小比对字符长度

        Returns:
            SimilarityResult
        """
        matches = []
        total_comparisons = 0

        for ref in reference_texts:
            for check in check_texts:
                total_comparisons += 1

                if mode == "global":
                    sim, matched, diff = self._jaccard_global(ref, check, min_char_len)
                else:
                    sim, matched, diff = self._jaccard_local(ref, check, min_char_len)

                if sim >= threshold:
                    risk, risk_type = self._assess_risk(ref, check, sim, audit_type)
                    matches.append(SimilarityMatch(
                        ref_text=ref,
                        check_text=check,
                        similarity=round(sim, 4),
                        risk=risk,
                        risk_type=risk_type,
                        matched_chars=matched,
                        diff_chars=diff,
                    ))

        high_risk = sum(1 for m in matches if m.similarity >= 0.85)

        return SimilarityResult(
            matches=sorted(matches, key=lambda x: x.similarity, reverse=True),
            mode=mode,
            threshold=threshold,
            total_comparisons=total_comparisons,
            high_risk_count=high_risk,
        )

    def _jaccard_global(
        self, ref: str, check: str, min_len: int
    ) -> Tuple[float, List[str], List[str]]:
        """全局Jaccard：将文本切分为字符n-gram集合"""
        ref_chars = set()
        check_chars = set()

        for i in range(len(ref) - min_len + 1):
            ref_chars.add(ref[i:i + min_len])

        for i in range(len(check) - min_len + 1):
            check_chars.add(check[i:i + min_len])

        if not ref_chars and not check_chars:
            return 0.0, [], []

        intersection = ref_chars & check_chars
        union = ref_chars | check_chars

        sim = len(intersection) / len(union) if union else 0.0

        matched = sorted(list(intersection))
        diff = sorted(list(ref_chars - check_chars))

        return sim, matched, diff

    def _jaccard_local(
        self, ref: str, check: str, min_len: int
    ) -> Tuple[float, List[str], List[str]]:
        """局部Jaccard：单字符粒度，检测名称微调"""
        ref_chars = set(ref.replace(" ", ""))
        check_chars = set(check.replace(" ", ""))

        if not ref_chars and not check_chars:
            return 0.0, [], []

        intersection = ref_chars & check_chars
        union = ref_chars | check_chars

        sim = len(intersection) / len(union) if union else 0.0

        matched = sorted(list(intersection))
        diff = sorted(list(ref_chars - check_chars))

        return sim, matched, diff

    def _assess_risk(
        self, ref: str, check: str, similarity: float, audit_type: str
    ) -> Tuple[str, str]:
        """评估相似度匹配的风险类型"""
        if similarity >= 0.95:
            return (
                f"极高相似度({similarity:.2%})，疑似同一条目重复或完全串换",
                "duplicate",
            )
        elif similarity >= 0.85:
            return (
                f"高相似度({similarity:.2%})，疑似名称微调/品名串换",
                "substitution",
            )
        elif similarity >= 0.7:
            return (
                f"中等相似度({similarity:.2%})，需人工确认是否为有意修改",
                "tweak",
            )
        else:
            return (
                f"低相似度({similarity:.2%})，偶发性匹配",
                "tweak",
            )


# ── MCP工具接口 ──────────────────────────────────────────────

def text_similarity_compare(
    reference_texts: List[str],
    check_texts: List[str],
    mode: str = "global",
    threshold: float = 0.7,
    audit_type: str = "general",
) -> dict:
    """MCP工具接口：text_similarity_compare"""
    comparator = TextSimilarityComparator()
    result = comparator.compare(
        reference_texts=reference_texts,
        check_texts=check_texts,
        mode=mode,
        threshold=threshold,
        audit_type=audit_type,
    )
    return {
        "matches": [asdict(m) for m in result.matches],
        "mode": result.mode,
        "threshold": result.threshold,
        "total_comparisons": result.total_comparisons,
        "high_risk_count": result.high_risk_count,
        "summary": (
            f"共比对{result.total_comparisons}组，发现{len(result.matches)}组匹配"
            f"（其中高风险{result.high_risk_count}组），"
            f"阈值={result.threshold}，模式={result.mode}"
        ),
    }
