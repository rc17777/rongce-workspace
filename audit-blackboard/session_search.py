# -*- coding: utf-8 -*-
"""
融策会话搜索引擎 v1.0 — Session Search (FTS5)
================================================
对标 ZLink SQLite FTS5：为 Agent 对话历史和审计发现建立全文索引。

融策的黑板模式中，每个子Agent的 spawn task 和 findings 都落盘为文件。
FTS5 索引让"合同猎犬当时为什么判定合同#23异常"可以从文件中搜出原文。

三层索引：
  1. findings/*.json  — 结构化审计发现（标题+描述+证据链）
  2. tasks/*.json     — spawn task 原始任务
  3. handovers/*.json — 交接包上下文

用法：
  from session_search import SessionSearch
  ss = SessionSearch()
  ss.rebuild_index('XX项目')        # 重建索引
  results = ss.search('围标 关联')   # 全文搜索
  ss.close()
"""

import sys, json, sqlite3, re, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

WORKSPACE = Path(__file__).parent.parent
PROJECTS = WORKSPACE / 'audit-blackboard' / 'projects'
INDEX_DIR = WORKSPACE / 'audit-blackboard' / 'search_index'
INDEX_DIR.mkdir(parents=True, exist_ok=True)


class SessionSearch:
    """
    SQLite FTS5 全文搜索引擎。

    对标 ZLink SearchIndex:
      - 增量更新（只索引新/修改过的文件）
      - 支持中文分词（unicode61 tokenizer）
      - snippet() 高亮命中位置
    """

    def __init__(self, db_path=None):
        self.db_path = str(db_path or (INDEX_DIR / 'session_fts.db'))
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self):
        """确保 FTS5 索引表存在"""
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS findings_fts USING fts5(
                project_id, agent, finding_id, title, description, evidence, severity, coordinate,
                tokenize='unicode61'
            )
        """)
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts USING fts5(
                project_id, agent, task_content, coordinate,
                tokenize='unicode61'
            )
        """)
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS handovers_fts USING fts5(
                project_id, source_agent, goal, confirmed_facts, warnings_text, context_snapshot,
                tokenize='unicode61'
            )
        """)
        # 元数据表：记录已索引的文件及其 mtime
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS index_meta (
                file_path TEXT PRIMARY KEY,
                project_id TEXT,
                index_type TEXT,
                indexed_at REAL,
                file_mtime REAL
            )
        """)
        self.conn.commit()

    def rebuild_project(self, project_name):
        """重建单个项目的全量索引"""
        proj_dir = PROJECTS / project_name.replace(' ', '_')
        if not proj_dir.exists():
            print(f'项目不存在: {proj_dir}')
            return 0

        total = 0

        # 1. 索引 findings
        findings_dir = proj_dir / 'findings'
        if findings_dir.exists():
            for fp in findings_dir.glob('*.json'):
                count = self._index_findings_file(project_name, fp)
                total += count

        # 2. 索引 tasks/penetrate plan
        tasks_dir = proj_dir / 'tasks'
        if tasks_dir.exists():
            for fp in tasks_dir.glob('*.json'):
                self._index_tasks_file(project_name, fp)
                total += 1

        # 3. 索引 handovers
        handovers_dir = proj_dir / 'handovers'
        if handovers_dir.exists():
            for fp in handovers_dir.glob('*.json'):
                self._index_handover_file(project_name, fp)
                total += 1

        self.conn.commit()
        return total

    def _index_findings_file(self, project_name, filepath):
        """索引单个 findings JSON 文件"""
        try:
            data = json.loads(Path(filepath).read_text(encoding='utf-8'))
        except:
            return 0

        items = data if isinstance(data, list) else data.get('findings', data.get('results', []))
        agent = Path(filepath).stem.split('_')[0]

        count = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            finding_id = item.get('finding_id', item.get('id', ''))
            title = item.get('title', '')[:500]
            desc = item.get('description', '')[:2000]
            evidence = json.dumps(item.get('evidence', []), ensure_ascii=False)[:2000]
            severity = item.get('severity', '')
            coordinate = item.get('coordinate', '')

            self.conn.execute(
                "INSERT INTO findings_fts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (project_name, agent, finding_id, title, desc, evidence, severity, coordinate)
            )
            count += 1

        return count

    def _index_tasks_file(self, project_name, filepath):
        """索引单个 task/penetrate_plan 文件"""
        try:
            data = json.loads(Path(filepath).read_text(encoding='utf-8'))
        except:
            return

        if 'parallel_tasks' in data:
            for t in data['parallel_tasks']:
                agent = t.get('agent_id', '')
                content = t.get('spawn_task', '')[:5000]
                coord = t.get('coordinate', '')
                self.conn.execute(
                    "INSERT INTO tasks_fts VALUES (?, ?, ?, ?)",
                    (project_name, agent, content, coord)
                )

    def _index_handover_file(self, project_name, filepath):
        """索引单个 handover 文件"""
        try:
            data = json.loads(Path(filepath).read_text(encoding='utf-8'))
        except:
            return

        source = data.get('source_agent', '')
        goal = data.get('goal', '')[:1000]
        facts = json.dumps(data.get('confirmed_facts', []), ensure_ascii=False)[:2000]
        warnings = json.dumps(data.get('warnings', []), ensure_ascii=False)[:1000]
        ctx = data.get('context_snapshot', '')[:2000]

        self.conn.execute(
            "INSERT INTO handovers_fts VALUES (?, ?, ?, ?, ?, ?)",
            (project_name, source, goal, facts, warnings, ctx)
        )

    def search(self, query, scope='all', project=None, limit=10):
        """
        全文搜索。

        参数:
          query: 搜索词
          scope: 'findings' | 'tasks' | 'handovers' | 'all'
          project: 限定项目名称
          limit: 返回条数

        返回: [{'type': str, 'project': str, 'snippet': str, 'source': str, ...}]
        """
        results = []
        project_filter = f' AND project_id="{project}"' if project else ''

        if scope in ('findings', 'all'):
            rows = self.conn.execute(
                f"""SELECT project_id, agent, finding_id, severity, coordinate,
                    snippet(findings_fts, 1, '<mark>', '</mark>', '...', 40) as snip1,
                    snippet(findings_fts, 2, '<mark>', '</mark>', '...', 40) as snip2
                    FROM findings_fts WHERE findings_fts MATCH ?{project_filter}
                    ORDER BY rank LIMIT ?""",
                (self._sanitize_query(query), limit)
            ).fetchall()
            for r in rows:
                results.append({
                    'type': 'finding',
                    'project': r['project_id'],
                    'agent': r['agent'],
                    'finding_id': r['finding_id'],
                    'severity': r['severity'],
                    'coordinate': r['coordinate'],
                    'snippet': (r['snip1'] or '') + ' ' + (r['snip2'] or ''),
                    'source': f"{r['agent']} → {r['finding_id']}",
                })

        if scope in ('tasks', 'all') and len(results) < limit:
            rows = self.conn.execute(
                f"""SELECT project_id, agent, coordinate,
                    snippet(tasks_fts, 2, '<mark>', '</mark>', '...', 40) as snip
                    FROM tasks_fts WHERE tasks_fts MATCH ?{project_filter}
                    ORDER BY rank LIMIT ?""",
                (self._sanitize_query(query), limit - len(results))
            ).fetchall()
            for r in rows:
                results.append({
                    'type': 'task',
                    'project': r['project_id'],
                    'agent': r['agent'],
                    'coordinate': r['coordinate'],
                    'snippet': r['snip'] or '',
                    'source': f"{r['agent']} spawn task ({r['coordinate']})",
                })

        if scope in ('handovers', 'all') and len(results) < limit:
            rows = self.conn.execute(
                f"""SELECT project_id, source_agent,
                    snippet(handovers_fts, 2, '<mark>', '</mark>', '...', 40) as snip
                    FROM handovers_fts WHERE handovers_fts MATCH ?{project_filter}
                    ORDER BY rank LIMIT ?""",
                (self._sanitize_query(query), limit - len(results))
            ).fetchall()
            for r in rows:
                results.append({
                    'type': 'handover',
                    'project': r['project_id'],
                    'agent': r['source_agent'],
                    'snippet': r['snip'] or '',
                    'source': f"{r['source_agent']} handover",
                })

        return results

    def _sanitize_query(self, query):
        """清理搜索词，防止 FTS5 语法错误"""
        # 移除 FTS5 特殊字符
        sanitized = re.sub(r'["\*\(\)]', '', query)
        if not sanitized.strip():
            return '""'
        # 对中文查询加引号避免解析问题
        if any('\u4e00' <= c <= '\u9fff' for c in sanitized):
            return f'"{sanitized}"'
        return sanitized

    def stats(self, project=None):
        """索引统计"""
        stats = {}
        for table in ['findings_fts', 'tasks_fts', 'handovers_fts']:
            if project:
                stats[table] = self.conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE project_id=?",
                    (project,)
                ).fetchone()[0]
            else:
                stats[table] = self.conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]

        stats['projects'] = [
            r[0] for r in self.conn.execute(
                "SELECT DISTINCT project_id FROM findings_fts"
            ).fetchall()
        ]
        return stats

    def close(self):
        self.conn.close()


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='融策会话搜索引擎 v1.0 (FTS5)')
    sub = parser.add_subparsers(dest='cmd')

    p_rebuild = sub.add_parser('rebuild', help='重建项目索引')
    p_rebuild.add_argument('--project', required=True, help='项目名称')

    p_rebuild_all = sub.add_parser('rebuild-all', help='重建所有项目索引')

    p_search = sub.add_parser('search', help='全文搜索')
    p_search.add_argument('query', help='搜索词')
    p_search.add_argument('--scope', default='all', choices=['all', 'findings', 'tasks', 'handovers'])
    p_search.add_argument('--project', default=None, help='限定项目')
    p_search.add_argument('--limit', type=int, default=10)

    p_stats = sub.add_parser('stats', help='索引统计')
    p_stats.add_argument('--project', default=None)

    args = parser.parse_args()

    ss = SessionSearch()

    if args.cmd == 'rebuild':
        count = ss.rebuild_project(args.project)
        print(f'✅ 已索引 {args.project}: {count} 条记录')

    elif args.cmd == 'rebuild-all':
        total = 0
        for proj_dir in PROJECTS.iterdir():
            if proj_dir.is_dir() and not proj_dir.name.startswith('_'):
                count = ss.rebuild_project(proj_dir.name)
                print(f'  {proj_dir.name}: {count} 条')
                total += count
        print(f'\n✅ 总计: {total} 条记录')

    elif args.cmd == 'search':
        results = ss.search(args.query, args.scope, args.project, args.limit)
        if not results:
            print('未找到匹配结果')
        else:
            for i, r in enumerate(results):
                print(f'\n[{i+1}] [{r["type"].upper()}] {r["source"]}')
                print(f'  项目: {r["project"]}')
                if r.get('severity'):
                    print(f'  严重度: {r["severity"]}')
                if r.get('finding_id'):
                    print(f'  ID: {r["finding_id"]}')
                print(f'  {r["snippet"][:200]}')
        print(f'\n共 {len(results)} 条结果')

    elif args.cmd == 'stats':
        s = ss.stats(args.project)
        print('=== FTS5 索引统计 ===')
        print(f'findings:  {s["findings_fts"]} 条')
        print(f'tasks:     {s["tasks_fts"]} 条')
        print(f'handovers: {s["handovers_fts"]} 条')
        print(f'项目:      {", ".join(s["projects"]) if s["projects"] else "(无)"}')

    else:
        parser.print_help()

    ss.close()
