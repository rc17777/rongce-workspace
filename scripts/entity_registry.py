#!/usr/bin/env python3
"""
实体注册表 (Entity Registry) — 融策 wiki 知识库地基
基于 SQLite，管理实体 ID、别名、溯源、版本、审核状态
"""
import sqlite3, json, uuid, hashlib, os, sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = Path(__file__).parent.parent / "config" / "entity_registry.sqlite"


class EntityRegistry:
    """实体注册表：唯一 ID、别名映射、溯源追踪、审核工作流"""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as db:
            db.executescript("""
                -- 实体主表
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,                -- 稳定UUID
                    canonical_name TEXT NOT NULL,       -- 规范名称
                    entity_type TEXT NOT NULL,          -- regulation/project/organization/fund/indicator/audit_finding/audit_procedure/rectification/person
                    properties TEXT DEFAULT '{}',       -- JSON: 类型特定字段
                    source_doc_id TEXT,                 -- 来源文档ID
                    source_chunk_id TEXT,               -- 来源chunk ID
                    source_quote TEXT,                  -- 原文片段
                    char_start INTEGER,                 -- 字符起始位置
                    char_end INTEGER,                   -- 字符结束位置
                    confidence REAL DEFAULT 1.0,        -- 抽取置信度
                    extractor TEXT DEFAULT 'manual',    -- regex/dictionary/uie/llm/manual
                    extractor_version TEXT,             -- 抽取器版本
                    review_status TEXT DEFAULT 'pending', -- pending/confirmed/rejected/merged/deprecated
                    source_type TEXT DEFAULT 'original', -- original/generated/human
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    valid_from TEXT,                    -- 生效日期(法规/项目)
                    valid_to TEXT                       -- 失效日期
                );

                -- 别名表
                CREATE TABLE IF NOT EXISTS aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                    alias TEXT NOT NULL,
                    alias_type TEXT DEFAULT 'synonym',  -- synonym/abbreviation/former_name/typo_variant
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_aliases_alias ON aliases(alias);
                CREATE INDEX IF NOT EXISTS idx_aliases_entity ON aliases(entity_id);

                -- 实体合并/重定向表
                CREATE TABLE IF NOT EXISTS redirects (
                    old_id TEXT PRIMARY KEY,
                    new_id TEXT NOT NULL REFERENCES entities(id),
                    reason TEXT,
                    merged_at TEXT DEFAULT (datetime('now'))
                );

                -- 关系表
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL REFERENCES entities(id),
                    predicate TEXT NOT NULL,            -- 关系类型
                    object_id TEXT NOT NULL REFERENCES entities(id),
                    properties TEXT DEFAULT '{}',       -- JSON: 额外属性
                    evidence_doc_id TEXT,               -- 证据文档
                    evidence_chunk_id TEXT,             -- 证据chunk
                    evidence_quote TEXT,                -- 证据原文
                    confidence REAL DEFAULT 1.0,
                    relation_status TEXT DEFAULT 'candidate', -- candidate/llm_verified/human_verified/rejected/deprecated
                    extractor TEXT DEFAULT 'manual',
                    created_at TEXT DEFAULT (datetime('now')),
                    valid_from TEXT,
                    valid_to TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_relations_subject ON relations(subject_id);
                CREATE INDEX IF NOT EXISTS idx_relations_object ON relations(object_id);
                CREATE INDEX IF NOT EXISTS idx_relations_predicate ON relations(predicate);

                -- 降级处理台账
                CREATE TABLE IF NOT EXISTS degradation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,            -- disambiguation/summary/relation
                    entity_ids TEXT,                    -- 涉及的实体ID
                    reason TEXT,                        -- 降级原因
                    degraded_at TEXT DEFAULT (datetime('now')),
                    replayed INTEGER DEFAULT 0          -- 是否已回补重跑
                );

                -- 编译运行日志
                CREATE TABLE IF NOT EXISTS compile_runs (
                    id TEXT PRIMARY KEY,
                    started_at TEXT,
                    finished_at TEXT,
                    docs_processed INTEGER,
                    entities_extracted INTEGER,
                    relations_created INTEGER,
                    l2_calls INTEGER,
                    l3_calls INTEGER,
                    status TEXT
                );
            """)

    # ---- 实体 CRUD ----

    def upsert_entity(self, canonical_name, entity_type, properties=None, **kwargs):
        """插入或更新实体。返回实体ID和是否新建"""
        existing = self.find_by_name(canonical_name, entity_type)
        if existing:
            eid = existing['id']
            self._update_entity(eid, properties, **kwargs)
            return eid, False

        eid = str(uuid.uuid4())
        data = {
            'id': eid,
            'canonical_name': canonical_name,
            'entity_type': entity_type,
            'properties': json.dumps(properties or {}, ensure_ascii=False),
            'review_status': 'pending',
            'source_type': 'original',
            'confidence': 1.0,
            'extractor': 'manual',
        }
        valid_cols = {'source_doc_id', 'source_chunk_id', 'source_quote', 'char_start',
                      'char_end', 'confidence', 'extractor', 'extractor_version',
                      'review_status', 'source_type', 'valid_from', 'valid_to'}
        for k, v in kwargs.items():
            if k in valid_cols and v is not None:
                data[k] = v

        cols = list(data.keys())
        placeholders = ':' + ', :'.join(cols)
        sql = f"INSERT INTO entities ({', '.join(cols)}) VALUES ({placeholders})"
        with self._connect() as db:
            db.execute(sql, data)
        return eid, True

    def _update_entity(self, eid, properties=None, **kwargs):
        updates = {'id': eid, 'updated_at': datetime.now().isoformat()}
        if properties:
            updates['properties'] = json.dumps(properties, ensure_ascii=False)
        for k, v in kwargs.items():
            if k in ('source_doc_id', 'source_chunk_id', 'source_quote', 'char_start',
                     'char_end', 'confidence', 'extractor', 'extractor_version',
                     'review_status', 'source_type', 'valid_from', 'valid_to',
                     'canonical_name'):
                updates[k] = v
        if len(updates) <= 2:
            return
        set_clause = ', '.join(f"{k}=:{k}" for k in updates if k != 'id')
        with self._connect() as db:
            db.execute(f"UPDATE entities SET {set_clause} WHERE id=:id", updates)

    def find_by_name(self, name, entity_type=None):
        with self._connect() as db:
            if entity_type:
                row = db.execute(
                    "SELECT * FROM entities WHERE canonical_name=? AND entity_type=? AND review_status != 'deprecated'",
                    (name, entity_type)).fetchone()
            else:
                # 先查规范名
                row = db.execute(
                    "SELECT * FROM entities WHERE canonical_name=? AND review_status != 'deprecated'",
                    (name,)).fetchone()
                if not row:
                    # 再查别名
                    row = db.execute("""
                        SELECT e.* FROM entities e
                        JOIN aliases a ON e.id = a.entity_id
                        WHERE a.alias=? AND e.review_status != 'deprecated'
                        ORDER BY a.confidence DESC LIMIT 1
                    """, (name,)).fetchone()
            return dict(row) if row else None

    def resolve_entity(self, name, entity_type=None):
        """解析实体名→稳定ID，处理重定向"""
        result = self.find_by_name(name, entity_type)
        if not result:
            return None
        # 追踪重定向链
        eid = result['id']
        with self._connect() as db:
            while True:
                redirect = db.execute("SELECT new_id FROM redirects WHERE old_id=?", (eid,)).fetchone()
                if not redirect:
                    break
                eid = redirect['new_id']
        return eid

    def add_alias(self, entity_id, alias, alias_type='synonym', confidence=1.0, source=None):
        with self._connect() as db:
            # 去重
            existing = db.execute(
                "SELECT id FROM aliases WHERE entity_id=? AND alias=?",
                (entity_id, alias)).fetchone()
            if existing:
                return
            db.execute("""
                INSERT INTO aliases (entity_id, alias, alias_type, confidence, source)
                VALUES (?, ?, ?, ?, ?)
            """, (entity_id, alias, alias_type, confidence, source))

    def merge_entities(self, old_id, new_id, reason=""):
        """合并实体：old_id → new_id，记录重定向"""
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO redirects (old_id, new_id, reason) VALUES (?, ?, ?)",
                       (old_id, new_id, reason))
            db.execute("UPDATE entities SET review_status='merged', updated_at=? WHERE id=?",
                       (datetime.now().isoformat(), old_id))
            # 迁移别名
            db.execute("UPDATE aliases SET entity_id=? WHERE entity_id=?", (new_id, old_id))
            # 迁移关系
            db.execute("UPDATE relations SET subject_id=? WHERE subject_id=?", (new_id, old_id))
            db.execute("UPDATE relations SET object_id=? WHERE object_id=?", (new_id, old_id))

    # ---- 关系 CRUD ----

    def add_relation(self, subject_id, predicate, object_id, properties=None,
                     evidence_quote=None, confidence=1.0,
                     relation_status='candidate', extractor='manual', **kwargs):
        rid = str(uuid.uuid4())
        data = {
            'id': rid, 'subject_id': subject_id, 'predicate': predicate,
            'object_id': object_id,
            'properties': json.dumps(properties or {}, ensure_ascii=False),
            'evidence_quote': evidence_quote,
            'confidence': confidence, 'relation_status': relation_status,
            'extractor': extractor
        }
        data.update(kwargs)
        fields = 'id,subject_id,predicate,object_id,properties,evidence_quote,confidence,relation_status,extractor,evidence_doc_id,evidence_chunk_id,valid_from,valid_to'
        placeholders = ':id,:subject_id,:predicate,:object_id,:properties,:evidence_quote,:confidence,:relation_status,:extractor,:evidence_doc_id,:evidence_chunk_id,:valid_from,:valid_to'
        with self._connect() as db:
            db.execute(f"INSERT INTO relations ({fields}) VALUES ({placeholders})", data)
        return rid

    def promote_relation(self, rid, new_status):
        """候选边→正式边"""
        with self._connect() as db:
            db.execute("UPDATE relations SET relation_status=?, updated_at=? WHERE id=?",
                       (new_status, datetime.now().isoformat(), rid))

    # ---- 降级台账 ----

    def log_degradation(self, task_type, entity_ids, reason):
        with self._connect() as db:
            db.execute("""
                INSERT INTO degradation_log (task_type, entity_ids, reason)
                VALUES (?, ?, ?)
            """, (task_type, json.dumps(entity_ids, ensure_ascii=False), reason))

    def get_unreplayed(self):
        with self._connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM degradation_log WHERE replayed=0 ORDER BY degraded_at").fetchall()]

    def mark_replayed(self, log_id):
        with self._connect() as db:
            db.execute("UPDATE degradation_log SET replayed=1 WHERE id=?", (log_id,))

    # ---- 查询辅助 ----

    def get_entity(self, eid):
        with self._connect() as db:
            row = db.execute("SELECT * FROM entities WHERE id=?", (eid,)).fetchone()
            return dict(row) if row else None

    def get_aliases(self, eid):
        with self._connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM aliases WHERE entity_id=?", (eid,)).fetchall()]

    def get_relations(self, eid, direction='both', status='confirmed'):
        """获取实体关联"""
        status_filter = "AND r.relation_status = ?" if status else ""
        params_out = (eid,) + ((status,) if status else ())
        params_in = params_out
        with self._connect() as db:
            outgoing = db.execute(f"""
                SELECT r.*, e.canonical_name as object_name, e.entity_type as object_type
                FROM relations r JOIN entities e ON r.object_id = e.id
                WHERE r.subject_id=? {status_filter}
            """, params_out).fetchall() if direction in ('out', 'both') else []
            incoming = db.execute(f"""
                SELECT r.*, e.canonical_name as subject_name, e.entity_type as subject_type
                FROM relations r JOIN entities e ON r.subject_id = e.id
                WHERE r.object_id=? {status_filter}
            """, params_in).fetchall() if direction in ('in', 'both') else []
        return {'out': [dict(r) for r in outgoing], 'in': [dict(r) for r in incoming]}

    def stats(self):
        with self._connect() as db:
            return {
                'total_entities': db.execute("SELECT COUNT(*) FROM entities WHERE review_status != 'deprecated'").fetchone()[0],
                'total_relations': db.execute("SELECT COUNT(*) FROM relations WHERE relation_status NOT IN ('rejected','deprecated')").fetchone()[0],
                'by_type': {r[0]: r[1] for r in db.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type").fetchall()},
                'by_status': {r[0]: r[1] for r in db.execute("SELECT review_status, COUNT(*) FROM entities GROUP BY review_status").fetchall()},
                'pending_review': db.execute("SELECT COUNT(*) FROM entities WHERE review_status='pending'").fetchone()[0],
                'degraded_tasks': db.execute("SELECT COUNT(*) FROM degradation_log WHERE replayed=0").fetchone()[0],
            }

    def export_entities_jsonl(self, path):
        with self._connect() as db:
            rows = db.execute("SELECT * FROM entities WHERE review_status != 'deprecated'").fetchall()
        with open(path, 'w', encoding='utf-8') as f:
            for r in rows:
                f.write(json.dumps(dict(r), ensure_ascii=False) + '\n')
        return len(rows)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--init', action='store_true', help='初始化数据库')
    p.add_argument('--stats', action='store_true', help='统计信息')
    p.add_argument('--export', type=str, help='导出JSONL路径')
    args = p.parse_args()

    reg = EntityRegistry()
    if args.stats:
        print(json.dumps(reg.stats(), ensure_ascii=False, indent=2))
    elif args.export:
        n = reg.export_entities_jsonl(args.export)
        print(f"导出 {n} 条实体到 {args.export}")
    else:
        print("实体注册表初始化完成:", reg.db_path)
        s = reg.stats()
        print(f"  实体: {s['total_entities']}, 关系: {s['total_relations']}, 待审核: {s['pending_review']}")


if __name__ == '__main__':
    main()
