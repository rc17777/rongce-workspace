"""
literature_collector.py — 文献自动采集脚本（v2 精准版）

策略：
  1. OpenAlex Concept 精确匹配（英文）：用 Audit 概念ID + 子概念
  2. OpenAlex 关键词搜索（中文）：添加后过滤，排除不相关
  3. 双重去重 + 相关度评分

用法：
  python scripts/literature_collector.py
  python scripts/literature_collector.py --digest-only
  python scripts/literature_collector.py --dry-run          # 只看统计，不保存
"""

import json, os, re, sys, time, hashlib
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import urllib.request, urllib.error, urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

# ── 路径 ──
WORKSPACE = Path(__file__).resolve().parent.parent
CONFIG_PATH = WORKSPACE / "config" / "literature_config.json"
OUTPUT_BASE = WORKSPACE / "knowledge" / "literature"
DIGEST_DIR = OUTPUT_BASE / "digests"

# ── 审计相关 OpenAlex 概念ID（精确匹配） ──
AUDIT_CONCEPTS = {
    "C199521495": "Audit",
    "C2909264111": "Financial Audit",
    "C152550464": "Performance audit",
    "C170856484": "Internal audit",
    "C13164825": "Operational auditing",
    "C2780587570": "Environmental audit",
    "C27504089": "Audit risk",
    "C58812954": "Audit substantive test",
    "C147859227": "Public sector",
}

# ── 审计相关关键词（中英文混合） ──
CORE_KEYWORDS = [
    # 中文核心
    "政府审计", "国家审计", "绩效审计", "财政审计", "专项资金审计",
    "经济责任审计", "预算执行审计", "政府会计", "公共资金", "财政监督",
    "政府治理", "审计全覆盖", "审计整改",
    # 英文核心
    "government audit", "public sector audit", "supreme audit institution",
    "public finance", "government accountability", "audit quality",
    "audit report lag", "audit opinion", "going concern",
    # 绩效/评价
    "performance measurement public sector", "public expenditure management",
    "fiscal transparency", "budgetary control",
]

# 排除不相关关键词（标题包含这些的大概率不是审计文献）
EXCLUDE_TITLE_PATTERNS = [
    r'(?i)\bclinical\b', r'(?i)\bmedical\b', r'(?i)\bcancer\b',
    r'(?i)\bdental\b', r'(?i)\bsurgery\b', r'(?i)\bpatient\b',
    r'(?i)\bnursing\b', r'(?i)\bpharma\b',
    r'(?i)\bneurological\b', r'(?i)\bpsychiatric\b',
    r'(?i)\bobstetric\b', r'(?i)\bpediatric\b',
    r'(?i)\bsoil\b', r'(?i)\bwater quality\b', r'(?i)\bair pollution\b',
    r'(?i)\bcrop\b', r'(?i)\bagricultural\b',
    r'(?i)\bclimate change adaptation\b',
    r'(?i)\belectric vehicle\b', r'(?i)\bbattery\b',
    r'(?i)\btextile\b', r'(?i)\bclothing\b',
    r'(?i)\bfood safety\b',
    r'(?i)\bethnic\b', r'(?i)\bminority\b', r'(?i)\bfolklore\b',
    r'(?i)\bsport\b', r'(?i)\bphysical education\b',
    r'(?i)\btourism\b', r'(?i)\bhotel\b',
    r'(?i)\be-commerce\b', r'(?i)\bsocial media\b',
    r'(?i)\binfluencer\b', r'(?i)\blivestream\b',
    r'(?i)\burban planning\b', r'(?i)\bhousing\b',
    r'(?i)\bcultural heritage\b', r'(?i)\bmuseum\b',
    r'(?i)\bvideo game\b', r'(?i)\bcinema\b', r'(?i)\bfilm\b',
    r'(?i)\buniversity student\b', r'(?i)\bcollege student\b',
]


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["storage"]["output_dir"] = str(WORKSPACE / cfg["storage"]["output_dir"])
    cfg["storage"]["digest_dir"] = str(WORKSPACE / cfg["storage"]["digest_dir"])
    return cfg


def slugify(text: str, max_len=80) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text[:max_len]


