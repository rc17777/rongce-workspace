"""
智能摘要器
==========
对采集文章进行智能摘要，提取核心要点、适用场景和优先级判定。
支持本地大模型API调用和规则回退两种模式。

依赖: requests
"""

import json
import logging
import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ============================================================
# 可配置参数
# ============================================================
API_URL = os.environ.get("OPENCLAW_API_URL", "http://127.0.0.1:18789/api")
SUMMARY_MAX_CHARS = 500               # 摘要最大字符数
# ============================================================

# 优先级判定关键词
P0_KEYWORDS = [
    "发布", "施行", "废止", "修订", "新规", "通知", "办法", "条例",
    "司法解释", "公告", "决定", "令", "意见", "关于印发"
]
P1_KEYWORDS = [
    "案例", "分析", "方法", "实践", "经验", "探讨", "研究",
    "评测", "对比", "指南", "教程", "调查报告"
]
P2_KEYWORDS = [
    "新闻", "动态", "会议", "讲话", "致辞", "活动", "评选"
]


@dataclass
class SummarizedArticle:
    """摘要后的文章"""
    title: str
    url: str
    source_name: str
    domain: int
    publish_date: str
    core_point: str                    # 一句话核心要点
    applicable_scenario: str          # 适用场景
    priority: str                     # P0/P1/P2
    keywords: list[str] = field(default_factory=list)
    full_summary: str = ""            # 完整摘要
    kb_entry_id: str = ""             # KB条目ID（归档时生成）


def _classify_priority(title: str, content: str = "") -> str:
    """根据标题和内容判定优先级"""
    combined = f"{title} {content}"

    # 检查P0关键词
    for kw in P0_KEYWORDS:
        if kw in combined:
            return "P0"

    # 检查P1关键词
    for kw in P1_KEYWORDS:
        if kw in combined:
            return "P1"

    # 默认P2
    return "P2"


def _extract_core_point(title: str, content: str) -> str:
    """提取一句话核心要点"""
    # 简单规则：取标题+内容第一句
    # 去掉"关于印发""关于转发"等冗余前缀
    cleaned = re.sub(r'^(关于印发|关于转发|关于公布|关于做好)\s*', '', title.strip())
    # 截断
    if len(cleaned) > 80:
        cleaned = cleaned[:80] + "…"

    # 如果内容不为空，追加第一句
    if content:
        # 提取内容第一句（到第一个句号）
        first_sentence = re.split(r'[。！？]', content)[0].strip()
        if len(first_sentence) > 20 and len(first_sentence) < 200:
            cleaned += f"。{first_sentence}"

    return cleaned[:SUMMARY_MAX_CHARS]


def _extract_keywords(title: str, content: str) -> list[str]:
    """从标题和内容提取关键词"""
    combined = f"{title} {content[:200]}"
    # 简单的名词提取：去掉常见停用词后取最长词
    stopwords = {"的", "了", "在", "是", "和", "与", "及", "对", "等", "为", "被", "把"}
    words = re.findall(r'[\u4e00-\u9fff]{2,}', combined)
    keywords = [w for w in words if w not in stopwords]
    # 去重并取前8个
    seen = set()
    unique_kw = []
    for kw in keywords:
        if kw not in seen and len(kw) >= 2:
            seen.add(kw)
            unique_kw.append(kw)
    return unique_kw[:8]


def _get_applicable_scenario(domain: int, title: str, priority: str) -> str:
    """根据域和标题推断适用场景"""
    domain_scenarios = {
        1: {
            "专项债": "专项债申报审核",
            "绩效": "绩效评价",
            "预算": "预算编制审核",
            "采购": "政府采购检查",
            "财政": "财政监督检查",
            "审计": "审计方法",
            "会计": "会计核算",
            "资金": "资金管理合规",
        },
        2: {
            "造价": "工程造价审核",
            "定额": "定额套用",
            "清单": "工程量清单编制",
            "合同": "合同管理",
            "招标": "招投标管理",
            "施工": "施工管理",
            "竣工": "竣工结算",
            "法律": "司法鉴定",
        },
        3: {
            "Agent": "多Agent系统设计",
            "RAG": "知识库检索增强",
            "LLM": "大模型应用",
            "NLP": "文本分析",
            "Python": "工具开发",
            "机器学习": "数据分析",
            "检测": "异常检测",
            "生成": "内容生成",
        },
    }

    scenarios = domain_scenarios.get(domain, {})
    for kw, scenario in scenarios.items():
        if kw in title:
            return scenario

    generic = {
        1: "审计方法参考",
        2: "工程管理参考",
        3: "AI技术跟踪",
    }
    return generic.get(domain, "通用参考")


