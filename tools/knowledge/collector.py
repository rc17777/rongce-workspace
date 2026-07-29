"""
融策知识Agent — 多源采集器
==========================
支持 RSS 订阅、HTML 页面解析、GitHub Trending 等多种采集源。
配置从 sources.yaml 读取，内置 URL 去重。

依赖: requests, beautifulsoup4, pyyaml
"""

import json
import logging
import hashlib
import time
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, field

import requests
import yaml
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ============================================================
# 可配置参数
# ============================================================
REQUEST_TIMEOUT = 30                  # 请求超时（秒）
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_ARTICLES_PER_SOURCE = 20          # 每个源最多采集文章数
SEEN_URLS_FILE = "logs/seen_urls.json"  # 去重记录文件
# ============================================================


@dataclass
class Article:
    """采集到的文章"""
    title: str
    url: str
    source_name: str                   # 来源名称（如"财政部-财政新闻"）
    domain: int                        # 知识域编号 1/2/3
    publish_date: str = ""             # YYYY-MM-DD
    summary: str = ""                  # 前200字摘要
    raw_html: str = ""                 # 原始HTML（可选）
    fetched_at: str = ""               # 采集时间

    @property
    def url_hash(self) -> str:
        return hashlib.md5(self.url.encode()).hexdigest()[:12]