def safe_request(url: str, headers: dict = None, retries=3, timeout=20) -> Optional[dict]:
    if headers is None:
        headers = {"User-Agent": "RongCe-Literature-Collector/1.0"}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"  [WARN] 请求失败: {e}")
    return None


# ── 相关度评分 ──
def relevance_score(paper: dict) -> float:
    """返回 0.0~1.0 的相关度评分"""
    title = (paper.get("title") or "").lower()
    abstract = (paper.get("abstract_text") or "").lower()[:500]
    keywords = [k.lower() for k in (paper.get("keywords") or [])]
    concepts = [c.get("display_name", "").lower() for c in (paper.get("concepts") or [])]
    text = title + " " + abstract + " " + " ".join(keywords) + " " + " ".join(concepts)

    score = 0.0

    # 强信号词（+0.3 each）
    strong_signals = [
        "government audit", "public sector audit", "supreme audit", "state audit",
        "national audit office", "audit quality", "audit committee", "audit opinion",
        "performance audit", "financial audit", "internal control", "audit fee",
        "going concern", "audit report lag", "government accountability",
        "public expenditure", "fiscal transparency", "budget execution",
        "government accounting", "public sector accounting", "新公共管理",
        "绩效审计", "政府审计", "国家审计", "财政审计", "经济责任审计",
        "预算执行", "审计署", "审计整改", "审计全覆盖", "公共资金",
    ]
    for sig in strong_signals:
        if sig in text:
            score += 0.3

    # 中等信号词（+0.15 each）
    med_signals = [
        "audit", "accountability", "public sector", "government",
        "accounting", "financial reporting", "internal audit", "risk assessment",
        "compliance", "oversight", "transparency",
        "corpor governance", "earnings management", "discretionary accrual",
        "审计", "财政", "监督", "公共", "政府会计", "预算",
    ]
    for sig in med_signals:
        if sig in text:
            score += 0.15

    # 扣分：排除模式
    for pat in EXCLUDE_TITLE_PATTERNS:
        if re.search(pat, title):
            score -= 0.5

    return max(0.0, min(1.0, score))


def is_relevant(paper: dict, min_score=0.4) -> bool:
    return relevance_score(paper) >= min_score


# ── 采集策略1：按 Concept 精确匹配（高精度） ──
OPENALEX_BASE = "https://api.openalex.org/works"


def collect_by_concept(concept_id: str, per_page=50, from_year=2022, mailto="") -> List[Dict]:
    """按 OpenAlex Concept ID 精确匹配论文"""
    params = {
        "filter": "concept.id:{},publication_year:{}-,type:article|review|book-chapter".format(
            concept_id, from_year
        ),
        "sort": "cited_by_count:desc",
        "per_page": min(per_page, 200),
        "select": "id,doi,title,publication_date,authorships,primary_location,cited_by_count,keywords,concepts,abstract_inverted_index,language,type,open_access",
    }
    if mailto:
        params["mailto"] = mailto

    qs = urllib.parse.urlencode(params)
    url = "{}?{}".format(OPENALEX_BASE, qs)
    name = AUDIT_CONCEPTS.get(concept_id, concept_id)
    print("  [Concept] {} → 请求中...".format(name))
    data = safe_request(url)
    if not data or "results" not in data:
        print("  [Concept] {} 返回空".format(name))
        return []

    papers = parse_openalex_results(data.get("results", []))
    print("  [Concept] {} → {} 篇".format(name, len(papers)))
    return papers


def collect_by_keyword(keyword: str, per_page=50, from_year=2022, mailto="") -> List[Dict]:
    """按关键词搜索（补充，主要用于中文）"""
    params = {
        "search": keyword,
        "filter": "publication_year:{}-,type:article|review|book-chapter".format(from_year),
        "sort": "cited_by_count:desc",
        "per_page": min(per_page, 200),
        "select": "id,doi,title,publication_date,authorships,primary_location,cited_by_count,keywords,concepts,abstract_inverted_index,language,type,open_access",
    }
    if mailto:
        params["mailto"] = mailto

    qs = urllib.parse.urlencode(params)
    url = "{}?{}".format(OPENALEX_BASE, qs)
    print("  [Keyword] {} → 请求中...".format(keyword[:20]))
    data = safe_request(url)
    if not data or "results" not in data:
        print("  [Keyword] {} 返回空".format(keyword[:20]))
        return []

    papers = parse_openalex_results(data.get("results", []))
    print("  [Keyword] {} → {} 篇".format(keyword[:20], len(papers)))
    return papers


