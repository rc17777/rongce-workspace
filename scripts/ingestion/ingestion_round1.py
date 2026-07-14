"""
Round 1: 规则匹配 — 零成本关键词+正则分类
"""
import re
import sys
from typing import List, Dict, Set
from dataclasses import dataclass, field

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from taxonomy_manager import get_taxonomy


@dataclass
class Round1Result:
    direct_hits: List[str] = field(default_factory=list)  # [L4, L12]
    matched_by: List[str] = field(default_factory=list)    # 命中的关键词
    method: str = 'keyword_match'


# 公文号前缀 → 业务线映射
DOCNUM_PREFIX_MAP = {
    '财预': ['L3', 'L11'],      # 预算 / 绩效
    '财社': ['L4'],              # 专项资金-社保
    '财建': ['L10'],             # 工程
    '财会': ['L3', 'L5'],       # 预算 / 往来款
    '财监': ['L13'],             # 监督检查
    '财金': ['L4'],              # 专项资金-金融
    '财教': ['L4'],              # 专项资金-教育
    '财农': ['L4'],              # 专项资金-农业
    '财资': ['L5', 'L7'],       # 往来款 / 国企
    '国资产权': ['L7'],          # 国企
    '国资发': ['L7'],            # 国企
    '审办': ['L1'],              # 经责
    '审财': ['L2', 'L3'],       # 收支 / 预算
    '发改投资': ['L6', 'L10'],  # 招投标 / 工程
    '发改价格': ['L8'],          # 成本效益
}

# 来源类型推断
SOURCE_TYPE_KEYWORDS = {
    'government_policy': ['部', '局', '办公厅', '财政部', '审计署', '国资委', '发文字号', '〔20'],
    'court_judgment': ['判决书', '裁定书', '法院', '民初', '行初', '刑初'],
    'industry_report': ['行业报告', '白皮书', '蓝皮书', '调研报告', '年度报告'],
}


def classify_round1(text: str, title: str = '', doc_number: str = '') -> Round1Result:
    """
    Round 1 classification: rule-based keyword + pattern matching.
    Zero API cost.

    Args:
        text: Full document text (or first 5000 chars)
        title: Document title
        doc_number: Government document number (e.g., "财预〔2026〕XX号")
    """
    taxonomy = get_taxonomy()
    lines = taxonomy.get_active_lines()
    result = Round1Result()
    hit_lines: Set[str] = set()
    matched_keywords: Set[str] = set()
    search_text = f"{title}\n{text[:5000]}"

    for line in lines:
        lid = line['id']
        keywords = line.get('keywords', {})
        detection_rules = line.get('detection_rules', [])

        # Step 1: Regex detection_rules (highest priority)
        for rule in detection_rules:
            pattern = rule.get('pattern', '')
            if pattern and re.search(pattern, search_text):
                hit_lines.add(lid)
                matched_keywords.add(f'regex:{pattern[:40]}')
                break
        else:
            # Step 2: Primary keywords — any match = hit
            primary_hit = False
            for kw in keywords.get('primary', []):
                if kw in search_text:
                    hit_lines.add(lid)
                    matched_keywords.add(kw)
                    primary_hit = True
                    break

            # Step 3: Secondary keywords — need ≥2 matches
            if not primary_hit:
                secondary_count = 0
                secondary_hits = []
                for kw in keywords.get('secondary', []):
                    if kw in search_text:
                        secondary_count += 1
                        secondary_hits.append(kw)
                if secondary_count >= 2:
                    hit_lines.add(lid)
                    matched_keywords.update(secondary_hits)

    # Step 4: Document number prefix inference
    if doc_number:
        for prefix, line_ids in DOCNUM_PREFIX_MAP.items():
            if doc_number.startswith(prefix):
                hit_lines.update(line_ids)
                matched_keywords.add(f'docnum:{prefix}')

    result.direct_hits = sorted(list(hit_lines))
    result.matched_by = sorted(list(matched_keywords))
    return result


def infer_source_type(text: str, url: str = '') -> str:
    """Infer document source type from content patterns."""
    text_sample = text[:2000]

    # URL-based inference first
    if url:
        if 'ccgp.gov.cn' in url or 'ggzy' in url or 'cebpubservice' in url:
            return 'tender_announcement'
        if 'wenshu.court.gov.cn' in url:
            return 'court_judgment'
        if 'weixin.qq.com' in url or 'mp.weixin' in url:
            return 'wechat_article'
        if 'gov.cn' in url:
            return 'government_policy'

    # Content-based inference
    # Check tender announcement patterns first
    tender_signals = ['采购公告', '招标公告', '中标公告', '成交公告', '采购项目',
                      '招标项目', '采购人', '代理机构', '中标供应商', '成交供应商']
    tender_score = sum(1 for kw in tender_signals if kw in text_sample)
    if tender_score >= 2:
        return 'tender_announcement'

    type_scores = {}
    for stype, keywords in SOURCE_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_sample)
        type_scores[stype] = score

    if url:
        if 'weixin.qq.com' in url or 'mp.weixin' in url:
            return 'wechat_article'
        if 'gov.cn' in url:
            return 'government_policy'
        if 'court.gov.cn' in url or 'wenshu.court.gov.cn' in url:
            return 'court_judgment'

    # Pick the type with highest keyword score
    if type_scores:
        best = max(type_scores, key=type_scores.get)
        if type_scores[best] >= 1:
            return best

    return 'other'


def extract_doc_number(text: str) -> str:
    """Extract Chinese government document number (e.g., 财预〔2026〕XX号)."""
    patterns = [
        r'([\u4e00-\u9fff]{2,6}〔\d{4}〕\d+号)',
        r'([\u4e00-\u9fff]{2,6}\[\d{4}\]\d+号)',
        r'([\u4e00-\u9fff]{2,6}函〔\d{4}〕\d+号)',
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            return match.group(1)
    return ''