class Collector:
    """多源采集器"""

    def __init__(self, sources_path: str = None):
        """
        Args:
            sources_path: sources.yaml 的路径，默认为工具目录下的 sources.yaml
        """
        if sources_path is None:
            sources_path = str(Path(__file__).parent / "sources.yaml")
        self.sources_path = Path(sources_path)
        self.sources = self._load_sources()
        self.seen_urls: set[str] = set()
        self._load_seen_urls()

    def _load_sources(self) -> dict:
        """加载采集源配置"""
        if not self.sources_path.exists():
            logger.warning(f"sources.yaml 不存在: {self.sources_path}，使用空配置")
            return {"sources": {}}

        with open(self.sources_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config.get("sources", {})

    def _load_seen_urls(self):
        """加载已采集URL记录"""
        seen_path = Path(SEEN_URLS_FILE)
        if seen_path.exists():
            try:
                with open(seen_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.seen_urls = set(data.get("urls", []))
            except (json.JSONDecodeError, KeyError):
                self.seen_urls = set()

    def _save_seen_urls(self):
        """保存已采集URL记录"""
        seen_path = Path(SEEN_URLS_FILE)
        seen_path.parent.mkdir(parents=True, exist_ok=True)
        with open(seen_path, "w", encoding="utf-8") as f:
            json.dump({"urls": list(self.seen_urls), "updated_at": datetime.now().isoformat()}, f)

    def _fetch_page(self, url: str) -> Optional[str]:
        """抓取网页HTML"""
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )
            resp.raise_for_status()
            # 自动检测编码
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except requests.RequestException as e:
            logger.error(f"抓取失败 [{url}]: {e}")
            return None

    def _parse_date(self, text: str) -> str:
        """从文本中提取日期 YYYY-MM-DD 格式"""
        patterns = [
            r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})',  # 2024-01-15 或 2024年1月15日
            r'(\d{4})(\d{2})(\d{2})',                     # 20240115
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                year, month, day = m.groups()
                return f"{year}-{int(month):02d}-{int(day):02d}"
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_summary(self, html: str, max_chars: int = 200) -> str:
        """从HTML提取前N字的文本摘要"""
        soup = BeautifulSoup(html, "html.parser")
        # 移除 script/style 标签
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # 压缩空白
        text = re.sub(r'\s+', ' ', text)
        return text[:max_chars] + ("..." if len(text) > max_chars else "")

    # ============================================================
    # 各类采集策略
    # ============================================================

    def _collect_html_parse(self, source: dict, domain: int) -> list[Article]:
        """
        HTML页面解析采集
        提取页面上所有 <a> 标签中的链接，过滤出文章列表
        """
        url = source["url"]
        name = source["name"]
        selector = source.get("selector", "a")            # CSS选择器
        link_filter = source.get("link_filter", "")        # 链接URL过滤关键词
        base_url = source.get("base_url", url)             # 相对链接的基URL

        html = self._fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        articles = []

        # 提取链接
        links = soup.select(selector)
        count = 0
        for link in links:
            if count >= MAX_ARTICLES_PER_SOURCE:
                break

            href = link.get("href", "")
            if not href:
                continue

            # 过滤
            if link_filter and link_filter not in href:
                continue

            # 转为绝对URL
            full_url = urljoin(base_url, href)
            # 去重
            url_hash = hashlib.md5(full_url.encode()).hexdigest()[:12]
            if url_hash in self.seen_urls:
                continue

            # 提取标题
            title = link.get_text(strip=True) or link.get("title", "") or urlparse(full_url).path.split("/")[-1]
            if not title or len(title) < 4:
                continue

            # 尝试提取日期（从父元素或相邻元素）
            parent_text = link.parent.get_text() if link.parent else ""

            article = Article(
                title=title,
                url=full_url,
                source_name=name,
                domain=domain,
                publish_date=self._parse_date(parent_text),
                fetched_at=datetime.now().isoformat()
            )
            articles.append(article)
            self.seen_urls.add(url_hash)
            count += 1

            logger.info(f"  [{name}] {title[:50]}...")

        return articles

    def _collect_rss_alt(self, source: dict, domain: int) -> list[Article]:
        """
        非标准RSS采集：尝试查找页面上的RSS链接或提取类RSS结构
        （中国很多政府网站用的是自定义格式，不是标准RSS）
        回退到 HTML 解析模式
        """
        # 大多数中国政府网站没有标准RSS，直接用HTML解析
        return self._collect_html_parse(source, domain)

    def _collect_github_trending(self, source: dict, domain: int) -> list[Article]:
        """GitHub Trending 采集"""
        url = source["url"]
        name = source["name"]

        html = self._fetch_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        articles = []

        # GitHub Trending 结构：article.Box-row
        repos = soup.select("article.Box-row")
        for repo in repos[:MAX_ARTICLES_PER_SOURCE]:
            # 仓库名
            h2 = repo.select_one("h2")
            if not h2:
                continue
            repo_name = h2.get_text(strip=True).replace("\n", " ").replace("  ", " ")

            # 链接
            link = h2.select_one("a")
            href = link.get("href", "") if link else ""
            full_url = urljoin("https://github.com", href) if href else ""

            url_hash = hashlib.md5(full_url.encode()).hexdigest()[:12]
            if url_hash in self.seen_urls:
                continue

            # 描述
            desc_el = repo.select_one("p")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            summary = desc[:200]

            # 语言和星数
            lang_el = repo.select_one("[itemprop='programmingLanguage']")
            lang = lang_el.get_text(strip=True) if lang_el else ""
            stars_el = repo.select_one(".octicon-star")
            stars_parent = stars_el.parent if stars_el else None
            stars = stars_parent.get_text(strip=True).replace(",", "") if stars_parent else "0"

            article = Article(
                title=f"{repo_name} ⭐{stars} [{lang}]",
                url=full_url,
                source_name=name,
                domain=domain,
                summary=summary,
                publish_date=datetime.now().strftime("%Y-%m-%d"),
                fetched_at=datetime.now().isoformat()
            )
            articles.append(article)
            self.seen_urls.add(url_hash)
            logger.info(f"  [{name}] {repo_name[:60]}")

        return articles

    def _collect_arxiv(self, source: dict, domain: int) -> list[Article]:
        """arXiv 论文采集"""
        url = source["url"]
        name = source["name"]
        categories = source.get("categories", ["cs.CL", "cs.AI"])

        articles = []
        for cat in categories:
            cat_url = f"{url}list/{cat}/new"
            html = self._fetch_page(cat_url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            papers = soup.select("dd")[:MAX_ARTICLES_PER_SOURCE]

            for paper in papers:
                # arXiv 结构比较特殊
                title_el = paper.select_one(".list-title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True).replace("Title:", "").strip()

                abs_url_el = paper.select_one(".list-identifier a")
                abs_url = urljoin("https://arxiv.org", abs_url_el.get("href", "")) if abs_url_el else ""

                url_hash = hashlib.md5(abs_url.encode()).hexdigest()[:12]
                if url_hash in self.seen_urls:
                    continue

                abs_el = paper.select_one(".mathjax")
                summary = abs_el.get_text(strip=True)[:200] if abs_el else ""

                article = Article(
                    title=title,
                    url=abs_url,
                    source_name=name,
                    domain=domain,
                    summary=summary,
                    publish_date=datetime.now().strftime("%Y-%m-%d"),
                    fetched_at=datetime.now().isoformat()
                )
                articles.append(article)
                self.seen_urls.add(url_hash)

        return articles

    # ============================================================
    # 主采集方法
    # ============================================================

    def collect(self, domain: Optional[int] = None, dry_run: bool = False) -> list[Article]:
        """
        执行全量采集

        Args:
            domain: 指定域编号（1/2/3），None表示全部
            dry_run: 仅采集不记录去重

        Returns:
            list[Article]: 采集到的文章列表
        """
        all_articles: list[Article] = []

        source_types = {
            "html_parse": self._collect_html_parse,
            "rss_alt": self._collect_rss_alt,
            "github_trending": self._collect_github_trending,
            "arxiv": self._collect_arxiv,
        }

        for domain_key, source_list in self.sources.items():
            # 提取域编号
            try:
                dom_id = int(domain_key.split("_")[1])
            except (IndexError, ValueError):
                dom_id = 0

            # 域过滤
            if domain is not None and dom_id != domain:
                continue

            logger.info(f"开始采集 域{dom_id}（{len(source_list)} 个源）")

            for source in source_list:
                source_type = source.get("type", "html_parse")
                collector_fn = source_types.get(source_type, self._collect_html_parse)

                try:
                    articles = collector_fn(source, dom_id)
                    all_articles.extend(articles)
                    logger.info(f"  完成: {source['name']} → {len(articles)} 篇")
                except Exception as e:
                    logger.error(f"  采集失败 [{source['name']}]: {e}", exc_info=True)

                # 礼貌地间隔一下
                time.sleep(0.5)

        if not dry_run:
            self._save_seen_urls()

        logger.info(f"采集完成: 共 {len(all_articles)} 篇")
        return all_articles

    def clear_seen_urls(self, days_old: int = 30):
        """清理N天前的去重记录，防止无限膨胀"""
        # 简单策略：保留最近的记录，清空旧文件
        seen_path = Path(SEEN_URLS_FILE)
        if seen_path.exists():
            bak = seen_path.with_suffix(".json.bak")
            seen_path.rename(bak)
            logger.info(f"已清空去重记录，旧文件保存为 {bak}")


# ============================================================
# CLI入口
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="多源采集器")
    parser.add_argument("--domain", type=int, choices=[1, 2, 3], help="指定域编号")
    parser.add_argument("--dry-run", action="store_true", help="仅采集不记录去重")
    parser.add_argument("--output", help="输出JSON文件路径")
    parser.add_argument("--sources", help="sources.yaml路径")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    collector = Collector(sources_path=args.sources)
    articles = collector.collect(domain=args.domain, dry_run=args.dry_run)

    # 输出
    output_data = [
        {
            "title": a.title,
            "url": a.url,
            "source": a.source_name,
            "domain": a.domain,
            "publish_date": a.publish_date,
            "summary": a.summary,
            "fetched_at": a.fetched_at,
            "url_hash": a.url_hash
        }
        for a in articles
    ]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"[✓] 结果已保存: {args.output}")
    else:
        print(json.dumps(output_data, ensure_ascii=False, indent=2))

    print(f"\n共采集 {len(articles)} 篇文章")


if __name__ == "__main__":
    main()