def parse_openalex_results(results: list) -> List[Dict]:
    """将 OpenAlex API 返回转换为统一格式"""
    papers = []
    for r in results:
        paper = {
            "source": "OpenAlex",
            "id": r.get("id", ""),
            "doi": r.get("doi"),
            "title": r.get("title", ""),
            "publication_date": r.get("publication_date", "") or "",
            "authors": [],
            "journal": "",
            "abstract_text": "",
            "keywords": [kw["display_name"] for kw in (r.get("keywords") or [])],
            "cited_by_count": r.get("cited_by_count", 0),
            "language": r.get("language", ""),
            "type": r.get("type", ""),
            "open_access": bool(r.get("open_access", {}).get("is_oa", False)),
            "landing_page_url": "",
            "concepts": r.get("concepts", []),
        }
        # 作者
        for auth in (r.get("authorships") or []):
            name = auth.get("author", {}).get("display_name", "")
            if name:
                paper["authors"].append(name)
        # 期刊
        loc = r.get("primary_location") or {}
        src = loc.get("source") or {}
        if src:
            paper["journal"] = src.get("display_name", "")
            paper["landing_page_url"] = loc.get("landing_page_url", "")
        # 摘要
        inv = r.get("abstract_inverted_index")
        if inv:
            words_pos = []
            for word, positions in inv.items():
                for pos in positions:
                    words_pos.append((pos, word))
            words_pos.sort()
            paper["abstract_text"] = " ".join(w for _, w in words_pos)
        papers.append(paper)
    return papers


# ── 去重 & 过滤 ──
def _safe_val(v: any) -> str:
    if v is None:
        return ""
    if not isinstance(v, str):
        return str(v)
    return v.strip().lower()


def deduplicate(papers: List[Dict]) -> List[Dict]:
    seen_dois = set()
    seen_titles = set()
    unique = []
    for p in papers:
        doi = _safe_val(p.get("doi"))
        title = _safe_val(p.get("title"))
        if doi and doi in seen_dois:
            continue
        if title and title in seen_titles:
            continue
        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.add(title)
        unique.append(p)
    return unique


def load_existing_ids() -> set:
    existing = set()
    if not OUTPUT_BASE.exists():
        return existing
    for f in OUTPUT_BASE.rglob("*.md"):
        if f.parent.name == "digests":
            continue
        content = f.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("doi:"):
                raw = line.split(":", 1)[1].strip().strip('"').strip("'").lower()
                if raw:
                    existing.add(raw)
            elif line.startswith("title:"):
                existing.add(line.split(":", 1)[1].strip().lower())
    return existing


# ── 保存 ──
SAVE_TEMPLATE = """---
source: {source}
doi: "{doi}"
publication_date: {pub_date}
journal: "{journal}"
cited_by: {cited_by}
open_access: {oa}
type: "{type_}"
language: "{lang}"
keywords: [{kw}]
collected_at: {collected}
---

# {title}

## 基本信息

| 字段 | 内容 |
|------|------|
| **来源** | {source} |
| **DOI** | [{doi}](https://doi.org/{doi_clean}) |
| **发表时间** | {pub_date} |
| **期刊** | {journal} |
| **引用次数** | {cited_by} |
| **开放获取** | {oa_label} |
| **类型** | {type_} |

## 作者

{authors_list}

## 关键词

{kw_list}

## 摘要

{abstract_text}

---

*自动采集于 {collected} | 来源: {source}*
"""


