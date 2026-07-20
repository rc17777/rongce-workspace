#!/usr/bin/env python3
"""
wiki_lint.py — wiki 知识库健康检查
规则引擎 (L1) + 量化指标报告

用法:
  python -X utf8 scripts/wiki_lint.py              # 全量检查
  python -X utf8 scripts/wiki_lint.py --report    # 生成量化报告
  python -X utf8 scripts/wiki_lint.py --fix-dry   # 预演修复
"""
import re, json, sys, sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(__file__).parent.parent
WIKI_DIR = WORKSPACE / "obsidian-vault" / "wiki"
CONFIG_DIR = WORKSPACE / "config"
DB_PATH = CONFIG_DIR / "entity_registry.sqlite"


class WikiLinter:
    """wiki 健康检查器"""

    def __init__(self):
        self.issues = []
        self.metrics = {}

    def run_all(self):
        """运行全部检查"""
        print("=" * 50)
        print("wiki 健康检查")
        print("=" * 50)

        pages = list(WIKI_DIR.rglob("*.md")) if WIKI_DIR.exists() else []

        self.check_broken_links(pages)
        self.check_orphans(pages)
        self.check_frontmatter(pages)
        self.check_deprecated_refs(pages)
        self.check_duplicates(pages)
        self.check_content_quality(pages)
        self.check_registry_health()
        self.check_degraded_tasks()

        self._compute_metrics(pages)
        self._print_report()

    # ---- 检查项 ----

    def check_broken_links(self, pages):
        count = 0
        for wp in pages:
            content = wp.read_text(encoding='utf-8', errors='replace')
            links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
            for link in links:
                link_name = link.split('#')[0].strip()
                target = WIKI_DIR / f"{link_name}.md"
                if not target.exists():
                    self.issues.append({
                        'type': 'broken_link', 'severity': 'P1',
                        'source': str(wp.relative_to(WORKSPACE)),
                        'detail': f"断链: [[{link}]] → 目标页面不存在"
                    })
                    count += 1
        self.metrics['broken_links'] = count

    def check_orphans(self, pages):
        if not pages:
            return
        # 统计每页的入链数
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        for wp in pages:
            content = wp.read_text(encoding='utf-8', errors='replace')
            links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
            out_degree[str(wp)] = len(links)
            for link in links:
                link_name = link.split('#')[0].strip()
                target = WIKI_DIR / f"{link_name}.md"
                in_degree[str(target)] += 1

        orphans = 0
        for wp in pages:
            total = in_degree.get(str(wp), 0) + out_degree.get(str(wp), 0)
            if total < 2:
                self.issues.append({
                    'type': 'orphan_page', 'severity': 'P2',
                    'source': str(wp.relative_to(WORKSPACE)),
                    'detail': f"孤立页面: 入链={in_degree.get(str(wp),0)}, 出链={out_degree.get(str(wp),0)}"
                })
                orphans += 1
        self.metrics['orphan_pages'] = orphans
        self.metrics['orphan_rate'] = orphans / len(pages) if pages else 0

    def check_frontmatter(self, pages):
        missing = 0
        incomplete = 0
        for wp in pages:
            content = wp.read_text(encoding='utf-8', errors='replace')
            if not content.startswith('---'):
                self.issues.append({
                    'type': 'missing_frontmatter', 'severity': 'P2',
                    'source': str(wp.relative_to(WORKSPACE)),
                    'detail': "缺少 YAML frontmatter"
                })
                missing += 1
            else:
                # 检查必要字段
                fm_text = content.split('---', 2)[1]
                required = ['title', 'type', 'source_type']
                for field in required:
                    if field not in fm_text:
                        incomplete += 1
                        self.issues.append({
                            'type': 'incomplete_frontmatter', 'severity': 'P2',
                            'source': str(wp.relative_to(WORKSPACE)),
                            'detail': f"frontmatter 缺少字段: {field}"
                        })
        self.metrics['missing_frontmatter'] = missing
        self.metrics['incomplete_frontmatter'] = incomplete

    def check_deprecated_refs(self, pages):
        """检查引用已废止法规"""
        if not DB_PATH.exists():
            return
        with sqlite3.connect(str(DB_PATH)) as db:
            db.row_factory = sqlite3.Row
            deprecated = db.execute(
                "SELECT canonical_name FROM entities WHERE entity_type='regulation' AND review_status='deprecated'"
            ).fetchall()
            deprecated_names = set(r['canonical_name'] for r in deprecated)

        count = 0
        for wp in pages:
            content = wp.read_text(encoding='utf-8', errors='replace')
            for name in deprecated_names:
                if name in content:
                    self.issues.append({
                        'type': 'deprecated_reg_ref', 'severity': 'P1',
                        'source': str(wp.relative_to(WORKSPACE)),
                        'detail': f"引用已废止法规: {name}"
                    })
                    count += 1
        self.metrics['deprecated_refs'] = count

    def check_duplicates(self, pages):
        """检查疑似重复页面"""
        from difflib import SequenceMatcher

        names = {}
        for wp in pages:
            name = wp.stem
            if name in names:
                self.issues.append({
                    'type': 'duplicate_page', 'severity': 'P2',
                    'source': str(wp.relative_to(WORKSPACE)),
                    'detail': f"疑似重复: {name} (已有 {names[name]})"
                })
            else:
                names[name] = str(wp.relative_to(WORKSPACE))

    def check_content_quality(self, pages):
        """内容质量检查"""
        short_pages = 0
        no_summary = 0

        for wp in pages:
            content = wp.read_text(encoding='utf-8', errors='replace')
            body = content.split('---', 2)[-1] if content.startswith('---') else content
            body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
            body = re.sub(r'[#>\-\s*|]', '', body).strip()

            if len(body) < 200:
                self.issues.append({
                    'type': 'short_page', 'severity': 'P2',
                    'source': str(wp.relative_to(WORKSPACE)),
                    'detail': f"页面太短 ({len(body)} 字符)，可能不完整"
                })
                short_pages += 1

            fm_text = content.split('---', 2)[1] if content.startswith('---') else ''
            if 'summary' not in fm_text:
                no_summary += 1

        self.metrics['short_pages'] = short_pages
        self.metrics['no_summary_pages'] = no_summary

    def check_registry_health(self):
        """注册表健康度"""
        if not DB_PATH.exists():
            self.metrics['registry_exists'] = False
            return
        self.metrics['registry_exists'] = True
        with sqlite3.connect(str(DB_PATH)) as db:
            total = db.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            with_source = db.execute("SELECT COUNT(*) FROM entities WHERE source_doc_id IS NOT NULL").fetchone()[0]
            without_alias = db.execute("""
                SELECT COUNT(*) FROM entities e
                WHERE NOT EXISTS (SELECT 1 FROM aliases a WHERE a.entity_id=e.id)
            """).fetchone()[0]
            no_evidence_rels = db.execute("""
                SELECT COUNT(*) FROM relations WHERE evidence_quote IS NULL AND relation_status='confirmed'
            """).fetchone()[0]

        self.metrics['entities_total'] = total
        self.metrics['entities_with_source'] = with_source
        self.metrics['source_coverage_rate'] = with_source / total if total else 0
        self.metrics['entities_without_alias'] = without_alias
        self.metrics['no_evidence_relations'] = no_evidence_rels

    def check_degraded_tasks(self):
        """降级任务检查"""
        if not DB_PATH.exists():
            return
        with sqlite3.connect(str(DB_PATH)) as db:
            unreplayed = db.execute("SELECT COUNT(*) FROM degradation_log WHERE replayed=0").fetchone()[0]
        self.metrics['unreplayed_degradations'] = unreplayed
        if unreplayed > 0:
            self.issues.append({
                'type': 'unreplayed_degradation', 'severity': 'P1',
                'source': 'degradation_log',
                'detail': f"{unreplayed} 条降级任务未回补重跑"
            })

    def _compute_metrics(self, pages):
        """汇总量化指标"""
        total_pages = len(pages)

        self.metrics.update({
            'total_pages': total_pages,
            'total_issues': len(self.issues),
            'p1_issues': sum(1 for i in self.issues if i['severity'] == 'P1'),
            'p2_issues': sum(1 for i in self.issues if i['severity'] == 'P2'),
            'health_score': max(0, 100 - len([i for i in self.issues if i['severity'] == 'P1']) * 10
                                   - len([i for i in self.issues if i['severity'] == 'P2']) * 3),
        })

    def _print_report(self):
        print(f"\n{'='*50}")
        print("📊 健康检查报告")
        print(f"{'='*50}")

        # 量化指标
        print("\n## 核心指标")
        indicators = [
            ('健康评分', f"{self.metrics.get('health_score', 0):.0f}/100"),
            ('总页面', self.metrics.get('total_pages', 0)),
            ('断链', self.metrics.get('broken_links', 0)),
            ('孤立页面', self.metrics.get('orphan_pages', 0)),
            ('孤立率', f"{self.metrics.get('orphan_rate', 0):.1%}"),
            ('缺少 frontmatter', self.metrics.get('missing_frontmatter', 0)),
            ('引用已废止法规', self.metrics.get('deprecated_refs', 0)),
            ('过短页面', self.metrics.get('short_pages', 0)),
            ('无摘要页面', self.metrics.get('no_summary_pages', 0)),
        ]
        for label, val in indicators:
            print(f"  {label}: {val}")

        # 注册表指标
        if self.metrics.get('registry_exists'):
            print("\n## 注册表健康")
            ri = [
                ('实体总数', self.metrics.get('entities_total', 0)),
                ('有溯源的实体', f"{self.metrics.get('entities_with_source', 0)} ({self.metrics.get('source_coverage_rate', 0):.1%})"),
                ('无别名实体', self.metrics.get('entities_without_alias', 0)),
                ('无证据关系', self.metrics.get('no_evidence_relations', 0)),
                ('未回补降级任务', self.metrics.get('unreplayed_degradations', 0)),
            ]
            for label, val in ri:
                print(f"  {label}: {val}")

        # 问题分级
        print(f"\n## 问题分级")
        sev = Counter(i['severity'] for i in self.issues)
        for s in ['P1', 'P2']:
            print(f"  {s}: {sev.get(s, 0)} 条")

        if sev.get('P1', 0) > 0:
            print(f"\n## 🚨 P1 问题 (需立即处理)")
            for i in self.issues:
                if i['severity'] == 'P1':
                    print(f"  [{i['type']}] {i['detail']}")

        # 保存报告
        report_path = WORKSPACE / "output" / "wiki_health_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics,
                'issues': self.issues[:50],  # 只保存前50条
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📄 完整报告: {report_path}")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--report', action='store_true', help='生成量化报告')
    p.add_argument('--fix-dry', action='store_true', help='预演修复')
    args = p.parse_args()

    linter = WikiLinter()
    linter.run_all()


if __name__ == '__main__':
    main()