def summarize_with_api(article: dict, api_url: str = API_URL) -> Optional[SummarizedArticle]:
    """
    调用本地大模型API进行摘要

    Args:
        article: 采集到的文章dict（含title, url, source_name, domain, content等）
        api_url: API地址

    Returns:
        SummarizedArticle 或 None（API不可用时回退到规则模式）
    """
    # 构建提示词
    title = article.get("title", "")
    content = article.get("content", article.get("summary", ""))
    domain = article.get("domain", 1)

    prompt = f"""请对以下文章进行摘要分析，输出JSON格式：

标题: {title}
内容: {content[:1000]}

请输出:
{{
    "core_point": "一句话核心要点（50字以内）",
    "applicable_scenario": "适用场景（如：专项债申报、绩效评价、造价审核等）",
    "priority": "P0/P1/P2",
    "keywords": ["关键词1", "关键词2"],
    "full_summary": "完整摘要（200字以内）"
}}

优先级规则: P0=新法规/政策变更, P1=方法论/案例, P2=一般信息"""

    try:
        resp = requests.post(
            api_url,
            json={"prompt": prompt, "max_tokens": 500},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code != 200:
            raise Exception(f"API返回 {resp.status_code}")

        result = resp.json()
        # 尝试从多种可能的响应格式中提取
        text = result.get("response") or result.get("text") or result.get("content") or "{}"

        # 尝试解析JSON
        try:
            summary = json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取JSON块
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                summary = json.loads(m.group())
            else:
                raise

        return SummarizedArticle(
            title=title,
            url=article.get("url", ""),
            source_name=article.get("source_name", ""),
            domain=domain,
            publish_date=article.get("publish_date", ""),
            core_point=summary.get("core_point", _extract_core_point(title, content)),
            applicable_scenario=summary.get("applicable_scenario", _get_applicable_scenario(domain, title, "P1")),
            priority=summary.get("priority", _classify_priority(title, content)),
            keywords=summary.get("keywords", _extract_keywords(title, content)),
            full_summary=summary.get("full_summary", content[:200])
        )

    except Exception as e:
        logger.warning(f"API摘要失败，回退到规则模式: {e}")
        return None


def summarize_with_rules(article: dict) -> SummarizedArticle:
    """基于规则的摘要（API不可用时的回退方案）"""
    title = article.get("title", "")
    content = article.get("content", article.get("summary", ""))
    domain = article.get("domain", 1)
    priority = _classify_priority(title, content)

    return SummarizedArticle(
        title=title,
        url=article.get("url", ""),
        source_name=article.get("source_name", ""),
        domain=domain,
        publish_date=article.get("publish_date", ""),
        core_point=_extract_core_point(title, content),
        applicable_scenario=_get_applicable_scenario(domain, title, priority),
        priority=priority,
        keywords=_extract_keywords(title, content),
        full_summary=content[:200] if content else title
    )


def summarize(articles: list[dict], use_api: bool = False) -> list[SummarizedArticle]:
    """
    对文章列表进行批量摘要

    Args:
        articles: 采集到的文章列表
        use_api: 是否使用大模型API（默认False，使用规则模式）

    Returns:
        list[SummarizedArticle]: 摘要后的文章列表
    """
    results = []
    for article in articles:
        if use_api:
            result = summarize_with_api(article)
            if result is None:
                result = summarize_with_rules(article)
        else:
            result = summarize_with_rules(article)

        results.append(result)
        logger.info(f"摘要完成 [{result.priority}] {result.title[:50]}...")

    logger.info(f"摘要完成: 共 {len(results)} 篇")
    return results


# ============================================================
# CLI入口
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="智能摘要器")
    parser.add_argument("--input", required=True, help="输入JSON文件路径（采集结果）")
    parser.add_argument("--output", required=True, help="输出JSON文件路径")
    parser.add_argument("--use-api", action="store_true", help="使用大模型API摘要")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    with open(args.input, "r", encoding="utf-8") as f:
        articles = json.load(f)

    results = summarize(articles, use_api=args.use_api)

    output_data = [
        {
            "title": r.title,
            "url": r.url,
            "source_name": r.source_name,
            "domain": r.domain,
            "publish_date": r.publish_date,
            "core_point": r.core_point,
            "applicable_scenario": r.applicable_scenario,
            "priority": r.priority,
            "keywords": r.keywords,
            "full_summary": r.full_summary
        }
        for r in results
    ]

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"[✓] 摘要结果已保存: {args.output}")
    print(f"P0: {sum(1 for r in results if r.priority == 'P0')}")
    print(f"P1: {sum(1 for r in results if r.priority == 'P1')}")
    print(f"P2: {sum(1 for r in results if r.priority == 'P2')}")


if __name__ == "__main__":
    main()