def save_paper(paper: Dict) -> Optional[Path]:
    """保存单篇文献"""
    pub_date = paper.get("publication_date") or ""
    year = pub_date[:4] if len(pub_date) >= 4 else "unknown"
    month = pub_date[5:7] if len(pub_date) >= 7 else "00"
    slug = slugify(paper.get("title", "untitled"))

    month_dir = Path(OUTPUT_BASE) / "{}-{}".format(year, month)
    month_dir.mkdir(parents=True, exist_ok=True)

    filepath = month_dir / "{}.md".format(slug)
    counter = 1
    while filepath.exists():
        filepath = month_dir / "{}-{}.md".format(slug, counter)
        counter += 1

    authors = paper.get("authors") or []
    keywords = paper.get("keywords") or []
    abstract = paper.get("abstract_text") or ""
    doi_raw = paper.get("doi")
    doi = _safe_val(doi_raw).replace("https://doi.org/", "")
    landing = paper.get("landing_page_url") or ""

    content = SAVE_TEMPLATE.format(
        source=paper.get("source", ""),
        doi=doi,
        pub_date=pub_date,
        authors=", ".join(authors),
        authors_list="\n".join("- {}".format(a) for a in authors) if authors else "（无）",
        journal=paper.get("journal") or "（未知）",
        cited_by=paper.get("cited_by_count", 0),
        oa=str(bool(paper.get("open_access", False))).lower(),
        oa_label="是" if paper.get("open_access", False) else "否",
        type_=paper.get("type", ""),
        lang=paper.get("language", ""),
        kw=", ".join(keywords) if keywords else "",
        kw_list="\n".join("- {}".format(kw) for kw in keywords) if keywords else "（无）",
        collected=datetime.now().strftime("%Y-%m-%d %H:%M"),
        title=paper.get("title", ""),
        doi_clean=doi,
        landing_url=landing or "https://doi.org/{}".format(doi),
        abstract_text=abstract[:2000] if abstract else "（无摘要）",
    )

    filepath.write_text(content, encoding="utf-8")
    return filepath


# ── 每日精选 ──
def generate_digest(papers_saved: List[tuple], force=False):
    today = date.today().isoformat()
    digest_file = Path(DIGEST_DIR) / "{}.md".format(today)
    if digest_file.exists() and not force:
        print("  [跳过] 当日精选已存在")
        return digest_file

    DIGEST_DIR.mkdir(parents=True, exist_ok=True)

    # 按相关度排序
    papers_saved.sort(key=lambda x: relevance_score(x[0]), reverse=True)

    lines = [
        "# 📚 文献精选 — {}".format(today),
        "",
        "本次采集：{} 篇新文献".format(len(papers_saved)),
        "",
        "---",
        "",
    ]

    for idx, (paper, fpath) in enumerate(papers_saved, 1):
        title = paper.get("title", "（无标题）")
        authors_short = ", ".join((paper.get("authors") or [])[:3])
        if len((paper.get("authors") or [])) > 3:
            authors_short += " 等"
        journal = paper.get("journal") or "（未知期刊）"
        pub_date = paper.get("publication_date", "")
        abstract = (paper.get("abstract_text") or "")[:300]
        cited = paper.get("cited_by_count", 0)
        score = relevance_score(paper)

        score_str = "⭐" if score >= 0.6 else ""
        lines.extend([
            "## {}. {}{}".format(idx, score_str, title),
            "",
            "- **作者**：{}".format(authors_short or "（无）"),
            "- **期刊**：{}".format(journal),
            "- **日期**：{}".format(pub_date),
            "- **引用**：{} 次".format(cited),
            "- **DOI**：{}".format(paper.get("doi", "")),
            "- **原文**：[链接]({})".format(fpath.relative_to(WORKSPACE)),
            "",
        ])
        if abstract:
            lines.append("> {}".format(abstract))
            lines.append("")

    lines.append("---")
    lines.append("*自动采集于 {} | {} 篇*".format(
        datetime.now().strftime("%Y-%m-%d %H:%M"), len(papers_saved)
    ))

    digest_file.write_text("\n".join(lines), encoding="utf-8")
    print("  ✅ 每日精选: {}".format(digest_file))
    return digest_file


# ── 主流程 ──
def main():
    import argparse
    parser = argparse.ArgumentParser(description="文献自动采集脚本 v2（精准版）")
    parser.add_argument("--digest-only", action="store_true", help="只生成每日精选")
    parser.add_argument("--dry-run", action="store_true", help="只看统计，不保存")
    parser.add_argument("--force", action="store_true", help="强制重新拉取")
    args = parser.parse_args()

    cfg = load_config()
    output_dir = Path(cfg["storage"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    mailto = cfg.get("openalex_mailto", "")
    filters = cfg.get("filters", {})
    from_year = filters.get("from_year", 2022)

    # ── 只生成精选 ──
    if args.digest_only:
        print("📋 只生成每日精选摘要...")
        papers_saved = []
        for f in sorted(output_dir.rglob("*.md")):
            if f.parent.name == "digests":
                continue
            content = f.read_text(encoding="utf-8")
            title = ""
            for line in content.splitlines():
                if line.startswith("# ") and not line.lstrip("#").startswith("#"):
                    title = line.replace("# ", "", 1).strip()
                    break
            if title:
                papers_saved.append(({"title": title}, f))
        digest_file = generate_digest(papers_saved, force=args.force)
        if digest_file:
            print("\n📋 每日精选已生成")
        return

    # ── 完整采集 ──
    print("=" * 60)
    print("📚 文献自动采集 v2（精准版）")
    print("   时间: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
    print("   输出: {}".format(output_dir))
    print("=" * 60)

    existing_ids = set() if args.force else load_existing_ids()
    print("   已有文献: {} 篇（增量跳过）".format(len(existing_ids)))

    all_papers = []
    total_limit = filters.get("max_total", 200)

    # ── Phase 1: 概念精确匹配（高精度） ──
    print("\n🔍 Phase 1: Concept 精确匹配...")
    for cid in AUDIT_CONCEPTS:
        if len(all_papers) >= total_limit:
            break
        papers = collect_by_concept(cid, per_page=30, from_year=from_year, mailto=mailto)
        all_papers.extend(papers)
        time.sleep(0.3)

    # ── Phase 2: 关键词补充（中文为主） ──
    # 只选中文关键词，因为英文概念已经覆盖了
    chinese_kw = [kw for kw in CORE_KEYWORDS if re.search(r'[\u4e00-\u9fff]', kw)]
    print("\n🔍 Phase 2: 关键词补充（中文）...")
    for kw in chinese_kw:
        if len(all_papers) >= total_limit:
            break
        papers = collect_by_keyword(kw, per_page=25, from_year=from_year, mailto=mailto)
        all_papers.extend(papers)
        time.sleep(0.3)

    # ── 去重 ──
    unique_papers = deduplicate(all_papers)
    print("\n📊 原始 {} → 去重后 {}".format(len(all_papers), len(unique_papers)))

    # ── 相关度过滤 ──
    relevant_papers = [p for p in unique_papers if is_relevant(p)]
    print("   相关度过滤后: {} 篇 (min_score≥0.4)".format(len(relevant_papers)))

    # ── 保存 ──
    new_count = 0
    papers_saved = []
    for paper in relevant_papers:
        doi = _safe_val(paper.get("doi"))
        title = _safe_val(paper.get("title"))
        if doi and doi in existing_ids:
            continue
        if title and title in existing_ids:
            continue
        if not title:
            continue

        if args.dry_run:
            papers_saved.append((paper, None))
            new_count += 1
        else:
            fpath = save_paper(paper)
            papers_saved.append((paper, fpath))
            new_count += 1

    print("\n💾 新保存: {} 篇".format(new_count))
    if new_count > 0:
        print("   路径: {}".format(output_dir))

    # ── 每日精选 ──
    if papers_saved and not args.dry_run:
        generate_digest(papers_saved, force=args.force)

    # ── 摘要 ──
    print("\n" + "=" * 60)
    print("✅ 采集完成")
    if papers_saved:
        papers_saved.sort(key=lambda x: relevance_score(x[0]), reverse=True)
        print("\n📌 今日新文献（按相关度排序 Top 15）:")
        for i, (p, f) in enumerate(papers_saved[:15], 1):
            title = (p.get("title") or "")[:65]
            score = relevance_score(p)
            stars = "⭐" * min(3, int(score / 0.3))
            print("   {:2d}. [{:.1f}] {} {}".format(i, score, stars, title))
        if len(papers_saved) > 15:
            print("       ... 还有 {} 篇".format(len(papers_saved) - 15))
    else:
        print("   无新文献（增量无变化）")
    print("=" * 60)

    # ── RAG 提示 ──
    if new_count > 0 and cfg.get("rag_pipeline", {}).get("auto_ingest", False):
        print("\n🔄 新文献已写入 knowledge/literature/")
        print("   RAG 重建: python scripts/rag_rebuild.py")

    return papers_saved


if __name__ == "__main__":
    main()